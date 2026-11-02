---
description: Structured Vibe Code — /vibecode (init + on, or status) | off | terse | understand | allow
argument-hint: "[off|terse|understand|allow <scope> --until <date>]"
---

Arguments: `$ARGUMENTS`

The `UserPromptSubmit` hook already handled the state switches (`/vibecode`, `off`, `terse`) before you read this; its message in the context tells you what it wrote. Never run `vibecode_init.py` or `vibecode_state.py` yourself for those. Scripts live in `${CLAUDE_PLUGIN_ROOT}/scripts/`; every script prints JSON and a nonzero exit code is a blocked state to show the developer, not to work around.

- **(empty)**: follow the hook message. First time in a repository it created `.vibecoding/`, `STRUCTURE.md`, `.decisions.jsonl`, the `.gitignore` entry, and turned active mode on: explain in three lines what `.vibecoding/` holds, load the `vibecode` skill, state the four rules, offer `/vibecode understand`. Repository already set up but off: confirm active in one line, state the four rules. Already active: report status (mode, terse flag, current slice, valid allowances with expiry) using `vibecode_state.py get` and `allowance.py list`.
- **`off`**: the hook wrote `mode=off`. Confirm in one line.
- **`terse`**: the hook toggled the compressed voice. Confirm the new value in one line. Active mode is unchanged.
- **`understand`**: load the `understand` skill and follow it. It runs `history_chunks.py` and produces `.vibecoding/understanding.md`.
- **`allow`** with no further arguments: run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/allowance.py list --repo .` and show a table: scope, expires, days left, note. Mark expired ones. Mention `allowance.py revoke --id <id>` for removing one.
- **`allow <scope> --until <YYYY-MM-DD> [--note "..."]`**: the developer is granting permission for autonomous implementation inside `<scope>` (a path or glob). Restate exactly what it covers and until when, wait for a yes, then run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/allowance.py grant --repo . --scope "<scope>" --until <date> --note "<note>"`.
- anything else: say the argument is unknown and print the table.

| Command | What it does |
|---|---|
| `/vibecode` | First run: creates `.vibecoding/`, `STRUCTURE.md`, `.decisions.jsonl`, `.gitignore` entry and turns active mode on. Later: turns it on, or shows status when already on |
| `/vibecode off` | Turns active mode off for this repository |
| `/vibecode terse` | Toggles the compressed voice; questions and warnings stay in full prose either way |
| `/vibecode understand` | Maps the repository and its history: how it started, what it became, where it is going |
| `/vibecode allow [<scope> --until <date>]` | Lists grants, or grants scoped, time-boxed permission for autonomous implementation |
