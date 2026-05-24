# Handoff 03 · AI Employees Implemented

Тип документа: handoff  
Дата: 2026-05-23  
Автор / роль: Codex / Architect + PPM coordinator  
Родительский документ: `Team.yml`, `harness/build-team.md`  
Родительская задача: реализация AI-сотрудников под Claude Code и Codex  
Цель ветки: создать полноценный рабочий слой AI-сотрудников с soul, стеком, запретами, task protocol, Claude/Codex профилями и Python entrypoints.

## Зависимости

- `AGENTS.md`
- `Team.yml`
- `harness/build-team.md`
- `docs/dev/ImplementationPlan.md`
- `docs/contracts/`
- `tasks/TASK-001`...`TASK-010`

## Что сделано

- Создан единый registry ролей: `harness/scripts/agents/_agent_common.py`.
- Создан генератор: `harness/scripts/agents/generate_agent_assets.py`.
- Создан валидатор: `harness/scripts/agents/validate_agent_profiles.py`.
- Созданы Python entrypoints для 13 ролей:
  - `architect.py`
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
- Сгенерированы Claude Code subagents в `.claude/agents/`.
- Сгенерированы Codex profiles в `.codex/agents/roles/`.
- Сгенерированы shared Codex protocols в `.codex/agents/_shared/`.
- Сгенерированы machine-readable registries:
  - `harness/scripts/agents/agent_registry.json`
  - `.codex/agents/agent-registry.json`
- Записан validation report: `reports/agent-profiles-validation.json`.

## Soul и стек

Каждый AI-сотрудник получил:

- индивидуальную `Soul`;
- role mission;
- canonical flow;
- primary docs;
- implementation contracts;
- stack and skills;
- owns;
- forbidden;
- quality gates;
- outputs;
- default task cards;
- handoff protocol.

## Quality Gates

- Все роли из `Team.yml` покрыты registry.
- Все роли имеют Claude Code profile.
- Все роли имеют Codex profile.
- Все роли имеют Python helper.
- Helper scripts поддерживают `--help`.
- Task cards имеют валидные роли и acyclic dependency graph.
- Запреты на `.env/credentials`, client tenant authority, PII/money to LLM, LLM pricing и publication bypass присутствуют в профилях.

## Проверки

- `python3 harness/scripts/agents/generate_agent_assets.py` — успешно.
- `python3 harness/scripts/agents/validate_agent_profiles.py` — `pass`.

## Что осталось

- При изменении ролей править сначала `harness/scripts/agents/_agent_common.py`, затем запускать generator и validator.
- Если появится нативный формат Codex agent profiles с другой схемой, адаптировать генератор, не меняя role registry.

## Следующий исполнитель

PPM может запускать AI-сотрудников по `TASK-001`...`TASK-010`. DevOps начинает `TASK-002`, BackendDeveloper и EstimationEngineDeveloper готовятся к `TASK-003` и `TASK-004`.

