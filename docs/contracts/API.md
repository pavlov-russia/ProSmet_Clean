# API.md · ProSmet MVP API Contracts

Дата: 2026-05-23  
Статус: архитектурный контракт API для MVP  
Основа: `Scope.md`, `docs/SolutionDesign.md`, `docs/Architecture.md`, `docs/Evals/QualityGates.md`

## 1. Назначение

Документ фиксирует прикладной контракт API ProSmet MVP. Он не является OpenAPI-спецификацией, но задает обязательные границы для route handlers, сервисов и тестов.

Инварианты:

- `tenantId` никогда не принимается из клиента как authority;
- tenant определяется только сервером: session, membership, signed token, entry token или worker job;
- все tenant-scoped операции выполняются внутри `withTenant`;
- расчетные суммы создаются только deterministic calculation engine;
- LLM не получает ПД, деньги, прайсы и PDF;
- клиентская ссылка/PDF создаются только после human approval или audited `auto_publish`;
- preview до телефона может быть partial/blurred и не является полным раскрытием сметы.

## 2. Canonical B2C Flow

Канонический B2C-поток:

```text
entry
  -> consent
  -> params/chat
  -> blurred/partial preview
  -> phone
  -> immutable calculation snapshot
  -> policy/human review
  -> full link/PDF
```

Детализация:

1. `entry`: клиент приходит из site widget, Avito entry или прямой публичной страницы. Сервер создает anonymous session и выводит tenant из domain/origin/entry token.
2. `consent`: до телефона, имени, email, адреса, голоса, файлов и свободного текста с возможными ПД записывается согласие с версией legal document.
3. `params/chat`: параметры собираются структурной формой или AI gateway. AI получает только sanitized payload без ПД и денег.
4. `blurred/partial preview`: deterministic engine может вернуть complete или partial preview. Итоги/ценовые блоки замыливаются по `tenant_settings.preview_reveal_policy`.
5. `phone`: если `phone_gate_enabled = true`, телефон фиксируется до полного раскрытия сметы/PDF.
6. `immutable calculation snapshot`: full publication workflow работает только с сохраненным immutable snapshot, версией формулы, прайса, коэффициентов и audit trail строк.
7. `policy/human review`: publication разрешается human review или deterministic policy decision `auto_publish`.
8. `full link/PDF`: клиент получает signed link и PDF/job только после publication/unlock gates.

## 3. Contexts And Tenant Resolution

| Context | Где используется | Источник tenant | Правило доступа |
| --- | --- | --- | --- |
| `public anonymous` | widget, Avito entry, consent, lead intake, preview | server-resolved `tenant_domains`, public slug, signed entry token, anonymous server session | Доступ только к текущей anonymous session и ее lead/calculation до публикации. |
| `public marketing` | ProSmet marketing site, demo/pilot request | no tenant; public ProSmet site context | Доступ только к public marketing content and consented marketing lead write path. |
| `signed link` | `GET /api/client-links/:token`, unlock, PDF download, link events | raw token -> `token_hash` -> `client_estimate_links.tenant_id` | Token не раскрывает `tenant_id`; доступ только к link-bound lead/calculation. |
| `owner session` | dashboard, settings, human review, owner downloads | authenticated user -> active `memberships.tenant_id` | RBAC поверх RLS; чтение original PII пишет `pii_access_log`. |
| `worker` | PDF, events ingest, notifications, price import, AI audit flush, bot callbacks | server-created job/callback binding with tenant scope | Worker обязан открыть `withTenant`; idempotency key обязателен для повторяемых side effects. |

Клиентские поля `tenantId`, `tenant_id`, `organizationId` в body/query/localStorage/postMessage игнорируются или приводят к `TENANT_AUTHORITY_REJECTED`. Они могут появляться только в server-side internal DTO после tenant resolution.

## 4. Common Types

