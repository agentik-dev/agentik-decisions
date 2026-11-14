"""dc2 (design/packets/dc2-render-invited.md): `render` rewrites a block that is there and
writes nothing into a file that holds none, naming the act that adds one; `init` over a ledger
that is there adds the block; `answer` names `init`. Each case in a temp HOME and a repo made
by `git init`; the ledger is written as a fixture, so the repo starts with no `.claude`."""

import os
import re
import shlex
import subprocess

from tests.test_dc1_init import Base, snapshot

L = ("# Decisions\n\n## In force\n\n### Every session\n\n"
     "1. **Indent.** This repo indents with four spaces. (2026-11-13; me)\n\n"
     "## Proposed\n\n## Superseded\n")
H = "# Orchard\n\nPears are picked by hand in the cool hours.\nThe ladder rests in the shed.\n"
BEGIN = "<!-- BEGIN GENERATED: decisions -->"
END = "<!-- END GENERATED: decisions -->"
BLOCK = (BEGIN + "\n"
         "Generated from `DECISIONS.md` by `decisions"
         " render`; edit the ledger and rerun it, "
         "never this block.\n\n"
         "1. **Indent.** This repo indents with four spaces. (2026-11-13)\n" + END + "\n")
REFUSED = ", and render only rewrites a block that is there; nothing written; "
INIT = "`agentik decisions init` adds it"
MARKS = ("a file takes the block once it holds the two marker lines, `%s` then `%s`, each "
         "alone on a line" % (BEGIN, END))
GATE_LINE = ("%s: %s is now on the edit-gates list .claude/edit-gates: a session changes it "
             "through /decisions:instruct, never by its own edit; deleting its line there "
             "lifts the gate\n")
# measured at c4ff3f2 (0.22.3) by the same fixtures: the lint, and the loaded-bytes lines
PIN_LINT_OUT = ("render: the block for CLAUDE.md is 236 B; it is loaded on every turn\n"
                "render: CLAUDE.md loads 252 B, comments aside and imports included; the "
                "ceiling for a repo's file is 3,072 B\n")
PIN_LINT_ERR = (
    "render: warning: entry 1 under `Every session` is titled `Indent`, none of the ten "
    "titles; it keeps its place after them\n"
    "render: warning: the ten titles, in their order: Writes, Never run, Devices, Commits, "
    "Pushes, Never commit, Helpers, Budget, Deciding and asking, Changing these rules\n")
PIN_LOADS_H = ("render: CLAUDE.md loads 252 B, comments aside and imports included; the "
               "ceiling for a repo's file is 3,072 B")
PIN_LOADS_ALONE = ("render: CLAUDE.md loads 166 B, comments aside and imports included; the "
                   "ceiling for a repo's file is 3,072 B")


def refusal(target, state, after):
    return "decisions: render: %s %s%s%s\n" % (target, state, REFUSED, after)


