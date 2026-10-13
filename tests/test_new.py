"""`new` (A4): the four-part question and its Proposed line, with the shared
next number; a fresh questions file, an existing one, the insert point, and
an empty part that writes nothing."""

import hashlib
import io
import os
import shutil
import tempfile
from unittest import mock

import decisions
from decisions import ask
from decisions.ledger import LEGACY
from tests.hermetic import SAMPLE, Hermetic

# The question the sample's Proposed entry 8 names, so a lint after `new` pairs them.
SAMPLE_QUESTIONS = os.path.join(os.path.dirname(SAMPLE), "OPEN-QUESTIONS.md")

OPTIONS = ["--option", "Pin: Keeps one interpreter.", "--option", "Follow: Tracks releases."]
PARTS = (["--title", "Pin the interpreter", "--stands", "The tool runs  under\n3.12.",
          "--choice", "Pin 3.12, or follow the newest?"] + OPTIONS
         + ["--recommend", "Pin 3.12. Revisit when 3.13 ships."])
PROPOSED = ("9. **Pin the interpreter.** Pin 3.12. (proposed 2026-09-28; OPEN-QUESTIONS.md)")
QUESTION = ("## 9. Pin the interpreter\n\n"
            "**Where things stand.** The tool runs under 3.12.\n\n"
            "**The choice.** Pin 3.12, or follow the newest?\n\n"
            "**What each answer sets in motion.**\n\n"
            "- **Pin (Recommended).** Keeps one interpreter.\n"
            "- **Follow.** Tracks releases.\n\n"
            "**Recommendation.** Pin 3.12. Revisit when 3.13 ships.\n\n"
            "**Your answer:**\n")


def with_options(*options):
    """PARTS with its two options replaced by `options`, each one `--option`."""
    argv = [a for a in PARTS if a not in OPTIONS]
    at = argv.index("--recommend")
    return argv[:at] + [x for o in options for x in ("--option", o)] + argv[at:]


def sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


class Base(Hermetic):

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.ledger = os.path.join(self.tmp, "DECISIONS.md")
        self.questions = os.path.join(self.tmp, "OPEN-QUESTIONS.md")
        shutil.copy(SAMPLE, self.ledger)
        patcher = mock.patch.object(ask, "today", lambda: "2026-09-28")
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["new"] + list(argv) + ["--ledger", self.ledger], out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def read(self, path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def write(self, path, text):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)


