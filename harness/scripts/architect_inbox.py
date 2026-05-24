#!/usr/bin/env python3
"""List open architect intervention and price input requests.

This is a local inbox helper. It does not read .env, does not call the network
and does not mutate request files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ARCHITECT_REQUESTS = ROOT / "workspace/architect-inbox/requests"
PRICE_REQUESTS = ROOT / "reports/price-requests"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def request_summary(path: Path, request: dict[str, Any], kind: str) -> dict[str, Any]:
    if kind == "price":
        title = request.get("reason", "Price input request")
        request_type = "price_input"
        priority = "blocking" if request.get("status") == "open" else "normal"
        can_continue = bool(request.get("safety", {}).get("syntheticFallbackAllowed", False))
        blocked_work = request.get("neededFor", [])
    else:
        title = request.get("title", "Architect intervention request")
        request_type = request.get("requestType", "unknown")
        priority = request.get("priority", "normal")
        can_continue = request.get("canContinueWithoutAnswer", False)
        blocked_work = request.get("blockedWork", [])

    return {
        "kind": kind,
        "path": str(path.relative_to(ROOT)),
        "requestId": request.get("requestId", path.stem),
        "taskId": request.get("taskId", ""),
        "status": request.get("status", "unknown"),
        "priority": priority,
        "requestType": request_type,
        "title": title,
        "canContinueWithoutAnswer": can_continue,
        "blockedWork": blocked_work,
        "nextActionForArchitect": request.get("nextActionForArchitect", ""),
    }


def collect_requests(include_closed: bool) -> tuple[list[dict[str, Any]], list[str]]:
    requests: list[dict[str, Any]] = []
    issues: list[str] = []

    for path in sorted(ARCHITECT_REQUESTS.glob("ARCH-REQUEST-*.json")):
        try:
            data = read_json(path)
        except json.JSONDecodeError as exc:
            issues.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
            continue
        if include_closed or data.get("status") == "open":
            requests.append(request_summary(path, data, "architect"))

    for path in sorted(PRICE_REQUESTS.glob("PRICE-REQUEST-*.json")):
        try:
            data = read_json(path)
        except json.JSONDecodeError as exc:
            issues.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
            continue
        if include_closed or data.get("status") == "open":
            requests.append(request_summary(path, data, "price"))

    priority_order = {"blocking": 0, "high": 1, "normal": 2, "low": 3}
    requests.sort(key=lambda item: (priority_order.get(item["priority"], 4), item["path"]))
    return requests, issues


def print_text(requests: list[dict[str, Any]], issues: list[str]) -> None:
    print(f"Architect inbox: {len(requests)} open request(s)")
    if not requests:
        print("- no open requests")
    for item in requests:
        print(
            f"- [{item['priority']}] {item['requestId']} "
            f"({item['kind']}, {item['requestType']}, {item['taskId']})"
        )
        print(f"  path: {item['path']}")
        print(f"  title: {item['title']}")
        print(f"  can continue: {str(item['canContinueWithoutAnswer']).lower()}")
        if item["blockedWork"]:
            print(f"  blocked: {', '.join(item['blockedWork'])}")
        if item["nextActionForArchitect"]:
            print(f"  next: {item['nextActionForArchitect']}")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")


def main() -> int:
    parser = argparse.ArgumentParser(description="List ProSmet architect inbox requests.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--all", action="store_true", help="Include answered/cancelled requests")
    args = parser.parse_args()

    requests, issues = collect_requests(include_closed=args.all)
    payload = {
        "status": "attention" if requests or issues else "empty",
        "requests": requests,
        "issues": issues,
        "requestCount": len(requests),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text(requests, issues)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
