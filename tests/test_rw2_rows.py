"""rw2 (agentik-hq design/16 section 4 items 5 and 6): `rows [check] [--json] [--root DIR]
[REPO...]` reads each build row's stage from its record folder and from git, and `rows check`
holds the records against git. Every home, repo and row is made here under the temp folder,
with made-up names."""

import hashlib
import io
import json
import os
import subprocess

import decisions
from decisions.rows import GATE_STATUS, KEYS, SCHEMA
from tests.test_d39_backlog_check import DATE, Orchard, commit, git

ROW = """# Row {name}: a made-up row

| item | value |
|---|---|
| repo | {repo} |
| level | {level} |
| from | {frm} |
| base | main |
| depends_on | {depends} |
{branch}| done | {done} |

Prose about the row.

## Owed
{owed}
"""


class Rows(Orchard):
    """The home `orchard-hq` holds `history/rows`; its member `pear` holds the branches."""

    def setUp(self):
        super().setUp()
        self.root = os.path.join(self.hq, "history", "rows")
        os.makedirs(self.root)

    def row(self, name, repo="pear", level="S3", frm="design/09 section 2", depends="none",
            done="", branch=None, owed=("- [ ] the install once it lands",)):
        branch = "| branch | %s |\n" % branch if branch is not None else ""
        self.put(os.path.join(self.root, name, "row.md"), ROW.format(
            name=name, repo=repo, level=level, frm=frm, depends=depends, done=done,
            branch=branch, owed="\n".join(owed)))
        self.put(os.path.join(self.root, name, "brief.md"), "# Brief\n")

    def record(self, name, file, **cells):
        kind = file.split("-")[0].capitalize()
        body = "".join("| %s | %s |\n" % (k, v) for k, v in cells.items())
        self.put(os.path.join(self.root, name, file), "# %s of %s\n\n| item | value |\n"
                 "|---|---|\n%s\nWhat changed, in prose.\n" % (kind, name, body))

    def build(self, name, n, head, stage="first build", gate="20261113-0001 exit 0"):
        self.record(name, "build-%d.md" % n, stage=stage, head=head, gate=gate)

    def review(self, name, n, span, blocks="none", ruling=""):
        self.record(name, "review-%d.md" % n, slice=span, blocks=blocks, ruling=ruling)

    def rows(self, *argv, repos=()):
        """(exit, stdout, stderr) of `rows --root ROOT [options] [check] [REPO...]`."""
        words = [a for a in argv if not a.startswith("--")]
        flags = [a for a in argv if a.startswith("--")]
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["rows", "--root", self.root] + flags + words + list(repos),
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def view(self, *argv, repos=()):
        code, out, err = self.rows("--json", *argv, repos=repos)
        self.assertEqual(code, 0, out + err)
        got = json.loads(out)
        self.assertEqual((got["schema"], got["ok"]), (SCHEMA, True))
        return {r["row"]: r for r in got["rows"]}

    def checked(self, *argv, repos=()):
        code, out, err = self.rows("check", *argv, repos=repos)
        self.assertIn(code, (0, 1), err)
        return code, out

    def on_branch(self, name, *files, repo=None):
        """Commit `files` on branch `name` of pear (made from main when absent); its tip."""
        repo = repo or self.pear
        exists = git(repo, "branch", "--list", name)
        git(repo, "checkout", "-q", name) if exists else git(repo, "checkout", "-q", "-b", name,
                                                             "main")
        tip = None
        for f in files:
            tip = commit(repo, f)
        git(repo, "checkout", "-q", "main")
        return tip or git(repo, "rev-parse", name)

    def base(self, name):
        return git(self.pear, "merge-base", "main", name)


