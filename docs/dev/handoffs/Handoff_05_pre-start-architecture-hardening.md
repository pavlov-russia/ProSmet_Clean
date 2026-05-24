# Handoff 05 · Pre-Start Architecture Hardening

Тип документа: handoff
Дата: 2026-05-23
Автор / роль: Codex / Architect + PPM
Родительский документ: `AGENTS.md`, `Team.yml`, `tasks/TASK-*.yml`, `harness/scripts/agents/`
Родительская задача: финальная доработка architecture/agent harness перед стартом разработки
Цель ветки: закрыть замечания Claude Code и субагентов по готовности AI-сотрудников, task sequencing и autonomous MVP context.

## Основание

Claude Code подтвердил базовую готовность agent harness:

- 13/13 ролей соответствуют `Team.yml`.
- 10/10 task cards имеют роли и зависимости.
- Граф зависимостей ацикличный.
- Referenced docs существуют.
- Профили имеют `Soul`, `Mission`, `Canonical Flow`, `Primary Docs`, `Implementation Contracts`, `Stack`, `Owns`, `Forbidden`, `Quality Gates`, `Outputs`, `Task Cards`, `Handoff`.

После этого выполнен дополнительный review двумя субагентами:

- Architect review: проверил архитектурные blockers, dependency rationale и MVP autonomous context.
- Harness/dispatch review: проверил reproducibility, task dispatch semantics и legacy QA alias.

## Что усилено

- `docs/Context/2026-05-19-autonomous-mvp-feedback.md` добавлен в обязательный base read всех Claude/Codex ролей.
- `docs/AI_M_MSF.md` добавлен в обязательный base read всех Claude/Codex ролей.
- `docs/dev/ImplementationPlan.md` и `docs/contracts/README.md` явно требуют читать autonomous context перед task card и implementation contracts.
- Legacy-дубликат `.claude/agents/qa-evaluator.md` удален; канонический QA employee теперь только `qa-engineer` / `QAEngineer`.
- Validator теперь fail-ит, если legacy `qa-evaluator.md` снова появится.
- Validator теперь проверяет presence autonomous context doc во всех Claude/Codex профилях.
- Dispatcher больше не считает `blocked` и `draft` workable статусами.
- Dispatcher добавляет в task binding:
  - `launch_owner`;
  - `advisory_roles`;
  - `related_profile_tasks`;
  - полный `must_read`;
  - конкретный `dispatch_prompt`.
- Dispatcher добавляет в plan:
  - `wave_reason`;
  - `unlocks`;
  - `blocked_by_status`.
- Execution waves теперь не пропускают dependency-задачи с non-workable статусом.
- `TASK-006` получил dependency note: policy engine использует готовый publication substrate из `TASK-009` и не создает второй путь link/PDF.
- `TASK-009` получил зеркальную dependency note: он не зависит от `TASK-006`, но обязан оставить hooks для audited `auto_publish`.
- `docs/dev/ImplementationPlan.md` объясняет, почему `TASK-006` намеренно идет после `TASK-009`.

## Текущий стартовый порядок

На чистом наборе task cards доступна только:

1. `TASK-001` -> `Architect`

После acceptance `TASK-001` и `TASK-002` dispatcher показывает:

1. `TASK-003` -> `BackendDeveloper`
2. `TASK-010` -> `QAEngineer`

Полные execution waves:

1. `TASK-001:Architect`
2. `TASK-002:DevOps`
3. `TASK-003:BackendDeveloper`, `TASK-010:QAEngineer`
4. `TASK-004:EstimationEngineDeveloper`
5. `TASK-005:AIFlowDeveloper`, `TASK-008:FrontendDeveloper`
6. `TASK-007:FrontendDeveloper`, `TASK-009:BackendDeveloper`
7. `TASK-006:BackendDeveloper`

## Проверки

- `python3 harness/scripts/agents/generate_agent_assets.py` — успешно.
- `python3 harness/scripts/agents/validate_agent_profiles.py` — успешно.
- `python3 harness/scripts/agents/dispatch_tasks.py` — успешно.
- `python3 harness/scripts/agents/dispatch_tasks.py --completed TASK-001 --completed TASK-002` — успешно.
- `find .claude/agents -maxdepth 1 -type f -name 'qa-evaluator.md' -print` — пустой вывод, legacy duplicate отсутствует.
- `rg -n "docs/Context/2026-05-19-autonomous-mvp-feedback.md|docs/AI_M_MSF.md" .claude/agents .codex/agents/roles` — документы найдены во всех профилях.

## Safety

- Scope не расширялся.
- `Vision.md`, `Scope.md`, `docs/ConceptualDesign.md` не изменялись в этой hardening-ветке.
- `.env`, credentials и внешние источники не читались.
- Dispatcher остается dry-run layer: не spawn-ит сотрудников, не ходит в сеть, не меняет task cards сам.

## Следующий исполнитель

Architect берет `TASK-001` для формальной acceptance архитектурного контракта. После этого PPM/DevOps запускают `TASK-002` по dispatch plan.
