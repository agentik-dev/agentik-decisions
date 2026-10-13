"""The ledger's parser and its lint (A7): the sample parses clean, and each
departure from the shape is one `file:line: message` problem."""

import io
import os
import shutil
import tempfile
import unittest

import decisions
from decisions.ledger import (EVERY_SESSION_CAP, IN_FORCE, IN_FORCE_CAP, LEGACY, PROPOSED,
                              SUPERSEDED, final_parenthetical, lint, parse)
from tests.hermetic import SAMPLE

HEAD = "# t\n\n## In force\n\n"


def entry(n, title="Title", body="Body.", paren="2026-09-01; t"):
    return "%d. **%s.** %s (%s)\n" % (n, title, body, paren)


def messages(text):
    return [message for _line, message in parse(text).problems]


class Sample(unittest.TestCase):

    def setUp(self):
        with open(SAMPLE, encoding="utf-8") as handle:
            self.ledger = parse(handle.read())

    def test_the_sample_lints_clean(self):
        self.assertEqual(self.ledger.problems, [])

    def test_entries_sections_and_areas(self):
        got = [(e.number, e.section, e.area) for e in self.ledger.entries]
        self.assertEqual(got, [(1, IN_FORCE, "Every session"), (2, IN_FORCE, "Every session"),
                               (3, IN_FORCE, "Build"), (4, IN_FORCE, "Build"),
                               (5, IN_FORCE, "Build tools"), (7, IN_FORCE, "Release"),
                               (8, PROPOSED, None), (None, SUPERSEDED, None),
                               (6, SUPERSEDED, None)])
        self.assertEqual([a.name for a in self.ledger.areas],
                         ["Every session", "Build", "Build tools", "Release"])

    def test_titles_drop_the_final_period(self):
        titles = {e.number: e.title for e in self.ledger.entries}
        self.assertEqual(titles[1], "Plain words")
        self.assertEqual(titles[8], "A second interpreter")
        self.assertTrue(titles[6].startswith("The old gate named by hand"))

    def test_heads_are_verbatim(self):
        first = self.ledger.entries[0]
        self.assertEqual(first.heads, ("## In force", "### Every session"))
        self.assertEqual(self.ledger.entries[6].heads, ("## Proposed",))
        self.assertTrue(first.text.startswith("1. **Plain words.**"))
        self.assertEqual(first.line, 14)