class Words(Rows):
    """Acceptance 1: one row through every word, `--json` at each step, never stale."""

    def step(self, want, text=None, command=None, record=None):
        got = self.view()["p3-basket"]
        self.assertEqual(got["state"], want, got)
        if text is not None:
            self.assertEqual(got["next"]["text"], text)
        self.assertEqual(got["next"]["command"], command)
        if record is not None:
            self.assertEqual(got["record"], record)
        self.assertEqual(got["stale"], [])
        code, out = self.checked()
        self.assertEqual(code, 0, out)
        self.assertIn(": 0 stale", out)
        return got

    def test_one_row_through_every_word(self):
        folder = os.path.join(os.path.realpath(self.root), "p3-basket")
        self.row("p0-cart")
        self.row("p3-basket", depends="p0-cart")
        got = self.step("waits", "p0-cart", record="row.md")
        self.assertEqual(got["waits"], ["p0-cart"])
        self.row("p0-cart", done="landed, pushed")
        self.step("briefed", os.path.join(folder, "brief.md"))
        tip1 = self.on_branch("p3-basket", "basket-1.txt")
        self.step("building", None, GATE_STATUS)
        self.build("p3-basket", 1, tip1)
        base = self.base("p3-basket")
        self.step("built", "review 1: %s..%s" % (base[:7], tip1[:7]), record="build-1.md")
        self.review("p3-basket", 1, "%s..%s" % (base[:7], tip1[:7]), blocks="F1, F2")
        self.step("to rule", os.path.join(folder, "review-1.md"), record="review-1.md")
        self.review("p3-basket", 1, "%s..%s" % (base[:7], tip1[:7]), blocks="F1, F2",
                    ruling="fix: F1 and F2, each with its test")
        self.step("to fix", "p3-basket: F1, F2")
        tip2 = self.on_branch("p3-basket", "basket-2.txt")
        self.build("p3-basket", 2, tip2, stage="fix of review 1")
        self.step("built", "review 2: %s..%s" % (tip1[:7], tip2[:7]), record="build-2.md")
        self.review("p3-basket", 2, "%s..%s" % (tip1[:7], tip2[:7]), ruling="closed: all mended")
        merge = os.path.join(folder, "merge.txt")
        self.step("reviewed", merge, record="review-2.md")
        commit(self.pear, "main-moves.txt")
        self.step("reviewed", "phase 2: merge main into p3-basket")
        git(self.pear, "checkout", "-q", "p3-basket")
        git(self.pear, "merge", "-q", "--no-ff", "-m", "Merge main into p3-basket", "main")
        git(self.pear, "checkout", "-q", "main")
        tip3 = git(self.pear, "rev-parse", "p3-basket")
        self.build("p3-basket", 3, tip3, stage="phase 2")
        self.step("reviewed", merge)
        self.put(merge, "Merge p3-basket: the basket\n")
        self.step("ready", None, "agentik session gate land %s %s %s %s"
                  % (os.path.realpath(self.pear), "p3-basket", tip3, merge), "merge.txt")
        git(self.pear, "merge", "-q", "--no-ff", "-m", "Merge p3-basket: the basket", "p3-basket")
        landing = git(self.pear, "rev-parse", "main")
        self.step("landed", "push pear's main")
        git(self.pear, "update-ref", "refs/remotes/origin/main", "main")
        self.step("pushed", "1 owed")
        self.row("p3-basket", owed=("- [x] the install once it lands",))
        self.step("pushed", "type done: %s %s" % (DATE, landing[:7]))


class Cells(Rows):
    """Acceptance 2: cells as hands write them give the same words; past and dirty."""

    def test_hand_written_cells_read_as_plain_ones(self):
        tip = self.on_branch("p4-crate", "crate-1.txt")
        self.row("p4-plain", branch="p4-crate")
        self.build("p4-plain", 1, tip)
        self.row("p4-hand", branch="`p4-crate` (cut from main at the pin)")
        self.build("p4-hand", 1, "`%s` (the check ran on the tree of the commit before)" % tip[:7],
                   gate="`20261113-0001 exit 0` (452 tests, the floor too)")
        got = self.view()
        plain, hand = got["p4-plain"], got["p4-hand"]
        for key in ("state", "branch", "tip", "gate", "past", "stale"):
            self.assertEqual(plain[key], hand[key], key)
        self.assertEqual(plain["next"], hand["next"])
        self.assertEqual(hand["head"], tip[:7])
        self.assertEqual(hand["gate"], {"id": "20261113-0001", "exit": 0})
        self.build("p4-hand", 1, tip, gate="20261113-0002 running (since noon)")
        self.assertEqual(self.view()["p4-hand"]["gate"], {"id": "20261113-0002", "exit": None})
        self.build("p4-hand", 1, tip, gate="none: a records-only change")
        self.assertIsNone(self.view()["p4-hand"]["gate"])

    def test_past_and_dirty(self):
        tip = self.on_branch("p4-crate", "crate-1.txt")
        self.row("p4-crate")
        self.build("p4-crate", 1, tip)
        self.assertEqual(self.view()["p4-crate"]["worktree"], None)
        tree = os.path.join(self.tmp, "pear-crate")
        git(self.pear, "worktree", "add", "-q", tree, "p4-crate")
        commit(tree, "crate-2.txt")
        commit(tree, "crate-3.txt")
        self.put(os.path.join(tree, "loose.txt"), "loose\n")
        got = self.view()["p4-crate"]
        self.assertEqual((got["past"], got["dirty"]), (2, 1))
        self.assertEqual(got["worktree"], os.path.realpath(tree))


