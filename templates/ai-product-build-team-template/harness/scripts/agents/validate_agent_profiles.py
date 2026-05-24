#!/usr/bin/env python3
"""Validate portable AI team registry and basic task cards."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from _agent_common import ROLE_PROFILES, ROOT


REPORT = ROOT / "reports/agent-profiles-validation.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_scalar(text: str, key: str) -> str:
    match = re.search(rf'^\s+{re.escape(key)}:\s*"?([^"\n]+)"?\s*$', text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def validate() -> dict:
    issues: list[str] = []
    checks: list[str] = []

    team_path = ROOT / "Team.yml"
    if not team_path.exists():
        team_path = ROOT / "Team.template.yml"
    team_text = read(team_path) if team_path.exists() else ""

    for role, profile in ROLE_PROFILES.items():
        if not profile.get("soul"):
            issues.append(f"Role {role} has no soul.")
        if not profile.get("mission"):
            issues.append(f"Role {role} has no mission.")
        if not profile.get("owns"):
            issues.append(f"Role {role} has no owns list.")
        if not profile.get("outputs"):
            issues.append(f"Role {role} has no outputs list.")
        if role not in team_text:
            issues.append(f"Role {role} missing from {team_path.name}.")
        script = ROOT / "harness/scripts/agents" / profile["script"]
        if not script.exists():
            issues.append(f"Missing role script: {script.relative_to(ROOT)}")
            continue
        result = subprocess.run([sys.executable, str(script), "--json"], cwd=ROOT, text=True, capture_output=True)
        if result.returncode != 0:
            issues.append(f"Role helper failed for {role}: {result.stderr.strip()}")
        else:
            checks.append(f"role_helper:{role}")

    task_files = sorted((ROOT / "tasks").glob("TASK-*.yml"))
    for path in task_files:
        text = read(path)
        task_id = parse_scalar(text, "id")
        role = parse_scalar(text, "role")
        owner = parse_scalar(text, "owner") or role
        if not task_id:
            issues.append(f"{path.relative_to(ROOT)} lacks id.")
        if owner and owner not in ROLE_PROFILES:
            issues.append(f"{path.relative_to(ROOT)} references unknown owner {owner}.")

    payload = {
        "status": "pass" if not issues else "fail",
        "roles": len(ROLE_PROFILES),
        "taskCards": len(task_files),
        "checks": checks,
        "issues": issues,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    payload = validate()
    print(f"Agent profile validation: {payload['status']}")
    print(f"Roles: {payload['roles']}")
    print(f"Task cards: {payload['taskCards']}")
    print(f"Report: {REPORT.relative_to(ROOT)}")
    if payload["issues"]:
        for issue in payload["issues"]:
            print(f"- {issue}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
