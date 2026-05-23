# Architecture.md · ProSmet

Дата: 2026-05-19  
Статус: clean target architecture, обновлено по autonomous MVP feedback  
Связано: `Vision.md`, `Scope.md`, `docs/ConceptualDesign.md`, `docs/SolutionDesign.md`, `docs/Domain/CeilingEstimateModel.md`, `docs/Evals/QualityGates.md`, `docs/ADR/ADR-007-autonomous-offer-mode.md`, `docs/ADR/ADR-008-approval-policy-protocol.md`, `docs/ADR/ADR-013-senior-ceiling-estimator-build-role.md`, `docs/ADR/ADR-014-partial-estimate-and-phone-gated-reveal.md`, `docs/ADR/ADR-015-rf-data-residency-and-deployment-path.md`

## 1. Архитектурный тезис

ProSmet строится как модульная мульти-тенантная платформа.

Общее ядро отвечает за пользователей, организации, заявки, расчеты, документы, права, AI gateway, approval policy, клиентские ссылки, аналитику событий, аудит и безопасность. Вертикальный модуль `ceiling` отвечает за предметку натяжных потолков: параметры, формулы, справочники, варианты сметы, тексты вопросов, policy flags и PDF-шаблон.

## 2. Целевая схема

```text
Сайт бригады / Авито
  -> loader.js с CDN prosmet.tech
  -> iframe widget.prosmet.tech / промежуточная страница ProSmet

apps/ceiling
  -> Next.js App Router
  -> виджет, Avito entry, кабинет, admin, route handlers
  -> вызывает только публичные сервисы @prosmet/core

apps/owner-bot
  -> Telegram и/или Max adapter
  -> уведомления владельцу
  -> быстрые действия по review, замеру и следующему шагу

packages/core
  -> calc: общий движок расчетов, включая partial estimate
  -> policy: auto_publish / review / measurement decisions
  -> db: Drizzle, миграции, RLS, withTenant
  -> ai: sanitizePII, removeMoney, aiGateway, fallback
  -> auth: magic-link, anonymous sessions
  -> pdf: шаблоны документов
  -> pricing: tenant pricing profile, markup policy
  -> links: клиентские ссылки и события
  -> channels: site, Avito, Telegram/Max adapters
  -> legal: согласия и юридические тексты
  -> queues: фоновые задачи
  -> telemetry: аудит, логи, метрики

apps/workers
  -> pdf.generate
  -> client-link-events.ingest
  -> price.import
  -> notifications.send
  -> ai.audit

apps/voice-gateway
  -> отдельный сервис после текстового пилота
  -> streaming STT через Yandex SpeechKit

Local / VPS / dev cloud
  -> вариант dev/stage, если не содержит реальные ПД
  -> Redis

RF production
  -> PostgreSQL в РФ
  -> Object Storage/PDF в РФ
  -> logs/backups в РФ
  -> compute в РФ
```

## 3. Монорепо

```text
apps/
  ceiling/
    app/
      (widget)/
      (avito-entry)/
      dashboard/
      admin/
      api/
    domain/
      params/
      pricing/
      prompts/
      pdf/
  workers/
    pdf-worker/
    link-event-worker/
    import-worker/
    notification-worker/
  owner-bot/
  voice-gateway/

packages/
  core/
    calc/
    policy/
    db/
    ai/
    auth/
    pdf/
    links/
    legal/
    channels/
    queues/
    telemetry/
  ui/
  widget-loader/
  config/
```

## 4. Граница `core` и `ceiling`

В `packages/core` разрешено:

- `tenant`;
- `user`;
- `lead`;
- `room`;
- `calculation`;
- `calculation_item`;
- `deal`;
- `price_book`;
- `client_estimate_link`;
- `client_link_event`;
- `approval_policy_decision`;
- `notification`;
- `legal_document`;
- `consent_record`;
- `audit_log`;
- общий расчетный engine;
- общий AI gateway;
- общий PDF renderer;
- RLS и `withTenant`.

В `packages/core` запрещено:

- `ceiling`;
- `потолок`;
- `натяж`;
- `полотно`;
- `багет`;
- `светильник`;
- потолочные коэффициенты;
- потолочные prompt templates.

Потолочная предметка живет в `apps/ceiling/domain`.

## 5. Данные

Минимальная схема MVP:

