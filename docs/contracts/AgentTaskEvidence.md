# AgentTaskEvidence

Дата: 2026-05-23
Статус: контракт evidence-отчета AI-сотрудника

## Назначение

Текстовый handoff удобен человеку, но плохо проверяется машиной. Поэтому каждая исполняемая task card должна завершаться JSON-отчетом:

```text
reports/task-evidence/TASK-ID.json
```

Отчет не заменяет короткий handoff, а делает его проверяемым.

## Инварианты

- Нельзя писать `passed`, если команда не запускалась.
- `not_run` обязан иметь `reason`.
- Отчет не содержит секретов, `.env` значений, реальных ПД и реального прайса пилота.
- `scopeExpanded`, `readSecrets`, `weakenedTenantIsolation`, `sentPiiOrMoneyToLlm`, `usedLlmForPrice` должны быть `false`.
- `gateResults[].gateId` должен существовать в `docs/Evals/gates.json`.

## Минимальный пример

```json
{
  "$schema": "../../docs/contracts/schemas/agent-task-evidence-v1.schema.json",
  "contractVersion": "agent-task-evidence.v1",
  "taskId": "TASK-004A",
  "role": "EstimationEngineDeveloper",
  "status": "blocked",
  "changedFiles": [],
  "checks": [
    {
      "command": "python3 harness/scripts/validate_predictability.py",
      "status": "passed"
    }
  ],
  "gateResults": [
    {
      "gateId": "FIXTURES.GOLDEN.SYNTHETIC",
      "status": "passed",
      "evidence": ["fixtures/golden-estimates/GE-001-simple-room-12sqm-no-light.json"]
    }
  ],
  "blockers": ["No implementation scaffold yet"],
  "nextExecutor": "DevOps",
  "confirmations": {
    "scopeExpanded": false,
    "readSecrets": false,
    "revertedOthersChanges": false,
    "weakenedTenantIsolation": false,
    "sentPiiOrMoneyToLlm": false,
    "usedLlmForPrice": false
  }
}
```
