# AI Employee Command Packet

Cycle: `ORCH-CYCLE-20260524-122641`  
Task: `TASK-001` · Architecture contract alignment  
Owner: `Architect`  
Approved by: `Architect`

## Must Read

- `AGENTS.md`
- `EntryPointForTask.md`
- `docs/AI_M_MSF.md`
- `Focus.md`
- `Team.yml`
- `docs/Context/2026-05-19-autonomous-mvp-feedback.md`
- `Scope.md`
- `docs/dev/ImplementationPlan.md`
- `docs/dev/PredictableAIWork.md`
- `Vision.md`
- `docs/ConceptualDesign.md`
- `docs/SolutionDesign.md`
- `docs/Architecture.md`
- `docs/ADR/`
- `Backlogs.md`
- `harness/build-team.md`
- `docs/Evals/QualityGates.md`
- `docs/contracts/README.md`
- `docs/contracts/ContractManifest.json`
- `docs/contracts/AgentTaskEvidence.md`
- `docs/contracts/ArchitectInterventionRequest.md`
- `docs/contracts/PriceInputRequest.md`
- `docs/Evals/GateMatrix.md`
- `docs/contracts/API.md`
- `docs/contracts/DataModelRLS.md`
- `docs/contracts/PublicationPolicy.md`

## Gate IDs

AGENT.TASK_CARD.READY, CONTRACT.MANIFEST.SCHEMAS, ARCHITECT.INTERVENTION.REQUEST_PROTOCOL, FIXTURES.GOLDEN.SYNTHETIC, PRICE.INPUT.REQUEST_PROTOCOL

## Expected Evidence

reports/task-evidence/TASK-001.json

## Architect Inbox Protocol

- If an Ask First blocker appears, create `workspace/architect-inbox/requests/ARCH-REQUEST-*.json`.
- If real price is needed, create `reports/price-requests/PRICE-REQUEST-*.json`.
- Mention the created request path in handoff/final.

## Dispatch Prompt

```text
Ты Architect AI Build Team ProSmet. Возьми TASK-001 (Architecture contract alignment). Slice: architecture_prep; work package: TASK-001. Сначала прочитай полный must_read список: AGENTS.md, EntryPointForTask.md, docs/AI_M_MSF.md, Focus.md, Team.yml, docs/Context/2026-05-19-autonomous-mvp-feedback.md, Scope.md, docs/dev/ImplementationPlan.md, docs/dev/PredictableAIWork.md, Vision.md, docs/ConceptualDesign.md, docs/SolutionDesign.md, docs/Architecture.md, docs/ADR/, Backlogs.md, harness/build-team.md, docs/Evals/QualityGates.md, docs/contracts/README.md, docs/contracts/ContractManifest.json, docs/contracts/AgentTaskEvidence.md, docs/contracts/ArchitectInterventionRequest.md, docs/contracts/PriceInputRequest.md, docs/Evals/GateMatrix.md, docs/contracts/API.md, docs/contracts/DataModelRLS.md, docs/contracts/PublicationPolicy.md. Task card: tasks/TASK-001-architecture-contract-alignment.yml. Запусти helper `harness/scripts/agents/architect.py` для контекста роли. Gate ids: AGENT.TASK_CARD.READY, CONTRACT.MANIFEST.SCHEMAS, ARCHITECT.INTERVENTION.REQUEST_PROTOCOL, FIXTURES.GOLDEN.SYNTHETIC, PRICE.INPUT.REQUEST_PROTOCOL. Required reports: reports/task-evidence/TASK-001.json, reports/predictability-validation.json. Работай строго в Scope, не читай .env/credentials, не ослабляй tenant/AI-money/publication gates. В конце дай handoff и machine-readable evidence report with changed files, checks, gate results, blockers and next executor.
```
