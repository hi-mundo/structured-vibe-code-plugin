# Defect Taxonomy

Classify the primary mismatch. Add secondary tags when needed.

| Class | Meaning | Typical evidence |
|---|---|---|
| intent-gap | Intended behavior is missing, conflicting, or too ambiguous to judge | contradictory docs, undecided product rule |
| function | Wrong or missing capability, algorithm, condition, or calculation | purpose-level input/output mismatch |
| domain | Business invariant or domain rule is violated | invalid state accepted, forbidden transition |
| state | Incorrect lifecycle, transition, ordering, idempotency, or persistence | before/after state differs from model |
| contract | Boundary shape, semantics, serialization, or compatibility is wrong | schema/provider/consumer mismatch |
| integration | Modules are individually plausible but compose incorrectly | handoff, units, timing, identity mismatch |
| data | Wrong selection, transformation, default, precision, or ownership | trace from source to incorrect result |
| control-flow | Branch, guard, early return, retry, or fallback changes the purpose | reachable path analysis or mimic probe |
| side-effect | Missing, duplicate, premature, or unintended external/internal effect | state/log/call evidence |
| observability | A meaningful failure or deviation is invisible or falsely successful | missing signal, swallowed error, false 2xx |
| regression | Previously satisfied behavior no longer holds | three-version history plus reproduction |
| consistency | Equivalent paths or sibling features disagree without a domain reason | comparison across implementations |

## Status

- `hypothesis`: plausible mismatch with incomplete evidence.
- `reproduced`: deterministic observation demonstrates the mismatch.
- `validated`: intent authority and actual behavior both establish a defect.
- `not-a-defect`: behavior is consistent with authoritative intent.
- `blocked`: evidence needed for a decision is unavailable.

## Calibration

Report separately:

- severity: consequence if the defect is real;
- confidence: strength of the evidence;
- breadth: isolated, feature, domain, cross-domain, or system-wide;
- detectability: visible, logged-only, silent, or misleading success.

Do not inflate severity because a path looks unusual. Do not inflate confidence because a test failed without first confirming the expected behavior.
