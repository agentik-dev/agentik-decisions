"""`answer` (d18 act 2): the owner's answer to question N becomes entry N, an
amendment or no entry; the question and its Proposed line leave, an Answered
line stays, and both files are written or neither."""

import io
import os
import shutil
from unittest import mock

import decisions
from decisions.ledger import LEGACY
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
        """D19: `--amends` keeps the whole tail and appends its clause, so the clause
        an earlier answer left stays, and the two read in order."""
        code, _, err = self.answer("9", "--pick", "pin", "--source", "s1", "--text",
                                   ONLY_312, "--amends", "3")
        self.assertEqual(code, 0, err)
        self.new("Move on")
        code, _, err = self.answer("10", "--pick", "follow", "--source", "s2", "--text",
                                   WHOLE_313, "--amends", "3")
        self.assertEqual(code, 0, err)
        lines = [l for l in self.read(self.ledger).splitlines() if l.startswith("3. ")]
        self.assertEqual(lines, ["3. **One interpreter.** %s (2026-09-03; the sample" % WHOLE_313 +
                                 ", amended 2026-09-10 (twice); amended 2026-09-28, the owner's "
                                 "answer to decision 9, s1; amended 2026-09-28, the owner's "
                                 "answer to decision 10, s2)"])
        self.assertEqual(self.answer("11", "--pick", "pin", "--source", "s", "--text", "t",
                                     "--amends", "3")[0], 2)
        self.lint()

    def test_amends_keeps_nested_parenthetical_balanced(self):
        """D19, closing round 2a F6: a tail with `(twice); amended` inside a nested
        parenthetical is kept whole, so the entry's parentheses stay balanced."""
        tail = "2026-09-03; the sample (moved (twice); amended in place)"
        self.write(self.ledger, self.read(self.ledger).replace(
            "(2026-09-03; the sample, amended 2026-09-10 (twice))", "(%s)" % tail))
        code, _, err = self.answer("9", "--pick", "pin", "--source", "s1", "--text",
                                   ONLY_312, "--amends", "3")
        self.assertEqual(code, 0, err)
        lines = [l for l in self.read(self.ledger).splitlines() if l.startswith("3. ")]
        self.assertEqual(lines, ["3. **One interpreter.** %s (%s; amended 2026-09-28, the owner's "
                                 "answer to decision 9, s1)" % (ONLY_312, tail)])
        self.assertEqual(lines[0].count("("), lines[0].count(")"))
        self.lint()

    def test_amends_refuses_a_paragraph_cut_by_half(self):
        """D21: a paragraph under half the old one's length is refused, exit 2, and
        both files stay byte-identical; the refusal names both lengths, the old
        paragraph on its own line and `--shorter`. Half exactly passes."""
        before = (sha(self.ledger), sha(self.questions))
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text",
                                     "Runs  under 3.13.", "--amends", "3")
        self.assertEqual((code, out), (2, ""), err)
        for part in ("16", "64", "\n%s\n" % OLD3, "--shorter", "nothing written"):
            self.assertIn(part, err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, ".new.lock")))
        half = "The tool runs under Python 3.13."
        self.assertEqual(len(half) * 2, len(OLD3))
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text", half,
                                     "--amends", "3")
        self.assertEqual(code, 0, err)
        self.assertIn("3. **One interpreter.** %s (2026-09-03;" % half, self.read(self.ledger))
        self.lint()

    def test_amends_shorter_writes_and_prints_replaced(self):
        """D21: `--shorter` lets the cut paragraph through, and the run still prints
        `replaced:` with the old paragraph after its done line."""
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text",
                                     "Runs under 3.13.", "--amends", "3", "--shorter")
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("answer: 9, Pin; entry 3 amended in "), out)
        self.assertEqual(lines[1], "replaced: " + OLD3)
        self.assertIn("3. **One interpreter.** Runs under 3.13. (2026-09-03; the sample, "
                      "amended 2026-09-10 (twice); amended 2026-09-28, the owner's answer to "
                      "decision 9, s)\n", self.read(self.ledger))
        self.lint()

    def test_amends_whole_paragraph_prints_replaced(self):
        """D21: a whole paragraph is written, and the run prints `replaced:` with the
        old body, between the bold title and the tail, as it stood."""
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text",
                                     WHOLE_313, "--amends", "3")
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
                                     "Hold it.", "--area", "Every session")
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
                                         "Pin it.", "--area", "Every session")
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
                                   "--area", "Every session")
        self.assertEqual(code, 0, err)
        self.assertIn("CLAUDE.md holds no GENERATED markers", err)
        self.assertEqual(self.read(claude), "# Notes\n")
        self.assertEqual(decisions.main(["render", "--ledger", self.ledger], out=io.StringIO(),
                                        err=io.StringIO()), 0)
        other = os.path.join(self.tmp, "elsewhere.md")
        shutil.copy(claude, other)
        self.new("Keep the lock")
        code, out, err = self.answer("10", "--pick", "pin", "--source", "s", "--text",
                                     "Hold the lock.", "--area", "Every session")
        self.assertEqual(code, 0, err)
        self.assertIn("rewrote the block", out)
        self.assertIn("Keep the lock", self.read(claude))
        self.assertNotIn("Keep the lock", self.read(other))
        self.new("Name the gate")
        code, out, err = self.answer("11", "--pick", "pin", "--source", "s", "--text", "Gate.",
                                     "--area", "Every session", "--into", other)
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
                                       "--text", paragraph, "--amends", "3")
            self.assertEqual(code, 0, err)
            self.lint()
        entry = next(l for l in self.read(self.ledger).splitlines() if l.startswith("3. "))
        self.assertTrue(entry.startswith("3. **One interpreter.** %s (2026-09-03; the sample, "
                                         "amended 2026-09-10 (twice); amended 2026-09-28, "
                                         % OLD3), entry)
        for number, source in zip((9, 10, 11), sources):
            self.assertIn("the owner's answer to decision %d, %s" % (number, source), entry)
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