class New(Base):

    def test_a_fresh_questions_file(self):
        code, out, err = self.run_cli(*PARTS)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(self.questions), "# Decisions for the owner\n\n" + QUESTION
                         + "\n## Decided without asking\n")
        self.assertIn("new: 9", out)

    def test_the_proposed_line_goes_last_under_proposed(self):
        shutil.copy(SAMPLE_QUESTIONS, self.questions)
        self.run_cli(*PARTS)
        lines = self.read(self.ledger).splitlines()
        at = lines.index(PROPOSED)
        self.assertTrue(lines[at - 2].startswith("8. **A second interpreter.**"))
        self.assertEqual(lines[at + 2], "## Superseded")
        self.assertEqual(decisions.main(["render", "--lint", "--ledger", self.ledger],
                                        out=io.StringIO(), err=io.StringIO()), 0)

    def test_an_existing_file_takes_it_before_decided_without_asking(self):
        self.write(self.questions, "# Decisions for the owner\n\nOne is open.\n\n"
                                   "## 11. An earlier question\n\n**Your answer:**\n\n"
                                   "## Decided without asking\n\n- A choice made.\n")
        self.assertEqual(self.run_cli(*PARTS)[0], 0)
        text = self.read(self.questions)
        self.assertIn("## 12. Pin the interpreter", text)
        self.assertLess(text.index("## 11."), text.index("## 12."))
        self.assertLess(text.index("## 12."), text.index("## Decided without asking"))
        self.assertTrue(text.endswith("## Decided without asking\n\n- A choice made.\n"))
        self.assertIn("\n12. **Pin the interpreter.** Pin 3.12. (proposed 2026-09-28; "
                      "OPEN-QUESTIONS.md)\n", self.read(self.ledger))

    def test_without_decided_without_asking_it_goes_at_the_end(self):
        self.write(self.questions, "# Questions\n\nNone open.\n")
        self.assertEqual(self.run_cli(*PARTS)[0], 0)
        self.assertEqual(self.read(self.questions), "# Questions\n\nNone open.\n\n" + QUESTION)

    def test_an_entry_under_an_unknown_section_keeps_its_number(self):
        # d-n3 fix round B1: `new` never reuses the number of an entry under `## Notes`.
        text = self.read(self.ledger).replace(
            "## Proposed", "## Notes\n\n9. **Nine.** Under notes. (2026-09-09; t)\n\n"
                           "## Proposed", 1)
        self.write(self.ledger, text)
        code, out, err = self.run_cli(*PARTS)
        self.assertEqual(code, 0, err)
        self.assertIn("new: 10", out)

    def test_a_decided_heading_with_trailing_text(self):
        # d-n3 item 3 (F10): `## Decided without asking` is matched by prefix.
        self.write(self.questions, "# Decisions for the owner\n\n"
                                   "## Decided without asking (since 2026-09)\n\n"
                                   "- A choice made.\n")
        self.assertEqual(self.run_cli(*PARTS)[0], 0)
        text = self.read(self.questions)
        self.assertLess(text.index("## 9."), text.index("## Decided without asking"))
        self.assertTrue(text.endswith("(since 2026-09)\n\n- A choice made.\n"), text)

    def test_the_report_paragraph(self):
        self.assertEqual(self.run_cli(*PARTS + ["--report", "history/r.md section 2"])[0], 0)
        self.assertIn("**Recommendation.** Pin 3.12. Revisit when 3.13 ships.\n\n"
                      "**Report.** history/r.md section 2\n\n**Your answer:**\n",
                      self.read(self.questions))

    def test_proposed_is_made_before_superseded(self):
        text = self.read(self.ledger)
        start, end = text.index("## Proposed"), text.index("## Superseded")
        self.write(self.ledger, text[:start] + text[end:])
        self.assertEqual(self.run_cli(*PARTS)[0], 0)
        text = self.read(self.ledger)
        self.assertIn("## Proposed\n\n%s\n\n## Superseded" % PROPOSED.replace("9.", "8.", 1),
                      text)

    def test_proposed_is_made_at_the_end_without_superseded(self):
        text = self.read(self.ledger)
        self.write(self.ledger, text[:text.index("## Proposed")])
        self.assertEqual(self.run_cli(*PARTS)[0], 0)
        self.assertTrue(self.read(self.ledger).endswith(
            "\n\n## Proposed\n\n%s\n" % PROPOSED.replace("9.", "8.", 1)))

    def test_new_writes_above_the_marker(self):
        """d18 L4: the Proposed line goes above the legacy marker, the text below unchanged."""
        legacy = LEGACY + "\n\n## Proposed\n\n5. An old proposal.\n\n## Superseded\n\n- Gone.\n"
        text = self.read(self.ledger)
        self.write(self.ledger, text + "\n" + legacy)
        shutil.copy(SAMPLE_QUESTIONS, self.questions)
        self.assertEqual(self.run_cli(*PARTS)[0], 0)
        got = self.read(self.ledger)
        self.assertTrue(got.endswith("\n" + legacy))
        self.assertLess(got.index(PROPOSED), got.index(LEGACY))
        lint = io.StringIO()
        self.assertEqual(decisions.main(["render", "--lint", "--ledger", self.ledger], out=lint,
                                        err=io.StringIO()), 0, lint.getvalue())
        head = text[:text.index("## Proposed")].rstrip("\n")
        self.write(self.ledger, head + "\n\n" + legacy)
        os.remove(self.questions)
        self.assertEqual(self.run_cli(*PARTS)[0], 0)
        self.assertEqual(self.read(self.ledger), head + "\n\n## Proposed\n\n%s\n\n%s"
                         % (PROPOSED.replace("9.", "8.", 1), legacy))
        self.assertEqual(decisions.main(["render", "--lint", "--ledger", self.ledger], out=lint,
                                        err=io.StringIO()), 0, lint.getvalue())

    def test_an_empty_part_exits_2_and_writes_nothing(self):
        before = sha(self.ledger)
        for flag in ("--title", "--stands", "--choice", "--recommend"):
            argv = list(PARTS)
            argv[argv.index(flag) + 1] = "  "
            with self.subTest(flag=flag):
                code, out, err = self.run_cli(*argv)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("empty part: %s" % flag, err)
                self.assertEqual(sha(self.ledger), before)
                self.assertFalse(os.path.exists(self.questions))
        self.assertEqual(self.run_cli(*PARTS + ["--report", ""])[0], 2)
        self.assertEqual(sha(self.ledger), before)

    def test_a_missing_part_is_usage(self):
        self.assertEqual(self.run_cli(*PARTS[:-2])[0], 2)
        self.assertEqual(sha(self.ledger), sha(SAMPLE))

    def test_the_next_number_is_shared(self):
        ledger = decisions.parse("## In force\n\n### A\n\n3. **T.** B. (2026-09-01)\n")
        self.assertEqual(ask.next_number(ledger, ""), 4)
        self.assertEqual(ask.next_number(ledger, "## 7. Q\n\n## Decided without asking\n"), 8)

    def test_the_next_number_counts_legacy_entries(self):
        """d-n2 item 2 (1b F7): an `N.` line below the legacy marker holds its number, so a
        new question takes the next one after it."""
        self.write(self.ledger, self.read(self.ledger) + "\n" + LEGACY
                   + "\n\n## In force\n\n12. **An old rule.** Kept. (2026-01-01)\n")
        code, out, err = self.run_cli(*PARTS)
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("new: 13, `## 13. "), out)


