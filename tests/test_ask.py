"""`ask` (d18 act 3): the open questions as AskUserQuestion calls, rendered once
through a stub respeak (`RESPEAK_ROOT`) and written back; with no respeak, or
a failed render, the text stays, one warning, exit 0."""

import io
import json
import os
import shutil
import tempfile
from unittest import mock

import decisions
from decisions import questions
from tests.test_new import PARTS, QUESTION, SAMPLE_QUESTIONS, Base, sha

# The stub renderer logs its argv, notes the contract, and writes $STUB_TEXT to --out;
# $STUB_ENV, when set, takes its working directory, the helper marks and the repo config
# it sees; $STUB_EDIT_TEXT, when set, overwrites $STUB_EDIT first (an edit during the
# render); $STUB_ERR goes to stderr, its backslash escapes read as printf's %b reads them;
# $STUB_GONE, when set, removes --out and exits 0.
STUB = """#!/bin/bash
printf '%s\\n' "$*" >> "$STUB_LOG"
[ -n "$STUB_ENV" ] && printf 'cwd=%s helper=%s depth=%s render_depth=%s\\n' "$(pwd -P)" \
  "${CLAUDE_SESSION_HELPER-unset}" "${CLAUDE_SESSION_DEPTH-unset}" \
  "${RESPEAK_RENDER_DEPTH-unset}" >> "$STUB_ENV"
[ -n "$STUB_ENV" ] && cat .claude/respeak/config.yaml >> "$STUB_ENV" 2>/dev/null
while [ $# -gt 0 ]; do
  case "$1" in --out) O="$2"; shift 2 ;; --contract) C="$2"; shift 2 ;; *) shift ;; esac
done
grep -q 'Rewrite only the prose' "$C" && echo contract >> "$STUB_LOG"
[ -n "$STUB_EDIT" ] && printf '%s' "$STUB_EDIT_TEXT" > "$STUB_EDIT"
[ -n "$STUB_ERR" ] && printf '%b' "$STUB_ERR" >&2
[ -n "$STUB_EXIT" ] && exit "$STUB_EXIT"
[ -n "$STUB_GONE" ] && { rm -f "$O"; exit 0; }
cp "$STUB_TEXT" "$O"
"""
REWORDS = (("The tool runs under 3.12.", "Today the tool runs on 3.12."),
           ("Pin 3.12. Revisit", "Keep 3.12 pinned. Revisit"))


