"""d23 section 7: `agentik decisions backlog`, each repo's NICE_TO_HAVE.md placed against
its HANDOFF.md build order. It writes nothing and never renders through respeak.

The fixtures under tests/fixtures/backlog/ are trimmed from the real files: relay
(a level in a `##` heading), session (the lead's four forms), intro (`Each line is
S<n>.`, `Each line below is S<n>.` and owner steps that are no build order),
numbered (`N. ` steps, `done` and `DECIDED`), table (rows whose first cell is an integer), both (a table, then `N. `
items on the same steps: the first shape wins), marker (the marker line beats a
heading prefix) and agents (the lead's fifth form, its level then a middle dot).
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

    def test_lead_dot_form(self):
        # d24: the fifth form, `S<n> · ` at the lead's head, in a bold lead or a plain one
        for needle, level in (("- **S1 · tests/test-apirun.py", "S1"),
                              ("- **S2 · plugin/skills", "S2"),
                              ("- **S3 · tests: the fixture drifts", "S3"),
                              ("- **S4 · README.md", "S4"),
                              ("- S1 · bin/run", "S1"),
                              ("- S2 · bin/check", "S2"),
                              ("- S3 · scripts/lint", "S3"),
                              ("- S4 · docs/guide.md", "S4"),
                              ("- **S3 · tests: a dot lead beats its heading", "S3")):
            with self.subTest(needle=needle):
                got = self.item("agents", needle)
                self.assertEqual((got["level"], got["level_from"]), (level, "lead"))
        # the title keeps its lead whole, as the other forms keep their token
        self.assertEqual(self.item("agents", "- **S1 · tests/test-apirun.py")["title"],
                         "S1 · tests/test-apirun.py: the mid-run read races the writer")

    def test_lead_dot_form_exact(self):
        # d24 ruling 2: the dot needs a space each side and the lead's head; S21 is no level
        for needle in ("- **S21 · the round's name", "- **S3·x the dot glued",
                       "- **Read the lead · S2 · in its middle"):
            with self.subTest(needle=needle):
                got = self.item("agents", needle)
                self.assertEqual((got["level"], got["level_from"]), (None, None))

    def test_lead_dot_form_ranks_first(self):
        line = line_of("agents", "- **S1 · tests/test-apirun.py")
        first = self.repo("agents")["items"][0]
        self.assertEqual((first["rank"], first["line"], first["level"], first["placed_as"]),
                         (1, line, "S1", "S1"))
        lines = self.text("agents")
        printed = [l for l in lines if re.match(r"^\d+ S[1-4]\??  ", l)]
        self.assertEqual(printed[0], "1 S1  %s:%d  S1 · tests/test-apirun.py: the mid-run "
                                     "read races the writer" % (NICE, line))
        self.assertEqual(lines[-1], "3 of 13 items carry no level (placed as S4)")

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
               "PYTHONPATH": os.path.join(REPO, "plugin", "lib")}
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

    # d26: design/05 section 2's NICE rows (the fixture `rows`)

    def rows_items(self):
        with open(os.path.join(fixture("rows"), NICE), encoding="utf-8") as handle:
            return decisions.nice_items(handle.read())

    def test_row_level_from_cell(self):
        got = self.item("rows", "| n1 |")
        self.assertEqual((got["level"], got["level_from"], got["id"]), ("S2", "cell", "n1"))
        self.assertEqual(self.item("rows", "| n4 |")["level"], "S3")
        # S4 when the cell says so, under a heading's S2 and a sentence's S1
        self.assertEqual(self.item("rows", "| n6 |")["level"], "S4")
        # anything but `^S[1-4]$` is unlevelled, as today: placed S4, never the heading's
        for needle in ("| n2 |", "| n3 |", "| n5 |", "| n7 |"):
            got = self.item("rows", needle)
            self.assertEqual((got["level"], got["level_from"], got["placed_as"]),
                             (None, None, "S4"), needle)

    def test_row_title_and_escaped_pipe(self):
        self.assertEqual(self.item("rows", "| n1 |")["title"], "The hint names make install")
        self.assertEqual(self.item("rows", "| n2 |")["title"], "An unsure level cell")
        self.assertEqual(self.item("rows", "| n4 |")["title"],
                         "A cell holding `a \\| b` keeps its pipe")
        # an S1 in the finding is text, as a token outside a lead is
        self.assertEqual(self.item("rows", "| n5 |")["title"], "An empty level cell")

    def test_row_spans_from_area_finding_evidence(self):
        by_id = {i.get("id"): i for i in self.rows_items()}
        self.assertEqual(by_id["n4"]["spans"], ["scripts/doclint",
                                                "plugin/lib/tool/backlog.py",
                                                "tests/fixtures/x.md"])
        self.assertEqual(by_id["n1"]["spans"], ["plugin/lib/tool/doctor.py", "doctor.py"])
        self.assertEqual(by_id["n2"]["spans"], [])

    def test_rows_and_bullets_in_file_order(self):
        items = self.rows_items()
        self.assertEqual([i.get("id") for i in items],
                         [None, "n1", "n2", "n3", "n4", "n5", None, "n6", "n7", None])
        self.assertEqual([i["line"] for i in items], sorted(i["line"] for i in items))
        # the bullets around the rows keep their levels: the lead's, then the sentence's
        bullets = [(i["level"], i["level_from"]) for i in items if "id" not in i]
        self.assertEqual(bullets, [("S3", "lead"), ("S1", "lead"), ("S1", "sentence")])

    def test_other_table_yields_nothing(self):
        lines = [i["line"] for i in self.repo("rows")["items"]]
        for needle in ("Another header yields nothing", "Five columns is another header",
                       "No separator line", "A fenced row is no item"):
            self.assertNotIn(line_of("rows", needle), lines, needle)
        self.assertEqual(len(lines), 10)

    def test_row_id_in_text_and_json(self):
        line = line_of("rows", "| n1 |")
        self.assertIn("3 S2  NICE_TO_HAVE.md:%d  n1  The hint names make install" % line,
                      self.text("rows"))
        got = self.item("rows", "| n1 |")
        self.assertEqual(set(got), {"rank", "line", "title", "level", "placed_as",
                                    "level_from", "after_step", "span", "id"})
        bullet = self.item("rows", "- S1: a bullet after the table")
        self.assertNotIn("id", bullet)
        # S1 first in file order, then S2: the two S1 bullets, then n1
        ranks = [(i["rank"], i.get("id")) for i in self.repo("rows")["items"]][:3]
        self.assertEqual(ranks, [(1, None), (2, None), (3, "n1")])

    # d26: `--order FILE`, one HANDOFF.md for every REPO (the fixture `order`)

    def ordered(self, *names):
        order = os.path.join(fixture("order"), "HANDOFF.md")
        data = self.view("--order", order, *[os.path.join(fixture("order"), n) for n in names])
        return {os.path.basename(r["repo"]): r for r in data["repos"]}

    def test_order_attaches_by_repo(self):
        got = self.ordered("agentik-relay", "agentik-session")
        relay, session = got["agentik-relay"], got["agentik-session"]
        self.assertEqual(relay["handoff"],
                         os.path.realpath(os.path.join(fixture("order"), "HANDOFF.md")))
        # the repo's own HANDOFF.md is not read: FILE's steps, the relay's and the suite's
        self.assertEqual([(s["n"], s["repo"]) for s in relay["steps"]], [(1, "relay"), (2, "suite")])
        self.assertEqual(relay["order"], {"line": 3, "heading": "Build order", "open": 2})
        after = {i["id"]: i["after_step"] for i in relay["items"]}
        # r2 shares a path only with the session's step 4, so it is not attached
        self.assertEqual((after["r1"], after["r2"]), (1, None))
        self.assertEqual({i["id"]: i["after_step"] for i in session["items"]}["s2"], 4)
        lines = self.text_of("agentik-relay", "agentik-session")
        self.assertIn("step 1  HANDOFF.md:7  The relay's drain", lines[0])
        self.assertNotIn("The relay's drain", lines[1])

    def test_order_suite_step_for_every_repo(self):
        got = self.ordered("agentik-relay", "agentik-session")
        for name in ("agentik-relay", "agentik-session"):
            self.assertIn((2, "suite"), [(s["n"], s["repo"]) for s in got[name]["steps"]], name)
        self.assertEqual({i["id"]: i["after_step"] for i in got["agentik-relay"]["items"]}["r3"], 2)

    def test_order_done_step_attracts_nothing(self):
        session = self.ordered("agentik-session")["agentik-session"]
        self.assertEqual([(s["n"], s["done"]) for s in session["steps"]],
                         [(2, False), (3, True), (4, False)])
        self.assertEqual(session["order"]["open"], 2)
        after = {i["id"]: (i["after_step"], i["placed_as"]) for i in session["items"]}
        # s1 shares its path with the done step 3 alone; s3 with the relay's step 1
        self.assertEqual(after, {"s1": (None, "S3"), "s2": (4, "S3"), "s3": (None, "S4")})

    def test_order_no_repo_column_is_todays_view(self):
        table = fixture("table")
        plain = self.view(table)["repos"][0]
        data = self.view("--order", os.path.join(table, "HANDOFF.md"), table)["repos"][0]
        self.assertEqual(data["items"], plain["items"])
        self.assertEqual(data["order"], plain["order"])
        self.assertEqual([(s["n"], s["repo"]) for s in data["steps"]],
                         [(s["n"], None) for s in plain["steps"]])
        self.assertNotIn("repo", plain["steps"][0])
        code, out, _err = self.run_cli("--order", os.path.join(table, "HANDOFF.md"), table)
        self.assertEqual((code, out), (0, "\n".join(self.text("table")) + "\n"))

    def test_order_not_a_file_exit_2(self):
        code, out, err = self.run_cli("--order", self.empty_dir("nofile"), fixture("rows"))
        self.assertEqual((code, out), (2, ""))
        self.assertIn("--order", err)

    def text_of(self, *names):
        code, out, err = self.run_cli("--order", os.path.join(fixture("order"), "HANDOFF.md"),
                                      *[os.path.join(fixture("order"), n) for n in names])
        self.assertEqual(code, 0, err)
        return out.split("\n\n")


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


# d31 (b3): the reply's probe file, byte for byte: ten lines, one open.
B2 = """# scratch: what a review left open

