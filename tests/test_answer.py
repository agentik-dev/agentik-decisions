"""`answer` (d18 act 2): the owner's answer to question N becomes entry N, an
amendment or no entry; the question and its Proposed line leave, an Answered
line stays, and both files are written or neither."""

import io
import os
import re
import shutil
from unittest import mock

import decisions
from decisions.ledger import LEGACY
from decisions.render import BEGIN, END
from tests.hermetic import SAMPLE
from tests.test_new import PARTS, SAMPLE_QUESTIONS, Base, sha

ENTRY9 = ("9. **Pin the interpreter.** Pin 3.12. (2026-09-28; the owner's answer to "
          "decision 9, the sitting)")
# Entry 3's paragraph in the sample, 64 characters, and whole paragraphs that replace it.
OLD3 = "The tool runs under Python 3.12 from the standard library alone."
ONLY_312 = "The tool runs under Python 3.12 only, from the standard library alone."
WHOLE_313 = "The tool runs under Python 3.13 from the standard library alone."


class Answer(Base):

    def setUp(self):
        super().setUp()
        shutil.copy(SAMPLE_QUESTIONS, self.questions)
        self.new("Pin the interpreter")

    def new(self, title):
        argv = list(PARTS)
        argv[argv.index("--title") + 1] = title
        code, _, err = self.run_cli(*argv)
        self.assertEqual(code, 0, err)

    def answer(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["answer"] + list(argv) + ["--ledger", self.ledger],
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def lint(self):
        out = io.StringIO()
        self.assertEqual(decisions.main(["render", "--lint", "--ledger", self.ledger],
                                        out=out, err=io.StringIO()), 0, out.getvalue())

    def test_pick_writes_entry_n(self):
        code, out, err = self.answer("9", "--pick", "PIN (Recommended)", "--source", "the sitting",
                                     "--text", "Pin 3.12.", "--area", "build")
        self.assertEqual(code, 0, err)
        self.assertIn("answer: 9, Pin; entry 9 under `### Build`", out)
        ledger = self.read(self.ledger)
        self.assertIn("4. **Tests first.** Every verb has its own tests. (2026-09-04; the sample)"
                      "\n\n%s\n\n### Build tools" % ENTRY9, ledger)
        self.assertNotIn("9. **Pin the interpreter.** Pin 3.12. (proposed", ledger)
        self.assertIn("8. **A second interpreter.**", ledger)
        questions = self.read(self.questions)
        self.assertNotIn("## 9.", questions)
        self.assertTrue(questions.endswith(
            "## Answered\n\n- 9. Pin the interpreter: Pin (2026-09-28; the sitting)\n"))
        self.new("Name the gate")
        code, _, err = self.answer("10", "--other", "Call it  the gate", "--source", "chat",
                                   "--text", "The gate is make.", "--area", "Operations")
        self.assertEqual(code, 0, err)
        ledger = self.read(self.ledger)
        self.assertIn("### Release\n\n7. **Releases follow the manifest.** A release name equals "
                      "the manifest version. (2026-09-07; the sample)\n\n### Operations\n\n"
                      "10. **Name the gate.** The gate is make. (2026-09-28; the owner's answer "
                      "to decision 10, chat)\n\n## Proposed", ledger)
        self.assertIn("- 9. Pin the interpreter: Pin (2026-09-28; the sitting)\n"
                      "- 10. Name the gate: Other: Call it the gate (2026-09-28; chat)\n",
                      self.read(self.questions))
        self.lint()

    def test_amends_keeps_earlier_amendments(self):
        """D19, d31: `--amends` writes the tail in form T2, so an earlier amendment
        stays as a count and the range of its dates, and the latest reads whole."""
        code, _, err = self.answer("9", "--pick", "pin", "--source", "s1", "--text",
                                   ONLY_312, "--amends", "3", "--shorter")
        self.assertEqual(code, 0, err)
        self.new("Move on")
        code, _, err = self.answer("10", "--pick", "follow", "--source", "s2", "--text",
                                   WHOLE_313, "--amends", "3", "--shorter")
        self.assertEqual(code, 0, err)
        lines = [l for l in self.read(self.ledger).splitlines() if l.startswith("3. ")]
        self.assertEqual(lines, ["3. **One interpreter.** %s (2026-09-03; amended 2 times, "
                                 "2026-09-10 to 2026-09-28; amended 2026-09-28, the owner's "
                                 "answer to decision 10, s2)" % WHOLE_313])
        self.assertEqual(self.answer("11", "--pick", "pin", "--source", "s", "--text", "t",
                                     "--amends", "3")[0], 2)
        self.lint()

    def test_amends_keeps_nested_parenthetical_balanced(self):
        """D19, closing round 2a F6, d31: a tail with `(twice); amended` inside a nested
        parenthetical holds no dated amendment, so form T2 keeps its date alone and the
        entry's parentheses stay balanced."""
        tail = "2026-09-03; the sample (moved (twice); amended in place)"
        self.write(self.ledger, self.read(self.ledger).replace(
            "(2026-09-03; the sample, amended 2026-09-10 (twice))", "(%s)" % tail))
        code, _, err = self.answer("9", "--pick", "pin", "--source", "s1", "--text",
                                   ONLY_312, "--amends", "3", "--shorter")
        self.assertEqual(code, 0, err)
        lines = [l for l in self.read(self.ledger).splitlines() if l.startswith("3. ")]
        self.assertEqual(lines, ["3. **One interpreter.** %s (2026-09-03; amended 2026-09-28, "
                                 "the owner's answer to decision 9, s1)" % ONLY_312])
        self.assertEqual(lines[0].count("("), lines[0].count(")"))
        self.lint()

    def test_amends_shorter_writes_and_prints_replaced(self):
        """D21, d30: `--shorter` lets a paragraph that drops a sentence through, and the
        run still prints `replaced:` with the old paragraph after its done line."""
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text",
                                     "Runs under 3.13.", "--amends", "3", "--shorter")
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("answer: 9, Pin; entry 3 amended in "), out)
        self.assertEqual(lines[1], "replaced: " + OLD3)
        self.assertIn("3. **One interpreter.** Runs under 3.13. (2026-09-03; amended once, "
                      "2026-09-10; amended 2026-09-28, the owner's answer to decision 9, s)\n",
                      self.read(self.ledger))
        self.assertEqual(lines[2], "tail was: (2026-09-03; the sample, amended 2026-09-10 "
                                   "(twice))")  # d31
        self.lint()

    def test_amends_whole_paragraph_prints_replaced(self):
        """D21: a whole paragraph is written (d30: with `--shorter`, as it swaps entry 3's
        one sentence), and the run prints `replaced:` with the old body, between the
        bold title and the tail, as it stood."""
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text",
                                     WHOLE_313, "--amends", "3", "--shorter")
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("answer: 9, Pin; entry 3 amended in "), out)
        self.assertEqual(lines[1], "replaced: " + OLD3)
        self.assertEqual(sum(l.startswith("replaced: ") for l in lines), 1)
        self.assertIn("3. **One interpreter.** %s (2026-09-03;" % WHOLE_313,
                      self.read(self.ledger))
        self.lint()

    def test_shorter_without_amends_refuses(self):
        """D21: `--shorter` is valid only with `--amends`: exit 2, nothing written."""
        before = (sha(self.ledger), sha(self.questions))
        for lands in (["--area", "build"], ["--no-entry"]):
            code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text",
                                         "Pin 3.12.", "--shorter", *lands)
            self.assertEqual((code, out), (2, ""), err)
            self.assertIn("--shorter is valid only with --amends", err)
            self.assertIn("nothing written", err)
            self.assertEqual((sha(self.ledger), sha(self.questions)), before)

    def test_body_only_refuses_a_title(self):
        """D22: `--text` is the body only; one that opens with a bold title, alone or
        after its number, is refused, exit 2, and both files stay byte-identical."""
        before = (sha(self.ledger), sha(self.questions))
        for text in ("**Pin the interpreter.** Pin 3.12.", "9. **Pin the interpreter.** Pin 3.12.",
                     "  **Pin**  3.12."):
            with self.subTest(text=text):
                code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text",
                                             text, "--area", "build")
                self.assertEqual((code, out), (2, ""), err)
                for part in ("opens with a bold title", "body only", "nothing written"):
                    self.assertIn(part, err)
                self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, ".new.lock")))

    def test_body_only_refuses_a_tail(self):
        """D22: a `--text` that ends in a `(YYYY-MM-DD; source)` tail is refused, for a
        new entry and with `--amends`, whose `--text` is the whole body in force."""
        before = (sha(self.ledger), sha(self.questions))
        cases = (("Pin 3.12. (2026-09-28; the sitting)", ["--area", "build"], False),
                 ("Pin 3.12 (2026-09-28 ~16:15, the sitting)", ["--area", "build"], False),
                 ("%s (2026-09-03; the sample)" % WHOLE_313, ["--amends", "3"], False),
                 ("3. **One interpreter.** %s (2026-09-03; the sample)" % WHOLE_313,
                  ["--amends", "3"], True))
        for text, lands, titled in cases:
            with self.subTest(text=text):
                code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text",
                                             text, *lands)
                self.assertEqual((code, out), (2, ""), err)
                self.assertIn("ends in a (date; source) tail", err)
                self.assertEqual("opens with a bold title" in err, titled, err)
                self.assertIn("body only", err)
                self.assertIn("nothing written", err)
                self.assertEqual((sha(self.ledger), sha(self.questions)), before)

    def test_body_only_passes_inner_parts(self):
        """D22: only the body's start and end are read: a dated parenthetical before
        the final period and a `**` past the start pass; `--no-entry` ignores `--text`."""
        text = "Pin 3.12 (since 2026-09-28; the sitting), and never `**` globs."
        code, _, err = self.answer("9", "--pick", "pin", "--source", "s", "--text", text,
                                   "--area", "build")
        self.assertEqual(code, 0, err)
        self.assertIn("\n9. **Pin the interpreter.** %s (2026-09-28; the owner's answer to "
                      "decision 9, s)\n" % text, self.read(self.ledger))
        self.lint()
        self.new("Move on")
        code, out, err = self.answer("10", "--pick", "pin", "--source", "s", "--text",
                                     "**T.** P (2026-09-28; s)", "--no-entry")
        self.assertEqual(code, 0, err)
        self.assertIn("answer: 10, Pin; no entry", out)
        self.lint()

    def test_no_entry_retires_number(self):
        code, _, err = self.answer("9", "--pick", "follow", "--source", "s", "--no-entry")
        self.assertEqual(code, 0, err)
        ledger = decisions.parse(self.read(self.ledger))
        self.assertNotIn(9, [e.number for e in ledger.entries])
        self.assertIn("- 9. Pin the interpreter: Follow (2026-09-28; s)", self.read(self.questions))
        code, out, _ = self.run_cli(*PARTS)
        self.assertEqual(code, 0)
        self.assertIn("new: 10", out)

    def test_answer_writes_above_the_marker(self):
        """d18 L4: an older ledger adopts the shape; the entry lands above the marker, in a
        new area even when an area of that name sits below it. d-n2 item 2: the new number
        counts the legacy entry 1, so the question and its entry are 2."""
        legacy = LEGACY + "\n\n## Old rulings\n\n### Build\n\n1. An old build ruling.\n"
        self.write(self.ledger, "# t\n\n## In force\n\n" + legacy)
        os.remove(self.questions)
        self.new("Pin the interpreter")
        code, out, err = self.answer("2", "--pick", "pin", "--source", "s", "--text", "Pin it.",
                                     "--area", "Build")
        self.assertEqual(code, 0, err)
        got = self.read(self.ledger)
        self.assertTrue(got.startswith("# t\n\n## In force\n\n### Build\n\n"
                                       "2. **Pin the interpreter.** Pin it. (2026-09-28; "))
        self.assertTrue(got.endswith("\n" + legacy))
        self.assertEqual(decisions.parse(got).legacy[1], legacy.splitlines()[1:])
        self.lint()

    def test_pick_ignores_the_marker_in_any_case(self):
        """Round 1 F1: design section 1.2, the match ignores case and ` (Recommended)`."""
        code, out, err = self.answer("9", "--pick", "pin (recommended)", "--source", "s",
                                     "--no-entry")
        self.assertEqual(code, 0, err)
        self.assertIn("answer: 9, Pin; no entry", out)
        self.new("Move on")
        code, out, err = self.answer("10", "--pick", "PIN (RECOMMENDED)", "--source", "s",
                                     "--no-entry")
        self.assertEqual(code, 0, err)
        self.assertIn("answer: 10, Pin; no entry", out)
        self.lint()

    def test_amending_an_untitled_entry_refuses(self):
        """Round 2 F4: an entry in force without a bold title is refused, exit 2, and
        nothing is written."""
        self.write(self.ledger, self.read(self.ledger).replace(
            "3. **One interpreter.** ", "3. One interpreter: "))
        before = (sha(self.ledger), sha(self.questions))
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text", "x.",
                                     "--amends", "3")
        self.assertEqual((code, out), (2, ""), err)
        self.assertIn("entry 3 has no bold title", err)
        self.assertIn("nothing written", err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, ".new.lock")))

    def test_a_mentioned_marker_is_no_block(self):
        """Round 2 F1: markers count only alone on their lines, as `render` counts them; a
        CLAUDE.md that mentions one gets no block appended, and stderr says so."""
        claude = os.path.join(self.tmp, "CLAUDE.md")
        mention = ("# Notes\n\nThe block sits between `<!-- BEGIN GENERATED: decisions -->` "
                   "and `<!-- END GENERATED: decisions -->`.\n")
        self.write(claude, mention)
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text",
                                     "Hold it.", "--area", "Every session", "--every-turn")
        self.assertEqual(code, 0, err)
        self.assertIn("CLAUDE.md holds no GENERATED markers", err)
        self.assertNotIn("rewrote the block", out)
        self.assertEqual(self.read(claude), mention)

    def test_unknown_label_exits_2(self):
        before = (sha(self.ledger), sha(self.questions))
        for argv in (["--pick", "Wait"], ["--pick", ""], ["--other", " "]):
            with self.subTest(argv=argv):
                code, out, err = self.answer("9", *argv, "--source", "s", "--no-entry")
                self.assertEqual((code, out), (2, ""))
                self.assertIn("nothing written", err)
                self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        self.assertEqual(self.answer("12", "--pick", "Pin", "--source", "s", "--no-entry")[0], 2)
        self.assertEqual(self.answer("9", "--pick", "Pin", "--source", "s", "--area", "A")[0], 2)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)

    def test_both_files_or_neither(self):
        before = (sha(self.ledger), sha(self.questions))
        real = os.replace

        def flaky(src, dst, *args, **kwargs):
            if os.path.realpath(dst) == os.path.realpath(self.ledger):
                raise PermissionError(1, "Operation not permitted")
            return real(src, dst, *args, **kwargs)

        with mock.patch("os.replace", flaky):
            code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--no-entry")
        self.assertEqual((code, out), (2, ""))
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        with open(self.questions, "a", encoding="utf-8") as handle:
            handle.write("\n## 12. Written by hand\n\n**Your answer:**\n")
        before = (sha(self.ledger), sha(self.questions))
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--no-entry")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("fails the lint", err)
        self.assertIn("question 12: the four labels in order", err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        self.assertEqual(sorted(os.listdir(self.tmp)), ["DECISIONS.md", "OPEN-QUESTIONS.md"])

    def test_a_failed_block_write_keeps_the_answer(self):
        # d18 1a obs: both files are written before the block; a failed block write is a
        # warning that names `agentik decisions render`, never exit 2
        claude = os.path.join(self.tmp, "CLAUDE.md")
        self.assertEqual(decisions.main(["render", "--ledger", self.ledger], out=io.StringIO(),
                                        err=io.StringIO()), 0)
        before = self.read(claude)
        real = os.replace

        def flaky(src, dst, *args, **kwargs):
            if os.path.realpath(dst) == os.path.realpath(claude):
                raise PermissionError(1, "Operation not permitted")
            return real(src, dst, *args, **kwargs)

        with mock.patch("os.replace", flaky):
            code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text",
                                         "Pin it.", "--area", "Every session",
                                         "--every-turn")
        self.assertEqual(code, 0, err)
        self.assertIn("answer: 9, Pin; entry 9 under `### Every session`", out)
        self.assertIn("9. **Pin the interpreter.** Pin it.", self.read(self.ledger))
        self.assertNotIn("## 9.", self.read(self.questions))
        self.assertIn("`agentik decisions render --ledger %s`" % self.ledger, err)
        self.assertIn("Operation not permitted", err)
        self.assertEqual(self.read(claude), before)
        self.lint()

    def test_into_the_ledger_itself_exits_2(self):
        # B1 (d-n1 review): `answer --into` the ledger, by path or hard link, writes nothing
        before = (sha(self.ledger), sha(self.questions))
        hard = os.path.join(self.tmp, "hard.md")
        os.link(self.ledger, hard)
        for into in (self.ledger, hard):
            with self.subTest(into=os.path.basename(into)):
                code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text",
                                             "Pin it.", "--area", "build", "--into", into)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("the ledger itself", err)
                self.assertEqual((sha(self.ledger), sha(self.questions)), before)

    def test_new_and_answer_keep_crlf_files(self):
        # F4: `new` and `answer` write a CRLF ledger and questions file back in CRLF
        for path in (self.ledger, self.questions):
            with open(path, "rb") as handle:
                data = handle.read()
            with open(path, "wb") as handle:
                handle.write(data.replace(b"\n", b"\r\n"))
        self.new("Name the gate")
        code, _, err = self.answer("9", "--pick", "pin", "--source", "s", "--text", "Pin 3.12.",
                                   "--area", "build")
        self.assertEqual(code, 0, err)
        for path, part in ((self.ledger, b"9. **Pin the interpreter.**"),
                           (self.questions, b"## 10. Name the gate")):
            with self.subTest(path=os.path.basename(path)):
                with open(path, "rb") as handle:
                    data = handle.read()
                self.assertIn(part, data)
                self.assertEqual(data.count(b"\n"), data.count(b"\r\n"))
        self.lint()

    def test_block_rewritten_only_with_markers(self):
        claude = os.path.join(self.tmp, "CLAUDE.md")
        self.write(claude, "# Notes\n")
        code, _, err = self.answer("9", "--pick", "pin", "--source", "s", "--text", "Pin it.",
                                   "--area", "Every session", "--every-turn")
        self.assertEqual(code, 0, err)
        self.assertIn("CLAUDE.md holds no GENERATED markers", err)
        self.assertEqual(self.read(claude), "# Notes\n")
        self.assertEqual(decisions.main(["render", "--ledger", self.ledger], out=io.StringIO(),
                                        err=io.StringIO()), 0)
        other = os.path.join(self.tmp, "elsewhere.md")
        shutil.copy(claude, other)
        self.new("Keep the lock")
        code, out, err = self.answer("10", "--pick", "pin", "--source", "s", "--text",
                                     "Hold the lock.", "--area", "Every session",
                                     "--every-turn")
        self.assertEqual(code, 0, err)
        self.assertIn("rewrote the block", out)
        self.assertIn("Keep the lock", self.read(claude))
        self.assertNotIn("Keep the lock", self.read(other))
        self.new("Name the gate")
        code, out, err = self.answer("11", "--pick", "pin", "--source", "s", "--text", "Gate.",
                                     "--area", "Every session", "--into", other,
                                     "--every-turn")
        self.assertEqual(code, 0, err)
        self.assertIn("Name the gate", self.read(other))
        self.assertNotIn("Name the gate", self.read(claude))
        self.assertEqual(sha(SAMPLE), sha(SAMPLE))

    def test_area_prefix_resolves_and_prints_the_heading(self):
        # d-n3 item 7 (1b F6, 2b obs): `--area` resolves as `show --area` does and the
        # success line names the heading matched; two matches refuse.
        before = (sha(self.ledger), sha(self.questions))
        code, out, err = self.answer("9", "--pick", "Pin", "--source", "s", "--text",
                                     "Pin 3.12.", "--area", "bui")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("ambiguous", err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        code, out, err = self.answer("9", "--pick", "Pin", "--source", "s", "--text",
                                     "Pin 3.12.", "--area", "REL")
        self.assertEqual(code, 0, err)
        self.assertIn("entry 9 under `### Release`", out)
        ledger = self.read(self.ledger)
        self.assertEqual(ledger.count("### Release\n"), 1)
        self.assertIn("(2026-09-07; the sample)\n\n9. **Pin the interpreter.**", ledger)
        self.lint()

    def test_area_is_stripped(self):
        # d-n3 item 7 (2a obs): `--area` is cleaned as `--source` is.
        code, out, err = self.answer("9", "--pick", "Pin", "--source", "s", "--text",
                                     "Pin 3.12.", "--area", "  build ")
        self.assertEqual(code, 0, err)
        self.assertIn("entry 9 under `### Build`", out)
        self.assertEqual(self.read(self.ledger).count("### Build\n"), 1)
        self.lint()

    def test_amends_refuses_a_tail_without_a_date(self):
        # d-n3 item 11 (2a F7, D19): no `(; amended DATE, ...)`; nothing written.
        line = ("4. **Tests first.** Every verb has its own tests. (2026-09-04; the sample)")
        original = self.read(self.ledger)
        for tail in ("", " (the sample)", " (the sample, 2026-09-04)"):
            with self.subTest(tail=tail):
                self.write(self.ledger, original.replace(
                    line, "4. **Tests first.** Every verb has its own tests.%s" % tail))
                before = (sha(self.ledger), sha(self.questions))
                code, out, err = self.answer("9", "--pick", "Pin", "--source", "s", "--text",
                                             "Every verb has its own unit tests.",
                                             "--amends", "4")
                self.assertEqual((code, out), (2, ""))
                self.assertIn("entry 4", err)
                self.assertIn("date", err)
                self.assertEqual((sha(self.ledger), sha(self.questions)), before)

    def test_a_question_title_takes_no_period(self):
        # d-n3 item 2 (the observer's S4): a title ending in `?` gets no `.`.
        self.new("Does the tool pin its interpreter?")
        code, out, err = self.answer("10", "--pick", "Pin", "--source", "s", "--text",
                                     "Pin 3.12.", "--area", "Build")
        self.assertEqual(code, 0, err)
        ledger = self.read(self.ledger)
        self.assertIn("\n10. **Does the tool pin its interpreter?** Pin 3.12. (2026-09-28; ",
                      ledger)
        self.assertNotIn("?.", ledger)
        self.assertIn("- 10. Does the tool pin its interpreter?: Pin (2026-09-28; s)\n",
                      self.read(self.questions))
        self.lint()

    def test_three_amendments_in_a_row_and_a_source_holding_parens(self):
        # D19 left open (d18 2a F7): the live-verb probes, three amendments in a row and a
        # source holding `)` or `;`, each lints clean and keeps every earlier amendment.
        sources = ("chat (the owner); then the charter", "a note; see (b)", "the sitting")
        paragraphs = (ONLY_312, WHOLE_313, OLD3)
        for i, (source, paragraph) in enumerate(zip(sources, paragraphs)):
            number = 9 + i
            if i:
                self.new("Pin it again %d" % i)
            code, _, err = self.answer(str(number), "--pick", "Pin", "--source", source,
                                       "--text", paragraph, "--amends", "3", "--shorter")
            self.assertEqual(code, 0, err)
            self.lint()
        entry = next(l for l in self.read(self.ledger).splitlines() if l.startswith("3. "))
        # d31: form T2 keeps the count and the latest whole; each source stays in its
        # Answered line
        self.assertEqual(entry, "3. **One interpreter.** %s (2026-09-03; amended 3 times, "
                                "2026-09-10 to 2026-09-28; amended 2026-09-28, the owner's "
                                "answer to decision 11, the sitting)" % OLD3)
        for source in sources:
            self.assertIn("(2026-09-28; %s)\n" % source, self.read(self.questions))
        self.new("Pin it a fourth time")
        before = (sha(self.ledger), sha(self.questions))
        code, _, err = self.answer("12", "--pick", "Pin", "--source", "an unbalanced )",
                                   "--text", OLD3, "--amends", "3")
        self.assertEqual(code, 2, err)
        self.assertIn("fails the lint", err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)

    def test_area_drops_the_and_hashes_and_refuses_a_newline(self):
        # d-n3 fix round: `--area` drops a leading "The" and leading `#`s, refuses a
        # newline, and reaches `Every session` only by its whole name.
        before = (sha(self.ledger), sha(self.questions))
        code, out, err = self.answer("9", "--pick", "Pin", "--source", "s", "--text",
                                     "Pin 3.12.", "--area", "Re\nlease")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("newline", err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        code, out, err = self.answer("9", "--pick", "Pin", "--source", "s", "--text",
                                     "Pin 3.12.", "--area", "The Release")
        self.assertEqual(code, 0, err)
        self.assertIn("entry 9 under `### Release`", out)
        self.new("Name the gate")
        code, out, err = self.answer("10", "--pick", "Pin", "--source", "s", "--text",
                                     "The gate is make.", "--area", "### Build")
        self.assertEqual(code, 0, err)
        self.assertIn("entry 10 under `### Build`", out)
        self.new("A third question")
        code, out, err = self.answer("11", "--pick", "Pin", "--source", "s", "--text",
                                     "A third.", "--area", "e")
        self.assertEqual(code, 0, err)
        self.assertIn("entry 11 under `### e`", out)
        ledger = self.read(self.ledger)
        self.assertEqual((ledger.count("### Release\n"), ledger.count("### Build\n")), (1, 1))
        self.assertNotIn("### ###", ledger)
        self.lint()

    def test_an_answer_over_the_cap_lowers_the_count(self):
        # rf1 item 8 (history/sessions INTAKE answer-over-the-cap): a merge can leave more
        # questions open than the cap; an answer lowers the count and is not refused for it.
        with mock.patch("decisions.ask.OPEN_CAP", 10):
            for title in ("Q two", "Q three", "Q four", "Q five", "Q six"):
                self.new(title)
        self.assertEqual(self.read(self.questions).count("\n**Your answer:**"), 7)
        code, out, err = self.answer("9", "--pick", "Pin", "--source", "s", "--text",
                                     "Pin 3.12.", "--area", "Build")
        self.assertEqual(code, 0, err)
        self.assertIn("answer: 9, Pin; entry 9 under `### Build`", out)
        self.assertEqual(self.read(self.questions).count("\n**Your answer:**"), 6)
        code, _, err = self.answer("10", "--pick", "Pin", "--source", "s", "--no-entry")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(self.questions).count("\n**Your answer:**"), 5)
        self.lint()

    # d28 (hq audit row d1, S1): `answer` reads the owner's typed text T, the rest of the
    # **Your answer:** line and every non-blank line under it, before any write.
    LINE = "Stay in hq, and never move the S1 rows out of the audit file"

    def typed(self, number, on_line, under=""):
        """Question `number`'s **Your answer:** line with `on_line` after it and `under`
        after that line."""
        text = self.read(self.questions)
        mark = text.index("**Your answer:**", text.index("## %d. " % number)) + 16
        end = text.find("\n", mark)
        end = len(text) if end < 0 else end
        self.write(self.questions, text[:mark] + on_line + under + text[end:])

    def refused(self, argv, words):
        before = (sha(self.ledger), sha(self.questions))
        code, out, err = self.answer("9", *argv)
        self.assertEqual((code, out), (2, ""), err)
        self.assertIn(words, err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        return err

    def test_typed_empty_picks(self):
        for n, (on_line, under) in enumerate((("   ", ""), ("", "\n\n   \n"))):
            with self.subTest(on_line=on_line, under=under):
                number = 9 + n
                if n:
                    self.new("Pin it again")
                self.typed(number, on_line, under)
                code, out, err = self.answer(str(number), "--pick", "Pin", "--source", "s",
                                             "--no-entry")
                self.assertEqual(code, 0, err)
                self.assertIn("answer: %d, Pin; no entry" % number, out)
                self.assertIn(": Pin (2026-09-28; s)\n", self.read(self.questions))
        self.lint()

    def test_typed_label_picks(self):
        for n, on_line in enumerate((" **pin (Recommended).**", " `Pin`.", " PIN. (Recommended)")):
            with self.subTest(on_line=on_line):
                if n:
                    self.new("Pin it %d" % n)
                self.typed(9 + n, on_line)
                code, out, err = self.answer(str(9 + n), "--pick", "Pin", "--source", "s",
                                             "--no-entry")
                self.assertEqual(code, 0, err)
                self.assertIn("answer: %d, Pin; no entry" % (9 + n), out)
        self.lint()

    def test_typed_other_label_refuses_pick(self):
        self.typed(9, " `Follow`")
        self.refused(["--pick", "Pin", "--source", "s", "--no-entry"],
                     "answer: question 9's **Your answer:** line names the option `Follow`; "
                     "pass --pick with it; nothing written")
        code, out, err = self.answer("9", "--pick", "follow", "--source", "s", "--no-entry")
        self.assertEqual(code, 0, err)
        self.assertIn("answer: 9, Follow; no entry", out)

    def test_typed_condition_refuses_pick(self):
        self.typed(9, " Pin, once 3.13 ships")
        for mode in (["--area", "Build", "--text", "Pin 3.12."],
                     ["--amends", "3", "--text", ONLY_312], ["--no-entry"]):
            with self.subTest(mode=mode):
                err = self.refused(["--pick", "Pin", "--source", "s"] + mode,
                                   "answer: question 9's **Your answer:** line says more than a "
                                   "label; pass --other, which keeps the line; nothing written:\n"
                                   "Pin, once 3.13 ships\n")
                self.assertNotIn("Traceback", err)
        self.refused(["--pick", "Wait", "--source", "s", "--no-entry"], "has no option 'Wait'")

    def test_typed_label_refuses_other(self):
        self.typed(9, " **pin (Recommended).**")
        for mode in (["--area", "Build", "--text", "Pin 3.12."], ["--no-entry"]):
            with self.subTest(mode=mode):
                self.refused(["--other", "Pin it", "--source", "s"] + mode,
                             "answer: question 9's **Your answer:** line names the option `Pin`; "
                             "pass --pick with it; nothing written")

    def test_typed_line_kept_under_other(self):
        self.typed(9, " " + self.LINE)
        code, out, err = self.answer("9", "--other", "Stay in hq", "--source", "s", "--text",
                                     "The NICE stays in hq.", "--area", "Build")
        self.assertEqual(code, 0, err)
        label = "Other: Stay in hq; the owner's line: " + self.LINE
        self.assertIn("answer: 9, %s; entry 9 under `### Build`" % label, out)
        self.assertIn("- 9. Pin the interpreter: %s (2026-09-28; s)\n" % label,
                      self.read(self.questions))
        self.assertNotIn("never move the S1 rows", self.read(self.ledger))
        self.assertIn("9. **Pin the interpreter.** The NICE stays in hq. (2026-09-28;",
                      self.read(self.ledger))
        self.new("Name the gate")
        self.typed(10, " " + self.LINE)
        code, out, err = self.answer("10", "--other", self.LINE.upper(), "--source", "s",
                                     "--no-entry")
        self.assertEqual(code, 0, err)
        self.assertIn("- 10. Name the gate: Other: %s (2026-09-28; s)\n" % self.LINE.upper(),
                      self.read(self.questions))
        self.assertNotIn("never move the S1 rows", self.read(self.ledger))
        self.lint()

    def test_typed_under_the_line_is_the_answer(self):
        self.typed(9, "", "\n\nPin, once\n3.13 ships.\n")
        block = [b for b in decisions.questions.parse(self.read(self.questions)).blocks
                 if b.number == 9][0]
        self.assertEqual(block.answer, "Pin, once 3.13 ships.")
        self.refused(["--pick", "Pin", "--source", "s", "--no-entry"],
                     "says more than a label; pass --other, which keeps the line; nothing "
                     "written:\nPin, once 3.13 ships.\n")
        code, out, err = self.answer("9", "--other", "Pin until 3.13 ships", "--source", "s",
                                     "--amends", "3", "--text", ONLY_312, "--shorter")
        self.assertEqual(code, 0, err)
        self.assertIn("- 9. Pin the interpreter: Other: Pin until 3.13 ships; the owner's line: "
                      "Pin, once 3.13 ships. (2026-09-28; s)\n", self.read(self.questions))
        self.assertNotIn("3.13 ships", self.read(self.ledger))
        self.lint()

    # The d28 review r1: F1, a label opening or ending in a backtick or `*` is named by the
    # owner's line holding it as it stands; F2, two labels one normal form apart never send
    # the pick to the wrong option.
    DEFAULT = "- **Pin (Recommended).** Keeps one interpreter.\n- **Follow.** Tracks releases.\n"

    def labelled(self, title, *lines):
        """A new question `title` whose option lines are `lines`; its number."""
        self.new(title)
        text = self.read(self.questions)
        number = max(b.number for b in decisions.questions.parse(text).blocks)
        at = text.index(self.DEFAULT, text.index("## %d. " % number))
        self.write(self.questions, text[:at] + "".join(line + "\n" for line in lines)
                   + text[at + len(self.DEFAULT):])
        return number

    def refuses(self, number, argv, words):
        before = (sha(self.ledger), sha(self.questions))
        code, out, err = self.answer(str(number), *argv)
        self.assertEqual((code, out), (2, ""), err)
        self.assertIn(words, err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)

    def test_typed_edge_label_picks(self):
        """Review r1 F1 (p3.sh E1 to E5): the owner's line that is a label with a backtick
        or `*` at its edge, as it stands, takes `--pick` of that label."""
        make = ("- **Keep `make check` (Recommended).** The gate stays whole.",
                "- **Run `make fast`.** A part of it.")
        cases = ((make, "Run `make fast`", "Run `make fast`"),
                 (make, "**Run `make fast`.**", "Run `make fast`"),
                 (make, "Keep `make check` (Recommended)", "Keep `make check`"),
                 (("- **`uv` everywhere (Recommended).** One tool.",
                   "- **`pip` stays.** As now."), "`pip` stays", "`pip` stays"),
                 (("- **Lint `*.md` only (Recommended).** Fast.",
                   "- **Lint every file matching *.** Slow."),
                  "Lint every file matching *", "Lint every file matching *"))
        start = (self.read(self.ledger), self.read(self.questions))
        for n, (lines, on_line, label) in enumerate(cases):
            with self.subTest(on_line=on_line):
                self.write(self.ledger, start[0])
                self.write(self.questions, start[1])
                number = self.labelled("Gate it %d" % n, *lines)
                self.typed(number, " " + on_line)
                code, out, err = self.answer(str(number), "--pick", label, "--source", "s",
                                             "--no-entry")
                self.assertEqual(code, 0, err)
                self.assertIn("answer: %d, %s; no entry" % (number, label), out)
        self.lint()

    def test_typed_twin_labels_never_pick_astray(self):
        """Review r1 F2 (p4.sh F1, F3): two lint-green labels one normal form apart. The
        owner's line that is one of them as it stands takes `--pick` of it alone; a line
        that names both refuses every `--pick` and `--other`, both files byte-identical."""
        pin = "- **Pin (Recommended).** Keeps one interpreter."
        pairs = (((pin, "- **Stay in hq.** One file.", "- **Stay in hq..** Forever."),
                  ("Stay in hq", "Stay in hq."), "Stay in hq", "**Stay in hq.**"),
                 ((pin, "- **main.** The branch.", "- **`main`.** The word."),
                  ("main", "`main`"), "`main`", "**main.**"))
        for n, (lines, twins, exact, both) in enumerate(pairs):
            with self.subTest(exact=exact):
                number = self.labelled("Twin it %d" % n, *lines)
                twin = [t for t in twins if t != exact][0]
                self.typed(number, " " + both)
                for argv in (["--pick", exact], ["--pick", twin], ["--other", exact]):
                    self.refuses(number, argv + ["--source", "s", "--no-entry"],
                                 "answer: question %d's **Your answer:** line could name any of "
                                 "`%s`, `%s`; ask the owner to type one label as it stands; "
                                 "nothing written" % ((number,) + twins))
                self.typed(number, " " + exact)
                self.refuses(number, ["--pick", twin, "--source", "s", "--no-entry"],
                             "line names the option `%s`; pass --pick with it" % exact)
                code, out, err = self.answer(str(number), "--pick", exact, "--source", "s",
                                             "--no-entry")
                self.assertEqual(code, 0, err)
                self.assertIn("answer: %d, %s; no entry" % (number, exact), out)
        self.lint()

    # d30 (the reply's b1, b2, b4; d28's review F3): what `answer` keeps.
    SECOND = "It imports nothing else."
    NEW1 = "A release is cut from the pinned interpreter and no other one."

    def two(self):
        """Entry 1 with a second sentence, and a CLAUDE.md holding the rendered block."""
        self.write(self.ledger, self.read(self.ledger).replace(
            "plain present-tense English.", "plain present-tense English. " + self.SECOND))
        self.claude = os.path.join(self.tmp, "CLAUDE.md")
        self.write(self.claude, "# Sample\n\n<!-- BEGIN GENERATED: decisions -->\n"
                                "<!-- END GENERATED: decisions -->\n")
        self.assertEqual(decisions.main(["render", "--ledger", self.ledger], out=io.StringIO(),
                                        err=io.StringIO()), 0)
        return "Every entry reads as plain present-tense English."

    def test_kept_amends_refuses_a_dropped_sentence(self):
        first = self.two()
        before = (sha(self.ledger), sha(self.questions), sha(self.claude))
        for text, lost in ((self.NEW1, [first, self.SECOND]),
                           ("%s %s" % (first, self.NEW1), [self.SECOND])):
            code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--amends", "1",
                                         "--text", text)
            self.assertEqual((code, out), (2, ""), err)
            self.assertIn("drops %d of its 2 sentences" % len(lost), err)
            self.assertTrue(err.rstrip().endswith("nothing written:\n" + "\n".join(lost)), err)
            for part in ("--add", "--shorter"):
                self.assertIn(part, err)
            self.assertEqual((sha(self.ledger), sha(self.questions), sha(self.claude)), before)
        whole = "%s  %s\n%s" % (self.SECOND, self.NEW1, first)
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--amends", "1",
                                     "--text", whole, "--every-turn")
        self.assertEqual(code, 0, err)
        self.assertIn("replaced: %s %s\n" % (first, self.SECOND), out)
        for path in (self.ledger, self.claude):
            self.assertEqual(self.read(path).count(self.SECOND), 1, path)
        self.lint()

    def test_kept_add_appends(self):
        first = self.two()
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--amends", "1",
                                     "--add", " %s " % self.NEW1, "--every-turn")
        self.assertEqual(code, 0, err)
        self.assertNotIn("replaced:", out)
        line = ("1. **Plain words.** %s %s %s (2026-09-01; amended 2026-09-28, the owner's "
                "answer to decision 9, s)\n" % (first, self.SECOND, self.NEW1))  # d31: T2
        self.assertIn(line, self.read(self.ledger))
        # d29 act 4: the block cuts the tail to its first date and a count
        self.assertIn(line.split(" (2026-09-01;")[0] + " (2026-09-01; amended once, see the "
                      "ledger)\n", self.read(self.claude))
        self.lint()

    def test_tails_after_amends(self):
        """d29 act 4: the block cuts the amended tail to its first date and a count."""
        first = self.two()
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--amends", "1",
                                     "--add", self.NEW1, "--every-turn")
        self.assertEqual(code, 0, err)
        self.assertIn("1. **Plain words.** %s %s %s (2026-09-01; amended once, see the ledger)\n"
                      % (first, self.SECOND, self.NEW1), self.read(self.claude))
        self.assertIn("(2026-09-01; amended 2026-09-28, the owner's answer to decision 9, "
                      "s)\n", self.read(self.ledger))  # d31: the ledger's tail in form T2
        self.assertEqual(decisions.main(["render", "--check", "--ledger", self.ledger],
                                        out=io.StringIO(), err=io.StringIO()), 0)

    def test_kept_add_refusals(self):
        self.two()
        before = (sha(self.ledger), sha(self.questions), sha(self.claude))
        for argv in (["--amends", "1", "--add", self.NEW1, "--text", self.NEW1],
                     ["--amends", "1", "--add", self.NEW1, "--shorter"],
                     ["--amends", "1", "--add", "  "],
                     ["--area", "Build", "--add", self.NEW1],
                     ["--no-entry", "--add", self.NEW1]):
            code, out, err = self.answer("9", "--pick", "pin", "--source", "s", *argv)
            self.assertEqual((code, out), (2, ""), err)
            self.assertIn("--add takes the place of --text under --amends", err)
            self.assertEqual((sha(self.ledger), sha(self.questions), sha(self.claude)), before)
        for add, words in (("**A title.** " + self.NEW1, "--add opens with a bold title"),
                           (self.NEW1 + " (2026-09-28; s)", "--add ends in a (date; source)")):
            code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--amends", "1",
                                         "--add", add)
            self.assertEqual((code, out), (2, ""), err)
            self.assertIn(words, err)
            self.assertEqual((sha(self.ledger), sha(self.questions), sha(self.claude)), before)

    def test_kept_text_with_an_unclosed_dated_bracket_refuses(self):
        before = (sha(self.ledger), sha(self.questions))
        cut = OLD3 + " (2026-09-03; the sample " + self.NEW1
        for argv in (["--amends", "3", "--text", cut], ["--amends", "3", "--add", cut],
                     ["--area", "Build", "--text", cut]):
            code, out, err = self.answer("9", "--pick", "pin", "--source", "s", *argv)
            self.assertEqual((code, out), (2, ""), err)
            self.assertIn("%s holds a `(` that opens with a date and never closes" % argv[2], err)
            self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        closed = OLD3 + " It held 3.11 (2026-09-03; the sample) before. :)"
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--amends", "3",
                                     "--text", closed)
        self.assertEqual(code, 0, err)
        self.lint()

    def test_kept_cap_refusal_comes_first_and_names_the_ways_out(self):
        more = "".join("\n%d. **Rule %d.** The thing does %d. (2026-09-09; the sample)\n"
                       % (n, n, n) for n in range(20, 39))
        self.write(self.ledger, self.read(self.ledger).replace("\n## Proposed", more[1:] +
                                                               "\n## Proposed"))
        self.lint()
        before = (sha(self.ledger), sha(self.questions))
        for text in ([], ["--text", "Pin 3.12."]):
            code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--area", "Build",
                                         *text)
            self.assertEqual((code, out), (2, ""), err)
            for part in ("25 entries are in force, the cap", "`## Superseded`", "--amends M",
                         "--no-entry", "nothing written"):
                self.assertIn(part, err)
            for part in ("--text is required", "fails the lint"):
                self.assertNotIn(part, err)
            self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--amends", "3",
                                     "--add", self.NEW1)
        self.assertEqual(code, 0, err)
        self.lint()

    STRAYS = (("leading space", "**Your answer:**", " **Your answer:** %s"),
              ("inside the bold", "**Your answer:**", "**Your answer: %s**"),
              ("colon outside the bold", "**Your answer:**", "**Your answer**: %s"),
              ("a paragraph above the line", "**Your answer:**", "%s\n\n**Your answer:**"),
              ("a line under an option", "- **Follow.** Tracks releases.\n",
               "- **Follow.** Tracks releases.\n  %s\n"))

    def stray(self, old, new):
        text = self.read(self.questions)
        at = text.index(old, text.index("## 9. "))
        self.write(self.questions, text[:at] + new % self.LINE + text[at + len(old):])

    def test_kept_stray_line_refuses_pick(self):
        pristine = self.read(self.questions)
        for name, old, new in self.STRAYS:
            for lands in (["--no-entry"], ["--area", "Build", "--text", "Pin 3.12."],
                          ["--amends", "3", "--add", self.NEW1]):
                with self.subTest(name=name, lands=lands[0]):
                    self.write(self.questions, pristine)
                    self.stray(old, new)
                    err = self.refused(["--pick", "Pin", "--source", "s"] + lands,
                                       "holds text no part of its block takes; pass --other")
                    self.assertIn(self.LINE, err.split("nothing written:\n")[1])

    def test_kept_stray_line_stays_under_other(self):
        self.stray("**Your answer:**", "%s\n\n**Your answer:** and keep the audit file")
        code, out, err = self.answer("9", "--other", "Stay, with two conditions", "--source", "s",
                                     "--no-entry")
        self.assertEqual(code, 0, err)
        self.assertIn("- 9. Pin the interpreter: Other: Stay, with two conditions; the owner's "
                      "line: %s and keep the audit file (2026-09-28; s)\n" % self.LINE,
                      self.read(self.questions))
        self.assertNotIn("never move", self.read(self.ledger))
        self.lint()

    def test_kept_report_line_is_a_part(self):
        self.new("Pin it again")
        text = self.read(self.questions)
        at = text.index("**Your answer:**", text.index("## 10. "))
        self.write(self.questions, text[:at] + "**Report.** design/pin.md\nsection 2\n\n"
                   + text[at:])
        block = [b for b in decisions.questions.parse(self.read(self.questions)).blocks
                 if b.number == 10][0]
        self.assertEqual(block.stray, ())
        code, out, err = self.answer("10", "--pick", "Pin", "--source", "s", "--no-entry")
        self.assertEqual(code, 0, err)


