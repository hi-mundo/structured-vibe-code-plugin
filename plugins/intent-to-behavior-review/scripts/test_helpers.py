#!/usr/bin/env python3
"""Behavioral tests for the deterministic skill helpers."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class HelperTests(unittest.TestCase):
    def make_repo(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Skill Test"], check=True)
        target = root / "feature.py"
        for value in range(3):
            target.write_text(f"VALUE = {value}\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "feature.py"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", f"revision {value}"], check=True)

    def test_preflight_collects_three_revisions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            self.make_repo(repo)
            result = run(
                str(SCRIPTS / "review_preflight.py"),
                "--repo", str(repo),
                "--mode", "scoped",
                "--scope", "feature.py",
                "--revisions", "3",
            )
            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(payload["ok"])
            self.assertEqual(len(payload["scopes"][0]["history"]), 3)

    def test_preflight_rejects_too_few_requested_revisions(self) -> None:
        result = run(
            str(SCRIPTS / "review_preflight.py"),
            "--mode", "deep",
            "--revisions", "2",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("at least 3", result.stdout)

    def test_deep_preflight_supports_repository_directory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            self.make_repo(repo)
            result = run(
                str(SCRIPTS / "review_preflight.py"),
                "--repo", str(repo),
                "--mode", "deep",
                "--revisions", "3",
            )
            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(payload["ok"])
            self.assertEqual(len(payload["scopes"][0]["history"]), 3)

    def test_mimic_requires_opt_in_and_compares_result(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            (repo / "sample.py").write_text("def double(value):\n    return value * 2\n", encoding="utf-8")
            common = (
                str(SCRIPTS / "mimic_python.py"),
                "--repo", str(repo),
                "--module", "sample",
                "--call", "double",
                "--args-json", "[2]",
                "--expected-json", "4",
            )
            refused = run(*common)
            accepted = run(*common, "--allow-execution")
            self.assertEqual(refused.returncode, 2)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertTrue(json.loads(accepted.stdout)["matched"])

    def test_report_validator_requires_three_history_observations(self) -> None:
        finding = {
            "id": "IBR-001", "title": "Mismatch", "status": "validated",
            "class": "function", "severity": "medium", "confidence": "high",
            "breadth": "feature", "detectability": "visible",
            "location": {"path": "feature.py", "line": 1, "symbol": "run"},
            "intended_behavior": "x", "intent_evidence": [], "actual_behavior": "y",
            "actual_evidence": [], "history": [{"revision": "a", "observation": "x"}],
            "reproduction": {"method": "static", "command": "", "result": ""},
            "impact": "x", "remediation_direction": "x", "limitations": [],
        }
        report = {
            "schema_version": 1, "mode": "scoped", "target": "feature.py",
            "reference": "HEAD", "comparison_reference": None, "intent_model": {},
            "coverage": [], "findings": [finding], "validation_run": [],
            "validation_not_run": [], "open_questions": [], "history_limitations": [],
        }
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            invalid = run(str(SCRIPTS / "validate_report.py"), str(path))
            self.assertEqual(invalid.returncode, 2)
            finding["history"] = [
                {"revision": "a", "observation": "x"},
                {"revision": "b", "observation": "x"},
                {"revision": "c", "observation": "x"},
            ]
            path.write_text(json.dumps(report), encoding="utf-8")
            valid = run(str(SCRIPTS / "validate_report.py"), str(path))
            self.assertEqual(valid.returncode, 0, valid.stdout)


if __name__ == "__main__":
    unittest.main()
