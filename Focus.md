# Focus.md

Дата: 2026-05-23
Текущий фокус: перейти от архитектурного clean-пакета к реализации по task cards AI-сотрудников.

## Сейчас

- Канонический клиентский путь зафиксирован как `entry -> consent -> params/chat -> blurred/partial preview -> phone -> immutable calculation snapshot -> policy/human review -> full link/PDF`.
- `docs/SolutionDesign.md` и `docs/Architecture.md` связаны с исполняемыми контрактами `docs/contracts/`.
- Добавлены контракты API, RLS/data model, calculation engine v1, AI gateway и publication policy.
- Добавлен `docs/dev/ImplementationPlan.md` со slices Architecture Prep, MVP-0, MVP-1 и MVP-2.
- Созданы task cards `TASK-001`...`TASK-011` для старта работы ролей из `Team.yml`, где `TASK-011` фиксирует AIOrchestrator harness.
- Реализованы 14 AI-сотрудников для Claude Code и Codex, включая AIOrchestrator, soul, stack, task protocol и Python entrypoints.
- Реализован auto-dispatcher, который подключает задачи к AI-сотрудникам и строит execution waves.
- Реализован AIOrchestrator с Python brain: proposal -> architect approval -> command packets -> evidence -> next cycle.
- Закрыт pre-start hardening после Claude/subagent review: `qa-evaluator` удален, autonomous context обязателен во всех профилях, dispatcher учитывает только workable статусы.
- Добавлен predictability слой для AI-сотрудников: `docs/dev/PredictableAIWork.md`, `docs/Evals/gates.json`, `docs/contracts/ContractManifest.json`, JSON Schemas, synthetic golden fixtures, tenant A/B seed, AI payload corpus and `harness/scripts/validate_predictability.py`.
- `TASK-002`...`TASK-010` переведены в work packages; исполняемые карточки раздроблены на `TASK-002A`...`TASK-010B`.
- Добавлен протокол `PriceInputRequest`: когда AI-сотруднику потребуется реальный прайс, он создает запрос в `reports/price-requests/` и явно уведомляет архитектора.
- Добавлен `Architect Inbox`: AI-сотрудники создают запросы вмешательства в `workspace/architect-inbox/requests/`, просмотр через `python3 harness/scripts/architect_inbox.py`.
- Зафиксирован контекст review архитектуры AI-команды реализации в `docs/Context/2026-05-23-ai-team-implementation-architecture.md`: сильные стороны harness, риски evidence self-attestation, dependency closure, stale approval, regex YAML parsing, slice acceptance and RACI.

## Ближайший следующий шаг

Запустить:

```bash
python3 harness/scripts/validate_predictability.py
python3 harness/scripts/agents/dispatch_tasks.py
python3 harness/scripts/ai_orchestrator.py propose
```

Затем взять `TASK-001-architecture-contract-alignment.yml` как финальную приемку prep-slice. После закрытия `TASK-001` переходить к micro-tasks:

- `TASK-002A-workspace-baseline.yml`;
- `TASK-002B-app-package-placeholders.yml`;
- `TASK-010A-baseline-qa-harness.yml`;
- затем `TASK-003A` / `TASK-004A` по dependency graph dispatcher.

Параллельно архитектору нужно закрыть продуктовые решения по первому пилоту, реальному прайсу, legal pack, первому bot-каналу and real expert-approved golden estimates. Synthetic fixtures уже есть только как engineering oracle. Если реальный прайс станет блокером конкретной task, ждем `PriceInputRequest` от AI-сотрудника.

Открытые запросы архитектору проверять командой:

```bash
python3 harness/scripts/architect_inbox.py
```

Если перед MVP-0 нужно усилить AI-team harness, использовать prompt из `docs/Context/2026-05-23-ai-team-implementation-architecture.md` и держать доработку узкой: evidence hardening, stale approval protection, dependency closure and read-only validation.
