#!/usr/bin/env python3
"""Read-only preflight for worktree, repository model, decisions, and slice state."""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path

def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True).stdout.strip()

def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--repo", default="."); p.add_argument("--allow-dirty", action="store_true")
    a = p.parse_args(); repo = Path(a.repo).resolve(); failures = []
    try:
        dirty = bool(git(repo, "status", "--porcelain"))
        head = git(repo, "rev-parse", "HEAD")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(json.dumps({"ok": False, "failures": ["PRE002_RULES_NOT_LOADED"], "error": "not a readable git repository"})); return 2
    if dirty and not a.allow_dirty: failures.append("PRE001_DIRTY_WORKTREE")
    structure = repo / "STRUCTURE.md"
    if not structure.exists(): failures.append("MODEL001_STRUCTURE_MISSING")
    elif f"Base commit: `{head}`" not in structure.read_text(encoding="utf-8"): failures.append("MODEL002_STRUCTURE_STALE")
    decision_log = repo / ".decisions.jsonl"
    if decision_log.exists():
        for line in decision_log.read_text(encoding="utf-8").splitlines():
            try: json.loads(line)
            except json.JSONDecodeError: failures.append("DEC010_LOG_CORRUPTED"); break
    result = {"ok": not failures, "repo": str(repo), "head": head, "dirty": dirty, "failures": failures}
    print(json.dumps(result, sort_keys=True)); return 0 if not failures else 1

if __name__ == "__main__": raise SystemExit(main())