- `tenants`;
- `tenant_domains`;
- `tenant_settings`;
- `users`;
- `memberships`;
- `sessions`;
- `verification_tokens`;
- `clients`;
- `leads`;
- `lead_sources`;
- `acquisition_sessions`;
- `rooms`;
- `calculation_inputs`;
- `calculations`;
- `calculation_items`;
- `estimate_variants`;
- `human_reviews`;
- `approval_policy_decisions`;
- `approval_policy_profiles`;
- `client_estimate_links`;
- `client_link_events`;
- `pdf_assets`;
- `deals`;
- `notifications`;
- `notification_channels`;
- `conversations`;
- `messages`;
- `price_books`;
- `price_imports`;
- `price_items`;
- `tenant_pricing_profiles`;
- `markup_policies`;
- `regions`;
- `coefficients`;
- `coefficient_sets`;
- `legal_documents`;
- `legal_packs`;
- `consent_records`;
- `audit_log`;
- `pii_access_log`;
- `ai_payload_audit`.
- `deployment_environments`.

Все чувствительные таблицы получают прямой `tenant_id`, даже когда tenant выводится через внешний ключ. Это упрощает RLS, индексы, фоновые задачи и аудит.

## 6. RLS

Правила:

- приложение работает через роль без `BYPASSRLS`;
- приложение не владеет пользовательскими таблицами;
- чувствительные таблицы имеют `FORCE ROW LEVEL SECURITY`;
- все пользовательские запросы идут через `withTenant`;
- tenant определяется серверной сессией;
- `tenantId` из клиента считается недоверенным;
- тесты проверяют доступ tenant A к данным tenant B.

Паттерн:

```ts
await withTenant(session.tenantId, async (tx) => {
  return tx.query.leads.findMany();
});
```

## 7. AI Gateway

Все вызовы моделей идут только через `packages/core/ai/gateway`.

Pipeline:

1. Проверить основание обработки данных.
2. Обнаружить признаки ПД.
3. Заменить ПД на placeholders.
4. Удалить денежные суммы и price-поля.
5. Записать audit-событие.
6. Вызвать основного провайдера.
7. При сбое включить fallback.
8. Сохранить только безопасный payload.

Запрещены прямые вызовы OpenAI, Anthropic, YandexGPT, Whisper, SpeechKit и embeddings вне gateway-слоя.

## 8. Деньги и AI

В LLM payload не попадают:

- итоговые суммы;
- строки с ценой;
- скидки;
- маржа;
- `final_price`;
- `quoted_price`;
- PDF со сметой;
- прайс с денежными значениями.

Если нужен клиентский текст, LLM получает структуру без денег. Денежные значения подставляет код после ответа модели.

## 9. Персональные данные

Согласие требуется до сбора:

- телефона;
- имени;
- email;
- адреса;
- голоса;
- файлов;
- свободного текста, где могут быть ПД.

Хранение сообщений:

- `content_encrypted` — оригинал, если нужен бизнесу;
- `content_sanitized` — то, что уходило в AI;
- `pii_detected`;
- `retention_until`;
- `tenant_id`.

Каждый доступ к оригиналу пишет запись в `pii_access_log`.

## 10. API MVP

Черновой набор route handlers:

- `POST /api/session` — создать клиентскую сессию и проверить tenant domain.
- `POST /api/consent` — записать согласие.
- `POST /api/leads` — создать лид после согласия.
- `POST /api/leads/:id/contact` — записать телефон для полного раскрытия сметы.
- `POST /api/leads/:id/params` — сохранить структурные ответы формы.
- `POST /api/calculations/preview` — рассчитать partial/complete preview.
- `POST /api/calculations` — создать immutable calculation snapshot из серверной сессии.
- `GET /api/calculations/:id` — получить расчет для разрешенного контекста.
- `POST /api/calculations/:id/policy-decision` — получить или зафиксировать решение публикации.
- `POST /api/client-links/:token/unlock` — открыть полную смету после phone-gate.
- `POST /api/pdf` — поставить PDF-задачу.
- `GET /api/pdf/:jobId` — статус PDF.
- `GET /api/client-links/:token` — открыть клиентскую ссылку.
- `POST /api/client-links/:token/events` — записать открытие, скачивание PDF или CTA.
- `POST /api/ai/collect-params` — текстовый сбор параметров через gateway.
- `POST /api/auth/signin` — magic-link.
- `GET /api/dashboard/leads` — список заявок.
- `GET /api/dashboard/leads/:id` — карточка заявки.
- `GET /api/dashboard/client-events` — события клиентских ссылок.
- `POST /api/dashboard/settings/price-imports` — загрузить прайс.
- `PATCH /api/dashboard/settings/pricing-profile` — настроить наценки, минимальную стоимость, округления.
- `POST /api/dashboard/calculations/:id/approve` — human review.
- `POST /api/dashboard/calculations/:id/requires-measurement` — отправить расчет в замер.
- `PATCH /api/dashboard/leads/:id/status` — обновить статус сделки.
- `POST /api/bot/telegram/webhook` — Telegram webhook после выбора канала.
- `POST /api/bot/max/webhook` — Max webhook после выбора канала.

## 11. Виджет и вход из Авито

