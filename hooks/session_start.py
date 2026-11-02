#!/usr/bin/env python3
"""SessionStart hook: announce the plugin and, when active mode is on, inject the rulesets.

Reads the loop rules from skills/vibecode/SKILL.md (heading "## Active mode rules") and,
when terse is on, the voice rules from skills/vibecode/references/terse.md plus the
vendored upstream body. The skill files stay the only source of truth. Never fails the
session: any error prints nothing and exits 0.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

RULES_HEADING = "## Active mode rules"
REFERENCES = PLUGIN_ROOT / "skills" / "vibecode" / "references"
UPSTREAM_MARKER = "<!-- upstream body below"


def section(text: str, heading: str) -> str:
    if heading not in text:
        return ""
    body = text.split(heading, 1)[1]
    nxt = body.find("\n## ")
    return body[:nxt].strip() if nxt != -1 else body.strip()


def active_rules() -> str:
    return section((PLUGIN_ROOT / "skills" / "vibecode" / "SKILL.md").read_text(encoding="utf-8"), RULES_HEADING)


def terse_rules() -> str:
    local = (REFERENCES / "terse.md").read_text(encoding="utf-8").strip()
    upstream = (REFERENCES / "terse-upstream.md").read_text(encoding="utf-8")
    if UPSTREAM_MARKER in upstream:
        upstream = upstream[upstream.index(UPSTREAM_MARKER):].split("\n", 1)[1]
    return local + "\n\n---\n\n" + upstream.strip()


def main() -> int:
    try:
        payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except (ValueError, OSError):
        payload = {}
    try:
        from vibecode_state import find_repo, read_state

        repo = find_repo(payload.get("cwd"))
        initialized = (repo / ".vibecoding").is_dir()
        state = read_state(repo)
        if state["mode"] == "active":
            lines = [
                f"STRUCTURED VIBE CODE ACTIVE — repository: {repo.name}. The developer decides; you show, propose and wait.",
                "Load the `vibecode` skill before any implementation work. Use the `asking` skill for every decision.",
                "",
                active_rules(),
            ]
            if state["terse"]:
                lines += ["", "TERSE VOICE ON (`/vibecode terse` toggles it). Rules:", "", terse_rules()]
        elif initialized:
            lines = [f"Structured Vibe Code installed in {repo.name}, inactive. `/vibecode` turns on active mode."]
        else:
            lines = ["Structured Vibe Code available. `/vibecode` prepares this repository and turns on active mode; `/vibecode understand` maps it before changes."]
        print("\n".join(lines))
    except Exception:  # noqa: BLE001 - a hook must never block the session
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
