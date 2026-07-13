#!/usr/bin/env python3
"""Validate the structural contract of an intent-to-behavior JSON report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


TOP_LEVEL = {
    "schema_version", "mode", "target", "reference", "comparison_reference",
    "intent_model", "coverage", "findings", "validation_run",
    "validation_not_run", "open_questions", "history_limitations",
}
FINDING_FIELDS = {
    "id", "title", "status", "class", "severity", "confidence", "breadth",
    "detectability", "location", "intended_behavior", "intent_evidence",
    "actual_behavior", "actual_evidence", "history", "reproduction", "impact",
    "remediation_direction", "limitations",
}
ENUMS = {
    "mode": {"deep", "scoped", "diff"},
    "status": {"hypothesis", "reproduced", "validated", "not-a-defect", "blocked"},
    "class": {"intent-gap", "function", "domain", "state", "contract", "integration", "data", "control-flow", "side-effect", "observability", "regression", "consistency"},
    "severity": {"critical", "high", "medium", "low"},
    "confidence": {"high", "medium", "low"},
    "breadth": {"isolated", "feature", "domain", "cross-domain", "system-wide"},
    "detectability": {"visible", "logged-only", "silent", "misleading-success"},
}


def missing(obj: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(required - obj.keys())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    args = parser.parse_args()
    path = Path(args.report)
    errors: list[str] = []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        return 2

    if not isinstance(data, dict):
        errors.append("report root must be an object")
    else:
        for field in missing(data, TOP_LEVEL):
            errors.append(f"missing top-level field: {field}")
        if data.get("schema_version") != 1:
            errors.append("schema_version must be 1")
        if data.get("mode") not in ENUMS["mode"]:
            errors.append(f"invalid mode: {data.get('mode')!r}")
        findings = data.get("findings")
        if not isinstance(findings, list):
            errors.append("findings must be an array")
        else:
            seen: set[str] = set()
            for index, finding in enumerate(findings):
                prefix = f"findings[{index}]"
                if not isinstance(finding, dict):
                    errors.append(f"{prefix} must be an object")
                    continue
                for field in missing(finding, FINDING_FIELDS):
                    errors.append(f"{prefix} missing field: {field}")
                finding_id = finding.get("id")
                if finding_id in seen:
                    errors.append(f"duplicate finding id: {finding_id}")
                if isinstance(finding_id, str):
                    seen.add(finding_id)
                for field in ("status", "class", "severity", "confidence", "breadth", "detectability"):
                    if finding.get(field) not in ENUMS[field]:
                        errors.append(f"{prefix} invalid {field}: {finding.get(field)!r}")
                history = finding.get("history")
                if not isinstance(history, list) or len(history) < 3:
                    errors.append(f"{prefix} history must contain at least 3 revision observations")

    print(json.dumps({"ok": not errors, "errors": errors}, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
