#!/usr/bin/env python3
"""Generate Claude/Codex agent profiles and per-role helper scripts."""

from __future__ import annotations

import json
import re
from pathlib import Path

from _agent_common import CANONICAL_FLOW, GLOBAL_INVARIANTS, ROLE_PROFILES, ROOT


GENERATED_NOTICE = "<!-- Generated from harness/scripts/agents/_agent_common.py. Edit registry, then rerun generator. -->"


def anchor(role_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", role_name.lower())


def md_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def claude_profile(role_name: str, profile: dict) -> str:
    tools = "\n".join(f"  - {tool}" for tool in profile["tools"])
    task_cards = "\n".join(f"- `{task}`" for task in profile["default_tasks"]) or "- нет прямой карточки"
    return f"""---
name: {profile["slug"]}
description: {profile["description"]}
tools:
{tools}
---

{GENERATED_NOTICE}

# {profile["title"]} · ProSmet AI Employee

## Soul

{profile["soul"]}

## Mission

{profile["mission"]}

## Canonical Flow

`{CANONICAL_FLOW}`

## Primary Docs

{md_list(profile["read_first"])}

## Implementation Contracts

{md_list(profile["contracts"])}

## Stack And Skills

{md_list(profile["stack"])}

## Owns

{md_list(profile["owns"])}

## Forbidden

{md_list(profile["forbidden"])}

## Quality Gates

{md_list(profile["quality_gates"])}

## Outputs

{md_list(profile["outputs"])}

## Task Cards

{task_cards}

## Handoff

В конце работы перечисли измененные файлы, выполненные проверки, незакрытые blockers, next executor из task card и явно подтверди, что Scope не расширен, секреты не читались, чужие изменения не откатывались.
"""


def codex_profile(role_name: str, profile: dict) -> str:
    task_cards = "\n".join(f"  - {task}" for task in profile["default_tasks"]) or "  - none"
    forbidden_codes = "\n".join(
        [
            "  - read_env_or_credentials",
            "  - trust_client_tenant_id",
            "  - send_pii_or_money_to_llm",
            "  - llm_price_or_discount_or_coefficient",
            "  - publish_without_human_review_or_audited_auto_publish",
            "  - bypass_rls_or_withTenant",
        ]
    )
    read_first = "\n".join(f"  - {doc}" for doc in profile["read_first"])
    contracts = "\n".join(f"  - {doc}" for doc in profile["contracts"])
    return f"""---
role_id: {role_name}
team_source: Team.yml
role_card: harness/build-team.md#{anchor(role_name)}
claude_profile: .claude/agents/{profile["slug"]}.md
helper: harness/scripts/agents/{profile["script"]}
task_selector:
  role: {role_name}
  task_glob: tasks/TASK-*.yml
default_tasks:
{task_cards}
must_read:
{read_first}
contracts:
{contracts}
forbidden_codes:
{forbidden_codes}
handoff_required: true
---

{GENERATED_NOTICE}

# {profile["title"]} · Codex Profile

## Soul

{profile["soul"]}

## Mission

{profile["mission"]}

## Canonical Flow

`{CANONICAL_FLOW}`

## Stack And Skills

{md_list(profile["stack"])}

## Owns

{md_list(profile["owns"])}

## Forbidden

{md_list(profile["forbidden"])}

## Outputs

{md_list(profile["outputs"])}

## Quality Gates

{md_list(profile["quality_gates"])}

## Operating Protocol

1. Прочитай `AGENTS.md`, `EntryPointForTask.md`, `Focus.md`, `Team.yml`, `Scope.md`.
2. Найди task card по `default_tasks`, `task.role`, `task.owner` или handoff.
3. Прочитай `source_docs` task card и релевантные contracts.
4. Работай только в границах task card и Scope.
5. Запусти helper: `python3 harness/scripts/agents/{profile["script"]}` для role summary или `--json` для machine-readable context.
6. Заверши handoff: changed files, checks, blockers, next executor, scope/secrets/tenant/AI-money confirmations.
"""


def role_script(role_name: str) -> str:
    return f"""#!/usr/bin/env python3
\"\"\"CLI helper for the ProSmet {role_name} AI employee.\"\"\"

from _agent_common import main


if __name__ == "__main__":
    main("{role_name}")
"""


def shared_docs() -> dict[str, str]:
    return {
        "base-profile.md": f"""# Base Agent Profile

{GENERATED_NOTICE}

Every ProSmet AI employee is a development-time role, not a runtime product agent.

Canonical flow:

```text
{CANONICAL_FLOW}
```

Every agent reads `AGENTS.md`, follows `Scope.md`, uses task cards, and ends with a handoff.
""",
        "invariants.md": "# Invariants\n\n" + GENERATED_NOTICE + "\n\n" + md_list(GLOBAL_INVARIANTS) + "\n",
        "task-protocol.md": f"""# Task Protocol

{GENERATED_NOTICE}

1. Read `EntryPointForTask.md`.
2. Select role from `Team.yml`.
3. Open the matching `tasks/TASK-*.yml`.
4. Read task `source_docs`.
5. Read the relevant file in `docs/contracts/`.
6. Implement only inside Scope.
7. Run or state checks.
8. Produce handoff.
""",
        "handoff-template.md": f"""# Handoff Template

{GENERATED_NOTICE}

Тип документа: handoff  
Дата: YYYY-MM-DD  
Автор / роль:  
Родительская задача:  

## Что сделано

## Измененные файлы

## Проверки

## Blockers

## Следующий исполнитель

## Подтверждения

- Scope не расширен.
- Секреты и `.env*` не читались.
- Tenant isolation / AI-money invariants не ослаблены.
- Чужие изменения не откатывались.
""",
    }


def write_readmes() -> None:
    claude_lines = [
        "# .claude/agents",
        "",
        "Project subagents Claude Code для ProSmet.",
        "",
        GENERATED_NOTICE,
        "",
        "## Canonical Roles",
        "",
    ]
    codex_lines = [
        "# .codex/agents",
        "",
        "Codex agent profiles для ProSmet. `AGENTS.md` остается главным harness; эти профили уточняют душу, стек, task protocol и helper scripts роли.",
        "",
        GENERATED_NOTICE,
        "",
        "## Canonical Roles",
        "",
    ]
    for role_name, profile in ROLE_PROFILES.items():
        claude_lines.append(f"- `{profile['slug']}` -> `{role_name}`")
        codex_lines.append(f"- `roles/{role_name}/profile.md` -> `{profile['script']}`")
    claude_lines += [
        "",
        "Regenerate with `python3 harness/scripts/agents/generate_agent_assets.py`.",
    ]
    codex_lines += [
        "",
        "Shared protocol lives in `_shared/`.",
        "",
        "Validate with `python3 harness/scripts/agents/validate_agent_profiles.py`.",
    ]
    write(ROOT / ".claude/agents/README.md", "\n".join(claude_lines))
    write(ROOT / ".codex/agents/README.md", "\n".join(codex_lines))


def write_registry() -> None:
    data = {
        "canonical_flow": CANONICAL_FLOW,
        "roles": {
            role_name: {
                "slug": profile["slug"],
                "title": profile["title"],
                "script": f"harness/scripts/agents/{profile['script']}",
                "claude_profile": f".claude/agents/{profile['slug']}.md",
                "codex_profile": f".codex/agents/roles/{role_name}/profile.md",
                "default_tasks": profile["default_tasks"],
            }
            for role_name, profile in ROLE_PROFILES.items()
        },
    }
    content = json.dumps(data, ensure_ascii=False, indent=2)
    write(ROOT / "harness/scripts/agents/agent_registry.json", content)
    write(ROOT / ".codex/agents/agent-registry.json", content)


def main() -> None:
    for role_name, profile in ROLE_PROFILES.items():
        write(ROOT / ".claude/agents" / f"{profile['slug']}.md", claude_profile(role_name, profile))
        write(ROOT / ".codex/agents/roles" / role_name / "profile.md", codex_profile(role_name, profile))
        write(ROOT / "harness/scripts/agents" / profile["script"], role_script(role_name))

    for filename, content in shared_docs().items():
        write(ROOT / ".codex/agents/_shared" / filename, content)

    write_readmes()
    write_registry()

    for path in (ROOT / "harness/scripts/agents").glob("*.py"):
        if path.name != "_agent_common.py":
            path.chmod(0o755)

    print(f"Generated {len(ROLE_PROFILES)} agent profiles for Claude and Codex.")


if __name__ == "__main__":
    main()
