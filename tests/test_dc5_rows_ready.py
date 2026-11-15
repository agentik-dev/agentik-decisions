"""dc5 (agentik-hq design/16 section 4 item 3, design/19 items 2 and 9): a reviewed row with a
merge file reads `ready` whatever its merge base where main's Makefile has a `stamp` target, and
the landing's commits past the reviewed head, each closing `Gate-Land: <sha>`, keep the row's
word; a plain commit there asks a review. Review 1's C1: the count starts at the covering
review's slice end where it is past that head, and a commit whose paths all lie under
`history/` keeps the word too. Every repo and row is made under the temp folder,
with made-up names."""

import os

from tests.test_d39_backlog_check import commit, git
from tests.test_rw2_rows import Rows

ROW = "p5-ready"
STAMP = "check:\n\t@true\n\nstamp:\n\t@true\n"
# no line opens `stamp:`; the landing's test is a line's start, so these two are not one
NO_STAMP = "check:\n\t@true\n\nstamp-check:\n\t@true\n # stamp: later\n"


class Ready(Rows):
    """R3: each rule of R1 and R2 on one row of `pear`, reviewed and with a merge file."""

    def reviewed(self, makefile):
        """Main takes `makefile`; the row is built, reviewed `closed` and given its merge
        file at main's head. (tip, merge file)."""
        self.put(os.path.join(self.pear, "Makefile"), makefile)
        git(self.pear, "add", "Makefile")
        git(self.pear, "commit", "-q", "-m", "add Makefile")
        tip = self.on_branch(ROW, "ready-5.txt")
        self.row(ROW)
        self.build(ROW, 1, tip)
        self.review(ROW, 1, "%s..%s" % (self.base(ROW)[:7], tip[:7]), ruling="closed")
        merge = os.path.join(os.path.realpath(self.root), ROW, "merge.txt")
        self.put(merge, "Merge p5-ready: the made-up row\n")
        return tip, merge

    def land(self, tip, merge):
        return "agentik session gate land %s %s %s %s" % (
            os.path.realpath(self.pear), ROW, tip, merge)

    def readied(self, given):
        """The landing's two commits on the branch, main merged then the stamp, each closing
        with the trailer; the new tip."""
        trailer = "Gate-Land: " + given
        git(self.pear, "checkout", "-q", ROW)
        git(self.pear, "merge", "-q", "--no-ff", "-m", ROW + ": merge main", "-m", trailer,
            "main")
        self.put(os.path.join(self.pear, "VERSION"), "0.0.2\n")
        git(self.pear, "add", "VERSION")
        git(self.pear, "commit", "-q", "-m", ROW + ": plugin 0.0.2", "-m", trailer)
        git(self.pear, "checkout", "-q", "main")
        return git(self.pear, "rev-parse", ROW)

    def recorded(self, name):
        """A record-only commit on the branch, one file under `history/`; the new tip."""
        git(self.pear, "checkout", "-q", ROW)
        path = os.path.join("history", "sittings", name)
        self.put(os.path.join(self.pear, path), "# a made-up sitting\n")
        git(self.pear, "add", path)
        git(self.pear, "commit", "-q", "-m", ROW + ": the charter")
        git(self.pear, "checkout", "-q", "main")
        return git(self.pear, "rev-parse", ROW)

    def word(self):
        got = self.view()[ROW]
        self.assertEqual(got["stale"], [], got)
        return got

    def test_r1_a_stamp_target_reads_ready_behind_main(self):
        tip, merge = self.reviewed(STAMP)
        commit(self.pear, "main-moves.txt")
        got = self.word()
        self.assertEqual(got["state"], "ready", got)
        self.assertEqual(got["next"]["command"], self.land(tip, merge))
        self.assertEqual(got["record"], "merge.txt")

    def test_r1_no_stamp_target_reads_reviewed_phase_2(self):
        self.reviewed(NO_STAMP)
        commit(self.pear, "main-moves.txt")
        got = self.word()
        self.assertEqual(got["state"], "reviewed", got)
        self.assertEqual(got["next"]["text"], "phase 2: merge main into %s" % ROW)
        self.assertIsNone(got["next"]["command"])
        self.assertEqual(got["record"], "review-1.md")

    def test_r2_two_gate_land_commits_keep_the_word(self):
        head, merge = self.reviewed(STAMP)
        commit(self.pear, "main-moves.txt")
        tip = self.readied(head)
        got = self.word()
        self.assertEqual(got["state"], "ready", got)
        self.assertEqual(got["next"]["command"], self.land(tip, merge))
        # a red landing: main moves on past the readied branch, and the row stays ready
        commit(self.pear, "main-moves-again.txt")
        got = self.word()
        self.assertEqual(got["state"], "ready", got)
        self.assertEqual(got["next"]["command"], self.land(tip, merge))
        # with no merge file the row is reviewed, its next act the merge file
        os.remove(merge)
        got = self.word()
        self.assertEqual((got["state"], got["next"]["text"]), ("reviewed", merge), got)

    def test_r2_a_plain_commit_past_the_review_reads_built(self):
        head, _ = self.reviewed(STAMP)
        tip = self.on_branch(ROW, "after-review.txt")
        got = self.word()
        self.assertEqual(got["state"], "built", got)
        self.assertEqual(got["next"]["text"], "review 2: %s..%s" % (head[:7], tip[:7]))
        self.assertIsNone(got["next"]["command"])
        self.assertEqual(got["record"], "build-1.md")

    def test_r2_a_plain_commit_after_the_landing_reads_built(self):
        head, _ = self.reviewed(STAMP)
        commit(self.pear, "main-moves.txt")
        readied = self.readied(head)
        tip = self.on_branch(ROW, "after-ready.txt")
        self.assertNotEqual(readied, tip)
        got = self.word()
        self.assertEqual(got["state"], "built", got)
        self.assertEqual(got["next"]["text"], "review 2: %s..%s" % (head[:7], tip[:7]))

    def test_c1_a_record_only_commit_past_the_checked_head_keeps_the_word(self):
        _, merge = self.reviewed(STAMP)
        tip = self.recorded("2026-01-01-1.md")
        got = self.word()
        self.assertEqual(got["state"], "ready", got)
        self.assertEqual(got["next"]["command"], self.land(tip, merge))
        # with no merge file the row is reviewed, its next act the merge file
        os.remove(merge)
        got = self.word()
        self.assertEqual((got["state"], got["next"]["text"]), ("reviewed", merge), got)

    def test_c1_a_review_that_ends_at_the_tip_past_a_record_only_commit_reads_ready(self):
        head, merge = self.reviewed(STAMP)
        end = self.recorded("2026-01-01-1.md")
        self.review(ROW, 1, "%s..%s" % (self.base(ROW)[:7], end[:7]), ruling="closed")
        got = self.word()
        self.assertEqual(got["state"], "ready", got)
        self.assertEqual(got["next"]["command"], self.land(end, merge))
        # a code commit past the slice end asks the next review from that end
        tip = self.on_branch(ROW, "after-review.txt")
        got = self.word()
        self.assertEqual(got["state"], "built", got)
        self.assertEqual(got["next"]["text"], "review 2: %s..%s" % (end[:7], tip[:7]))

    def test_c1_a_code_commit_the_review_read_keeps_the_word(self):
        head, merge = self.reviewed(STAMP)
        end = self.on_branch(ROW, "read-by-review.txt")
        self.review(ROW, 1, "%s..%s" % (self.base(ROW)[:7], end[:7]), ruling="closed")
        got = self.word()
        self.assertEqual(got["state"], "ready", got)
        self.assertEqual(got["next"]["command"], self.land(end, merge))
