# Implementation Contracts

Дата: 2026-05-23  
Статус: индекс контрактов для реализации

## Назначение

Эта папка переводит архитектурный нарратив ProSmet в контракты, по которым AI-сотрудники могут начинать разработку без свободного додумывания критичных стыков.

Если contract-file противоречит `Scope.md`, ADR или `docs/Evals/QualityGates.md`, кодовая задача останавливается до архитектурного решения.

## Канонический поток

```text
entry
  -> consent
  -> params/chat
  -> blurred/partial preview
  -> phone
  -> immutable calculation snapshot
  -> policy/human review
  -> full link/PDF
```

## Контракты

- `API.md` — contexts, endpoint contracts, tenant resolution, errors, idempotency, audit events, publication/unlock gates.
- `DataModelRLS.md` — RLS matrix, `withTenant`, worker context, signed link tokens, PII access logging, tenant isolation tests.
- `CalculationEngineV1.md` — pure calculation contracts, snapshots, formula registry, partial/unusable semantics, golden fixtures, deterministic tests.
- `AIGateway.md` — safe AI pipeline, schemas, forbidden fields, PII/money redaction, audit record, fallback, eval corpus.
- `PublicationPolicy.md` — approval policy input/decision, reason codes, publication state machine, fail-closed behavior, link/PDF gates.
- `ContractManifest.json` — machine-readable индекс контрактов, схем и fixture folders.
- `schemas/*.schema.json` — JSON Schemas for gate matrix, evidence, fixtures and task cards.
- `AgentTaskEvidence.md` — формат evidence-отчета AI-сотрудника.
- `SeedData.md` — synthetic seed contract for tenant isolation and PII audit tests.
- `PriceInputRequest.md` — формат запроса реального прайса у архитектора, когда synthetic fixtures недостаточны.
- `ArchitectInterventionRequest.md` — формат запроса вмешательства архитектора для Scope, ADR, legal, deploy, external service, PII and product decisions.
- `AIOrchestrator.md` — контракт development-time AI-оркестратора: proposal, approval, command packets and feedback loop.
- `VisualIdentityAndMarketingSite.md` — визуальное направление, стартовая палитра, UX-границы и public marketing site ProSmet.

## Правило использования

Перед началом task card разработчик читает:

1. `AGENTS.md`
2. `EntryPointForTask.md`
3. `docs/AI_M_MSF.md`
4. `docs/Context/2026-05-19-autonomous-mvp-feedback.md`
5. свою task card из `tasks/`
6. `docs/dev/ImplementationPlan.md`
7. релевантный contract-file из этой папки
8. `docs/Evals/QualityGates.md`
9. `docs/Evals/GateMatrix.md` и `docs/Evals/gates.json`, если task содержит `gate_ids`
