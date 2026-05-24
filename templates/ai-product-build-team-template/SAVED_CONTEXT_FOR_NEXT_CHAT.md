# Saved Context For Next Chat

Дата: 2026-05-24

## Что было сделано

Из проекта ProSmet вынесен универсальный шаблон AI-команды для разработки других продуктов.

Шаблон не привязан к натяжным потолкам. Потолочная предметка заменена универсальными ролями:

- `DomainAnalyst` — описывает предметную область;
- `DomainExpert` — экспертно проверяет реальные кейсы;
- `RulesEngineDeveloper` — реализует детерминированные правила/decision engine.

## Что важно сохранить

Главный процесс:

```text
Vision -> Scope -> Conceptual Design -> Solution Design -> Architecture -> ADR -> Tasks -> Evidence
```

Главный принцип:

```text
Сначала архитектура и task cards, потом код.
```

Главная модель управления:

```text
человек -> AIOrchestrator -> command packets -> AI-сотрудники -> evidence -> следующий цикл
```

## Что сказать AI в новом чате

Используй `NEW_CHAT_PROMPT.md`.

Если нужно совсем коротко:

```text
Возьми шаблон `ai-product-build-team-template`.
Подготовь архитектуру нового продукта по методологии AI_M_MSF.
Не начинай с кода.
Сначала Vision, Scope, Conceptual Design, Solution Design, ADR, Team, Tasks, Quality Gates.
Пиши просто.
```

## Какие роли универсальны

- AIOrchestrator
- Architect
- ProductAnalyst
- BusinessAnalyst
- DomainAnalyst
- DomainExpert
- SolutionArchitect
- RulesEngineDeveloper
- BackendDeveloper
- FrontendDeveloper
- AIFlowDeveloper
- QAEngineer
- DevOps
- PPM

## Что заменить под новый продукт

- название продукта;
- целевую аудиторию;
- предметную область;
- DomainExpert;
- RulesEngineDeveloper;
- legal/security constraints;
- quality gates;
- MVP Scope.