## From a review (0 S1, 0 S2, 0 S3, 4 S4)
- S4, F0: an open line, the only open one here.
- **Closed 2026-10-28 by branch `sec-s4` (a8b5bef).** S4, F1: a closed line with a bold Closed lead.
- ~~S4, F2: a closed line struck through.~~
- [x] S4, F3: a closed line with a ticked box.
- S4, F4 (closed 2026-10-28, a8b5bef): a closed line whose lead says closed.

## No tally in this heading
- **Closed 2026-10-28 by branch `x` (a8b5bef).** S1, F5: closed, its own level S1 after the bold lead.
- S1, F6: DONE at a8b5bef, landed.
- ~~S1, F7: struck through.~~

## Open findings

| id | level | area | finding | evidence | from |
|---|---|---|---|---|---|
| n1 | S1 | `a.py` | Closed 2026-11-01 at abc1234: a closed row left in the table | `a.py:1` | 2026-11-01 |
| ~~n2~~ | ~~S1~~ | `a.py` | ~~a struck row~~ | `a.py:2` | 2026-11-01 |
"""

TALLY = """# scratch

## From a review (0 S1, 0 S2, 0 S3, 2 S4)
- an open line with no level of its own

## S2: the gate (1 S2)
- a line under a level and its tally

## 10 S4 left
- a line under a count alone