class Text(Rows):
    """Acceptance 6: a row's keys, the text view, no root, `--help`."""

    def test_a_row_holds_exactly_the_keys(self):
        self.row("p3-basket")
        self.assertEqual(tuple(self.view()["p3-basket"]), KEYS)
        self.assertEqual(len(KEYS), 19)

    def test_the_text_view(self):
        tip = self.on_branch("p4-crate", "crate-1.txt")
        self.row("p4-crate")
        self.build("p4-crate", 1, tip, gate="20261113-0007 exit 0")
        self.row("p5-gone")
        self.build("p5-gone", 1, tip)
        self.row("p6-new")
        code, out, _ = self.rows()
        self.assertEqual(code, 0)
        base = self.base("p4-crate")
        self.assertEqual(out.splitlines(), [
            "p4-crate  S3 pear  built  tip %s  gate 20261113-0007 exit 0  next: review 1: %s..%s"
            % (tip[:7], base[:7], tip[:7]),
            "p5-gone  S3 pear  built  gate 20261113-0001 exit 0  next: review 1: ?..%s" % tip[:7],
            "  stale: branch p5-gone is gone and no merge names it",
            "p6-new  S3 pear  briefed  next: %s" % os.path.join(os.path.realpath(self.root),
                                                               "p6-new", "brief.md")])

    def test_no_open_rows(self):
        code, out, _ = self.rows()
        self.assertEqual((code, out), (0, "no open rows under %s\n" % os.path.realpath(self.root)))

    def test_no_root_exits_2_and_says_why_under_json(self):
        missing = os.path.join(self.tmp, "no-such-rows")
        for argv in ([], ["check"]):
            out, err = io.StringIO(), io.StringIO()
            code = decisions.main(["rows", "--root", missing] + argv, out=out, err=err)
            self.assertEqual((code, out.getvalue()), (2, ""))
            self.assertIn("is not a directory", err.getvalue())
            out = io.StringIO()
            code = decisions.main(["rows", "--root", missing, "--json"] + argv, out=out,
                                  err=io.StringIO())
            got = json.loads(out.getvalue())
            self.assertEqual(code, 2)
            self.assertEqual((got["schema"], got["ok"]), (SCHEMA, False))
            self.assertEqual(sorted(got["error"]), ["code", "message", "remedy"])

    def test_help_lists_rows_within_100_characters(self):
        out = io.StringIO()
        self.assertEqual(decisions.main(["--help"], out=out, err=io.StringIO()), 0)
        self.assertIn("rows [check] [--json] [--root DIR] [REPO...]", out.getvalue())
        out = io.StringIO()
        self.assertEqual(decisions.main(["rows", "--help"], out=out, err=io.StringIO()), 0)
        self.assertIn("--root DIR", out.getvalue())
        for text in (out.getvalue(), decisions.cli.__doc__):
            self.assertTrue(all(len(l) <= 100 for l in text.splitlines()))


