#!/usr/bin/env python3
"""Build an automatic AI employee dispatch plan from task cards.

The dispatcher is intentionally dry-run only: it does not spawn agents, does not
read secrets, does not call the network, and does not mutate task cards. It
connects documentation tasks to Claude/Codex profiles and Python helpers so a
human or orchestration layer can launch the right employee with the right docs.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from _agent_common import CANONICAL_FLOW, ROLE_PROFILES, ROOT


DEFAULT_REPORT = ROOT / "reports/agent-dispatch-plan.json"
COMPLETED_STATUSES = {"done", "complete", "completed", "accepted", "closed"}
WORKABLE_STATUSES = {"ready", "in_progress"}
EPIC_STATUSES = {"epic"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def unquote(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def parse_scalar(text: str, key: str) -> str | None:
    match = re.search(rf'^\s+{re.escape(key)}:\s*"?([^"\n]+)"?\s*$', text, re.MULTILINE)
    return match.group(1).strip() if match else None


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
            match = re.match(r'^\s+-\s*(.+?)\s*$', line)
            if match:
                result.append(unquote(match.group(1)))
    return result


def task_cards() -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    for path in sorted((ROOT / "tasks").glob("TASK-*.yml")):
        text = read(path)
        task_id = parse_scalar(text, "id") or path.stem
        role = parse_scalar(text, "role") or ""
        owner = parse_scalar(text, "owner") or role
        card = {
            "id": task_id,
            "title": parse_scalar(text, "title") or "",
            "role": role,
            "owner": owner,
            "status": (parse_scalar(text, "status") or "draft").lower(),
            "slice": parse_scalar(text, "slice") or "",
            "work_package": parse_scalar(text, "work_package") or "",
            "path": str(path.relative_to(ROOT)),
            "source_docs": parse_list(text, "source_docs"),
            "dependencies": parse_list(text, "dependencies"),
            "dependency_notes": parse_mapping_notes(text, "dependency_notes"),
            "handoff_to": parse_list(text, "handoff_to"),
            "quality_gates": parse_list(text, "quality_gates"),
            "gate_ids": parse_list(text, "gate_ids"),
            "required_evidence": parse_list(text, "required_evidence"),
            "required_reports": parse_list(text, "required_reports"),
            "acceptance": parse_list(text, "acceptance"),
            "micro_tasks": parse_list(text, "micro_tasks"),
        }
        cards[task_id] = card
    return cards


def parse_mapping_notes(text: str, key: str) -> dict[str, str]:
    lines = text.splitlines()
    result: dict[str, str] = {}
    capture = False
    current_key: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_lines
        if current_key:
            result[current_key] = " ".join(line.strip() for line in current_lines).strip()
        current_key = None
        current_lines = []

    for line in lines:
        if re.match(rf"^\s+{re.escape(key)}:\s*$", line):
            capture = True
            continue
        if capture:
            if re.match(r"^\s+[a-zA-Z_]+:", line):
                flush()
                break
            match = re.match(r"^\s{4}([A-Za-z0-9_-]+):\s*>?\s*$", line)
            if match:
                flush()
                current_key = match.group(1)
                continue
            if current_key and re.match(r"^\s{6,}\S", line):
                current_lines.append(line)
    if capture:
        flush()
    return result


def role_binding(role_name: str) -> dict[str, Any]:
    profile = ROLE_PROFILES.get(role_name)
    if not profile:
        return {
            "role": role_name,
            "error": "unknown_role",
        }
    return {
        "role": role_name,
        "slug": profile["slug"],
        "title": profile["title"],
        "soul": profile["soul"],
        "claude_profile": f".claude/agents/{profile['slug']}.md",
        "codex_profile": f".codex/agents/roles/{role_name}/profile.md",
        "helper": f"harness/scripts/agents/{profile['script']}",
        "read_first": profile["read_first"],
        "contracts": profile["contracts"],
        "default_tasks": profile["default_tasks"],
        "forbidden": profile["forbidden"],
        "quality_gates": profile["quality_gates"],
        "dispatch_command": f"python3 harness/scripts/agents/{profile['script']} --json",
    }


def task_with_binding(card: dict[str, Any]) -> dict[str, Any]:
    binding = role_binding(card["owner"] or card["role"])
    read_set = []
    if "read_first" in binding:
        read_set.extend(binding["read_first"])
    read_set.extend(card["source_docs"])
    if "contracts" in binding:
        read_set.extend(binding["contracts"])
    return {
        **card,
        "launch_owner": card["owner"] or card["role"],
        "advisory_roles": card["handoff_to"],
        "slice": card["slice"],
        "work_package": card["work_package"],
        "employee": binding,
        "must_read": dedupe(read_set),
        "gate_ids": card["gate_ids"],
        "required_evidence": card["required_evidence"],
        "required_reports": card["required_reports"],
        "acceptance": card["acceptance"],
        "related_profile_tasks": binding.get("default_tasks", []),
        "dispatch_prompt": build_dispatch_prompt(card, binding, dedupe(read_set)),
    }


def build_dispatch_prompt(card: dict[str, Any], binding: dict[str, Any], must_read: list[str]) -> str:
    role_name = binding.get("role", card["owner"] or card["role"])
    helper = binding.get("helper", "")
    docs = ", ".join(must_read)
    gates = ", ".join(card.get("gate_ids", [])) or "no gate_ids"
    reports = ", ".join(card.get("required_reports", [])) or "no required_reports"
    return (
        f"Ты {role_name} AI Build Team ProSmet. "
        f"Возьми {card['id']} ({card['title']}). "
        f"Slice: {card.get('slice')}; work package: {card.get('work_package')}. "
        f"Сначала прочитай полный must_read список: {docs}. "
        f"Task card: {card['path']}. "
        f"Запусти helper `{helper}` для контекста роли. "
        f"Gate ids: {gates}. Required reports: {reports}. "
        "Работай строго в Scope, не читай .env/credentials, не ослабляй tenant/AI-money/publication gates. "
        "В конце дай handoff и machine-readable evidence report with changed files, checks, gate results, blockers and next executor."
    )


def dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def dependency_report(cards: dict[str, dict[str, Any]], completed_override: set[str]) -> dict[str, Any]:
    completed = {
        task_id
        for task_id, card in cards.items()
        if card["status"] in COMPLETED_STATUSES
    } | completed_override

    missing_dependencies: dict[str, list[str]] = {}
    available_now: list[str] = []
    blocked_by_dependencies: dict[str, list[str]] = {}
    blocked_by_status: dict[str, str] = {}
    terminal: list[str] = []
    work_packages: list[str] = []

    for task_id, card in cards.items():
        if task_id in completed:
            terminal.append(task_id)
            continue
        if card["status"] in EPIC_STATUSES:
            work_packages.append(task_id)
            continue
        deps = card["dependencies"]
        missing = [dep for dep in deps if dep not in cards]
        if missing:
            missing_dependencies[task_id] = missing
            continue
        unresolved = [dep for dep in deps if dep not in completed]
        if unresolved:
            blocked_by_dependencies[task_id] = unresolved
        elif card["status"] in WORKABLE_STATUSES:
            available_now.append(task_id)
        else:
            blocked_by_status[task_id] = card["status"]

    return {
        "completed": sorted(completed),
        "available_now": sorted(available_now),
        "blocked_by_dependencies": blocked_by_dependencies,
        "blocked_by_status": blocked_by_status,
        "missing_dependencies": missing_dependencies,
        "terminal": sorted(terminal),
        "work_packages": sorted(work_packages),
    }


def execution_waves(cards: dict[str, dict[str, Any]], completed_override: set[str]) -> tuple[list[list[str]], list[str]]:
    completed = {
        task_id
        for task_id, card in cards.items()
        if card["status"] in COMPLETED_STATUSES
    } | completed_override
    candidates = {
        task_id
        for task_id, card in cards.items()
        if card["status"] not in COMPLETED_STATUSES
        and card["status"] in WORKABLE_STATUSES
        and task_id not in completed_override
    }

    active = {
        task_id
        for task_id in candidates
        if all(dep in completed or dep in candidates for dep in cards[task_id]["dependencies"])
    }
    indegree = {task_id: 0 for task_id in active}
    outgoing: dict[str, list[str]] = defaultdict(list)

    for task_id in active:
        for dep in cards[task_id]["dependencies"]:
            if dep in active:
                indegree[task_id] += 1
                outgoing[dep].append(task_id)

    queue = deque(sorted(task_id for task_id, degree in indegree.items() if degree == 0))
    waves: list[list[str]] = []
    processed: list[str] = []

    while queue:
        wave = list(queue)
        queue.clear()
        waves.append(wave)
        for task_id in wave:
            processed.append(task_id)
            for child in sorted(outgoing.get(task_id, [])):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

    cycle_or_blocked = sorted(candidates - set(processed))
    return waves, cycle_or_blocked


def wave_objects(waves: list[list[str]], enriched: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    completed_so_far: set[str] = set()
    for index, wave in enumerate(waves, start=1):
        unlocks: dict[str, list[str]] = {}
        current = set(wave)
        after_wave = completed_so_far | current
        for candidate_id, task in enriched.items():
            if candidate_id in after_wave:
                continue
            deps = set(task["dependencies"])
            if deps and deps <= after_wave and deps & current and task["status"] in WORKABLE_STATUSES:
                unlocks[candidate_id] = sorted(deps & current)
        if index == 1:
            reason = "Tasks with no unresolved dependencies and workable status."
        else:
            reason = "Previous waves satisfy dependencies for this wave."
        result.append(
            {
                "wave": index,
                "wave_reason": reason,
                "tasks": [enriched[task_id] for task_id in wave],
                "unlocks": unlocks,
            }
        )
        completed_so_far = after_wave
    return result


def assignments_by_role(cards: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for task_id, card in cards.items():
        result[card["owner"] or card["role"]].append(task_id)
    return {role: sorted(tasks) for role, tasks in sorted(result.items())}


def build_plan(completed_override: set[str]) -> dict[str, Any]:
    cards = task_cards()
    dep_report = dependency_report(cards, completed_override)
    waves, cycle_or_blocked = execution_waves(cards, completed_override)
    enriched = {task_id: task_with_binding(card) for task_id, card in cards.items()}

    plan = {
        "status": "ready" if not dep_report["missing_dependencies"] and not cycle_or_blocked else "needs_attention",
        "canonical_flow": CANONICAL_FLOW,
        "generated_by": "harness/scripts/agents/dispatch_tasks.py",
        "tasks_total": len(cards),
        "roles_total": len(ROLE_PROFILES),
        "available_now": [enriched[task_id] for task_id in dep_report["available_now"]],
        "execution_waves": wave_objects(waves, enriched),
        "blocked_by_dependencies": dep_report["blocked_by_dependencies"],
        "blocked_by_status": dep_report["blocked_by_status"],
        "missing_dependencies": dep_report["missing_dependencies"],
        "work_packages": dep_report["work_packages"],
        "cycle_or_blocked": cycle_or_blocked,
        "assignments_by_role": assignments_by_role(cards),
        "tasks": enriched,
        "safety": {
            "dry_run_only": True,
            "does_not_spawn_agents": True,
            "does_not_read_env_or_credentials": True,
            "does_not_call_network": True,
            "does_not_mutate_task_cards": True,
        },
    }
    return plan


def print_summary(plan: dict[str, Any]) -> None:
    print(f"Agent dispatch plan: {plan['status']}")
    print(f"Tasks: {plan['tasks_total']}")
    print(f"Roles: {plan['roles_total']}")
    print(f"Work packages: {len(plan.get('work_packages', []))}")
    print(f"Available now: {len(plan['available_now'])}")
    for task in plan["available_now"]:
        employee = task["employee"]
        print(
            f"- {task['id']} {task['title']} -> {employee.get('role')} "
            f"({employee.get('claude_profile')}, {employee.get('codex_profile')})"
        )
    print(f"Execution waves: {len(plan['execution_waves'])}")
    for wave in plan["execution_waves"]:
        items = ", ".join(f"{task['id']}:{task['owner']}" for task in wave["tasks"])
        print(f"- wave {wave['wave']}: {items} ({wave['wave_reason']})")
    if plan["missing_dependencies"]:
        print("Missing dependencies:")
        for task_id, deps in plan["missing_dependencies"].items():
            print(f"- {task_id}: {', '.join(deps)}")
    if plan["cycle_or_blocked"]:
        print(f"Cycle/blocked tasks: {', '.join(plan['cycle_or_blocked'])}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an AI employee dispatch plan from ProSmet task cards.")
    parser.add_argument("--json", action="store_true", help="Print the full plan JSON to stdout")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Report path")
    parser.add_argument(
        "--completed",
        action="append",
        default=[],
        metavar="TASK-ID",
        help="Treat a task as completed for planning simulation. Can be repeated.",
    )
    args = parser.parse_args()

    completed_override = set(args.completed)
    plan = build_plan(completed_override)

    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = ROOT / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print_summary(plan)
        print(f"Report: {report_path.relative_to(ROOT)}")

    return 0 if plan["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
