# Sources.md

Дата: 2026-05-19  
Назначение: зафиксировать методологические основания clean-пакета.

## 1. Канонические источники внутри clean-пакета

Дальнейшая работа AI-сотрудников ведется от этих документов:

- `AGENTS.md`;
- `CLAUDE.md`;
- `Team.yml`;
- `docs/AI_M_MSF.md`;
- `Vision.md`;
- `Scope.md`;
- `docs/ConceptualDesign.md`;
- `docs/SolutionDesign.md`;
- `docs/Architecture.md`;
- `docs/Context/2026-05-19-autonomous-mvp-feedback.md`;
- `docs/Domain/CeilingEstimateModel.md`;
- `docs/Domain/DeterministicEstimation.md`;
- `docs/Evals/QualityGates.md`;
- `docs/ADR/`.

## 2. Методологические основания

В clean-пакет заложена схема AI_M_MSF:

```text
Vision -> Scope -> Conceptual Design -> Solution Design -> tasks/handoffs -> implementation
```

## 3. Agent Harness

Принята схема:

- `AGENTS.md` — общий neutral harness для AI-агентов.
- `CLAUDE.md` — Claude Code adapter, импортирующий `AGENTS.md`.
- `.claude/settings.json` — enforceable permissions.
- `Team.yml` — список AI-сотрудников разработки.
- `harness/build-team.md` — описание ролей команды сборки проекта.

## 4. Практики инструментов

OpenAI Codex:

- использует `AGENTS.md` как проектные инструкции;
- поддерживает вложенные инструкции по папкам;
- допускает глобальный слой в домашней директории.

Anthropic Claude Code:

- использует `CLAUDE.md` или `.claude/CLAUDE.md`;
- может импортировать файлы через `@path`;
- separates memory files and settings;
- permissions и deny/ask/allow должны жить в `.claude/settings.json`.

## 5. Принятый вывод

`AGENTS.md` должен быть нейтральным и пригодным для разных AI-агентов.

Claude Code не "становится Codex", когда читает `AGENTS.md`. Он просто получает общий проектный harness через импорт в `CLAUDE.md`.

## 6. Product feedback от 2026-05-19

Обратная связь архитектора-человека зафиксирована как канонический контекст:

- `docs/Context/2026-05-19-autonomous-mvp-feedback.md`.

Эта правка уточняет, что MVP должен дойти до автономного B2C lead-to-estimate контура: сайт/Авито, телефон/согласие, уникальная ссылка, PDF, метрики открытия/скачивания и web+бот интерфейс владельца.