class Stale(Rows):
    """Acceptance 3: each contradiction of R7, one at a time, red and then mended."""

    def red_then_mended(self, line, mend):
        code, out = self.checked()
        self.assertEqual(code, 1, out)
        self.assertIn(line, out.splitlines())
        self.assertIn(": 1 stale", out)
        self.assertEqual(self.rows()[0], 0)
        mend()
        code, out = self.checked()
        self.assertEqual(code, 0, out)
        self.assertTrue(out.endswith(": 0 stale\n"), out)

    def test_a_head_off_the_branch(self):
        tip = self.on_branch("p4-crate", "crate-1.txt")
        self.row("p4-crate")
        self.build("p4-crate", 1, self.side[:7])
        self.red_then_mended("p4-crate  stale: head %s of build-1.md is not on p4-crate"
                             % self.side[:7], lambda: self.build("p4-crate", 1, tip))

    def test_a_slice_end_off_the_branch(self):
        tip = self.on_branch("p4-crate", "crate-1.txt")
        self.row("p4-crate")
        self.build("p4-crate", 1, tip)
        self.review("p4-crate", 1, "%s..%s" % (tip[:7], self.side[:7]))
        self.red_then_mended(
            "p4-crate  stale: slice end %s of review-1.md is not on p4-crate" % self.side[:7],
            lambda: self.review("p4-crate", 1, "%s..%s" % (self.base("p4-crate")[:7], tip[:7])))

    def test_a_level_against_the_build_order(self):
        self.table((4, "pear", "open"))
        self.row("p4-crate", level="S2", frm="HANDOFF 4 (the crate)")
        self.red_then_mended("p4-crate  stale: level S2 differs from HANDOFF 4's S3",
                             lambda: self.row("p4-crate", level="S3", frm="HANDOFF 4"))

    def test_a_level_against_the_nice_rows(self):
        self.put(os.path.join(self.pear, "NICE_TO_HAVE.md"), "# Nice\n\n"
                 "| id | level | area | finding | evidence | from |\n|---|---|---|---|---|---|\n"
                 "| n3 | S3 | `a.py` | A finding | x | y |\n| n5 | S2 | `b.py` | Another | x | y |\n")
        self.row("p4-crate", level="S3", frm="pear n3, n5")
        self.red_then_mended("p4-crate  stale: level S3 differs from pear n3, n5's S2",
                             lambda: self.row("p4-crate", level="S3", frm="pear n3, n9"))

    def test_a_branch_gone_with_no_merge(self):
        tip = self.on_branch("p4-crate", "crate-1.txt")
        git(self.pear, "branch", "-q", "-D", "p4-crate")
        self.row("p4-crate")
        self.build("p4-crate", 1, tip)
        self.red_then_mended("p4-crate  stale: branch p4-crate is gone and no merge names it",
                             lambda: git(self.pear, "branch", "-q", "p4-crate", tip))

    def test_a_done_sha_off_main(self):
        self.row("p1-done", done="%s %s" % (DATE, self.side[:7]))
        self.row("h1-done", repo="hq", done="%s `%s` (hq main)" % (DATE, self.hq_plain[:7]))
        self.red_then_mended(
            "p1-done  stale: done %s is not on main's first-parent line" % self.side[:7],
            lambda: self.row("p1-done", done="%s %s" % (DATE, self.p2_merge[:7])))


class Skipped(Rows):
    """Acceptance 4: an absent repo, a folder that is no checkout, a REPO named."""

    def test_absent_and_no_checkout(self):
        os.makedirs(os.path.join(self.tmp, "fig"))
        self.row("f1-fig", repo="fig")
        self.row("m1-plum", repo="plum")
        self.row("p4-crate")
        lines = ["skipped (no checkout): fig: f1-fig", "skipped (absent): plum: m1-plum"]
        code, out, _ = self.rows()
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[-2:], lines)
        code, out = self.checked()
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[-3:-1], lines)
        self.assertEqual(list(self.view()), ["p4-crate"])
        _, out, _ = self.rows("--json")
        self.assertEqual(json.loads(out)["skipped"], [
            {"repo": "fig", "why": "no checkout", "rows": ["f1-fig"]},
            {"repo": "plum", "why": "absent", "rows": ["m1-plum"]}])

    def test_a_repo_named_skips_another(self):
        quince = os.path.join(self.tmp, "quince")
        os.makedirs(quince)
        git(quince, "init", "-q")
        commit(quince, "start.txt")
        self.row("q1-quince", repo="quince")
        self.row("p4-crate")
        self.assertEqual(sorted(self.view()), ["p4-crate", "q1-quince"])
        self.assertEqual(list(self.view(repos=[self.pear])), ["p4-crate"])
        code, out, _ = self.rows(repos=[self.pear])
        self.assertEqual(code, 0)
        self.assertIn("skipped (not named): quince: q1-quince", out.splitlines())


