---
name: structured-vibecoding
description: "Run the complete structured AI-assisted development workflow: repository preflight and modeling, recovery of prior decisions, human input for unresolved technical choices, one closed implementation slice at a time, execution backlog for out-of-scope discoveries, agent-driven intent-to-behavior validation, and explicit commit authorization. Use for any feature, fix, refactor, review, test execution, repository investigation, or architecture decision."
---

# Structured VibeCoding

Begin every active turn with exactly:

*VibeCode Protector enabled*

The human owns product and technical decisions. The agent discovers evidence, exposes options and tradeoffs, critiques the selected solution, and performs approved operational work.

## Execute the state machine

1. **Preflight.** Read applicable instructions and repository documentation. Verify Git state and commands. Model users, capabilities, entrypoints, modules, ownership, contracts, dependencies, state, side effects, invariants, failure surfaces, risk, and required validation in root `STRUCTURE.md`. Register relevant paths in `.vibecoding/preflight.json`. Run `../../scripts/protector_preflight.py --repo .` when available.
2. **Understand the task.** State goal, context, constraints, done conditions, relevant domains and paths, known decisions, and pending decisions. Do not ask for facts discoverable from the repository.
3. **Recover decisions.** Inspect `.decisions.jsonl` for the affected domain, paths, and symbols. Exact repetition of a rejected or failed approach requires explicit human override.
4. **Request human input.** Stop when product behavior, architecture, domain ownership, contract, persistence, security, observability, compatibility, or another material tradeoff is unresolved. Present concrete options, recommendation, and critique.
5. **Define one closed slice.** Write `.vibecoding/current-slice.json` with one observable objective, domains, paths, symbols, done conditions, validation, exclusions, and approved status. Open-ended scopes are invalid.
6. **Backlog discoveries.** Put every additional concern in `.vibecoding/execution-backlog.json`. Never expand the active slice because related work was discovered.
7. **Implement only the slice.** Before editing a concrete block, show the proposed patch or exact before/after text. Use direct technical language and name the mechanism, contract, failure mode, risk, and decision owner.
8. **Validate with Review I2B.** Invoke `$review-i2b` before commit. It reconstructs expected behavior, uses contracts, inspects at least three relevant revisions, creates temporary direct-import or mimic probes, starts local services, makes API requests, and observes logs/state when relevant. It may run existing automated tests. It must not add or modify permanent automated tests; that work requires a separate approved slice.
9. **Commit gate.** Review the diff and report checks, missing evidence, and risk. Commit only after explicit user authorization. Record the commit, confirm a clean worktree, then select at most one clear backlog item as the next closed slice.

Continue through consecutive slices only while every next slice is closed and all material decisions are already clear. Otherwise stop for human input.

## Required artifacts

```text
STRUCTURE.md
.decisions.jsonl
.vibecoding/preflight.json
.vibecoding/current-slice.json
.vibecoding/execution-backlog.json
.vibecoding/i2b-validation.json
```

Use `$execution-slices` for the detailed authority and scope gates and `$review-i2b` for the pre-commit behavioral review.
