# Handoff 04 · Agent Auto Dispatcher

Тип документа: handoff  
Дата: 2026-05-23  
Автор / роль: Codex / PPM + Architect  
Родительский документ: `tasks/TASK-*.yml`, `Team.yml`, `harness/scripts/agents/`  
Родительская задача: автоматическое подключение AI-сотрудников к работе  
Цель ветки: реализовать диспетчер, который читает task cards, проверяет dependencies и связывает задачи с Claude/Codex профилями и Python helper-ами.

## Что сделано

- Добавлен `harness/scripts/agents/dispatch_tasks.py`.
- Диспетчер читает `tasks/TASK-*.yml`.
- Диспетчер строит:
  - `available_now`;
  - `execution_waves`;
  - `blocked_by_dependencies`;
  - `assignments_by_role`;
  - привязку task -> role -> Claude profile -> Codex profile -> Python helper;
  - `dispatch_prompt` для запуска сотрудника.
- Диспетчер пишет отчет `reports/agent-dispatch-plan.json`.
- `validate_agent_profiles.py` теперь проверяет, что dispatch plan генерируется.
- Обновлены README/Focus/Backlogs/harness scripts docs.

## Проверки

- `python3 harness/scripts/agents/dispatch_tasks.py` — успешно.
- `python3 harness/scripts/agents/dispatch_tasks.py --completed TASK-001 --completed TASK-002` — успешно.
- `python3 harness/scripts/agents/validate_agent_profiles.py` — должен проходить после этой ветки.

## Текущий план подключения

На чистом наборе task cards доступен:

- `TASK-001` -> `Architect`

Полные execution waves:

1. `TASK-001:Architect`
2. `TASK-002:DevOps`
3. `TASK-003:BackendDeveloper`, `TASK-010:QAEngineer`
4. `TASK-004:EstimationEngineDeveloper`
5. `TASK-005:AIFlowDeveloper`, `TASK-008:FrontendDeveloper`
6. `TASK-007:FrontendDeveloper`, `TASK-009:BackendDeveloper`
7. `TASK-006:BackendDeveloper`

## Safety

Dispatcher является dry-run orchestration layer:

- не spawn-ит агентов сам;
- не читает `.env` или credentials;
- не ходит в сеть;
- не меняет task cards;
- только строит план подключения и отчет.

## Следующий исполнитель

PPM запускает `dispatch_tasks.py`, затем Architect берет `TASK-001`.

