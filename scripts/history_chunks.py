#!/usr/bin/env python3
"""Slice a repository's git history into chronological chunks for the understand skill.

The agent reads one chunk at a time instead of the whole log: which paths churned,
which areas appeared for the first time, who was working, what the commit subjects
say. Output is JSON. Exit 1 when the history is too short to chunk.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

from vibecode_state import find_repo

SEP = "\x1e"
MIN_COMMITS = 3


def git_log(repo: Path, max_commits: int) -> list[dict]:
    fmt = SEP.join(["%H", "%h", "%aI", "%an", "%s"])
    out = subprocess.run(
        ["git", "-C", str(repo), "log", "--reverse", "--numstat", f"--max-count={max_commits}", f"--format=@@{fmt}"],
        text=True, capture_output=True, check=True,
    ).stdout
    commits: list[dict] = []
    # str.splitlines() treats \x1e as a line break; split on newline only.
    for line in out.split("\n"):
        if line.startswith("@@"):
            full, short, when, author, subject = line[2:].split(SEP, 4)
            commits.append({"hash": full, "short": short, "date": when, "author": author, "subject": subject, "files": []})
        elif line.strip() and commits:
            parts = line.split("\t")
            if len(parts) == 3:
                added, removed, path = parts
                churn = (int(added) if added.isdigit() else 0) + (int(removed) if removed.isdigit() else 0)
                commits[-1]["files"].append((path, churn))
    return commits


def split(commits: list[dict], n: int) -> list[list[dict]]:
    n = max(1, min(n, len(commits)))
    size, rest = divmod(len(commits), n)
    chunks, start = [], 0
    for i in range(n):
        end = start + size + (1 if i < rest else 0)
        chunks.append(commits[start:end])
        start = end
    return chunks


def summarize(index: int, chunk: list[dict], seen_paths: set[str], top: int) -> dict:
    churn: Counter[str] = Counter()
    dirs: Counter[str] = Counter()
    authors: Counter[str] = Counter()
    new_paths: list[str] = []
    for commit in chunk:
        authors[commit["author"]] += 1
        for path, lines in commit["files"]:
            churn[path] += lines
            dirs[str(Path(path).parent) if "/" in path else "."] += lines
            if path not in seen_paths:
                seen_paths.add(path)
                new_paths.append(path)
    return {
        "index": index,
        "range": {"first": chunk[0]["short"], "last": chunk[-1]["short"], "diff": f"{chunk[0]['hash']}^..{chunk[-1]['hash']}"},
        "dates": {"from": chunk[0]["date"][:10], "to": chunk[-1]["date"][:10]},
        "commits": len(chunk),
        "authors": authors.most_common(),
        "top_paths": [{"path": p, "lines": c} for p, c in churn.most_common(top)],
        "top_dirs": [{"dir": d, "lines": c} for d, c in dirs.most_common(top)],
        "new_areas": sorted({str(Path(p).parent) if "/" in p else p for p in new_paths})[:top],
        "subjects": [c["subject"] for c in chunk[:8]] + (["..."] if len(chunk) > 8 else []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--chunks", type=int, default=6)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--max-commits", type=int, default=5000)
    args = parser.parse_args()
    repo = find_repo(args.repo)
    try:
        commits = git_log(repo, args.max_commits)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(json.dumps({"ok": False, "error": f"git log failed: {exc}"}))
        return 2
    if len(commits) < MIN_COMMITS:
        print(json.dumps({"ok": False, "error": f"only {len(commits)} commit(s); need at least {MIN_COMMITS} to chunk", "commits": len(commits)}))
        return 1
    seen: set[str] = set()
    chunks = [summarize(i, c, seen, args.top) for i, c in enumerate(split(commits, args.chunks), 1)]
    first_commit = commits[0]["hash"]
    print(json.dumps({
        "ok": True,
        "repo": str(repo),
        "total_commits": len(commits),
        "span": {"from": commits[0]["date"][:10], "to": commits[-1]["date"][:10]},
        "first_commit": first_commit,
        "chunks": chunks,
        "how_to_read": "for each chunk run: git diff --stat <range.diff>; then git show <hash> on the top_paths that explain the chunk's new_areas",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
