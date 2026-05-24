# Handoff 06 · Predictable AI Development Harness

Дата: 2026-05-23
Автор / роль: Codex / Architect + PPM + QA hardening
Родительская задача: pre-implementation predictability hardening

## Что сделано

- Добавлен протокол управляемой работы AI-сотрудников: `docs/dev/PredictableAIWork.md`.
- Добавлена machine-readable gate matrix: `docs/Evals/GateMatrix.md`, `docs/Evals/gates.json`.
- Добавлен contract manifest and JSON Schemas: `docs/contracts/ContractManifest.json`, `docs/contracts/schemas/`.
- Добавлены synthetic engineering fixtures: golden estimates, stub price book, coefficients, pricing profile, markup policy.
- Добавлены tenant A/B seed data and AI payload safety corpus.
- Wide tasks `TASK-002`...`TASK-010` переведены в work packages.
- Добавлены executable micro-tasks `TASK-002A`...`TASK-010B`.
- Добавлен валидатор `harness/scripts/validate_predictability.py`.
- Dispatcher and profile validator updated to understand micro-task metadata, gate ids and work packages.
- Добавлен `PriceInputRequest` protocol: AI-сотрудник обязан создать machine-readable запрос, если для продолжения нужен реальный прайс.
- Добавлен `ArchitectInterventionRequest` and `workspace/architect-inbox/`: AI-сотрудник обязан создать request для любых Ask First решений.
- Добавлен `harness/scripts/architect_inbox.py` для просмотра открытых запросов архитектором.

## Проверки

- `python3 harness/scripts/validate_predictability.py` — pass.
- `python3 harness/scripts/agents/validate_agent_profiles.py` — pass.
- `python3 harness/scripts/agents/dispatch_tasks.py --completed TASK-001` — pass, shows next executable tasks `TASK-002A` and `TASK-010A`.
- `python3 harness/scripts/architect_inbox.py` — pass, shows open requests if any.
- `python3 -m py_compile harness/scripts/validate_predictability.py harness/scripts/agents/dispatch_tasks.py harness/scripts/agents/validate_agent_profiles.py harness/scripts/agents/_agent_common.py` — pass.

`npm run format:check` and `npm run lint` не запускались: в текущем окружении `npm`/`node` отсутствуют в PATH.

## Blockers

- Real expert/pilot-approved golden estimates still need human/pilot input.
- Real pilot price, legal pack, bot channel and production PII readiness remain product/architect decisions.
- `future:*` commands in `docs/Evals/gates.json` must be replaced by real commands as implementation lands.

## Следующий исполнитель

- Architect/QAEngineer: close `TASK-001` with evidence.
- DevOps: `TASK-002A`.
- QAEngineer: `TASK-010A`.

## Подтверждения

- Scope не расширен.
- Секреты и `.env*` не читались.
- Tenant isolation / AI-money invariants не ослаблены.
- Synthetic fixtures не являются реальным пилотным прайсом.
- Чужие изменения не откатывались.
