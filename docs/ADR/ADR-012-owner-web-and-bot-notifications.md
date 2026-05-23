# ADR-012 · Owner web и Telegram/Max bot notifications

Дата: 2026-05-19  
Статус: принято  
Связано: `Scope.md`, `docs/ConceptualDesign.md`, `docs/SolutionDesign.md`

## Контекст

Во многих потолочных компаниях владелец одновременно продает, замеряет и монтирует. Ему нужен быстрый рабочий пульт, а не тяжелая CRM. Web-кабинет нужен для контроля и review, а Telegram/Max-бот — для быстрых уведомлений и действий на ходу.

## Решение

Web-кабинет является основным интерфейсом владельца.

Telegram/Max-бот является notification/action layer, а не полной заменой web-review.

Бот отправляет:

- новый лид;
- клиент увидел preview;
- клиент оставил телефон;
- auto-published estimate;
- requires review;
- requires measurement;
- клиент открыл ссылку;
- клиент скачал PDF;
- клиент нажал CTA;
- ошибка PDF или уведомления.

Быстрые действия разрешены только для безопасных операций или через signed deep link в web.

## Последствия

- `notifications` и `notification_channels` входят в MVP data model.
- Отсутствие бота не должно ломать продукт: событие остается в web и retry queue.
- Bot payload не должен раскрывать лишние ПД, AI payload или скрытые tenant identifiers.
- Review-risk actions deep-link в web, где виден полный контекст.
