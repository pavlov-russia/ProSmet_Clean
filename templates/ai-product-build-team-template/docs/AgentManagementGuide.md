# Agent Management Guide

Как управлять AI-сотрудниками в новом проекте.

## Где список сотрудников

Главный файл:

```text
Team.yml
```

Если ты только начал проект, скопируй:

```text
Team.template.yml -> Team.yml
```

## Где Python-сотрудники

Registry:

```text
harness/scripts/agents/_agent_common.py
```

Там у каждого сотрудника есть:

- `soul` — рабочий характер роли;
- `mission` — зачем роль существует;
- `owns` — за что отвечает;
- `outputs` — что должна выдавать.

Entry points:

```text
harness/scripts/agents/architect.py
harness/scripts/agents/product_analyst.py
harness/scripts/agents/backend_developer.py
...
```

Проверить роль:

```bash
python3 harness/scripts/agents/architect.py --json
```

## Как проверить всю команду

```bash
python3 harness/scripts/agents/validate_agent_profiles.py
```

## Как добавить нового сотрудника

1. Добавь роль в `Team.yml`.
2. Добавь роль в `ROLE_PROFILES` внутри `harness/scripts/agents/_agent_common.py`.
3. Заполни `soul`, `mission`, `owns`, `outputs`.
4. Создай entrypoint:

```text
harness/scripts/agents/new_role.py
```

5. Добавь задачу или gates, где эта роль нужна.
6. Запусти:

```bash
python3 harness/scripts/agents/validate_agent_profiles.py
```

Подробнее про `soul`: `docs/AgentSouls.md`.

## Как сгенерировать Codex/Claude профили

```bash
python3 harness/scripts/agents/generate_agent_assets.py
```

Скрипт создаст:

```text
.codex/agents/roles/<Role>/profile.md
.claude/agents/<role-slug>.md
```

## Как запустить процесс

```bash
python3 harness/scripts/agents/dispatch_tasks.py
python3 harness/scripts/ai_orchestrator.py propose
```

После approval появятся command packets:

```text
workspace/orchestrator/outbox/
```
