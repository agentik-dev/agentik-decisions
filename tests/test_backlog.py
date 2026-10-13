"""d23 section 7: `agentik decisions backlog`, each repo's NICE_TO_HAVE.md placed against
its HANDOFF.md build order. It writes nothing and never renders through respeak.

The fixtures under tests/fixtures/backlog/ are trimmed from the real files: relay
(a level in a `##` heading), session (the lead's four forms), intro (`Each line is
S<n>.`, `Each line below is S<n>.` and owner steps that are no build order),
numbered (`N. ` steps, `done` and `DECIDED`), table (rows whose first cell is an integer), both (a table, then `N. `
items on the same steps: the first shape wins) and marker (the marker line beats a
heading prefix).
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import decisions
from decisions import doctor, speak
from tests.hermetic import REPO, Hermetic

FIXTURES = os.path.join(REPO, "tests", "fixtures", "backlog")
NICE = "NICE_TO_HAVE.md"
# respeak's include file: under plugin/ so an install copies it, beside commands/ and
# skills/ so no loader reads it as either.
INCLUDE = "plugin/respeak-include.md"


def fixture(name):
    return os.path.join(FIXTURES, name)


def line_of(name, needle, file=NICE):
    """The 1-based line of `needle` in the fixture `name`'s `file`."""
    with open(os.path.join(fixture(name), file), encoding="utf-8") as handle:
        for n, line in enumerate(handle, 1):
            if needle in line:
                return n
    raise AssertionError("%r not in %s/%s" % (needle, name, file))


def snapshot(root):
    """{relative path: (size, mtime_ns, bytes)} of every file under `root`."""
    found = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(dirpath, name)
            with open(path, "rb") as handle:
                body = handle.read()
            st = os.stat(path)
            found[os.path.relpath(path, root)] = (st.st_size, st.st_mtime_ns, body)
    return found


