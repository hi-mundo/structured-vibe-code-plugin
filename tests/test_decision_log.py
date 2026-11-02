import importlib.util, json, subprocess, sys, tempfile, unittest
from pathlib import Path

MODULE = Path(__file__).parents[1] / "scripts" / "decision_log.py"
spec = importlib.util.spec_from_file_location("decision_log", MODULE); d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)

class DecisionLogTests(unittest.TestCase):
    def test_fingerprint_is_order_stable(self):
        self.assertEqual(d.fingerprint("x", "y", "z", ["b", "a"]), d.fingerprint("x", "y", "z", ["a", "b"]))
    def test_compaction_keeps_at_least_200(self):
        records = [{"id": str(i), "status": "accepted", "fingerprint": str(i), "payload": "x" * 6000} for i in range(250)]
        self.assertGreaterEqual(len(d.compact(records)), 200)
    def test_compaction_preserves_active_old_record(self):
        records = [{"id": str(i), "status": "accepted", "fingerprint": str(i), "payload": "x" * 6000} for i in range(250)]
        records[0]["status"] = "proposed"
        self.assertIn("0", {item["id"] for item in d.compact(records)})
    def test_atomic_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".decisions.jsonl"; records = [{"id": "1", "status": "accepted", "fingerprint": "f"}]
            d.atomic_write(path, records); self.assertEqual(d.load(path), records)

    def test_prior_art_is_recorded_and_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / ".decisions.jsonl"
            base = [sys.executable, str(MODULE), "--file", str(log), "--domain", "retry", "--scope", "http", "--reason", "r", "--status", "accepted", "--paths-json", '["src/http.py"]']
            good = json.dumps([{"project": "tenacity", "url": "https://github.com/jd/tenacity", "license": "Apache-2.0", "used_as": "dependency"}, {"project": "K", "license": "AGPL-3.0", "used_as": "pattern"}])
            proc = subprocess.run(base + ["--decision", "adopt tenacity", "--prior-art-json", good], text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stdout)
            self.assertEqual(json.loads(proc.stdout)["record"]["prior_art"][1]["used_as"], "pattern")
            proc = subprocess.run(base + ["--decision", "copy K", "--prior-art-json", json.dumps([{"project": "K", "license": "AGPL-3.0", "used_as": "copy"}])], text=True, capture_output=True)
            self.assertEqual(proc.returncode, 11)
            self.assertEqual(json.loads(proc.stdout)["code"], "DEC011")

if __name__ == "__main__": unittest.main()