class T2Answer(Base):
    """d31: `--amends` writes the tail in form T2 and prints the tail it cut."""

    def setUp(self):
        super().setUp()
        shutil.copy(SAMPLE_QUESTIONS, self.questions)

    def ask(self, title):
        argv = list(PARTS)
        argv[argv.index("--title") + 1] = title
        code, _, err = self.run_cli(*argv)
        self.assertEqual(code, 0, err)
        return re.findall(r"^## (\d+)\. %s$" % title, self.read(self.questions), re.M)[0]

    def amend(self, title, entry, sentence):
        out, err = io.StringIO(), io.StringIO()
        number = self.ask(title)
        code = decisions.main(["answer", number, "--pick", "PIN (Recommended)", "--source",
                               "the sitting", "--amends", entry, "--add", sentence,
                               "--every-turn", "--ledger", self.ledger], out=out, err=err)
        self.assertEqual(code, 0, err.getvalue())
        return number, out.getvalue()

    def test_t2_amends_writes_the_form(self):
        was = ("(2026-09-04; the sample; amended 2026-09-10, answer 3 (see design/04 "
               "(2026-09-09)); amended 2026-09-12, the owner's word)")
        self.write(self.ledger, self.read(self.ledger).replace("(2026-09-04; the sample)", was))
        n, out = self.amend("Pin the interpreter", "4", "A red test stops the landing.")
        self.assertIn("4. **Tests first.** Every verb has its own tests. A red test stops the "
                      "landing. (2026-09-04; amended 2 times, 2026-09-10 to 2026-09-12; amended "
                      "2026-09-28, the owner's answer to decision %s, the sitting)\n" % n,
                      self.read(self.ledger))
        self.assertIn("tail was: %s\n" % was, out)
        # again, on a tail in the form: the count grows and the range's end moves
        n, out = self.amend("Pin the linter", "4", "It names the test.")
        self.assertIn("It names the test. (2026-09-04; amended 3 times, 2026-09-10 to "
                      "2026-09-28; amended 2026-09-28, the owner's answer to decision %s, the "
                      "sitting)\n" % n, self.read(self.ledger))
        # an entry never amended: its first date, then the amendment whole
        n, out = self.amend("Pin the formatter", "2", "The lint counts them.")
        self.assertIn("The lint counts them. (2026-09-02; amended 2026-09-28, the owner's "
                      "answer to decision %s, the sitting)\n" % n, self.read(self.ledger))
        self.assertIn("tail was: (2026-09-02; the sample)\n", out)
        self.assertEqual(decisions.main(["render", "--lint", "--ledger", self.ledger],
                                        out=io.StringIO(), err=io.StringIO()), 0)