class Closed(Rows):
    """Acceptance 5: a withdrawn folder is in no list; a closed one is checked, not listed."""

    def test_withdrawn_and_closed(self):
        self.row("p7-dropped", done="withdrawn: the owner chose another way")
        self.row("p8-landed", done="landed, pushed")
        self.row("p9-old", done="%s %s" % (DATE, self.p2_merge[:7]))
        self.row("p4-crate")
        self.assertEqual(list(self.view()), ["p4-crate"])
        code, out, _ = self.rows("--json", "check")
        got = json.loads(out)
        self.assertEqual((code, got["checked"], got["stale"]), (0, 3, []))
        self.assertEqual([r["row"] for r in got["rows"]], ["p4-crate"])
        code, out = self.checked()
        self.assertEqual(out, "checked 3 rows under %s: 0 stale\n" % os.path.realpath(self.root))
        self.assertNotIn("p7-dropped", self.rows()[1])


class ReadOnly(Rows):
    """Acceptance 7: a read leaves the home and pear, `.git` included, byte for byte."""

    def tree(self):
        found = {}
        for top in (self.hq, self.pear, os.path.join(self.tmp, "pear-crate")):
            for folder, _, files in os.walk(top):
                for name in files:
                    path = os.path.join(folder, name)
                    with open(path, "rb") as handle:
                        found[path] = hashlib.sha256(handle.read()).hexdigest()
        return found

    def test_a_read_writes_nothing(self):
        tip = self.on_branch("p4-crate", "crate-1.txt")
        self.row("p4-crate")
        self.build("p4-crate", 1, tip)
        self.review("p4-crate", 1, "%s..%s" % (self.base("p4-crate")[:7], tip[:7]),
                    ruling="closed")
        tree = os.path.join(self.tmp, "pear-crate")
        git(self.pear, "worktree", "add", "-q", tree, "p4-crate")
        self.put(os.path.join(tree, "crate-1.txt"), "changed\n")
        before = self.tree()
        for argv in ([], ["--json"], ["check"], ["--json", "check"]):
            self.assertIn(self.rows(*argv)[0], (0, 1))
        self.assertEqual(self.view()["p4-crate"]["dirty"], 1)
        self.assertEqual(self.tree(), before)


