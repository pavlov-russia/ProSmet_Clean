#!/usr/bin/env python3
"""Build a dry-run dispatch plan from task cards."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from _agent_common import ROLE_PROFILES, ROOT, STANDARD_DOCS


REPORT = ROOT / "reports/agent-dispatch-plan.json"
COMPLETED = {"done", "complete", "completed", "accepted", "closed"}
WORKABLE = {"ready", "in_progress"}
EPIC = {"epic"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def unquote(value: str) -> str:
    value = value.strip()
    return value[1:-1] if value.startswith('"') and value.endswith('"') else value


def parse_scalar(text: str, key: str) -> str:
    match = re.search(rf'^\s+{re.escape(key)}:\s*"?([^"\n]+)"?\s*$', text, re.MULTILINE)
    return match.group(1).strip() if match else ""


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


def cards() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted((ROOT / "tasks").glob("TASK-*.yml")):
        text = read(path)
        task_id = parse_scalar(text, "id") or path.stem
        role = parse_scalar(text, "role")
        owner = parse_scalar(text, "owner") or role
        result[task_id] = {
            "id": task_id,
            "title": parse_scalar(text, "title"),
            "role": role,
            "owner": owner,
            "status": (parse_scalar(text, "status") or "draft").lower(),
            "slice": parse_scalar(text, "slice"),
            "work_package": parse_scalar(text, "work_package"),
            "path": str(path.relative_to(ROOT)),
            "dependencies": parse_list(text, "dependencies"),
            "source_docs": parse_list(text, "source_docs"),
            "gate_ids": parse_list(text, "gate_ids"),
            "required_reports": parse_list(text, "required_reports"),
            "handoff_to": parse_list(text, "handoff_to"),
            "micro_tasks": parse_list(text, "micro_tasks"),
        }
    return result


def with_prompt(card: dict[str, Any]) -> dict[str, Any]:
    profile = ROLE_PROFILES.get(card["owner"], {})
    docs = []
    for item in STANDARD_DOCS + card["source_docs"]:
        if item not in docs:
            docs.append(item)
    prompt = (
        f"Ты {card['owner']} AI Product Build Team. Возьми {card['id']} ({card['title']}). "
        f"Task card: {card['path']}. Must read: {', '.join(docs)}. "
        f"Gate ids: {', '.join(card['gate_ids']) or 'none'}. "
        f"Required reports: {', '.join(card['required_reports']) or 'none'}. "
        "Работай строго в Scope, не читай .env/credentials, не делай deploy. "
        "В конце создай machine-readable evidence report."
    )
    return {
        **card,
        "helper": f"harness/scripts/agents/{profile.get('script', '')}",
        "codexProfile": f".codex/agents/roles/{card['owner']}/profile.md",
        "claudeProfile": f".claude/agents/{profile.get('slug', card['owner'].lower())}.md",
        "must_read": docs,
        "dispatch_prompt": prompt,
    }


def build_plan(completed_override: set[str] | None = None) -> dict[str, Any]:
    completed_override = completed_override or set()
    all_cards = cards()
    completed = {
        task_id for task_id, card in all_cards.items() if card["status"] in COMPLETED
    } | completed_override
    available: list[dict[str, Any]] = []
    blocked_by_dependencies: dict[str, list[str]] = {}
    blocked_by_status: dict[str, str] = {}
    work_packages: list[str] = []

    for task_id, card in all_cards.items():
        if task_id in completed:
            continue
        if card["status"] in EPIC:
            work_packages.append(task_id)
            continue
        unresolved = [dep for dep in card["dependencies"] if dep not in completed]
        if unresolved:
            blocked_by_dependencies[task_id] = unresolved
        elif card["status"] in WORKABLE:
            available.append(with_prompt(card))
        else:
            blocked_by_status[task_id] = card["status"]

    plan = {
        "status": "ready" if available else "blocked",
        "tasks": len(all_cards),
        "roles": len(ROLE_PROFILES),
        "workPackages": len(work_packages),
        "completed": sorted(completed),
        "available_now": available,
        "blocked_by_dependencies": blocked_by_dependencies,
        "blocked_by_status": blocked_by_status,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Build task dispatch plan.")
    parser.add_argument("--completed", action="append", default=[], help="Treat task as completed.")
    args = parser.parse_args()
    plan = build_plan(set(args.completed))
    print(f"Agent dispatch plan: {plan['status']}")
    print(f"Tasks: {plan['tasks']}")
    print(f"Roles: {plan['roles']}")
    print(f"Available now: {len(plan['available_now'])}")
    for task in plan["available_now"]:
        print(f"- {task['id']} {task['title']} -> {task['owner']}")
    print(f"Report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

