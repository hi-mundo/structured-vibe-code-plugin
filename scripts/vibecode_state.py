#!/usr/bin/env python3
"""Per-repository on/off switch for Structured Vibe Code, stored in .vibecoding/state.json."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

MODES = ("active", "off")
STATE_DIR = ".vibecoding"
STATE_FILE = "state.json"
MAX_STATE_BYTES = 4096


def find_repo(start: str | os.PathLike[str] | None = None) -> Path:
    """Walk up from start looking for .vibecoding/ or .git/. Fall back to start itself."""
    here = Path(start or os.getcwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / STATE_DIR).is_dir() or (candidate / ".git").exists():
            return candidate
    return here


def state_path(repo: Path) -> Path:
    return repo / STATE_DIR / STATE_FILE


def read_mode(repo: Path) -> str:
    """Return the stored mode. Anything missing, oversized, symlinked or malformed reads as off."""
    path = state_path(repo)
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_STATE_BYTES:
            return "off"
        mode = json.loads(path.read_text(encoding="utf-8")).get("mode")
    except (OSError, ValueError, AttributeError):
        return "off"
    return mode if mode in MODES else "off"


def write_mode(repo: Path, mode: str) -> dict:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    path = state_path(repo)
    if path.is_symlink():
        raise OSError(f"refusing to write through symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"mode": mode, "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("get", "set"))
    parser.add_argument("mode", nargs="?", choices=MODES)
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    repo = find_repo(args.repo)
    if args.action == "set":
        if not args.mode:
            parser.error("set requires a mode: active | off")
        write_mode(repo, args.mode)
    print(json.dumps({"repo": str(repo), "mode": read_mode(repo), "state_file": str(state_path(repo)), "initialized": (repo / STATE_DIR).is_dir()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
