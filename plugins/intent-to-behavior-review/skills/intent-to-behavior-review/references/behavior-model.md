# Behavioral Model

Model intent before reading implementation details deeply enough to anchor correctness on the code itself.

## Evidence priority

Use the highest-authority available source and preserve conflicts:

1. approved product/domain decision or normative specification;
2. accepted user story, contract, schema, policy, or design decision;
3. user-facing documentation, UI copy, examples, and operational runbook;
4. established tests and stable sibling behavior;
5. current implementation and commit history;
6. reviewer inference.

Tests and code demonstrate implemented expectations; they do not automatically define intended behavior.

## Model template

```yaml
capability: ""
actor: ""
purpose: ""
trigger: ""
preconditions: []
inputs:
  valid: []
  invalid: []
state_before: ""
transition: ""
outputs: []
side_effects: []
state_after: ""
invariants: []
forbidden_outcomes: []
failure_signals: []
observability: []
intent_sources:
  - source: ""
    authority: normative|accepted|descriptive|implemented|inferred
    location: ""
open_questions: []
```

## Comparison matrix

For each modeled behavior, record:

| Dimension | Intended | Actual | Match | Evidence |
|---|---|---|---|---|
| Preconditions | | | yes/no/unknown | |
| Transition | | | yes/no/unknown | |
| Output | | | yes/no/unknown | |
| Side effects | | | yes/no/unknown | |
| Invariants | | | yes/no/unknown | |
| Forbidden outcomes | | | yes/no/unknown | |
| Failure visibility | | | yes/no/unknown | |

Do not collapse `unknown` into `match`.
