# EntryPointForTask.md

Это входная точка для любой новой задачи AI-сотрудника.

## 1. Перед стартом

Прочитай:

1. `AGENTS.md`
2. `CLAUDE.md`, если работа идет в Claude Code
3. `docs/AI_M_MSF.md`
4. `Focus.md`
5. `Team.yml`
6. `docs/Context/2026-05-19-autonomous-mvp-feedback.md`
7. `Scope.md`

## 2. Определи тип задачи

- Vision / Scope
- Conceptual Design
- Solution Design
- Architecture / ADR
- Autonomous offer mode
- Domain model
- Estimation engine
- AI flow
- Frontend
- Backend
- QA / eval
- DevOps

## 3. Выбери роль

Роль берется из `Team.yml` и раскрывается в `harness/build-team.md`.

## 4. Проверь границы

Если задача расширяет `Scope.md`, остановись и задай вопрос архитектору.

Если задача меняет архитектурный инвариант, создай или обнови ADR.

Если задача касается смет, проверь `docs/Domain/DeterministicEstimation.md`.

## 5. Завершение задачи

В конце работы:

- перечисли измененные файлы;
- укажи, какие проверки выполнены;
- вынеси нерешенные вопросы в `Backlogs.md`;
- если нужно, создай handoff в `docs/dev/handoffs/`.
