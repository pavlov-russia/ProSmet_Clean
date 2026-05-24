#!/usr/bin/env python3
"""Generate basic Codex and Claude role profiles from the Python registry."""

from __future__ import annotations

from pathlib import Path

from _agent_common import ROLE_PROFILES, ROOT


def profile_text(role: str, profile: dict) -> str:
    owns = "\n".join(f"- {item}" for item in profile["owns"])
    outputs = "\n".join(f"- {item}" for item in profile["outputs"])
    return f"""# {role}

Mission: {profile["mission"]}

## Soul

{profile["soul"]}

## Owns

{owns}

## Outputs

{outputs}

## Rules

- Work only on assigned task cards.
- Read Vision, Scope, Architecture and the task card first.
- Do not read `.env` or credentials.
- Do not deploy or call external services without approval.
- Finish with evidence report.
"""


def main() -> None:
    codex_root = ROOT / ".codex/agents/roles"
    claude_root = ROOT / ".claude/agents"
    codex_root.mkdir(parents=True, exist_ok=True)
    claude_root.mkdir(parents=True, exist_ok=True)

    for role, profile in ROLE_PROFILES.items():
        codex_dir = codex_root / role
        codex_dir.mkdir(parents=True, exist_ok=True)
        (codex_dir / "profile.md").write_text(profile_text(role, profile), encoding="utf-8")
        (claude_root / f"{profile['slug']}.md").write_text(profile_text(role, profile), encoding="utf-8")

    print(f"Generated profiles for {len(ROLE_PROFILES)} roles.")


if __name__ == "__main__":
    main()
