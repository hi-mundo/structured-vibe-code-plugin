# Review Report Contract

Lead with findings ordered by consequence, then confidence. A review with no validated findings must still describe coverage and remaining uncertainty.

## Required finding fields

```json
{
  "id": "IBR-001",
  "title": "Short purpose-level mismatch",
  "status": "hypothesis|reproduced|validated|not-a-defect|blocked",
  "class": "intent-gap|function|domain|state|contract|integration|data|control-flow|side-effect|observability|regression|consistency",
  "severity": "critical|high|medium|low",
  "confidence": "high|medium|low",
  "breadth": "isolated|feature|domain|cross-domain|system-wide",
  "detectability": "visible|logged-only|silent|misleading-success",
  "location": {"path": "", "line": 1, "symbol": ""},
  "intended_behavior": "",
  "intent_evidence": [{"source": "", "authority": "", "location": ""}],
  "actual_behavior": "",
  "actual_evidence": [],
  "history": [{"revision": "", "observation": ""}],
  "reproduction": {"method": "static|test|direct-mimic|replicated-mimic|runtime", "command": "", "result": ""},
  "impact": "",
  "remediation_direction": "",
  "limitations": []
}
```

## Top-level report

```json
{
  "schema_version": 1,
  "mode": "deep|scoped|diff",
  "target": "",
  "reference": "",
  "comparison_reference": null,
  "intent_model": {},
  "coverage": [],
  "findings": [],
  "validation_run": [],
  "validation_not_run": [],
  "open_questions": [],
  "history_limitations": []
}
```

Run `../../scripts/validate_report.py` for structural validation. Structural validity does not establish correctness.
