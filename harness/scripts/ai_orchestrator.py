#!/usr/bin/env python3
"""Development-time AI orchestrator for ProSmet.

The orchestrator is a deterministic local control plane. It proposes the next
AI employee cycle, waits for explicit architect approval, and only then emits
command packets for the selected AI employees. It does not spawn agents, read
.env files, call the network, or mutate task cards.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
AGENT_SCRIPT_DIR = ROOT / "harness/scripts/agents"
if str(AGENT_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_SCRIPT_DIR))

from _agent_common import CANONICAL_FLOW, ROLE_PROFILES  # noqa: E402
from dispatch_tasks import build_plan  # noqa: E402


REPORT_DIR = ROOT / "reports/orchestrator"
WORKSPACE_DIR = ROOT / "workspace/orchestrator"
OUTBOX_DIR = WORKSPACE_DIR / "outbox"
APPROVAL_DIR = WORKSPACE_DIR / "approvals"
LATEST_CYCLE = REPORT_DIR / "latest-cycle.json"
LATEST_APPROVED = REPORT_DIR / "latest-approved-dispatch.json"
DISPATCH_REPORT = ROOT / "reports/agent-dispatch-plan.json"

CONTEXT_DOCS = [
    "AGENTS.md",
    "EntryPointForTask.md",
    "Focus.md",
    "Team.yml",
    "Scope.md",
    "docs/dev/ImplementationPlan.md",
    "docs/dev/PredictableAIWork.md",
    "docs/contracts/AIOrchestrator.md",
    "docs/Evals/gates.json",
    "docs/contracts/ContractManifest.json",
]

ORCHESTRATOR_PREFERENCES = [
    "Сначала закрывать contract/evidence gates, потом расширять функциональность.",
    "До приемки architecture prep держать параллелизм низким: один главный task за цикл.",
    "После baseline scaffold и QA harness параллелить только независимые роли и write scopes.",
    "Каждый dispatch packet должен требовать конкретный evidence report.",
    "Любой real price, real PII, deploy, Scope или legal blocker превращать в inbox request, а не в устную договоренность.",
    "План менять маленькими корректировками, чтобы dependency graph оставался машинно проверяемым.",
]

SAFETY = {
    "development_time_only": True,
    "no_runtime_product_agent": True,
    "does_not_read_env_or_credentials": True,
    "does_not_call_network": True,
    "does_not_mutate_task_cards": True,
    "does_not_spawn_agents": True,
    "requires_architect_approval_before_command_packets": True,
    "does_not_calculate_prices": True,
    "does_not_handle_real_pii_or_real_price": True,
}

COMPLETED_STATUSES = {"done", "complete", "completed", "accepted", "closed"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def cycle_id() -> str:
    return "ORCH-CYCLE-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def ensure_dirs() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned or "item"


def safe_env() -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    pythonpath = os.environ.get("PYTHONPATH")
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    return env


def run_local_check(command: list[str], timeout: int = 30) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
        env=safe_env(),
    )
    output = result.stdout.strip()
    lines = output.splitlines()
    return {
        "command": " ".join(command),
        "status": "passed" if result.returncode == 0 else "failed",
        "exitCode": result.returncode,
        "outputSummary": lines[-12:],
    }


def context_doc_status() -> list[dict[str, Any]]:
    result = []
    for item in CONTEXT_DOCS:
        path = ROOT / item
        result.append({"path": item, "exists": path.exists()})
    return result


def load_inbox() -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "harness/scripts/architect_inbox.py", "--json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
        check=False,
        env=safe_env(),
    )
    output = result.stdout.strip()
    check = {
        "command": "python3 harness/scripts/architect_inbox.py --json",
        "status": "passed" if result.returncode == 0 else "failed",
        "exitCode": result.returncode,
        "outputSummary": output.splitlines()[-12:],
    }
    if result.returncode != 0:
        return {
            "status": "needs_attention",
            "requests": [],
            "issues": ["architect_inbox.py failed"],
            "check": check,
        }
    try:
        payload = json.loads(output or "{}")
    except json.JSONDecodeError as exc:
        return {
            "status": "needs_attention",
            "requests": [],
            "issues": [f"Cannot parse architect inbox JSON: {exc}"],
            "check": check,
        }
    payload["check"] = check
    return payload


def blocking_inbox_requests(inbox: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in inbox.get("requests", []):
        if item.get("kind") == "price" and not item.get("canContinueWithoutAnswer", False):
            result.append(item)
            continue
        if item.get("priority") == "blocking":
            result.append(item)
            continue
        if item.get("canContinueWithoutAnswer") is False:
            result.append(item)
    return result


def write_dispatch_report(plan: dict[str, Any]) -> None:
    write_json(DISPATCH_REPORT, plan)


def evidence_path(task: dict[str, Any]) -> str:
    expected = [
        item
        for item in task.get("required_reports", [])
        if item.startswith("reports/task-evidence/")
    ]
    return expected[0] if expected else f"reports/task-evidence/{task['id']}.json"


def evidence_exists(task: dict[str, Any]) -> bool:
    return (ROOT / evidence_path(task)).exists()


def select_tasks(plan: dict[str, Any], max_tasks: int, wave: int | None) -> tuple[list[dict[str, Any]], str]:
    if wave is not None:
        for item in plan.get("execution_waves", []):
            if item.get("wave") == wave:
                return item.get("tasks", [])[:max_tasks], f"Selected from execution wave {wave}."
        return [], f"Execution wave {wave} is not available."

    available = plan.get("available_now", [])
    prep = [task for task in available if task.get("slice") == "architecture_prep"]
    if prep:
        return prep[:1], "Architecture prep is still available; keep the cycle focused on prep acceptance."

    first_wave = plan.get("execution_waves", [{}])[0].get("tasks", [])
    return first_wave[:max_tasks], "Selected from the first executable wave."


def task_summary(task: dict[str, Any], reason: str) -> dict[str, Any]:
    employee = task.get("employee", {})
    expected_report = evidence_path(task)
    return {
        "taskId": task["id"],
        "title": task.get("title", ""),
        "owner": task.get("owner") or task.get("role"),
        "role": task.get("role", ""),
        "slice": task.get("slice", ""),
        "workPackage": task.get("work_package", ""),
        "taskPath": task.get("path", ""),
        "selectionReason": reason,
        "helper": employee.get("helper", ""),
        "claudeProfile": employee.get("claude_profile", ""),
        "codexProfile": employee.get("codex_profile", ""),
        "gateIds": task.get("gate_ids", []),
        "mustRead": task.get("must_read", []),
        "dispatchPrompt": task.get("dispatch_prompt", ""),
        "expectedEvidenceReports": [expected_report],
        "evidenceAlreadyExists": (ROOT / expected_report).exists(),
        "handoffTo": task.get("handoff_to", []),
    }


def summarize_plan(plan: dict[str, Any]) -> dict[str, Any]:
    completed = [
        task_id
        for task_id, task in plan.get("tasks", {}).items()
        if task.get("status") in COMPLETED_STATUSES
    ]
    evidence_files = sorted((ROOT / "reports/task-evidence").glob("TASK-*.json"))
    return {
        "dispatchStatus": plan.get("status", "unknown"),
        "tasksTotal": plan.get("tasks_total", 0),
        "rolesTotal": plan.get("roles_total", len(ROLE_PROFILES)),
        "availableNow": [task.get("id") for task in plan.get("available_now", [])],
        "executionWaveCount": len(plan.get("execution_waves", [])),
        "completedTasks": sorted(completed),
        "evidenceReportCount": len(evidence_files),
        "blockedByDependencies": plan.get("blocked_by_dependencies", {}),
        "blockedByStatus": plan.get("blocked_by_status", {}),
        "missingDependencies": plan.get("missing_dependencies", {}),
    }


def recommendations(
    plan: dict[str, Any],
    selected: list[dict[str, Any]],
    inbox: dict[str, Any],
    validations: list[dict[str, Any]],
) -> tuple[list[str], list[str], list[str]]:
    good: list[str] = []
    attention: list[str] = []
    corrections: list[str] = []

    if plan.get("status") == "ready":
        good.append("Dependency graph готов к управляемому запуску следующего цикла.")
    else:
        attention.append("Dispatch plan требует внимания перед выдачей команд.")

    if selected:
        task_ids = ", ".join(task["taskId"] for task in selected)
        good.append(f"Следующий управляемый запуск можно ограничить задачами: {task_ids}.")
    else:
        attention.append("Нет выбранных задач для выдачи команд.")

    open_requests = inbox.get("requests", [])
    if open_requests:
        attention.append(f"В inbox есть открытые запросы архитектора: {len(open_requests)}.")

    failed = [item for item in validations if item.get("status") == "failed"]
    if failed:
        corrections.append("Сначала исправить failed local checks, потом утверждать dispatch.")

    if "TASK-001" not in summarize_plan(plan)["completedTasks"]:
        corrections.append("Не начинать MVP-0 код широкой волной до acceptance по TASK-001 или explicit override.")

    if any(not task["evidenceAlreadyExists"] for task in selected):
        attention.append("Команды должны завершиться evidence report; без него задача не считается done.")

    if not corrections:
        corrections.append("План корректировать не нужно: достаточно выполнить выбранный цикл и сверить evidence.")

    return good, attention, corrections


def build_cycle(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    run_id = cycle_id()
    completed = set(args.completed or [])
    plan = build_plan(completed)
    write_dispatch_report(plan)

    validations: list[dict[str, Any]] = []
    if not args.no_checks:
        validations.append(run_local_check([sys.executable, "harness/scripts/validate_predictability.py"]))
        validations.append(run_local_check([sys.executable, "harness/scripts/architect_inbox.py"]))

    inbox = load_inbox()
    selected_raw, reason = select_tasks(plan, max_tasks=args.max_tasks, wave=args.wave)
    selected = [task_summary(task, reason) for task in selected_raw]

    validation_failed = any(item.get("status") == "failed" for item in validations)
    blocking_requests = blocking_inbox_requests(inbox)

    if validation_failed:
        status = "blocked_by_validation"
    elif blocking_requests:
        status = "blocked_by_inbox"
    elif plan.get("status") != "ready":
        status = "needs_attention"
    elif not selected:
        status = "no_work_available"
    else:
        status = "ready_for_architect_approval"

    good, attention, corrections = recommendations(plan, selected, inbox, validations)
    report_path = REPORT_DIR / f"{run_id}.json"
    payload = {
        "$schema": "../../docs/contracts/schemas/ai-orchestrator-cycle-v1.schema.json",
        "contractVersion": "ai-orchestrator-cycle.v1",
        "cycleId": run_id,
        "generatedAt": utc_now(),
        "mode": "proposed",
        "status": status,
        "dryRun": True,
        "canonicalFlow": CANONICAL_FLOW,
        "safety": SAFETY,
        "consent": {
            "state": "pending" if status == "ready_for_architect_approval" else "not_requested",
            "requiredBeforeCommandPackets": True,
            "approvedBy": "",
            "decisionNote": "",
        },
        "sourceReports": {
            "dispatchPlan": rel(DISPATCH_REPORT),
            "predictabilityReport": "reports/predictability-validation.json",
            "architectInbox": "workspace/architect-inbox/requests/",
        },
        "contextDocs": context_doc_status(),
        "developmentState": summarize_plan(plan),
        "validations": validations,
        "architectInbox": {
            "status": inbox.get("status", "unknown"),
            "requestCount": inbox.get("requestCount", len(inbox.get("requests", []))),
            "requests": inbox.get("requests", []),
            "issues": inbox.get("issues", []),
        },
        "selectedTasks": selected,
        "orchestratorPreferences": ORCHESTRATOR_PREFERENCES,
        "feedback": {
            "whatIsGoingWell": good,
            "watchPoints": attention,
            "planCorrections": corrections,
        },
        "nextActionForArchitect": next_action(status, report_path),
    }
    write_json(report_path, payload)
    write_json(LATEST_CYCLE, payload)
    return payload


def next_action(status: str, report_path: Path) -> str:
    report = rel(report_path)
    if status == "ready_for_architect_approval":
        return (
            "Проверь cycle report и утверди командные пакеты: "
            f"python3 harness/scripts/ai_orchestrator.py approve --cycle {report} "
            '--approved-by Architect --decision-note "approved next AI employee cycle"'
        )
    if status == "blocked_by_validation":
        return "Исправить failed validations, затем заново выполнить propose."
    if status == "blocked_by_inbox":
        return "Ответить на blocking Architect Inbox / PriceInputRequest, затем заново выполнить propose."
    if status == "no_work_available":
        return "Обновить task statuses/evidence или попросить PPM подготовить следующую micro-task."
    return "Проверить feedback.planCorrections и dispatch plan перед approval."


def command_packet(task: dict[str, Any], cycle: dict[str, Any], approved_by: str) -> dict[str, Any]:
    return {
        "contractVersion": "ai-orchestrator-command-packet.v1",
        "cycleId": cycle["cycleId"],
        "approvedBy": approved_by,
        "createdAt": utc_now(),
        "taskId": task["taskId"],
        "title": task["title"],
        "owner": task["owner"],
        "role": task["role"],
        "taskPath": task["taskPath"],
        "helper": task["helper"],
        "claudeProfile": task["claudeProfile"],
        "codexProfile": task["codexProfile"],
        "gateIds": task["gateIds"],
        "mustRead": task["mustRead"],
        "expectedEvidenceReports": task["expectedEvidenceReports"],
        "dispatchPrompt": task["dispatchPrompt"],
        "architectInterventionProtocol": {
            "inboxCommand": "python3 harness/scripts/architect_inbox.py",
            "architectRequestContract": "docs/contracts/ArchitectInterventionRequest.md",
            "architectRequestPathPattern": "workspace/architect-inbox/requests/ARCH-REQUEST-YYYYMMDD-TASK-ID-short-slug.json",
            "priceInputContract": "docs/contracts/PriceInputRequest.md",
            "priceRequestPathPattern": "reports/price-requests/PRICE-REQUEST-YYYYMMDD-TASK-ID.json",
            "requiredFinalNotice": [
                "Нужен ввод архитектора: architect intervention request создан",
                "Нужен ввод архитектора: real price input request создан"
            ],
        },
        "stopRules": [
            "Если нужен Ask First decision, создай ArchitectInterventionRequest и останови зависимую часть.",
            "Если нужен реальный прайс, создай PriceInputRequest и не придумывай значения.",
            "Не продолжай price-dependent, PII, deploy, Scope, legal или external-service работу без явного ответа архитектора.",
        ],
        "safety": SAFETY,
        "handoffRequired": True,
    }


def packet_markdown(packet: dict[str, Any]) -> str:
    must_read = "\n".join(f"- `{item}`" for item in packet.get("mustRead", []))
    gates = ", ".join(packet.get("gateIds", []))
    evidence = ", ".join(packet.get("expectedEvidenceReports", []))
    return f"""# AI Employee Command Packet

