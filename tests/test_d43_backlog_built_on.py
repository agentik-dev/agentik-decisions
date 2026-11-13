"""d43 (agentik-hq design/14 §5): `backlog --check` reads a branch built on since its merge,
or cut again under its name, as live; a `<repo>` is a name of the table's repo column or of a
REPO named on the command line; a `waiting:` cell of no known form is named on one `unread`
line. Every repo and HANDOFF is made here under the temp home, with made-up names."""

import json
import os

from tests.test_d39_backlog_check import DATE, DONE_HEAD, Orchard, branch, commit, git

UNREAD = "unread (waiting names no owner, row or repo): "


class BuiltOn(Orchard):
    """Acceptance 1 to 3: a merge named for the branch counts only when the branch is gone,
    or its tip is that merge's second parent or an ancestor of it."""

    def setUp(self):
        super().setUp()
        self.put(self.done, DONE_HEAD)

    def landed(self, merge):
        return "stale: landed %s %s" % (merge[:7], DATE)

    def test_1_merged_by_name_then_a_commit_is_clean_and_write_writes_nothing(self):
        branch(self.pear, "more1", merge="Merge more1: the first crate")
        git(self.pear, "checkout", "-q", "more1")
        commit(self.pear, "more1-again.txt")
        git(self.pear, "checkout", "-q", "main")
        self.table((7, "pear", "building more1"))
        snap = self.bytes_of(self.handoff, self.done)
        code, out, err = self.check("--write")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("stale", out)
        self.assertEqual(self.bytes_of(self.handoff, self.done), snap)

    def test_2_merged_by_name_deleted_and_cut_again_is_clean(self):
        for name, again in (("more2", True), ("more3", False)):
            branch(self.pear, name, merge="Merge %s: a crate" % name, delete=True)
            git(self.pear, "branch", "-q", name, "main")
            if again:
                git(self.pear, "checkout", "-q", name)
                commit(self.pear, name + "-again.txt")
                git(self.pear, "checkout", "-q", "main")
        got, code = self.reds((1, "pear", "building more2"), (2, "pear", "building more3"))
        self.assertEqual((got, code), ({1: None, 2: None}, 0))

    def test_3_merged_by_name_at_its_tip_or_gone_is_landed(self):
        _, gone = branch(self.pear, "more4", merge="Merge more4: a crate", delete=True)
        got, code = self.reds((1, "pear", "building p2-done"), (2, "pear", "building more4"))
        self.assertEqual(got, {1: self.landed(self.p2_merge), 2: self.landed(gone)})
        self.assertEqual(code, 1)

    def test_3_a_tip_behind_the_merged_one_is_landed(self):
        _, merge = branch(self.pear, "more5", merge="Merge more5: a crate")
        git(self.pear, "checkout", "-q", "more5")
        commit(self.pear, "more5-second.txt")
        git(self.pear, "checkout", "-q", "main")
        git(self.pear, "merge", "-q", "--no-ff", "-m", "Merge more5: the second crate", "more5")
        second = git(self.pear, "rev-parse", "HEAD")
        git(self.pear, "branch", "-q", "-f", "more5", merge + "^2")
        got, _ = self.reds((1, "pear", "building more5"))
        self.assertEqual(got, {1: self.landed(second)})

    def test_3_the_newest_named_merge_the_tip_reached_is_the_one(self):
        _, first = branch(self.pear, "more6", merge="Merge more6: a crate")
        git(self.pear, "checkout", "-q", "more6")
        commit(self.pear, "more6-second.txt")
        git(self.pear, "checkout", "-q", "main")
        git(self.pear, "merge", "-q", "--no-ff", "-m", "Merge more6: the second crate", "more6")
        second = git(self.pear, "rev-parse", "HEAD")
        got, _ = self.reds((1, "pear", "building more6"))
        self.assertEqual(got, {1: self.landed(second)})
        self.assertNotEqual(first, second)