class Invited(Base):

    def setUp(self):
        super().setUp()
        self.write(self.ledger, L)

    def write(self, path, text, mode="w"):
        with open(path, mode, encoding="utf-8", newline="") as handle:
            handle.write(text)

    def refuses(self, argv, err_line):
        before = snapshot(self.tmp)
        code, out, err = self.run_cli(*argv)
        self.assertEqual((code, out, err), (2, "", err_line), argv)
        self.assertEqual(snapshot(self.tmp), before, argv)
        return err

    def test_1_hand_lines_get_nothing(self):
        self.write(self.claude, H)
        self.refuses(["render"], refusal("CLAUDE.md", "holds no generated block", INIT))
        self.assertEqual(self.read(self.claude), H)
        self.assertFalse(os.path.lexists(os.path.join(self.repo, ".claude")))

    def test_2_no_claude_md_gets_nothing(self):
        self.refuses(["render"], refusal("CLAUDE.md", "is absent", INIT))
        self.assertFalse(os.path.lexists(self.claude))
        self.assertFalse(os.path.lexists(os.path.join(self.repo, ".claude")))

    def test_3_a_stale_block_between_hand_lines_is_rewritten(self):
        stale = BEGIN + "\nold text\n" + END + "\n"
        self.assertEqual(len(stale.encode()), 79)
        self.write(self.claude, H + "\n" + stale + "\nA last hand line.\n")
        code, out, err = self.run_cli("render")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "render: wrote CLAUDE.md: 79 B to 236 B, +157 B; the block is "
                              "loaded on every turn\n" + GATE_LINE % ("render", "CLAUDE.md"))
        self.assertEqual(self.read(self.claude), H + "\n" + BLOCK + "\nA last hand line.\n")
        self.assertEqual(self.run_cli("render")[1], "render: CLAUDE.md is fresh\n")

    def test_4_each_file_without_a_block_gets_nothing(self):
        elsewhere = os.path.join(self.tmp, "elsewhere")
        os.mkdir(elsewhere)
        self.write(os.path.join(elsewhere, "hand.md"), H)
        self.write(os.path.join(self.repo, "AGENTS.md"), H)
        no_block = refusal("CLAUDE.md", "holds no generated block", INIT)
        cases = [
            ("empty", "", no_block),
            ("blank lines", "\n\n\n", no_block),
            ("fenced markers", "# Notes\n```\n%s\nan example\n%s\n```\n" % (BEGIN, END), no_block),
            ("CRLF", H.replace("\n", "\r\n"), no_block),
            ("a link to AGENTS.md beside it", "AGENTS.md", no_block),
            ("a link to another folder", os.path.join("..", "elsewhere", "hand.md"), no_block),
            ("a link to nothing", "gone.md", refusal("CLAUDE.md", "is absent", INIT)),
        ]
        for name, text, line in cases:
            if os.path.lexists(self.claude):
                os.unlink(self.claude)
            if name.startswith("a link"):
                os.symlink(text, self.claude)
            else:
                self.write(self.claude, text)
            self.refuses(["render"], line)
            # the CLAUDE.md beside the ledger however it is named: `init` adds its block
            for named in ("CLAUDE.md", os.path.join(".", "CLAUDE.md"), self.claude):
                self.refuses(["render", "--into", named], line)
        self.assertFalse(os.path.lexists(os.path.join(self.repo, "gone.md")))
        self.assertFalse(os.path.lexists(os.path.join(self.repo, ".claude")))

    def test_5_another_file_takes_the_block_once_it_holds_the_markers(self):
        notes = os.path.join(self.repo, "NOTES.md")
        self.write(notes, H)
        self.refuses(["render", "--into", "NOTES.md"],
                     refusal("NOTES.md", "holds no generated block", MARKS))
        self.refuses(["render", "--into", "NEW.md"], refusal("NEW.md", "is absent", MARKS))
        self.assertFalse(os.path.lexists(os.path.join(self.repo, "NEW.md")))
        self.write(notes, H + BEGIN + "\n" + END + "\nAfter.\n")
        code, out, err = self.run_cli("render", "--into", "NOTES.md")
        self.assertEqual(code, 0, err)
        text = self.read(notes)
        self.assertTrue(text.startswith(H + BEGIN + "\nGenerated from `DECISIONS.md` by "
                                        "`decisions"
                                        " render --into NOTES.md`"), text)
        self.assertTrue(text.endswith("(2026-11-13)\n" + END + "\nAfter.\n"), text)

    def test_6_check_and_lint_write_nothing(self):
        for hand, state, loads in ((H, "holds no generated block", PIN_LOADS_H),
                                   (None, "is absent", PIN_LOADS_ALONE)):
            if hand is not None:
                self.write(self.claude, hand)
            elif os.path.lexists(self.claude):
                os.unlink(self.claude)
            before = snapshot(self.tmp)
            code, out, err = self.run_cli("render", "--check")
            self.assertEqual(code, 1, err)
            lines = out.splitlines()
            self.assertEqual(lines[0], "render: CLAUDE.md %s; %s" % (state, INIT))
            self.assertFalse([l for l in lines if l.startswith("+++")], out)
            self.assertEqual(lines[-1], loads)
            self.assertEqual(len(lines), 2, out)
            self.assertEqual(snapshot(self.tmp), before)
        self.write(self.claude, H)
        before = snapshot(self.tmp)
        self.assertEqual(self.run_cli("render", "--lint"), (0, PIN_LINT_OUT, PIN_LINT_ERR))
        self.assertEqual(snapshot(self.tmp), before)

    def test_7_fold_tails_refuses_before_it_folds(self):
        from tests.test_render import FIXTURE
        self.write(self.ledger, FIXTURE)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=fixture", "-c",
                        "commit.gpgsign=false", "-C", self.repo, "add", "DECISIONS.md"],
                       check=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=fixture", "-c",
                        "commit.gpgsign=false", "-C", self.repo, "commit", "-q", "-m", "l"],
                       check=True)
        self.write(self.claude, H)
        self.refuses(["render", "--fold-tails"],
                     refusal("CLAUDE.md", "holds no generated block", INIT))
        self.assertEqual(self.read(self.ledger), FIXTURE)

    def test_8_init_adds_the_block_under_hand_lines(self):
        self.write(self.claude, H)
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(BLOCK.encode()), 236)
        self.assertEqual(self.read(self.ledger), L)
        self.assertEqual(self.read(self.claude), H + "\n" + BLOCK)
        self.assertEqual(out, "init: DECISIONS.md is already there; it stays as it is\n"
                              "init: wrote CLAUDE.md: 0 B to 236 B, +236 B; the block is "
                              "loaded on every turn\n" + GATE_LINE % ("init", "CLAUDE.md") +
                              "init: next, `agentik decisions new` records a question; its "
                              "answer becomes an entry and reaches CLAUDE.md\n")
        self.assertEqual(self.listed(), ["CLAUDE.md"])
        self.assertEqual(self.run_cli("render"), (0, "render: CLAUDE.md is fresh\n", ""))

    def test_9_init_over_a_ledger(self):
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(self.claude), BLOCK)
        before = snapshot(self.tmp)
        code, out, err = self.run_cli("init")
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(err, "decisions: init: a ledger is already at %s; nothing written\n"
                         % self.ledger)
        self.assertEqual(snapshot(self.tmp), before)
        os.unlink(self.claude)
        self.write(self.ledger, "# Decisions\n\n## In force\n\n1. no bold title here\n")
        before = snapshot(self.tmp)
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 1, err)
        self.assertTrue(out.startswith("DECISIONS.md:"), out)
        self.assertEqual((code, out), self.run_cli("render")[:2])
        self.assertEqual(snapshot(self.tmp), before)
        os.unlink(self.ledger)
        os.mkdir(os.path.join(self.repo, "sub"))
        self.write(os.path.join(self.repo, "sub", "DECISIONS.md"), L)
        code, out, err = self.run_cli("init", "--ledger", "sub/DECISIONS.md")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(os.path.join(self.repo, "sub", "CLAUDE.md")), BLOCK)
        self.assertFalse(os.path.lexists(self.claude))
        self.assertIn("init: sub/DECISIONS.md is already there; it stays as it is\n", out)

    def round_trip(self, argv, fresh):
        code, _, err = self.run_cli(*argv)
        self.assertEqual(code, 2, err)
        command = shlex.split(re.search(r"; `([^`]*)` adds it$", err.strip()).group(1))
        self.assertEqual(command[:3], ["agentik", "decisions", "init"])
        code, _, err = self.run_cli(*command[2:])
        self.assertEqual(code, 0, err)
        self.assertEqual(self.run_cli(*argv)[:2], (0, fresh))
        return command

    def test_10_the_refusals_command_runs(self):
        self.write(self.claude, H)
        self.round_trip(["render"], "render: CLAUDE.md is fresh\n")
        for path in (self.claude, self.gates):
            os.unlink(path)
        self.round_trip(["render"], "render: CLAUDE.md is fresh\n")
        sub = os.path.join(self.repo, "sub")
        os.mkdir(sub)
        self.write(os.path.join(sub, "DECISIONS.md"), L)
        self.write(os.path.join(sub, "CLAUDE.md"), H)
        command = self.round_trip(["render", "--ledger", "sub/DECISIONS.md"],
                                  "render: sub/CLAUDE.md is fresh\n")
        self.assertEqual(command[3:], ["--ledger", "sub/DECISIONS.md"])

    def test_11_answer_names_init(self):
        self.write(self.claude, H)
        code, out, err = self.run_cli(
            "new", "--title", "Width", "--stands", "Lines run long.", "--choice",
            "Which width here?", "--option", "Short: lines stop at eighty",
            "--option", "Long: lines stop at a hundred", "--recommend", "Short: most do.")
        self.assertEqual(code, 0, err)
        number = re.search(r"^(\d+)\. ", self.read(self.ledger).split("## Proposed")[1],
                           re.M).group(1)
        code, out, err = self.run_cli("answer", number, "--pick", "Short", "--source", "me",
                                      "--text", "Lines stop at eighty.", "--area",
                                      "Every session", "--every-turn")
        self.assertEqual(code, 0, err)
        self.assertIn("**Width.** Lines stop at eighty.", self.read(self.ledger))
        self.assertEqual(self.read(self.claude), H)
        self.assertIn("answer: CLAUDE.md holds no GENERATED markers; the block is left as it "
                      "is; %s\n" % INIT, err)

    def asked(self):
        """The number of a question filed by `new`, its answer one `Every session` entry."""
        code, out, err = self.run_cli(
            "new", "--title", "Width", "--stands", "Lines run long.", "--choice",
            "Which width here?", "--option", "Short: lines stop at eighty",
            "--option", "Long: lines stop at a hundred", "--recommend", "Short: most do.")
        self.assertEqual(code, 0, err)
        return re.search(r"^(\d+)\. ", self.read(self.ledger).split("## Proposed")[1],
                         re.M).group(1)

    def answering(self, number, *extra):
        return self.run_cli("answer", number, "--pick", "Short", "--source", "me", "--text",
                            "Lines stop at eighty.", "--area", "Every session",
                            "--every-turn", *extra)

    def test_r1_f1_preview_shows_no_append_and_no_cost(self):
        number = self.asked()
        for hand, state in ((H, "holds no generated block"), (None, "is absent")):
            if hand is None:
                os.remove(self.claude)
            else:
                self.write(self.claude, hand)
            before = snapshot(self.tmp)
            code, out, err = self.answering(number, "--preview")
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshot(self.tmp), before, state)
            self.assertIn("answer --preview: CLAUDE.md %s; %s\n" % (state, INIT), out)
            self.assertNotIn(BEGIN, out, state)
            self.assertNotIn("CLAUDE.md loads", out, state)
            self.assertNotIn("(after the answer)", out, state)

    def test_r1_f2_answer_over_markers_that_are_not_one_block_names_no_init(self):
        markers = "decisions: CLAUDE.md: the GENERATED markers are not one BEGIN before one END\n"
        for marked in (H + BEGIN + "\n", H + END + "\n", H + END + "\nx\n" + BEGIN + "\n"):
            number = self.asked()
            self.write(self.claude, marked)
            code, out, err = self.answering(number, "--preview")
            self.assertEqual(code, 0, err)
            self.assertIn("answer --preview: CLAUDE.md: the GENERATED markers are not one "
                          "BEGIN before one END; render would refuse it, so no diff\n", out)
            code, out, err = self.answering(number)
            self.assertEqual(code, 0, err)
            self.assertIn("answer: %s, Short;" % number, out)
            self.assertEqual(self.read(self.claude), marked)
            self.assertEqual(err, "answer: CLAUDE.md: the GENERATED markers are not one BEGIN "
                                  "before one END; the block is left as it is\n", marked)
            self.assertNotIn("init", out + err)
            for verb in ("init", "render"):
                code, _, said = self.run_cli(verb)
                self.assertEqual((code, said), (2, markers), (verb, marked))
            self.assertEqual(self.read(self.claude), marked)

    def test_notes_4_init_over_a_ledger_refuses_a_text_that_holds_not_one_block(self):
        import decisions.init
        self.write(self.claude, H)
        before = snapshot(self.tmp)
        held = decisions.init.apply
        decisions.init.apply = lambda text, generated, target=None: (
            held(text, generated, target) + generated)
        try:
            code, out, err = self.run_cli("init")
        finally:
            decisions.init.apply = held
        self.assertEqual(code, 2, out)
        self.assertIn("CLAUDE.md: its block could not be placed", err)
        self.assertIn("nothing written", err)
        self.assertEqual(snapshot(self.tmp), before)
