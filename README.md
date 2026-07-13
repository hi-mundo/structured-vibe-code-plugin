# Structured VibeCoding Plugins

Professional controls for AI-assisted development: understand purpose before judging code, keep architecture decisions with the human, model the repository, and finish one validated scope at a time.

[![License: MIT](https://img.shields.io/badge/License-MIT-0f766e.svg)](LICENSE)
[![Codex marketplace](https://img.shields.io/badge/Codex-marketplace-111827.svg)](codex://plugins/marketplace/add?url=https%3A%2F%2Fgithub.com%2Fhi-mundo%2Fstructured-vibecoding-plugins.git)
[![Claude marketplace](https://img.shields.io/badge/Claude-copy%20commands-d97706.svg)](#claude-code)

## Plugins

| Plugin | What it controls | What it is not |
|---|---|---|
| **Review I2B** | Reconstructs intended behavior, examines at least three relevant revisions, compares actual behavior, runs focused mimic probes when justified, and maintains `.decisions.jsonl`. | A generic test runner or an exception scanner. |
| **VibeCoding Protector** | Models the repository in `STRUCTURE.md`, makes architecture choices explicit and human-owned, gates a single coherent slice, validation, commit authorization, and clean worktree. | An autonomous architect or a file-count commit bot. |

## Install

### Codex

[Add Structured VibeCoding marketplace](codex://plugins/marketplace/add?url=https%3A%2F%2Fgithub.com%2Fhi-mundo%2Fstructured-vibecoding-plugins.git)

Then install **Review I2B** and/or **VibeCoding Protector** in the plugin browser.

### Make VibeCoding Protector the repository default

After installing the plugin, add its activation contract to the target repository's `AGENTS.md`:

```bash
curl -fsSL https://raw.githubusercontent.com/hi-mundo/structured-vibecoding-plugins/main/scripts/enable-protector.sh | sh
```

The command is idempotent: running it again replaces the managed block instead of duplicating it. It makes `$vibecoding-protector` the default workflow for implementation, fixes, refactors, and architecture work, and requires active turns to begin with:

*VibeCode Protector enabled*

For an auditable installation, download and inspect the script first:

```bash
curl -fsSLO https://raw.githubusercontent.com/hi-mundo/structured-vibecoding-plugins/main/scripts/enable-protector.sh
less enable-protector.sh
sh enable-protector.sh
```

Pass a path to target another instruction file:

```bash
sh enable-protector.sh path/to/AGENTS.md
```

### Claude Code

```bash
claude plugin marketplace add hi-mundo/structured-vibecoding-plugins
claude plugin install review-i2b@structured-vibecoding-plugins
claude plugin install vibecoding-protector@structured-vibecoding-plugins
```

## Architecture

`shared/structured-vibecoding/` is the canonical home for reusable contracts, methodology, templates, Python utilities, and tests. `scripts/sync_shared.py` materializes verified copies inside each plugin because Codex and Claude install plugin packages in isolation.

```text
shared/structured-vibecoding/   canonical reusable source
plugins/review-i2b/             installable intent-to-behavior review
plugins/vibecoding-protector/   installable development guardrails
codex/, warp/, shared/*.md      reference-only legacy notes
```

The layers are intentionally distinct:

- **Plugin:** distributable package.
- **Skill:** agent workflow inside a plugin.
- **Contract:** deterministic machine-readable rules.
- **Script:** executable preflight or validation.
- **Reference:** methodology and evidence; never an executable gate.
- **Generated artifact:** project-local model or ledger such as `STRUCTURE.md` and `.decisions.jsonl`.

## Development

```bash
python3 scripts/sync_shared.py
python3 scripts/sync_shared.py --check
python3 -m unittest discover shared/structured-vibecoding/tests
```

See [AGENTS.md](AGENTS.md) for repository rules and `shared/structured-vibecoding/references/` for published methodological foundations.