## S3 and S4
- a line under two levels
"""

OPEN = """# scratch

## Open
- Closed captions lag the video: an open line that opens with the word.
- **Closedown is slow.** An open line, bold.
- S3, a plain one.
"""


class Closed(Hermetic):

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.repo = os.path.join(self.tmp, "b2")
        os.mkdir(self.repo)

    def backlog(self, text, *argv):
        with open(os.path.join(self.repo, "NICE_TO_HAVE.md"), "w", encoding="utf-8") as handle:
            handle.write(text)
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["backlog", self.repo] + list(argv), out=out, err=err)
        self.assertEqual(code, 0, err.getvalue())
        return out.getvalue()

    def test_closed_tally_is_no_level(self):
        items = decisions.backlog.nice_items(TALLY)
        self.assertEqual([(i["level"], i["level_from"]) for i in items],
                         [(None, None), ("S2", "heading"), (None, None), ("S3", "heading")])

    def test_closed_leads_go_to_one_line(self):
        self.assertEqual(self.backlog(B2).splitlines(), [
            "== b2  build order: none (no HANDOFF.md)",
            "1 S1  NICE_TO_HAVE.md:12  S1, F6",
            "2 S4  NICE_TO_HAVE.md:4  S4, F0",
            "3 S4  NICE_TO_HAVE.md:8  S4, F4 (closed 2026-10-28, a8b5bef)",
            "0 of 3 items carry no level (placed as S4)",
            "7 closed, not placed"])

    def test_closed_lines_in_json_and_none_without_one(self):
        repo = json.loads(self.backlog(B2, "--json"))["repos"][0]
        self.assertEqual(repo["closed"], [5, 6, 7, 11, 13, 19, 20])
        self.assertEqual([i["line"] for i in repo["items"]], [12, 4, 8])
        self.assertEqual(json.loads(self.backlog(OPEN, "--json"))["repos"][0]["closed"], [])
        text = self.backlog(OPEN).splitlines()
        self.assertEqual(text[-1], "2 of 3 items carry no level (placed as S4)")
        self.assertEqual(len(text), 5)


if __name__ == "__main__":
    unittest.main()
