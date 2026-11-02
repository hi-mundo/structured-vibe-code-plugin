#!/usr/bin/env python3
"""Per-repository switches for Structured Vibe Code, stored in .vibecoding/state.json.

mode:  active | off      the loop and its rules
terse: true | false      the compressed voice (on by default when mode becomes active)
"""
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


def read_state(repo: Path) -> dict:
    """Return {mode, terse}. Anything missing, oversized, symlinked or malformed reads as off."""
    path = state_path(repo)
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_STATE_BYTES:
            return {"mode": "off", "terse": False}
        data = json.loads(path.read_text(encoding="utf-8"))
        mode = data.get("mode")
        terse = data.get("terse")
    except (OSError, ValueError, AttributeError):
        return {"mode": "off", "terse": False}
    mode = mode if mode in MODES else "off"
    return {"mode": mode, "terse": bool(terse) if isinstance(terse, bool) else mode == "active"}


def read_mode(repo: Path) -> str:
    return read_state(repo)["mode"]


def write_state(repo: Path, mode: str | None = None, terse: bool | None = None) -> dict:
    """Update one or both switches. Turning mode active with no stored terse value turns terse on."""
    if mode is not None and mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    path = state_path(repo)
    if path.is_symlink():
        raise OSError(f"refusing to write through symlink: {path}")
    current = read_state(repo)
    stored_terse = path.is_file() and "terse" in (json.loads(path.read_text(encoding="utf-8")) if path.stat().st_size <= MAX_STATE_BYTES else {})
    payload = {"mode": mode if mode is not None else current["mode"], "terse": current["terse"] if stored_terse else True}
    if terse is not None:
        payload["terse"] = terse
    payload["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def write_mode(repo: Path, mode: str) -> dict:
    return write_state(repo, mode=mode)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("get", "set", "terse"))
    parser.add_argument("value", nargs="?", help="set: active | off; terse: on | off")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    repo = find_repo(args.repo)
    if args.action == "set":
        if args.value not in MODES:
            parser.error("set requires a mode: active | off")
        write_state(repo, mode=args.value)
    elif args.action == "terse":
        if args.value not in ("on", "off"):
            parser.error("terse requires on | off")
        write_state(repo, terse=args.value == "on")
    state = read_state(repo)
    print(json.dumps({"repo": str(repo), "mode": state["mode"], "terse": state["terse"], "state_file": str(state_path(repo)), "initialized": (repo / STATE_DIR).is_dir()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
