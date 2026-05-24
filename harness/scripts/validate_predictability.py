#!/usr/bin/env python3
"""Validate predictable AI-work contracts, gates, tasks and fixtures.

The script is intentionally local and dependency-free. It does not read .env,
does not call the network and does not execute implementation code.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "reports/predictability-validation.json"
TASK_ID_RE = re.compile(r"^TASK-[0-9A-Z]+$")
REQUIRED_MICRO_FIELDS = [
    "slice",
    "work_package",
    "source_docs",
    "outputs",
    "constraints",
    "forbidden",
    "gate_ids",
    "required_evidence",
    "required_reports",
    "dependencies",
    "handoff_to",
    "acceptance",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(read(path))


def parse_scalar(text: str, key: str) -> str | None:
    match = re.search(rf'^\s+{re.escape(key)}:\s*"?([^"\n]+)"?\s*$', text, re.MULTILINE)
    return match.group(1).strip() if match else None


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


def task_cards() -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    for path in sorted((ROOT / "tasks").glob("TASK-*.yml")):
        text = read(path)
        task_id = parse_scalar(text, "id") or path.stem
        card = {
            "id": task_id,
            "path": str(path.relative_to(ROOT)),
            "title": parse_scalar(text, "title") or "",
            "role": parse_scalar(text, "role") or "",
            "owner": parse_scalar(text, "owner") or "",
            "status": (parse_scalar(text, "status") or "draft").lower(),
            "slice": parse_scalar(text, "slice") or "",
            "work_package": parse_scalar(text, "work_package") or "",
            "source_docs": parse_list(text, "source_docs"),
            "outputs": parse_list(text, "outputs"),
            "constraints": parse_list(text, "constraints"),
            "forbidden": parse_list(text, "forbidden"),
            "gate_ids": parse_list(text, "gate_ids"),
            "required_evidence": parse_list(text, "required_evidence"),
            "required_reports": parse_list(text, "required_reports"),
            "dependencies": parse_list(text, "dependencies"),
            "handoff_to": parse_list(text, "handoff_to"),
            "acceptance": parse_list(text, "acceptance"),
            "micro_tasks": parse_list(text, "micro_tasks"),
            "has_goal": bool(re.search(r"^\s+goal:\s*", text, re.MULTILINE)),
        }
        cards[task_id] = card
    return cards


def validate_manifest(report: dict[str, Any]) -> None:
    manifest_path = ROOT / "docs/contracts/ContractManifest.json"
    if not manifest_path.exists():
        issue(report, "Missing docs/contracts/ContractManifest.json")
        return

    manifest = load_json(manifest_path)
    if manifest.get("contractVersion") != "contract-manifest.v1":
        issue(report, "ContractManifest.json has wrong contractVersion.")

    base = manifest_path.parent
    contract_ids: set[str] = set()
    for contract in manifest.get("contracts", []):
        contract_id = contract.get("id", "")
        if contract_id in contract_ids:
            issue(report, f"Duplicate contract id in manifest: {contract_id}")
        contract_ids.add(contract_id)

        for key in ["doc", "schema"]:
            rel = contract.get(key)
            if not rel:
                issue(report, f"Manifest contract {contract_id} lacks {key}.")
                continue
            target = (base / rel).resolve()
            if not target.exists():
                issue(report, f"Manifest contract {contract_id} references missing {key}: {rel}")
            elif key == "schema":
                try:
                    load_json(target)
                except json.JSONDecodeError as exc:
                    issue(report, f"Schema is invalid JSON {target.relative_to(ROOT)}: {exc}")


def validate_gates(report: dict[str, Any]) -> set[str]:
    gates_path = ROOT / "docs/Evals/gates.json"
    if not gates_path.exists():
        issue(report, "Missing docs/Evals/gates.json")
        return set()

    gates = load_json(gates_path)
    if gates.get("contractVersion") != "gate-matrix.v1":
        issue(report, "gates.json has wrong contractVersion.")

    ids: set[str] = set()
    for gate in gates.get("gates", []):
        gate_id = gate.get("id", "")
        if not gate_id:
            issue(report, "Gate without id.")
            continue
        if gate_id in ids:
            issue(report, f"Duplicate gate id: {gate_id}")
        ids.add(gate_id)
        for key in ["title", "slice", "owner", "command", "requiredEvidence"]:
            if key not in gate or gate[key] in ("", []):
                issue(report, f"Gate {gate_id} lacks {key}.")
    report["gate_count"] = len(ids)
    return ids


def validate_tasks(report: dict[str, Any], gate_ids: set[str]) -> None:
    cards = task_cards()
    report["task_count"] = len(cards)
    report["epic_count"] = sum(1 for card in cards.values() if card["status"] == "epic")
    report["micro_task_count"] = sum(1 for card in cards.values() if card["status"] != "epic")

    for task_id, card in cards.items():
        if not TASK_ID_RE.match(task_id):
            issue(report, f"{card['path']} has invalid task id {task_id}.")

        if card["status"] == "epic":
            if not card["micro_tasks"]:
                issue(report, f"{card['path']} is epic but has no micro_tasks.")
            for micro_id in card["micro_tasks"]:
                if micro_id not in cards:
                    issue(report, f"{card['path']} references missing micro task {micro_id}.")
            continue

        for field in REQUIRED_MICRO_FIELDS:
            value = card.get(field)
            if field == "dependencies":
                if value is None:
                    issue(report, f"{card['path']} lacks required micro-task field {field}.")
                continue
            if value in ("", [], None):
                issue(report, f"{card['path']} lacks required micro-task field {field}.")

        if not card["has_goal"]:
            issue(report, f"{card['path']} lacks goal.")

        for gate_id in card["gate_ids"]:
            if gate_id not in gate_ids:
                issue(report, f"{card['path']} references unknown gate id {gate_id}.")

        expected_report = f"reports/task-evidence/{task_id}.json"
        if expected_report not in card["required_reports"]:
            issue(report, f"{card['path']} must require {expected_report}.")

        for dep in card["dependencies"]:
            if dep not in cards:
                issue(report, f"{card['path']} depends on missing {dep}.")

    cycles = dependency_cycles(cards)
    if cycles:
        issue(report, f"Task dependency cycles: {cycles}")


def dependency_cycles(cards: dict[str, dict[str, Any]]) -> list[list[str]]:
    graph = {
        task_id: [dep for dep in card.get("dependencies", []) if dep in cards]
        for task_id, card in cards.items()
        if card.get("status") != "epic"
    }
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
            visit(dep)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return cycles


def validate_fixtures(report: dict[str, Any]) -> None:
    required_fixture_files = [
        ROOT / "fixtures/price-books/ceiling-basic-v1.json",
        ROOT / "fixtures/coefficients/ceiling-basic-v1.json",
        ROOT / "fixtures/pricing-profiles/default-v1.json",
        ROOT / "fixtures/markup-policies/default-v1.json",
        ROOT / "fixtures/seeds/tenant-ab.json",
        ROOT / "fixtures/ai-gateway/ai-payload-safety-cases.json",
    ]
    for path in required_fixture_files:
        if not path.exists():
            issue(report, f"Missing fixture {path.relative_to(ROOT)}")
            continue
        try:
            load_json(path)
        except json.JSONDecodeError as exc:
            issue(report, f"Invalid JSON fixture {path.relative_to(ROOT)}: {exc}")

    golden_files = sorted((ROOT / "fixtures/golden-estimates").glob("*.json"))
    report["golden_estimates_count"] = len(golden_files)
    if len(golden_files) < 5:
        issue(report, "Need at least 5 synthetic golden estimates.")

    nonzero_complete_totals = 0
    for path in golden_files:
        try:
            fixture = load_json(path)
        except json.JSONDecodeError as exc:
            issue(report, f"Invalid golden fixture {path.relative_to(ROOT)}: {exc}")
            continue
        if fixture.get("contractVersion") != "golden-estimate.v1":
            issue(report, f"{path.relative_to(ROOT)} has wrong contractVersion.")
        if fixture.get("source") != "synthetic_stub":
            issue(report, f"{path.relative_to(ROOT)} must be synthetic_stub until real pilot approval.")
        expected = fixture.get("expected", {})
        if expected.get("completenessStatus") == "complete":
            for variant in expected.get("variants", {}).values():
                amount = (variant.get("finalTotal") or {}).get("amountMinor")
                if amount and amount != "0":
                    nonzero_complete_totals += 1
        snapshots = fixture.get("snapshots", {})
        for ref_key, ref in snapshots.items():
            target = ROOT / ref
            if not target.exists():
                issue(report, f"{path.relative_to(ROOT)} {ref_key} references missing {ref}.")
    if nonzero_complete_totals == 0:
        issue(report, "Golden complete fixtures do not contain non-zero expected totals.")

    ai_corpus = ROOT / "fixtures/ai-gateway/ai-payload-safety-cases.json"
    if ai_corpus.exists():
        data = load_json(ai_corpus)
        report["ai_payload_case_count"] = len(data.get("cases", []))
        if len(data.get("cases", [])) < 4:
            issue(report, "AI payload safety corpus needs at least 4 cases.")

    seed = ROOT / "fixtures/seeds/tenant-ab.json"
    if seed.exists():
        data = load_json(seed)
        tenant_ids = {tenant.get("tenantId") for tenant in data.get("tenants", [])}
        if len(tenant_ids) < 2:
            issue(report, "Tenant seed must contain at least two tenants.")


def validate_evidence_reports(report: dict[str, Any], gate_ids: set[str]) -> None:
    evidence_files = sorted((ROOT / "reports/task-evidence").glob("TASK-*.json"))
    report["evidence_report_count"] = len(evidence_files)
    for path in evidence_files:
        try:
            evidence = load_json(path)
        except json.JSONDecodeError as exc:
            issue(report, f"Invalid evidence JSON {path.relative_to(ROOT)}: {exc}")
            continue
        if evidence.get("contractVersion") != "agent-task-evidence.v1":
            issue(report, f"{path.relative_to(ROOT)} has wrong contractVersion.")
        for check in evidence.get("checks", []):
            if check.get("status") == "not_run" and not check.get("reason"):
                issue(report, f"{path.relative_to(ROOT)} has not_run check without reason.")
        for gate in evidence.get("gateResults", []):
            gate_id = gate.get("gateId")
            if gate_id not in gate_ids:
                issue(report, f"{path.relative_to(ROOT)} references unknown gate {gate_id}.")
            if gate.get("status") == "not_run" and not gate.get("reason"):
                issue(report, f"{path.relative_to(ROOT)} has not_run gate without reason.")
        confirmations = evidence.get("confirmations", {})
        for key, value in confirmations.items():
            if value is not False:
                issue(report, f"{path.relative_to(ROOT)} confirmation {key} must be false.")


def validate_price_requests(report: dict[str, Any]) -> None:
    request_files = sorted((ROOT / "reports/price-requests").glob("PRICE-REQUEST-*.json"))
    report["price_request_count"] = len(request_files)
    for path in request_files:
        try:
            request = load_json(path)
        except json.JSONDecodeError as exc:
            issue(report, f"Invalid price request JSON {path.relative_to(ROOT)}: {exc}")
            continue
        if request.get("contractVersion") != "price-input-request.v1":
            issue(report, f"{path.relative_to(ROOT)} has wrong contractVersion.")
        if request.get("status") == "open" and not request.get("nextActionForArchitect"):
            issue(report, f"{path.relative_to(ROOT)} is open but lacks nextActionForArchitect.")
        safety = request.get("safety", {})
        if safety.get("doNotSendToLlm") is not True:
            issue(report, f"{path.relative_to(ROOT)} must set safety.doNotSendToLlm = true.")
        if safety.get("containsRealPii") is not False:
            issue(report, f"{path.relative_to(ROOT)} must set safety.containsRealPii = false.")
        if safety.get("containsSecrets") is not False:
            issue(report, f"{path.relative_to(ROOT)} must set safety.containsSecrets = false.")


def validate_architect_requests(report: dict[str, Any]) -> None:
    request_files = sorted((ROOT / "workspace/architect-inbox/requests").glob("ARCH-REQUEST-*.json"))
    report["architect_request_count"] = len(request_files)
    for path in request_files:
        try:
            request = load_json(path)
        except json.JSONDecodeError as exc:
            issue(report, f"Invalid architect request JSON {path.relative_to(ROOT)}: {exc}")
            continue
        if request.get("contractVersion") != "architect-intervention-request.v1":
            issue(report, f"{path.relative_to(ROOT)} has wrong contractVersion.")
        if request.get("status") == "open" and not request.get("nextActionForArchitect"):
            issue(report, f"{path.relative_to(ROOT)} is open but lacks nextActionForArchitect.")
        if request.get("status") == "open" and not request.get("blockedWork"):
            issue(report, f"{path.relative_to(ROOT)} is open but lacks blockedWork.")
        safety = request.get("safety", {})
        if safety.get("containsRealPii") is not False:
            issue(report, f"{path.relative_to(ROOT)} must set safety.containsRealPii = false.")
        if safety.get("containsSecrets") is not False:
            issue(report, f"{path.relative_to(ROOT)} must set safety.containsSecrets = false.")


def validate_orchestrator_reports(report: dict[str, Any], gate_ids: set[str]) -> None:
    report_dir = ROOT / "reports/orchestrator"
    report["orchestrator_report_count"] = len(sorted(report_dir.glob("ORCH-CYCLE-*.json"))) if report_dir.exists() else 0

    latest = report_dir / "latest-cycle.json"
    if not latest.exists():
        return

    try:
        cycle = load_json(latest)
    except json.JSONDecodeError as exc:
        issue(report, f"Invalid orchestrator report {latest.relative_to(ROOT)}: {exc}")
        return

    if cycle.get("contractVersion") != "ai-orchestrator-cycle.v1":
        issue(report, f"{latest.relative_to(ROOT)} has wrong contractVersion.")
    if cycle.get("mode") == "proposed" and cycle.get("dryRun") is not True:
        issue(report, f"{latest.relative_to(ROOT)} proposed cycle must be dryRun=true.")

    safety = cycle.get("safety", {})
    required_true = [
        "development_time_only",
        "no_runtime_product_agent",
        "does_not_read_env_or_credentials",
        "does_not_call_network",
        "does_not_mutate_task_cards",
        "does_not_spawn_agents",
        "requires_architect_approval_before_command_packets",
        "does_not_calculate_prices",
        "does_not_handle_real_pii_or_real_price",
    ]
    for key in required_true:
        if safety.get(key) is not True:
            issue(report, f"{latest.relative_to(ROOT)} safety.{key} must be true.")

    cards = task_cards()
    for task in cycle.get("selectedTasks", []):
        task_id = task.get("taskId")
        if task_id not in cards:
            issue(report, f"{latest.relative_to(ROOT)} selected unknown task {task_id}.")
        for gate_id in task.get("gateIds", []):
            if gate_id not in gate_ids:
                issue(report, f"{latest.relative_to(ROOT)} selected task {task_id} references unknown gate {gate_id}.")
        expected = task.get("expectedEvidenceReports", [])
        if not expected:
            issue(report, f"{latest.relative_to(ROOT)} selected task {task_id} lacks expectedEvidenceReports.")

    if cycle.get("mode") == "approved" and not cycle.get("commandPackets"):
        issue(report, f"{latest.relative_to(ROOT)} approved cycle lacks commandPackets.")


def issue(report: dict[str, Any], message: str) -> None:
    report["status"] = "fail"
    report["issues"].append(message)


def main() -> int:
    report: dict[str, Any] = {
        "status": "pass",
        "checks": [
            "contract_manifest",
            "gate_matrix",
            "task_micro_metadata",
            "task_dependencies",
            "fixtures",
            "evidence_reports_if_present",
            "price_requests_if_present",
            "architect_requests_if_present",
            "orchestrator_reports_if_present",
        ],
        "issues": [],
    }

    validate_manifest(report)
    gate_ids = validate_gates(report)
    validate_tasks(report, gate_ids)
    validate_fixtures(report)
    validate_evidence_reports(report, gate_ids)
    validate_price_requests(report)
    validate_architect_requests(report)
    validate_orchestrator_reports(report, gate_ids)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Predictability validation: {report['status']}")
    print(f"Gates: {report.get('gate_count', 0)}")
    print(f"Tasks: {report.get('task_count', 0)}")
    print(f"Micro-tasks: {report.get('micro_task_count', 0)}")
    print(f"Golden estimates: {report.get('golden_estimates_count', 0)}")
    print(f"Price requests: {report.get('price_request_count', 0)}")
    print(f"Architect requests: {report.get('architect_request_count', 0)}")
    print(f"Orchestrator reports: {report.get('orchestrator_report_count', 0)}")
    print(f"Report: {REPORT_PATH.relative_to(ROOT)}")
    if report["issues"]:
        print("Issues:")
        for item in report["issues"]:
            print(f"- {item}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
