# DataModelRLS.md · ProSmet Data Model And RLS Contract

Дата: 2026-05-23  
Статус: архитектурный контракт Data Model/RLS для MVP  
Основа: `Scope.md`, `docs/SolutionDesign.md`, `docs/Architecture.md`, `docs/Evals/QualityGates.md`

## 1. Назначение

Документ фиксирует контракт tenant isolation, RLS и минимальные тесты доступа для таблиц ProSmet MVP.

Инварианты:

- приложение работает через DB role без `BYPASSRLS`;
- приложение не владеет пользовательскими таблицами;
- tenant-owned sensitive tables имеют прямой `tenant_id`;
- sensitive tables включают `FORCE ROW LEVEL SECURITY`;
- все пользовательские и worker-запросы идут через `withTenant`;
- `tenantId` из клиента не используется как authority;
- tenant A не читает, не изменяет и не удаляет данные tenant B;
- доступ к original PII пишет `pii_access_log`;
- audit tables append-only для приложения.

## 2. Tenant Resolution Sources

| Source | Используется для | Правило |
| --- | --- | --- |
| `server_session` | public anonymous session | Tenant определен сервером при `POST /api/session` через domain/origin/entry token. |
| `membership` | owner dashboard | Tenant берется из active `memberships` authenticated user. |
| `signed_link_token` | client estimate link/PDF/events | Raw token хешируется; tenant берется из `client_estimate_links.tenant_id`. |
| `worker_job` | PDF, events, notifications, price import | Job создан сервером и содержит tenant scope; worker сверяет tenant job с tenant сущности. |
| `bot_callback_token` | bot quick actions | Tenant берется из signed callback token или server-side channel binding. |
| `admin_system` | migrations/admin maintenance | Только controlled admin path; не используется web/API request handlers. |
| `public_marketing` | ProSmet marketing site | Tenant отсутствует; доступ только к public marketing content and consented marketing lead write path. |

`tenant_id` из body/query/header/localStorage/postMessage не является источником tenant.

## 3. withTenant Contract

```ts
type TenantActor =
  | { type: "public_anonymous"; sessionId: string }
  | { type: "signed_link"; linkId: string }
  | { type: "owner_user"; userId: string; role: string; membershipId: string }
  | { type: "worker"; jobId: string; kind: string }
  | { type: "bot"; callbackId: string; provider: "telegram" | "max" };

type TenantContext = {
  tenantId: string; // server-resolved only
  source:
    | "server_session"
    | "membership"
    | "signed_link_token"
    | "worker_job"
    | "bot_callback_token"
    | "admin_system";
  actor: TenantActor;
  requestId: string;
  reason?: string;
};

async function withTenant<T>(
  context: TenantContext,
  fn: (tx: TenantBoundTransaction) => Promise<T>
): Promise<T>;
```

Обязательные свойства:

- открывает транзакцию или scoped DB session;
- выставляет DB session variables, например `app.tenant_id`, `app.actor_type`, `app.actor_id`, `app.request_id`;
- запрещает nested `withTenant` с другим tenant без явного system boundary;
- сбрасывает context после завершения;
- не принимает raw client `tenantId`;
- все repositories получают только `TenantBoundTransaction`, не global DB client;
- RLS policies используют `tenant_id = current_setting('app.tenant_id', true)::uuid`;
- server-side RBAC проверяется дополнительно к RLS.

## 4. RLS Matrix

Сокращения:

- `PA`: public anonymous context текущей server session;
- `SL`: signed link context текущего token;
- `OW`: owner session с membership/RBAC;
- `WK`: worker context;
- `ADM`: controlled admin/system context;
- `A/B`: тест tenant A не видит tenant B;
- `PII`: чтение decrypted/original PII требует `pii_access_log`;
- `APPEND`: приложение может только вставлять, не обновлять/удалять audit rows.

