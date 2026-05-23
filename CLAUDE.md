@AGENTS.md

# Claude Code Adapter

Claude Code читает `CLAUDE.md` или `.claude/CLAUDE.md`. Общие правила проекта находятся в `AGENTS.md` и импортируются строкой `@AGENTS.md` выше.

Важно: если в общих правилах упоминаются разные coding agents, Claude должен применять смысл правила к себе. `AGENTS.md` не является "инструкцией для Codex внутри Claude"; это общий проектный harness.

## Memory Discipline

- Держи этот файл компактным. Детальный продуктовый контекст находится в `Vision.md`, `Scope.md` и `docs/`.
- Если правило относится только к части проекта, добавляй его в `.claude/rules/`, а не раздувай `CLAUDE.md`.
- Если правило является многошаговой процедурой, оформи его как skill в `harness/skills/`.
- Если правило должно быть технически enforced, добавляй его в `.claude/settings.json`, потому что `CLAUDE.md` является контекстом, а не системой безопасности.

## Claude Workflow

- Для задач с несколькими шагами веди todo и обновляй статусы.
- Перед изменением Scope, архитектуры БД, AI-шлюза, RLS, биллинга или деплоя сначала покажи план.
- Используй subagents только для конкретных ограниченных задач, когда это явно разрешено текущей средой и задачей.
- После нетривиальной правки запускай релевантную проверку или честно фиксируй, что проверка не запускалась.
- Если задача передается subagent, передавай ссылку на `Team.yml`, `harness/build-team.md` и конкретный AI_M_MSF-документ.

## Claude Paths

- Project settings: `.claude/settings.json`.
- Project subagents: `.claude/agents/`.
- Path-scoped rules: `.claude/rules/`.
- Local personal memory, if needed: `CLAUDE.local.md` and it must stay out of git.

## Claude Permissions

Смотри `.claude/settings.json`. Этот файл должен запрещать чтение секретов, опасные команды, автодеплой без подтверждения и работу с credential-файлами.
