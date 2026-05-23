# ADR-010 · Client link, PDF и аналитика событий

Дата: 2026-05-19  
Статус: принято  
Связано: `docs/ADR/ADR-003-human-review-before-client-send.md`, `docs/ADR/ADR-007-autonomous-offer-mode.md`, `docs/ADR/ADR-014-partial-estimate-and-phone-gated-reveal.md`

## Контекст

Клиентская ссылка и PDF являются центральным B2C-результатом MVP. Компания должна видеть не только факт создания сметы, но и поведение клиента: увидел preview, оставил телефон, открыл полную ссылку, вернулся, скачал PDF, нажал следующий шаг.

## Решение

Клиентская ссылка является отдельной сущностью `client_estimate_links`.

Она создается только после:

- human approval; или
- audited `auto_publish`.

PDF является отдельным `pdf_asset`, привязанным к immutable calculation snapshot.

Минимальные события:

- `preview_shown`;
- `phone_submitted`;
- `opened`;
- `reopened`;
- `pdf_downloaded`;
- `cta_clicked`;
- `expired_link_opened`.

События пишутся в `client_link_events` с idempotency key, hashed IP/user-agent и metadata без raw PII.

## Последствия

- Dashboard показывает link/PDF activity по заявке.
- Owner bot может отправлять уведомления о важных событиях.
- Ссылка не раскрывает tenant id, calculation id, price snapshot или ПД.
- Preview до телефона не дает PDF и не раскрывает полный расчет.
- Просроченная ссылка не показывает смету, но пишет safe event.
- Quality gates включают preview, phone submit, открытие, повторное открытие, скачивание PDF и CTA.
