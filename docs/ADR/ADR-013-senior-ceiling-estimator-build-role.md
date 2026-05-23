# ADR-013 · SeniorCeilingEstimator как AI-сотрудник разработки, а не runtime-агент

Дата: 2026-05-19  
Статус: принято  
Связано: `Team.yml`, `harness/build-team.md`, `docs/Domain/CeilingEstimateModel.md`

## Контекст

Senior AI-сметчик по натяжным потолкам нужен ProSmet, но его роль легко перепутать с runtime AI-агентом внутри продукта. Если оставить его как "мозг продукта", появится риск, что AI начнет считать деньги или принимать решение по смете.

Архитектор уточнил: SeniorCeilingEstimator должен работать над созданием решения ProSmet вместе с другими AI-сотрудниками команды. Он может экспертно просчитывать сметы, проверять формулы и давать точные данные для системы, но production-расчет должен выполнять deterministic engine.

## Решение

SeniorCeilingEstimator является AI-сотрудником build team.

Он делает:

- экспертно просчитывает учебные и пилотные сметы для golden estimates;
- формирует предметные вопросы;
- проверяет формулы и коэффициенты;
- описывает risk flags;
- объясняет причины `requires_measurement`;
- дает EstimationEngineDeveloper и SolutionArchitect точные предметные данные.

Он не является runtime AI-сотрудником внутри MVP-продукта.

В runtime MVP остаются только минимальные AI-функции:

- сбор и нормализация параметров;
- выявление пропусков и рисков;
- объяснение уже рассчитанной сметы без денег в LLM payload.

## Последствия

- `harness/agent-roles.md` не должен описывать SeniorCeilingEstimator как внутреннего product agent.
- Экспертные расчеты SeniorCeilingEstimator становятся golden estimates, формулами, справочниками, coefficient rules и tests.
- Клиенту деньги показывает только deterministic calculation engine.
- Не плодим лишних AI-сотрудников в MVP.
