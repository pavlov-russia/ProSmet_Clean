# PriceInputRequest

Дата: 2026-05-23
Статус: контракт запроса реального прайса у архитектора

## Назначение

Synthetic fixtures позволяют разрабатывать engine без реального прайса. Но перед реальным пилотом, tenant pricing profile, import flow, calibration или production publication AI-сотрудник может упереться в отсутствие реального прайса.

В этом случае AI-сотрудник не придумывает цены и не продолжает работу на догадках. Он создает machine-readable price input request и явно уведомляет архитектора-человека.

## Где хранить запрос

```text
reports/price-requests/PRICE-REQUEST-YYYYMMDD-TASK-ID.json
```

Формат проверяется схемой:

```text
docs/contracts/schemas/price-input-request-v1.schema.json
```

## Когда создавать

Создать request нужно, если task требует:

- реальный прайс пилота;
- реальные коэффициенты, скидки, минимальный заказ или округления tenant;
- real price import mapping;
- expert/pilot-approved golden estimates;
- legal/pilot readiness для выдачи клиенту не-synthetic сметы.

Не нужно создавать request, если task может корректно завершиться на synthetic fixtures and explicitly says so.

## Что должен сделать AI-сотрудник

1. Остановить часть работы, которая зависит от реального прайса.
2. Создать price request JSON.
3. В handoff/final написать: "Нужен ввод архитектора: real price input request создан".
4. Не помещать реальный прайс в LLM prompt, если ты передал его позже как файл/данные с ПД или коммерческой тайной.
5. Продолжать только независимую часть задачи на synthetic fixtures.

## Минимальный пример

```json
{
  "$schema": "../../docs/contracts/schemas/price-input-request-v1.schema.json",
  "contractVersion": "price-input-request.v1",
  "requestId": "PRICE-REQUEST-20260523-TASK-004C",
  "taskId": "TASK-004C",
  "requestedByRole": "EstimationEngineDeveloper",
  "status": "open",
  "reason": "Need expert-approved price book before replacing synthetic golden estimates.",
  "neededFor": ["pilot_ready_golden_estimates", "real_price_book_snapshot"],
  "requestedInputs": [
    {
      "id": "price_book",
      "label": "Прайс по материалам и работам",
      "required": true,
      "acceptedFormats": ["csv", "xlsx", "json", "markdown_table"],
      "notes": "Можно без ПД клиентов. Нужны единицы измерения, цена, валюта и дата актуальности."
    }
  ],
  "safety": {
    "containsRealPii": false,
    "containsSecrets": false,
    "doNotSendToLlm": true,
    "syntheticFallbackAllowed": true
  },
  "nextActionForArchitect": "Передать synthetic-safe прайс без ПД или подтвердить, что task остается на stub fixtures."
}
```
