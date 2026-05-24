# harness/scripts

Здесь должны жить проектные проверочные скрипты.

Реализованные скрипты:

- `agents/_agent_common.py` — единый registry AI-сотрудников ProSmet.
- `agents/generate_agent_assets.py` — генерирует Claude/Codex profiles и персональные role helpers.
- `agents/dispatch_tasks.py` — автоматически связывает task cards с AI-сотрудниками и строит план подключения.
- `agents/validate_agent_profiles.py` — проверяет полноту AI-сотрудников, task cards и dependency graph.
- `agents/<role>.py` — персональные entrypoints AI-сотрудников.
- `validate_predictability.py` — проверяет contract manifest, schemas, gate matrix, micro-task metadata, synthetic fixtures and evidence reports.
- `architect_inbox.py` — показывает открытые запросы архитектору из `workspace/architect-inbox/requests/` and `reports/price-requests/`.
- `ai_orchestrator.py` — локальный Python brain AIOrchestrator: proposal, approval-before-dispatch, command packets and status.

Планируемые скрипты:

- `check-core-boundary` — проверяет, что `packages/core` не содержит потолочных терминов.
- `check-ai-payload-fixtures` — проверяет fixtures на отсутствие ПД и денежных сумм.
- `check-pdf-legal` — проверяет обязательную юридическую фразу в PDF/link templates.
- `check-tenant-access` — запускает cross-tenant regression tests.

Правило:

- агент не должен ссылаться на скрипт как на существующий, пока файл реально не создан.
- новый скрипт должен иметь README или usage внутри файла.
- скрипты не читают `.env` и не требуют production secrets.

Базовый цикл оркестратора:

```bash
python3 harness/scripts/ai_orchestrator.py propose
python3 harness/scripts/ai_orchestrator.py approve --cycle reports/orchestrator/latest-cycle.json --approved-by Architect
python3 harness/scripts/ai_orchestrator.py status
```
