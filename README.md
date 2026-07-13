# Structured VibeCoding Plugins

## Plugins

| Plugin | Contract |
|---|---|
| `structured-vibecoding` | Repository preflight, decision recovery, human-owned architecture, closed execution slices, execution backlog, and Review I2B before commit. |

## Install

### Codex

[Add marketplace](codex://plugins/marketplace/add?url=https%3A%2F%2Fgithub.com%2Fhi-mundo%2Fstructured-vibecoding-plugins.git)

### Claude Code

```bash
claude plugin marketplace add hi-mundo/structured-vibecoding-plugins
claude plugin install structured-vibecoding@structured-vibecoding-plugins
```

## Make VibeCoding Protector the default

Copy this block into the repository instruction file used by your code agent, such as `AGENTS.md` or `CLAUDE.md`:

```md
## VibeCode Protector

Use the installed `$structured-vibecoding` workflow for implementation, bug
fixes, refactoring, code review, test execution, repository investigation, and
architectural decisions.

At the beginning of every active turn, write:

*VibeCode Protector enabled*

Before acting, provide a concise technical checkback containing:

- objective understood;
- scope and affected files or modules;
- intended behavioral change and mechanism;
- validation and failure checks;
- risks, exclusions, and decisions requiring human confirmation.

Do not make product, architecture, domain, persistence, security, observability,
or contract decisions on the user's behalf. Present concrete options,
tradeoffs, and a recommendation, then wait for the user's decision.

Before editing a concrete block, show the proposed patch or exact before/after
text. Work on one coherent scope at a time. Do not start a new scope with an
unexplained dirty worktree.
```

The plugins do not edit or persist agent instruction files.

## Validate

```bash
python3 scripts/sync_shared.py --check
python3 -m unittest discover shared/structured-vibecoding/tests
python3 /path/to/plugin-creator/scripts/validate_plugin.py plugins/structured-vibecoding
git diff --check
```
