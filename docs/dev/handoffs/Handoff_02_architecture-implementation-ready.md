# Handoff 02 · Architecture Implementation Ready

Тип документа: handoff  
Дата: 2026-05-23  
Автор / роль: Codex / Architect + PPM coordinator  
Родительский документ: `docs/Architecture.md`, `docs/SolutionDesign.md`  
Родительская задача: architecture prep по запросу архитектора  
Цель ветки: довести архитектуру до состояния, где AI-сотрудники могут стартовать реализацию по контрактам и task cards.

## Зависимости

- `AGENTS.md`
- `Scope.md`
- `Team.yml`
- `docs/SolutionDesign.md`
- `docs/Architecture.md`
- `docs/Evals/QualityGates.md`
- `docs/contracts/`
- `docs/dev/ImplementationPlan.md`
- `tasks/TASK-001`...`TASK-010`

## Что сделано

- Подключены subagent-ы для параллельной подготовки контрактов API/RLS, calculation/AI/policy и implementation plan/task cards.
- Зафиксирован единый canonical flow: `entry -> consent -> params/chat -> blurred/partial preview -> phone -> immutable calculation snapshot -> policy/human review -> full link/PDF`.
- Добавлены implementation contracts:
  - `docs/contracts/API.md`
  - `docs/contracts/DataModelRLS.md`
  - `docs/contracts/CalculationEngineV1.md`
  - `docs/contracts/AIGateway.md`
  - `docs/contracts/PublicationPolicy.md`
  - `docs/contracts/README.md`
- Добавлен стартовый план реализации `docs/dev/ImplementationPlan.md`.
- Созданы task cards `TASK-001`...`TASK-010` для ролей из `Team.yml`.
- Обновлены `Focus.md`, `EntryPointForTask.md`, `README.md`, `Backlogs.md`, `docs/SolutionDesign.md`, `docs/Architecture.md`, `harness/build-team.md`.

## Что осталось

- Принять `TASK-001` как финальную архитектурную приемку prep-slice.
- Собрать 5-10 golden estimates от эксперта или пилота.
- Уточнить первый пилот, источник реального прайса, legal pack и первый bot-канал.
- Запустить реализацию с `TASK-002`, `TASK-003`, `TASK-004`.
- Доработать ADR-003/ADR-007, если архитектор хочет отдельный документ связки human review vs autonomous mode поверх текущих контрактов.

## Quality Gates

- Canonical flow указан в `Focus.md`, `harness/build-team.md`, `docs/SolutionDesign.md`, `docs/dev/ImplementationPlan.md`, `docs/contracts/README.md`.
- Контракты не разрешают LLM считать деньги, видеть прайсы или принимать publication decision.
- RLS/tenant isolation contract запрещает доверять `tenantId` из клиента.
- Publication contract fail-closed и требует human approval или audited `auto_publish`.
- Task cards содержат role, owner, source docs, goal, outputs, constraints, forbidden, quality gates, dependencies и handoff.

## Следующий исполнитель

PPM запускает `TASK-001-architecture-contract-alignment.yml`, затем DevOps берет `TASK-002-monorepo-scaffold.yml`.

