"""in1: `questions [REPO...] [--json]` reads each repo's OPEN-QUESTIONS.md as one object
or one text block, in `ask`'s judgement, and never locks, renders, calls a model or
writes."""

import io
import json
import os
import shutil
import subprocess
import sys
from unittest import mock

import decisions
from decisions import ask
from tests.hermetic import SAMPLE, Hermetic

TITLE = "Where the hay goes"
NEW = ["new", "--title", TITLE, "--stands", "The hay sits in the yard.",
       "--choice", "The barn, or the loft?",
       "--option", "Barn: Keeps it dry by the gate.", "--option", "Loft: Frees the floor.",
       "--recommend", "The barn. It is nearer."]
DAY = "2026-09-28"
ANSWER = "**Your answer:**"
DECIDED = ("\n## Decided without asking\n\nA paragraph above the bullets.\n\n"
           "- Kept the gate red (2026-09-01; chat)\n"
           "- Fed the goats first (2999-01-01; chat)\n"
           "- Moved the trough (2026-10-02; chat)\n"
           "  its second line, no bullet\n"
           "\n## Answered\n\nA paragraph above them.\n\n"
           "- 3. Fence the field: Wire (2026-08-15; chat)\n"
           "- 4. Paint the shed: Green (2026-08-16; chat)\n")
STUB = "#!/bin/sh\necho \"$@\" >> \"%s\"\n"
HOLD = ("import fcntl, sys\nf = open(sys.argv[1], 'a')\nfcntl.flock(f, fcntl.LOCK_EX)\n"
        "print('held', flush=True)\nsys.stdin.read()\n")


