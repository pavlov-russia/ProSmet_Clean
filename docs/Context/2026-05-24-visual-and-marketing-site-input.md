# Context: Visual Direction and ProSmet Marketing Site

Дата: 2026-05-24  
Статус: принятая контекстная правка для архитектуры

## Источники

- `docs/Visual/2026-05-06-2766a0.md`
- `docs/Visual/unnamed (7).png`
- `docs/Visual/vision.md`
- `docs/Visual/vision-long-term-platform.md`
- `docs/Visual/README1.md`

## Принятые вводные

- UX должен быть легким: много воздуха, светлый фон, бело-голубая основа, фиолетовые акценты.
- Интерфейс владельца должен быть не тяжелой CRM, а единым рабочим окном: заявки, чаты, выводы AI, статусы и следующие действия.
- Mobile-first обязателен: быстрый доступ снизу, крупные действия, понятные карточки, короткие состояния.
- Дизайн должен поддерживать гибридный ввод: чат, быстрые ответы, классические формы, позже голос/фото.
- Архитектура AI-команды и runtime AI не должны смешиваться: development-time AI-сотрудники помогают строить продукт, runtime AI остается только в безопасном gateway.
- Нужен отдельный сайт ProSmet для рекламы нашего сервиса потолочным компаниям и мастерам.

## Архитектурное решение

Добавить в архитектуру pre-launch public marketing surface:

```text
apps/marketing
  -> сайт ProSmet для рекламы сервиса
  -> страницы: главная, потолочная вертикаль, demo/lead form, legal pages
  -> использует packages/ui design tokens
  -> не имеет доступа к tenant/customer data
  -> не показывает реальные прайсы, реальные ПД или реальные сметы без отдельного разрешения
```

Это не генератор сайтов подрядчиков и не production deploy. Генерация сайтов подрядчиков остается отложенной частью платформы.

## Подключаемые AI-сотрудники

- `AIOrchestrator` — выпускает cycle/command packets.
- `Architect` — следит за Scope boundary and architecture invariants.
- `ProductAnalyst` — формулирует offer, audience, UX acceptance and conversion metrics.
- `FrontendDeveloper` — реализует visual system, marketing pages and responsive UI.
- `BusinessAnalyst` — проверяет consent/legal wording for lead form.
- `QAEngineer` — проверяет browser smoke, mobile layout, no secrets/no real PII in fixtures.
- `PPM` — заводит task cards and handoff.

## Нельзя

- Подменять MVP расчетного продукта маркетинговой страницей.
- Обещать точные цены, скидки, окупаемость или юридические гарантии без подтвержденных данных.
- Использовать реальные ПД, реальные сметы, реальные отзывы или реальные прайсы без отдельного разрешения.
- Добавлять production deploy или внешние сервисы на этом шаге.