class Ask(Base):

    def setUp(self):
        super().setUp()
        side = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, side)
        self.stub = os.path.join(side, "respeak")
        os.makedirs(os.path.join(self.stub, "scripts"))
        self.write(os.path.join(self.stub, "scripts", "respeak-render.sh"), STUB)
        self.log, self.text = os.path.join(side, "log"), os.path.join(side, "text")
        self.env = {"RESPEAK_ROOT": self.stub, "STUB_LOG": self.log, "STUB_TEXT": self.text}

    def new(self, *titles):
        for title in titles:
            argv = list(PARTS)
            argv[argv.index("--title") + 1] = title
            code, _, err = self.run_cli(*argv)
            self.assertEqual(code, 0, err)

    def rendered(self, reword=(), lose=()):
        """The stub's text: every open block, reworded where named, losing its marker."""
        blocks = []
        for block in questions.parse(self.read(self.questions)).blocks:
            text = block.text
            if block.number in reword:
                for old, new in REWORDS:
                    text = text.replace(old, new)
            if block.number in lose:
                text = text.replace(" (Recommended)", "")
            blocks.append(text)
        self.write(self.text, "\n\n".join(blocks) + "\n")

    def ask(self, *argv, env=None):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, self.env if env is None else env):
            code = decisions.main(["ask"] + list(argv) + ["--ledger", self.ledger],
                                  out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def runs(self):
        with open(self.log, encoding="utf-8") as handle:
            return handle.read().splitlines()

    def test_five_questions_two_calls(self):
        self.new("Q one", "Q two", "Q three", "Q four", "Q five")
        self.rendered()
        code, out, err = self.ask()
        self.assertEqual((code, err), (0, ""))
        calls = json.loads(out)
        self.assertEqual([len(c["questions"]) for c in calls], [4, 1])
        self.assertEqual([q["header"] for c in calls for q in c["questions"]],
                         ["Decision %d" % n for n in range(9, 14)])
        self.assertEqual(len(self.runs()), 2)

    def test_payload_fields(self):
        self.write(self.questions, "# Decisions for the owner\n\n"
                   + QUESTION.replace("## 9.", "## 999.") + "\n## Decided without asking\n")
        code, out, err = self.ask("999", env={})
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), [{"questions": [{
            "header": "Decision 999",
            "question": "The tool runs under 3.12. Pin 3.12, or follow the newest?",
            "options": [{"label": "Pin (Recommended)",
                         "description": "Keeps one interpreter. Pin 3.12."},
                        {"label": "Follow", "description": "Tracks releases."}],
            "multiSelect": False}]}])
        self.assertEqual(len("Decision 999"), 12)
        self.assertNotIn("metadata", out)
        self.assertNotIn("preview", out)

    def env_log(self):
        return os.path.join(os.path.dirname(self.log), "env")

    def test_one_render_carries_the_repo_config(self):
        """d-n2 item 5: one render, run in its temp dir, which carries a copy of the
        repo's respeak configuration (`.claude/respeak/` beside the ledger)."""
        config = os.path.join(self.tmp, ".claude", "respeak", "config.yaml")
        os.makedirs(os.path.dirname(config))
        self.write(config, "version: 3\n")
        self.new("Q one", "Q two", "Q three")
        self.rendered()
        before = sha(self.questions)
        code, _, err = self.ask(env=dict(self.env, STUB_ENV=self.env_log()))
        self.assertEqual((code, err), (0, ""))
        runs = self.runs()
        self.assertEqual(runs[1:], ["contract"])
        argv = runs[0].split()
        self.assertEqual(argv[argv.index("--mode") + 1], "technical")
        self.assertEqual(argv[argv.index("--max-rounds") + 1], "2")
        seen = self.read(self.env_log()).splitlines()
        self.assertEqual(seen[0].split()[0], "cwd=" + os.path.realpath(
            os.path.dirname(argv[argv.index("--source") + 1])))
        self.assertEqual(seen[1:], ["version: 3"])
        self.assertEqual(sorted(os.listdir(self.tmp)),
                         [".claude", "DECISIONS.md", "OPEN-QUESTIONS.md"])
        self.assertEqual(sha(self.questions), before)

    def test_the_render_reads_open_questions_md_in_a_temp_dir(self):
        """d-n2 item 5 (1b F10, L35): the render's source and output are named
        OPEN-QUESTIONS.md in a temp dir away from the ledger, gone after the run, so no
        `.decisions-ask-*` temp sits beside the file, even after a kill."""
        self.new("Q one")
        self.rendered(reword=(9,))
        code, _, err = self.ask()
        self.assertEqual((code, err), (0, ""))
        argv = self.runs()[0].split()
        source = argv[argv.index("--source") + 1]
        self.assertEqual(os.path.basename(source), "OPEN-QUESTIONS.md")
        self.assertEqual(os.path.basename(argv[argv.index("--out") + 1]), "OPEN-QUESTIONS.md")
        for flag in ("--source", "--out", "--contract"):
            path = os.path.realpath(argv[argv.index(flag) + 1])
            self.assertFalse(path.startswith(os.path.realpath(self.tmp) + os.sep), path)
        self.assertFalse(os.path.exists(os.path.dirname(source)))
        self.assertEqual(sorted(os.listdir(self.tmp)), ["DECISIONS.md", "OPEN-QUESTIONS.md"])
        self.assertIn("Today the tool runs on 3.12.", self.read(self.questions))

    def test_the_render_runs_as_a_marked_helper(self):
        """d-n2 item 9 (L37, L59): the renderer's child is a session helper one level down,
        refused past depth 2 or inside a render, and respeak's own guard is left to it."""
        self.new("Q one")
        self.rendered()
        for caller, child in ((None, "1"), ("1", "2")):
            with self.subTest(caller=caller):
                extra = {} if caller is None else {"CLAUDE_SESSION_DEPTH": caller}
                code, _, err = self.ask(env=dict(self.env, STUB_ENV=self.env_log(), **extra))
                self.assertEqual((code, err), (0, ""))
                fields = self.read(self.env_log()).splitlines()[-1].split()
                self.assertEqual(fields[1:], ["helper=1", "depth=" + child, "render_depth=unset"])
        runs = len(self.runs())
        for name, value, words in (("CLAUDE_SESSION_DEPTH", "2", "past depth 2"),
                                   ("CLAUDE_SESSION_DEPTH", "x", "CLAUDE_SESSION_DEPTH 'x'"),
                                   ("RESPEAK_RENDER_DEPTH", "1", "RESPEAK_RENDER_DEPTH is set"),
                                   ("RESPEAK_DEPTH", "1", "RESPEAK_DEPTH is set")):
            with self.subTest(name=name, value=value):
                code, out, err = self.ask(env=dict(self.env, **{name: value}))
                self.assertEqual(code, 0, err)
                self.assertEqual(len(err.splitlines()), 1, err)
                self.assertIn(words, err)
                self.assertIn("the questions stay as written", err)
                self.assertEqual(json.loads(out)[0]["questions"][0]["header"], "Decision 9")
        self.assertEqual(len(self.runs()), runs)

    def test_a_render_that_empties_a_part_keeps_the_text(self):
        """d-n2 item 1 (1b F2): a blank line after **Recommendation.** empties the part, so
        the render is not kept and the description keeps the recommendation."""
        self.new("Q one")
        old, ledger = self.read(self.questions), sha(self.ledger)
        self.write(self.text, questions.parse(old).blocks[0].text.replace(
            "The tool runs under 3.12.", "Today the tool runs on 3.12.").replace(
            "**Recommendation.** Pin 3.12.", "**Recommendation.**\n\nPin 3.12.") + "\n")
        code, out, err = self.ask()
        self.assertEqual(code, 0, err)
        self.assertIn("lost part of question 9", err)
        self.assertEqual((self.read(self.questions), sha(self.ledger)), (old, ledger))
        self.assertEqual(json.loads(out)[0]["questions"][0]["options"][0]["description"],
                         "Keeps one interpreter. Pin 3.12.")

    def test_a_render_that_drops_an_effect_keeps_the_text(self):
        """d-n2 fix round B1: an option bullet that loses its effect is not kept, so the
        file keeps the effect and the payload's description carries it."""
        self.new("Q one")
        old = self.read(self.questions)
        self.write(self.text, questions.parse(old).blocks[0].text.replace(
            "The tool runs under 3.12.", "Today the tool runs on 3.12.").replace(
            "- **Follow.** Tracks releases.", "- **Follow.**") + "\n")
        code, out, err = self.ask()
        self.assertEqual(code, 0, err)
        self.assertIn("the render lost part of question 9; its text stays", err)
        self.assertEqual(self.read(self.questions), old)
        self.assertEqual(json.loads(out)[0]["questions"][0]["options"][1]["description"],
                         "Tracks releases.")

    def test_a_stderr_not_utf8_or_holding_escapes_keeps_the_payload(self):
        """d-n2 fix round N1: a renderer that exits 3 after bytes that are not UTF-8, or
        after terminal escapes and a long line, leaves one warning of at most 200
        characters for its line, no control character in it, and the payload."""
        self.new("Q one")
        self.rendered(reword=(9,))
        head, tail = "ask: the render exited 3: ", "; the questions stay as written\n"
        for name, said in (("not UTF-8", "\\377\\376 broken\\n"),
                           ("escapes", "\\033]0;title\\007\\033[31mred\\033[0m " + "x" * 300)):
            with self.subTest(case=name):
                code, out, err = self.ask(env=dict(self.env, STUB_EXIT="3", STUB_ERR=said))
                self.assertEqual(code, 0, err)
                self.assertTrue(err.startswith(head) and err.endswith(tail), err)
                line = err[len(head):-len(tail)]
                self.assertLessEqual(len(line), 200)
                self.assertFalse([c for c in line if ord(c) < 32 or ord(c) == 127], line)
                self.assertNotIn("]0;", line)
                self.assertEqual(json.loads(out)[0]["questions"][0]["header"], "Decision 9")

    def test_added_prose_after_the_answer_line_keeps_the_text(self):
        """d-n2 item 1 (L32): prose the render adds after **Your answer:** is no part of
        the block, so the render is not kept."""
        self.new("Q one")
        old = self.read(self.questions)
        self.write(self.text, questions.parse(old).blocks[0].text.replace(
            "The tool runs under 3.12.", "Today the tool runs on 3.12.")
            + "\n\nI would pin it.\n")
        code, _, err = self.ask()
        self.assertEqual(code, 0, err)
        self.assertIn("lost part of question 9", err)
        self.assertEqual(self.read(self.questions), old)

    def test_an_answered_block_is_not_asked(self):
        """d-n2 item 3 (1b F8): a block whose **Your answer:** line is filled in is skipped
        with a warning naming `agentik decisions answer N`, named or not."""
        self.new("Q one", "Q two")
        self.write(self.questions, self.read(self.questions).replace(
            "**Your answer:**\n", "**Your answer:** Pin.\n", 1))
        self.rendered()
        code, out, err = self.ask()
        self.assertEqual(code, 0, err)
        self.assertEqual([q["header"] for c in json.loads(out) for q in c["questions"]],
                         ["Decision 10"])
        self.assertEqual(len(err.splitlines()), 1, err)
        self.assertIn("question 9", err)
        self.assertIn("`agentik decisions answer 9`", err)
        code, out, err = self.ask("9")
        self.assertEqual((code, json.loads(out)), (0, []))
        self.assertIn("`agentik decisions answer 9`", err)

    def test_a_block_the_lint_refuses_is_not_asked(self):
        """d-n2 item 4 (1b F9): a block with five options, which AskUserQuestion rejects,
        is skipped with the lint's words; the others are asked."""
        five = QUESTION.replace("## 9.", "## 999.").replace(
            "- **Follow.** Tracks releases.\n", "- **Follow.** Tracks releases.\n"
            "- **Three.** c.\n- **Four.** d.\n- **Five.** e.\n")
        self.write(self.questions, "# Decisions for the owner\n\n" + QUESTION + "\n" + five
                   + "\n## Decided without asking\n")
        code, out, err = self.ask(env={})
        self.assertEqual(code, 0, err)
        asked = [q for c in json.loads(out) for q in c["questions"]]
        self.assertEqual([q["header"] for q in asked], ["Decision 9"])
        self.assertIn("question 999", err)
        self.assertIn("5 options", err)

    def test_a_read_only_directory_keeps_the_text(self):
        """d-n2 item 6 (1b F12): beside a read-only directory `ask` keeps the text, warns
        once and prints the calls, exit 0, as for a failed render."""
        if os.geteuid() == 0:
            self.skipTest("root writes a read-only directory")
        self.new("Q one")
        self.rendered(reword=(9,))
        before = (sha(self.ledger), sha(self.questions))
        os.chmod(self.tmp, 0o555)
        self.addCleanup(os.chmod, self.tmp, 0o755)
        code, out, err = self.ask()
        self.assertEqual(code, 0, err)
        self.assertEqual(len(err.splitlines()), 1, err)
        self.assertIn("the questions stay as written", err)
        self.assertEqual(json.loads(out)[0]["questions"][0]["header"], "Decision 9")
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)

    def test_a_failed_render_warns_with_its_first_stderr_line(self):
        """d-n2 item 8 (1b F14): the warning names the renderer's exit and its first
        stderr line."""
        self.new("Q one")
        self.rendered(reword=(9,))
        env = dict(self.env, STUB_EXIT="3",
                   STUB_ERR="\nrespeak-render: runner exited 3 (round 1)\nthe second line\n")
        code, _, err = self.ask(env=env)
        self.assertEqual(code, 0)
        self.assertEqual(err, "ask: the render exited 3: respeak-render: runner exited 3 "
                              "(round 1); the questions stay as written\n")

    def test_lost_label_keeps_old_text(self):
        self.new("Q one", "Q two")
        self.rendered(reword=(9, 10), lose=(9,))
        old = questions.parse(self.read(self.questions)).blocks[0].text
        code, out, err = self.ask()
        self.assertEqual(code, 0)
        self.assertIn("lost part of question 9", err)
        now = {b.number: b.text for b in questions.parse(self.read(self.questions)).blocks}
        self.assertEqual(now[9], old)
        self.assertIn("Today the tool runs on 3.12.", now[10])
        self.assertEqual([q["question"][:12] for q in json.loads(out)[0]["questions"]],
                         ["The tool run", "Today the to"])

    def test_ask_writes_back(self):
        shutil.copy(SAMPLE_QUESTIONS, self.questions)
        self.new("Q one", "Q two")
        self.rendered(reword=(9, 10))
        edited = self.read(self.questions).replace(
            "## 10. Q two\n\n**Where things stand.** The tool runs under 3.12.",
            "## 10. Q two\n\n**Where things stand.** Edited by hand on 3.12.")
        env = dict(self.env, STUB_EDIT=self.questions, STUB_EDIT_TEXT=edited)
        code, out, err = self.ask(env=env)
        self.assertEqual((code, err), (0, ""))
        text = self.read(self.questions)
        self.assertIn("## 9. Q one\n\n**Where things stand.** Today the tool runs on 3.12.", text)
        self.assertIn("**Recommendation.** Keep 3.12 pinned. Revisit when 3.13 ships.", text)
        self.assertIn("Edited by hand on 3.12.", text)
        ledger = self.read(self.ledger)
        self.assertIn("\n9. **Q one.** Keep 3.12 pinned. (proposed 2026-09-28; OPEN-QUESTIONS.md)\n",
                      ledger)
        self.assertIn("\n10. **Q two.** Pin 3.12. (proposed 2026-09-28; OPEN-QUESTIONS.md)\n",
                      ledger)
        asked = {q["header"]: q["question"] for q in json.loads(out)[0]["questions"]}
        self.assertEqual(asked["Decision 9"],
                         "Today the tool runs on 3.12. Pin 3.12, or follow the newest?")
        self.assertEqual(decisions.main(["render", "--lint", "--ledger", self.ledger],
                                        out=io.StringIO(), err=io.StringIO()), 0)
        self.new("Q three")
        self.rendered(reword=(11,))
        before = (sha(self.ledger), sha(self.questions))
        real = os.replace

        def flaky(src, dst, *args, **kwargs):
            if os.path.realpath(dst) == os.path.realpath(self.ledger):
                raise PermissionError(1, "Operation not permitted")
            return real(src, dst, *args, **kwargs)

        with mock.patch("os.replace", flaky):
            code, out, err = self.ask("11")
        self.assertEqual((code, out), (2, ""))
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        self.assertEqual(sorted(os.listdir(self.tmp)), ["DECISIONS.md", "OPEN-QUESTIONS.md"])

    def test_no_respeak_exits_0(self):
        self.new("Q one")
        before = sha(self.questions)
        for name, env in (("no root", {}), ("render exits 1", dict(self.env, STUB_EXIT="1"))):
            with self.subTest(case=name):
                self.rendered(reword=(9,))
                code, out, err = self.ask(env=env)
                self.assertEqual(code, 0)
                self.assertEqual(len(err.splitlines()), 1, err)
                self.assertIn("the questions stay as written", err)
                self.assertEqual(json.loads(out)[0]["questions"][0]["header"], "Decision 9")
                self.assertEqual(sha(self.questions), before)
                self.assertEqual(sorted(os.listdir(self.tmp)),
                                 ["DECISIONS.md", "OPEN-QUESTIONS.md"])
        self.assertEqual(self.ask("12")[0], 2)

    def test_an_unreadable_render_keeps_the_text(self):
        """Round 1 F4: the renderer exits 0, but --out is gone or not UTF-8; `ask` warns once,
        keeps the text, prints the payload and exits 0."""
        self.new("Q one")
        before = sha(self.questions)
        for name in ("out gone", "out not UTF-8"):
            with self.subTest(case=name):
                env = dict(self.env)
                if name == "out gone":
                    self.rendered(reword=(9,))
                    env["STUB_GONE"] = "1"
                else:
                    with open(self.text, "wb") as handle:
                        handle.write(b"\xff\xfe")
                code, out, err = self.ask(env=env)
                self.assertEqual(code, 0, err)
                self.assertEqual(len(err.splitlines()), 1, err)
                self.assertIn("the questions stay as written", err)
                self.assertEqual(json.loads(out)[0]["questions"][0]["header"], "Decision 9")
                self.assertEqual(sha(self.questions), before)
                self.assertEqual(sorted(os.listdir(self.tmp)),
                                 ["DECISIONS.md", "OPEN-QUESTIONS.md"])

    def test_a_render_that_drops_the_mark_keeps_the_text(self):
        """Round 1 F6: a render whose choice no longer ends in `?` is not kept, so the
        payload's question still ends in `?`."""
        self.new("Q one")
        old = self.read(self.questions)
        self.write(self.text, questions.parse(old).blocks[0].text.replace(
            "The tool runs under 3.12.", "Today the tool runs on 3.12.").replace(
            "Pin 3.12, or follow the newest?", "Choose between pinning 3.12 and the newest."))
        code, out, err = self.ask()
        self.assertEqual(code, 0, err)
        self.assertIn("lost part of question 9", err)
        self.assertEqual(self.read(self.questions), old)
        self.assertTrue(json.loads(out)[0]["questions"][0]["question"].endswith("?"))