class Backlog(Hermetic):

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="decisions-backlog-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["backlog"] + list(argv), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def view(self, *repos):
        code, out, err = self.run_cli(*(list(repos) + ["--json"]))
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def repo(self, name):
        data = self.view(fixture(name))
        self.assertEqual(len(data["repos"]), 1)
        return data["repos"][0]

    def item(self, name, needle):
        line = line_of(name, needle)
        found = [i for i in self.repo(name)["items"] if i["line"] == line]
        self.assertEqual(len(found), 1, "no item at %s:%d" % (name, line))
        return found[0]

    def level(self, name, needle):
        return self.item(name, needle)["level"]

    def text(self, name):
        code, out, err = self.run_cli(fixture(name))
        self.assertEqual(code, 0, err)
        return out.splitlines()

    def empty_dir(self, name):
        path = os.path.join(self.tmp, name)
        os.makedirs(path)
        return path

    # section 2: parsing NICE_TO_HAVE.md

    def test_column_zero_bullets_only(self):
        lines = [i["line"] for i in self.repo("relay")["items"]]
        want = [line_of("relay", n) for n in (
            "- Ruling 9's first edge", "- A paused row", "- If the night is draining",
            "- Under a bug", "- The `fresh` gate", "- A plain `agentik relay plan`",
            "- `plugin/agents/attendant.md`")]
        self.assertEqual(sorted(lines), want)
        for prose in ("A continuation line", "A nested bullet", "a fenced line",
                      "An S1 in prose"):
            self.assertNotIn(line_of("relay", prose), lines, prose)
        # the nested bullet's S1 is the item's text, never its level
        self.assertIsNone(self.level("relay", "- Ruling 9's first edge"))
        self.assertEqual(self.item("relay", "- Ruling 9's first edge")["title"],
                         "Ruling 9's first edge")

    def test_lead_level_wins(self):
        self.assertEqual(self.level("session", "- S4: a lead level beats"), "S4")
        self.assertEqual(self.item("session", "- S4: a lead level beats")["level_from"], "lead")
        got = self.item("intro", "S2, the read date")
        self.assertEqual((got["level"], got["level_from"]), ("S2", "lead"))

    def test_lead_forms_only(self):
        for needle, level in (("- S4: the plugin version", "S4"),
                              ("- S4, unconfirmed source", "S4"),
                              ("- S21 (2026-10-10), S4:", "S4"),
                              ("- **Rename it (S4).**", "S4"),
                              ("- **Lift it, S2**", "S2"),
                              ("- N4; S3:", "S3"),
                              ("- S3, S1:", "S1"),
                              ("- S18, 2026-10-04", None),
                              ("- S1 and S2 of the review", None)):
            with self.subTest(needle=needle):
                self.assertEqual(self.level("session", needle), level)
        self.assertEqual(self.item("session", "- S4: the plugin version")["title"],
                         "the plugin version must move with any change under plugin/")
        self.assertEqual(self.item("session", "- **Rename it (S4).**")["title"], "Rename it (S4)")
        row = "- Row rtfix4 takes findings S1 and S2"
        self.assertIsNone(self.level("table", row))
        printed = [l for l in self.text("table") if "%s:%d " % (NICE, line_of("table", row)) in l]
        self.assertEqual(len(printed), 1)
        self.assertRegex(printed[0], r"^\d+ S4\?  ")
        # example-app's line 50: the lead runs to the first `. `
        self.assertEqual(self.item("table", "- Refuse a slash")["title"],
                         "Refuse a slash in a workflow kind")

    def test_intro_sentence_level(self):
        got = self.item("intro", "Entry 25 against the graded exit")
        self.assertEqual((got["level"], got["level_from"]), ("S4", "sentence"))
        got = self.item("intro", "The sentence beats the heading")
        self.assertEqual((got["level"], got["level_from"]), ("S4", "sentence"))
        self.assertIsNone(self.level("intro", "A parked item before the sentence"))
        self.assertIsNone(self.level("intro", "A parked item after the sentence"))
        # N2: the second sentence form, `Each line below is S<n>.`
        got = self.item("intro", "A reading with a time-zone offset")
        self.assertEqual((got["level"], got["level_from"]), ("S3", "sentence"))

    def test_heading_level_covers_items(self):
        for needle in ("- If the night is draining", "- Under a bug", "- The `fresh` gate",
                       "- A plain `agentik relay plan`"):
            with self.subTest(needle=needle):
                got = self.item("relay", needle)
                self.assertEqual((got["level"], got["level_from"]), ("S4", "heading"))
        self.assertIsNone(self.level("relay", "- `plugin/agents/attendant.md`"))
        got = self.item("session", "The heading's level covers this one")
        self.assertEqual((got["level"], got["level_from"]), ("S3", "heading"))

    def test_token_elsewhere_is_text(self):
        self.assertIsNone(self.level("intro", "The backup drill runs on import"))
        self.assertIsNone(self.level("session", "- N2: a heading naming S21"))
        self.assertIsNone(self.level("session", "- S18, 2026-10-04"))
        self.assertIsNone(self.level("table", "- Refuse a slash"))

    def test_unlevelled_is_s4_marked(self):
        got = self.item("table", "- Row rtfix4 takes findings")
        self.assertEqual((got["level"], got["placed_as"], got["level_from"]), (None, "S4", None))
        lines = self.text("table")
        unlevelled = [l for l in lines if re.match(r"^\d+ S4\?  ", l)]
        self.assertEqual(len(unlevelled), 5)
        self.assertEqual(lines[-1], "5 of 7 items carry no level (placed as S4)")
        self.assertEqual(self.text("relay")[-1], "3 of 7 items carry no level (placed as S4)")

    # section 3: reading the build order

    def test_marker_beats_prefix(self):
        got = self.repo("marker")
        self.assertEqual(got["order"], {"line": line_of("marker", "## The plan", "HANDOFF.md"),
                                        "heading": "The plan", "open": 1})
        self.assertEqual([(s["n"], s["title"], s["done"]) for s in got["steps"]],
                         [(1, "First real step", False), (2, "Second real step", True)])

    def test_owner_steps_are_not_order(self):
        got = self.repo("intro")
        self.assertIsNone(got["order"])
        self.assertEqual(got["steps"], [])
        self.assertEqual(self.text("intro")[0],
                         "== intro  build order: none (no build-order section in HANDOFF.md)")

    def test_numbered_steps_done(self):
        got = self.repo("numbered")
        self.assertEqual([(s["n"], s["done"]) for s in got["steps"]],
                         [(1, False), (2, False), (3, True), (4, False), (5, True), (6, False),
                          (7, True)])
        self.assertEqual(got["steps"][5]["title"], "Known gap: `freeze` never discovers new files")
        self.assertEqual(got["steps"][0]["line"], line_of("numbered", "1. **OWNER", "HANDOFF.md"))
        lines = self.text("numbered")
        self.assertEqual(lines[0], '== numbered  build order: HANDOFF.md:%d "Open work, highest '
                         'value first", 4 open steps'
                         % line_of("numbered", "## Open work", "HANDOFF.md"))
        steps = [l.split()[1] for l in lines if l.startswith("step ")]
        self.assertEqual(steps, ["1", "2", "4", "6"])
        self.assertIn("step 4  HANDOFF.md:%d  Install the LaunchAgent from the repo copy"
                      % line_of("numbered", "4. **Install", "HANDOFF.md"), lines)

    def test_table_steps_done(self):
        got = self.repo("table")
        self.assertEqual([(s["n"], s["done"]) for s in got["steps"]],
                         [(1, True), (2, True), (7, False), (8, False), (10, False), (11, True)])
        self.assertEqual(got["steps"][3]["title"], "Row RT3: the retention mint")
        self.assertEqual(got["steps"][5]["title"], "Row with an escaped \\| pipe")
        self.assertEqual(got["order"]["heading"], "Next work, in order")
        self.assertEqual(got["order"]["open"], 3)

    def test_first_step_shape_wins(self):
        # N1: example-app's section holds the rank table and numbered items on the same steps
        got = self.repo("both")
        self.assertEqual([(s["n"], s["line"], s["done"]) for s in got["steps"]],
                         [(1, line_of("both", "| 1 |", "HANDOFF.md"), True),
                          (4, line_of("both", "| 4 |", "HANDOFF.md"), False),
                          (7, line_of("both", "| 7 |", "HANDOFF.md"), False)])
        self.assertEqual(got["order"]["open"], 2)
        self.assertEqual(self.item("both", "- S3:")["after_step"], 7)
        steps = [l.split()[1] for l in self.text("both") if l.startswith("step ")]
        self.assertEqual(steps, ["4", "7"])
        # the other order: the list comes first, so the table is ignored
        repo = self.empty_dir("list-first")
        with open(os.path.join(repo, "HANDOFF.md"), "w", encoding="utf-8") as handle:
            handle.write("# handoff\n\n## Next work\n\n1. **First.** Open.\n\n"
                         "| rank | work | state |\n|---|---|---|\n| 1 | First | open |\n"
                         "| 2 | Second | open |\n")
        with open(os.path.join(repo, NICE), "w", encoding="utf-8") as handle:
            handle.write("- ok\n")
        steps = self.view(repo)["repos"][0]["steps"]
        self.assertEqual([(s["n"], s["line"]) for s in steps], [(1, 5)])

    def test_ascii_digits_only_number_a_step(self):
        # B1: `¹` passes str.isdigit() and fails int(); `١` matches \d
        cases = {"table": "| ¹ | footnoted | open |\n| 2 | kept | open |\n",
                 "numbered": "١. Arabic-Indic one\n2. kept\n"}
        for name, body in cases.items():
            with self.subTest(shape=name):
                repo = self.empty_dir("digits-" + name)
                with open(os.path.join(repo, "HANDOFF.md"), "w", encoding="utf-8") as handle:
                    handle.write("# handoff\n\n## Next work\n\n" + body)
                with open(os.path.join(repo, NICE), "w", encoding="utf-8") as handle:
                    handle.write("- ok\n")
                code, out, err = self.run_cli(repo, "--json")
                self.assertEqual(code, 0, err)
                steps = json.loads(out)["repos"][0]["steps"]
                self.assertEqual([(s["n"], s["title"]) for s in steps], [(2, "kept")])

    # section 4: placement

    def test_s1_s2_before_step_one(self):
        got = self.repo("numbered")["items"]
        self.assertEqual([(i["rank"], i["level"]) for i in got[:2]], [(1, "S1"), (2, "S2")])
        self.assertIsNone(got[0]["after_step"])
        lines = self.text("numbered")
        first_step = next(n for n, l in enumerate(lines) if l.startswith("step "))
        self.assertRegex(lines[1], r"^1 S1  ")
        self.assertRegex(lines[2], r"^2 S2  ")
        self.assertEqual(first_step, 3)

    def test_span_attaches_after_step(self):
        got = self.item("numbered", "- S3, the LaunchAgent")
        self.assertEqual((got["after_step"], got["span"]), (4, "launchd/com.example.serve.plist"))
        got = self.item("numbered", "- `freeze` never discovers")
        self.assertEqual((got["after_step"], got["span"]), (6, "dotfiles/home/"))
        self.assertIsNone(self.item("numbered", "- S4: `example-site-a` and")["after_step"])
        self.assertIsNone(self.item("numbered", "- S4: `docs/history")["after_step"])
        got = self.item("table", "- `internal/apiroster/key.go:116`")
        self.assertEqual((got["after_step"], got["span"]), (8, "internal/apiroster/key.go"))
        got = self.item("table", "- S3: `docs/design-credential-life.md:40-52`")
        self.assertEqual(got["after_step"], 7)
        lines = self.text("numbered")
        at = lines.index(next(l for l in lines if l.startswith("step 4  ")))
        self.assertIn("%s:%d " % (NICE, line_of("numbered", "- S3, the LaunchAgent")), lines[at + 1])

    def test_done_step_attaches_nothing(self):
        self.assertIsNone(self.item("numbered", "- S3: `scripts/corpus-budget`")["after_step"])
        self.assertIsNone(self.item("table", "- S3: the renewal workflow")["after_step"])

    def test_tail_s3_then_s4_in_file_order(self):
        got = self.repo("numbered")["items"]
        want = [line_of("numbered", n) for n in (
            "- S1: the plist", "- S2: the brew", "- S3, the LaunchAgent", "- `freeze` never",
            "- S3: `scripts/corpus-budget`", "- tmux is not", "- `HANDOFF.md` reads",
            "- S4: `docs/history", "- S4: `example-site-a` and")]
        self.assertEqual([i["line"] for i in got], want)
        self.assertEqual([i["rank"] for i in got], list(range(1, 10)))
        got = self.repo("table")["items"]
        want = [line_of("table", n) for n in (
            "- S3: `docs/design-credential", "- `internal/apiroster", "- S3: the renewal",
            "- Refuse a slash", "- Quarantine per", "- Row rtfix4", "- Row l2b2")]
        self.assertEqual([i["line"] for i in got], want)

    # section 1: the verb's edges

    def test_no_handoff_exit_0(self):
        got = self.repo("relay")
        self.assertEqual((got["handoff"], got["order"], got["steps"]), (None, None, []))
        self.assertEqual(self.text("relay")[0], "== relay  build order: none (no HANDOFF.md)")
        # it ignores --ledger, before or after the verb
        out = io.StringIO()
        self.assertEqual(decisions.main(["--ledger", "/nowhere/DECISIONS.md", "backlog",
                                         fixture("relay")], out=out, err=io.StringIO()), 0)
        self.assertEqual(self.run_cli(fixture("relay"), "--ledger", "/nowhere")[0], 0)

    def test_no_nice_exit_0(self):
        bare = self.empty_dir("bare")
        code, out, err = self.run_cli(bare)
        self.assertEqual((code, out, err), (0, "== bare  no NICE_TO_HAVE.md\n", ""))
        data = self.view(bare)
        self.assertEqual((data["repos"], data["skipped"]), ([], [os.path.realpath(bare)]))
        # REPO by default: the working directory's git top level
        subprocess.run(["git", "init", "-q", bare], check=True)
        os.makedirs(os.path.join(bare, "sub"))
        here = os.getcwd()
        os.chdir(os.path.join(bare, "sub"))
        self.addCleanup(os.chdir, here)
        self.assertEqual(self.run_cli(), (0, "== bare  no NICE_TO_HAVE.md\n", ""))

    def test_not_a_directory_exit_2(self):
        afile = os.path.join(self.tmp, "afile")
        with open(afile, "w", encoding="utf-8") as handle:
            handle.write("x\n")
        for path in (afile, os.path.join(self.tmp, "missing")):
            with self.subTest(path=path):
                code, out, err = self.run_cli(fixture("relay"), path)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("not a directory", err)
        self.assertEqual(self.run_cli("--bogus")[0], 2)

    def test_bad_utf8_exit_2(self):
        for name in (NICE, "HANDOFF.md"):
            with self.subTest(name=name):
                repo = self.empty_dir("bad-" + name)
                for each in (NICE, "HANDOFF.md"):
                    with open(os.path.join(repo, each), "wb") as handle:
                        handle.write(b"- ok\n" if each != name else b"- \xff\xfe bad\n")
                code, out, err = self.run_cli(repo)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("unreadable", err)

    def test_json_fields(self):
        data = self.view(fixture("numbered"))
        self.assertEqual(set(data), {"repos", "skipped"})
        repo = data["repos"][0]
        self.assertEqual(set(repo), {"repo", "nice", "handoff", "order", "steps", "items"})
        self.assertEqual(repo["repo"], os.path.realpath(fixture("numbered")))
        self.assertEqual(repo["nice"], os.path.join(repo["repo"], NICE))
        self.assertEqual(repo["handoff"], os.path.join(repo["repo"], "HANDOFF.md"))
        self.assertEqual(set(repo["order"]), {"line", "heading", "open"})
        for step in repo["steps"]:
            self.assertEqual(set(step), {"n", "line", "title", "done"})
        for item in repo["items"]:
            self.assertEqual(set(item), {"rank", "line", "title", "level", "placed_as",
                                         "level_from", "after_step", "span"})
            self.assertEqual(item["placed_as"], item["level"] or "S4")
            self.assertLessEqual(len(item["title"]), 80)

    def test_many_repos_and_skipped(self):
        one, two = self.empty_dir("one"), self.empty_dir("two")
        code, out, err = self.run_cli(fixture("relay"), one, fixture("numbered"), two)
        self.assertEqual((code, err), (0, ""))
        lines = out.splitlines()
        heads = [l.split()[1] for l in lines if l.startswith("== ")]
        self.assertEqual(heads, ["relay", "numbered"])
        self.assertEqual(lines[-1], "skipped (no NICE_TO_HAVE.md): one, two")
        data = self.view(fixture("relay"), one, fixture("numbered"), two)
        self.assertEqual([os.path.basename(r["repo"]) for r in data["repos"]],
                         ["relay", "numbered"])
        self.assertEqual([os.path.basename(p) for p in data["skipped"]], ["one", "two"])

    def test_writes_nothing(self):
        copy = os.path.join(self.tmp, "copy")
        shutil.copytree(FIXTURES, copy)
        before = snapshot(copy)
        names = sorted(os.listdir(copy))
        here = os.getcwd()
        os.chdir(copy)
        self.addCleanup(os.chdir, here)
        for flags in ([], ["--json"]):
            code, _out, err = self.run_cli(*([os.path.join(copy, n) for n in names] + flags))
            self.assertEqual(code, 0, err)
        self.assertEqual(snapshot(copy), before)

    # section 6: respeak kept optional

    def test_backlog_runs_no_render(self):
        root = os.path.join(self.tmp, "respeak")
        trace = os.path.join(self.tmp, "rendered")
        script = os.path.join(root, speak.RENDER)
        os.makedirs(os.path.dirname(script))
        with open(script, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\ntouch '%s'\n" % trace)
        os.chmod(script, 0o755)
        copy = os.path.join(self.tmp, "numbered")
        shutil.copytree(fixture("numbered"), copy)
        with mock.patch.dict(os.environ, {"RESPEAK_ROOT": root}), \
                mock.patch.object(speak, "render_text",
                                  side_effect=AssertionError("backlog rendered")):
            for flags in ([], ["--json"]):
                self.assertEqual(self.run_cli(copy, *flags)[0], 0)
        self.assertFalse(os.path.exists(trace))
        self.assertEqual(sorted(os.listdir(copy)), ["HANDOFF.md", NICE])

    def test_plugin_declares_no_dependency(self):
        for rel in ("plugin/.claude-plugin/plugin.json",):
            with open(os.path.join(REPO, rel), encoding="utf-8") as handle:
                text = handle.read()
            with self.subTest(rel=rel):
                self.assertNotIn("dependencies", json.loads(text))
                for plugin in json.loads(text).get("plugins", []):
                    self.assertNotIn("dependencies", plugin)
                self.assertNotIn("respeak", text)
        with open(os.path.join(REPO, "pyproject.toml"), encoding="utf-8") as handle:
            self.assertRegex(handle.read(), r"(?m)^dependencies = \[\]$")

    def test_suite_green_without_respeak(self):
        """The modules that meet respeak (ask, doctor, the CLI, the plugin) pass under an
        empty plugin cache and no RESPEAK_ROOT."""
        home = self.empty_dir("home")
        os.makedirs(os.path.join(home, ".claude", "plugins", "cache"))
        env = {"HOME": home, "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
               "PYTHONPATH": os.path.join(REPO, "src")}
        self.assertIsNone(speak.respeak_root(env, os.path.join(home, ".claude", "plugins",
                                                                "cache")))
        run = subprocess.run([sys.executable, "-m", "unittest", "-q", "tests.test_ask",
                              "tests.test_doctor", "tests.test_cli", "tests.test_plugin"],
                             cwd=REPO, env=env, capture_output=True, text=True, timeout=300)
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])

    def test_doctor_respeak_warn_absent(self):
        home = self.empty_dir("home")
        status, detail = doctor.check_respeak({"HOME": home})
        self.assertEqual(status, "warn")
        self.assertIn("respeak", detail)
        root = os.path.join(self.tmp, "respeak")
        os.makedirs(os.path.join(root, "scripts"))
        open(os.path.join(root, speak.RENDER), "w").close()
        self.assertEqual(doctor.check_respeak({"HOME": home, "RESPEAK_ROOT": root}),
                         ("ok", root))
        # a warn never changes the exit
        ok = mock.Mock(return_value=("ok", "fine"))
        with mock.patch.multiple(doctor, check_python=ok, check_tool=ok, check_marketplace=ok,
                                 check_plugin=ok, check_provider=ok, check_ledger=ok), \
                mock.patch.dict(os.environ, {"HOME": home}):
            out = io.StringIO()
            self.assertEqual(decisions.main(["doctor"], out=out, err=io.StringIO()), 0)
        self.assertIn("warn respeak: ", out.getvalue())


class Shipped(unittest.TestCase):
    """Not hermetic: it reads CLAUDE.md, which `Hermetic` guards, and calls no verb."""

    def test_include_shipped_and_imported(self):
        """respeak include r1 sections 1 to 3: the author's rendered file ships under
        plugin/, within the 1,500-byte cap, stamped, and CLAUDE.md imports it. Read from
        this repo only, so the test holds with no respeak installed."""
        path = os.path.join(REPO, INCLUDE)
        self.assertTrue(os.path.isfile(path), "no %s" % INCLUDE)
        with open(path, "rb") as handle:
            data = handle.read()
        self.assertLessEqual(len(data), 1500)
        first = data.split(b"\n", 1)[0].decode("utf-8")
        self.assertRegex(first, r"^<!-- respeak include v\S+, inputs [0-9a-f]{8};.*-->$")
        with open(os.path.join(REPO, "CLAUDE.md"), encoding="utf-8") as handle:
            self.assertIn("@" + INCLUDE, handle.read().splitlines())


if __name__ == "__main__":
    unittest.main()
