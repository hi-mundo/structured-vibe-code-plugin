#!/usr/bin/env python3
"""Create the support files Structured Vibe Code works with. Never overwrites existing files."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from vibecode_state import find_repo

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
GITIGNORE_BLOCK = ["# Structured Vibe Code: local state, allowances and slices stay out of the repo", ".vibecoding/"]


def head(repo: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True, capture_output=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "<no commits yet>"


def init(repo: Path) -> dict:
    """Create the support files that do not exist yet. Never overwrites. Returns the JSON report."""
    created, skipped = [], []

    def ensure(rel: str, content: str) -> None:
        path = repo / rel
        if path.exists():
            skipped.append(rel)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(rel)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ensure(".vibecoding/state.json", json.dumps({"mode": "off", "terse": True, "updated_at": now}, indent=2) + "\n")
    ensure(".vibecoding/allowances/.gitkeep", "")
    ensure(".vibecoding/current-slice.json", json.dumps({"id": None, "status": "none"}, indent=2) + "\n")
    ensure(".vibecoding/execution-backlog.json", "[]\n")
    ensure(".vibecoding/preflight.json", json.dumps({"created_at": now, "paths": []}, indent=2) + "\n")
    ensure(".decisions.jsonl", "")
    template = (PLUGIN_ROOT / "templates" / "STRUCTURE.md").read_text(encoding="utf-8")
    ensure("STRUCTURE.md", template.replace("<commit>", head(repo)).replace("<ISO-8601 timestamp>", now))

    gitignore = repo / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if ".vibecoding/" not in existing.splitlines():
        sep = "" if not existing or existing.endswith("\n") else "\n"
        gitignore.write_text(existing + sep + ("\n" if existing else "") + "\n".join(GITIGNORE_BLOCK) + "\n", encoding="utf-8")
        created.append(".gitignore (+ .vibecoding/)")
    else:
        skipped.append(".gitignore")
    return {"ok": True, "repo": str(repo), "created": created, "skipped": skipped, "next": "/vibecode understand"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    print(json.dumps(init(find_repo(args.repo)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
