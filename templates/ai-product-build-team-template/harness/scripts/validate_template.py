#!/usr/bin/env python3
"""Validate base portable template structure."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "README.md",
    "NEW_CHAT_PROMPT.md",
    "AGENTS.template.md",
    "Team.template.yml",
    "docs/AI_M_MSF.md",
    "docs/ArchitecturePreparationGuide.md",
    "docs/AgentSouls.md",
    "docs/RoleCatalog.md",
    "docs/TaskAndEvidenceProtocol.md",
    "docs/QualityGatesTemplate.md",
    "tasks/task_template.yml",
    "harness/scripts/agents/_agent_common.py",
    "harness/scripts/agents/dispatch_tasks.py",
    "harness/scripts/ai_orchestrator.py",
]


def main() -> None:
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    print("Template validation:", "pass" if not missing else "fail")
    print(f"Root: {ROOT}")
    if missing:
        for path in missing:
            print(f"- missing {path}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
