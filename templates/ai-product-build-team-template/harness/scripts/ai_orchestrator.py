#!/usr/bin/env python3
"""Portable development-time AI orchestrator.

It proposes the next tasks and emits command packets only after approval.
It does not spawn agents, read secrets, call network or deploy.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports/orchestrator"
LATEST_CYCLE = REPORT_DIR / "latest-cycle.json"
LATEST_APPROVED = REPORT_DIR / "latest-approved-dispatch.json"
OUTBOX = ROOT / "workspace/orchestrator/outbox"
APPROVALS = ROOT / "workspace/orchestrator/approvals"

sys.path.insert(0, str(ROOT / "harness/scripts/agents"))
from dispatch_tasks import build_plan  # noqa: E402


def now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_check(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    lines = (result.stdout + result.stderr).strip().splitlines()
    return {
        "command": " ".join(command),
        "status": "passed" if result.returncode == 0 else "failed",
        "exitCode": result.returncode,
        "outputSummary": lines[:12],
    }


def propose(args: argparse.Namespace) -> dict[str, Any]:
    plan = build_plan()
    validations = [] if args.no_checks else [
        run_check([sys.executable, "harness/scripts/agents/validate_agent_profiles.py"]),
        run_check([sys.executable, "harness/scripts/architect_inbox.py"]),
    ]
    selected = plan["available_now"][: args.limit]
    cycle_id = f"ORCH-CYCLE-{now_id()}"
    status = "ready_for_architect_approval" if selected and all(v["status"] == "passed" for v in validations) else "blocked"
    payload = {
        "contractVersion": "ai-orchestrator-cycle.v1",
        "cycleId": cycle_id,
        "generatedAt": utc_now(),
        "mode": "proposed",
        "status": status,
        "dryRun": True,
        "selectedTasks": selected,
        "validations": validations,
        "feedback": {
            "watchPoints": ["Each selected task must finish with reports/task-evidence/TASK-ID.json."],
            "planCorrections": [] if status == "ready_for_architect_approval" else ["Resolve blockers before approval."],
        },
        "nextActionForArchitect": f"Approve with: python3 harness/scripts/ai_orchestrator.py approve --cycle reports/orchestrator/{cycle_id}.json --approved-by Architect",
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / f"{cycle_id}.json", payload)
    write_json(LATEST_CYCLE, payload)
    return payload


def approve(args: argparse.Namespace) -> dict[str, Any]:
    cycle_path = ROOT / args.cycle
    cycle = json.loads(cycle_path.read_text(encoding="utf-8"))
    if cycle.get("status") != "ready_for_architect_approval" and not args.force:
        raise SystemExit("Cycle is not ready. Use --force only after explicit human decision.")

    OUTBOX.mkdir(parents=True, exist_ok=True)
    APPROVALS.mkdir(parents=True, exist_ok=True)
    packets = []
    for task in cycle.get("selectedTasks", []):
        packet = {
            "contractVersion": "ai-orchestrator-command-packet.v1",
            "cycleId": cycle["cycleId"],
            "approvedBy": args.approved_by,
            "createdAt": utc_now(),
            "taskId": task["id"],
            "title": task["title"],
            "owner": task["owner"],
            "taskPath": task["path"],
            "helper": task.get("helper", ""),
            "dispatchPrompt": task.get("dispatch_prompt", ""),
            "expectedEvidenceReports": task.get("required_reports", []),
        }
        base = OUTBOX / f"{cycle['cycleId']}-{task['id']}-{task['owner']}"
        json_path = base.with_suffix(".json")
        md_path = base.with_suffix(".md")
        write_json(json_path, packet)
        md_path.write_text(
            f"# AI Employee Command Packet\n\nTask: `{task['id']}` · {task['title']}\n\n"
            f"Owner: `{task['owner']}`\n\n"
            f"Expected evidence: `{', '.join(task.get('required_reports', []))}`\n\n"
            f"```text\n{task.get('dispatch_prompt', '')}\n```\n",
            encoding="utf-8",
        )
        packets.append({"taskId": task["id"], "json": rel(json_path), "markdown": rel(md_path)})

    approved = {
        **cycle,
        "mode": "approved",
        "status": "approved_dispatch_ready",
        "approvedAt": utc_now(),
        "approvedBy": args.approved_by,
        "decisionNote": args.decision_note,
        "commandPackets": packets,
    }
    write_json(REPORT_DIR / f"{cycle['cycleId']}-approved.json", approved)
    write_json(APPROVALS / f"{cycle['cycleId']}-approval.json", {
        "cycleId": cycle["cycleId"],
        "approvedBy": args.approved_by,
        "decisionNote": args.decision_note,
        "approvedAt": approved["approvedAt"],
    })
    write_json(LATEST_APPROVED, approved)
    return approved


def status() -> dict[str, Any]:
    latest = json.loads(LATEST_CYCLE.read_text(encoding="utf-8")) if LATEST_CYCLE.exists() else {}
    approved = json.loads(LATEST_APPROVED.read_text(encoding="utf-8")) if LATEST_APPROVED.exists() else {}
    return {
        "latestCycle": latest.get("cycleId", ""),
        "latestCycleStatus": latest.get("status", "missing"),
        "latestApproved": approved.get("cycleId", ""),
        "latestApprovedStatus": approved.get("status", "missing"),
        "commandPackets": approved.get("commandPackets", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Portable AI team orchestrator.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("propose")
    p.add_argument("--limit", type=int, default=2)
    p.add_argument("--no-checks", action="store_true")
    a = sub.add_parser("approve")
    a.add_argument("--cycle", default=rel(LATEST_CYCLE))
    a.add_argument("--approved-by", required=True)
    a.add_argument("--decision-note", default="")
    a.add_argument("--force", action="store_true")
    sub.add_parser("status")
    args = parser.parse_args()

    if args.command == "propose":
        payload = propose(args)
        print(f"AI orchestrator cycle: {payload['status']}")
        print(f"Cycle: {payload['cycleId']}")
        for task in payload["selectedTasks"]:
            print(f"- {task['id']} {task['title']} -> {task['owner']}")
        print(f"Report: {rel(LATEST_CYCLE)}")
    elif args.command == "approve":
        payload = approve(args)
        print("AI orchestrator approval: approved_dispatch_ready")
        for packet in payload["commandPackets"]:
            print(f"- {packet['taskId']}: {packet['markdown']} / {packet['json']}")
    elif args.command == "status":
        payload = status()
        print("AI orchestrator status")
        print(f"- latest cycle: {payload['latestCycleStatus']} {payload['latestCycle']}")
        print(f"- latest approved: {payload['latestApprovedStatus']} {payload['latestApproved']}")


if __name__ == "__main__":
    main()

