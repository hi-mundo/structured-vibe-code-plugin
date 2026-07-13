# Repository Instructions

## Project layout

- `plugins/structured-vibecoding/`: installable workflow containing preflight, execution gates, and Review I2B skills.
- `shared/structured-vibecoding/`: canonical reusable contracts, references, templates, Python runtime, and tests.
- `scripts/sync_shared.py`: copies and verifies only the shared helpers required by each plugin.
- `codex/`, `shared/*.md`, `warp/`: legacy reference-only documentation; not plugins.

## Build, test, and lint

- Sync package copies: `python3 scripts/sync_shared.py`
- Verify no shared drift: `python3 scripts/sync_shared.py --check`
- Unit tests: `python3 -m unittest discover shared/structured-vibecoding/tests`
- Compile Python: `python3 -m compileall shared plugins scripts`

## Architecture and boundaries

- Shared utilities are canonical. Edit copied plugin helpers only through their source under `shared/structured-vibecoding/utils/`.
- The plugin must remain usable when installed from an isolated cache.
- Deterministic scripts emit JSON and nonzero exit codes on blocked states.
- References guide analysis; they do not act as runtime guardrails or proof.

## Done means

- manifests parse, skills validate, shared drift check passes, tests pass, and plugin install is verified.
