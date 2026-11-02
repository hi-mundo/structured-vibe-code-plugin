#!/usr/bin/env python3
"""UserPromptSubmit hook: switch state on /vibecode enable|disable|terse and remind the rules every turn.

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
PLAIN = re.compile(r"^\s*/(?:vibecode:)?vibecode\s+([^\n]*)", re.S)

REMINDER = (
    "STRUCTURED VIBE CODE ACTIVE — developer decides. Before any edit: show the current code, the options with "
    "before/after, your recommendation, then ask (asking skill). Question buttons are named options, each with a "
    "one-line consequence in its description; never Yes/No/OK and never a button without the context above it. "
    "Never implement a whole module without a valid allowance: run `python3 {root}/scripts/allowance.py check --repo . --path <path>` first. "
    "One closed slice at a time; commit only on explicit authorization."
)
TERSE_REMINDER = (
    " TERSE VOICE ON: fragments, each fact once, payload (code, paths, errors, numbers, negations) verbatim; "
    "questions, options, warnings and anything persisted in full prose."
)


def emit(context: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}))


def main() -> int:
    try:
        payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        prompt = payload.get("prompt", "") or ""
        if prompt.lstrip().startswith("<scheduled-task"):
            return 0
        from vibecode_state import find_repo, read_state, write_state

        repo = find_repo(payload.get("cwd"))
        match = COMMAND.search(prompt) or PLAIN.match(prompt)
        words = match.group(1).strip().lower().split() if match else []
        sub, arg = (words[0] if words else ""), (words[1] if len(words) > 1 else "")
        state_file = repo / ".vibecoding" / "state.json"
        if sub in ("enable", "disable"):
            mode = "active" if sub == "enable" else "off"
            state = write_state(repo, mode=mode)
            emit(f"vibecode state already written: mode={mode} terse={'on' if state['terse'] else 'off'} in {state_file}. Do not run vibecode_state.py again; confirm the mode to the developer in one line." + (" Then load the `vibecode` skill and state the three active-mode rules." if mode == "active" else ""))
            return 0
        if sub == "terse" and arg in ("on", "off"):
            write_state(repo, terse=arg == "on")
            emit(f"vibecode state already written: terse={arg} in {state_file}. Do not run vibecode_state.py again; confirm in one line.")
            return 0
        state = read_state(repo)
        if state["mode"] == "active":
            emit(REMINDER.format(root=PLUGIN_ROOT) + (TERSE_REMINDER if state["terse"] else ""))
    except Exception:  # noqa: BLE001 - a hook must never block the turn
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
