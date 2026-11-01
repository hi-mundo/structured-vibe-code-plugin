#!/usr/bin/env python3
"""UserPromptSubmit hook: switch mode on /vibecode enable|disable and remind the ruleset every turn.

Claude Code wraps a slash command as <command-name>/vibecode</command-name><command-args>enable</command-args>.
State changes happen here, deterministically, instead of trusting the model to run the script.
Always exits 0.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

COMMAND = re.compile(r"<command-name>/(?:vibecode:)?vibecode</command-name>\s*<command-args>([^<]*)</command-args>", re.S)
PLAIN = re.compile(r"^\s*/(?:vibecode:)?vibecode\s+(\w+)", re.S)

REMINDER = (
    "STRUCTURED VIBE CODE ACTIVE — developer decides. Before any edit: show the current code, the options with "
    "before/after, your recommendation, then ask (asking skill). Never implement a whole module without a valid "
    "allowance: run `python3 {root}/scripts/allowance.py check --repo . --path <path>` first. One closed slice at a time; "
    "commit only on explicit authorization."
)


def emit(context: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}))


def main() -> int:
    try:
        payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        prompt = payload.get("prompt", "") or ""
        if prompt.lstrip().startswith("<scheduled-task"):
            return 0
        from vibecode_state import find_repo, read_mode, write_mode

        repo = find_repo(payload.get("cwd"))
        match = COMMAND.search(prompt) or PLAIN.match(prompt)
        sub = (match.group(1).strip().split() or [""])[0].lower() if match else ""
        if sub in ("enable", "disable"):
            mode = "active" if sub == "enable" else "off"
            write_mode(repo, mode)
            emit(f"vibecode state already written: mode={mode} in {repo / '.vibecoding' / 'state.json'}. Do not run vibecode_state.py again; confirm the mode to the developer in one line." + (" Then load the `vibecode` skill and state the three active-mode rules." if mode == "active" else ""))
            return 0
        if read_mode(repo) == "active":
            emit(REMINDER.format(root=PLUGIN_ROOT))
    except Exception:  # noqa: BLE001 - a hook must never block the turn
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
