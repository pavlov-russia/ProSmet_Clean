# ADR-011 · Site widget и Avito entry как MVP-каналы входа

Дата: 2026-05-19  
Статус: принято  
Связано: `Scope.md`, `docs/SolutionDesign.md`, `docs/Architecture.md`

## Контекст

MVP должен принимать заявки с сайта подрядчика и Авито. Глубокие интеграции с внешними платформами не входят в первый scope, но клиентский путь должен быть реальным и измеряемым.

## Решение

Для сайта используем iframe widget через `loader.js`.

Для Авито используем легкий entry:

- уникальная ссылка в объявлении или сообщении;
- QR на промежуточную страницу;
- короткий landing URL;
- ручная ссылка как fallback.

Сервер определяет tenant по allowed domain, public slug или signed entry token. Клиентский `tenantId` не считается доверенным.

## Последствия

- `tenant_domains` и `lead_sources` становятся обязательными сущностями.
- `loader.js` содержит только публичный slug, а не секреты.
- `postMessage` используется только для UI-событий.
- Авито-текст считается untrusted input и проходит consent/redaction перед AI.
- Вся дальнейшая обработка одинакова для site и Avito: consent, phone-gate, params, calculation, policy, link/PDF analytics.
