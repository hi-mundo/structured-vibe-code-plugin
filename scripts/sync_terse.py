#!/usr/bin/env python3
"""Vendor the ultracave ruleset from JuliusBrussee/caveman into this plugin.

Fetches skills/ultracave/SKILL.md from the upstream default branch, strips its
frontmatter, prefixes provenance (commit, date, license) and writes
skills/vibecode/references/terse-upstream.md. Standard library only.

Exit codes: 0 up to date or written, 1 drift found with --check, 2 fetch failed.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UPSTREAM_REPO = "JuliusBrussee/caveman"
UPSTREAM_PATH = "skills/ultracave/SKILL.md"
UPSTREAM_BRANCH = "main"
TARGET = Path(__file__).resolve().parents[1] / "skills" / "vibecode" / "references" / "terse-upstream.md"
HEADER_END = "<!-- upstream body below; edits here are overwritten by scripts/sync_terse.py -->"
EXIT_OK, EXIT_DRIFT, EXIT_FETCH = 0, 1, 2


def fetch(url: str, timeout: int = 20) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "structured-vibe-code-plugin sync_terse"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed https host
        return response.read()


def upstream_sha(branch: str) -> str:
    try:
        payload = json.loads(fetch(f"https://api.github.com/repos/{UPSTREAM_REPO}/commits/{branch}"))
        return payload.get("sha", "unknown")
    except (urllib.error.URLError, ValueError, OSError):
        return "unknown"


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    return text.strip() + "\n"


def render(body: str, sha: str, synced: str) -> str:
    header = "\n".join([
        "# Terse voice: upstream ruleset",
        "",
        f"Source: https://github.com/{UPSTREAM_REPO}/blob/{UPSTREAM_BRANCH}/{UPSTREAM_PATH}",
        f"Upstream commit: `{sha}`  Synced: {synced}",
        "License: MIT, Copyright (c) 2026 Julius Brussee. Vendored unchanged except for this header and the removed frontmatter.",
        "",
        HEADER_END,
        "",
    ])
    return header + body


def body_of(rendered: str) -> str:
    """The part of a vendored file that must match upstream (everything after the header marker)."""
    return rendered.split(HEADER_END, 1)[1].strip() if HEADER_END in rendered else rendered.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="exit 1 when the vendored body differs from upstream; write nothing")
    parser.add_argument("--branch", default=UPSTREAM_BRANCH)
    parser.add_argument("--target", default=str(TARGET))
    args = parser.parse_args()
    target = Path(args.target)
    try:
        upstream = fetch(f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{args.branch}/{UPSTREAM_PATH}").decode("utf-8")
    except (urllib.error.URLError, OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"ok": False, "error": f"fetch failed: {exc}"}))
        return EXIT_FETCH
    body = strip_frontmatter(upstream)
    current = target.read_text(encoding="utf-8") if target.exists() else ""
    changed = body_of(current) != body.strip()
    if args.check:
        print(json.dumps({"ok": not changed, "changed": changed, "target": str(target)}))
        return EXIT_DRIFT if changed else EXIT_OK
    if changed:
        sha = upstream_sha(args.branch)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(body, sha, datetime.now(timezone.utc).date().isoformat()), encoding="utf-8")
    print(json.dumps({"ok": True, "changed": changed, "target": str(target)}))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
