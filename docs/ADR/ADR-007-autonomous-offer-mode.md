# ADR-007 · Autonomous offer mode для типовых заявок

Дата: 2026-05-19  
Статус: принято  
Связано: `docs/ADR/ADR-003-human-review-before-client-send.md`, `docs/ADR/ADR-008-approval-policy-protocol.md`, `docs/ADR/ADR-009-phone-gate-and-consent.md`, `docs/ADR/ADR-010-client-link-and-pdf-analytics.md`

## Контекст

Product feedback от 2026-05-19 уточнил Definition of Done MVP: ProSmet должен быть автономным продуктом расчета смет под ключ, а не полу-ручным помощником компании.

Клиент должен прийти с сайта или Авито, ввести данные, оставить телефон и согласие, получить уникальную ссылку на рассчитанную смету с итоговой стоимостью и скачать PDF. Компания должна получить лида, метрики открытия/скачивания, статус сделки и следующий шаг.

## Решение

Вводим `autonomous offer mode` для типовых заявок.

Клиентская ссылка и PDF могут создаваться без ручного действия компании, если deterministic policy engine выдал decision `auto_publish`.

Policy engine может вернуть:

- `auto_publish`;
- `requires_review`;
- `requires_measurement`;
- `reject_as_incomplete`.

`auto_publish` разрешен только если:

- tenant явно включил autonomous offer mode;
- настроены price book, formula version, coefficient set, legal pack и notification channel;
- клиент дал согласие;
- телефон записан, если включен phone-gate;
- расчетная основа достаточна для complete или partial estimate;
- calculation engine создал immutable calculation snapshot;
- AI confidence выше threshold policy profile;
- нет contradictions, blocking risk flags, сложной геометрии без данных, ручных скидок и юридически рискованных формулировок;
- missing fields допустимы только при `publicationMode = partial`, если они явно показаны клиенту как "недостаточно данных";
- решение записано в `approval_policy_decisions`;
- audit log содержит входной hash, policy version, risk flags и reason codes.

## Последствия

- MVP считается завершенным только после автономной выдачи сметы для типовой заявки.
- ADR-003 остается действительным для MVP-0, MVP-1 и исключений.
- Появляется обязательная сущность `approval_policy_decisions`.
- PDF/link protocol принимает human approval или audited `auto_publish`.
- Quality gates должны проверять, что рискованная заявка не публикуется автоматически.
- AI не принимает решение о цене и не отправляет смету. Автопубликация является результатом deterministic workflow.
- Owner web и Telegram/Max уведомления становятся частью публикационного контура: владелец должен видеть auto-published lead и события клиента.

## Открытые вопросы

- точные пилотные значения thresholds после первых golden estimates;
- полный список risk flags после интервью с пилотом;
- первый мессенджер владельца: Telegram, Max или оба;
- нужен ли отдельный tenant-level режим "только ссылка" без PDF.