```ts
type UUID = string;
type ISODateTime = string;
type ISODate = string;
type MinorUnitAmount = string; // base-10 integer string in kopecks, no float
type MinorMoney = { amountMinor: MinorUnitAmount; currency: "RUB" };
type IdempotencyKey = string;

type ApiContext =
  | "public_marketing"
  | "public_anonymous"
  | "signed_link"
  | "owner_session"
  | "worker";

type CalculationCompleteness = "complete" | "partial" | "unusable";
type CalculationStatus = "draft_preview" | "snapshot_created" | "published" | "requires_review" | "requires_measurement" | "rejected";
type PolicyDecision = "auto_publish" | "requires_review" | "requires_measurement" | "reject_as_incomplete";
type PublicationMode = "full" | "partial";

type ApiErrorCode =
  | "VALIDATION_FAILED"
  | "UNAUTHENTICATED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "TENANT_NOT_FOUND"
  | "TENANT_INACTIVE"
  | "TENANT_AUTHORITY_REJECTED"
  | "ORIGIN_NOT_ALLOWED"
  | "CONSENT_REQUIRED"
  | "PHONE_REQUIRED"
  | "TOKEN_INVALID"
  | "TOKEN_EXPIRED"
  | "IDEMPOTENCY_CONFLICT"
  | "RATE_LIMITED"
  | "AI_UNAVAILABLE"
  | "AI_FORBIDDEN_FIELDS"
  | "CALCULATION_UNUSABLE"
  | "CALCULATION_MUTABLE"
  | "PRICE_BOOK_MISSING"
  | "PRICING_PROFILE_MISSING"
  | "LEGAL_PACK_MISSING"
  | "POLICY_REQUIRES_REVIEW"
  | "POLICY_REQUIRES_MEASUREMENT"
  | "AUTO_PUBLISH_DISABLED"
  | "PUBLICATION_GATE_BLOCKED"
  | "PDF_REQUIRED_BUT_UNAVAILABLE";

type ApiError = {
  error: {
    code: ApiErrorCode;
    message: string;
    requestId: string;
    details?: Record<string, unknown>;
  };
};

type PageRequest = {
  cursor?: string;
  limit?: number;
};

type PageResponse<T> = {
  items: T[];
  nextCursor: string | null;
};
```

## 5. Endpoint Matrix

