# Harness

Локальный harness управляет AI-командой разработки.

Он не является частью runtime-продукта. Его задача:

- хранить registry AI-сотрудников;
- проверять, что роли и task cards согласованы;
- строить dispatch plan;
- выпускать command packets после approval;
- показывать inbox запросов человеку-архитектору.

## Основные команды

```bash
python3 harness/scripts/validate_template.py
python3 harness/scripts/agents/validate_agent_profiles.py
python3 harness/scripts/agents/dispatch_tasks.py
python3 harness/scripts/architect_inbox.py
python3 harness/scripts/ai_orchestrator.py propose
```

Approval цикла:

```bash
python3 harness/scripts/ai_orchestrator.py approve --cycle reports/orchestrator/latest-cycle.json --approved-by Architect --decision-note "approved next AI employee cycle"
```

## Где редактировать сотрудников

Основной источник:

```text
Team.yml
```

Python registry:

```text
harness/scripts/agents/_agent_common.py
```

Если добавил роль, добавь:

- запись в `Team.yml`;
- запись в `_agent_common.py`;
- role entrypoint в `harness/scripts/agents/`;
- при необходимости профиль в `.codex/agents/roles/` or `.claude/agents/`.

