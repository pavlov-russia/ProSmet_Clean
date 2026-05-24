# ImplementationPlan.md · ProSmet

Дата: 2026-05-23
Статус: стартовый implementation plan для AI-сотрудников
Владелец: PPM

## 1. Назначение

Этот план переводит текущий архитектурный контракт ProSmet в порядок разработки для AI-сотрудников. План не расширяет `Scope.md` и не заменяет `docs/SolutionDesign.md` или `docs/Architecture.md`.

Источник правды:

- `AGENTS.md`
- `EntryPointForTask.md`
- `docs/AI_M_MSF.md`
- `Focus.md`
- `Backlogs.md`
- `Team.yml`
- `docs/Context/2026-05-19-autonomous-mvp-feedback.md`
- `harness/build-team.md`
- `docs/SolutionDesign.md`
- `docs/Architecture.md`
- `docs/Evals/QualityGates.md`
- `docs/dev/PredictableAIWork.md`
- `docs/Evals/GateMatrix.md`
- `docs/Evals/gates.json`
- `docs/contracts/ContractManifest.json`

## 2. Scope Guardrails

- Vision шире Scope; реализация идет по Scope и текущему Solution/Architecture contract.
- Любое архитектурное отклонение фиксируется через ADR до кода.
- Любая попытка расширить MVP, сменить вертикаль, добавить production-зависимость, включить deploy или работать с реальными ПД требует вопроса архитектору.
- AI не считает деньги, не выбирает коэффициенты, не создает строки сметы с суммами и не принимает решение публикации.
- Calculation engine является pure deterministic module.
- Tenant определяется сервером, `tenantId` из клиента недоверен.
- Human review обязателен для MVP-0 и MVP-1; MVP-2 добавляет только audited deterministic `auto_publish`.

## 3. Canonical Flow

Канонический поток для MVP-1/MVP-2:

Короткая форма: `entry -> consent -> params/chat -> blurred/partial preview -> phone -> immutable calculation snapshot -> policy/human review -> full link/PDF`.

```text
entry
  -> consent
  -> params/chat
  -> blurred/partial preview
  -> phone
  -> immutable calculation snapshot
  -> policy/human review
  -> full link/PDF
  -> client analytics
  -> owner web/bot follow-up
```

Раскрытие по компонентам:

1. `entry`: сайт подрядчика, iframe widget или Avito entry URL. Tenant определяется сервером через domain/origin/signed entry token.
2. `consent`: согласие и версия legal document записываются до телефона, имени, email, адреса, голоса, файлов и свободного текста с ПД.
3. `params/chat`: виджет собирает параметры быстрыми ответами, формой или безопасным AI gateway; LLM payload не содержит ПД, денег, прайса и PDF.
4. `blurred/partial preview`: calculation service может вернуть partial estimate; UI замыливает итоговые и ценовые блоки по tenant policy и явно показывает `insufficient_data`.
5. `phone`: phone-gate требуется до полного раскрытия сметы/PDF, если включен tenant policy.
6. `immutable calculation snapshot`: сервисный слой загружает price/coefficient/formula snapshots, pure engine считает результат, snapshot сохраняется неизменяемым.
7. `policy/human review`: MVP-0/MVP-1 публикуют только после human approval. MVP-2 допускает `auto_publish` только через deterministic ApprovalPolicyService и audit.
8. `full link/PDF`: ссылка и PDF создаются только из approved или auto-published snapshot, содержат версии расчета/прайса и юридическую фразу.
9. `client analytics`: `preview_shown`, `phone_submitted`, `opened`, `reopened`, `pdf_downloaded`, `cta_clicked`, `expired_link_opened` пишутся с idempotency key.
10. `owner follow-up`: владелец видит статус, события, risk flags, next action в web-кабинете и выбранном bot/channel adapter.

## 4. Role Dependency Map

