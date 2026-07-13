# Repository Instructions

## Project layout

- `plugins/`: independently installable Codex and Claude plugins.
- `shared/structured-vibecoding/`: canonical reusable contracts, references, templates, Python runtime, and tests.
- `scripts/sync_shared.py`: materializes and verifies canonical shared files in plugin packages.
- `codex/`, `shared/*.md`, `warp/`: legacy reference-only documentation; not plugins.

## Build, test, and lint

- Sync package copies: `python3 scripts/sync_shared.py`
- Verify no shared drift: `python3 scripts/sync_shared.py --check`
- Unit tests: `python3 -m unittest discover shared/structured-vibecoding/tests`
- Compile Python: `python3 -m compileall shared plugins scripts`

## Architecture and boundaries

- Shared source is canonical. Never edit `plugins/*/vendor/structured-vibecoding/` directly.
- A plugin must remain usable when installed from an isolated cache.
- Deterministic scripts emit JSON and nonzero exit codes on blocked states.
- References guide analysis; they do not act as runtime guardrails or proof.

## Done means

- manifests parse, skills validate, shared drift check passes, tests pass, and plugin install is verified.
