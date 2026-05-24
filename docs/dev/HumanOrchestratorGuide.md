# Human Orchestrator Guide

Дата: 2026-05-24  
Статус: рабочий регламент для архитектора/оркестратора AI-команды ProSmet

## 1. Твоя роль

Ты управляешь не "чатом с агентами", а локальным development-time control plane.

Практически это означает: ты в основном коммуницируешь с AIOrchestrator/Architect loop, а не вручную микроменеджишь каждого AI-сотрудника.

AIOrchestrator должен:

- предложить следующий цикл;
- показать blockers, corrections and watch points;
- после твоего approval выпустить command packets;
- проверить inbox, dependencies, gates and evidence;
- остановить процесс, если появился блокер.

Ты нужен не как ручной диспетчер задач, а как владелец решений, которые AI не имеет права принимать сам:

- принимаешь решения, которые AI не имеет права принимать сам;
- утверждаешь orchestration cycles;
- подтверждаешь, что предложенный цикл можно выполнять;
- принимаешь или отклоняешь architect/price requests;
- смотришь итоговую evidence summary по задаче или wave;
- не разрешаешь обходить Scope, tenant isolation, deterministic calculation, AI payload safety, human review and publication gates.

AIOrchestrator не заменяет твое approval, но именно он должен быть основным интерфейсом управления процессом.

## 1.1. Где живут решения

Решения не должны оставаться только в переписке.

Операционные решения цикла:

```text
reports/orchestrator/latest-cycle.json
reports/orchestrator/ORCH-CYCLE-*.json
reports/orchestrator/ORCH-CYCLE-*-approved.json
workspace/orchestrator/approvals/
```

Что смотреть:

- `selectedTasks`: что AIOrchestrator предлагает делать;
- `feedback.planCorrections`: что надо применить или исправить;
- `feedback.watchPoints`: риски текущего цикла;
- `consent`: кто и с какой заметкой утвердил цикл;
- `commandPackets`: какие задания выпущены после approval.

Решения, которые AI не имеет права принимать сам:

```text
workspace/architect-inbox/requests/ARCH-REQUEST-*.json
reports/price-requests/PRICE-REQUEST-*.json
```

Что с ними делать:

- выбрать option или дать короткое решение;
- если решение архитектурное, закрепить его в ADR или contract-doc;
- если решение меняет план, обновить task card, `Backlogs.md`, `Focus.md` or `docs/dev/ImplementationPlan.md`;
- после выполнения зависимой части убедиться, что evidence report ссылается на принятое решение.

Текущий gap: отдельного `ArchitectDecisionResponse` контракта пока нет. До его появления решение считается примененным только если оно закреплено в ADR, contract-doc, task card, backlog/focus update or evidence report. Если нужен строгий machine-readable close для requests, это отдельная harness-hardening задача.

Долгоживущие решения:

```text
docs/ADR/
docs/contracts/
docs/dev/ImplementationPlan.md
Focus.md
Backlogs.md
tasks/TASK-*.yml
reports/task-evidence/TASK-ID.json
```

Правило: если решение влияет на архитектуру, Scope boundary, gates, dependencies or product behavior, оно должно стать документным контрактом, task change, ADR, backlog item or evidence. Иначе команда не сможет воспроизводимо его применить.

## 2. Базовый цикл управления

Каждый цикл выглядит так:

```text
status/checks -> propose -> review -> approve -> execute task packets -> evidence -> next propose
```

Команды:

```bash
python3 harness/scripts/validate_predictability.py
python3 harness/scripts/agents/dispatch_tasks.py
python3 harness/scripts/architect_inbox.py
python3 harness/scripts/ai_orchestrator.py propose
```

Если proposal нормальный:

```bash
python3 harness/scripts/ai_orchestrator.py approve --cycle reports/orchestrator/latest-cycle.json --approved-by Architect --decision-note "approved next AI employee cycle"
```

После approval command packets появляются в:

```text
workspace/orchestrator/outbox/
```

Задача считается закрытой только после:

```text
reports/task-evidence/TASK-ID.json
```

## 3. Что читать в proposal

В `reports/orchestrator/latest-cycle.json` смотри:

- `status`: можно ли approve;
- `selectedTasks`: какие задачи предлагаются;
- `validations`: прошли ли локальные проверки;
- `architectInbox`: есть ли blocking requests;
- `developmentState.blockedByDependencies`: почему следующие задачи еще закрыты;
- `feedback.watchPoints`: на что обратить внимание;
- `feedback.planCorrections`: что надо изменить до запуска.

Если `status` не `ready_for_architect_approval`, не утверждай цикл без понятной причины.

## 4. Как выдавать работу AI-сотруднику

