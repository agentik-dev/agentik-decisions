"""rw2 (agentik-hq design/16 section 4 items 5 and 6): `rows [check] [--json] [--root DIR]
[REPO...]` reads each build row's stage from its record folder and from git, and `rows check`
holds the records against git. Every home, repo and row is made here under the temp folder,
with made-up names."""

import hashlib
import io
import json
import os

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