class Review1(Rows):
    """Review 1's mends: F1 the order of words and options, F2 a command quoted for a shell,
    F3 no control character in the text view, F4 a stage by its opening words, F5 a cell is
    the second cell, L1 an unreadable row.md skipped."""

    def ready(self, branch):
        """A row of `branch` under self.root that reads `ready`; its folder."""
        tip = self.on_branch(branch, "ready-1.txt")
        self.row("p1-ready", branch=branch)
        self.build("p1-ready", 1, tip)
        self.review("p1-ready", 1, "%s..%s" % (self.base(branch)[:7], tip[:7]), ruling="closed")
        folder = os.path.join(os.path.realpath(self.root), "p1-ready")
        self.put(os.path.join(folder, "merge.txt"), "Merge it\n")
        return tip, folder

    def pasted(self, command):
        """The arguments a stub `agentik` gets when `command` runs under `sh -c`."""
        bin_dir = os.path.join(self.tmp, "stub-bin")
        work = os.path.join(self.tmp, "stub-cwd")
        os.makedirs(work, exist_ok=True)
        got = os.path.join(self.tmp, "stub-argv.json")
        self.put(os.path.join(bin_dir, "agentik"), "#!/usr/bin/python3\nimport json, os, sys\n"
                 "open(os.environ['STUB_OUT'], 'w').write(json.dumps(sys.argv[1:]))\n")
        os.chmod(os.path.join(bin_dir, "agentik"), 0o755)
        subprocess.run(["/bin/sh", "-c", command], cwd=work, check=True, env={
            "PATH": bin_dir + ":/usr/bin:/bin", "STUB_OUT": got, "IFS": " "})
        self.assertEqual(os.listdir(work), [])
        with open(got, encoding="utf-8") as handle:
            return json.load(handle)

    def test_f1_words_and_options_in_any_order(self):
        self.row("p4-crate")
        self.row("q1-quince", repo="quince")
        forms = (["check", "--root", self.root, self.pear, "--json"],
                 ["--root", self.root, "check", self.pear, "--json"],
                 ["check", self.pear, "--root", self.root, "--json"])
        seen = []
        for form in forms:
            out, err = io.StringIO(), io.StringIO()
            code = decisions.main(["rows"] + form, out=out, err=err)
            self.assertEqual(code, 0, err.getvalue())
            seen.append(json.loads(out.getvalue()))
        self.assertEqual(seen[0], seen[1])
        self.assertEqual(seen[0], seen[2])
        self.assertEqual(seen[0]["skipped"][0]["why"], "not named")
        err = io.StringIO()
        code = decisions.main(["analyze", "churn", "--json", self.pear], out=io.StringIO(),
                              err=err)
        self.assertEqual(code, 2)
        self.assertIn("unrecognized arguments", err.getvalue())

    def test_f2_the_land_command_pastes_as_four_words(self):
        branch = "p1;echo$IFS'x\""
        for name, view in (("my rows;$HOME 'q\"", "text"), ("rows\nwith a newline", "json")):
            self.root = os.path.join(self.hq, name)
            os.makedirs(self.root)
            tip, folder = self.ready(branch)
            if view == "json":
                command = self.view()["p1-ready"]["next"]["command"]
            else:
                line = self.rows()[1].splitlines()[0]
                command = line.split("  next: ", 1)[1]
            self.assertEqual(self.pasted(command), [
                "session", "gate", "land", os.path.realpath(self.pear), branch, tip,
                os.path.join(folder, "merge.txt")])

    def test_f3_no_control_character_reaches_the_text_view(self):
        tip = self.on_branch("p2-fix", "fix-1.txt")
        name = "p2\x1b[31m-fix"
        self.row(name, branch="p2-fix")
        self.build(name, 1, tip)
        self.review(name, 1, "%s..%s" % (self.base("p2-fix")[:7], tip[:7]),
                    blocks="F1 \x1b]0;OWNED\x07\x1b[2J\x1b[31mred\x01", ruling="fix")
        self.row("p9-gone", branch="p9\x1b[2J-gone")
        self.build("p9-gone", 1, tip)
        for argv in ([], ["check"]):
            out = self.rows(*argv)[1]
            self.assertIn("gone", out)
            self.assertFalse([c for c in out if c != "\n" and (ord(c) < 32 or 127 <= ord(c) < 160)],
                             repr(out))
        self.assertIn("\x1b", self.view()["p2\x1b[31m-fix"]["next"]["text"])

    def test_f4_a_stage_by_its_opening_words(self):
        tip, folder = self.ready("p1-ready")
        commit(self.pear, "main-moves.txt")
        git(self.pear, "checkout", "-q", "p1-ready")
        git(self.pear, "merge", "-q", "--no-ff", "-m", "Merge main into p1-ready", "main")
        git(self.pear, "checkout", "-q", "main")
        tip2 = git(self.pear, "rev-parse", "p1-ready")
        self.build("p1-ready", 2, "`%s`" % tip2[:7], stage="`phase 2` (main merged in)")
        self.assertEqual(self.view()["p1-ready"]["state"], "ready")

    def test_f5_a_cell_is_the_second_cell(self):
        self.put(os.path.join(self.root, "p4-wide", "row.md"),
                 "# Row p4-wide\n\n| item | value | note |\n|---|---|---|\n"
                 "| repo | pear | the app |\n| level | S3 | |\n| depends_on | none | |\n"
                 "| done | | |\n")
        got = self.view()
        self.assertEqual(list(got), ["p4-wide"])
        self.assertEqual(got["p4-wide"]["repo"], "pear")

    def test_l1_an_unreadable_row_is_skipped(self):
        self.row("p4-crate")
        os.makedirs(os.path.join(self.root, "p8-binary"))
        with open(os.path.join(self.root, "p8-binary", "row.md"), "wb") as handle:
            handle.write(b"# Row \xff\xfe\n")
        code, out, _ = self.rows()
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[-1], "skipped (unreadable): p8-binary")
        code, out, _ = self.rows("--json", "check")
        got = json.loads(out)
        self.assertEqual((code, got["checked"], got["stale"]), (0, 1, []))
        self.assertEqual(got["skipped"], [{"repo": None, "why": "unreadable",
                                           "rows": ["p8-binary"]}])
        self.assertEqual([r["row"] for r in got["rows"]], ["p4-crate"])