# d32: the generated block is loaded on every turn, so its growth is shown and, under
# `Every session`, refused without `--every-turn`.
LOADED = "the block is loaded on every turn"
GROWTH = re.compile(r": (\d+) B to (\d+) B, ([+-]\d+) B; " + LOADED)
OLD1 = "Every entry reads as plain present-tense English."
LONG = ("Each entry is one paragraph, written for a human who acts on it without opening the "
        "source.")
WIDE = LONG.replace("paragraph,", "paragraph, \u00a7 2 \u2014")


def held(text):
    """The bytes of the block between the markers in `text`, markers included; 0 without."""
    lines = text.splitlines(keepends=True)
    marks = [i for i, line in enumerate(lines) if line.strip() in (BEGIN, END)]
    return len("".join(lines[marks[0]:marks[1] + 1]).encode()) if len(marks) == 2 else 0


def raw(path):
    with open(path, "rb") as handle:
        return handle.read()


def on_disk(path):
    """The bytes of the block in the file at `path` as they are on disk, line ends kept."""
    lines = raw(path).splitlines(keepends=True)
    marks = [i for i, line in enumerate(lines) if line.strip() in (BEGIN.encode(),
                                                                    END.encode())]
    return len(b"".join(lines[marks[0]:marks[1] + 1])) if len(marks) == 2 else 0