| Роль | Зависит от | Передает дальше | Контракт |
| --- | --- | --- | --- |
| AIOrchestrator | Architect, PPM, QAEngineer, dispatch plan | Все роли, Architect | Cycle proposal, approval-before-dispatch, command packets, feedback loop |
| Architect | Scope, SolutionDesign, Architecture, ADR | SolutionArchitect, PPM, QAEngineer | Инварианты, scope guardrails, решения по отклонениям |
| PPM | Architect, Team.yml, Backlogs | Все роли | Task cards, sequencing, DoD, handoff |
| SolutionArchitect | Architect, ProductAnalyst, BusinessAnalyst | BackendDeveloper, FrontendDeveloper, AIFlowDeveloper, EstimationEngineDeveloper | API, data model, RLS, integration boundaries |
| ProductAnalyst | Scope, canonical journey | FrontendDeveloper, QAEngineer | UX acceptance, metrics, value checks |
| BusinessAnalyst | Scope, legal/consent assumptions | BackendDeveloper, FrontendDeveloper, AIFlowDeveloper | Consent, lifecycle, statuses, exceptions |
| DomainAnalyst | Ceiling domain docs, pilot questions | EstimationEngineDeveloper, AIFlowDeveloper, SeniorCeilingEstimator | Parameters, edge cases, golden estimate structure |
| SeniorCeilingEstimator | DomainAnalyst, pilot/golden inputs | EstimationEngineDeveloper, SolutionArchitect, QAEngineer | Risk flags, requires_measurement reasons, expert golden review |
| DevOps | Architect, QAEngineer, repo scaffold | Все implementation roles | Environments, CI, scripts, no-secret policy |
| BackendDeveloper | SolutionArchitect, DevOps, EstimationEngineDeveloper | FrontendDeveloper, AIFlowDeveloper, QAEngineer | Route handlers, schema, services, workers, tenant context |
| EstimationEngineDeveloper | DomainAnalyst, SeniorCeilingEstimator, SolutionArchitect | BackendDeveloper, FrontendDeveloper, QAEngineer | Pure calculation module, formula registry, audit trail |
| AIFlowDeveloper | BusinessAnalyst, DomainAnalyst, BackendDeveloper | FrontendDeveloper, BackendDeveloper, QAEngineer | Safe extraction, redaction, AI audit, confidence/risk fields |
| FrontendDeveloper | ProductAnalyst, BackendDeveloper, AIFlowDeveloper | QAEngineer, ProductAnalyst, BusinessAnalyst | Widget, dashboard, review UI, client link UI |
| QAEngineer | Все роли | DevOps, Architect, PPM | Quality gates, regression reports, release readiness |

## 5. Slice Order

| Slice | Цель | Основные задачи | Primary roles | Что разблокирует |
| --- | --- | --- | --- | --- |
| Architecture prep | Свести документы, роли и implementation cards в единый контракт | `TASK-001` | Architect, SolutionArchitect, PPM | Безопасный старт кода |
| MVP-0 | Внутренний deterministic estimate под human review | `TASK-002`, `TASK-003`, `TASK-004`, старт `TASK-008`, baseline `TASK-010` | DevOps, BackendDeveloper, EstimationEngineDeveloper, FrontendDeveloper, QAEngineer | Проверяемое ядро расчета и ручная приемка |
| MVP-1 | Публичный reviewed flow: entry -> consent -> params/chat -> blurred/partial preview -> phone -> human review -> full link/PDF | `TASK-005`, `TASK-007`, `TASK-008`, `TASK-009`, расширение `TASK-010` | AIFlowDeveloper, FrontendDeveloper, BackendDeveloper, QAEngineer | Пилотный клиентский путь без auto_publish |
| MVP-2 | Autonomous offer mode через deterministic policy | `TASK-006`, финал `TASK-010` | BackendDeveloper, SolutionArchitect, QAEngineer, DevOps | `auto_publish` только после policy/audit gates |

Примечание по зависимости: `TASK-006` намеренно зависит от `TASK-009`. Сначала создается единый substrate публикации: client link, PDF, analytics и их gates. Затем `TASK-006` добавляет deterministic policy, который решает, когда использовать этот substrate через audited `auto_publish`. Так policy engine не создает второй путь публикации.

## 6. Slice Definition of Done

### 6.1. Architecture Prep

Done, когда:

- `docs/SolutionDesign.md`, `docs/Architecture.md` и `docs/Evals/QualityGates.md` не конфликтуют по tenant, AI, calculation, phone-gate, publication и analytics.
- Implementation tasks имеют роли из `Team.yml`, зависимости и handoff.
- Канонический поток зафиксирован как обязательный путь MVP-1/MVP-2.
- Открытые вопросы из backlog не блокируют MVP-0, либо отмечены как explicit blocker.
- Любое найденное архитектурное отклонение вынесено в ADR/handoff до кода.

### 6.2. MVP-0

Done, когда:

- Монорепо собрано с `apps/ceiling`, `apps/workers`, `apps/owner-bot`, `packages/core`, `packages/ui`, `packages/widget-loader`, `packages/config`.
- Strict TypeScript, test runner и базовые команды разработки работают локально без секретов и production deploy.
- Drizzle schema и RLS покрывают минимальные таблицы MVP; чувствительные таблицы имеют `tenant_id`.
- `withTenant` используется как обязательный серверный вход к данным; API игнорирует клиентский `tenantId`.
- Calculation engine считает pure deterministic result из input, formula version, price snapshot, coefficient snapshot и explicit calculation date.
- Partial estimate возвращает `insufficient_data` блоки и не выдает неполный итог как финальный.
- Golden/regression tests проверяют одинаковый результат 100 запусков подряд и неизменность старого snapshot после обновления прайса.
- Owner review UI показывает расчет, версии, warnings, missing blocks, risk flags и позволяет принять human decision.
- Публикация в MVP-0 невозможна без human approval.

### 6.3. MVP-1

Done, когда:

- Site widget и Avito entry создают anonymous session через серверное определение tenant.
- Consent записывается до ПД, а phone-gate блокирует full reveal/PDF при включенной политике tenant.
- AI gateway собирает и нормализует параметры только через sanitized payload, без ПД, денег, прайса и forbidden output fields.
- Клиент видит blurred/partial preview до телефона, затем оставляет телефон для полного раскрытия.
- Immutable calculation snapshot создается после сбора достаточных данных или как partial snapshot с явными missing blocks.
- Human review остается обязательным источником публикации.
- Client link/PDF содержат бренд, дату, версии расчета и прайса, параметры, строки, срок действия и юридическую фразу.
- Events `preview_shown`, `phone_submitted`, `opened`, `reopened`, `pdf_downloaded`, `cta_clicked` пишутся и видны владельцу.
- Browser smoke checks покрывают widget, owner review и client link на desktop/mobile.

