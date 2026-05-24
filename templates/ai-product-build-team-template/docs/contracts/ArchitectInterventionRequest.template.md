# Architect Intervention Request Template

Когда AI-сотруднику нужно решение человека, он создает файл:

```text
workspace/architect-inbox/requests/ARCH-REQUEST-YYYYMMDD-TASK-ID-short-slug.json
```

Пример:

```json
{
  "contractVersion": "architect-intervention-request.v1",
  "requestId": "ARCH-REQUEST-20260524-TASK-001-choose-first-vertical",
  "taskId": "TASK-001",
  "requestedByRole": "ProductAnalyst",
  "status": "open",
  "priority": "normal",
  "requestType": "product_decision",
  "title": "Выбрать первую вертикаль MVP",
  "reason": "Без выбора вертикали нельзя сузить Scope и предметную модель.",
  "blockedWork": [
    "Scope MVP",
    "Domain model"
  ],
  "canContinueWithoutAnswer": false,
  "options": [
    {
      "id": "option_a",
      "label": "Вариант A",
      "tradeoff": "Быстрее, но уже рынок."
    },
    {
      "id": "option_b",
      "label": "Вариант B",
      "tradeoff": "Шире рынок, но сложнее MVP."
    }
  ],
  "recommendedOptionId": "option_a",
  "neededBy": "before_scope_acceptance",
  "safety": {
    "containsRealPii": false,
    "containsSecrets": false,
    "requiresScopeChange": true,
    "requiresAdr": true
  },
  "nextActionForArchitect": "Выбрать option или дать новое решение."
}
```