| Table | `tenant_id` required | Readable by | Writable by | Tenant resolution source | Audit requirement | Minimum tests |
| --- | --- | --- | --- | --- | --- | --- |
| `tenants` | Нет | PA только public profile после domain/token; OW через membership; ADM | ADM; controlled onboarding | domain/slug, membership, admin | `tenant.created`, `tenant.status_changed` | no private tenant fields in PA; inactive tenant blocks API |
| `tenant_domains` | Да | PA resolver server-side; OW settings; ADM | OW admin role; ADM | origin/domain -> tenant row | `tenant_domain.changed` | origin A cannot create/read domain B; invalid origin -> 403 |
| `tenant_settings` | Да | PA public subset; OW; WK readiness | OW admin role; ADM | session, membership, job | `tenant_settings.updated` | A/B read/update blocked; public response exposes only allowed fields |
| `users` | Нет | OW self; ADM; other users only through membership-scoped projection | auth service, user self, ADM | authenticated user id, membership | PII when reading phone/email/name outside self | user from A cannot enumerate B; full PII read logs |
| `memberships` | Да | OW own tenant memberships; ADM | OW tenant admin; ADM | authenticated user -> membership | `membership.changed` | user without membership cannot read tenant; A cannot add role in B |
| `sessions` | Да | PA own session; OW own session; WK cleanup | auth/session service | server_session, membership | `session.created`, `session.revoked` | session A cannot read/update session B; expired session rejected |
| `verification_tokens` | Нет; tenant-bound token stores tenant scope when applicable | auth service only; no list API | auth service only | token hash, auth flow | `auth.token_issued`, `auth.token_used` without raw token | raw token never stored; token for A cannot grant B |
| `tenant_pricing_profiles` | Да | OW; WK calculation/policy | OW admin; price import worker | membership, worker_job | `pricing_profile.updated` | A/B read/update blocked; old calculations keep old snapshot |
| `markup_policies` | Да | OW; WK calculation/policy | OW admin | membership, worker_job | `markup_policy.updated` | A/B blocked; discount policy changes audited |
| `approval_policy_profiles` | Да | OW; WK policy engine | OW admin | membership, worker_job | `approval_policy_profile.updated` | A/B blocked; weaker policy change audited |
| `notification_channels` | Да | OW masked external ids; WK send | OW admin; notification worker status update | membership, worker_job | `notification_channel.changed` | A/B blocked; external ids hashed/masked |
| `clients` | Да | OW masked by default; SL own published link subset; WK minimal | PA after consent; OW; WK normalization without decrypt read | session, membership, signed link, job | PII for decrypted phone/name/email | A/B blocked; full PII read creates log; consent required before insert |
| `leads` | Да | PA own session lead; OW; SL linked lead safe subset; WK | PA after consent; OW; WK | session, membership, signed link, job | `lead.created`, status changes | PA lead A cannot fetch lead B by id; OW A cannot read B |
| `lead_sources` | Да | OW; WK analytics; PA only current source response | PA session creation; OW; WK | session, membership, job | `lead_source.created` | A/B blocked; entry token hash not exposed |
| `acquisition_sessions` | Да | PA own session; OW; WK analytics | PA session service; WK analytics | session, membership, job | `acquisition_session.created` | A/B blocked; no raw PII in UTM/referrer audit |
| `consent_records` | Да | PA own consent; OW; SL own lead consent state; WK policy | PA consent service; OW; WK | session, membership, signed link, job | `consent.accepted` | consent A not reusable for B; consent before PII |
| `conversations` | Да | PA own conversation; OW; WK AI audit | PA/OW via chat service; WK | session, membership, job | `conversation.created` | A/B blocked; PA cannot attach to B lead |
| `messages` | Да | PA own messages; OW sanitized by default; WK AI gateway | PA/OW chat service; WK AI gateway | session, membership, job | `message.created`; PII for `content_encrypted` read | A/B blocked; AI sees sanitized only; encrypted read logs |
| `ai_payload_audit` | Да | OW audit view; WK AI audit | AI gateway/WK only | session/membership through AI gateway, job | append-only `ai_payload.*` | A/B blocked; no PII/money; APPEND |
| `rooms` | Да | PA own lead room; OW; SL published safe subset; WK | PA/OW params service; WK derived writes | session, membership, signed link, job | `room.params_saved` | A/B blocked; PA cannot mutate after ownership lost |
| `calculation_inputs` | Да | PA own lead input; OW; WK calculation/policy | params service, AI gateway, OW | session, membership, job | `calculation_input.created` | A/B blocked; AI confidence/risk stored; input hash stable |
| `calculations` | Да | PA own preview/snapshot before publication; OW; SL published calculation; WK | calculation service only | session, membership, signed link, job | `calculation.snapshot_created` | A/B blocked; immutable snapshot cannot update sums |
| `calculation_items` | Да | PA preview policy subset; OW; SL published subset; WK | calculation service only | parent calculation tenant | line audit in calculation plus row audit | A/B blocked; no manual insert outside engine service |
| `estimate_variants` | Да | PA preview policy subset; OW; SL published subset; WK | calculation service only | parent calculation tenant | variant totals tied to snapshot | A/B blocked; economy <= standard <= premium test |
| `approval_policy_decisions` | Да | OW; SL only publication state; WK policy | policy engine/WK only | membership, signed link, job | append-only `policy.decided` | A/B blocked; auto_publish impossible without snapshot; APPEND |
| `human_reviews` | Да | OW; WK publication worker | OW reviewer only | membership | `human_review.*` | A/B blocked; reviewer must be tenant member; APPEND or correction audit |
| `client_estimate_links` | Да | SL by token; OW; WK | publication service only | signed_link_token, membership, job | `client_link.created`, status changes | token A cannot access B; raw token not stored |
| `client_link_events` | Да | OW analytics; WK ingest; SL own event ack only | SL event API; WK ingest | signed_link_token, job | event-specific audit, idempotent | A/B blocked; duplicate key dedupes; no raw PII metadata |
| `pdf_assets` | Да | OW; SL bound link asset; WK PDF worker | PDF worker/publication service | membership, signed_link_token, job | `pdf.job_enqueued`, `pdf.generated`, `pdf.downloaded` | A/B blocked; asset requires approval/auto_publish |
| `price_books` | Да | OW; WK calculation/readiness | price import worker; OW admin activates | membership, job | `price_book.created`, `price_book.activated` | A/B blocked; old calculation unaffected after update |
| `price_imports` | Да | OW; WK import worker | OW upload/import; WK validation | membership, job | `price_import.created`, validation status changes | A/B blocked; source asset scoped to tenant |
| `price_items` | Да | OW; WK calculation | price import worker only after validation | membership, job | `price_item.imported` via import audit | A/B blocked; no AI access to price values |
| `coefficient_sets` | Да | OW; WK calculation | OW admin/import worker | membership, job | `coefficient_set.updated` | A/B blocked; snapshot hash stored in calculation |
| `coefficients` | Да | OW; WK calculation | OW admin/import worker | membership, job | `coefficient.updated` | A/B blocked; coefficient values never chosen by LLM |
| `regions` | Нет | PA/OW/WK readonly reference | ADM/migration only | global reference | migration/admin audit | public can read active regions; non-admin cannot write |
| `deployment_environments` | Нет | ADM; readiness service safe projection | ADM only | admin_system | `deployment_environment.changed` | no public read of sensitive infra fields; non-admin cannot write |
| `marketing_leads` | Нет | ADM/controlled ProSmet owner view only | public_marketing after consent; ADM | public_marketing, admin_system | `marketing.demo_requested`, `marketing_consent.accepted` | consent before phone/email/name; no tenant/customer access; no LLM payload |
| `marketing_events` | Нет | ADM aggregate/safe projection | public_marketing event API | public_marketing | `marketing.*` idempotent | no raw PII in metadata; no tenant/customer ids |
| `marketing_consent_records` | Нет | ADM/controlled ProSmet owner view only | public_marketing consent service | public_marketing | `marketing_consent.accepted` | exact legal version stored before contact data |
| `legal_documents` | Да | PA public active docs; OW; WK policy | OW admin/ADM | session, membership, job | `legal_document.changed` | A/B blocked; consent stores exact version |
| `legal_packs` | Да | PA public active pack metadata; OW; WK policy | OW admin/ADM | session, membership, job | `legal_pack.changed` | A/B blocked; publication blocked without active pack |
| `notifications` | Да | OW; WK sender | notification service/WK; owner test endpoint | membership, job | `notification.enqueued/sent/failed` | A/B blocked; bot payload contains no forbidden PII/price |
| `deals` | Да | OW; WK analytics/notification | lead service, OW status update, WK workflow | membership, job | `deal.created`, `deal.status_changed` | A/B blocked; status changes audited |
| `audit_log` | Да | OW tenant admin/auditor; ADM | services append only | current `withTenant` context | APPEND; payload hash only | A/B blocked; app cannot update/delete; no raw PII |
| `pii_access_log` | Да | OW tenant admin/auditor; ADM | PII access service append only | current `withTenant` owner context | APPEND; reason required | A/B blocked; PII read creates row; app cannot update/delete |