class Options(Base):
    """d18 act 1: two to four `--option "Label: effect"`, the first recommended; each
    refusal exits 2 and writes nothing."""

    def refused(self, argv, words):
        before = sha(self.ledger)
        code, out, err = self.run_cli(*argv)
        self.assertEqual((code, out), (2, ""), err)
        self.assertIn(words, err)
        self.assertIn("nothing written", err)
        self.assertEqual(sha(self.ledger), before)
        self.assertFalse(os.path.exists(self.questions))

    def test_two_to_four_options(self):
        pool = ["A: a.", "B: b.", "C: c.", "D: d.", "E: e."]
        for count in (1, 5):
            with self.subTest(count=count):
                self.refused(with_options(*pool[:count]), "2 to 4 options")
        for count in (2, 4):
            with self.subTest(count=count):
                shutil.copy(SAMPLE, self.ledger)
                if os.path.exists(self.questions):
                    os.unlink(self.questions)
                code, _, err = self.run_cli(*with_options(*pool[:count]))
                self.assertEqual(code, 0, err)
                text = self.read(self.questions)
                self.assertEqual(text.count("\n- **"), count)

    def test_first_option_recommended(self):
        self.assertEqual(self.run_cli(*PARTS)[0], 0)
        text = self.read(self.questions)
        self.assertIn(QUESTION, text)
        self.assertEqual(text.count("(Recommended)"), 1)
        shutil.copy(SAMPLE, self.ledger)
        os.unlink(self.questions)
        self.refused(with_options("Pin (Recommended): keeps one.", "Follow: tracks."),
                     "(Recommended)")

    def test_choice_ends_in_question_mark(self):
        argv = list(PARTS)
        argv[argv.index("--choice") + 1] = "Pin 3.12, or follow the newest."
        self.refused(argv, "end in `?`")

    def test_long_label_refused(self):
        self.refused(with_options("B: b.", "One two three four five six: effect."),
                     "five words")
        self.refused(with_options(": effect.", "B: b."), "empty label")
        for bare in ("A", "A: ", "A:  "):
            with self.subTest(option=bare):
                self.refused(with_options(bare, "B: b."), "empty effect")
        code, _, err = self.run_cli(*with_options("B: b.", "One two three four five: effect."))
        self.assertEqual(code, 0, err)

    def test_a_five_word_first_label_refused(self):
        """d-n2 item 7 (L47): the first label takes ` (Recommended)`, so it holds at most
        four words; the others keep five."""
        self.refused(with_options("One two three four five: effect.", "B: b."), "four words")
        code, _, err = self.run_cli(*with_options("One two three four: effect.",
                                                  "B two three four five: b."))
        self.assertEqual(code, 0, err)

    def test_an_other_label_refused(self):
        """d-n2 item 7 (1b F13): AskUserQuestion adds "Other" itself, so no option takes
        that label, in any case."""
        for options in (("Pin: keeps one.", "Other: anything else."),
                        ("Pin: keeps one.", "OTHER.: anything else."),
                        ("other: first.", "Pin: keeps one.")):
            with self.subTest(options=options):
                self.refused(with_options(*options), '"Other"')

    def test_an_other_label_in_punctuation_or_emphasis_refused(self):
        """d-n2 fix round N2: punctuation or emphasis around "Other" does not let it pass;
        a label that only holds the word does."""
        for label in ("Other!", "Other?", "Other\u2026", "**Other**", "_other_", "(Other)"):
            with self.subTest(label=label):
                self.refused(with_options("Pin: keeps one.", label + ": anything else."),
                             '"Other"')
        code, _, err = self.run_cli(*with_options("Pin: keeps one.", "Other tools: drift."))
        self.assertEqual(code, 0, err)

    def test_labels_equal_but_for_case_refused(self):
        """Round 1 F2: `answer --pick` ignores case, so two such labels would record the
        first when the owner picked the second."""
        for pair in (("Keep: runs as is.", "keep: drops the cache."),
                     ("Keep: runs as is.", "B: b.", "KEEP.: drops it.")):
            with self.subTest(options=pair):
                self.refused(with_options(*pair), "the same label as another option")

    def test_sixth_question_refused(self):
        blocks = "".join("## %d. Question %d\n\n**Your answer:**\n\n" % (n, n)
                         for n in range(11, 16))
        self.write(self.questions, "# Decisions for the owner\n\n" + blocks
                   + "## Decided without asking\n")
        before = (sha(self.ledger), sha(self.questions))
        code, out, err = self.run_cli(*PARTS)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("five questions are open", err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)

    def test_answers_flag_removed(self):
        code, out, err = self.run_cli(*PARTS + ["--answers", "Pinning keeps one."])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("unrecognized arguments: --answers", err)
        self.assertEqual(sha(self.ledger), sha(SAMPLE))
        self.assertFalse(os.path.exists(self.questions))
        help_out = io.StringIO()
        decisions.main(["new", "--help"], out=help_out, err=io.StringIO())
        self.assertNotIn("--answers", help_out.getvalue())
        self.assertIn("--option", help_out.getvalue())