| Endpoint | Context | Tenant resolution | Request | Response | Idempotency | Audit events |
| --- | --- | --- | --- | --- | --- | --- |
| `POST /api/marketing/leads` | public marketing | no tenant | `CreateMarketingLeadRequest` | `CreateMarketingLeadResponse` | required | `marketing.demo_requested`, `marketing_consent.accepted` |
| `POST /api/marketing/events` | public marketing | no tenant | `RecordMarketingEventRequest` | `RecordMarketingEventResponse` | event key required | `marketing.page_viewed`, `marketing.hero_cta_clicked`, `marketing.vertical_interest_clicked` |
| `POST /api/session` | public anonymous | origin/domain/public slug/entry token | `CreateSessionRequest` | `CreateSessionResponse` | optional | `session.created`, `entry.resolved` |
| `POST /api/consent` | public anonymous | anonymous session | `RecordConsentRequest` | `RecordConsentResponse` | required | `consent.accepted` |
| `POST /api/leads` | public anonymous, owner session | anonymous session or owner membership | `CreateLeadRequest` | `CreateLeadResponse` | required | `lead.created`, `deal.created` |
| `POST /api/leads/:id/contact` | public anonymous, owner session | lead must belong to current context | `SaveContactRequest` | `SaveContactResponse` | required | `contact.submitted`, `client.upserted` |
| `POST /api/leads/:id/params` | public anonymous, owner session | lead must belong to current context | `SaveLeadParamsRequest` | `SaveLeadParamsResponse` | required | `params.saved` |
| `POST /api/ai/collect-params` | public anonymous, owner session | lead/conversation scope | `CollectParamsRequest` | `CollectParamsResponse` | optional request id | `ai_payload.sanitized`, `ai_payload.completed` |
| `POST /api/calculations/preview` | public anonymous, owner session | lead/session or owner membership | `CreatePreviewCalculationRequest` | `CreatePreviewCalculationResponse` | required | `calculation.preview_created`, optional `client_link.preview_shown` |
| `POST /api/calculations` | public anonymous, owner session | lead/session or owner membership | `CreateCalculationSnapshotRequest` | `CreateCalculationSnapshotResponse` | required | `calculation.snapshot_created` |
| `GET /api/calculations/:id` | owner session, signed link | membership or signed link binding | none | `GetCalculationResponse` | no | `calculation.viewed`; PII read logs separately |
| `POST /api/calculations/:id/policy-decision` | public anonymous, owner session, worker | calculation tenant from server context | `RunPolicyDecisionRequest` | `RunPolicyDecisionResponse` | required | `policy.decided` |
| `POST /api/client-links/:token/unlock` | signed link, public anonymous | signed link token plus session/contact gate | `UnlockClientLinkRequest` | `UnlockClientLinkResponse` | required | `client_link.unlocked`, `phone_submitted` when present |
| `GET /api/client-links/:token` | signed link | signed link token | none | `GetClientLinkResponse` | no | `client_link.opened` or `client_link.reopened` |
| `POST /api/client-links/:token/events` | signed link | signed link token | `RecordClientLinkEventRequest` | `RecordClientLinkEventResponse` | event key required | event-specific `client_link.*` |
| `POST /api/auth/signin` | public anonymous | email/phone auth bootstrap; tenant after membership selection | `SignInRequest` | `SignInResponse` | required | `auth.signin_requested` |
| `GET /api/dashboard/leads` | owner session | membership | `ListLeadsRequest` | `ListLeadsResponse` | no | `dashboard.leads_listed` |
| `GET /api/dashboard/leads/:id` | owner session | membership and lead tenant | `GetLeadRequest` | `GetLeadResponse` | no | `lead.viewed`; `pii_access_log` if full PII |
| `PATCH /api/dashboard/leads/:id/status` | owner session | membership and lead tenant | `UpdateLeadStatusRequest` | `UpdateLeadStatusResponse` | required | `deal.status_changed` |
| `GET /api/dashboard/calculations/:id` | owner session | membership and calculation tenant | none | `GetDashboardCalculationResponse` | no | `calculation.viewed` |
| `POST /api/dashboard/calculations/:id/approve` | owner session | membership and calculation tenant | `ApproveCalculationRequest` | `ApproveCalculationResponse` | required | `human_review.approved`, `client_link.created` |
| `POST /api/dashboard/calculations/:id/request-clarification` | owner session | membership and calculation tenant | `RequestClarificationRequest` | `ReviewActionResponse` | required | `human_review.clarification_requested` |
| `POST /api/dashboard/calculations/:id/requires-measurement` | owner session | membership and calculation tenant | `RequiresMeasurementRequest` | `ReviewActionResponse` | required | `human_review.requires_measurement` |
| `POST /api/dashboard/calculations/:id/manual-adjustment` | owner session | membership and calculation tenant | `ManualAdjustmentRequest` | `ManualAdjustmentResponse` | required | `manual_adjustment.recorded` |
| `GET /api/dashboard/client-events` | owner session | membership | `ListClientEventsRequest` | `ListClientEventsResponse` | no | `dashboard.client_events_listed` |
| `GET /api/dashboard/analytics/summary` | owner session | membership | `AnalyticsSummaryRequest` | `AnalyticsSummaryResponse` | no | `dashboard.analytics_viewed` |
| `GET /api/dashboard/settings/readiness` | owner session | membership | none | `ReadinessResponse` | no | `settings.readiness_viewed` |
| `POST /api/dashboard/settings/price-imports` | owner session | membership | `CreatePriceImportRequest` | `CreatePriceImportResponse` | required | `price_import.created` |
| `GET /api/dashboard/settings/price-imports/:id` | owner session | membership and import tenant | none | `GetPriceImportResponse` | no | `price_import.viewed` |
| `PATCH /api/dashboard/settings/pricing-profile` | owner session | membership | `UpdatePricingProfileRequest` | `UpdatePricingProfileResponse` | required | `pricing_profile.updated` |
| `PATCH /api/dashboard/settings/autonomous-mode` | owner session | membership | `UpdateAutonomousModeRequest` | `UpdateAutonomousModeResponse` | required | `autonomous_mode.updated` |
| `POST /api/notifications/test` | owner session | membership | `TestNotificationRequest` | `TestNotificationResponse` | required | `notification.test_enqueued` |
| `POST /api/pdf` | owner session, worker | approved calculation/link tenant | `CreatePdfJobRequest` | `CreatePdfJobResponse` | required | `pdf.job_enqueued` |
| `GET /api/pdf/:jobId` | owner session, signed link, worker | membership, signed link or job tenant | none | `GetPdfJobResponse` | no | `pdf.job_viewed` |
| `GET /api/pdf-assets/:assetId/download` | owner session, signed link | membership or signed link bound asset | none | `DownloadPdfAssetResponse` | no | `pdf.downloaded` |
| `POST /api/bot/telegram/webhook` | worker | provider signature and channel binding | `BotWebhookRequest` | `BotWebhookResponse` | provider update id | `bot.webhook_received` |
| `POST /api/bot/max/webhook` | worker | provider signature and channel binding | `BotWebhookRequest` | `BotWebhookResponse` | provider update id | `bot.webhook_received` |
| `POST /api/bot/actions` | worker, owner session | signed callback token; approval requires owner auth | `BotActionRequest` | `BotActionResponse` | required | `bot.action_received`, action-specific audit |