## 5. Worker Context

Worker jobs must carry tenant scope created by a trusted server path.

```ts
type TenantScopedJob = {
  jobId: string;
  tenantId: string; // server-created, not client-provided
  kind:
    | "pdf.generate"
    | "client-link-event.ingest"
    | "notification.send"
    | "ai-payload-audit.flush"
    | "price-import.validate"
    | "deployment-readiness.check";
  entityRefs: Record<string, string>;
  idempotencyKey: string;
  createdAt: string;
};
```

Rules:

- worker opens every DB operation through `withTenant({ source: "worker_job" })`;
- worker verifies every loaded entity has the same `tenant_id` as job context;
- worker does not use service role with `BYPASSRLS`;
- worker cannot call LLM outside AI gateway;
- PDF/event/notification jobs are idempotent;
- job payloads do not contain raw PII unless a specific service contract requires encrypted storage ref;
- failed jobs write audit and retry metadata without leaking PII.

## 6. Signed Link Token Contract

Client estimate links use high-entropy raw tokens.

Rules:

- raw token is shown only in URL and never stored;
- DB stores `token_hash`;
- token resolves to exactly one `client_estimate_links` row;
- `tenant_id`, `lead_id`, `calculation_id` are loaded server-side from the link row;
- signed link context opens `withTenant` after token resolution;
- expired/revoked tokens return safe state and can write `expired_link_opened`;
- token does not expose tenant id, price snapshot internals, storage keys or PII;
- PDF asset download through token is allowed only for asset bound to the same link/calculation.

