#!/usr/bin/env python3
"""Scoped, time-boxed permissions for autonomous implementation.

An allowance is one JSON file under .vibecoding/allowances/. It names a path or glob
the developer has authorized the agent to implement without asking per edit, and the
date that authorization expires. Without a valid allowance covering a path, the agent
must stop and ask before touching it as a whole.

Exit codes: 0 covered/ok, 1 not covered, 2 usage or IO error, 3 covered only by an
expired allowance.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from vibecode_state import find_repo

ALLOWANCES_DIR = Path(".vibecoding") / "allowances"
EXIT_OK, EXIT_NOT_COVERED, EXIT_ERROR, EXIT_EXPIRED = 0, 1, 2, 3


def today() -> date:
    return datetime.now(timezone.utc).date()


def git_user(repo: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(repo), "config", "user.name"], text=True, capture_output=True, check=True).stdout.strip() or "unknown"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def load_all(repo: Path) -> list[dict]:
    folder = repo / ALLOWANCES_DIR
    if not folder.is_dir():
        return []
    items = []
    for path in sorted(folder.glob("*.json")):
        if path.is_symlink():
            continue
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(item, dict) and item.get("scope") and item.get("expires_at"):
            item["_file"] = path.name
            items.append(item)
    return items


def describe(item: dict) -> dict:
    expires = date.fromisoformat(item["expires_at"])
    days_left = (expires - today()).days
    return {
        "id": item.get("id"),
        "scope": item["scope"],
        "granted_at": item.get("granted_at"),
        "expires_at": item["expires_at"],
        "days_left": days_left,
        "status": "valid" if days_left >= 0 else "expired",
        "note": item.get("note", ""),
        "granted_by": item.get("granted_by", "unknown"),
    }


def covers(scope: str, target: str) -> bool:
    """A scope covers a target when it matches as a glob or is a parent path of it."""
    scope_n, target_n = scope.strip("/").replace("\\", "/"), target.strip("/").replace("\\", "/")
    if fnmatch.fnmatch(target_n, scope_n) or fnmatch.fnmatch(target_n, scope_n.rstrip("/") + "/*"):
        return True
    return target_n == scope_n or target_n.startswith(scope_n + "/")


def cmd_grant(repo: Path, args: argparse.Namespace) -> int:
    try:
        expires = date.fromisoformat(args.until)
    except ValueError:
        print(json.dumps({"ok": False, "error": f"--until must be YYYY-MM-DD, got {args.until!r}"}))
        return EXIT_ERROR
    if expires < today():
        print(json.dumps({"ok": False, "error": f"--until {args.until} is already in the past"}))
        return EXIT_ERROR
    folder = repo / ALLOWANCES_DIR
    folder.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", args.scope.lower()).strip("-")[:40] or "scope"
    item = {
        "id": f"{today().isoformat()}-{slug}-{uuid.uuid4().hex[:6]}",
        "scope": args.scope,
        "granted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "expires_at": expires.isoformat(),
        "granted_by": git_user(repo),
        "note": args.note or "",
    }
    (folder / f"{item['id']}.json").write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "allowance": describe(item), "file": str(folder / f"{item['id']}.json")}, sort_keys=True))
    return EXIT_OK


def cmd_check(repo: Path, args: argparse.Namespace) -> int:
    target = str(Path(args.path))
    try:
        target = str(Path(args.path).resolve().relative_to(repo))
    except ValueError:
        pass
    matches = [describe(i) for i in load_all(repo) if covers(i["scope"], target)]
    valid = [m for m in matches if m["status"] == "valid"]
    result = {"path": target, "covered": bool(valid), "valid": valid, "expired": [m for m in matches if m["status"] == "expired"]}
    print(json.dumps(result, sort_keys=True))
    if valid:
        return EXIT_OK
    return EXIT_EXPIRED if matches else EXIT_NOT_COVERED


def cmd_list(repo: Path, _: argparse.Namespace) -> int:
    items = [describe(i) for i in load_all(repo)]
    print(json.dumps({"repo": str(repo), "count": len(items), "valid": sum(i["status"] == "valid" for i in items), "allowances": items}, sort_keys=True))
    return EXIT_OK


def cmd_revoke(repo: Path, args: argparse.Namespace) -> int:
    for item in load_all(repo):
        if item.get("id") == args.id:
            (repo / ALLOWANCES_DIR / item["_file"]).unlink()
            print(json.dumps({"ok": True, "revoked": args.id}))
            return EXIT_OK
    print(json.dumps({"ok": False, "error": f"no allowance with id {args.id!r}"}))
    return EXIT_NOT_COVERED


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    g = sub.add_parser("grant", help="record a new allowance", parents=[common])
    g.add_argument("--scope", required=True, help="path or glob, e.g. src/billing/ or src/**/*.test.ts")
    g.add_argument("--until", required=True, help="expiry date, YYYY-MM-DD")
    g.add_argument("--note", default="", help="why this was granted")
    c = sub.add_parser("check", help="is this path covered by a valid allowance?", parents=[common])
    c.add_argument("--path", required=True)
    sub.add_parser("list", help="list allowances with status", parents=[common])
    r = sub.add_parser("revoke", help="delete an allowance by id", parents=[common])
    r.add_argument("--id", required=True)
    args = parser.parse_args()
    repo = find_repo(args.repo)
    return {"grant": cmd_grant, "check": cmd_check, "list": cmd_list, "revoke": cmd_revoke}[args.command](repo, args)


if __name__ == "__main__":
    raise SystemExit(main())