MVP-решение: iframe.

Контракт:

- `loader.js` читает публичный `tenant_slug`;
- сервер проверяет `Origin`, `parentUrl` и `allowed_domains`;
- iframe получает session от сервера;
- `postMessage` используется только для UI-событий;
- сбор параметров идет как чат с быстрыми ответами и своим вводом;
- до телефона можно показать замыленный preview;
- расчет и лиды не принимают tenant из `postMessage`.

Авито-вход:

- объявление ведет на уникальную ссылку, QR или промежуточную страницу ProSmet;
- источник `avito` фиксируется в `lead_sources`;
- согласие фиксируется до ПД;
- телефон фиксируется до полного раскрытия сметы/PDF;
- link token не раскрывает `tenant_id`, price snapshot или персональные данные.

## 12. PDF, клиентская ссылка и автономная публикация

Создаются после human review или после аудируемого решения policy engine `auto_publish`.

`auto_publish` разрешен только когда:

- tenant включил autonomous offer mode;
- прайс, pricing profile, наценки, формулы, coefficient set, legal pack и notification channel настроены;
- согласие записано;
- телефон записан, если включен phone-gate;
- расчетная основа достаточна для complete или partial estimate;
- AI confidence выше утвержденного порога;
- нет risk flags, которые требуют замера или проверки;
- расчет сохранен как immutable snapshot.

Обязательные элементы:

- бренд бригады;
- дата;
- версия расчета;
- версия прайса;
- параметры помещения;
- строки материалов и работ;
- строки `insufficient_data`, если расчет неполный;
- варианты предложения;
- срок действия;
- юридическая фраза: "не является публичной офертой (ст. 437 ГК РФ). Окончательные условия определяются в договоре по результатам замера."

События клиентской ссылки:

- открытие;
- повторное открытие;
- скачивание PDF;
- клик по следующему шагу;
- открытие просроченной ссылки.

Preview до телефона:

- может показывать часть рассчитанных строк;
- должен замыливать итоговые/ценовые блоки по tenant policy;
- не дает PDF;
- не раскрывает приватные идентификаторы;
- пишет событие preview, если включена аналитика.

## 13. Clean Source Policy

Clean-пакет является самостоятельным источником истины для дальнейшей работы.

Правила:

- текущая архитектура берется из `Vision.md`, `Scope.md`, `docs/ConceptualDesign.md`, `docs/SolutionDesign.md`, `docs/Architecture.md`;
- внешние черновики используются только как историческая фактура, если архитектор явно попросит провести сравнение;
- новые решения фиксируются в ADR;
- код и формулы будущей реализации создаются заново под утвержденный Scope и deterministic estimation contract.

## 14. Тестовая стратегия

Обязательные проверки перед пилотом:

- расчет детерминирован;
- partial estimate показывает "недостаточно данных" и не выдает неполный итог за финальный;
- edge cases потолочной сметы покрыты;
- фиксированные строки не умножаются на коэффициенты;
- tenant A не видит tenant B;
- AI payload не содержит ПД;
- AI payload не содержит денег;
- согласие требуется до ПД;
- PDF содержит юридическую фразу;
- клиентская ссылка пишет opening/download/CTA events;
- `auto_publish` невозможен без policy decision и audit log;
- `auto_publish` с `publicationMode = partial` явно показывает неполноту;
- рискованная заявка уходит в `requires_review` или `requires_measurement`;
- уведомление владельца отправляется в web и выбранный чат-канал или fallback;
- `packages/core` не содержит потолочных терминов;
- API не принимает tenant из клиента.
- реальные ПД не попадают в неподтвержденный local/VPS контур.

## 15. Порядок реализации

1. Утвердить `Vision.md`.
2. Утвердить `Scope.md`.
3. Дособрать `docs/ConceptualDesign.md`.
4. Дособрать `docs/SolutionDesign.md` со схемами.
5. Собрать 5-10 golden estimates.
6. Скаффолд монорепо.
7. Поднять БД, миграции, RLS и `withTenant`.
8. Реализовать загрузку прайса и tenant pricing profile.
9. Реализовать расчетное ядро с partial estimate.
10. Сделать внутренний экран заявки и human review.
11. Сделать чатовый widget/form с preview до телефона.
12. Сделать клиентскую ссылку и PDF после phone-gate.
13. Подключить трекинг preview/opening/download/CTA.
14. Подключить текстовый AI-сборщик через gateway.
15. Подключить pilot widget/form и Авито-вход.
16. Реализовать owner web dashboard и первый бот-канал уведомлений.
17. Реализовать approval policy и autonomous offer mode.
18. Подготовить RF production deployment milestone до реальных ПД в публичном запуске.
19. После автономного текстового пилота включать голос, интеграции и расширенную CRM.