class Read(Hermetic):

    def setUp(self):
        super().setUp()
        self.home = os.path.realpath(os.environ["HOME"])
        side = os.path.dirname(self.home)
        self.calls = os.path.join(side, "claude-calls")
        stub_bin = os.path.join(side, "bin")
        os.makedirs(stub_bin)
        with open(os.path.join(stub_bin, "claude"), "w") as handle:
            handle.write(STUB % self.calls)
        os.chmod(os.path.join(stub_bin, "claude"), 0o755)
        os.environ["PATH"] = stub_bin + os.pathsep + os.environ["PATH"]
        self.pear, self.quince = self.repo("pear"), self.repo("quince")
        self.bare = self.repo("bare")
        self.file = os.path.join(self.pear, "OPEN-QUESTIONS.md")
        shutil.copy(SAMPLE, os.path.join(self.pear, "DECISIONS.md"))
        with mock.patch.object(ask, "today", lambda: DAY):
            code, out, err = self.run_tool(*NEW + ["--ledger", os.path.join(self.pear,
                                                                             "DECISIONS.md")])
        self.assertEqual(code, 0, out + err)
        self.clean = self.read(self.file)
        self.write(os.path.join(self.quince, "OPEN-QUESTIONS.md"), "# Decisions for the owner\n")

    def repo(self, name):
        path = os.path.join(self.home, name)
        os.makedirs(path)
        return path

    def read(self, path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def write(self, path, text):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def run_tool(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(list(argv), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def snapshot(self):
        found = {}
        for top, _dirs, files in os.walk(self.home):
            for name in files:
                path = os.path.join(top, name)
                st = os.stat(path)
                with open(path, "rb") as handle:
                    found[path] = (st.st_size, st.st_mtime_ns, handle.read())
        return found

    def questions(self, *argv, **kw):
        """`questions` run; every file under the home as it was, the stub never called."""
        before = self.snapshot()
        code, out, err = self.run_tool("questions", *argv)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(os.path.exists(self.calls))
        self.assertEqual(code, kw.get("code", 0), out + err)
        return json.loads(out) if "--json" in argv else out

    def one(self):
        got = self.questions(self.pear, "--json")
        self.assertEqual(len(got["repos"][0]["questions"]), 1)
        return got["repos"][0], got["repos"][0]["questions"][0]

    def swap(self, old, new):
        text = self.read(self.file)
        self.assertEqual(text.count(old), 1, old)
        self.write(self.file, text.replace(old, new))


class Json(Read):

    def test_1_one_clean_block(self):
        got = self.questions(self.pear, "--json")
        self.assertEqual(set(got), {"schema", "ok", "repos", "skipped"})
        self.assertEqual((got["schema"], got["ok"], got["skipped"]),
                         ("agentik.questions/1", True, []))
        repo = got["repos"][0]
        self.assertEqual(repo["repo"], self.pear)
        self.assertEqual(repo["file"], self.file)
        self.assertEqual((repo["answered"], repo["decided"], repo["problems"]),
                         (0, {"count": 0, "newest": None}, []))
        q = repo["questions"][0]
        self.assertEqual((q["state"], q["why"], q["base"], q["typed"], q["typed_above"]),
                         ("open", None, True, "", []))
        self.assertEqual((q["title"], q["recommended"], q["proposed"], q["problems"]),
                         (TITLE, "Barn", DAY, []))
        self.assertEqual(q["options"], [
            {"label": "Barn", "effect": "Keeps it dry by the gate.", "recommended": True},
            {"label": "Loft", "effect": "Frees the floor.", "recommended": False}])
        self.assertEqual(q["parts"], {"stands": "The hay sits in the yard.",
                                      "choice": "The barn, or the loft?",
                                      "recommendation": "The barn. It is nearer."})
        heading = "## %d. %s" % (q["n"], TITLE)
        self.assertEqual(self.clean.splitlines()[q["line"] - 1], heading)
        self.assertTrue(q["text"].startswith(heading + "\n"))
        self.assertNotIn("decisions: base", q["text"])
        self.assertIn(ANSWER, q["text"])
        self.assertIn("decisions: base", self.clean)
        ledger = self.read(os.path.join(self.pear, "DECISIONS.md"))
        self.assertIn("(proposed %s; OPEN-QUESTIONS.md)" % DAY, ledger)

    def test_2_typed(self):
        self.swap(ANSWER, ANSWER + " The barn")
        _repo, q = self.one()
        self.assertEqual((q["state"], q["why"], q["typed"]),
                         ("answered", "typed on the answer line", "The barn"))
        self.write(self.file, self.clean)
        self.swap(ANSWER, "Ask the neighbour first.\n\n" + ANSWER)
        _repo, q = self.one()
        self.assertEqual((q["state"], q["why"], q["typed"], q["typed_above"]),
                         ("answered", "typed above the answer line", "",
                          ["Ask the neighbour first."]))

    def test_3_unreadable(self):
        self.swap("- **Loft.** Frees the floor.\n", "")
        repo, q = self.one()
        message = "1 options under the third label; 2 to 4 are asked"
        self.assertEqual((q["state"], q["why"], q["problems"], q["base"]),
                         ("unreadable", message, [message], True))
        self.assertEqual(repo["problems"], [
            {"line": q["line"], "message": "question %d: %s" % (q["n"], message)}])
        self.swap(ANSWER, ANSWER + " The barn")
        _repo, q = self.one()
        self.assertEqual((q["state"], q["typed"]), ("answered", "The barn"))
        self.write(self.file, self.clean)
        base = next(l for l in self.clean.splitlines() if l.startswith("<!-- decisions: base"))
        self.swap(base + "\n", "")
        _repo, q = self.one()
        self.assertEqual((q["state"], q["why"], q["base"], q["typed_above"]),
                         ("unreadable", "no base line, or more than one", False, []))

    def test_4_counts(self):
        self.write(self.file, self.clean.rstrip("\n") + "\n" + DECIDED)
        repo, _q = self.one()
        self.assertEqual(repo["answered"], 2)
        self.assertEqual(repo["decided"], {"count": 3, "newest": "2026-10-02"})

    def decided(self, *bullets):
        text = "\n## Decided without asking\n\n" + "".join("- %s\n" % b for b in bullets)
        self.write(self.file, self.clean.rstrip("\n") + "\n" + text)
        return self.one()[0]["decided"]

    def test_f1_no_calendar_date(self):
        got = self.decided("Kept the gate red (2025-13-45; chat)",
                           "Moved the trough (2025-01-01; chat)")
        self.assertEqual(got, {"count": 2, "newest": "2025-01-01"})

    def test_f1_cut_from_a_longer_run(self):
        got = self.decided("Fed the goats (12026-01-011; chat)")
        self.assertEqual(got, {"count": 1, "newest": None})

    def test_f1_no_such_day(self):
        got = self.decided("Kept the gate red (2025-02-30; chat)",
                           "Moved the trough (2025-01-01; chat)")
        self.assertEqual(got, {"count": 2, "newest": "2025-01-01"})

    def test_5_many(self):
        nowhere = os.path.join(self.home, "nowhere")
        got = self.questions(self.pear, self.quince, nowhere, self.bare, "--json")
        self.assertEqual([r["repo"] for r in got["repos"]], [self.pear, self.quince])
        self.assertEqual(got["repos"][1]["questions"], [])
        self.assertEqual(got["skipped"], [{"repo": nowhere, "why": "not a directory"},
                                          {"repo": self.bare, "why": "no OPEN-QUESTIONS.md"}])

    def test_5_unreadable_file(self):
        with open(os.path.join(self.bare, "OPEN-QUESTIONS.md"), "wb") as handle:
            handle.write(b"# Decisions for the owner \xff\n")
        got = self.questions(self.bare, self.pear, "--json")
        self.assertEqual(got["skipped"], [{"repo": self.bare, "why": "unreadable"}])
        self.assertEqual([r["repo"] for r in got["repos"]], [self.pear])

    def test_6_default_repo(self):
        subprocess.run(["git", "init", "-q", self.pear], check=True)
        inside = os.path.join(self.pear, "deep", "er")
        os.makedirs(inside)
        here = os.getcwd()
        self.addCleanup(os.chdir, here)
        os.chdir(inside)
        got = self.questions("--json")
        self.assertEqual(got["repos"][0]["repo"], self.pear)
        self.assertEqual(len(got["repos"][0]["questions"]), 1)

    def test_7_lock_held(self):
        want = self.questions(self.pear, "--json")
        lock = os.path.join(self.pear, ".new.lock")
        holder = subprocess.Popen([sys.executable, "-c", HOLD, lock], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE)
        self.addCleanup(holder.wait)
        self.addCleanup(holder.stdin.close)
        self.addCleanup(holder.stdout.close)
        self.assertEqual(holder.stdout.readline().strip(), b"held")
        self.assertEqual(self.questions(self.pear, "--json"), want)
        self.assertEqual(self.questions(self.pear, "--json", "--ledger", "/nowhere"), want)

    def test_refusal_under_json(self):
        with mock.patch("decisions.questions_read.git_top",
                        side_effect=decisions.common.Refusal("git rev-parse timed out")):
            got = self.questions("--json", code=2)
        self.assertEqual(got, {"schema": "agentik.questions/1", "ok": False, "error": {
            "code": "refused", "message": "git rev-parse timed out", "remedy": None}})


class Text(Read):

    def test_8_clean(self):
        out = self.questions(self.pear)
        self.assertEqual(out, "== pear  1 open, 0 answered, 0 decided without asking\n"
                              "9  open  %s  recommended: Barn; proposed %s\n" % (TITLE, DAY))

    def test_8_typed(self):
        self.swap(ANSWER, ANSWER + " The barn")
        self.assertIn("9  answered  %s  recommended: Barn; proposed %s; typed on the answer "
                      "line\n" % (TITLE, DAY), self.questions(self.pear))
        self.write(self.file, self.clean)
        self.swap(ANSWER, "Ask the neighbour first.\n\n" + ANSWER)
        self.assertIn("9  answered  %s  recommended: Barn; proposed %s; typed above the answer "
                      "line\n" % (TITLE, DAY), self.questions(self.pear))

    def test_8_unreadable_and_counts(self):
        self.swap("- **Loft.** Frees the floor.\n", "")
        self.write(self.file, self.read(self.file).rstrip("\n") + "\n" + DECIDED
                   + "\n1. a numbered line\n")
        out = self.questions(self.pear)
        lines = out.splitlines()
        self.assertEqual(lines[0], "== pear  1 open, 2 answered, 3 decided without asking, "
                                   "newest 2026-10-02")
        self.assertEqual(lines[1], "9  unreadable  %s  recommended: Barn; proposed %s; 1 options "
                                   "under the third label; 2 to 4 are asked" % (TITLE, DAY))
        loose = [l for l in lines if l.startswith("problem  ")]
        self.assertEqual(len(loose), 1)
        self.assertRegex(loose[0], r"^problem  OPEN-QUESTIONS\.md:\d+  a line under `Answered` "
                                   r"that is not a `- ` bullet$")
        self.write(self.file, self.clean)
        self.swap(next(l for l in self.clean.splitlines() if l.startswith("<!-- decisions: base"))
                  + "\n", "")
        self.assertIn("; no base line, or more than one\n", self.questions(self.pear))

    def test_8_many(self):
        nowhere, gone = os.path.join(self.home, "nowhere"), os.path.join(self.home, "gone")
        out = self.questions(self.pear, self.quince, nowhere, self.bare, gone)
        self.assertEqual(out.split("\n\n")[1:], [
            "== quince  0 open, 0 answered, 0 decided without asking",
            "skipped (not a directory): nowhere, gone\nskipped (no OPEN-QUESTIONS.md): bare\n"])


class Help(Read):

    def test_9_help(self):
        code, out, _err = self.run_tool("--help")
        self.assertEqual(code, 0)
        self.assertIn("questions [REPO...] [--json]", out)
        self.assertEqual(list(decisions.VERBS)[8:10], ["backlog", "questions"])
        code, out, _err = self.run_tool("questions", "--help")
        self.assertEqual(code, 0)
        self.assertIn("REPO", out)
