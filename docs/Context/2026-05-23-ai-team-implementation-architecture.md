# 2026-05-23 · AI Team Implementation Architecture Review

Статус: принято как контекст доработки AI-команды реализации  
Связано: `Team.yml`, `harness/build-team.md`, `harness/agent-roles.md`, `docs/dev/PredictableAIWork.md`, `docs/contracts/AIOrchestrator.md`, `docs/Evals/gates.json`, `reports/orchestrator/latest-cycle.json`

## 1. Суть

В ProSmet есть два разных AI-слоя:

- runtime AI внутри продукта: только безопасный сбор/нормализация параметров и объяснение уже рассчитанной сметы без ПД, денег, прайса и PDF в LLM payload;
- development-time AI-команда: AI-сотрудники, которые проектируют, реализуют, проверяют и документируют ProSmet под контролем архитектора-человека.

Эти слои нельзя смешивать. AI-сотрудники реализации не являются runtime-агентами продукта и не принимают клиентские решения.

Текущий harness AI-команды уже оформлен как локальная фабрика разработки:

```text
task card
  -> dispatcher builds dependency graph
  -> AIOrchestrator proposes cycle
  -> Architect approves or rejects
  -> command packets
  -> AI employee executes micro-task
  -> evidence report
  -> acceptance / next cycle
```

## 2. Что уже хорошо

- `Team.yml` описывает 14 ролей AI Build Team и общие инварианты.
- `harness/build-team.md` и `harness/agent-roles.md` разделяют роли по управлению, продукту, предметке, реализации, QA и DevOps.
- `harness/scripts/agents/_agent_common.py` является единым registry для Claude/Codex profiles и Python helpers.
- `docs/dev/PredictableAIWork.md` вводит micro-task protocol: `owner`, `dependencies`, `gate_ids`, `required_evidence`, `required_reports`, `acceptance`.
- `docs/contracts/AIOrchestrator.md` фиксирует proposal -> approval -> command packets -> evidence -> next cycle.
- `harness/scripts/ai_orchestrator.py` не spawn-ит агентов, не читает `.env`, не ходит в сеть, не считает цены, не мутирует task cards и выпускает command packets только после approval.
- `docs/contracts/AgentTaskEvidence.md` требует machine-readable evidence report вместо одного текстового handoff.
- `PriceInputRequest` и `ArchitectInterventionRequest` переводят блокеры архитектора в проверяемые файлы.
- Synthetic fixtures позволяют двигать engineering без реальных ПД и реального прайса.

## 3. Текущий статус на момент review

- `reports/predictability-validation.json`: `pass`.
- Gates: 23.
- Tasks: 31.
- Micro-tasks: 22.
- Evidence reports: 1.
- Завершена только `TASK-011`.
- Доступна к запуску `TASK-001`.
- Последний orchestrator cycle: `ready_for_architect_approval`.
- Command packets еще не выпускались, потому что approval не был явно дан.

## 4. Архитектурные риски AI-команды

### 4.1. Evidence пока частично self-attestation

Evidence report фиксирует checks и gate results, но валидатор пока не доказывает, что команды реально запускались. `passed` доверяется JSON-отчету.

Нужно усилить:

- соответствие `reports/task-evidence/TASK-ID.json` реальной task card;
- совпадение `taskId`, filename, role/owner;
- покрытие всех `task.gate_ids` через `gateResults`;
- существование путей из `changedFiles` и `gateResults[].evidence`;
- запрет `passed` для future gates без реальной команды или explicit `not_run`/`not_applicable`;
- artifact hashes, timestamps, exit codes and output summaries.

### 4.2. Dependency closure недостаточно строгая

Dispatcher считает dependency закрытой по статусу task card (`done`, `accepted`, etc.), а не по связке `accepted status + valid evidence report`.

Нужно: dependency считается закрытой только если:

- task card имеет accepted/done status;
- evidence report существует;
- evidence валиден;
- все gates task покрыты или есть explicit Architect override.

### 4.3. Stale approval

`approve` перечитывает Architect Inbox, но не пересобирает dispatch plan and validations. Если task cards или reports изменились после `propose`, можно утвердить устаревший cycle.

Нужно:

- хранить input hashes proposal;
- на `approve` пересобирать plan/validations or compare hashes;
- блокировать approval при drift.

### 4.4. Regex-based YAML parsing

`dispatch_tasks.py` и `validate_predictability.py` парсят task cards regex-ами. Для текущего простого формата это работает, но усложнение YAML может сломать graph незаметно.

Нужно после workspace baseline перейти на нормальный YAML parser или зафиксировать строгий subset формата.

### 4.5. Роли местами пересекаются

Потенциальные зоны конфликтов:

- `Architect` / `SolutionArchitect` / `PPM` / `AIOrchestrator`;
- `DomainAnalyst` / `SeniorCeilingEstimator`;
- `BackendDeveloper` / `EstimationEngineDeveloper` в расчетно-сервисной границе;
- `QAEngineer` / `DevOps` в CI gates.

Нужно добавить RACI/conflict-resolution matrix для ключевых артефактов.

### 4.6. Slice acceptance не machine-readable

Переходы Architecture Prep -> MVP-0 -> MVP-1 -> MVP-2 описаны в тексте, но нет отдельного machine-readable slice acceptance report.

Нужно добавить:

