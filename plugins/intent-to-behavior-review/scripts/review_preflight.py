#!/usr/bin/env python3
"""Emit a deterministic JSON inventory for an intent-to-behavior review."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


MANIFESTS = (
    "pyproject.toml", "requirements.txt", "package.json", "Cargo.toml",
    "go.mod", "pom.xml", "build.gradle", "Makefile", "Taskfile.yml",
)
DOCS = ("AGENTS.md", "AGENTS.override.md", "README.md", "CONTRIBUTING.md", "PLANS.md")
TEST_MARKERS = (
    "pytest.ini", "tox.ini", "jest.config.js", "jest.config.ts",
    "vitest.config.js", "vitest.config.ts", "playwright.config.ts",
)


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(f"git {' '.join(args)}: {message}")
    return result


def existing(repo: Path, names: tuple[str, ...]) -> list[str]:
    return [name for name in names if (repo / name).exists()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--mode", choices=("deep", "scoped", "diff"), required=True)
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--reference", default="HEAD")
    parser.add_argument("--base")
    parser.add_argument("--revisions", type=int, default=3)
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    if not repo.is_dir():
        errors.append(f"repository directory does not exist: {repo}")
    if args.revisions < 3:
        errors.append("revisions must be at least 3")
    if args.mode == "scoped" and not args.scope:
        errors.append("scoped mode requires at least one --scope")
    if args.mode == "diff" and not args.base:
        errors.append("diff mode requires --base")
    if errors:
        print(json.dumps({"ok": False, "errors": errors, "warnings": warnings}, indent=2))
        return 2

    try:
        root = Path(run_git(repo, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
        reference = run_git(root, "rev-parse", "--verify", f"{args.reference}^{{commit}}").stdout.strip()
        base = None
        if args.base:
            base = run_git(root, "rev-parse", "--verify", f"{args.base}^{{commit}}").stdout.strip()

        scopes: list[dict[str, object]] = []
        requested_scopes = args.scope or ["."]
        for raw_scope in requested_scopes:
            candidate = (root / raw_scope).resolve()
            try:
                relative = candidate.relative_to(root)
            except ValueError:
                errors.append(f"scope escapes repository: {raw_scope}")
                continue
            pathspec = "." if str(relative) == "." else relative.as_posix()
            log_args = ["log"]
            if candidate.is_file():
                log_args.append("--follow")
            log_args.extend(
                [
                    f"--max-count={args.revisions}",
                    "--format=%H%x09%aI%x09%s",
                    args.reference,
                    "--",
                    pathspec,
                ]
            )
            log = run_git(root, *log_args, check=False)
            if log.returncode != 0:
                errors.append(
                    f"could not inspect history for {pathspec!r}: "
                    f"{log.stderr.strip() or log.stdout.strip()}"
                )
            commits = [line.split("\t", 2) for line in log.stdout.splitlines() if line.strip()]
            if len(commits) < args.revisions:
                warnings.append(
                    f"scope {pathspec!r} has {len(commits)} visible revision(s); {args.revisions} required"
                )
            scopes.append(
                {
                    "path": pathspec,
                    "exists_at_worktree": candidate.exists(),
                    "history": [
                        {"revision": item[0], "date": item[1], "subject": item[2]}
                        for item in commits
                    ],
                }
            )

        status_lines = run_git(root, "status", "--porcelain=v1").stdout.splitlines()
        if status_lines:
            warnings.append("working tree is dirty; inspect overlap before review or probe creation")

        result = {
            "ok": not errors,
            "repository": str(root),
            "mode": args.mode,
            "reference": reference,
            "base": base,
            "requested_revisions": args.revisions,
            "working_tree": {"clean": not status_lines, "changes": status_lines},
            "discovery": {
                "documentation": existing(root, DOCS),
                "manifests": existing(root, MANIFESTS),
                "test_configuration": existing(root, TEST_MARKERS),
            },
            "scopes": scopes,
            "warnings": warnings,
            "errors": errors,
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["ok"] else 2
    except (OSError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)], "warnings": warnings}, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