### 6.4. MVP-2

Done, когда:

- ApprovalPolicyService является deterministic module и не вызывает LLM.
- `auto_publish` возможен только при включенном autonomous mode tenant, complete readiness, consent, phone-gate, immutable snapshot, sufficient completeness, confidence threshold, legal gates и отсутствии blocking risk flags.
- Policy decision записывается в `approval_policy_decisions` с reason codes, input hash, profile version и audit trail.
- `auto_publish` с `publicationMode = partial` явно показывает `insufficient_data` и не маскирует partial total под full total.
- Нестандартные, противоречивые, рискованные и manual-adjusted заявки уходят в `requires_review` или `requires_measurement`.
- Client link/PDF создаются только из human approval или audited `auto_publish`.
- Owner получает web/bot notification или fallback queue event.
- CI quality gates блокируют merge/release при нарушении calculation, AI, security, PDF/link, autonomous, channel или architecture gates.

### 6.5. Межslice Acceptance Checkpoint

Следующий slice не стартует автоматически после последней task card. Нужен acceptance checkpoint:

- QAEngineer сверяет evidence reports with `docs/Evals/gates.json`.
- Architect проверяет, что Scope, ADR and implementation contracts не разошлись.
- PPM обновляет `Focus.md`, `Backlogs.md` and dispatch report.
- Любой gate со статусом `failed` blocks next slice.
- Любой critical gate со статусом `not_run` требует явного решения Architect before moving on.

## 7. Task Cards

`TASK-002`...`TASK-010` are work packages, not direct implementation units. AI-сотрудники берут micro-tasks with one owner, one main artifact and explicit gates:

- `TASK-001`: architecture contract alignment.
- `TASK-002A` / `TASK-002B`: workspace baseline and app/package placeholders.
- `TASK-003A` / `TASK-003B` / `TASK-003C`: data model, tenant/RLS and PII audit.
- `TASK-004A` / `TASK-004B` / `TASK-004C`: calc contracts, ceiling adapter and golden/partial tests.
- `TASK-005A` / `TASK-005B`: AI redaction/schema guards and gateway boundary.
- `TASK-006A` / `TASK-006B`: pure approval policy and persistence/publication hook.
- `TASK-007A` / `TASK-007B`: public entry/consent and params/preview/phone-gate.
- `TASK-008A` / `TASK-008B`: owner read-only review and human decision actions.
- `TASK-009A` / `TASK-009B`: signed client link and PDF/analytics substrate.
- `TASK-010A` / `TASK-010B`: baseline QA harness and incremental quality gates.
- `TASK-011`: development-time AIOrchestrator harness, proposal/approval cycle and command packets.

Each executable task must reference `gate_ids` from `docs/Evals/gates.json` and produce `reports/task-evidence/TASK-ID.json`.

## 8. Predictability Gates

Before implementation roles start coding, run:

```bash
python3 harness/scripts/validate_predictability.py
python3 harness/scripts/agents/dispatch_tasks.py
python3 harness/scripts/ai_orchestrator.py propose
```

The predictability validator checks:

- contract manifest and JSON schemas;
- gate matrix and task `gate_ids`;
- micro-task metadata and dependency graph;
- synthetic golden estimates and stub snapshots;
- price input request protocol for real pilot price blockers;
- architect inbox protocol for human decisions and Ask First blockers;
- AIOrchestrator cycle proposal, approval-before-dispatch and command packet protocol;
- tenant A/B seed data;
- AI payload safety corpus;
- evidence reports if present.

No task may be marked done without evidence. No slice may start from unaccepted previous-slice output unless Architect records an explicit override.

If an implementation task needs real pilot price data, the assignee creates a `PriceInputRequest` in `reports/price-requests/` and stops the price-dependent part until Architect provides the input. Synthetic fixtures remain the only allowed fallback for engineering work.

If a task needs any other Ask First decision, the assignee creates an `ArchitectInterventionRequest` in `workspace/architect-inbox/requests/`. The request is visible through `python3 harness/scripts/architect_inbox.py`.

AIOrchestrator не заменяет Architect approval: он предлагает следующий управляемый цикл и выпускает command packets только после явного `approve`.

## 9. Handoff Protocol

Каждая роль завершает задачу только после:

- перечисления измененных файлов;
- указания выполненных проверок;
- записи machine-readable evidence report from task `required_reports`;
- фиксации незакрытых вопросов или blockers;
- передачи next-step роли из `handoff_to`;
- подтверждения, что Scope не расширен и чужие изменения не откатывались.

Если задача требует изменения `Scope.md`, production dependency, реальных ПД, внешнего сервиса, deploy, pricing/legal promises или деструктивной миграции, AI-сотрудник останавливается и задает вопрос архитектору.
