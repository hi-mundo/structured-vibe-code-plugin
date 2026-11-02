---
description: Structured Vibe Code — init | understand | enable | disable | terse | status | allow | allowances
argument-hint: "[init|understand|enable|disable|terse on|off|status|allow <scope> --until <date>|allowances]"
---

Subcommand requested: `$ARGUMENTS`

Run the matching branch. Scripts live in `${CLAUDE_PLUGIN_ROOT}/scripts/`. Every script prints JSON; a nonzero exit code means a blocked state that you must show to the developer instead of working around.

- **(empty) or `help`**: print the table below and ask which one to run. Do not guess.
- **`init`**: run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/vibecode_init.py --repo .`. Show the developer the `created` and `skipped` lists from the JSON, then explain what `.vibecoding/` holds in three lines. Suggest `/vibecode understand` next.
- **`understand`**: load the `understand` skill and follow it. It runs `history_chunks.py` and produces `.vibecoding/understanding.md`.
- **`enable`** / **`disable`**: run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/vibecode_state.py set active` (or `off`). Confirm the new mode in one line. When enabling, load the `vibecode` skill and state the three rules of active mode.
- **`terse on`** / **`terse off`**: the hook already wrote the flag. Confirm in one line. `on` means the compressed voice from `skills/vibecode/references/terse.md`; `off` means normal prose. Active mode is unaffected.
- **`status`**: run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/vibecode_state.py get` and `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/allowance.py list --repo .`. Report mode, terse flag, active slice, and valid allowances with their expiry.
- **`allow <scope> --until <YYYY-MM-DD> [--note "..."]`**: the developer is granting permission for autonomous implementation inside `<scope>` (a path or glob). Before writing it, restate exactly what the allowance covers and until when, and wait for a yes. Then run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/allowance.py grant --repo . --scope "<scope>" --until <date> --note "<note>"`.
- **`allowances`**: run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/allowance.py list --repo .` and show a table: scope, expires, days left, note. Mark expired ones.
- anything else: say the subcommand is unknown and print the table.

| Subcommand | What it does |
|---|---|
| `init` | Creates `.vibecoding/`, `STRUCTURE.md`, `.decisions.jsonl`, `.gitignore` entries |
| `understand` | Maps the repository and its history: how it started, what it became, where it is going |
| `enable` / `disable` | Turns active mode on or off for this repository (terse voice comes on with it) |
| `terse on` / `terse off` | Compressed voice on or off; questions and warnings stay in full prose either way |
| `status` | Mode, current slice, valid allowances |
| `allow <scope> --until <date>` | Grants scoped, time-boxed permission for autonomous implementation |
| `allowances` | Lists grants and their expiry |