## 6. Marketing Site Contracts

Marketing site рекламирует ProSmet как сервис. Он не является tenant runtime and не имеет доступа к клиентским сметам, прайсам или данным пилотов.

```ts
type CreateMarketingLeadRequest = {
  consent: {
    accepted: true;
    legalDocumentId: UUID;
    legalDocumentVersion: string;
  };
  contact: {
    name?: string;
    phone?: string;
    email?: string;
    company?: string;
  };
  interest: {
    vertical: "ceilings" | "other";
    sourcePage: string;
    message?: string;
  };
  utm?: Record<string, string>;
  idempotencyKey: IdempotencyKey;
};

type CreateMarketingLeadResponse = {
  marketingLeadId: UUID;
  status: "received";
};

type RecordMarketingEventRequest = {
  event:
    | "page_viewed"
    | "hero_cta_clicked"
    | "demo_requested"
    | "vertical_interest_clicked";
  sourcePage: string;
  metadata?: Record<string, string | number | boolean>;
  idempotencyKey: IdempotencyKey;
};

type RecordMarketingEventResponse = {
  eventId: UUID;
  accepted: true;
};
```

Rules:

- consent is required before phone/email/name;
- marketing payload is not sent to LLM;
- real testimonials, screenshots, prices and pilot data require architect approval;
- external CRM/analytics provider requires ArchitectInterventionRequest.

## 7. Public Intake Contracts

```ts
type CreateSessionRequest = {
  entry: {
    kind: "site_widget" | "avito" | "direct_link";
    publicTenantSlug?: string;
    entryToken?: string;
    parentUrl?: string;
    referrer?: string;
    utm?: Record<string, string>;
  };
  widget?: {
    loaderVersion?: string;
    postMessageOrigin?: string;
  };
};

type CreateSessionResponse = {
  sessionId: UUID;
  context: "public_anonymous";
  tenantPublic: {
    slug: string;
    displayName: string;
    phoneGateEnabled: boolean;
    previewRevealPolicy: "blur_totals" | "blur_prices" | "show_partial_without_final_total";
  };
  legal: {
    legalPackVersion: string;
    consentDocuments: { id: UUID; kind: string; version: string; title: string }[];
  };
  expiresAt: ISODateTime;
};

type RecordConsentRequest = {
  accepted: true;
  legalDocumentId: UUID;
  legalDocumentVersion: string;
  purpose: "lead_intake" | "phone_gate" | "client_link_unlock";
};

type RecordConsentResponse = {
  consentRecordId: UUID;
  acceptedAt: ISODateTime;
};

type CreateLeadRequest = {
  source?: {
    channel: "site" | "avito" | "manual" | "direct";
    sourceUrl?: string;
    campaign?: string;
  };
  initialRoomCount?: number;
};

type CreateLeadResponse = {
  leadId: UUID;
  dealId: UUID;
  status: "new";
  createdAt: ISODateTime;
};

type SaveContactRequest = {
  consentRecordId: UUID;
  phone?: string;
  name?: string;
  email?: string;
  preferredContact?: "phone" | "messenger" | "email";
};

type SaveContactResponse = {
  clientId: UUID;
  contactCaptured: boolean;
  phoneGateSatisfied: boolean;
};

type SaveLeadParamsRequest = {
  roomId?: UUID;
  answers: Record<string, unknown>;
  source: "form" | "chat" | "owner_manual";
};

type SaveLeadParamsResponse = {
  roomId: UUID;
  calculationInputId: UUID;
  missingFields: string[];
  assumptions: string[];
  riskFlags: string[];
  completenessScore: number;
};

type CollectParamsRequest = {
  leadId: UUID;
  conversationId?: UUID;
  message: string;
  knownParams?: Record<string, unknown>;
  consentRecordId: UUID;
};

type CollectParamsResponse = {
  conversationId: UUID;
  messageId: UUID;
  normalizedParams: Record<string, unknown>;
  missingFields: string[];
  clarificationQuestions: string[];
  assumptions: string[];
  contradictions: string[];
  riskFlags: string[];
  confidence: number;
  aiPayloadAuditId: UUID;
};
```

