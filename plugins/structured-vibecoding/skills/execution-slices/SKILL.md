---
name: execution-slices
description: Control human-owned technical decisions and implement exactly one closed software scope at a time, recording additional discoveries in an execution backlog and requiring validation plus explicit commit authorization before the next slice. Use only as a phase of the Structured VibeCoding workflow.
---

# Execution Slices

## Surface the plan

Before investigation, commands, tests, diff review, edits, or technical decisions, state objective, affected domains and paths, mechanism, validation, failure checks, exclusions, risk, and decisions requiring human confirmation. Before a concrete edit, show the patch or exact before/after text.

The human owns product behavior, architecture, domain ownership, contracts, persistence, security, observability, compatibility, and irreversible choices. Present options, recommendation, and critique; wait when any material decision is unresolved.

## Require a closed slice

`.vibecoding/current-slice.json` must contain one observable objective, explicit domains/paths/symbols, done conditions, required validation, exclusions, and approved status. Reject open scopes such as “improve”, “clean up”, or “refactor” without a bounded outcome.

Implement only that slice. Put every additional discovery in `.vibecoding/execution-backlog.json`; never expand the active scope. After Review I2B passes, review the diff, report evidence and risk, and request explicit commit authorization. Record the commit and confirm a clean worktree before selecting the next backlog item.

Continue with consecutive slices only when the next item can be converted into a closed scope and all material decisions are already clear. Otherwise request human input.

Use direct technical language. Name mechanisms, contracts, inputs, outputs, tradeoffs, failure modes, and decision owners.
