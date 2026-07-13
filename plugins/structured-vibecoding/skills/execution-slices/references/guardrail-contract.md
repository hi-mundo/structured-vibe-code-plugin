# Guardrail contract

- `PRE001_DIRTY_WORKTREE`: unexplained changes block a new slice.
- `PRE002_RULES_NOT_LOADED`: repository or instruction context is unavailable.
- `MODEL001_STRUCTURE_MISSING`, `MODEL002_STRUCTURE_STALE`: repository model is absent or does not match HEAD.
- `DEC001_PENDING_DECISIONS`, `DEC002_CRITIQUE_UNRESOLVED`: human authority gate is incomplete.
- `DEC003_REPEATED_REJECTED_APPROACH`, `DEC004_REPEATED_FAILED_APPROACH`, `DEC009_HUMAN_OVERRIDE_REQUIRED`, `DEC010_LOG_CORRUPTED`: decision-memory gate.
- `SCOPE001_NO_ACTIVE_SLICE`, `SCOPE002_MULTIPLE_SCOPES`: slice contract is invalid.
- `VAL001_REQUIRED_CHECK_MISSING`, `VAL002_FAILED_CHECK`: evidence is incomplete or failing.
- `COMMIT001_AUTH_REQUIRED`, `COMMIT002_SLICE_UNCOMMITTED`: checkpoint is incomplete.
- `DRIFT001_CONTEXT_DRIFT`: implementation departed from the approved model or slice.

Codes are deterministic observations. They do not authorize the agent to resolve the underlying technical decision.