AI output schema validator обязан отклонить `price`, `priceRub`, `finalPrice`, `discount`, `margin`, `coefficientValue`, `estimateLineAmount`, `total` и любые производные price-поля.

## 8. Calculation And Policy Contracts

```ts
type CreatePreviewCalculationRequest = {
  leadId: UUID;
  roomId: UUID;
  calculationInputId?: UUID;
  calculationDate: ISODate;
  requestedVariants?: ("economy" | "standard" | "premium")[];
};

type PreviewLine = {
  kind: "material" | "work" | "service" | "insufficient_data";
  label: string;
  quantity?: number;
  unit?: string;
  reveal: "visible" | "blurred" | "hidden";
  amount?: MinorMoney;
  insufficientDataReason?: string;
};

type CreatePreviewCalculationResponse = {
  previewId: UUID;
  completenessStatus: CalculationCompleteness;
  completenessScore: number;
  missingBlocks: string[];
  revealPolicyApplied: string;
  variants: {
    code: "economy" | "standard" | "premium";
    label: string;
    totalReveal: "visible" | "blurred" | "partial_not_final";
    total?: MinorMoney;
    lines: PreviewLine[];
  }[];
  warnings: string[];
};

type CreateCalculationSnapshotRequest = {
  leadId: UUID;
  roomId: UUID;
  calculationInputId: UUID;
  calculationDate: ISODate;
};

type CreateCalculationSnapshotResponse = {
  calculationId: UUID;
  immutable: true;
  formulaVersion: string;
  priceBookId: UUID;
  priceBookVersion: string;
  priceBookHash: string;
  coefficientSnapshotHash: string;
  inputHash: string;
  completenessStatus: CalculationCompleteness;
  completenessScore: number;
  missingBlocks: string[];
  status: "snapshot_created";
};

type GetCalculationResponse = {
  calculationId: UUID;
  leadId: UUID;
  roomId: UUID;
  formulaVersion: string;
  priceBookVersion: string;
  completenessStatus: CalculationCompleteness;
  status: CalculationStatus;
  variants: {
    id: UUID;
    code: "economy" | "standard" | "premium";
    label: string;
    total: MinorMoney;
  }[];
  items: {
    id: UUID;
    variantId: UUID;
    kind: string;
    label: string;
    quantity?: number;
    unit?: string;
    unitPrice?: MinorMoney;
    amount?: MinorMoney;
    calculationStatus: "calculated" | "insufficient_data";
    insufficientDataReason?: string;
    sourceRef: string;
    audit: Record<string, unknown>;
  }[];
};

type RunPolicyDecisionRequest = {
  mode: "run_or_get_existing";
};

type RunPolicyDecisionResponse = {
  decisionId: UUID;
  decision: PolicyDecision;
  publicationMode?: PublicationMode;
  publishable: boolean;
  reasonCodes: string[];
  decidedAt: ISODateTime;
};
```

`POST /api/calculations` не принимает `priceBookId`, price item, coefficient value, formula body, discount или manual total из клиента. Эти значения выбирает сервер из tenant pricing profile и immutable snapshots.

## 9. Client Link And Event Contracts

```ts
type UnlockClientLinkRequest = {
  consentRecordId?: UUID;
  phone?: string;
  selectedVariantCode?: "economy" | "standard" | "premium";
};

type UnlockClientLinkResponse = {
  unlocked: boolean;
  linkStatus: "active" | "locked" | "expired" | "revoked";
  fullEstimateAvailable: boolean;
  pdf: {
    required: boolean;
    status: "not_requested" | "queued" | "ready" | "failed";
    assetId?: UUID;
    jobId?: UUID;
  };
};

type GetClientLinkResponse =
  | {
      state: "locked";
      preview: CreatePreviewCalculationResponse;
      unlockRequirements: {
        consentRequired: boolean;
        phoneRequired: boolean;
        publicationRequired: boolean;
      };
    }
  | {
      state: "published";
      publicationMode: PublicationMode;
      calculation: GetCalculationResponse;
      legalPhrase: string;
      validUntil: ISODateTime;
      pdfAssetId?: UUID;
    }
  | {
      state: "expired" | "revoked";
      safeMessage: string;
    };

type RecordClientLinkEventRequest = {
  eventType:
    | "preview_shown"
    | "phone_submitted"
    | "opened"
    | "reopened"
    | "pdf_downloaded"
    | "cta_clicked"
    | "expired_link_opened";
  eventIdempotencyKey: IdempotencyKey;
  occurredAt?: ISODateTime;
  metadata?: Record<string, unknown>;
};

type RecordClientLinkEventResponse = {
  accepted: true;
  eventId: UUID;
  duplicate: boolean;
};
```

