# Gate Matrix

Дата: 2026-05-23
Статус: machine-checkable индекс gates для разработки AI-сотрудниками

## Назначение

`docs/Evals/QualityGates.md` остается человеческим описанием качества. `docs/Evals/gates.json` является машинно-проверяемым индексом: каждый gate имеет id, владельца, slice, evidence и future command.

Task card ссылается на gates через `gate_ids`. Если gate отсутствует в `gates.json`, task не готова к исполнению.

## Правила

- Gate нельзя считать passed без evidence-отчета.
- `not_run` допустим только с причиной.
- Gate, связанный с расчетом, AI payload, tenant isolation или publication, блокирует следующий slice.
- Synthetic fixtures разрешены для разработки, но не являются реальным пилотным прайсом.
- Real PII, real pilot price и production deploy требуют отдельного решения архитектора.

## Группы

- `AGENT.*` — дисциплина AI-сотрудника, task card и evidence.
- `AGENT.ORCHESTRATOR.*` — локальный AI-оркестратор, approval-before-dispatch and command packets.
- `CONTRACT.*` — machine-checkable contracts и schema manifest.
- `FIXTURES.*` — synthetic fixtures and seed data.
- `DEV.*` — scaffold and local commands.
- `SECURITY.*` — tenant isolation, RLS, PII audit.
- `CALC.*` — deterministic calculation and partial estimate.
- `AI.*` — AI payload safety.
- `POLICY.*` — deterministic approval policy.
- `PUBLICATION.*` — link/PDF gates.
- `UI.*` — widget, owner dashboard, visual identity, marketing site, browser smoke.
- `CI.*` — no-secret CI and quality gate reporting.

## Файл

Machine-readable gate list:

```text
docs/Evals/gates.json
```
