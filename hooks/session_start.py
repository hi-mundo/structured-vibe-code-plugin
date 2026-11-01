#!/usr/bin/env python3
"""SessionStart hook: announce the plugin and, when active mode is on, inject the ruleset.

Reads the ruleset from skills/vibecode/SKILL.md at runtime so the skill stays the only
source of truth. Never fails the session: any error prints nothing and exits 0.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

RULES_HEADING = "## Active mode rules"


def active_rules() -> str:
    text = (PLUGIN_ROOT / "skills" / "vibecode" / "SKILL.md").read_text(encoding="utf-8")
    if RULES_HEADING not in text:
        return ""
    body = text.split(RULES_HEADING, 1)[1]
    next_heading = body.find("\n## ")
    return body[:next_heading].strip() if next_heading != -1 else body.strip()


def main() -> int:
    try:
        payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except (ValueError, OSError):
        payload = {}
    try:
        from vibecode_state import find_repo, read_mode

        repo = find_repo(payload.get("cwd"))
        initialized = (repo / ".vibecoding").is_dir()
        mode = read_mode(repo)
        if mode == "active":
            lines = [
                f"STRUCTURED VIBE CODE ACTIVE — repository: {repo.name}. The developer decides; you show, propose and wait.",
                "Load the `vibecode` skill before any implementation work. Use the `asking` skill for every decision.",
                "",
                active_rules(),
            ]
        elif initialized:
            lines = [f"Structured Vibe Code installed in {repo.name}, inactive. `/vibecode enable` turns on active mode; `/vibecode status` shows state."]
        else:
            lines = ["Structured Vibe Code available. `/vibecode init` prepares this repository; `/vibecode understand` maps it before changes."]
        print("\n".join(line for line in lines if line is not None))
    except Exception:  # noqa: BLE001 - a hook must never block the session
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