Minimum tests:

- token for tenant A cannot fetch tenant B link/calculation/PDF even if URL ids are guessed;
- expired token cannot reveal estimate details;
- raw token is absent from DB and audit logs;
- link event idempotency prevents duplicate `opened` spam.

## 7. pii_access_log Contract

Original PII includes:

- `clients.phone_encrypted`;
- `clients.name_encrypted`;
- `clients.email_encrypted`;
- `users.email`;
- `users.phone`;
- `users.name`;
- `messages.content_encrypted`;
- any future address, voice, file or free-text original field.

Rules:

- masked projections do not require `pii_access_log`;
- decrypting or returning original PII to owner UI requires `pii_access_log`;
- reason is required for full PII read;
- log payload never contains the PII value;
- public anonymous and signed link contexts should not decrypt original PII;
- worker should avoid original PII; if unavoidable, use a dedicated audited service path and `audit_log` reason.

Minimum log fields from current model:

```ts
type PiiAccessLogRow = {
  id: string;
  tenant_id: string;
  user_id: string;
  entity_type: string;
  entity_id: string;
  reason: string;
  created_at: string;
};
```

## 8. Required Tenant Isolation Tests

Минимальный набор integration/security tests:

1. `owner_a_cannot_read_owner_b_lead`: owner tenant A запрашивает `GET /api/dashboard/leads/:id` tenant B и получает `404` или `403` без утечки существования.
2. `owner_a_cannot_update_owner_b_lead`: tenant A не может менять status/deal/status review tenant B.
3. `public_session_a_cannot_mutate_lead_b`: anonymous session tenant A не может сохранить contact/params для lead tenant B.
4. `signed_link_a_cannot_open_link_b`: token tenant A не открывает calculation/PDF tenant B при подмене ids.
5. `worker_job_tenant_mismatch_fails`: job с tenant A и entity tenant B fail-closed до side effect.
6. `rls_select_insert_update_delete`: прямые repository calls внутри `withTenant(A)` не видят и не меняют rows tenant B.
7. `tenant_id_in_body_is_rejected`: API body/query с `tenantId` tenant B не меняет server-resolved tenant A.
8. `pii_read_writes_log`: owner full PII read создает `pii_access_log`; masked read не создает.
9. `audit_append_only`: app role не может update/delete `audit_log`, `pii_access_log`, `ai_payload_audit`.
10. `ai_payload_no_pii_no_money`: stored AI payload audit не содержит phone/name/email/address/money/price fields.
11. `publication_requires_review_or_auto_publish`: link/PDF не создаются без human review или audited `auto_publish`.
12. `old_snapshot_unchanged_after_price_update`: tenant price update не меняет старые `calculations` и `calculation_items`.

## 9. Policy Shape

Canonical RLS policy для tenant-owned таблиц:

```sql
CREATE POLICY tenant_isolation_select ON <table>
  FOR SELECT
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

CREATE POLICY tenant_isolation_insert ON <table>
  FOR INSERT
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);

CREATE POLICY tenant_isolation_update ON <table>
  FOR UPDATE
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);

CREATE POLICY tenant_isolation_delete ON <table>
  FOR DELETE
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
```

Для append-only audit tables `UPDATE` и `DELETE` не выдаются application role. Для public/global reference tables (`regions`, часть `tenants` public profile) используется отдельная readonly policy или view/projection.

## 10. Fail-Closed Rules

Операция должна завершаться отказом до чтения/записи, если:

- tenant не определен сервером;
- tenant inactive;
- `withTenant` не установлен;
- `tenant_id` сущности не совпадает с context tenant;
- signed token invalid/expired/revoked;
- owner user не имеет active membership;
- worker job tenant scope не совпадает с entity tenant;
- endpoint пытается принять client `tenantId` как источник доступа;
- чтение original PII запрошено без role/reason;
- publication/link/PDF пытается обойти review/policy gates.