class TurnAnswer(Base):

    def setUp(self):
        super().setUp()
        shutil.copy(SAMPLE_QUESTIONS, self.questions)
        self.claude = os.path.join(self.tmp, "CLAUDE.md")
        self.write(self.claude, "# Notes\n")
        self.render()
        self.new("Pin the interpreter")

    def new(self, title):
        argv = list(PARTS)
        argv[argv.index("--title") + 1] = title
        code, _, err = self.run_cli(*argv)
        self.assertEqual(code, 0, err)

    def render(self):
        self.assertEqual(decisions.main(["render", "--ledger", self.ledger], out=io.StringIO(),
                                        err=io.StringIO()), 0)

    def answer(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["answer"] + list(argv) + ["--ledger", self.ledger],
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def files(self):
        return [raw(p) for p in (self.ledger, self.questions, self.claude)]

    def refused(self, *argv):
        before = self.files()
        code, out, err = self.answer(*argv)
        self.assertEqual((code, out), (2, ""), err)
        self.assertRegex(err, r"adds \d+ B to the block, \d+ B to \d+ B, which is loaded on "
                              r"every turn")
        for part in ("outside `Every session`", "by title only", "--every-turn",
                     "nothing written"):
            self.assertIn(part, err)
        self.assertEqual(self.files(), before)
        return int(re.search(r"adds (\d+) B", err).group(1)), err

    def grew(self, out, before):
        """The growth line `answer` printed, held to the CLAUDE.md block before and after."""
        found = GROWTH.search(out)
        self.assertIsNotNone(found, out)
        after = held(self.read(self.claude))
        self.assertIn("answer: rewrote the block in", out)
        self.assertEqual([int(g) for g in found.groups()], [before, after, after - before])
        return after - before

    def test_every_turn_amends_refuses_growth(self):
        size = held(self.read(self.claude))
        added, err = self.refused("9", "--pick", "pin", "--source", "s", "--amends", "1",
                                  "--add", WIDE)
        # sizes are bytes: WIDE's `§` and em dash take 2 and 3 bytes each
        self.assertIn(", %d B to %d B, which" % (size, size + added), err)
        self.assertIn("; 30 B of it is the entry's tail note; nothing written", err)
        self.refused("9", "--pick", "pin", "--source", "s", "--amends", "1",
                     "--text", OLD1 + " " + WIDE)
        # the tail note is paid every turn too: a same-length reword of an entry never
        # amended grows the block by the note alone, and is refused
        same = OLD1.replace("plain", "clear")
        self.assertEqual(len(same), len(OLD1))
        added_same, err = self.refused("9", "--pick", "pin", "--source", "s", "--amends", "1",
                                       "--text", same, "--shorter")
        self.assertEqual(added_same, 30)
        self.assertIn("30 B of it is the entry's tail note", err)
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--amends", "1",
                                     "--add", WIDE, "--every-turn")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.grew(out, size), added)

    def test_every_turn_area_refuses_growth(self):
        for area in ("Every session", "every session"):
            with self.subTest(area=area):
                _, err = self.refused("9", "--pick", "pin", "--source", "s", "--text",
                                      "Pin it.", "--area", area)
                self.assertNotIn("tail note", err)
        os.remove(self.claude)  # the relay copies the same block: measured from the ledger
        self.files = lambda: [raw(p) for p in (self.ledger, self.questions)]
        self.refused("9", "--pick", "pin", "--source", "s", "--text", "Pin it.",
                     "--area", "Every session")
        self.write(self.claude, "# Notes\n")
        self.render()
        size = held(self.read(self.claude))
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text", "Pin it.",
                                     "--area", "Build")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.grew(out, size), len("- 9 Pin the interpreter (Build)\n"))

    def test_every_turn_heading_matched_in_any_case(self):
        # a ledger whose heading is `### every session`, lower case, is still Every session
        self.write(self.ledger, self.read(self.ledger).replace("### Every session",
                                                               "### every session"))
        self.render()
        self.refused("9", "--pick", "pin", "--source", "s", "--text", "Pin it.",
                     "--area", "Every session")
        self.refused("9", "--pick", "pin", "--source", "s", "--amends", "1", "--add", LONG)

    def test_every_turn_crlf_sizes_are_the_bytes_on_disk(self):
        with open(self.claude, "wb") as handle:
            handle.write(b"# Notes\r\n")
        out, err = io.StringIO(), io.StringIO()
        self.assertEqual(decisions.main(["render", "--ledger", self.ledger], out=out, err=err),
                         0, err.getvalue())
        size = on_disk(self.claude)
        self.assertIn(b"\r\n" + BEGIN.encode(), raw(self.claude))
        self.assertIn(": 0 B to %d B, +%d B;" % (size, size), out.getvalue())
        out = io.StringIO()
        self.assertEqual(decisions.main(["render", "--lint", "--ledger", self.ledger], out=out,
                                        err=io.StringIO()), 0)
        self.assertIn(" is %d B; it is loaded" % size, out.getvalue())
        added, err = self.refused("9", "--pick", "pin", "--source", "s", "--amends", "1",
                                  "--add", WIDE)
        self.assertIn(", %d B to %d B, which" % (size, size + added), err)
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--amends", "1",
                                     "--add", WIDE, "--every-turn")
        self.assertEqual(code, 0, err)
        after = on_disk(self.claude)
        self.assertEqual(after - size, added)
        self.assertIn(": %d B to %d B, +%d B;" % (size, after, after - size), out)

    def test_every_turn_lint_refuses_before_the_check(self):
        # a result that fails the lint is refused on the lint, never told to pass --every-turn
        text = self.read(self.ledger)
        start = text.index("### Every session")
        self.write(self.ledger, text[:start] + text[text.index("### ", start + 4):])
        self.render()
        before = self.files()
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text", "Pin it.",
                                     "--area", "Every session")
        self.assertEqual((code, out), (2, ""), err)
        self.assertIn("the result fails the lint; nothing written", err)
        self.assertNotIn("--every-turn", err)
        self.assertEqual(self.files(), before)

    def test_every_turn_same_or_smaller_passes(self):
        code, _, err = self.answer("9", "--pick", "pin", "--source", "s", "--amends", "1",
                                   "--add", LONG, "--every-turn")
        self.assertEqual(code, 0, err)
        size = held(self.read(self.claude))
        self.new("Trim it")
        code, out, err = self.answer("10", "--pick", "pin", "--source", "s", "--amends", "1",
                                     "--text", OLD1, "--shorter")
        self.assertEqual(code, 0, err)
        self.assertLess(self.grew(out, size), 0)
        size = held(self.read(self.claude))
        same = OLD1.replace("plain", "clear")
        self.assertEqual(len(same), len(OLD1))
        self.new("Reword it")
        code, out, err = self.answer("11", "--pick", "pin", "--source", "s", "--amends", "1",
                                     "--text", same, "--shorter")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.grew(out, size), 0)

    def test_every_turn_flag_needs_an_entry(self):
        before = self.files()
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--no-entry",
                                     "--every-turn")
        self.assertEqual((code, out), (2, ""), err)
        self.assertIn("--every-turn is valid only with --area or --amends", err)
        self.assertEqual(self.files(), before)
