#!/usr/bin/env python3
"""Copy only required canonical helpers into installable plugin packages."""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "shared" / "structured-vibecoding"
TARGETS = {
    "structured-vibecoding": ("decision_log.py", "protector_preflight.py"),
}

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true"); args = parser.parse_args()
    drift = []
    for plugin_name, names in TARGETS.items():
        plugin = ROOT / "plugins" / plugin_name
        if not args.check:
            for name in names:
                shutil.copy2(SHARED / "utils" / name, plugin / "scripts" / name)
        for name in names:
            source = SHARED / "utils" / name
            target = plugin / "scripts" / name
            if not target.is_file() or digest(source) != digest(target):
                drift.append(f"{plugin_name}/scripts/{name}")
    print(json.dumps({"ok": not drift, "copied_helpers": sum(map(len, TARGETS.values())), "drift": drift}))
    return 0 if not drift else 1

if __name__ == "__main__": raise SystemExit(main())
