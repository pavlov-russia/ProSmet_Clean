# Predictable AI Work Protocol

Дата: 2026-05-23
Статус: обязательный протокол управляемой разработки AI-сотрудниками

## 1. Цель

Этот документ делает работу AI-сотрудников разработки воспроизводимой: задача должна иметь малый размер, машинно-проверяемые входы, явные gates, evidence-отчет и стопор между slices.

Протокол не расширяет `Scope.md`. Он уточняет, как выполнять уже принятый implementation plan.

## 2. Единица работы

AI-сотрудник берет не широкий work package, а micro-task.

Micro-task имеет:

- один `owner`;
- один основной артефакт;
- один маленький write scope;
- явные `dependencies`;
- `gate_ids` из `docs/Evals/gates.json`;
- `required_evidence`;
- `required_reports`;
- проверяемый `acceptance`.

Карточки `TASK-002`...`TASK-010` считаются work packages. Исполняемые карточки имеют суффикс, например `TASK-004A`.

## 3. Stop Rules

AI-сотрудник останавливается до кода, если:

- task card не содержит `slice`, `work_package`, `gate_ids`, `required_evidence`, `required_reports` и `acceptance`;
- хотя бы один `gate_id` отсутствует в `docs/Evals/gates.json`;
- нужный fixture/schema отсутствует;
- dependency не закрыта evidence-отчетом или explicit override архитектора;
- задача требует изменения Scope, production dependency, реальных ПД, реального прайса, deploy или внешнего сервиса.

Если блокер требует решения архитектора, AI-сотрудник создает `ArchitectInterventionRequest` в `workspace/architect-inbox/requests/` по контракту `docs/contracts/ArchitectInterventionRequest.md` и явно пишет в handoff/final: "Нужен ввод архитектора: architect intervention request создан".

Если блокер — реальный прайс, AI-сотрудник не ограничивается текстовым вопросом. Он создает `PriceInputRequest` в `reports/price-requests/` по контракту `docs/contracts/PriceInputRequest.md` и явно пишет в handoff/final: "Нужен ввод архитектора: real price input request создан".

## 4. Evidence First

Задача считается завершенной только после evidence-отчета.

Отчет хранится в:

```text
reports/task-evidence/TASK-ID.json
```

Формат описан в `docs/contracts/AgentTaskEvidence.md` и JSON Schema `docs/contracts/schemas/agent-task-evidence-v1.schema.json`.

Если проверка не запускалась, ее нельзя записывать как passed. Она записывается как `not_run` с причиной.

## 5. Slice Gates

Переход между slices разрешен только после acceptance summary:

- `Architecture prep -> MVP-0`: Architect + QAEngineer подтверждают contract alignment, gate matrix, micro-task graph и synthetic fixtures.
- `MVP-0 -> MVP-1`: QAEngineer подтверждает deterministic calculation, RLS/tenant isolation, human review и baseline CI gates.
- `MVP-1 -> MVP-2`: QAEngineer подтверждает AI payload safety, phone-gate, human-reviewed publication, link/PDF analytics.
- `MVP-2 -> pilot`: Architect подтверждает real-price/legal/PII readiness отдельно от synthetic engineering fixtures.

## 6. Machine-Checkable Inputs

Минимальный набор перед кодом:

- `docs/contracts/ContractManifest.json`;
- JSON Schemas в `docs/contracts/schemas/`;
- `docs/Evals/gates.json`;
- synthetic golden estimates в `fixtures/golden-estimates/`;
- synthetic price/coefficient/pricing fixtures;
- tenant A/B seed data в `fixtures/seeds/tenant-ab.json`;
- AI payload safety corpus в `fixtures/ai-gateway/`.

## 7. Architect Inbox Protocol

AI-сотрудники отправляют запросы тебе через локальный inbox:

```text
workspace/architect-inbox/requests/
```

Ты смотришь inbox командой:

```bash
python3 harness/scripts/architect_inbox.py
```

В inbox попадают решения, которые нельзя принимать автономно: Scope, ADR, production dependency, legal promise, destructive migration, deploy/publish, external service, real PII, pilot data, policy thresholds, risk flags and slice acceptance overrides.

Каждый request обязан указывать:

- что заблокировано;
- может ли агент продолжать независимую часть;
- варианты решения and tradeoffs;
- recommended option, если он есть;
- нужен ли ADR после ответа;
- next action for Architect.

## 7.1. AI Orchestrator Protocol

AIOrchestrator является development-time control plane для AI-команды. Он не является runtime-агентом продукта.

Мозг оркестратора:

```bash
python3 harness/scripts/ai_orchestrator.py propose
python3 harness/scripts/ai_orchestrator.py approve --cycle reports/orchestrator/latest-cycle.json --approved-by Architect
python3 harness/scripts/ai_orchestrator.py status
```

Правило согласия:

- `propose` только строит dry-run cycle report;
- command packets для AI-сотрудников появляются только после `approve`;
- `approve` повторно проверяет Architect Inbox и блокируется, если появился новый blocking request или price request без synthetic fallback;
- approval пишет решение в `workspace/orchestrator/approvals/`;
- command packets пишутся в `workspace/orchestrator/outbox/`;
- AI-сотрудник после command packet обязан создать свой `reports/task-evidence/TASK-ID.json`.

Orchestrator может предлагать next task/wave, подсвечивать blockers, failed checks, open inbox, missing evidence and plan corrections. Он не может сам менять `Scope.md`, task cards, deploy, external services, production dependencies, real PII или real price flow. Такие решения идут через Architect Inbox или PriceInputRequest.

## 8. Real Price Input Protocol

Synthetic fixtures are enough for engineering tasks until a task explicitly needs pilot-ready price data. When real price data becomes necessary, AI-сотрудник обязан:

- остановить зависимую часть работы;
- создать `reports/price-requests/PRICE-REQUEST-YYYYMMDD-TASK-ID.json`;
- указать, какие именно inputs нужны: price book, coefficients, minimum order, rounding, markup, discount policy, import mapping or expert-approved golden totals;
- отметить `doNotSendToLlm = true`;
- продолжать только независимую работу на synthetic fixtures;
- уведомить архитектора в handoff/final.

AI-сотрудник не может:

- придумать реальный прайс;
- заменить real price input market guess;
- отправить прайс в LLM prompt;
- считать pilot-ready golden estimates на synthetic fixtures.

## 9. Local Checks

Перед стартом implementation роли запускают:

```bash
python3 harness/scripts/agents/validate_agent_profiles.py
python3 harness/scripts/validate_predictability.py
python3 harness/scripts/agents/dispatch_tasks.py
python3 harness/scripts/architect_inbox.py
python3 harness/scripts/ai_orchestrator.py propose
```

Эти проверки не читают `.env`, не ходят в сеть и не используют реальные ПД.