class Titles(Base):
    """F1: every title `new` writes lints clean; a title the lint cannot take is refused."""

    def with_title(self, title):
        argv = list(PARTS)
        argv[argv.index("--title") + 1] = title
        return self.run_cli(*argv)

    def test_a_title_holding_a_star_lints_clean(self):
        for title in ("Glob *.md files", "Globs like `*.md` are fine", "*Lead* star"):
            with self.subTest(title=title):
                shutil.copy(SAMPLE, self.ledger)
                shutil.copy(SAMPLE_QUESTIONS, self.questions)
                code, _, err = self.with_title(title)
                self.assertEqual(code, 0, err)
                lint = io.StringIO()
                self.assertEqual(decisions.main(["render", "--lint", "--ledger", self.ledger],
                                                out=lint, err=io.StringIO()), 0, lint.getvalue())

    def test_a_title_the_lint_cannot_take_is_refused_before_any_write(self):
        before = sha(self.ledger)
        for title in ("Use **bold** titles", ".", "Ends in **"):
            with self.subTest(title=title):
                code, out, err = self.with_title(title)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("the ledger's lint", err)
                self.assertEqual(sha(self.ledger), before)
                self.assertFalse(os.path.exists(self.questions))

    def test_a_question_title_takes_no_period(self):
        # d-n3 item 2 (F9, the observer's S4): a title ending in `?` or `!` gets no `.`.
        for title in ("Does the plane get its own network?", "Ship it now!"):
            with self.subTest(title=title):
                shutil.copy(SAMPLE, self.ledger)
                shutil.copy(SAMPLE_QUESTIONS, self.questions)
                code, _, err = self.with_title(title)
                self.assertEqual(code, 0, err)
                self.assertIn("\n9. **%s** Pin 3.12. (proposed 2026-09-28; OPEN-QUESTIONS.md)\n"
                              % title, self.read(self.ledger))
                lint = io.StringIO()
                self.assertEqual(decisions.main(["render", "--lint", "--ledger", self.ledger],
                                                out=lint, err=io.StringIO()), 0, lint.getvalue())

    def test_the_first_sentence_passes_e_g(self):
        # d-n3 item 2 (F9): the first sentence does not cut at e.g., i.e., etc. or vs.
        argv = list(PARTS)
        argv[argv.index("--recommend") + 1] = ("Pin one, e.g. 3.12 (i.e. the current one) vs. "
                                               "the newest, tools etc. as well. Revisit later.")
        code, _, err = self.run_cli(*argv)
        self.assertEqual(code, 0, err)
        self.assertIn("\n9. **Pin the interpreter.** Pin one, e.g. 3.12 (i.e. the current one) "
                      "vs. the newest, tools etc. as well. (proposed 2026-09-28; "
                      "OPEN-QUESTIONS.md)\n", self.read(self.ledger))