```text
reports/slice-acceptance/architecture_prep.json
reports/slice-acceptance/mvp_0.json
reports/slice-acceptance/mvp_1.json
reports/slice-acceptance/mvp_2.json
```

### 4.7. Read-only audit mode отсутствует

`validate_predictability.py` всегда пишет report. Для архитектурного аудита нужен `--check` или `--no-write`.

## 5. Рекомендуемые доработки AI-команды

Приоритет 1:

- усилить `validate_predictability.py` как evidence linter;
- добавить `--check`/`--no-write`;
- требовать valid evidence report для dependency closure;
- защитить `approve` от stale proposal через input hashes or rerun validations.

Приоритет 2:

- добавить RACI matrix для AI-команды;
- добавить machine-readable slice acceptance reports;
- расширить command packet schema статусами `assigned`, `in_progress`, `blocked`, `completed`, `reviewed`, `accepted`;
- зафиксировать кто и как переводит task card в `accepted`.

Приоритет 3:

- перейти от regex parsing к YAML parser после workspace baseline;
- добавить scanner reports/evidence/payload fixtures на secrets/PII/money patterns без чтения `.env`;
- сделать evidence runner, который сам пишет command, exitCode, timestamp, output summary and artifact hashes.

## 6. Prompt для доработки AI-команды

Используй этот prompt для следующей задачи Architect/AIOrchestrator/QAEngineer/PPM по доработке harness AI-команды:

```text
Ты senior AI-архитектор ProSmet и работаешь внутри /root/projects/ProSmet_Clean.

Цель: доработать architecture and harness AI-команды реализации ProSmet, чтобы development-time AI Build Team стала более проверяемой, управляемой и безопасной перед стартом MVP-0 implementation.

Обязательный контекст:
- AGENTS.md
- EntryPointForTask.md
- Focus.md
- Team.yml
- harness/build-team.md
- harness/agent-roles.md
- docs/dev/PredictableAIWork.md
- docs/dev/ImplementationPlan.md
- docs/contracts/AIOrchestrator.md
- docs/contracts/AgentTaskEvidence.md
- docs/contracts/ArchitectInterventionRequest.md
- docs/contracts/PriceInputRequest.md
- docs/Evals/GateMatrix.md
- docs/Evals/gates.json
- docs/Context/2026-05-23-ai-team-implementation-architecture.md
- reports/orchestrator/latest-cycle.json
- reports/agent-dispatch-plan.json
- reports/predictability-validation.json
- tasks/TASK-001-architecture-contract-alignment.yml
- tasks/TASK-011-ai-orchestrator.yml

Не меняй Scope.md, Vision.md, runtime product architecture или бизнес-модель. Не подключай production dependencies. Не читай .env, credentials, secrets, real PII или real pilot price. Не запускай deploy/publish/git push. Не используй LLM как источник цены.

Нужно спроектировать и при возможности реализовать узкую доработку AI-team harness. Приоритеты:

1. Evidence hardening:
   - validate that evidence filename matches taskId;
   - validate task exists;
   - validate role/owner matches task card;
   - validate every task.gate_ids entry is covered by evidence.gateResults;
   - validate passed gates have non-empty evidence;
   - validate changedFiles and evidence paths exist or are explicitly marked external/not_applicable;
   - keep not_run honest with required reason.

2. Dependency closure hardening:
   - dispatcher/orchestrator must not treat dependency as closed by task status alone;
   - dependency is closed only by accepted/done task status plus valid evidence report, or explicit Architect override;
   - document the acceptance/status update rule.

3. Stale approval protection:
   - proposal should include hashes or summaries of task cards, dispatch plan, validation report and inbox state;
   - approve should rerun or compare these inputs and block if proposal is stale.

4. Read-only validation:
   - add `--check` or `--no-write` mode to `harness/scripts/validate_predictability.py`;
   - default behavior may still write reports if existing workflows require it.

5. Slice acceptance:
   - define machine-readable slice acceptance report contract and file locations;
   - do not overbuild implementation before TASK-001 acceptance.

6. RACI/conflict-resolution:
   - document ownership boundaries between Architect, SolutionArchitect, PPM, AIOrchestrator, QAEngineer, DomainAnalyst, SeniorCeilingEstimator, BackendDeveloper and EstimationEngineDeveloper.

Expected outputs:
- updated docs describing the AI-team harness improvements;
- if code is changed, small scoped patches only in harness/scripts and related contracts;
- updated or new gates only if necessary;
- evidence report for the task if the task card requires it;
- clear handoff: what changed, what checks ran, what remains blocked.

Acceptance criteria:
- AIOrchestrator remains development-time only;
- command packets still require explicit architect approval;
- no real PII, real price or secrets are introduced;
- task evidence becomes less self-attested and more mechanically checked;
- next MVP-0 implementation wave cannot start from stale or unevidenced dependencies.
```

## 7. Как использовать этот контекст

Перед запуском следующего AI-team hardening task архитектор должен решить:

- делать это как отдельную micro-task перед `TASK-001`, или включить в `TASK-001` acceptance;
- менять ли task statuses вручную после valid evidence или добавить отдельный accepted report;
- насколько глубоко усиливать harness до workspace baseline.

Рекомендуемый путь: не расширять Scope и не блокировать MVP-0 бесконечным meta-process. Сделать минимальный hardening, который закрывает stale approval, evidence coverage and dependency closure.
