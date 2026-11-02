#!/usr/bin/env python3
"""UserPromptSubmit hook: handle /vibecode, /vibecode off and /vibecode terse deterministically, remind the rules every turn.

Claude Code wraps a slash command as <command-name>/vibecode</command-name><command-args>off</command-args>.
`/vibecode` alone initializes the repository when needed and turns active mode on; when already active it asks for a status report.
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
PLAIN = re.compile(r"^\s*/(?:vibecode:)?vibecode(?:\s+([^\n]*))?\s*$", re.S)

REMINDER = (
    "STRUCTURED VIBE CODE ACTIVE — developer decides. Before any edit: show the current code, the options with "
    "before/after, your recommendation, then ask (asking skill). Question buttons are named options, each with a "
    "one-line consequence in its description; never Yes/No/OK and never a button without the context above it. "
    "Never implement a whole module without a valid allowance: run `python3 {root}/scripts/allowance.py check --repo . --path <path>` first. "
    "One closed slice at a time; commit only on explicit authorization. "
    "Anything new to the repository: prior-art first (repository, then community); options carry source and license; copy only permissive code."
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
        words = (match.group(1) or "").strip().lower().split() if match else []
        sub = words[0] if words else ""
        state_file = repo / ".vibecoding" / "state.json"
        if match and not words:
            if not state_file.exists():
                from vibecode_init import init
                report = init(repo)
                state = write_state(repo, mode="active")
                emit(f"vibecode initialized and active: created={report['created']} skipped={report['skipped']} terse={'on' if state['terse'] else 'off'}. Do not run vibecode_init.py or vibecode_state.py again. Tell the developer in three lines what `.vibecoding/` holds, load the `vibecode` skill, state the four active-mode rules, and offer `/vibecode understand` next.")
            elif read_state(repo)["mode"] != "active":
                state = write_state(repo, mode="active")
                emit(f"vibecode state already written: mode=active terse={'on' if state['terse'] else 'off'} in {state_file}. Do not run vibecode_state.py again; confirm in one line, load the `vibecode` skill and state the four active-mode rules.")
            else:
                emit(f"vibecode already active. Report status: run `python3 {PLUGIN_ROOT}/scripts/vibecode_state.py get --repo .` and `python3 {PLUGIN_ROOT}/scripts/allowance.py list --repo .`; show mode, terse flag, current slice and valid allowances with expiry.")
            return 0
        if sub == "off":
            state = write_state(repo, mode="off")
            emit(f"vibecode state already written: mode=off terse={'on' if state['terse'] else 'off'} in {state_file}. Do not run vibecode_state.py again; confirm in one line.")
            return 0
        if sub == "terse":
            state = write_state(repo, terse=not read_state(repo)["terse"])
            emit(f"vibecode state already written: terse={'on' if state['terse'] else 'off'} in {state_file}. Do not run vibecode_state.py again; confirm in one line. Active mode is unchanged.")
            return 0
        state = read_state(repo)
        if state["mode"] == "active":
            emit(REMINDER.format(root=PLUGIN_ROOT) + (TERSE_REMINDER if state["terse"] else ""))
    except Exception:  # noqa: BLE001 - a hook must never block the turn
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