class Lock(Base):
    """F2: the read, the number and both writes run under `.new.lock`."""

    def test_a_held_lock_refuses_and_writes_nothing(self):
        import fcntl
        lock = os.path.join(self.tmp, ".new.lock")
        fd = os.open(lock, os.O_CREAT | os.O_RDWR, 0o644)
        self.addCleanup(os.close, fd)
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.write(fd, b"4242\n")
        before = sha(self.ledger)
        with mock.patch.object(ask, "NEW_WAIT", 0.2):
            code, out, err = self.run_cli(*PARTS)
        self.assertEqual((code, out), (2, ""))
        self.assertIn(".new.lock is held by pid 4242", err)
        self.assertEqual(sha(self.ledger), before)
        self.assertFalse(os.path.exists(self.questions))

    def test_the_lock_leaves_with_the_run(self):
        self.assertEqual(self.run_cli(*PARTS)[0], 0)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, ".new.lock")))

    def test_parallel_runs_take_distinct_numbers(self):
        import subprocess
        import sys
        from tests.hermetic import REPO
        runner = os.path.join(REPO, "src", "decisions.py")
        children = [subprocess.Popen(
            [sys.executable, runner, "new", "--title", "Q%d" % i, "--stands", "s",
             "--choice", "c?", "--option", "A: a.", "--option", "B: b.", "--recommend", "Yes.",
             "--ledger", self.ledger],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for i in range(5)]
        for child in children:
            out, err = child.communicate(timeout=60)
            self.assertEqual(child.returncode, 0, err)
        questions = self.read(self.questions)
        ledger = decisions.parse(self.read(self.ledger))
        self.assertEqual(ledger.problems, [])
        proposed = sorted(e.number for e in ledger.entries if e.section == "Proposed")
        self.assertEqual(proposed, list(range(8, 14)))
        for number in range(9, 14):
            self.assertEqual(questions.count("## %d. Q" % number), 1, questions)


class AllOrNothing(Base):
    """F2 and F3: a failed second write leaves both files as they were, and exits 2."""

    def test_a_failed_ledger_write_restores_the_questions(self):
        self.write(self.questions, "# Decisions for the owner\n\n## Decided without asking\n")
        before = (sha(self.ledger), sha(self.questions))
        real = os.replace

        def flaky(src, dst, *args, **kwargs):
            if os.path.realpath(dst) == os.path.realpath(self.ledger):
                raise PermissionError(1, "Operation not permitted")
            return real(src, dst, *args, **kwargs)

        with mock.patch("os.replace", flaky):
            code, out, err = self.run_cli(*PARTS)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("unwritable", err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        self.assertEqual(sorted(os.listdir(self.tmp)), ["DECISIONS.md", "OPEN-QUESTIONS.md"])

    def test_a_failed_first_write_on_a_fresh_file_leaves_none(self):
        before = sha(self.ledger)
        real = os.replace

        def flaky(src, dst, *args, **kwargs):
            if os.path.realpath(dst) == os.path.realpath(self.ledger):
                raise PermissionError(1, "Operation not permitted")
            return real(src, dst, *args, **kwargs)

        with mock.patch("os.replace", flaky):
            self.assertEqual(self.run_cli(*PARTS)[0], 2)
        self.assertEqual(sha(self.ledger), before)
        self.assertEqual(sorted(os.listdir(self.tmp)), ["DECISIONS.md"])
