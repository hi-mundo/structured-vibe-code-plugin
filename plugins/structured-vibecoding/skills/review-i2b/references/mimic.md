# Mimic Probes

Mimic is a narrow evidence tactic for purpose-level behavior. It is not a substitute for end-to-end behavior or product intent.

## Evidence strength

1. direct import of the real callable with controlled dependencies;
2. real callable through an existing unit/component harness;
3. verbatim replicated excerpt with source revision and exact lines;
4. conceptual reimplementation.

Only levels 1–3 are mimic evidence. Treat level 4 as a hypothesis generator.

## Required probe record

```yaml
probe_type: direct|replicated
source_revision: ""
source_location: ""
inputs: {}
preconditions: []
expected_purpose: ""
expected_state: ""
forbidden_outcomes: []
actual_result: ""
actual_state: ""
stdout: ""
stderr: ""
limitations: []
```

## Safety

- Review imports before execution; importing application modules may run startup code.
- Use temporary data and replace explicit external boundaries.
- Never point mimic probes at production, real accounts, billing, or destructive services.
- Preserve errors and timeouts as failures; never fabricate a passing result.
- Delete temporary probes after the review unless the user approves converting one into a regression test.

## Python helper

`../../scripts/mimic_python.py` loads a module from a repository, resolves a dotted callable, invokes it in a subprocess, captures output, and compares its JSON-serializable return value with an expected JSON value. It requires `--allow-execution` so repository code is never imported accidentally.

The helper does not mock dependencies. Build a task-specific wrapper when dependency isolation is required, and show that wrapper in the evidence.
