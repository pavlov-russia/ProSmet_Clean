# Architecture Preparation Guide

Пошаговая инструкция подготовки архитектуры нового продукта.

## Шаг 1. Сбор вводных

Собери коротко:

- что за продукт;
- кто пользователь;
- какую боль решаем;
- что является MVP;
- какие данные нужны;
- есть ли деньги, ПД, медицина, право, финансы;
- какие внешние сервисы нужны;
- что нельзя делать AI.

## Шаг 2. Vision

Создай `Vision.md`.

В нем опиши:

- суть продукта в одной фразе;
- почему продукт нужен;
- пользователей;
- основные сценарии;
- долгосрочный образ;
- метрики успеха;
- что продуктом не является.

## Шаг 3. Scope

Создай `Scope.md`.

Раздели:

- входит в MVP;
- откладывается;
- open decisions;
- quality gates;
- риски;
- критерии готовности.

## Шаг 4. Conceptual Design

Создай `docs/ConceptualDesign.md`.

Опиши:

- роли пользователей;
- пользовательские потоки;
- бизнес-сущности;
- lifecycle;
- AI boundaries;
- human review boundaries.

## Шаг 5. Solution Design

Создай `docs/SolutionDesign.md`.

Опиши:

- компоненты;
- API surface;
- data model;
- auth/access;
- AI gateway;
- integration boundaries;
- workers;
- audit/logging;
- quality gates.

## Шаг 6. Architecture

Создай `docs/Architecture.md`.

Зафиксируй:

- целевую схему;
- структуру репозитория;
- границы модулей;
- что запрещено в общем ядре;
- какие зависимости разрешены;
- как расширять систему.

## Шаг 7. ADR

Создай ADR для ключевых развилок:

- стартовая вертикаль;
- AI boundaries;
- работа с ПД;
- deterministic rules vs LLM;
- human review;
- deployment path;
- visual/design system;
- external services.

## Шаг 8. Team

Скопируй `Team.template.yml` в `Team.yml`.

Переименуй предметные роли:

- `DomainExpert`;
- `RulesEngineDeveloper`.

Например:

```text
DomainExpert -> LegalExpert
RulesEngineDeveloper -> DocumentRulesDeveloper
```

## Шаг 9. Quality Gates

Создай `docs/Evals/QualityGates.md`.

Минимум:

- architecture gates;
- security gates;
- AI safety gates;
- data gates;
- UI gates;
- release gates.

## Шаг 10. Tasks

Создай task cards в `tasks/`.

Каждая задача должна иметь:

- owner;
- dependencies;
- outputs;
- forbidden;
- gate_ids;
- required_evidence;
- required_reports;
- acceptance.

## Шаг 11. Evidence

Каждая завершенная задача создает:

```text
reports/task-evidence/TASK-ID.json
```

Без evidence задача не считается done.

