# External Input Request Template

Когда AI-сотруднику нужны реальные данные, он не должен их придумывать.

Файл:

```text
workspace/architect-inbox/requests/EXTERNAL-INPUT-REQUEST-YYYYMMDD-TASK-ID.json
```

Пример:

```json
{
  "contractVersion": "external-input-request.v1",
  "requestId": "EXTERNAL-INPUT-REQUEST-20260524-TASK-004",
  "taskId": "TASK-004",
  "requestedByRole": "DomainExpert",
  "status": "open",
  "title": "Нужны реальные экспертные примеры",
  "reason": "Synthetic examples enough for engineering, but not enough for pilot calibration.",
  "neededInputs": [
    "5-10 expert-approved examples",
    "source of truth for real rules",
    "known edge cases"
  ],
  "doNotSendToLlm": true,
  "canContinueWithSyntheticData": true,
  "nextActionForArchitect": "Передать данные вручную или подтвердить, что работаем только на synthetic fixtures."
}
```

