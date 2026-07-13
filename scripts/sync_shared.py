#!/usr/bin/env python3
"""Materialize canonical shared runtime into installable plugin packages."""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "shared" / "structured-vibecoding"
TARGETS = [ROOT / "plugins" / "review-i2b", ROOT / "plugins" / "vibecoding-protector"]

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def expected() -> dict[str, str]:
    return {str(p.relative_to(SHARED)): digest(p) for p in sorted(SHARED.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true"); args = parser.parse_args()
    manifest = expected(); drift = []
    for plugin in TARGETS:
        vendor = plugin / "vendor" / "structured-vibecoding"
        if not args.check:
            if vendor.exists(): shutil.rmtree(vendor)
            shutil.copytree(SHARED, vendor, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            (vendor / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            for name in ("decision_log.py", "protector_preflight.py"):
                shutil.copy2(SHARED / "utils" / name, plugin / "scripts" / name)
            if plugin.name == "vibecoding-protector":
                shutil.copy2(ROOT / "scripts" / "enable-protector.sh", plugin / "scripts" / "enable-protector.sh")
        current = {str(p.relative_to(vendor)): digest(p) for p in vendor.rglob("*") if p.is_file() and p.name != "MANIFEST.json"} if vendor.exists() else {}
        if current != manifest: drift.append(plugin.name)
    print(json.dumps({"ok": not drift, "shared_files": len(manifest), "drift": drift}))
    return 0 if not drift else 1

if __name__ == "__main__": raise SystemExit(main())
