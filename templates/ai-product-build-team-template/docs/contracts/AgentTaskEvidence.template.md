# Agent Task Evidence Template

Файл:

```text
reports/task-evidence/TASK-ID.json
```

Минимальный пример:

```json
{
  "contractVersion": "agent-task-evidence.v1",
  "taskId": "TASK-001",
  "role": "Architect",
  "status": "passed",
  "changedFiles": [
    "docs/Architecture.md"
  ],
  "checks": [
    {
      "command": "npm test",
      "status": "not_run",
      "reason": "No implementation yet"
    }
  ],
  "gateResults": [
    {
      "gateId": "ARCH.CONTRACT.ALIGNMENT",
      "status": "passed",
      "evidence": [
        "docs/Architecture.md"
      ]
    }
  ],
  "blockers": [],
  "nextExecutor": "PPM",
  "confirmations": {
    "scopeExpanded": false,
    "readSecrets": false,
    "usedRealPii": false,
    "usedExternalService": false
  }
}
```

