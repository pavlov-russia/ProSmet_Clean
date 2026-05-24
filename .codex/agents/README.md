# .codex/agents

Codex agent profiles для ProSmet. `AGENTS.md` остается главным harness; эти профили уточняют душу, стек, task protocol и helper scripts роли.

<!-- Generated from harness/scripts/agents/_agent_common.py. Edit registry, then rerun generator. -->

## Canonical Roles

- `roles/AIOrchestrator/profile.md` -> `ai_orchestrator_role.py`
- `roles/Architect/profile.md` -> `architect.py`
- `roles/ProductAnalyst/profile.md` -> `product_analyst.py`
- `roles/BusinessAnalyst/profile.md` -> `business_analyst.py`
- `roles/DomainAnalyst/profile.md` -> `domain_analyst.py`
- `roles/SeniorCeilingEstimator/profile.md` -> `senior_ceiling_estimator.py`
- `roles/SolutionArchitect/profile.md` -> `solution_architect.py`
- `roles/EstimationEngineDeveloper/profile.md` -> `estimation_engineer.py`
- `roles/BackendDeveloper/profile.md` -> `backend_developer.py`
- `roles/FrontendDeveloper/profile.md` -> `frontend_developer.py`
- `roles/AIFlowDeveloper/profile.md` -> `ai_flow_engineer.py`
- `roles/QAEngineer/profile.md` -> `qa_engineer.py`
- `roles/DevOps/profile.md` -> `devops.py`
- `roles/PPM/profile.md` -> `ppm.py`

Shared protocol lives in `_shared/`.

Validate with `python3 harness/scripts/agents/validate_agent_profiles.py`.
