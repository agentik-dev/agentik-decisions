"""`analyze` (d29): churn's known answers on five fixture repos, A to E, each built
in a temp directory with fixed dates, an identity by `-c` and no global config.
The window is 2026-10-26 to 2026-11-09; the verb reads git and writes nothing."""

import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from unittest import mock

import decisions
from decisions import common
from decisions.render import BEGIN, END
from tests.hermetic import Hermetic
from tests.test_backlog import snapshot

GIT = shutil.which("git") or "/usr/bin/git"
WINDOW = ["--since", "2026-10-26", "--until", "2026-11-09"]
HEADER = "| id | level | area | finding | evidence | from |\n|---|---|---|---|---|---|\n"
NOT_COMPUTED = ("not computed: tokens, account spend, work redone at a respawn, rows built "
                "and never landed")
STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
VERBS = {"rev-parse", "log", "rev-list", "show"}


def lines(n, word="line"):
    return "".join("%s %d\n" % (word, i) for i in range(1, n + 1))


def rows(*ids):
    return HEADER + "".join("| %s | S4 | a | finding %s | e | f |\n" % (i, i) for i in ids)


class Fixture:
    """A repo under `root`: files written, committed at a fixed date."""

    def __init__(self, root):
        self.root = root
        os.makedirs(root)
        self.git("init", "-q")

    def git(self, *args, date=None):
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        if date:
            env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date + " 12:00:00 +0000"
        subprocess.run([GIT, "-c", "user.name=fixture", "-c", "user.email=fixture",
                        "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]
                       + list(args), cwd=self.root, env=env, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def write(self, path, text):
        full = os.path.join(self.root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(text)

    def commit(self, date, files):
        for path, text in files.items():
            self.write(path, text)
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "at " + date, date=date)


def build(top):
    """The five fixtures under `top`, as the packet's section 3 rules them."""
    a = Fixture(os.path.join(top, "A"))
    a.commit("2026-11-01", {"src/app.py": lines(5)})
    a.commit("2026-11-02", {"tests/test_app.py": lines(3)})
    a.commit("2026-11-03", {"history/sittings/2026-11-03-1.md": lines(4)})
    a.commit("2026-11-04", {"vendor/lib/x.py": lines(7)})

    b = Fixture(os.path.join(top, "B"))
    b.commit("2026-10-20", {"src/app.py": lines(20)})
    b.git("checkout", "-q", "-b", "row")
    charter = "history/sittings/2026-10-27-1.md"
    b.commit("2026-10-27", {"design/packets/p.md": lines(6), charter: lines(2)})
    os.makedirs(os.path.join(b.root, "plugin", "lib"))
    b.git("mv", "src/app.py", "plugin/lib/app.py")
    b.commit("2026-10-28", {"plugin/lib/app.py": lines(21), charter: lines(3)})
    b.commit("2026-10-29", {charter: lines(4)})
    b.commit("2026-10-30", {charter: lines(5)})
    b.git("checkout", "-q", "main")
    b.git("merge", "-q", "--no-ff", "-m", "land row", "row", date="2026-10-31")
    b.commit("2026-11-02", {"history/sittings/2026-11-02-1.md": lines(2),
                              "HANDOFF.md": lines(9)})

    c = Fixture(os.path.join(top, "C"))
    c.commit("2026-10-25", {"NICE_TO_HAVE.md": rows("n1", "n2")})
    c.commit("2026-10-30", {"NICE_TO_HAVE.md": rows("n2", "n3", "n4")})
    c.git("checkout", "-q", "-b", "side")
    c.commit("2026-11-01", {"NICE_TO_HAVE.md": rows("n2", "n3", "n4", "n9")})
    c.git("checkout", "-q", "main")
    c.git("merge", "-q", "--no-ff", "-m", "land side", "side", date="2026-11-03")
    c.commit("2026-11-05", {"NICE_TO_HAVE.md": rows("n3", "n4", "n5", "n6", "n9"),
                            "history/NICE-overflow.md": rows("n2")})

    d = Fixture(os.path.join(top, "D"))
    d.commit("2026-10-25", {"NICE_TO_HAVE.md": "- one\n- two\n- three\n"})
    d.commit("2026-11-01", {"NICE_TO_HAVE.md": rows("n1")})
    d.commit("2026-11-05", {"NICE_TO_HAVE.md": rows("n1", "n2")})

    e = Fixture(os.path.join(top, "E"))
    e.commit("2026-10-01", {"src/app.py": lines(1)})


class Analyze(Hermetic):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.top = tempfile.mkdtemp(prefix="decisions-analyze-")
        build(cls.top)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.top, True)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="decisions-analyze-run-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def repo(self, name):
        return os.path.join(self.top, name)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["analyze"] + list(argv), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def text(self, *argv):
        code, out, err = self.run_cli(*(list(argv) + WINDOW))
        self.assertEqual(code, 0, err)
        return out

    def view(self, *argv):
        code, out, err = self.run_cli(*(list(argv) + WINDOW + ["--json"]))
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def one(self, name):
        return self.view(self.repo(name))["churn"]["repos"][0]

    def logging_git(self, body=""):
        """A `git` on PATH that logs each call's arguments, a tab after each, then runs
        the real one; `body` runs first."""
        log = os.path.join(self.tmp, "git.log")
        fake = os.path.join(self.tmp, "bin", "git")
        os.makedirs(os.path.dirname(fake))
        with open(fake, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\nprintf '%%s\\t' \"$@\" >> %s\necho >> %s\n%s\nexec %s \"$@\"\n"
                         % (log, log, body, GIT))
        os.chmod(fake, 0o755)
        path = os.path.dirname(fake) + os.pathsep + os.environ.get("PATH", "/usr/bin:/bin")
        return log, mock.patch.dict(os.environ, {"PATH": path})

    def calls(self, log):
        with open(log, encoding="utf-8") as handle:
            return [line.rstrip("\n").rstrip("\t").split("\t") for line in handle if line.strip()]

    # -- the classes and R1

    def test_known_classes(self):
        got = self.one("A")
        self.assertEqual(got["commits"], 4)
        self.assertEqual({k: n for k, n in got["lines"].items() if n},
                         {"product": 5, "test": 3, "charter": 4})
        self.assertEqual(got["vendor"], 7)
        self.assertEqual(sorted(got["lines"]), sorted(
            ["charter", "history", "packets", "design", "handoff", "nice", "other", "test",
             "product"]))
        from decisions import analyze
        for path, cls in (("docs/a.md", "design"), ("README.md", "other"), ("go.sum", "vendor"),
                          ("a/dist/b.js", "vendor"), ("a/x_test.go", "test"),
                          ("history/sittings/x.md", "charter"), ("history/y.md", "history"),
                          ("design/packets/p.md", "packets"), ("design/d.md", "design"),
                          ("HANDOFF.md", "handoff"), ("NICE_TO_HAVE.md", "nice"),
                          ("a/README.md", "product"), ("node_modules/x/test_a.py", "vendor"),
                          ("tests/a.py", "test"), ("conftest.py", "test")):
            self.assertEqual(analyze.path_class(path), cls, path)
        self.assertEqual((analyze.percent(1, 8), analyze.percent(1, 3)), (13, 33))
        self.assertEqual(self.text(self.repo("A")).splitlines()[-1], NOT_COMPUTED)

    def test_known_no_landing(self):
        out = self.text(self.repo("A"))
        self.assertEqual(out.splitlines(), [
            "churn  2026-10-26T00:00:00Z..2026-11-09T00:00:00Z",
            "== A  commits 4  landings 0  records 33% of 12 lines  record commits 1, - a landing"
            "  charters 1: median 1 commits, 1 charter-only  NICE - - -",
            "not measured: R2 (no merge on the first-parent line)",
            "not measured: R4 filed and closed (no NICE_TO_HAVE.md at 2026-10-26)",
            NOT_COMPUTED])
        self.assertEqual(self.text("churn", self.repo("A")), out)
        here = os.getcwd()
        os.chdir(os.path.join(self.repo("A"), "src"))
        try:
            self.assertEqual(self.text(), out)
        finally:
            os.chdir(here)
        got = self.one("A")
        self.assertEqual((got["landings"], got["record_commits"]), (0, 1))
        self.assertEqual(got["charters"]["count"], 1)
        self.assertEqual(got["charters"]["median"], 1)

    # -- R2 and R3

    def test_known_landing_and_rename(self):
        got = self.one("B")
        self.assertEqual((got["commits"], got["landings"], got["record_commits"]), (5, 1, 4))
        self.assertEqual({k: n for k, n in got["lines"].items() if n},
                         {"charter": 7, "packets": 6, "handoff": 9, "product": 1})
        line = self.text(self.repo("B")).splitlines()[1]
        self.assertIn("  records 96% of 23 lines  ", line)
        self.assertIn("  record commits 4, 4.0 a landing  ", line)

    def test_known_charters(self):
        self.assertEqual(self.one("B")["charters"], {
            "count": 2, "median": 2.5, "max": 4,
            "alone": {"commits": 2, "median": 1, "max": 2}})
        self.assertIn("  charters 2: median 2.5 commits, 1 charter-only  ",
                      self.text(self.repo("B")).splitlines()[1])

    def test_known_json(self):
        got = self.view(self.repo("B"))
        self.assertEqual(sorted(got), ["churn", "since", "until"])
        self.assertEqual((got["since"], got["until"]),
                         ("2026-10-26T00:00:00Z", "2026-11-09T00:00:00Z"))
        churn = got["churn"]
        self.assertEqual(sorted(churn), ["all", "not_computed", "repos", "skipped"])
        self.assertIsNone(churn["all"])
        self.assertEqual(churn["skipped"], [])
        self.assertEqual(churn["not_computed"], ["tokens", "account spend",
                                                 "work redone at a respawn",
                                                 "rows built and never landed"])
        repo = churn["repos"][0]
        self.assertEqual(sorted(repo), sorted(
            ["repo", "head", "commits", "landings", "lines", "vendor", "record_commits",
             "charters", "nice", "not_measured"]))
        self.assertEqual(sorted(repo["charters"]), ["alone", "count", "max", "median"])
        self.assertEqual(sorted(repo["charters"]["alone"]), ["commits", "max", "median"])
        self.assertEqual(sorted(repo["nice"]), ["closed", "filed", "moved", "rising",
                                                "snapshots"])
        self.assertEqual([sorted(s) for s in repo["nice"]["snapshots"]],
                         [["at", "commit", "form", "items"]] * 3)
        self.assertEqual(repo["repo"], os.path.realpath(self.repo("B")))
        self.assertTrue(re.match(r"^[0-9a-f]{40}$", repo["head"]), repo["head"])
        self.assertEqual(repo["not_measured"], ["R4 filed and closed (no NICE_TO_HAVE.md at "
                                                "2026-10-26)"])

    # -- R4

    def test_known_rows(self):
        line = self.text(self.repo("C")).splitlines()[1]
        self.assertTrue(line.endswith("  NICE 2 3 5 +5 -1 moved 1 rising"), line)
        nice = self.one("C")["nice"]
        self.assertEqual((nice["filed"], nice["closed"], nice["moved"], nice["rising"]),
                         (5, 1, 1, True))

    def test_known_first_parent(self):
        snaps = self.one("C")["nice"]["snapshots"]
        self.assertEqual([(s["at"], s["form"], s["items"]) for s in snaps], [
            ("2026-10-26T00:00:00Z", "rows", 2), ("2026-11-02T00:00:00Z", "rows", 3),
            ("2026-11-09T00:00:00Z", "rows", 5)])
        # without --first-parent the middle snapshot is the side branch's, 4 rows
        sha = subprocess.run([GIT, "rev-list", "-1", "--before=2026-11-02T00:00:00Z", "HEAD"],
                             cwd=self.repo("C"), capture_output=True, text=True).stdout.strip()
        body = subprocess.run([GIT, "show", sha + ":NICE_TO_HAVE.md"], cwd=self.repo("C"),
                              capture_output=True, text=True).stdout
        self.assertEqual(len(decisions.nice_items(body)), 4)
        self.assertNotEqual(sha[:7], snaps[1]["commit"][:7])

    def test_known_bullets(self):
        out = self.text(self.repo("D")).splitlines()
        self.assertTrue(out[1].endswith("  NICE 3b 1 2"), out[1])
        self.assertIn("not measured: R4 filed and closed (bullets at 2026-10-26: a bullet has "
                      "no id)", out)
        code, later, err = self.run_cli(self.repo("D"), "--since", "2026-11-02", "--until",
                                        "2026-11-09")
        self.assertEqual(code, 0, err)
        self.assertTrue(later.splitlines()[1].endswith("  NICE 1 2 +1 -0"), later)

    def test_known_empty(self):
        out = self.text(self.repo("E")).splitlines()
        self.assertEqual(out[1], "== E  commits 0  landings 0  records -  record commits 0, "
                                 "- a landing  charters -  NICE - - -")
        self.assertEqual(out[2:6], [
            "not measured: R1 (no line changed)",
            "not measured: R2 (no merge on the first-parent line)",
            "not measured: R3 (no charter changed)",
            "not measured: R4 filed and closed (no NICE_TO_HAVE.md at 2026-10-26)"])
        got = self.one("E")
        self.assertEqual(got["charters"], {"count": 0, "median": None, "max": None,
                                           "alone": {"commits": 0, "median": None,
                                                     "max": None}})
        self.assertEqual([got["nice"][k] for k in ("filed", "closed", "moved", "rising")],
                         [None] * 4)

    def test_known_all(self):
        out = self.text(self.repo("A"), self.repo("B")).splitlines()
        self.assertIn("== all 2  commits 9  landings 1  records 74% of 35 lines  record "
                      "commits 5, 5.0 a landing", out)
        got = self.view(self.repo("A"), self.repo("B"))["churn"]["all"]
        self.assertEqual((got["commits"], got["landings"], got["record_commits"]), (9, 1, 5))
        self.assertEqual(sum(got["lines"].values()), 35)

    # -- exits, git, the bound, read-only

    def test_known_exits(self):
        plain = os.path.join(self.tmp, "plain")
        os.makedirs(plain)
        fresh = Fixture(os.path.join(self.tmp, "fresh")).root
        code, out, err = self.run_cli(plain, fresh, *WINDOW)
        self.assertEqual(code, 0, err)
        self.assertIn("== plain  not a git work tree", out.splitlines())
        self.assertIn("== fresh  no commit", out.splitlines())
        skipped = self.view(plain, fresh)["churn"]["skipped"]
        self.assertEqual(skipped, [{"repo": os.path.realpath(plain), "why": "not a git work tree"},
                                   {"repo": os.path.realpath(fresh), "why": "no commit"}])
        for argv in ([os.path.join(self.tmp, "absent")] + WINDOW,
                     ["nosuch"] + WINDOW,
                     [plain, "--since", "yesterday"],
                     [plain, "--since", "2026-13-01"],
                     [plain, "--until", "14d"],
                     [plain, "--since", "2026-11-10", "--until", "2026-11-09"]):
            with self.subTest(argv=argv):
                code, out, err = self.run_cli(*argv)
                self.assertEqual((code, out), (2, ""), err)
                self.assertTrue(err, argv)

    def test_known_dates(self):
        log, patch = self.logging_git()
        with patch:
            code, _, err = self.run_cli(self.repo("C"), *WINDOW)
            self.assertEqual(code, 0, err)
            code, _, err = self.run_cli(self.repo("C"), "--since", "7d")
            self.assertEqual(code, 0, err)
        dated = [a for call in self.calls(log) for a in call
                 if a.startswith(("--since=", "--until=", "--before="))]
        self.assertTrue(any(a.startswith("--before=") for a in dated), dated)
        self.assertTrue(any(a.startswith("--since=") for a in dated), dated)
        for arg in dated:
            self.assertTrue(STAMP.match(arg.split("=", 1)[1]), arg)

    def test_known_git_verbs(self):
        log, patch = self.logging_git()
        with patch:
            for name in "ABCDE":
                code, _, err = self.run_cli(self.repo(name), *WINDOW)
                self.assertEqual(code, 0, err)
        verbs = set()
        for call in self.calls(log):
            i = 0
            while i < len(call) and call[i].startswith("-"):
                i += 2 if call[i] in ("-c", "-C") else 1
            verbs.add(call[i] if i < len(call) else "")
        self.assertTrue(verbs)
        self.assertLessEqual(verbs, VERBS)

    def test_known_timeout(self):
        hung = os.path.join(self.tmp, "hung")
        shutil.copytree(self.repo("A"), hung)
        body = ('case "$(pwd -P)" in */hung) for a in "$@"; do [ "$a" = log ] && '
                'exec sleep 30; done;; esac')
        _, patch = self.logging_git(body)
        start = time.monotonic()
        with patch, mock.patch.object(common, "GIT_TIMEOUT", 1):
            code, out, err = self.run_cli(hung, self.repo("B"), *WINDOW)
        self.assertLess(time.monotonic() - start, 10)
        self.assertEqual(code, 0, err)
        lines_out = out.splitlines()
        self.assertIn("== hung  timed out after 1 s (git log)", lines_out)
        self.assertFalse([line for line in lines_out
                          if "hung" in line and "records" in line], out)
        self.assertTrue(any(line.startswith("== B  commits 5") for line in lines_out), out)
        self.assertFalse(any(line.startswith("== all") for line in lines_out), out)

    def test_known_writes_nothing(self):
        before = {name: snapshot(self.repo(name)) for name in "ABCD"}
        self.assertTrue(all(any(p.startswith(".git" + os.sep) for p in snap)
                            for snap in before.values()))
        repos = [self.repo(name) for name in "ABCD"]
        code, out, err = self.run_cli(*(repos + WINDOW))
        self.assertEqual(code, 0, err)
        self.assertIn("== all 4", out)
        code, out, err = self.run_cli(*(repos + WINDOW + ["--json"]))
        self.assertEqual(code, 0, err)
        self.assertEqual(len(json.loads(out)["churn"]["repos"]), 4)
        self.assertEqual({name: snapshot(self.repo(name)) for name in "ABCD"}, before)


class TurnAnalyze(Hermetic):
    """d32: analyze measures the CLAUDE.md block at both ends of the window."""

    def setUp(self):
        super().setUp()
        self.top = tempfile.mkdtemp(prefix="decisions-d32-")
        self.addCleanup(shutil.rmtree, self.top, True)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["analyze"] + list(argv) + WINDOW, out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def test_every_turn_analyze_measures_the_block(self):
        small = "%s\nGenerated.\n\n1. **One.** One. (2026-09-01)\n%s\n" % (BEGIN, END)
        large = small.replace("One. (", "One. Two more words. (")
        f = Fixture(os.path.join(self.top, "F"))
        f.commit("2026-10-20", {"CLAUDE.md": "# F\n\n" + small})
        f.commit("2026-11-05", {"CLAUDE.md": "# F\n\n" + large + "tail\n"})
        g = Fixture(os.path.join(self.top, "G"))
        g.commit("2026-10-20", {"src/app.py": "x\n"})
        code, out, err = self.run_cli(f.root, g.root, "--json")
        self.assertEqual(code, 0, err)
        repos = json.loads(out)["churn"]["repos"]
        a, b = len(small.encode()), len(large.encode())
        self.assertEqual(repos[0]["block"], {"start": a, "end": b})
        self.assertEqual(repos[1]["block"], {"start": None, "end": None})
        code, out, err = self.run_cli(f.root, g.root)
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        at = next(i for i, line in enumerate(lines) if line.startswith("== F "))
        self.assertEqual(lines[at + 1], "block  %d B to %d B, +%d B" % (a, b, b - a))
        self.assertEqual(len([line for line in lines if line.startswith("block ")]), 1)
