# Harness Scripts

## Scripts

- `validate_template.py` — проверяет базовую структуру шаблона.
- `architect_inbox.py` — показывает запросы к человеку-архитектору.
- `ai_orchestrator.py` — локальный orchestrator: proposal -> approval -> command packets.
- `agents/_agent_common.py` — registry универсальных AI-сотрудников.
- `agents/<role>.py` — Python entrypoint конкретного сотрудника.
- `agents/validate_agent_profiles.py` — проверяет, что сотрудники и task cards согласованы.
- `agents/dispatch_tasks.py` — строит план задач по dependencies.
- `agents/generate_agent_assets.py` — генерирует базовые Codex/Claude профили из registry.

## Правило

Скрипты не читают `.env`, не ходят в сеть, не делают deploy и не запускают внешних AI-агентов.

