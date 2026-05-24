# ArchitectInterventionRequest

Дата: 2026-05-23
Статус: контракт запроса вмешательства архитектора-человека

## Назначение

Когда AI-сотруднику нужно решение владельца/архитектора, он не должен прятать вопрос в длинном handoff. Он создает отдельный machine-readable request в рабочем inbox.

Файл запроса:

```text
workspace/architect-inbox/requests/ARCH-REQUEST-YYYYMMDD-TASK-ID-short-slug.json
```

Схема:

```text
docs/contracts/schemas/architect-intervention-request-v1.schema.json
```

## Когда создавать

Запрос обязателен, если задача требует:

- изменить `Scope.md`;
- сменить стартовую вертикаль;
- добавить production dependency;
- изменить бизнес-модель, тарифы или юридические обещания;
- выполнить деструктивную миграцию;
- включить deploy, publish, git push или внешний production action;
- отправлять данные во внешний сервис;
- работать с реальными ПД, секретами или pilot data;
- использовать внешний источник вне clean-пакета как архитектурную опору;
- выбрать первый pilot, legal pack, bot/channel, policy threshold, risk flags;
- принять architecture override between slices.

Для реального прайса используется специальный `PriceInputRequest` в `reports/price-requests/`, но он тоже показывается в Architect Inbox.

## Правила

- Request не содержит секретов, `.env`, приватных ключей, реальных ПД или полный реальный прайс.
- Если решение влияет на архитектуру, после ответа нужен ADR или обновление contract-doc.
- AI-сотрудник обязан указать, что он может продолжать без ответа, а что заблокировано.
- В handoff/final AI-сотрудник пишет путь к созданному request.

## Минимальный пример

```json
{
  "$schema": "../../docs/contracts/schemas/architect-intervention-request-v1.schema.json",
  "contractVersion": "architect-intervention-request.v1",
  "requestId": "ARCH-REQUEST-20260523-TASK-007A-choose-bot-channel",
  "taskId": "TASK-007A",
  "requestedByRole": "BusinessAnalyst",
  "status": "open",
  "priority": "normal",
  "requestType": "product_decision",
  "title": "Выбрать первый bot/channel для MVP notifications",
  "reason": "TASK-007A can proceed without bot adapter, but MVP-1 notification path needs one selected channel.",
  "blockedWork": ["owner notification adapter selection"],
  "canContinueWithoutAnswer": true,
  "options": [
    {
      "id": "telegram_first",
      "label": "Telegram first",
      "tradeoff": "Fastest to prototype, but production availability/legal review remains separate."
    },
    {
      "id": "defer_bot",
      "label": "Defer bot",
      "tradeoff": "Keeps MVP-1 web-only until channel decision."
    }
  ],
  "recommendedOptionId": "defer_bot",
  "neededBy": "before_mvp_1_acceptance",
  "safety": {
    "containsRealPii": false,
    "containsSecrets": false,
    "requiresScopeChange": false,
    "requiresAdr": false
  },
  "nextActionForArchitect": "Выбрать channel option или подтвердить defer."
}
```