`metadata` не содержит raw phone, name, email, address, tenant private identifiers, price snapshots или AI payload. IP и user-agent хешируются сервером.

## 10. Owner Dashboard Contracts

```ts
type SignInRequest = {
  email?: string;
  phone?: string;
  returnTo?: string;
};

type SignInResponse = {
  accepted: true;
  delivery: "magic_link" | "otp";
};

type LeadListItem = {
  id: UUID;
  sourceChannel: string;
  status: string;
  dealStatus: string;
  createdAt: ISODateTime;
  lastActivityAt: ISODateTime | null;
  contactMasked?: string;
  latestCalculationStatus?: CalculationStatus;
};

type ListLeadsRequest = PageRequest & {
  status?: string;
  sourceChannel?: string;
  createdFrom?: ISODate;
  createdTo?: ISODate;
};

type ListLeadsResponse = PageResponse<LeadListItem>;

type GetLeadRequest = {
  pii?: "masked" | "full";
  piiAccessReason?: string;
};

type GetLeadResponse = {
  lead: LeadListItem & {
    clientId?: UUID;
    contact?: { phone?: string; name?: string; email?: string };
    rooms: { id: UUID; roomType?: string; areaSqm?: number; params: Record<string, unknown> }[];
    latestCalculationId?: UUID;
    latestPolicyDecisionId?: UUID;
  };
};

type UpdateLeadStatusRequest = {
  status: string;
  reason?: string;
};

type UpdateLeadStatusResponse = {
  leadId: UUID;
  status: string;
  dealStatus: string;
  updatedAt: ISODateTime;
};

type GetDashboardCalculationResponse = GetCalculationResponse & {
  snapshotHash: string;
  auditTrail: Record<string, unknown>[];
  policyDecision?: RunPolicyDecisionResponse;
  humanReview?: {
    id: UUID;
    decision: "approve" | "request_clarification" | "requires_measurement" | "reject";
    reviewerUserId: UUID;
    reason?: string;
    createdAt: ISODateTime;
  };
};

type ApproveCalculationRequest = {
  reason?: string;
  createClientLink: boolean;
  enqueuePdf: boolean;
};

type ApproveCalculationResponse = {
  reviewId: UUID;
  decision: "approve";
  clientLinkId?: UUID;
  pdfJobId?: UUID;
};

type RequestClarificationRequest = {
  reason: string;
  missingFields: string[];
};

type RequiresMeasurementRequest = {
  reason: string;
  riskFlags: string[];
};

type ReviewActionResponse = {
  reviewId: UUID;
  calculationId: UUID;
  status: "requires_review" | "requires_measurement";
};

type ManualAdjustmentRequest = {
  reason: string;
  adjustment: {
    kind: "params_change" | "manual_discount_request" | "line_note";
    payload: Record<string, unknown>;
  };
};

type ManualAdjustmentResponse = {
  accepted: true;
  auditLogId: UUID;
  requiresNewCalculation: boolean;
  newCalculationId?: UUID;
};
```

Manual adjustment не меняет существующий immutable snapshot. Если adjustment влияет на расчетные суммы, создается новый calculation snapshot или заявка остается в review/measurement.

## 11. Settings, Analytics, PDF And Bot Contracts

