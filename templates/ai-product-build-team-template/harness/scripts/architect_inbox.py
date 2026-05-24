#!/usr/bin/env python3
"""Show open architect/external-input requests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUEST_DIR = ROOT / "workspace/architect-inbox/requests"


def load_requests() -> list[dict]:
    items: list[dict] = []
    for path in sorted(REQUEST_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"path": str(path.relative_to(ROOT)), "status": "invalid_json"}
        payload.setdefault("path", str(path.relative_to(ROOT)))
        items.append(payload)
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="Show architect inbox.")
    parser.add_argument("--json", action="store_true", help="Print JSON.")
    args = parser.parse_args()
    requests = [item for item in load_requests() if item.get("status", "open") == "open"]
    payload = {"openRequestCount": len(requests), "requests": requests}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"Architect inbox: {len(requests)} open request(s)")
    if not requests:
        print("- no open requests")
    for item in requests:
        print(f"- {item.get('requestId', item.get('path'))}: {item.get('title', '')}")


if __name__ == "__main__":
    main()