Cycle: `{packet["cycleId"]}`  
Task: `{packet["taskId"]}` · {packet["title"]}  
Owner: `{packet["owner"]}`  
Approved by: `{packet["approvedBy"]}`

## Must Read

{must_read}

## Gate IDs

{gates}

## Expected Evidence

{evidence}

## Architect Inbox Protocol

- If an Ask First blocker appears, create `workspace/architect-inbox/requests/ARCH-REQUEST-*.json`.
- If real price is needed, create `reports/price-requests/PRICE-REQUEST-*.json`.
- Mention the created request path in handoff/final.

## Dispatch Prompt

```text
{packet["dispatchPrompt"]}
```
"""


def approve_cycle(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    cycle_path = ROOT / args.cycle if not Path(args.cycle).is_absolute() else Path(args.cycle)
    cycle = read_json(cycle_path)
    if cycle.get("contractVersion") != "ai-orchestrator-cycle.v1":
        raise SystemExit("Cycle report has wrong contractVersion.")
    if cycle.get("status") != "ready_for_architect_approval" and not args.force:
        raise SystemExit(
            "Cycle is not ready_for_architect_approval. Use --force only after explicit architect decision."
        )
    if not cycle.get("selectedTasks"):
        raise SystemExit("Cycle has no selectedTasks to approve.")

    inbox = load_inbox()
    blocking_requests = blocking_inbox_requests(inbox)
    if (inbox.get("issues") or blocking_requests) and not args.force:
        request_ids = ", ".join(item.get("requestId", item.get("path", "")) for item in blocking_requests)
        raise SystemExit(
            "Approval blocked by Architect Inbox. "
            f"Resolve blocking requests first: {request_ids or 'inbox issues'} "
            "or use --force after explicit architect decision."
        )

    command_paths: list[dict[str, str]] = []
    for task in cycle["selectedTasks"]:
        base = OUTBOX_DIR / f"{cycle['cycleId']}-{task['taskId']}-{slug(task['owner'])}"
        packet = command_packet(task, cycle, args.approved_by)
        json_path = base.with_suffix(".json")
        md_path = base.with_suffix(".md")
        write_json(json_path, packet)
        md_path.write_text(packet_markdown(packet), encoding="utf-8")
        command_paths.append(
            {
                "taskId": task["taskId"],
                "json": rel(json_path),
                "markdown": rel(md_path),
            }
        )
        task["commandPacketPaths"] = command_paths[-1]

    approved = {
        **cycle,
        "mode": "approved",
        "status": "approved_dispatch_ready",
        "dryRun": False,
        "approvedAt": utc_now(),
        "consent": {
            "state": "approved",
            "requiredBeforeCommandPackets": True,
            "approvedBy": args.approved_by,
            "decisionNote": args.decision_note,
        },
        "commandPackets": command_paths,
        "approvalInboxCheck": {
            "status": inbox.get("status", "unknown"),
            "requestCount": inbox.get("requestCount", len(inbox.get("requests", []))),
            "blockingRequestCount": len(blocking_requests),
            "issues": inbox.get("issues", []),
            "forced": args.force,
        },
        "nextActionForArchitect": (
            "Передай command packets соответствующим AI-сотрудникам. "
            "После выполнения проверь reports/task-evidence/TASK-ID.json и заново запусти propose."
        ),
    }
    approved_path = REPORT_DIR / f"{cycle['cycleId']}-approved.json"
    write_json(approved_path, approved)
    write_json(LATEST_APPROVED, approved)

    approval_record = {
        "cycleId": cycle["cycleId"],
        "status": "approved",
        "approvedAt": approved["approvedAt"],
        "approvedBy": args.approved_by,
        "decisionNote": args.decision_note,
        "approvedReport": rel(approved_path),
        "commandPackets": command_paths,
        "approvalInboxCheck": approved["approvalInboxCheck"],
    }
    write_json(APPROVAL_DIR / f"{cycle['cycleId']}-approval.json", approval_record)
    return approved


def reject_cycle(args: argparse.Namespace) -> dict[str, Any]:
    ensure_dirs()
    cycle_path = ROOT / args.cycle if not Path(args.cycle).is_absolute() else Path(args.cycle)
    cycle = read_json(cycle_path)
    rejected = {
        **cycle,
        "mode": "rejected",
        "status": "rejected_by_architect",
        "rejectedAt": utc_now(),
        "consent": {
            "state": "rejected",
            "requiredBeforeCommandPackets": True,
            "approvedBy": args.rejected_by,
            "decisionNote": args.decision_note,
        },
        "selectedTasks": [],
        "nextActionForArchitect": "Скорректировать task statuses/plan или rerun propose with different options.",
    }
    rejected_path = REPORT_DIR / f"{cycle['cycleId']}-rejected.json"
    write_json(rejected_path, rejected)
    write_json(
        APPROVAL_DIR / f"{cycle['cycleId']}-rejection.json",
        {
            "cycleId": cycle["cycleId"],
            "status": "rejected",
            "rejectedAt": rejected["rejectedAt"],
            "rejectedBy": args.rejected_by,
            "decisionNote": args.decision_note,
            "rejectedReport": rel(rejected_path),
        },
    )
    return rejected


def status_payload() -> dict[str, Any]:
    plan = build_plan(set())
    inbox = load_inbox()
    latest_cycle = read_json(LATEST_CYCLE) if LATEST_CYCLE.exists() else {}
    latest_approved = read_json(LATEST_APPROVED) if LATEST_APPROVED.exists() else {}
    return {
        "contractVersion": "ai-orchestrator-status.v1",
        "generatedAt": utc_now(),
        "safety": SAFETY,
        "developmentState": summarize_plan(plan),
        "architectInbox": {
            "status": inbox.get("status", "unknown"),
            "requestCount": inbox.get("requestCount", len(inbox.get("requests", []))),
            "requests": inbox.get("requests", []),
            "issues": inbox.get("issues", []),
        },
        "latestCycle": {
            "cycleId": latest_cycle.get("cycleId", ""),
            "status": latest_cycle.get("status", "missing"),
            "path": rel(LATEST_CYCLE) if LATEST_CYCLE.exists() else "",
            "selectedTasks": [task.get("taskId") for task in latest_cycle.get("selectedTasks", [])],
        },
        "latestApprovedDispatch": {
            "cycleId": latest_approved.get("cycleId", ""),
            "status": latest_approved.get("status", "missing"),
            "path": rel(LATEST_APPROVED) if LATEST_APPROVED.exists() else "",
            "commandPackets": latest_approved.get("commandPackets", []),
        },
    }


def print_cycle(payload: dict[str, Any]) -> None:
    print(f"AI orchestrator cycle: {payload['status']}")
    print(f"Cycle: {payload['cycleId']}")
    print(f"Report: {rel(LATEST_CYCLE)}")
    selected = payload.get("selectedTasks", [])
    print(f"Selected tasks: {len(selected)}")
    for task in selected:
        print(f"- {task['taskId']} {task['title']} -> {task['owner']}")
        print(f"  evidence: {', '.join(task['expectedEvidenceReports'])}")
    print("Watch points:")
    for item in payload.get("feedback", {}).get("watchPoints", []):
        print(f"- {item}")
    print("Plan corrections:")
    for item in payload.get("feedback", {}).get("planCorrections", []):
        print(f"- {item}")
    print(f"Next: {payload['nextActionForArchitect']}")


def print_approved(payload: dict[str, Any]) -> None:
    print("AI orchestrator approval: approved_dispatch_ready")
    print(f"Cycle: {payload['cycleId']}")
    for packet in payload.get("commandPackets", []):
        print(f"- {packet['taskId']}: {packet['markdown']} / {packet['json']}")
    print(f"Report: {rel(LATEST_APPROVED)}")


def print_status(payload: dict[str, Any]) -> None:
    state = payload["developmentState"]
    print("AI orchestrator status")
    print(f"- dispatch: {state['dispatchStatus']}")
    print(f"- available: {', '.join(state['availableNow']) or 'none'}")
    print(f"- evidence reports: {state['evidenceReportCount']}")
    print(f"- inbox requests: {payload['architectInbox']['requestCount']}")
    print(f"- latest cycle: {payload['latestCycle']['status']} {payload['latestCycle']['cycleId']}")
    print(
        f"- latest approved: {payload['latestApprovedDispatch']['status']} "
        f"{payload['latestApprovedDispatch']['cycleId']}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ProSmet development-time AI orchestrator.")
    sub = parser.add_subparsers(dest="command")

    propose = sub.add_parser("propose", help="Build the next cycle proposal for architect approval.")
    propose.add_argument("--report", default=str(LATEST_CYCLE), help="Compatibility option; latest-cycle is always written.")
    propose.add_argument("--completed", action="append", default=[], help="Treat TASK-ID as completed for simulation.")
    propose.add_argument("--max-tasks", type=int, default=1, help="Maximum tasks to select from the executable wave.")
    propose.add_argument("--wave", type=int, help="Select a specific execution wave.")
    propose.add_argument("--no-checks", action="store_true", help="Skip local validation commands.")
    propose.add_argument("--json", action="store_true", help="Print JSON instead of text summary.")

    approve = sub.add_parser("approve", help="Approve a proposed cycle and emit command packets.")
    approve.add_argument("--cycle", default=str(LATEST_CYCLE), help="Cycle report to approve.")
    approve.add_argument("--approved-by", required=True, help="Human architect approving the cycle.")
    approve.add_argument("--decision-note", default="", help="Short human decision note.")
    approve.add_argument("--force", action="store_true", help="Allow approval despite non-ready status after explicit decision.")
    approve.add_argument("--json", action="store_true", help="Print JSON instead of text summary.")

    reject = sub.add_parser("reject", help="Reject a proposed cycle without emitting command packets.")
    reject.add_argument("--cycle", default=str(LATEST_CYCLE), help="Cycle report to reject.")
    reject.add_argument("--rejected-by", required=True, help="Human architect rejecting the cycle.")
    reject.add_argument("--decision-note", required=True, help="Why the cycle was rejected.")
    reject.add_argument("--json", action="store_true", help="Print JSON instead of text summary.")

    status = sub.add_parser("status", help="Show current orchestration status.")
    status.add_argument("--json", action="store_true", help="Print JSON instead of text summary.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command is None:
        args = parser.parse_args(["propose"])
    command = args.command

    if command == "propose":
        payload = build_cycle(args)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print_cycle(payload)
        return 0 if payload["status"] == "ready_for_architect_approval" else 1

    if command == "approve":
        payload = approve_cycle(args)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print_approved(payload)
        return 0

    if command == "reject":
        payload = reject_cycle(args)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"AI orchestrator cycle rejected: {payload['cycleId']}")
        return 0

    if command == "status":
        payload = status_payload()
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print_status(payload)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
