"""d39 (agentik-hq design/14 §3.2, §3.3): `backlog --check --order FILE [REPO...]` holds each
row's state cell against git, read with `git -C` and never written; `--write` moves a landed
`building` row out to the done file. R7: the owner's file linked into a checkout stays the
owner's. Every repo, HANDOFF and list is made here under the temp home, with made-up names."""

import io
import json
import os
import shutil
import subprocess
import tempfile

import decisions
from decisions.render import GATES
from tests.hermetic import Hermetic
from tests.test_d38_gate_layers import Home, lines

GIT = shutil.which("git") or "/usr/bin/git"
DATE = "2026-11-10"
HEADER = "| # | item | level | repo | where | state |\n|---|---|---|---|---|---|\n"
QUESTIONS = ("# Open questions\n\n## Open\n\n- 9. Whether the pear ripens\n\n"
             "## Answered\n\n- 4. Where the plums go: To the shed (2026-11-01; the owner)\n")
DONE_HEAD = ("# the build order's done items\n\n"
             "1 The first orchard row, done 2026-10-01 abc1234\n")


def git(repo, *argv):
    env = dict(os.environ, GIT_AUTHOR_DATE=DATE + " 12:00:00 +0000",
               GIT_COMMITTER_DATE=DATE + " 12:00:00 +0000")
    done = subprocess.run([GIT, "-C", repo, "-c", "user.name=f", "-c", "user.email=f",
                           "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]
                          + list(argv), env=env, capture_output=True, text=True, check=True)
    return done.stdout.strip()


def commit(repo, name):
    with open(os.path.join(repo, name), "w", encoding="utf-8") as handle:
        handle.write(name + "\n")
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", "add " + name)
    return git(repo, "rev-parse", "HEAD")


def branch(repo, name, merge=None, delete=False):
    """A branch of one commit off main; merged with `merge` as its message when given."""
    git(repo, "checkout", "-q", "-b", name, "main")
    tip = commit(repo, name.replace("/", "-") + ".txt")
    git(repo, "checkout", "-q", "main")
    if merge is not None:
        git(repo, "merge", "-q", "--no-ff", "-m", merge, name)
    if delete:
        git(repo, "branch", "-q", "-D", name)
    return tip, git(repo, "rev-parse", "HEAD")


class Orchard(Hermetic):
    """An hq checkout holding HANDOFF.md, and one member, `pear`, with its branches."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="decisions-d39-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.hq = os.path.join(self.tmp, "orchard-hq")
        self.pear = os.path.join(self.tmp, "pear")
        for repo in (self.hq, self.pear):
            os.makedirs(repo)
            git(repo, "init", "-q")
        self.hq_plain = commit(self.hq, "start.txt")
        commit(self.pear, "start.txt")
        branch(self.pear, "p1-live")
        _, self.p2_merge = branch(self.pear, "p2-done", merge="Merge p2-done: the drain")
        branch(self.pear, "g2")
        branch(self.pear, "g2b-edit-gates", merge="Merge g2b-edit-gates: the gates")
        _, self.p5_merge = branch(self.pear, "p5-quiet", merge="Fold the orchard work")
        branch(self.pear, "p6-gone", merge="Fold more", delete=True)
        self.side, _ = branch(self.pear, "side")
        self.pear_plain = commit(self.pear, "plain.txt")
        self.handoff = os.path.join(self.hq, "HANDOFF.md")
        self.done = os.path.join(self.hq, "history", "handoff-done.md")
        self.put(os.path.join(self.hq, "OPEN-QUESTIONS.md"), QUESTIONS)

    def put(self, path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)

    def table(self, *rows):
        """HANDOFF.md with `rows`, each (n, repo, state)."""
        body = "".join("| %d | Row %d of the orchard | S3 | %s | `x.md` | %s |\n" % (n, n, repo, s)
                       for n, repo, s in rows)
        self.put(self.handoff, "# Handoff\n\n## The build order\n\n" + HEADER + body
                 + "\n## After\n\nProse.\n")

    def check(self, *argv, repos=None):
        out, err = io.StringIO(), io.StringIO()
        named = [self.pear] if repos is None else list(repos)
        code = decisions.main(["backlog", "--check", "--order", self.handoff] + named
                              + list(argv), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def reds(self, *rows, repos=None):
        """{n: red or None} of `rows` checked, by --json, and the exit."""
        self.table(*rows)
        code, out, err = self.check("--json", repos=repos)
        self.assertIn(code, (0, 1), err)
        got = json.loads(out)
        return {r["n"]: r["red"] for r in got["rows"]}, code

    def bytes_of(self, *paths):
        found = []
        for path in paths:
            with open(path, "rb") as handle:
                found.append(handle.read())
        return found


class Reds(Orchard):
    """Acceptance 1: each red of R3, and the clean cell beside it."""

    def test_building_a_live_branch_is_clean_and_a_gone_one_is_stale(self):
        got, code = self.reds((1, "pear", "building p1-live"), (2, "pear", "building p9-none"))
        self.assertEqual(got, {1: None, 2: "stale: branch gone"})
        self.assertEqual(code, 1)

    def test_building_a_merged_branch_is_landed(self):
        got, code = self.reds((1, "pear", "building p2-done"))
        self.assertEqual(got, {1: "stale: landed %s %s" % (self.p2_merge[:7], DATE)})
        self.assertEqual(code, 1)

    def test_done_on_main_is_clean_and_off_it_red(self):
        got, code = self.reds((1, "pear", "done %s %s" % (DATE, self.p2_merge[:7])),
                              (2, "pear", "done %s %s" % (DATE, self.side[:7])),
                              (3, "pear", "done %s %s" % (DATE, self.pear_plain[:7])),
                              (4, "hq", "done %s %s" % (DATE, self.hq_plain[:7])))
        self.assertIsNone(got[1])
        self.assertTrue(got[2] and got[2].startswith("stale"), got)
        self.assertTrue(got[3] and got[3].startswith("stale"), got)
        self.assertIsNone(got[4])
        self.assertEqual(code, 1)

    def test_waiting_on_an_answered_question_is_red(self):
        got, code = self.reds((1, "hq", "waiting: owner 4; the shed"), (2, "hq", "waiting: owner 9"))
        self.assertEqual(got, {1: "answered", 2: None})
        self.assertEqual(code, 1)

    def test_waiting_on_a_row_gone_is_resolved(self):
        got, _ = self.reds((1, "suite", "waiting: row 2"), (2, "suite", "waiting: row 30"))
        self.assertEqual(got, {1: None, 2: "resolved"})

    def test_waiting_on_a_branch_is_checked_as_building(self):
        got, _ = self.reds((1, "suite", "waiting: pear p1-live; its review"),
                           (2, "suite", "waiting: pear p2-done"),
                           (3, "suite", "waiting: pear p9-none"))
        self.assertEqual(got, {1: None, 2: "stale: landed %s %s" % (self.p2_merge[:7], DATE),
                               3: "stale: branch gone"})

    def test_the_owners_text_and_watch_are_never_red(self):
        got, code = self.reds((1, "hq", "waiting: the owner: picks the pears"),
                              (2, "pear", "watch: the first frost"), (3, "pear", "open"))
        self.assertEqual(got, {1: None, 2: None, 3: None})
        self.assertEqual(code, 0)

    def test_a_suite_row_building_another_repos_branch(self):
        got, _ = self.reds((1, "suite", "building pear p2-done"), (2, "suite", "building pear g2"))
        self.assertEqual(got, {1: "stale: landed %s %s" % (self.p2_merge[:7], DATE), 2: None})

    def test_the_text_view_prints_one_line_a_red(self):
        self.table((1, "pear", "building p1-live"), (2, "pear", "building p9-none; later"))
        code, out, err = self.check()
        self.assertEqual(code, 1, err)
        red = [l for l in out.splitlines() if "stale" in l and l.startswith("2")]
        self.assertEqual(len(red), 1, out)
        self.assertIn("building p9-none", red[0])
        self.assertNotIn("p1-live", out)


class Landed(Orchard):
    """Acceptance 2: the whole name, the branch's tip, and §5's unprovable case."""

    def test_g2_is_not_landed_by_g2bs_merge(self):
        got, _ = self.reds((1, "pear", "building g2"))
        self.assertEqual(got, {1: None})

    def test_an_otherwise_worded_merge_of_the_tip_is_landed(self):
        got, _ = self.reds((1, "pear", "building p5-quiet"))
        self.assertEqual(got, {1: "stale: landed %s %s" % (self.p5_merge[:7], DATE)})

    def test_a_deleted_branch_after_an_unnamed_merge_is_gone(self):
        got, _ = self.reds((1, "pear", "building p6-gone"))
        self.assertEqual(got, {1: "stale: branch gone"})


class Skipped(Orchard):
    """Acceptance 3: an absent repo is skipped and named; with no REPO, hq and suite only."""

    def test_a_row_whose_repo_is_absent_is_skipped_and_named(self):
        self.table((1, "pear", "building p1-live"), (2, "plum", "building p9-none"))
        absent = os.path.join(self.tmp, "plum")
        code, out, err = self.check(repos=[self.pear, absent])
        self.assertEqual(code, 0, out + err)
        skip = [l for l in out.splitlines() if l.startswith("skipped")]
        self.assertEqual(len(skip), 1, out)
        self.assertIn("2 plum", skip[0])

    def test_no_repo_named_reads_the_hq_and_suite_rows_only(self):
        self.table((1, "pear", "building p9-none"), (2, "hq", "waiting: owner 9"),
                   (3, "suite", "waiting: row 30"))
        code, out, err = self.check("--json", repos=[])
        self.assertEqual(code, 1, err)
        rows = {r["n"]: r for r in json.loads(out)["rows"]}
        self.assertIsNone(rows[1]["red"])
        self.assertTrue(rows[1]["skipped"])
        self.assertEqual((rows[2]["red"], rows[3]["red"]), (None, "resolved"))
        self.assertFalse(rows[2]["skipped"] or rows[3]["skipped"])

    def test_a_repo_with_no_nice_file_is_still_checked(self):
        self.assertFalse(os.path.exists(os.path.join(self.pear, "NICE_TO_HAVE.md")))
        got, code = self.reds((1, "pear", "building p9-none"))
        self.assertEqual((got, code), ({1: "stale: branch gone"}, 1))


class Write(Orchard):
    """Acceptance 4 and 5: `--write` moves a landed row out whole; `--check` alone and a
    `--write` without `--check` write nothing."""

    def setUp(self):
        super().setUp()
        self.put(self.done, DONE_HEAD)

    def test_write_moves_the_landed_row_and_nothing_else(self):
        self.table((7, "pear", "building p1-live"), (8, "pear", "building p2-done"))
        with open(self.handoff, encoding="utf-8") as handle:
            before = handle.read()
        code, out, err = self.check("--write")
        self.assertEqual(code, 0, out + err)
        with open(self.handoff, encoding="utf-8") as handle:
            after = handle.read()
        landed = [l for l in before.splitlines(True) if l.startswith("| 8 |")]
        self.assertEqual(after, before.replace(landed[0], ""))
        with open(self.done, encoding="utf-8") as handle:
            done = handle.read()
        self.assertTrue(done.startswith(DONE_HEAD))
        self.assertEqual(done.splitlines()[-1],
                         "8 Row 8 of the orchard, done %s %s" % (DATE, self.p2_merge[:7]))
        snap = self.bytes_of(self.handoff, self.done)
        code, out, err = self.check("--write")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.bytes_of(self.handoff, self.done), snap)

    def test_a_bulleted_done_file_takes_a_bullet(self):
        self.put(self.done, DONE_HEAD + "- 2026-11-02 off the build order: a pruning\n")
        self.table((8, "pear", "building p2-done"))
        self.assertEqual(self.check("--write")[0], 0)
        with open(self.done, encoding="utf-8") as handle:
            last = handle.read().splitlines()[-1]
        self.assertEqual(last, "- 8 Row 8 of the orchard, done %s %s" % (DATE, self.p2_merge[:7]))

    def test_write_leaves_a_red_that_is_not_landed(self):
        self.table((7, "pear", "building p9-none"), (8, "pear", "building p2-done"))
        code, out, err = self.check("--write")
        self.assertEqual(code, 1, out + err)
        with open(self.handoff, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("building p9-none", text)
        self.assertNotIn("p2-done", text)

    def test_check_alone_writes_nothing(self):
        self.table((7, "pear", "building p1-live"), (8, "pear", "building p2-done"))
        snap = self.bytes_of(self.handoff, self.done)
        self.assertEqual(self.check()[0], 1)
        self.assertEqual(self.bytes_of(self.handoff, self.done), snap)

    def test_write_without_check_is_a_usage_error(self):
        self.table((8, "pear", "building p2-done"))
        snap = self.bytes_of(self.handoff, self.done)
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["backlog", "--write", "--order", self.handoff, self.pear],
                              out=out, err=err)
        self.assertEqual(code, 2)
        self.assertEqual(self.bytes_of(self.handoff, self.done), snap)

    def test_check_without_order_is_a_usage_error(self):
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(decisions.main(["backlog", "--check", self.pear], out=out, err=err), 2)


class Json(Orchard):
    """Acceptance 6: `--json` carries each row's reference and red."""

    def test_json_carries_the_reference_and_the_red(self):
        self.table((1, "hq", "waiting: owner 4; the shed"), (2, "suite", "waiting: row 1"),
                   (3, "suite", "waiting: pear p1-live"), (4, "hq", "waiting: the owner: picks"),
                   (5, "pear", "building p2-done"), (6, "suite", "building pear g2"),
                   (7, "pear", "done %s %s" % (DATE, self.p2_merge[:7])), (8, "pear", "watch: frost"))
        code, out, err = self.check("--json")
        self.assertEqual(code, 1, err)
        rows = {r["n"]: r for r in json.loads(out)["rows"]}
        refs = {n: r["reference"] for n, r in rows.items()}
        self.assertEqual(refs[1], {"kind": "waiting", "on": "owner", "n": 4})
        self.assertEqual(refs[2], {"kind": "waiting", "on": "row", "n": 1})
        self.assertEqual(refs[3], {"kind": "waiting", "on": "branch", "repo": "pear",
                                   "branch": "p1-live"})
        self.assertEqual(refs[4], {"kind": "waiting", "on": "the owner"})
        self.assertEqual(refs[5], {"kind": "building", "repo": None, "branch": "p2-done"})
        self.assertEqual(refs[6], {"kind": "building", "repo": "pear", "branch": "g2"})
        self.assertEqual(refs[7], {"kind": "done", "date": DATE, "sha": self.p2_merge[:7]})
        self.assertEqual(refs[8], {"kind": "watch"})
        self.assertEqual(rows[1]["red"], "answered")
        self.assertTrue(rows[5]["red"].startswith("stale: landed"))
        self.assertEqual(json.loads(out)["stale"], 2)


class OwnerLink(Home):
    """Acceptance 7, R7: the owner's file that is a link into a checkout stays the owner's."""

    def test_the_owners_file_linked_into_a_checkout_is_the_owners(self):
        dots = os.path.join(self.home, "work", "dots")
        os.makedirs(os.path.join(dots, ".git"))
        with open(os.path.join(dots, "CLAUDE.md"), "w", encoding="utf-8") as handle:
            handle.write("# Mine\n")
        target = os.path.join(self.home, ".claude", "CLAUDE.md")
        os.makedirs(os.path.dirname(target))
        os.symlink(os.path.join(dots, "CLAUDE.md"), target)
        for _ in range(2):
            code, _, err = self.render("--into", target)
            self.assertEqual(code, 0, err)
        self.assertEqual(lines(self.owner), ["~/.claude/CLAUDE.md"])
        self.assertFalse(os.path.exists(os.path.join(dots, ".claude", GATES)))
        self.assertTrue(os.path.islink(target))
