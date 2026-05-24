#!/usr/bin/env python3
"""Validate ProSmet AI employee profiles without network or secrets."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from _agent_common import ROLE_PROFILES, ROOT


REPORT_PATH = ROOT / "reports/agent-profiles-validation.json"
DISPATCH_REPORT_PATH = ROOT / "reports/agent-dispatch-plan.json"
PREDICTABILITY_REPORT_PATH = ROOT / "reports/predictability-validation.json"
ORCHESTRATOR_SCRIPT = ROOT / "harness/scripts/ai_orchestrator.py"
REQUIRED_FORBIDDEN_MARKERS = [
    "tenantId",
    "ПД",
    "деньги",
    "LLM",
    "auto_publish",
]
REQUIRED_CONTEXT_DOC = "docs/Context/2026-05-19-autonomous-mvp-feedback.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def role_names_from_team() -> list[str]:
    text = read(ROOT / "Team.yml")
    roles: list[str] = []
    in_roles = False
    for line in text.splitlines():
        if line.strip() == "roles:":
            in_roles = True
            continue
        if in_roles:
            match = re.match(r"^    ([A-Za-z][A-Za-z0-9]+):\s*$", line)
            if match:
                roles.append(match.group(1))
            elif line and not line.startswith(" "):
                break
    return roles


def parse_task_cards() -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    for path in sorted((ROOT / "tasks").glob("TASK-*.yml")):
        text = read(path)
        card: dict[str, Any] = {"path": str(path.relative_to(ROOT))}
        for key in ["id", "title", "role", "owner", "status"]:
            match = re.search(rf'^\s+{key}:\s+"?([^"\n]+)"?\s*$', text, re.MULTILINE)
            if match:
                card[key] = match.group(1)
        card["dependencies"] = parse_list(text, "dependencies")
        card["micro_tasks"] = parse_list(text, "micro_tasks")
        card["gate_ids"] = parse_list(text, "gate_ids")
        cards[card.get("id", path.stem)] = card
    return cards


def unquote(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def parse_list(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    result: list[str] = []
    capture = False
    for line in lines:
        if re.match(rf"^\s+{re.escape(key)}:\s*$", line):
            capture = True
            continue
        if capture:
            if re.match(r"^\s+[a-zA-Z_]+:", line):
                break
            match = re.match(r"^\s+-\s*(.+?)\s*$", line)
            if match:
                result.append(unquote(match.group(1)))
    return result


def check_help(script: Path) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=10,
        check=False,
    )
    return result.returncode == 0, result.stdout.strip().splitlines()[0] if result.stdout else ""


def script_imports_are_safe(script: Path) -> list[str]:
    tree = ast.parse(read(script), filename=str(script))
    issues: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            lowered = node.value.lower()
            if ".env" in lowered or "credential" in lowered or "secret" in lowered:
                issues.append(f"forbidden literal in {script.name}: {node.value}")
    return issues


def dependency_cycles(cards: dict[str, dict[str, Any]]) -> list[list[str]]:
    graph = {task_id: card.get("dependencies", []) for task_id, card in cards.items()}
    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> None:
        if node in visiting:
            if node in stack:
                cycles.append(stack[stack.index(node) :] + [node])
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for dep in graph.get(node, []):
            if dep in graph:
                visit(dep)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return cycles


def main() -> int:
    roles_from_team = role_names_from_team()
    cards = parse_task_cards()
    report: dict[str, Any] = {
        "status": "pass",
        "roles_from_team": roles_from_team,
        "roles_in_registry": sorted(ROLE_PROFILES.keys()),
        "checks": [],
        "issues": [],
    }

    def issue(message: str) -> None:
        report["status"] = "fail"
        report["issues"].append(message)

    if sorted(roles_from_team) != sorted(ROLE_PROFILES.keys()):
        issue("Team.yml roles do not match ROLE_PROFILES registry.")

    build_team = read(ROOT / "harness/build-team.md")
    for role_name, profile in ROLE_PROFILES.items():
        claude = ROOT / ".claude/agents" / f"{profile['slug']}.md"
        codex = ROOT / ".codex/agents/roles" / role_name / "profile.md"
        script = ROOT / "harness/scripts/agents" / profile["script"]

        for path in [claude, codex, script]:
            if not path.exists():
                issue(f"Missing {path.relative_to(ROOT)} for {role_name}.")

        if f"## {role_name}" not in build_team:
            issue(f"Missing harness/build-team.md section for {role_name}.")

        if claude.exists():
            text = read(claude)
            for marker in REQUIRED_FORBIDDEN_MARKERS:
                if marker not in text:
                    issue(f"Claude profile {claude.name} lacks marker {marker}.")
            if REQUIRED_CONTEXT_DOC not in text:
                issue(f"Claude profile {claude.name} lacks required context doc.")

        if codex.exists():
            text = read(codex)
            for marker in ["role_id:", "helper:", "handoff_required: true", "forbidden_codes:"]:
                if marker not in text:
                    issue(f"Codex profile {role_name} lacks {marker}.")
            if REQUIRED_CONTEXT_DOC not in text:
                issue(f"Codex profile {role_name} lacks required context doc.")

        if script.exists():
            ok, first_line = check_help(script)
            if not ok:
                issue(f"Helper --help failed for {script.name}: {first_line}")
            for script_issue in script_imports_are_safe(script):
                issue(script_issue)

    valid_roles = set(ROLE_PROFILES.keys())
    for task_id, card in cards.items():
        for key in ["role", "owner"]:
            if card.get(key) not in valid_roles:
                issue(f"{card['path']} has invalid {key}: {card.get(key)}")
        for dep in card.get("dependencies", []):
            if dep not in cards:
                issue(f"{card['path']} depends on missing {dep}")
        if card.get("status") == "epic":
            if not card.get("micro_tasks"):
                issue(f"{card['path']} is epic but has no micro_tasks.")
            for micro_task in card.get("micro_tasks", []):
                if micro_task not in cards:
                    issue(f"{card['path']} references missing micro task {micro_task}")
        elif not card.get("gate_ids"):
            issue(f"{card['path']} has no gate_ids.")

    cycles = dependency_cycles(cards)
    if cycles:
        issue(f"Task dependency cycles: {cycles}")

    legacy_qa = ROOT / ".claude/agents/qa-evaluator.md"
    if legacy_qa.exists():
        issue("Legacy duplicate .claude/agents/qa-evaluator.md should not exist; use qa-engineer.md.")

    dispatch_script = ROOT / "harness/scripts/agents/dispatch_tasks.py"
    if not dispatch_script.exists():
        issue("Missing harness/scripts/agents/dispatch_tasks.py.")
    else:
        ok, first_line = check_help(dispatch_script)
        if not ok:
            issue(f"Dispatch --help failed: {first_line}")
        dispatch_result = subprocess.run(
            [
                sys.executable,
                str(dispatch_script),
                "--report",
                str(DISPATCH_REPORT_PATH.relative_to(ROOT)),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
            check=False,
        )
        if dispatch_result.returncode != 0:
            issue(f"Dispatch plan failed: {dispatch_result.stdout.strip()}")
        elif DISPATCH_REPORT_PATH.exists():
            dispatch_report = json.loads(read(DISPATCH_REPORT_PATH))
            if not dispatch_report.get("available_now"):
                issue("Dispatch plan has no available_now tasks.")
            if not dispatch_report.get("execution_waves"):
                issue("Dispatch plan has no execution_waves.")
            report["dispatch_report"] = str(DISPATCH_REPORT_PATH.relative_to(ROOT))
        else:
            issue("Dispatch report was not created.")

    predictability_script = ROOT / "harness/scripts/validate_predictability.py"
    if not predictability_script.exists():
        issue("Missing harness/scripts/validate_predictability.py.")
    else:
        predictability_result = subprocess.run(
            [sys.executable, str(predictability_script)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
            check=False,
        )
        if predictability_result.returncode != 0:
            issue(f"Predictability validation failed: {predictability_result.stdout.strip()}")
        elif PREDICTABILITY_REPORT_PATH.exists():
            report["predictability_report"] = str(PREDICTABILITY_REPORT_PATH.relative_to(ROOT))
        else:
            issue("Predictability report was not created.")

    if not ORCHESTRATOR_SCRIPT.exists():
        issue("Missing harness/scripts/ai_orchestrator.py.")
    else:
        ok, first_line = check_help(ORCHESTRATOR_SCRIPT)
        if not ok:
            issue(f"AI orchestrator --help failed: {first_line}")

    report["task_cards"] = cards
    report["checks"].append("roles_match_team")
    report["checks"].append("claude_profiles_exist")
    report["checks"].append("codex_profiles_exist")
    report["checks"].append("helpers_support_help")
    report["checks"].append("task_cards_roles_and_dependencies")
    report["checks"].append("task_dependency_graph_acyclic")
    report["checks"].append("context_doc_in_all_profiles")
    report["checks"].append("no_qa_evaluator_duplicate")
    report["checks"].append("dispatch_plan_generated")
    report["checks"].append("predictability_validation_generated")
    report["checks"].append("ai_orchestrator_help")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Agent profile validation: {report['status']}")
    print(f"Roles: {len(ROLE_PROFILES)}")
    print(f"Task cards: {len(cards)}")
    print(f"Report: {REPORT_PATH.relative_to(ROOT)}")
    if report["issues"]:
        print("Issues:")
        for item in report["issues"]:
            print(f"- {item}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
