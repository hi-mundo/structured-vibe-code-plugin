import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
HOOKS = ROOT / "hooks"


def run(*args, cwd=None, stdin=None):
    proc = subprocess.run([sys.executable, *map(str, args)], cwd=cwd, input=stdin, text=True, capture_output=True)
    out = json.loads(proc.stdout) if proc.stdout.strip() else None
    return proc.returncode, out


def git_repo(path: Path, commits: int = 1) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    for i in range(commits):
        (path / f"f{i}.txt").write_text(f"{i}\n")
        subprocess.run(["git", "-C", str(path), "add", "."], check=True)
        subprocess.run(["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", f"c{i}"], check=True)


class InitAndStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "r"
        git_repo(self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def test_init_creates_files_once(self):
        code, out = run(SCRIPTS / "vibecode_init.py", "--repo", self.repo)
        self.assertEqual(code, 0)
        self.assertIn("STRUCTURE.md", out["created"])
        self.assertIn(".vibecoding/", (self.repo / ".gitignore").read_text().splitlines())
        code, out = run(SCRIPTS / "vibecode_init.py", "--repo", self.repo)
        self.assertEqual(out["created"], [])
        self.assertIn("STRUCTURE.md", out["skipped"])

    def test_state_defaults_off_and_round_trips(self):
        _, out = run(SCRIPTS / "vibecode_state.py", "get", "--repo", self.repo)
        self.assertEqual(out["mode"], "off")
        _, out = run(SCRIPTS / "vibecode_state.py", "set", "active", "--repo", self.repo)
        self.assertEqual(out["mode"], "active")
        _, out = run(SCRIPTS / "vibecode_state.py", "get", "--repo", self.repo / "nested-does-not-exist-yet")
        self.assertEqual(out["mode"], "active", "find_repo walks up to the repository root")

    def test_terse_defaults_on_with_active_and_toggles(self):
        _, out = run(SCRIPTS / "vibecode_state.py", "set", "active", "--repo", self.repo)
        self.assertEqual((out["mode"], out["terse"]), ("active", True))
        _, out = run(SCRIPTS / "vibecode_state.py", "terse", "off", "--repo", self.repo)
        self.assertEqual((out["mode"], out["terse"]), ("active", False))
        _, out = run(SCRIPTS / "vibecode_state.py", "set", "off", "--repo", self.repo)
        self.assertEqual(out["terse"], False, "explicit terse choice survives a mode change")

    def test_corrupt_state_reads_as_off(self):
        (self.repo / ".vibecoding").mkdir()
        (self.repo / ".vibecoding" / "state.json").write_text("{not json")
        _, out = run(SCRIPTS / "vibecode_state.py", "get", "--repo", self.repo)
        self.assertEqual(out["mode"], "off")


class AllowanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "r"
        git_repo(self.repo)
        self.future = (date.today() + timedelta(days=10)).isoformat()

    def tearDown(self):
        self.tmp.cleanup()

    def grant(self, scope, until=None):
        return run(SCRIPTS / "allowance.py", "grant", "--repo", self.repo, "--scope", scope, "--until", until or self.future, "--note", "t")

    def test_grant_then_check_covers_children_and_globs(self):
        code, out = self.grant("src/billing/")
        self.assertEqual(code, 0)
        self.assertEqual(out["allowance"]["status"], "valid")
        code, out = run(SCRIPTS / "allowance.py", "check", "--repo", self.repo, "--path", "src/billing/invoice.py")
        self.assertEqual((code, out["covered"]), (0, True))
        code, out = run(SCRIPTS / "allowance.py", "check", "--repo", self.repo, "--path", "src/auth/login.py")
        self.assertEqual((code, out["covered"]), (1, False))
        self.grant("src/**/*.test.ts")
        code, _ = run(SCRIPTS / "allowance.py", "check", "--repo", self.repo, "--path", "src/a/b/c.test.ts")
        self.assertEqual(code, 0)

    def test_expired_allowance_exits_3(self):
        folder = self.repo / ".vibecoding" / "allowances"
        folder.mkdir(parents=True)
        (folder / "old.json").write_text(json.dumps({"id": "old", "scope": "src/", "expires_at": "2000-01-01"}))
        code, out = run(SCRIPTS / "allowance.py", "check", "--repo", self.repo, "--path", "src/x.py")
        self.assertEqual(code, 3)
        self.assertEqual(out["expired"][0]["status"], "expired")

    def test_past_until_is_rejected(self):
        code, out = self.grant("src/", until="2000-01-01")
        self.assertEqual(code, 2)
        self.assertFalse(out["ok"])

    def test_list_and_revoke(self):
        _, granted = self.grant("docs/")
        _, listed = run(SCRIPTS / "allowance.py", "list", "--repo", self.repo)
        self.assertEqual(listed["count"], 1)
        code, _ = run(SCRIPTS / "allowance.py", "revoke", "--repo", self.repo, "--id", granted["allowance"]["id"])
        self.assertEqual(code, 0)
        _, listed = run(SCRIPTS / "allowance.py", "list", "--repo", self.repo)
        self.assertEqual(listed["count"], 0)


class HistoryChunksTests(unittest.TestCase):
    def test_chunks_cover_all_commits_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            git_repo(repo, commits=7)
            code, out = run(SCRIPTS / "history_chunks.py", "--repo", repo, "--chunks", "3")
            self.assertEqual(code, 0)
            self.assertEqual(out["total_commits"], 7)
            self.assertEqual([c["commits"] for c in out["chunks"]], [3, 2, 2])
            self.assertEqual(out["chunks"][0]["new_areas"], ["f0.txt", "f1.txt", "f2.txt"])
            self.assertEqual(out["chunks"][1]["new_areas"], ["f3.txt", "f4.txt"])

    def test_too_short_history_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "r"
            git_repo(repo, commits=2)
            code, out = run(SCRIPTS / "history_chunks.py", "--repo", repo)
            self.assertEqual(code, 1)
            self.assertFalse(out["ok"])


class SyncTerseTests(unittest.TestCase):
    def test_render_and_body_round_trip_without_network(self):
        sys.path.insert(0, str(SCRIPTS))
        import sync_terse

        upstream = "---\nname: ultracave\ndescription: x\n---\n\n# ultracave\n\nRules.\n"
        body = sync_terse.strip_frontmatter(upstream)
        self.assertTrue(body.startswith("# ultracave"))
        rendered = sync_terse.render(body, "abc123", "2026-01-01")
        self.assertIn("abc123", rendered)
        self.assertIn("MIT", rendered)
        self.assertEqual(sync_terse.body_of(rendered), body.strip())

    def test_vendored_file_has_provenance_and_rules(self):
        text = (ROOT / "skills" / "vibecode" / "references" / "terse-upstream.md").read_text()
        self.assertRegex(text, r"Upstream commit: `[0-9a-f]{7,40}|unknown`")
        self.assertIn("JuliusBrussee/caveman", text)
        self.assertIn("## Rules", text)


class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "r"
        git_repo(self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def payload(self, prompt):
        return json.dumps({"cwd": str(self.repo), "prompt": prompt})

    def test_bare_command_inits_then_activates_then_reports(self):
        code, out = run(HOOKS / "prompt_submit.py", stdin=self.payload("<command-name>/vibecode</command-name><command-args></command-args>"))
        self.assertEqual(code, 0)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("initialized and active", ctx)
        self.assertTrue((self.repo / "STRUCTURE.md").exists(), "first /vibecode runs init")
        self.assertEqual(json.loads((self.repo / ".vibecoding" / "state.json").read_text())["mode"], "active")
        _, out = run(HOOKS / "prompt_submit.py", stdin=self.payload("add a login endpoint"))
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("ACTIVE", ctx)
        self.assertIn("prior-art first", ctx, "rule 4 is reminded every turn")
        _, out = run(HOOKS / "prompt_submit.py", stdin=self.payload("/vibecode:vibecode off"))
        self.assertIn("mode=off", out["hookSpecificOutput"]["additionalContext"])
        code, out = run(HOOKS / "prompt_submit.py", stdin=self.payload("hello"))
        self.assertEqual((code, out), (0, None), "inactive mode injects nothing")
        _, out = run(HOOKS / "prompt_submit.py", stdin=self.payload("/vibecode"))
        self.assertIn("mode=active", out["hookSpecificOutput"]["additionalContext"], "second bare run only re-activates")
        _, out = run(HOOKS / "prompt_submit.py", stdin=self.payload("/vibecode"))
        self.assertIn("already active", out["hookSpecificOutput"]["additionalContext"], "third bare run asks for status")
        _, out = run(HOOKS / "prompt_submit.py", stdin=self.payload("/vibecode enable"))
        self.assertNotIn("state already written", out["hookSpecificOutput"]["additionalContext"], "old names are not aliases")

    def test_session_start_injects_rules_only_when_active(self):
        proc = subprocess.run([sys.executable, str(HOOKS / "session_start.py")], input=json.dumps({"cwd": str(self.repo), "source": "startup"}), text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("`/vibecode` prepares", proc.stdout)
        run(SCRIPTS / "vibecode_state.py", "set", "active", "--repo", self.repo)
        proc = subprocess.run([sys.executable, str(HOOKS / "session_start.py")], input=json.dumps({"cwd": str(self.repo), "source": "startup"}), text=True, capture_output=True)
        self.assertIn("ACTIVE", proc.stdout)
        self.assertIn("Show before you ask", proc.stdout)
        self.assertIn("Never reinvent the wheel", proc.stdout, "rule 4 ships with the ruleset")
        self.assertIn("TERSE VOICE ON", proc.stdout)
        self.assertIn("# ultracave", proc.stdout, "vendored upstream body is injected")
        self.assertNotIn("<!-- upstream body below", proc.stdout, "provenance header is not injected")
        run(SCRIPTS / "vibecode_state.py", "terse", "off", "--repo", self.repo)
        proc = subprocess.run([sys.executable, str(HOOKS / "session_start.py")], input=json.dumps({"cwd": str(self.repo), "source": "startup"}), text=True, capture_output=True)
        self.assertNotIn("TERSE VOICE ON", proc.stdout)

    def test_terse_toggle_and_reminder(self):
        run(HOOKS / "prompt_submit.py", stdin=self.payload("/vibecode"))
        _, out = run(HOOKS / "prompt_submit.py", stdin=self.payload("anything"))
        self.assertIn("TERSE VOICE ON", out["hookSpecificOutput"]["additionalContext"])
        _, out = run(HOOKS / "prompt_submit.py", stdin=self.payload("<command-name>/vibecode</command-name><command-args>terse</command-args>"))
        self.assertIn("terse=off", out["hookSpecificOutput"]["additionalContext"])
        _, out = run(HOOKS / "prompt_submit.py", stdin=self.payload("anything"))
        self.assertNotIn("TERSE VOICE ON", out["hookSpecificOutput"]["additionalContext"])
        _, out = run(HOOKS / "prompt_submit.py", stdin=self.payload("/vibecode terse"))
        self.assertIn("terse=on", out["hookSpecificOutput"]["additionalContext"], "toggle goes back on")

    def test_hooks_survive_garbage_stdin(self):
        for script in ("prompt_submit.py", "session_start.py"):
            proc = subprocess.run([sys.executable, str(HOOKS / script)], input="not json", text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, script)


if __name__ == "__main__":
    unittest.main()