```ts
type ListClientEventsRequest = PageRequest & {
  leadId?: UUID;
  eventType?: string;
  from?: ISODateTime;
  to?: ISODateTime;
};

type ListClientEventsResponse = PageResponse<{
  id: UUID;
  leadId: UUID;
  clientEstimateLinkId: UUID;
  eventType: string;
  occurredAt: ISODateTime;
  metadata: Record<string, unknown>;
}>;

type AnalyticsSummaryRequest = {
  from?: ISODate;
  to?: ISODate;
  sourceChannel?: string;
};

type AnalyticsSummaryResponse = {
  leads: number;
  previewsShown: number;
  phonesSubmitted: number;
  linksOpened: number;
  pdfDownloads: number;
  ctaClicks: number;
};

type ReadinessResponse = {
  autonomousOfferEnabled: boolean;
  priceBookReady: boolean;
  pricingProfileReady: boolean;
  formulaReady: boolean;
  legalPackReady: boolean;
  notificationChannelReady: boolean;
  blockingReasons: string[];
};

type CreatePriceImportRequest = {
  sourceFileAssetId: UUID;
  declaredFormat: "csv" | "xlsx";
  columnMapping?: Record<string, string>;
};

type CreatePriceImportResponse = {
  priceImportId: UUID;
  status: "queued" | "validating";
};

type GetPriceImportResponse = {
  priceImportId: UUID;
  status: "queued" | "validating" | "valid" | "invalid" | "applied";
  validationErrors: Record<string, unknown>[];
  resultingPriceBookId?: UUID;
};

type UpdatePricingProfileRequest = {
  priceBookId?: UUID;
  coefficientSetId?: UUID;
  markupPolicyId?: UUID;
  minimumOrderAmountMinor?: MinorUnitAmount;
  roundingPolicy?: Record<string, unknown>;
  estimateValidityDays?: number;
  measurementFeePolicy?: Record<string, unknown>;
};

type UpdatePricingProfileResponse = {
  pricingProfileId: UUID;
  status: "active" | "draft";
  readiness: ReadinessResponse;
};

type UpdateAutonomousModeRequest = {
  enabled: boolean;
  reason: string;
};

type UpdateAutonomousModeResponse = {
  autonomousOfferEnabled: boolean;
  readiness: ReadinessResponse;
};

type TestNotificationRequest = {
  channelId: UUID;
  kind: "test";
};

type TestNotificationResponse = {
  notificationId: UUID;
  status: "queued";
};

type CreatePdfJobRequest = {
  calculationId: UUID;
  clientEstimateLinkId?: UUID;
  reason: "human_approved" | "auto_published" | "owner_download";
};

type CreatePdfJobResponse = {
  jobId: UUID;
  status: "queued";
};

type GetPdfJobResponse = {
  jobId: UUID;
  status: "queued" | "running" | "ready" | "failed";
  assetId?: UUID;
  errorCode?: string;
};

type DownloadPdfAssetResponse = {
  assetId: UUID;
  contentType: "application/pdf";
  contentHash: string;
  downloadUrl?: string;
};

type BotWebhookRequest = {
  provider: "telegram" | "max";
  updateId: string;
  signature?: string;
  payload: unknown;
};

type BotWebhookResponse = {
  accepted: true;
};

type BotActionRequest = {
  signedActionToken: string;
  action: "acknowledge" | "mark_callback_needed" | "requires_measurement" | "disable_auto_publish_for_lead" | "approve";
  reason?: string;
};

type BotActionResponse = {
  accepted: boolean;
  requiresOwnerAuth?: boolean;
  dashboardUrl?: string;
};
```

Bot API не доверяет tenant из callback payload. Tenant выводится из provider binding или signed callback token. Действие `approve` допустимо только после owner auth и полного review context; иначе возвращается deep link в dashboard.

## 12. Publication And Unlock Gates

### 11.1. Publication Gates

Клиентская ссылка и PDF создаются только если выполнены все условия:

- calculation сохранен как immutable snapshot;
- snapshot содержит `formulaVersion`, `priceBookVersion`, `priceBookHash`, coefficient snapshot hash и input hash;
- consent записан;
- pricing profile, markup policy, formula registry, legal pack и notification policy готовы;
- tenant активен;
- publication source является `human_reviews.decision = approve` или `approval_policy_decisions.decision = auto_publish`;
- `auto_publish` имеет audit event и `publicationMode = full | partial`;
- partial publication явно показывает `insufficient_data` blocks и не выдает partial total за финальную полную стоимость;
- legal phrase присутствует в link/PDF;
- если `tenant_settings.pdf_required_for_publish = true`, PDF job успешно поставлен в очередь;
- owner notification поставлен в очередь или записан fallback.

Publication fail-closed:

