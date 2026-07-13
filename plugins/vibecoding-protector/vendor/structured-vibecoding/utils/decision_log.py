#!/usr/bin/env python3
"""Deterministic JSONL decision memory with bounded, atomic retention."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MIN_RECORDS = 200
SOFT_MAX = 1_048_576
TARGET = 921_600
BLOCKING = {"rejected": "DEC003", "failed": "DEC004"}


def fingerprint(domain: str, scope: str, decision: str, paths: list[str]) -> str:
    value = {"decision": decision.strip().lower(), "domain": domain.strip().lower(), "paths": sorted(paths), "scope": scope.strip().lower()}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"DEC010 line {line_no}: {exc.msg}") from exc
        if not isinstance(item, dict) or not item.get("fingerprint"):
            raise ValueError(f"DEC010 line {line_no}: invalid record")
        records.append(item)
    return records


def compact(records: list[dict]) -> list[dict]:
    encoded = lambda xs: sum(len(json.dumps(x, sort_keys=True).encode()) + 1 for x in xs)
    if encoded(records) <= SOFT_MAX:
        return records
    terminal = {"accepted", "rejected", "failed", "superseded"}
    protected_ids = {x.get("id") for x in records[-MIN_RECORDS:]}
    protected_ids.update(x.get("id") for x in records if x.get("status") not in terminal)
    result = list(records)
    cursor = 0
    while len(result) > MIN_RECORDS and encoded(result) > TARGET and cursor < len(result):
        if result[cursor].get("id") not in protected_ids:
            result.pop(cursor)
        else:
            cursor += 1
    return result


def atomic_write(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush(); os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=".decisions.jsonl")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--domain"); parser.add_argument("--scope"); parser.add_argument("--decision")
    parser.add_argument("--reason"); parser.add_argument("--status"); parser.add_argument("--paths-json", default="[]")
    parser.add_argument("--override", action="store_true")
    args = parser.parse_args(); path = Path(args.file)
    try: records = load(path)
    except ValueError as exc:
        print(json.dumps({"ok": False, "code": "DEC010", "error": str(exc)})); return 10
    if args.check:
        print(json.dumps({"ok": True, "records": len(records), "bytes": path.stat().st_size if path.exists() else 0})); return 0
    missing = [name for name in ("domain", "scope", "decision", "reason", "status") if not getattr(args, name)]
    if missing:
        print(json.dumps({"ok": False, "code": "DEC006", "missing": missing})); return 6
    paths = json.loads(args.paths_json)
    if not isinstance(paths, list) or not paths:
        print(json.dumps({"ok": False, "code": "DEC007"})); return 7
    fp = fingerprint(args.domain, args.scope, args.decision, paths)
    prior = next((x for x in reversed(records) if x.get("fingerprint") == fp and x.get("status") in BLOCKING), None)
    if prior and not args.override:
        code = BLOCKING[prior["status"]]
        print(json.dumps({"ok": False, "code": code, "requires": "DEC009_HUMAN_OVERRIDE_REQUIRED", "prior": prior.get("id")})); return 9
    now = datetime.now(timezone.utc).isoformat()
    record = {"id": hashlib.sha256(f"{now}:{fp}".encode()).hexdigest()[:16], "timestamp": now, "domain": args.domain, "scope": args.scope, "decision": args.decision, "reason": args.reason, "status": args.status, "paths": paths, "fingerprint": fp}
    records.append(record); atomic_write(path, compact(records))
    print(json.dumps({"ok": True, "record": record})); return 0


if __name__ == "__main__": raise SystemExit(main())