class Lint(unittest.TestCase):
    """A7: one test per case, then the other shapes the lint names."""

    def test_a_duplicate_number(self):
        text = HEAD + "### A\n\n" + entry(1) + "\n## Superseded\n\n1. Old: replaced by one (entry 2), 2026-09-01.\n"
        problems = parse(text).problems
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0], (11, "entry 1 repeats the number of line 7"))

    def test_26_in_force(self):
        text = HEAD + "### A\n\n" + "".join(entry(n) for n in range(1, 27))
        problems = parse(text).problems
        self.assertEqual(problems, [(32, "26 entries in force; the cap is %d" % IN_FORCE_CAP)])
        self.assertEqual(parse(HEAD + "### A\n\n" + "".join(entry(n) for n in range(1, 26))
                               ).problems, [])

    def test_8_in_every_session(self):
        text = HEAD + "### Every session\n\n" + "".join(entry(n) for n in range(1, 9))
        self.assertEqual(messages(text), ["8 entries under `Every session`; the cap is %d"
                                          % EVERY_SESSION_CAP])
        self.assertEqual(messages(HEAD + "### Every session\n\n"
                                  + "".join(entry(n) for n in range(1, 8))), [])

    def test_an_entry_outside_a_subsection(self):
        text = HEAD + entry(1) + "\n### A\n\n" + entry(2)
        self.assertEqual(parse(text).problems, [(5, "entry 1 sits outside a `###` subsection")])

    def test_an_entry_without_its_dated_parenthetical(self):
        for bad in ("1. **Title.** Body without one.\n",
                    "1. **Title.** Body (no date here)\n",
                    "1. **Title.** Body (2026-09-01) and then more.\n"):
            with self.subTest(bad=bad):
                self.assertEqual(messages(HEAD + "### A\n\n" + bad),
                                 ["entry 1: it does not end in a parenthetical holding a date"])

    def test_a_nested_parenthetical_holds_its_date(self):
        text = HEAD + "### A\n\n" + entry(1, paren="2026-09-01; ruling (3) of the day")
        self.assertEqual(parse(text).problems, [])
        self.assertEqual(final_parenthetical("x (a (b) c)"), "a (b) c")
        self.assertIsNone(final_parenthetical("x (a) c"))

    def test_the_title_ends_in_a_period_inside_the_bold(self):
        for bad in ("1. **Title** Body. (2026-09-01)\n", "1. Title. Body. (2026-09-01)\n",
                    "1. **Title.**\n"):
            with self.subTest(bad=bad):
                self.assertEqual(len(messages(HEAD + "### A\n\n" + bad)), 1)
                self.assertIn("the shape is", messages(HEAD + "### A\n\n" + bad)[0])

    def test_a_title_may_hold_a_single_star(self):
        """F1: a backticked glob in a title; a doubled star still ends the bold."""
        for title in ("Globs like `*.md` are fine", "Glob *.md files", "*Lead* star"):
            with self.subTest(title=title):
                text = HEAD + "### A\n\n" + entry(1, title=title, paren="2026-01-01; src")
                self.assertEqual(parse(text).problems, [])
                self.assertEqual(parse(text).entries[0].title, title)
        self.assertEqual(len(messages(HEAD + "### A\n\n" + entry(1, title="Use **bold** titles"))),
                         1)
        text = HEAD + "### A\n\n1. **Title** Body. More.** tail (2026-09-01)\n"
        self.assertIn("the shape is", messages(text)[0])

    def test_a_title_or_tail_twice(self):
        """D22: an entry whose body repeats its bold title or its dated tail, as an
        `answer --text` given a whole line once wrote, is named once per part; a
        dated parenthetical inside the body, or a later `**`, is no repeat."""
        title, tail = ("entry %d: its bold title appears twice",
                       "entry %d: its (date; source) tail appears twice")
        cases = (("**Title.** Body. (2026-09-01; t)", [title, tail]),
                 ("1. **Title.** Body.", [title]),
                 ("**Other** body.", [title]),
                 ("Body. (2026-09-01 ~16:15, t)", [tail]),
                 ("Body (2026-09-01; t; amended 2026-09-02, u)", [tail]),
                 ("Body (since 2026-09-01; t).", []),
                 ("Body with `**` inside.", []),
                 ("Body (2026-09-01)", []),
                 ("Body (no date)", []))
        for body, want in cases:
            with self.subTest(body=body):
                self.assertCountEqual(messages(HEAD + "### A\n\n" + entry(1, body=body)),
                                      [m % 1 for m in want])
        proposed = ("## Proposed\n\n2. **P.** **P.** One. (proposed 2026-09-02; "
                    "OPEN-QUESTIONS.md)\n")
        self.assertEqual(messages(HEAD + "### A\n\n" + entry(1) + "\n" + proposed), [title % 2])
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        path = os.path.join(tmp, "DECISIONS.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(HEAD + "### A\n\n" + entry(1, body="1. **Title.** Body. (2026-09-01; t)"))
        out = io.StringIO()
        self.assertEqual(decisions.main(["render", "--lint", "--ledger", path], out=out,
                                        err=io.StringIO()), 1)
        self.assertEqual(out.getvalue().count(" appears twice\n"), 2, out.getvalue())

    def test_a_proposed_line_names_its_date(self):
        good = "## Proposed\n\n2. **P.** One sentence. (proposed 2026-09-02; OPEN-QUESTIONS.md)\n"
        self.assertEqual(messages(HEAD + "### A\n\n" + entry(1) + "\n" + good), [])
        bad = "## Proposed\n\n2. **P.** One sentence. (2026-09-02)\n"
        self.assertEqual(messages(HEAD + "### A\n\n" + entry(1) + "\n" + bad),
                         ["entry 2: a Proposed line ends in `(proposed YYYY-MM-DD; ...)`"])

    def test_every_session_comes_first(self):
        text = HEAD + "### A\n\n" + entry(1) + "\n### Every session\n\n" + entry(2)
        self.assertEqual(messages(text), ["`### Every session` comes first under `## In force`"])

    def test_the_sections_and_their_order(self):
        self.assertEqual(messages("# t\n\n## Proposed\n\n## In force\n\n### A\n\n" + entry(1)),
                         ["`## In force` comes before `## Proposed`"])
        self.assertEqual(messages(HEAD + "### A\n\n" + entry(1) + "\n## Notes\n"),
                         ["unknown section `## Notes`; the sections are In force, Proposed "
                          "and Superseded"])
        self.assertEqual(messages("# t\n\nNo sections.\n"), ["no `## In force` section"])
        self.assertEqual(messages(HEAD + "### A\n\n" + entry(1) + "\n## In force\n"),
                         ["a second `## In force`"])

    def test_a_subsection_outside_in_force(self):
        text = HEAD + "### A\n\n" + entry(1) + "\n## Superseded\n\n### Old\n"
        self.assertEqual(messages(text), ["a level-3 heading outside `## In force`"])

    def test_a_wrapped_entry_is_a_line_that_is_not_an_entry(self):
        text = HEAD + "### A\n\n1. **Title.** Body that wraps\nonto a second line. (2026-09-01)\n"
        self.assertIn("a line in `## In force` that is not an entry", messages(text))

    def test_a_superseded_line_is_a_list_item(self):
        text = HEAD + "### A\n\n" + entry(1) + "\n## Superseded\n\nA bare line.\n"
        self.assertEqual(messages(text), ["a line in `## Superseded` that is not an entry"])

    def test_front_matter_and_prose_precede_the_sections(self):
        text = "---\nstatus: current\n---\n# t\n\nProse, with 3. a number.\n\n## In force\n\n" \
               "### A\n\n" + entry(1)
        self.assertEqual(parse(text).problems, [])
        self.assertEqual(parse(text).entries[0].line, 12)


L1 = "entry 1: its tail names a source after the date: `(YYYY-MM-DD; source)`"
FATE = ("a Superseded line holds a date and names its fate: `replaced by`, `merged into` "
        "or `lapsed with`")
QHEAD = "# Decisions for the owner (t)\n\n"
BLOCK = ("## {n}. Q{n}\n\n**Where things stand.** S.\n\n**The choice.** A or B?\n\n"
         "**What each answer sets in motion.**\n\n- **A (Recommended).** a.\n- **B.** b.\n\n"
         "**Recommendation.** A.\n\n**Your answer:**\n\n")


class Shape(unittest.TestCase):
    """d18 L1, L2 and L4: the tail names a source, a Superseded line its fate, and the
    legacy marker ends the parsed part."""

    def test_l1_tail_names_a_source(self):
        for good in ("2026-09-01; t", "2026-09-24, run 13", "2026-09-25 ~16:15; the owner",
                     "2026-09-01; a; amended 2026-09-28, b"):
            with self.subTest(good=good):
                self.assertEqual(messages(HEAD + "### A\n\n" + entry(1, paren=good)), [])
        for bad in ("2026-09-01", "2026-09-01;", "2026-09-01 the owner"):
            with self.subTest(bad=bad):
                self.assertEqual(messages(HEAD + "### A\n\n" + entry(1, paren=bad)), [L1])

    def test_l2_superseded_date_and_fate(self):
        base = HEAD + "### A\n\n" + entry(1) + "\n## Superseded\n\n"
        for good in ("- Old: replaced by one (entry 1), 2026-09-01.",
                     "- Old: merged into entry 1, 2026-09-01.",
                     "- Old: lapsed with the gate, 2026-09-01.",
                     "2. Old: replaced by one (entry 1), 2026-09-01."):
            with self.subTest(good=good):
                self.assertEqual(messages(base + good + "\n"), [])
        for bad, who in (("- Old: gone, 2026-09-01.", "a line"),
                         ("- Old: replaced by one.", "a line"),
                         ("2. Old: merged into one.", "entry 2")):
            with self.subTest(bad=bad):
                self.assertEqual(messages(base + bad + "\n"), ["%s: %s" % (who, FATE)])

    def test_legacy_marker_stops_parsing(self):
        below = ("## Old rulings\n\n### Build\n\n" + "".join(entry(n) for n in range(1, 27))
                 + "\nA stray line.\n\n## In force\n\n#### Deep\n")
        text = HEAD + "### A\n\n" + entry(1) + "\n" + LEGACY + "\n\n" + below
        ledger = parse(text)
        self.assertEqual(ledger.problems, [])
        self.assertEqual([(e.number, e.line) for e in ledger.entries], [(1, 7)])
        self.assertEqual([a.name for a in ledger.areas], ["A"])
        self.assertEqual(ledger.legacy, (9, text.splitlines()[9:]))
        self.assertNotEqual(parse(text.replace(LEGACY, "")).problems, [])
        adopted = parse("# t\n\n## In force\n\n" + LEGACY + "\n\n" + below)
        self.assertEqual((adopted.problems, adopted.entries), ([], []))
        self.assertIsNone(parse(HEAD + "### A\n\n" + entry(1)).legacy)

    def test_l1_body_only_a_tail_and_proposed_without_open_questions(self):
        # d-n3 item 4 (F11): an entry in force needs a body; a Proposed line names the file.
        only = HEAD + "### A\n\n1. **Title.** (2026-09-01; t)\n"
        self.assertEqual(messages(only), ["entry 1: its body is only its parenthetical; the "
                                          "paragraph sits between the title and the tail"])
        base = HEAD + "### A\n\n" + entry(1) + "\n## Proposed\n\n"
        self.assertEqual(messages(base + "2. **Q.** A. (proposed 2026-09-28; OPEN-QUESTIONS.md)"
                                         "\n"), [])
        self.assertEqual(messages(base + "2. **Q.** A. (proposed 2026-09-28; the sitting)\n"),
                         ["entry 2: a Proposed line names `OPEN-QUESTIONS.md` in its tail"])

    def test_l1_amended_is_not_a_source(self):
        # d-n3 item 9: `amended DATE` after the date names no source.
        for bad in ("2026-09-28; amended 2026-09-29", "2026-09-28, Amended 2026-09-29"):
            with self.subTest(bad=bad):
                self.assertEqual(messages(HEAD + "### A\n\n" + entry(1, paren=bad)), [L1])

    def test_l1_the_date_opens_the_tail(self):
        # d-n3 item 11 (2a F7): the date opens the tail; `(; amended DATE, ...)` is refused.
        for bad in ("see x; 2026-09-01; t", "; amended 2026-09-30, the owner"):
            with self.subTest(bad=bad):
                self.assertEqual(messages(HEAD + "### A\n\n" + entry(1, paren=bad)), [L1])
        for good in (" 2026-09-01; t", "2026-09-22 and 2026-09-23; t"):
            with self.subTest(good=good):
                self.assertEqual(messages(HEAD + "### A\n\n" + entry(1, paren=good)), [])

    def test_l1_amended_ignores_case_and_a_later_source(self):
        # d-n3 fix round L1: `AMENDED DATE` names no source; a source after it does.
        self.assertEqual(messages(HEAD + "### A\n\n" + entry(1, paren="2026-09-28; AMENDED "
                                                                     "2026-09-29")), [L1])
        good = "2026-09-28; amended 2026-09-29; the owner's word"
        self.assertEqual(messages(HEAD + "### A\n\n" + entry(1, paren=good)), [])

    def test_l2_superseded_by_is_a_fate(self):
        # d-n3 fix round L2: item 12 names `Superseded by` as a fate phrase.
        base = HEAD + "### A\n\n" + entry(1) + "\n## Superseded\n\n"
        self.assertEqual(messages(base + "- Old: Superseded by entry 1, 2026-09-01.\n"), [])

    def test_an_unknown_section_keeps_its_entries_for_the_numbers(self):
        # d-n3 fix round B1: an entry under an unknown `## ` keeps its number, with no
        # section and no area, so the lint sees a number it repeats.
        text = (HEAD + "### A\n\n" + entry(1) + "\n## Notes\n\n" + entry(2)
                + "\n## Superseded\n\n2. Old: replaced by one (entry 1), 2026-09-01.\n")
        ledger = parse(text)
        self.assertEqual([(e.number, e.section, e.area) for e in ledger.entries],
                         [(1, IN_FORCE, "A"), (2, None, None), (2, SUPERSEDED, None)])
        self.assertIn("entry 2 repeats the number of line 11", messages(text))

    def test_l2_fate_ignores_case(self):
        # d-n3 item 12: the fate phrases match ignoring case.
        base = HEAD + "### A\n\n" + entry(1) + "\n## Superseded\n\n"
        for good in ("- Old: Replaced by one (entry 1), 2026-09-01.",
                     "- Old: MERGED INTO entry 1, 2026-09-01.",
                     "2. Old: Lapsed with the gate, 2026-09-01."):
            with self.subTest(good=good):
                self.assertEqual(messages(base + good + "\n"), [])


class Questions(unittest.TestCase):
    """d18 L3: the OPEN-QUESTIONS.md beside the ledger, when present."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def lint(self, text, numbers=(9,)):
        path = os.path.join(self.tmp, "DECISIONS.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(HEAD + "### A\n\n" + entry(1) + "\n## Proposed\n\n" + "".join(
                "%d. **Q%d.** A. (proposed 2026-09-28; OPEN-QUESTIONS.md)\n" % (n, n)
                for n in numbers))
        with open(os.path.join(self.tmp, "OPEN-QUESTIONS.md"), "w", encoding="utf-8") as handle:
            handle.write(text)
        return [message for _name, _line, message in lint(path, self.tmp)[1]]

    def test_l3_question_blocks(self):
        good = QHEAD + BLOCK.format(n=9) + BLOCK.format(n=10)
        self.assertEqual(self.lint(good, (9, 10)), [])
        six = QHEAD + "".join(BLOCK.format(n=n) for n in range(9, 15))
        cases = (
            (good.replace("# Decisions for the owner", "# Questions"), (9, 10),
             "the first H1 does not start with"),
            (six, range(9, 15), "6 questions open; the cap is 5"),
            (good.replace("**Where things stand.** S.\n\n**The choice.** A or B?",
                          "**The choice.** A or B?\n\n**Where things stand.** S.", 1), (9, 10),
             "question 9: the four labels in order"),
            (good.replace("- **B.** b.\n", "", 1), (9, 10), "question 9: 1 options"),
            (good.replace("- **B.** b.", "- **B (Recommended).** b.", 1), (9, 10),
             "question 9: the first option alone is marked (Recommended)"),
            (good.replace("**Your answer:**\n", "", 1), (9, 10),
             "question 9: no `**Your answer:**` line"),
            (good, (9,), "question 10 has no Proposed line in DECISIONS.md"),
            (good, (9, 10, 11), "entry 11: a Proposed line with no question in OPEN-QUESTIONS.md"))
        for text, numbers, want in cases:
            with self.subTest(want=want):
                got = self.lint(text, numbers)
                self.assertTrue(any(m.startswith(want) for m in got), got)

    def test_l3_answered_and_decided_lines(self):
        tail = ("## Decided without asking\n\nA paragraph first.\n\n- A bullet.\n- Another.\n\n"
                "## Answered\n\nA paragraph.\n\n- 7. Q7: A (2026-09-28; the sitting)\n"
                "- 6. Q6: B (2026-09-25 ~07:58, the owner)\n")
        self.assertEqual(self.lint(QHEAD + BLOCK.format(n=9) + tail), [])
        decided = tail.replace("- Another.", "1. A numbered line.")
        self.assertEqual(self.lint(QHEAD + BLOCK.format(n=9) + decided),
                         ["a line under `Decided without asking` that is not a `- ` bullet"])
        for bad in ("- 7. Q7: A\n", "- 7. Q7: A (2026-09-28)\n"):
            with self.subTest(bad=bad):
                answered = tail.replace("- 7. Q7: A (2026-09-28; the sitting)\n", bad)
                self.assertEqual(self.lint(QHEAD + BLOCK.format(n=9) + answered),
                                 ["a line under `Answered` ends in `(YYYY-MM-DD; source)`"])
        self.assertEqual(self.lint(QHEAD + tail, ()), [])

    def test_l3_skips_front_matter(self):
        # d-n3 item 8 (1b F11): a `# ` comment in the front matter is not the first H1.
        front = "---\n# a comment\nstatus: current\n---\n"
        self.assertEqual(self.lint(front + QHEAD + BLOCK.format(n=9)), [])
        got = self.lint(front + "# Questions\n\n" + BLOCK.format(n=9))
        self.assertEqual([m for m in got if "first H1" in m],
                         ["the first H1 does not start with `# Decisions for the owner`"])

    def test_l3_fenced_heading_and_repeated_number(self):
        # d-n3 item 10: a `## ` line in a code fence is text; one number twice is flagged.
        fenced = BLOCK.format(n=9).replace("**Where things stand.** S.\n\n",
                                           "**Where things stand.** S.\n\n```\n## 3. Not a "
                                           "block\n```\n\n", 1)
        self.assertEqual(self.lint(QHEAD + fenced), [])
        self.assertIn("question 9: a second block numbered 9",
                      self.lint(QHEAD + BLOCK.format(n=9) + BLOCK.format(n=9)))

    def test_l3_labels_equal_ignoring_case(self):
        # d-n3 item 10 (2a F5): two option labels equal ignoring case are flagged.
        text = QHEAD + BLOCK.format(n=9).replace("- **B.** b.", "- **a.** b.", 1)
        self.assertEqual(self.lint(text),
                         ["question 9: two options share the label `a`, ignoring case"])

    def test_l3_unclosed_fence_and_front_matter(self):
        # d-n3 fix round: an unclosed fence hides nothing and is flagged; a fence closes
        # on its own character at least as long; unclosed front matter is flagged.
        opened = BLOCK.format(n=9).replace("**Where things stand.** S.\n\n",
                                           "**Where things stand.** S.\n\n```\n\n", 1)
        got = self.lint(QHEAD + opened + "## Answered\n\n- 3. T: A (no date at all)\n")
        self.assertIn("a code fence that is never closed", got)
        self.assertIn("a line under `Answered` ends in `(YYYY-MM-DD; source)`", got)
        longer = BLOCK.format(n=9).replace("**Where things stand.** S.\n\n",
                                           "**Where things stand.** S.\n\n````\n```\n## 3. "
                                           "Not a block\n````\n\n", 1)
        self.assertEqual(self.lint(QHEAD + longer), [])
        self.assertIn("the front matter has no closing `---`",
                      self.lint("---\nstatus: x\n" + QHEAD + BLOCK.format(n=9)))

    def test_one_final_parenthetical(self):
        # d-n3 item 13: one final_parenthetical (ledger.py) and one ANSWERED_LINE (questions.py).
        src = os.path.join(os.path.dirname(decisions.__file__))
        defs = {}
        for name in sorted(os.listdir(src)):
            if name.endswith(".py"):
                with open(os.path.join(src, name), encoding="utf-8") as handle:
                    text = handle.read()
                defs[name] = (text.count("def final_parenthetical("),
                              text.count("ANSWERED_LINE = "))
        self.assertEqual({n: d for n, d in defs.items() if d[0]}, {"ledger.py": (1, 0)})
        self.assertEqual({n: d for n, d in defs.items() if d[1]}, {"questions.py": (0, 1)})


if __name__ == "__main__":
    unittest.main()
