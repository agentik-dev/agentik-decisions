"""su5 (agentik-hq design/18 §3.3 item 11): each step of `backlog --json` gains `level`, the
table's `level` cell when it is S1 to S4, and `state`, its state cell read into six keys, so
that a reader counts a row's level and its wait without parsing the cell. Every repo and
HANDOFF is made here under the temp home, with made-up names."""

import io
import json
import os

import decisions
from tests.test_d39_backlog_check import HEADER, Orchard

NICE_TEXT = "# Nice to have\n\n- S3: the crate's lid sticks (`lid.md`)\n"
ROWS = ((3, "S2", "pear", "waiting: the owner: opens the gate; then the cart"),
        (4, "S3", "pear", "waiting: owner 9; after row 3"),
        (5, "S4", "pear", "building p1-crate"),
        (6, "soon", "pear", "open"))
STEP_KEYS = {"n", "line", "title", "done", "level", "state"}


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


def state(cell, word, rest, on=None, n=None, text=""):
    return {"cell": cell, "word": word, "rest": rest, "on": on, "n": n, "text": text}


class Fields(Orchard):
    """Acceptance 1 to 4, and the held lines beside them."""

    def setUp(self):
        super().setUp()
        self.put(os.path.join(self.pear, "NICE_TO_HAVE.md"), NICE_TEXT)

    def handoff_text(self, rows, header=HEADER):
        body = "".join("| %d | Row %d of the orchard | %s | %s | `x.md` | %s |\n"
                       % (n, n, level, repo, cell) for n, level, repo, cell in rows)
        return ("# Handoff\n\n<!-- decisions: build order -->\n\n## The build order\n\n"
                + header + body + "\n## After\n\nProse.\n")

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["backlog"] + list(argv), out=out, err=err)
        self.assertEqual(code, 0, err.getvalue())
        return out.getvalue()

    def steps(self, rows=ROWS, header=HEADER, ordered=True, repos=None):
        """{n: step} of pear's view, read by `--order FILE` or from pear's own HANDOFF.md."""
        path = self.handoff if ordered else os.path.join(self.pear, "HANDOFF.md")
        self.put(path, self.handoff_text(rows, header))
        named = [self.pear] if repos is None else list(repos)
        argv = (["--order", self.handoff] if ordered else []) + named + ["--json"]
        data = json.loads(self.run_cli(*argv))
        # R6: no new top-level key but ak6 R8's two, first
        self.assertEqual(list(data), ["schema", "ok", "repos", "skipped"])
        view = {os.path.basename(r["repo"]): r for r in data["repos"]}["pear"]
        return {s["n"]: s for s in view["steps"]}

    def test_1_order_json_gives_each_step_its_level_and_state(self):
        got = self.steps()
        for step in got.values():
            self.assertEqual(set(step), STEP_KEYS | {"repo"})
        self.assertEqual(got[3]["level"], "S2")
        self.assertEqual(got[3]["state"], state(
            "waiting: the owner: opens the gate; then the cart", "waiting",
            "the owner: opens the gate; then the cart", on="the owner",
            text="opens the gate; then the cart"))
        self.assertEqual(got[4]["level"], "S3")
        self.assertEqual(got[4]["state"], state("waiting: owner 9; after row 3", "waiting",
                                                "owner 9; after row 3", on="owner", n=9,
                                                text="after row 3"))
        self.assertEqual(got[5]["level"], "S4")
        self.assertEqual(got[5]["state"], state("building p1-crate", "building", "p1-crate"))
        self.assertIsNone(got[6]["level"])
        self.assertEqual(got[6]["state"], state("open", "open", ""))

    def test_2_more_cells(self):
        rows = ((7, "S3", "pear", "waiting: row 4"),
                (8, "S3", "pear", "waiting: pear p1-crate"),
                (9, "S3", "pear", "waiting: plum p1"),
                (10, "S3", "pear", "watch: a loose crate"),
                (11, "S3", "pear", "done 2026-11-10 abc1234"),
                (12, "S3", "pear", ""))
        got = {n: s["state"] for n, s in self.steps(rows).items()}
        self.assertEqual(got[7], state("waiting: row 4", "waiting", "row 4", on="row", n=4))
        self.assertEqual(got[8], state("waiting: pear p1-crate", "waiting", "pear p1-crate",
                                       on="branch"))
        self.assertEqual(got[9], state("waiting: plum p1", "waiting", "plum p1"))
        self.assertEqual(got[10], state("watch: a loose crate", "watch", "a loose crate"))
        self.assertEqual(got[11], state("done 2026-11-10 abc1234", "done",
                                        "2026-11-10 abc1234"))
        self.assertEqual(got[12], state("", None, ""))

    def test_2_a_repo_named_is_a_name(self):
        plum = os.path.join(self.tmp, "plum")
        os.makedirs(plum)  # R4: no checkout, and still a name
        got = self.steps(((9, "S3", "pear", "waiting: plum p1"),), repos=[self.pear, plum])
        self.assertEqual(got[9]["state"]["on"], "branch")

    def test_3_own_handoff_json_gives_level_and_state_and_no_repo(self):
        got = self.steps(ordered=False)
        for step in got.values():
            self.assertEqual(set(step), STEP_KEYS)
        self.assertEqual((got[3]["level"], got[3]["state"]["on"]), ("S2", "the owner"))
        self.assertEqual((got[4]["state"]["on"], got[4]["state"]["n"]), ("owner", 9))
        self.assertEqual(got[5]["state"]["word"], "building")
        self.assertEqual((got[6]["level"], got[6]["state"]["word"]), (None, "open"))

    def test_4_a_list_step_has_neither(self):
        fixture = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "fixtures", "backlog", "numbered")
        data = json.loads(self.run_cli(fixture, "--json"))
        steps = data["repos"][0]["steps"]
        self.assertTrue(steps)
        for step in steps:
            self.assertEqual(set(step), STEP_KEYS)
            self.assertEqual((step["level"], step["state"]), (None, None))

    def test_4_a_table_with_no_level_column(self):
        header = "| # | item | grade | repo | where | state |\n|---|---|---|---|---|---|\n"
        got = self.steps(header=header)
        self.assertEqual([s["level"] for s in got.values()], [None] * 4)
        self.assertEqual(got[4]["state"]["n"], 9)

    def test_held_text_view(self):
        self.put(self.handoff, self.handoff_text(ROWS))
        out = self.run_cli("--order", self.handoff, self.pear)
        self.assertEqual(out.splitlines(), [
            '== pear  build order: HANDOFF.md:5 "The build order", 4 open steps',
            "step 3  HANDOFF.md:9  Row 3 of the orchard",
            "step 4  HANDOFF.md:10  Row 4 of the orchard",
            "step 5  HANDOFF.md:11  Row 5 of the orchard",
            "step 6  HANDOFF.md:12  Row 6 of the orchard",
            "1 S3  NICE_TO_HAVE.md:3  the crate's lid sticks (`lid.md`)",
            "0 of 1 items carry no level (placed as S4)"])

    def test_held_check_json_keys(self):
        self.put(self.handoff, self.handoff_text(ROWS))
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["backlog", "--check", "--order", self.handoff, self.pear,
                               "--json"], out=out, err=err)
        self.assertIn(code, (0, 1), err.getvalue())
        data = json.loads(out.getvalue())
        self.assertEqual(list(data), ["schema", "ok", "handoff", "checkout", "rows", "stale",
                                      "written"])  # ak6 R8: the plug's two keys first
        self.assertEqual(len(data["rows"]), 4)
        for row in data["rows"]:
            self.assertEqual(set(row), {"n", "repo", "cell", "reference", "checked_in", "red",
                                        "skipped", "written"})
        self.assertEqual(data["rows"][0]["cell"],
                         "waiting: the owner: opens the gate; then the cart")

    def test_held_line_1_writes_nothing(self):
        self.put(self.handoff, self.handoff_text(ROWS))
        home = os.path.dirname(os.environ["HOME"])
        before = (snapshot(self.tmp), snapshot(home))
        self.run_cli("--order", self.handoff, self.pear, "--json")
        self.assertEqual((snapshot(self.tmp), snapshot(home)), before)
