import importlib.util, tempfile, unittest
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

if __name__ == "__main__": unittest.main()
