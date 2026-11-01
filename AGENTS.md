# Repository Instructions

This repository is one plugin, `vibecode` (Structured Vibe Code), for Claude Code and Codex. The repository is also its own single-plugin marketplace.

## Commands the plugin exposes

| Command | Effect |
|---|---|
| `/vibecode init` | create `.vibecoding/`, `STRUCTURE.md`, `.decisions.jsonl`, gitignore entry |
| `/vibecode understand` | map repository and history into `.vibecoding/understanding.md` |
| `/vibecode enable` / `disable` | active mode on/off, stored in `.vibecoding/state.json` |
| `/vibecode status` | mode, slice, allowances |
| `/vibecode allow <scope> --until <date>` | scoped, dated permission for autonomous implementation |
| `/vibecode allowances` | list grants |

`commands/vibecode.md` dispatches on `$ARGUMENTS`. `hooks/prompt_submit.py` also parses `enable|disable` and writes the state deterministically.

## Layout

- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`: manifests. Keep `version` identical in both plugin manifests.
- `commands/`: one thin command file.
- `hooks/`: `hooks.json` (Claude Code), `codex-hooks.json`, `session_start.py`, `prompt_submit.py`. Hooks read the ruleset from `skills/vibecode/SKILL.md` under the heading `## Active mode rules`; do not rename that heading.
- `skills/`: `vibecode` (loop), `asking` (decision protocol), `understand` (history), `execution-slices` (scope gates), `review-i2b` (behavioral review). Each has `agents/openai.yaml` for Codex.
- `scripts/`: Python 3.9+ standard library. `vibecode_state.py` is imported by the others and by the hooks; keep it dependency-free.
- `contracts/`, `references/`, `templates/`: schemas, methodology, `STRUCTURE.md` template.
- `tests/`: `unittest`.
- `docs/legacy/`: unrelated historical notes (local OpenAI-compatible proxies). Not part of the plugin.

## Build, test, lint

- `python3 -m unittest discover tests`
- `python3 -m compileall -q scripts hooks`
- `git diff --check`

## Rules for changes here

- Skills reference scripts as `<plugin>/scripts/...`; in Claude Code `<plugin>` is `${CLAUDE_PLUGIN_ROOT}`, otherwise two directories above the SKILL.md.
- Scripts print one JSON object and use the exit codes documented in `README.md`; changing a code means updating the README table and the skill that interprets it.
- Hooks never raise, always exit 0, and must finish within 5 seconds.
- A feature that lets the agent decide more on its own does not belong here.

## Done means

Manifests parse, `unittest` passes, `compileall` passes, hooks answer the sample payloads in the README, and the plugin installs from a clean cache.
