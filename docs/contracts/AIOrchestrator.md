# AIOrchestrator

Дата: 2026-05-23  
Статус: контракт development-time AI-оркестратора

## Назначение

AIOrchestrator управляет процессом разработки ProSmet как локальный control plane:

- читает task cards и dispatch plan;
- сверяет dependency graph, evidence, inbox и gates;
- предлагает следующий управляемый цикл;
- просит явное согласие архитектора-человека;
- после согласия выпускает command packets для AI-сотрудников;
- собирает обратную связь о ходе, рисках и корректировках плана.

Это не runtime-агент продукта и не часть клиентского MVP. Runtime ProSmet по-прежнему содержит только разрешенные AI-функции: сбор/нормализация параметров и объяснение уже рассчитанной сметы без денег в LLM payload.

## Python brain

Исполняемый мозг:

```bash
python3 harness/scripts/ai_orchestrator.py propose
python3 harness/scripts/ai_orchestrator.py approve --cycle reports/orchestrator/latest-cycle.json --approved-by Architect
python3 harness/scripts/ai_orchestrator.py status
```

Скрипт использует только стандартную библиотеку Python и существующий `harness/scripts/agents/dispatch_tasks.py`.

## Цикл работы

1. Orchestrator строит proposal и пишет:

```text
reports/orchestrator/latest-cycle.json
reports/orchestrator/ORCH-CYCLE-YYYYMMDD-HHMMSS.json
```

2. Архитектор читает proposal: selected tasks, watch points, plan corrections, validations and next action.
3. Если архитектор согласен, он запускает `approve`.
4. Только после approval появляются command packets:

```text
workspace/orchestrator/outbox/ORCH-CYCLE-*-TASK-*.json
workspace/orchestrator/outbox/ORCH-CYCLE-*-TASK-*.md
```

5. AI-сотрудники выполняют command packets и создают свои evidence reports в `reports/task-evidence/TASK-ID.json`.
6. Orchestrator снова запускается через `propose` и решает следующий цикл.

Перед выпуском command packets `approve` заново читает Architect Inbox. Если появился blocking `ArchitectInterventionRequest`, price request без synthetic fallback или ошибка inbox, approval останавливается. Обойти это можно только через `--force` после явного решения архитектора.

## Полномочия

AIOrchestrator может:

- выбирать следующий executable task или wave из dispatch plan;
- ограничивать параллелизм;
- требовать evidence reports;
- подсвечивать blockers, missing evidence, failed checks and open inbox requests;
- предлагать корректировку плана;
- создавать reports and command packets после approval.

AIOrchestrator не может:

- сам запускать внешних AI-агентов или CLI без отдельного решения архитектора;
- менять `Scope.md`;
- читать `.env`, credentials, secrets, real PII or real pilot price;
- ходить в сеть;
- выполнять deploy, publish, git push или destructive migration;
- считать цены, коэффициенты, скидки или строки сметы;
- принимать решение публикации клиенту;
- обходить task dependencies, gate ids, evidence reports или slice acceptance.

## Safety defaults

Orchestrator по умолчанию:

- development-time only;
- dry-run до approval;
- не spawn-ит агентов;
- не меняет task cards;
- пишет только reports/workspace artifacts;
- требует явного approval для command packets;
- блокируется на failed validations и blocking inbox/price requests.
- повторно проверяет Architect Inbox на этапе `approve`, чтобы старый proposal не обошел новый blocker.

## Предпочтения управления

- Сначала закрывать contract/evidence gates, потом расширять функциональность.
- До приемки architecture prep держать параллелизм низким.
- После baseline scaffold и QA harness параллелить только независимые роли и write scopes.
- Каждый command packet должен требовать конкретный evidence report.
- Любой real price, real PII, deploy, Scope или legal blocker превращать в inbox request.
- План менять маленькими корректировками, чтобы dependency graph оставался машинно проверяемым.

## Machine-readable schema

Цикл proposal/approval описан схемой:

```text
docs/contracts/schemas/ai-orchestrator-cycle-v1.schema.json
```
