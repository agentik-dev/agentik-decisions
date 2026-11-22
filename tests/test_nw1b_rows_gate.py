"""nw1b: a row whose review closed and whose merge file is written reads `ready`, with the
landing's command, only where the newest build record's gate cell is exit 0, a running cell
read from its job's own result.json as rg1 reads it; else `reviewed`, no command, its next act
the check it waits on. Every repo, row and job is made under the temp folder, with made-up
names."""

import os

from tests.test_rw2_rows import Rows

ROW = "p6-gated"


class Gated(Rows):
    """R1 and R2 on one row of `pear`, reviewed `closed`, its merge file written, main still."""

    def setUp(self):
        super().setUp()
        self.tip = self.on_branch(ROW, "gated-1.txt")
        self.row(ROW)
        self.merge = os.path.join(os.path.realpath(self.root), ROW, "merge.txt")
        self.put(self.merge, "Merge p6-gated: the made-up row\n")

    def built(self, gate, n=1, head=None, reviewed=True):
        """Build record `n` with `gate` (no gate cell when None); the review covers it."""
        head = head or self.tip
        if gate is None:
            self.record(ROW, "build-%d.md" % n, stage="first build", head=head)
        else:
            self.build(ROW, n, head, gate=gate)
        if reviewed:
            self.review(ROW, 1, "%s..%s" % (self.base(ROW)[:7], head[:7]), ruling="closed")

    def result(self, job, body):
        self.put(os.path.join(os.environ["XDG_STATE_HOME"], "agentik-session", "gate", job,
                              "result.json"), body)

    def seen(self):
        """(the row's `--json` object, its text line)."""
        got = self.view()[ROW]
        self.assertEqual(got["stale"], [], got)
        line = [t for t in self.rows()[1].splitlines() if t.startswith(ROW + " ")][0]
        return got, line

    def ready(self, tip=None):
        got, line = self.seen()
        command = "agentik session gate land %s %s %s %s" % (
            os.path.realpath(self.pear), ROW, tip or self.tip, self.merge)
        self.assertEqual((got["state"], got["next"]["command"]), ("ready", command), got)
        self.assertEqual(got["record"], "merge.txt")
        self.assertIn("  ready  ", line)
        self.assertTrue(line.endswith("next: " + command), line)

    def reviewed(self, text, record="build-1.md"):
        got, line = self.seen()
        self.assertEqual(got["state"], "reviewed", got)
        self.assertEqual(got["next"], {"text": text, "command": None}, got)
        self.assertEqual(got["record"], record)
        self.assertIn("  reviewed  ", line)
        self.assertTrue(line.endswith("next: " + text), line)
        self.assertNotIn("gate land", line)

    def test_exit_0_is_ready(self):
        self.built("G1 exit 0")
        self.ready()

    def test_running_with_no_result_is_reviewed(self):
        self.built("G2 running (position 3)")
        self.reviewed("check G2 still runs")

    def test_running_with_a_result_of_exit_0_is_ready(self):
        self.result("G3", '{"exit": 0}')
        self.built("G3 running")
        self.ready()

    def test_running_with_a_result_of_exit_2_is_reviewed(self):
        self.result("G4", '{"exit": 2}')
        self.built("G4 running")
        self.reviewed("check G4 exit 2, not green")

    def test_exit_2_is_reviewed(self):
        self.built("G5 exit 2 (three tests red)")
        self.reviewed("check G5 exit 2, not green")

    def test_no_gate_cell_and_none_name_no_check(self):
        self.built(None)
        self.reviewed("build-1.md names no check")
        self.built("none: a records-only change")
        self.reviewed("build-1.md names no check")

    def test_the_newest_build_decides(self):
        self.built("G6 exit 0", reviewed=False)
        tip2 = self.on_branch(ROW, "gated-2.txt")
        self.built("G7 running", n=2, head=tip2)
        self.reviewed("check G7 still runs", record="build-2.md")
        self.built("G7 exit 1", n=2, head=tip2)
        self.reviewed("check G7 exit 1, not green", record="build-2.md")
        self.built("G6 exit 2", reviewed=False)
        self.built("G7 exit 0", n=2, head=tip2)
        self.ready(tip2)

    def test_a_row_before_the_ruling_reads_as_before(self):
        self.built("G8 running", reviewed=False)
        got, _ = self.seen()
        self.assertEqual(got["state"], "built", got)
        self.review(ROW, 1, "%s..%s" % (self.base(ROW)[:7], self.tip[:7]), ruling="fix: F1")
        self.assertEqual(self.seen()[0]["state"], "to fix")
