# ProSmet AI Employees Scripts

Дата: 2026-05-23  
Статус: рабочий harness AI-сотрудников

## Назначение

Эта папка содержит единый registry AI-сотрудников ProSmet и Python entrypoints для каждой роли из `Team.yml`.

Скрипты не читают `.env`, credential-файлы и не ходят в сеть. Они дают role summary, task context, стек, запреты, quality gates и machine-readable JSON для Claude Code/Codex workflow.

## Основные файлы

- `_agent_common.py` — единый registry, soul, stack, docs, contracts, forbidden и gates всех ролей.
- `generate_agent_assets.py` — генерирует `.claude/agents/*.md`, `.codex/agents/roles/*/profile.md`, shared Codex protocol и role scripts.
- `dispatch_tasks.py` — читает `tasks/TASK-*.yml`, проверяет dependencies, связывает задачи с Claude/Codex profiles и строит execution waves.
- `validate_agent_profiles.py` — проверяет, что все роли реализованы для Claude/Codex, helpers запускаются, task cards валидны, dependency graph без циклов.
- `agent_registry.json` — machine-readable индекс профилей.

Соседний скрипт `harness/scripts/validate_predictability.py` проверяет слой прогнозируемости: contract manifest, JSON schemas, gate matrix, micro-task metadata, synthetic golden estimates, tenant seed data and AI payload safety corpus.
Соседний скрипт `harness/scripts/ai_orchestrator.py` управляет approved orchestration cycle and command packets поверх dispatcher.

## Роли

Каждая роль имеет отдельный скрипт:

- `architect.py`
- `ai_orchestrator_role.py`
- `product_analyst.py`
- `business_analyst.py`
- `domain_analyst.py`
- `senior_ceiling_estimator.py`
- `solution_architect.py`
- `estimation_engineer.py`
- `backend_developer.py`
- `frontend_developer.py`
- `ai_flow_engineer.py`
- `qa_engineer.py`
- `devops.py`
- `ppm.py`

Пример:

```bash
python3 harness/scripts/agents/backend_developer.py
python3 harness/scripts/agents/backend_developer.py --json
python3 harness/scripts/agents/dispatch_tasks.py
python3 harness/scripts/agents/dispatch_tasks.py --completed TASK-001 --completed TASK-002
python3 harness/scripts/agents/validate_agent_profiles.py
python3 harness/scripts/validate_predictability.py
```

## Правило изменения

Правь сначала `_agent_common.py`, затем запускай:

```bash
python3 harness/scripts/agents/generate_agent_assets.py
python3 harness/scripts/agents/validate_agent_profiles.py
```
