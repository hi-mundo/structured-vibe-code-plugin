#!/usr/bin/env python3
"""Invoke a Python callable in a subprocess and compare JSON results."""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def resolve_dotted(value: Any, dotted: str) -> Any:
    current = value
    for part in dotted.split("."):
        current = getattr(current, part)
    return current


def worker(payload: dict[str, Any]) -> int:
    repo = Path(payload["repo"]).resolve()
    sys.path.insert(0, str(repo))
    captured_out = io.StringIO()
    captured_err = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
            module = importlib.import_module(payload["module"])
            callable_value = resolve_dotted(module, payload["call"])
            result = callable_value(*payload["args"], **payload["kwargs"])
        response = {
            "ok": True,
            "result": result,
            "stdout": captured_out.getvalue(),
            "stderr": captured_err.getvalue(),
        }
        print(json.dumps(response, sort_keys=True))
        return 0
    except Exception as exc:  # Preserve the named runtime failure in structured output.
        response = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "stdout": captured_out.getvalue(),
            "stderr": captured_err.getvalue(),
        }
        print(json.dumps(response, sort_keys=True))
        return 1


def parse_json(label: str, raw: str, expected_type: type | None = None) -> Any:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {exc}") from exc
    if expected_type is not None and not isinstance(value, expected_type):
        raise ValueError(f"{label} must decode to {expected_type.__name__}")
    return value


def controller(args: argparse.Namespace) -> int:
    if not args.allow_execution:
        print(json.dumps({"ok": False, "error": "refusing to import repository code without --allow-execution"}, indent=2))
        return 2

    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        print(json.dumps({"ok": False, "error": f"repository directory does not exist: {repo}"}, indent=2))
        return 2

    try:
        call_args = parse_json("--args-json", args.args_json, list)
        call_kwargs = parse_json("--kwargs-json", args.kwargs_json, dict)
        expected = parse_json("--expected-json", args.expected_json)
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2

    payload = {
        "repo": str(repo),
        "module": args.module,
        "call": args.call,
        "args": call_args,
        "kwargs": call_kwargs,
    }
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", json.dumps(payload)]
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(json.dumps({"ok": False, "matched": False, "error": f"probe timed out after {args.timeout}s"}, indent=2))
        return 1

    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError:
        print(
            json.dumps(
                {
                    "ok": False,
                    "matched": False,
                    "error": "worker did not emit valid JSON",
                    "worker_stdout": completed.stdout,
                    "worker_stderr": completed.stderr,
                },
                indent=2,
            )
        )
        return 1

    matched = bool(response.get("ok")) and response.get("result") == expected
    report = {
        "ok": bool(response.get("ok")),
        "matched": matched,
        "module": args.module,
        "call": args.call,
        "expected": expected,
        **response,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if matched else 1


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "--worker":
        return worker(json.loads(sys.argv[2]))

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--module", required=True)
    parser.add_argument("--call", required=True)
    parser.add_argument("--args-json", default="[]")
    parser.add_argument("--kwargs-json", default="{}")
    parser.add_argument("--expected-json", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--allow-execution", action="store_true")
    return controller(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