- отсутствует snapshot или он mutable -> `CALCULATION_MUTABLE`;
- нет consent -> `CONSENT_REQUIRED`;
- включен phone-gate и нет телефона для полного раскрытия -> `PHONE_REQUIRED`;
- нет human approval и нет `auto_publish` -> `PUBLICATION_GATE_BLOCKED`;
- policy вернул `requires_review` -> `POLICY_REQUIRES_REVIEW`;
- policy вернул `requires_measurement` -> `POLICY_REQUIRES_MEASUREMENT`;
- расчет `unusable` -> `CALCULATION_UNUSABLE`;
- нет прайса/legal/pricing profile -> соответствующий readiness error;
- PDF обязателен, но job нельзя поставить -> `PDF_REQUIRED_BUT_UNAVAILABLE`.

### 11.2. Unlock Gates

Full unlock signed link выполняется только если:

- raw token валиден, не истек и не отозван;
- token hash найден в `client_estimate_links`;
- link tenant определяется из найденной строки;
- расчет опубликован через human approval или `auto_publish`;
- consent записан для текущего lead/client;
- если phone-gate включен, телефон уже записан или передан в unlock request вместе с consent;
- signed link не раскрывает `tenant_id`, internal ids, price snapshot internals и ПД других сущностей;
- событие `phone_submitted`, `opened`, `reopened` или `expired_link_opened` записывается идемпотентно.

До выполнения unlock gates endpoint возвращает `state = "locked"` и только разрешенный preview.

## 13. Idempotency Contract

Для mutating endpoints используется заголовок `Idempotency-Key` или поле `eventIdempotencyKey`.

Правила:

- scope ключа: `tenant + context actor/session/link + method + route + key`;
- повтор с тем же body возвращает прежний response без повторного side effect;
- повтор с другим body возвращает `IDEMPOTENCY_CONFLICT`;
- keys обязательны для lead/contact/params/calculation/policy/publication/PDF/notification/link events;
- worker jobs используют job id как часть idempotency scope;
- link events дополнительно имеют unique constraint на `client_estimate_link_id + event_idempotency_key`.

## 14. Error Semantics

HTTP mapping:

- `400`: `VALIDATION_FAILED`, `TENANT_AUTHORITY_REJECTED`, `AI_FORBIDDEN_FIELDS`;
- `401`: `UNAUTHENTICATED`, `TOKEN_INVALID`, `TOKEN_EXPIRED`;
- `403`: `FORBIDDEN`, `ORIGIN_NOT_ALLOWED`, `TENANT_INACTIVE`;
- `404`: `NOT_FOUND`, `TENANT_NOT_FOUND`;
- `409`: `IDEMPOTENCY_CONFLICT`, `CALCULATION_MUTABLE`, `PUBLICATION_GATE_BLOCKED`;
- `422`: `CONSENT_REQUIRED`, `PHONE_REQUIRED`, `CALCULATION_UNUSABLE`, readiness errors;
- `423`: `POLICY_REQUIRES_REVIEW`, `POLICY_REQUIRES_MEASUREMENT`, `AUTO_PUBLISH_DISABLED`;
- `429`: `RATE_LIMITED`;
- `503`: `AI_UNAVAILABLE`, `PDF_REQUIRED_BUT_UNAVAILABLE`.

Ошибки публичного и signed-link контекста не раскрывают существование tenant, lead, calculation или client, если текущий контекст не имеет права это знать.

## 15. Audit Contract

Audit events пишутся без raw PII и без secret tokens. Для чувствительных payload сохраняется hash, reason codes и entity refs.

Обязательные события:

- entry/session: `entry.resolved`, `session.created`;
- consent/contact: `consent.accepted`, `contact.submitted`;
- lead/params: `lead.created`, `params.saved`;
- AI: `ai_payload.sanitized`, `ai_payload.completed`, `ai_payload.rejected`;
- calculation: `calculation.preview_created`, `calculation.snapshot_created`;
- policy/review: `policy.decided`, `human_review.approved`, `human_review.clarification_requested`, `human_review.requires_measurement`, `manual_adjustment.recorded`;
- publication: `client_link.created`, `client_link.unlocked`, `pdf.job_enqueued`;
- analytics: `client_link.preview_shown`, `client_link.opened`, `client_link.reopened`, `client_link.pdf_downloaded`, `client_link.cta_clicked`, `client_link.expired_link_opened`;
- owner/settings: `deal.status_changed`, `price_import.created`, `pricing_profile.updated`, `autonomous_mode.updated`, `notification.test_enqueued`;
- bot/worker: `bot.webhook_received`, `bot.action_received`, `notification.sent`, `notification.failed`, `pdf.generated`, `pdf.failed`;
- PII read: отдельная запись в `pii_access_log`.
