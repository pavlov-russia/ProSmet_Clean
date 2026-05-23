# Handoff_01_autonomous-mvp-context

Тип документа: handoff  
Дата: 2026-05-19  
Автор / роль: Architect  
Родительский документ: `docs/Context/2026-05-19-autonomous-mvp-feedback.md`  
Родительская задача: занести обратную связь по autonomous MVP в clean-пакет

## Цель ветки

Подготовить ProSmet_Clean к следующему чату, где будут собираться Conceptual Design, Solution Design, ADR и AI-сотрудники разработки уже от новой продуктовой рамки.

## Что сделано

- `Vision.md` обновлен: MVP теперь автономный lead-to-estimate контур для сайта и Авито.
- `Scope.md` обновлен: добавлен MVP-2 Product-ready autonomous MVP.
- Введен `autonomous offer mode` и решение `auto_publish`.
- Зафиксированы client link metrics: opening, reopening, PDF download, CTA.
- Добавлен web+Telegram/Max интерфейс владельца.
- Добавлен senior AI-сметчик по натяжным потолкам в `Team.yml`, `harness/build-team.md`, `harness/agent-roles.md` и `.claude/agents/`.
- Создан ADR-007 для autonomous offer mode.
- ADR-003 уточнен: human review остается для MVP-0/MVP-1 и исключений.

## Что осталось

- Полноценно пересобрать `docs/ConceptualDesign.md`.
- Полноценно пересобрать `docs/SolutionDesign.md` со схемами.
- Доработать ADR-007: точные policy gates, confidence threshold, risk flags.
- Описать role cards AI-сотрудников разработки.
- Собрать 5-10 golden estimates с участием senior AI-сметчика.

## Quality Gates

- Новая продуктовая рамка должна сохранять правило: AI не считает цену.
- `auto_publish` не должен обходить deterministic calculation, legal gates, consent, phone-gate и audit.
- Нестандартные заявки должны уходить в `requires_review` или `requires_measurement`.

## Следующий исполнитель

Architect + SolutionArchitect + SeniorCeilingEstimator.