class Named(Orchard):
    """Acceptance 4: a REPO named on the command line is a `<repo>` though no row's repo
    column holds it."""

    def setUp(self):
        super().setUp()
        self.quince = os.path.join(self.tmp, "quince")
        os.makedirs(self.quince)
        git(self.quince, "init", "-q")
        commit(self.quince, "start.txt")
        _, self.q1_merge = branch(self.quince, "q1", merge="Merge q1: the quince crate")

    def test_4_a_named_repo_outside_the_column_is_a_reference(self):
        got, code = self.reds((1, "suite", "waiting: quince q1"),
                              (2, "suite", "building quince q1"), (9, "pear", "open"),
                              repos=[self.pear, self.quince])
        landed = "stale: landed %s %s" % (self.q1_merge[:7], DATE)
        self.assertEqual(got, {1: landed, 2: landed, 9: None})
        self.assertEqual(code, 1)

    def test_4_the_json_names_the_repo(self):
        self.table((1, "suite", "waiting: quince q1"))
        code, out, err = self.check("--json", repos=[self.pear, self.quince])
        self.assertEqual(code, 1, err)
        ref = json.loads(out)["rows"][0]["reference"]
        self.assertEqual(ref, {"kind": "waiting", "on": "branch", "repo": "quince",
                               "branch": "q1"})


class Unread(Orchard):
    """Acceptance 5: a `waiting:` cell of none of the four forms is named, never red."""

    def test_5_an_unread_waiting_cell_is_named_on_one_line(self):
        self.table((1, "suite", "waiting: plum p1"), (2, "pear", "building p1-live"),
                   (3, "hq", "waiting: someone, later"))
        code, out, err = self.check()
        self.assertEqual(code, 0, out + err)
        unread = [l for l in out.splitlines() if l.startswith("unread")]
        self.assertEqual(unread, [UNREAD + "1, 3"], out)
        self.assertEqual(out.splitlines()[-1], "checked 3 rows of HANDOFF.md: 0 stale")

    def test_5_the_json_is_unchanged(self):
        self.table((1, "suite", "waiting: plum p1"))
        code, out, err = self.check("--json")
        self.assertEqual(code, 0, err)
        got = json.loads(out)
        self.assertEqual(got["rows"][0]["reference"], {"kind": "waiting", "on": None})
        self.assertEqual((got["rows"][0]["red"], got["stale"]), (None, 0))


class Unproven(Orchard):
    """Acceptance 6: a fast-forward and a squash stay unread as landings."""

    def test_6_a_fast_forward_and_a_squash_are_clean(self):
        git(self.pear, "checkout", "-q", "-b", "ff1", "main")
        commit(self.pear, "ff1.txt")
        git(self.pear, "checkout", "-q", "main")
        git(self.pear, "merge", "-q", "--ff-only", "ff1")
        git(self.pear, "checkout", "-q", "-b", "sq1", "main")
        commit(self.pear, "sq1.txt")
        git(self.pear, "checkout", "-q", "main")
        git(self.pear, "merge", "-q", "--squash", "sq1")
        git(self.pear, "commit", "-q", "-m", "Merge sq1: squashed")
        got, code = self.reds((1, "pear", "building ff1"), (2, "pear", "building sq1"))
        self.assertEqual((got, code), ({1: None, 2: None}, 0))


class AsAtThePin(Orchard):
    """Acceptance 7: a table with no unread cell prints what it printed at the pin."""

    def test_7_the_text_view_is_unchanged(self):
        self.table((1, "pear", "building p1-live"), (2, "pear", "building p2-done; later"),
                   (3, "pear", "building p9-none"), (4, "hq", "waiting: owner 4"),
                   (5, "suite", "waiting: row 30"), (6, "hq", "waiting: the owner: picks"),
                   (7, "plum", "building p1"), (8, "pear", "done %s %s" % (DATE, self.side[:7])))
        code, out, err = self.check()
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "".join(l + "\n" for l in (
            "2  building p2-done  stale: landed %s %s" % (self.p2_merge[:7], DATE),
            "3  building p9-none  stale: branch gone",
            "4  waiting: owner 4  answered",
            "5  waiting: row 30  resolved",
            "8  done %s %s  stale: %s is not on main's first-parent line"
            % (DATE, self.side[:7], self.side[:7]),
            "skipped (repo not named or absent): 7 plum",
            "checked 8 rows of HANDOFF.md: 5 stale")))