В текущей версии harness AIOrchestrator выпускает command packets, но сам не spawn-ит внешних AI-агентов. Это намеренное ограничение v1: запуск другого AI/CLI имеет побочные эффекты, поэтому пока требует явного человеческого approval.

Целевая рабочая модель:

```text
ты -> AIOrchestrator/Architect -> approved command packets -> AI-сотрудники -> evidence -> AIOrchestrator
```

То есть ты не должен придумывать задачи каждому сотруднику. Ты утверждаешь цикл и используешь packet, который подготовил AIOrchestrator.

Открой markdown command packet:

```text
workspace/orchestrator/outbox/ORCH-CYCLE-*-TASK-*-role.md
```

Передай AI-сотруднику весь `Dispatch Prompt` из packet. Он уже содержит:

- роль;
- task card;
- must-read документы;
- gate ids;
- required reports;
- stop rules;
- evidence path.

Не давай сотруднику широкую формулировку вроде "сделай MVP". Давай только конкретную micro-task из outbox.

Если работа идет внутри одного Codex/Claude сеанса, можно сказать: "выполни command packet для TASK-XXX". Это все равно считается запуском через AIOrchestrator, потому что источником задания является approved packet, а не свободная формулировка.

## 5. Как принимать работу

AIOrchestrator должен подсветить missing evidence and blockers, но финальное доверие к задаче строится на machine-readable evidence.

После работы AI-сотрудника проверь:

```bash
python3 harness/scripts/validate_predictability.py
python3 harness/scripts/agents/dispatch_tasks.py
python3 harness/scripts/architect_inbox.py
python3 harness/scripts/ai_orchestrator.py status
```

Минимальная приемка:

- есть `reports/task-evidence/TASK-ID.json`;
- task id, role and changed files соответствуют задаче;
- checks не помечены `passed`, если они не запускались;
- gate results ссылаются на реальные файлы/проверки;
- нет новых open architect/price requests;
- задача не расширила `Scope.md`;
- не ослаблены tenant/RLS, deterministic calculation, AI money boundary, publication policy.

Если evidence нет, задача не done.

Если хочешь не читать каждый report вручную, проси AIOrchestrator/Architect сделать acceptance summary по новой evidence. Но summary не заменяет сам файл `reports/task-evidence/TASK-ID.json`.

## 6. Когда останавливать команду

AIOrchestrator обязан блокировать approval при failed validations, open blocking inbox requests, price requests without synthetic fallback and missing dependencies.

Ты вмешиваешься только если AIOrchestrator просит решение или если видишь, что команда пытается обойти стоп-правило.

Стоп-блокеры:

- нужен реальный прайс, коэффициенты, скидки, минимальный заказ or expert-approved golden totals;
- нужны реальные ПД, pilot data, secrets or external service;
- требуется изменить `Scope.md`;
- требуется production dependency, deploy, publish or destructive migration;
- задача хочет обойти dependency graph, gate ids or evidence;
- LLM оказывается в цепочке расчета цены, скидки, коэффициента или строки сметы.

Правильный результат блокера:

- `reports/price-requests/PRICE-REQUEST-*.json` для реального прайса;
- `workspace/architect-inbox/requests/ARCH-REQUEST-*.json` для решения архитектора.

Смотреть все запросы:

```bash
python3 harness/scripts/architect_inbox.py
```

## 7. Как управлять параллелизмом

До закрытия `TASK-001` держи один активный task: architecture prep acceptance.

После `TASK-001` можно параллелить только независимые задачи из одной wave:

```bash
python3 harness/scripts/agents/dispatch_tasks.py
```

Пример ближайшей волны после `TASK-001`:

- `TASK-002A`: workspace baseline;
- `TASK-010A`: baseline QA harness.

Не запускай задачи из будущих waves вручную, если dependency graph не показывает, что они открыты.

## 8. Текущая позиция проекта

На 2026-05-24 approved cycle уже выпущен для:

```text
TASK-001 Architecture contract alignment
```

Command packets:

```text
workspace/orchestrator/outbox/ORCH-CYCLE-20260524-122641-TASK-001-architect.md
workspace/orchestrator/outbox/ORCH-CYCLE-20260524-122641-TASK-001-architect.json
```

Следующий нужный артефакт:

```text
reports/task-evidence/TASK-001.json
```

После него снова запусти:

```bash
python3 harness/scripts/ai_orchestrator.py propose
```

## 9. Практическое правило

Каждый день или перед каждой новой волной задавай один вопрос:

```text
Есть ли у нас маленькая executable task с dependencies, gates and evidence?
```

Если да - запускай через command packet.  
Если нет - сначала чинить task card, gate, contract, inbox decision or evidence.
