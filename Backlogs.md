# Backlogs.md

Дата: 2026-05-23

## Product Backlog

- Собрать 5-10 real expert/pilot-approved golden estimates. Synthetic engineering fixtures уже добавлены и не являются реальным прайсом.
- Уточнить первый пилот и источник реального прайса. Когда это станет блокером task, AI-сотрудник должен создать `PriceInputRequest` в `reports/price-requests/`.
- Уточнить phone-gate: всегда ли телефон обязателен перед выдачей сметы или зависит от tenant.
- Зафиксировать первый клиентский выход: уникальная ссылка + PDF как обязательный комплект или ссылка с PDF по кнопке.
- Описать минимальный вход из Авито: ссылка, QR, промежуточная страница, UTM/source.
- Выбрать первый чат-канал владельца: Telegram, Max или оба.
- Уточнить минимальный legal pack для клиентской формы.
- Определить список risk flags для `auto_publish`.
- Определить порог AI confidence для autonomous offer mode.
- Проверить, нужен ли голос до первого автономного текстового пилота.
- Подготовить marketing message для сайта ProSmet: главный оффер, аудитория, CTA, ограничения обещаний.

## Architecture Backlog

- Доработать ADR-003/ADR-007 в связке human review vs autonomous offer mode.
- Подготовить отдельный ADR или appendix, если canonical flow будет меняться после пилота.
- Уточнить, когда `apps/marketing` становится ready-to-implement task, чтобы не отвлекать MVP calculation path до TASK-001/TASK-002B.
- Добавить RACI/conflict-resolution matrix для AI-команды реализации: Architect, SolutionArchitect, PPM, AIOrchestrator, QAEngineer, DomainAnalyst, SeniorCeilingEstimator, BackendDeveloper, EstimationEngineDeveloper.
- Добавить machine-readable slice acceptance reports для `architecture_prep`, `mvp_0`, `mvp_1`, `mvp_2`.

## Engineering Backlog

- Scaffold монорепо.
- После workspace baseline создать `apps/marketing` для public ProSmet site, если TASK-012B переведен из draft в ready.
- Настроить strict TypeScript.
- Настроить Drizzle и миграции.
- Реализовать `withTenant`.
- Реализовать calculation engine как pure module.
- Реализовать regression tests на golden estimates.
- Реализовать AI payload audit.
- Реализовать unique client links и event tracking.
- Реализовать approval policy service.
- Реализовать owner web notifications и первый bot adapter.
- После появления реализации подключить реальные команды вместо `future:*` in `docs/Evals/gates.json`.
- Когда real price input потребуется для pilot/calibration, обработать open `reports/price-requests/PRICE-REQUEST-*.json`.
- Обрабатывать open architect requests from `workspace/architect-inbox/requests/` через `python3 harness/scripts/architect_inbox.py`.
- Усилить evidence validation: filename/taskId match, task exists, role/owner match, all task gates covered, paths exist, passed gates have evidence.
- Добавить `--check` или `--no-write` mode в `harness/scripts/validate_predictability.py`.
- Усилить dependency closure: dependency закрыта только accepted/done status plus valid evidence report или explicit Architect override.
- Защитить `ai_orchestrator.py approve` от stale proposal через input hashes or rerun validations.
- Добавить machine-readable `ArchitectDecisionResponse` / decision ledger для закрытия `ARCH-REQUEST-*` и фиксации выбранного option, статуса, примененной правки and required follow-up.
- После workspace baseline заменить regex parsing task cards на YAML parser или зафиксировать строгий YAML subset.
- Добавить безопасный scanner reports/evidence/payload fixtures на secrets/PII/money patterns без чтения `.env`.

## Documentation Backlog

- Утвердить `Vision.md`.
- Утвердить `Scope.md`.
- Добавить PlantUML/Mermaid схемы компонентов.
- Подготовить PDF-render pipeline для Solution Design.

## Completed Architecture Prep

- Описана полная модель данных в `docs/SolutionDesign.md`.
- Добавлены API контракты MVP в `docs/contracts/API.md`.
- Добавлен расчетный contract и formula registry v1 в `docs/contracts/CalculationEngineV1.md`.
- Добавлена RLS policy matrix в `docs/contracts/DataModelRLS.md`.
- Добавлены AI gateway schemas в `docs/contracts/AIGateway.md`.
- Описан PDF/link generation и publication pipeline в `docs/contracts/PublicationPolicy.md`.
- Описан approval policy engine и `approval_policy_decisions` в `docs/contracts/PublicationPolicy.md`.
- Описана client link analytics: `opened`, `reopened`, `pdf_downloaded`, `cta_clicked`.
- Создан `docs/dev/ImplementationPlan.md`.
- Созданы task cards `TASK-001`...`TASK-011`, где `TASK-011` фиксирует AIOrchestrator harness.
- Реализованы Claude Code subagents в `.claude/agents/` для всех 14 ролей `Team.yml`.
- Реализованы Codex profiles в `.codex/agents/roles/` для всех 14 ролей `Team.yml`.
- Добавлены Python entrypoints и валидатор в `harness/scripts/agents/`.
- Добавлен auto-dispatcher `harness/scripts/agents/dispatch_tasks.py` и отчет `reports/agent-dispatch-plan.json`.
- Закрыт pre-start hardening в `docs/dev/handoffs/Handoff_05_pre-start-architecture-hardening.md`.
- Добавлен протокол прогнозируемой работы AI-сотрудников `docs/dev/PredictableAIWork.md`.
- Добавлена machine-readable gate matrix `docs/Evals/gates.json` and `docs/Evals/GateMatrix.md`.
- Добавлен contract manifest and JSON Schemas в `docs/contracts/`.
- Добавлены synthetic golden estimates, stub price/coefficient/pricing fixtures, tenant A/B seed and AI payload safety corpus.
- Wide task cards `TASK-002`...`TASK-010` переведены в work packages and decomposed into executable micro-tasks `TASK-002A`...`TASK-010B`.
- Добавлен валидатор `harness/scripts/validate_predictability.py`.
- Создан handoff `docs/dev/handoffs/Handoff_06_predictable-ai-development-harness.md`.
- Добавлен контракт `docs/contracts/PriceInputRequest.md`: AI-сотрудник обязан запросить реальный прайс через machine-readable report, когда synthetic fixtures уже недостаточны.
- Добавлен контракт `docs/contracts/ArchitectInterventionRequest.md` и локальный inbox `workspace/architect-inbox/` для всех Ask First решений.
- Добавлен скрипт `harness/scripts/architect_inbox.py` для просмотра открытых запросов.
- Добавлен AIOrchestrator с Python brain, approval-before-dispatch and command packets: `docs/contracts/AIOrchestrator.md`, `harness/scripts/ai_orchestrator.py`, `reports/orchestrator/`, `workspace/orchestrator/`.
