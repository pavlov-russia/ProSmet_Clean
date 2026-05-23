# HarnessMethodology.md

Дата: 2026-05-19  
Назначение: как формировать AI-harness проекта и почему `AGENTS.md` + `CLAUDE.md` работают вместе.

## 1. Что такое harness

Harness — это рабочая обвязка AI-агента.

Он отвечает не за описание продукта, а за поведение агента:

- роль;
- источники истины;
- порядок чтения документов;
- разрешенные действия;
- действия, где нужно спросить;
- запреты;
- quality gates;
- маршруты scripts / skills / subagents;
- правила handoff.

Формула:

```text
Vision отвечает: зачем и куда идем.
Scope отвечает: что делаем сейчас и что отрезаем.
Conceptual Design отвечает: как решение выглядит на уровне ролей, потоков и сущностей.
Solution Design отвечает: как компоненты работают и взаимодействуют.
Harness отвечает: как AI-агент обязан работать с проектом.
```

## 2. Почему `AGENTS.md` и `CLAUDE.md` оба нужны

`AGENTS.md` — общий проектный harness.

Он написан нейтрально, чтобы им могли пользоваться разные coding agents.

`CLAUDE.md` — адаптер Claude Code.

Claude Code читает `CLAUDE.md`, а внутри него стоит:

```md
@AGENTS.md
```

Это означает: Claude подтягивает общий harness и добавляет только Claude-специфику.

Практический смысл:

- правила не дублируются в двух файлах;
- Claude получает те же проектные инварианты, что и другие агенты;
- Claude-specific settings живут рядом, но отдельно;
- если меняется общее правило, достаточно обновить `AGENTS.md`.

## 3. Что класть в `AGENTS.md`

В `AGENTS.md`:

- роль агента;
- контекстная маршрутизация;
- operating principles;
- allowed actions;
- ask first;
- forbidden actions;
- quality gates;
- communication rules.

Не класть:

- длинное описание продукта;
- весь Vision;
- весь Scope;
- большие процедуры;
- секреты;
- инструкции конкретной IDE.

## 4. Что класть в `CLAUDE.md`

В `CLAUDE.md`:

- импорт `@AGENTS.md`;
- пояснение, что это adapter для Claude Code;
- путь к `.claude/settings.json`;
- путь к `.claude/agents/`;
- путь к `.claude/rules/`;
- правила Claude workflow;
- memory discipline.

Не класть:

- копию `AGENTS.md`;
- длинные продуктовые документы;
- deny/allow списки, если они должны enforced;
- секреты.

## 5. Что класть в `.claude/settings.json`

Это слой enforcement.

Туда выносятся:

- запрет чтения `.env`;
- запрет чтения ключей;
- запрет опасных bash-команд;
- ask для `git push`, deploy, publish;
- allow для безопасных локальных команд;
- hooks, если они нужны.

Важно: текст в `CLAUDE.md` просит агента соблюдать правило, а `.claude/settings.json` технически ограничивает действие.

## 6. Роль `Team.yml`

`Team.yml` описывает AI-сотрудников, которые собирают проект.

Это не продуктовые AI-сотрудники внутри ProSmet.

Пример:

```yaml
team:
  name: "ProSmet AI Build Team"
  standard_docs:
    - "docs/AI_M_MSF.md"
    - "Vision.md"
    - "Scope.md"
  roles:
    Architect: "harness/build-team.md#architect"
    BusinessAnalyst: "harness/build-team.md#businessanalyst"
    SolutionArchitect: "harness/build-team.md#solutionarchitect"
    EstimationEngineDeveloper: "harness/build-team.md#estimationenginedeveloper"
```

## 7. Рабочий каркас проекта

```text
Project/
  AGENTS.md
  CLAUDE.md
  Team.yml
  Vision.md
  Scope.md
  Focus.md
  Backlogs.md
  EntryPointForTask.md
  docs/
    AI_M_MSF.md
    ConceptualDesign.md
    SolutionDesign.md
    ADR/
    Domain/
    Evals/
    dev/handoffs/
  harness/
    build-team.md
    skills/
    scripts/
  tasks/
  reports/
  workspace/
```

## 8. Что такое ADR

ADR — Architecture Decision Record.

Это короткая запись архитектурного решения.

ADR нужен, чтобы будущий человек или AI-агент понимал:

- какая развилка была;
- что выбрали;
- почему выбрали;
- какие последствия появились;
- какие правила теперь нельзя случайно нарушить.

Мини-шаблон:

```md
# ADR-XXX · Название

Дата:
Статус: proposed | accepted | superseded

## Контекст

Какая проблема или развилка.

## Решение

Что выбрали.

## Последствия

Что это меняет в архитектуре и работе команды.
```

## 9. Порядок создания нового проекта

1. Собрать `Vision.md`.
2. Собрать `Scope.md`.
3. Создать `AGENTS.md` как общий harness.
4. Создать `CLAUDE.md` как adapter через `@AGENTS.md`.
5. Создать `.claude/settings.json`.
6. Создать `Team.yml`.
7. Описать роли в `harness/build-team.md`.
8. Создать `docs/ConceptualDesign.md`.
9. Создать `docs/SolutionDesign.md`.
10. Зафиксировать ключевые решения в `docs/ADR/`.
11. Создать `EntryPointForTask.md`, `Focus.md`, `Backlogs.md`.
12. Разложить задачи в `tasks/`.

## 10. Главная логика

```text
AGENTS.md = общие правила поведения агента.
CLAUDE.md = способ дать эти правила Claude Code.
settings.json = технические запреты и разрешения.
Team.yml = кто из AI-сотрудников собирает проект.
Vision/Scope/Conceptual/Solution = что именно строим и как понимаем решение.
ADR = почему приняты важные решения.
```
