"""`show` (A2) and `find` (A3) over the sample sectioned ledger."""

import io
import os
import shutil
import tempfile

import decisions
from decisions.ledger import LEGACY
from tests.hermetic import SAMPLE, Hermetic


class Verb(Hermetic):

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.ledger = os.path.join(self.tmp, "DECISIONS.md")
        shutil.copy(SAMPLE, self.ledger)
        with open(self.ledger, encoding="utf-8") as handle:
            self.lines = handle.read().splitlines()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(list(argv) + ["--ledger", self.ledger], out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def line(self, prefix):
        return next(line for line in self.lines if line.startswith(prefix))


class Show(Verb):

    def test_an_unknown_section_resets_the_area(self):
        # d-n3 item 1 (F7): no entry after an unknown `## ` lands under the area before it.
        with open(self.ledger, encoding="utf-8") as handle:
            text = handle.read()
        stray = "9. **Stray.** Under the notes heading. (2026-09-09; t)"
        with open(self.ledger, "w", encoding="utf-8") as handle:
            handle.write(text.replace("## Proposed", "## Notes\n\n%s\n\n## Proposed" % stray, 1))
        code, out, err = self.run_cli("show", "--area", "release")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "## In force\n\n### Release\n\n%s\n" % self.line("7. "))
        self.assertEqual(self.run_cli("find", "notes heading")[1], "9 Stray (Notes)\n")
        self.assertEqual(self.run_cli("show", "9")[1], "## Notes\n\n%s\n" % stray)

    def test_one_entry_verbatim_under_its_heading(self):
        code, out, err = self.run_cli("show", "3")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "## In force\n\n### Build\n\n%s\n" % self.line("3. "))

    def test_a_shared_heading_prints_once(self):
        code, out, _ = self.run_cli("show", "3", "4")
        self.assertEqual(code, 0)
        self.assertEqual(out, "## In force\n\n### Build\n\n%s\n\n%s\n"
                         % (self.line("3. "), self.line("4. ")))

    def test_entries_across_sections_in_the_order_named(self):
        code, out, _ = self.run_cli("show", "8", "1", "6")
        self.assertEqual(code, 0)
        self.assertEqual(out, "## Proposed\n\n%s\n\n## In force\n\n### Every session\n\n%s\n\n"
                              "## Superseded\n\n%s\n"
                         % (self.line("8. "), self.line("1. "), self.line("6. ")))

    def test_area_prints_the_whole_subsection(self):
        code, out, _ = self.run_cli("show", "--area", "every")
        self.assertEqual(code, 0)
        self.assertEqual(out, "## In force\n\n### Every session\n\n%s\n\n%s\n"
                         % (self.line("1. "), self.line("2. ")))

    def test_area_prefers_an_exact_name_then_a_unique_prefix(self):
        self.assertIn(self.line("3. "), self.run_cli("show", "--area", "BUILD")[1])
        self.assertNotIn(self.line("5. "), self.run_cli("show", "--area", "build")[1])
        code, out, _ = self.run_cli("show", "--area", "build t")
        self.assertEqual((code, out), (0, "## In force\n\n### Build tools\n\n%s\n"
                                       % self.line("5. ")))
        self.assertIn(self.line("7. "), self.run_cli("show", "--area", "rel")[1])

    def test_an_ambiguous_area_names_its_candidates(self):
        code, out, err = self.run_cli("show", "--area", "bui")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("ambiguous: Build, Build tools", err)

    def test_an_unknown_area_exits_2(self):
        code, out, err = self.run_cli("show", "--area", "nowhere")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("the areas are: Every session, Build, Build tools, Release", err)

    def test_an_unknown_number_exits_2_and_prints_nothing(self):
        code, out, err = self.run_cli("show", "3", "99")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("no entry 99", err)

    def test_numbers_or_area_one_of_them(self):
        self.assertEqual(self.run_cli("show")[0], 2)
        self.assertEqual(self.run_cli("show", "3", "--area", "build")[0], 2)
        self.assertEqual(self.run_cli("show", "three")[0], 2)

    def test_show_reads_a_ledger_the_lint_refuses(self):
        with open(self.ledger, "a", encoding="utf-8") as handle:
            handle.write("\n## Notes\n")
        code, out, _ = self.run_cli("show", "4")
        self.assertEqual(code, 0)
        self.assertIn(self.line("4. "), out)


class Find(Verb):

    def test_a_title_match_case_insensitive(self):
        code, out, _ = self.run_cli("find", "PLAIN")
        self.assertEqual((code, out), (0, "1 Plain words (Every session)\n"))

    def test_a_body_match(self):
        code, out, _ = self.run_cli("find", "standard library")
        self.assertEqual((code, out), (0, "3 One interpreter (Build)\n"))

    def test_every_section_is_searched(self):
        code, out, _ = self.run_cli("find", "interpreter")
        self.assertEqual(out, "3 One interpreter (Build)\n8 A second interpreter (Proposed)\n")
        out = self.run_cli("find", "replaced")[1].splitlines()
        self.assertEqual(out[0], "- Entries as separate files: replaced by one ledger "
                                 "(entry 2), 2026-09-02. (Superseded)")
        self.assertTrue(out[1].startswith("6 The old gate named by hand"))

    def test_no_match_prints_nothing_and_exits_0(self):
        self.assertEqual(self.run_cli("find", "zebra")[:2], (0, ""))

    def test_an_empty_word_exits_2(self):
        self.assertEqual(self.run_cli("find", " ")[0], 2)


class Legacy(Verb):
    """d18 L4: below the marker, `find` and `show --area` read an older ledger's text."""

    OLD = ("## Old rulings\n\nThe interpreter was 3.9 once.\n\n- Old lines wrap\n"
           "  onto a second line about the interpreter.\n\n### Relay days\n\n"
           "1. the relay ran nightly.\n")

    def setUp(self):
        super().setUp()
        with open(self.ledger, "a", encoding="utf-8") as handle:
            handle.write("\n" + LEGACY + "\n\n" + self.OLD)

    def test_find_and_show_read_legacy(self):
        n = len(self.lines)
        code, out, _ = self.run_cli("find", "interpreter")
        self.assertEqual((code, out), (0, "3 One interpreter (Build)\n8 A second interpreter "
                                          "(Proposed)\nL%d Old rulings (legacy)\n"
                                          "L%d Old rulings (legacy)\n" % (n + 6, n + 8)))
        self.assertEqual(self.run_cli("find", "RELAY")[:2],
                         (0, "L%d Relay days (legacy)\nL%d Relay days (legacy)\n"
                             % (n + 11, n + 13)))
        self.assertEqual(self.run_cli("show", "--area", "relay")[:2],
                         (0, "### Relay days\n\n1. the relay ran nightly.\n"))
        self.assertEqual(self.run_cli("show", "--area", "old rulings")[:2], (0, self.OLD))
        self.assertIn(self.line("3. "), self.run_cli("show", "--area", "build")[1])
        self.assertEqual(self.run_cli("show", "1")[1].splitlines()[-1], self.line("1. "))
        self.assertEqual(self.run_cli("render", "--lint")[:2], (0, ""))


class TheArea(Verb):
    """`--area relay` reaches `### The relay`: a leading "The " drops before the prefix match."""

    def setUp(self):
        super().setUp()
        with open(self.ledger, "w", encoding="utf-8") as handle:
            handle.write("## In force\n\n### The ledger\n\n1. **L.** One. (2026-09-01)\n\n"
                         "### The relay\n\n2. **R.** Two. (2026-09-02)\n\n"
                         "### Tools and plugins\n\n3. **T.** Three. (2026-09-03)\n")

    def test_relay_reaches_the_relay(self):
        code, out, err = self.run_cli("show", "--area", "relay")
        self.assertEqual((code, out), (0, "## In force\n\n### The relay\n\n"
                                          "2. **R.** Two. (2026-09-02)\n"), err)

    def test_the_full_heading_and_other_prefixes_still_match(self):
        self.assertIn("2. **R.**", self.run_cli("show", "--area", "The rel")[1])
        self.assertIn("1. **L.**", self.run_cli("show", "--area", "led")[1])
        self.assertIn("3. **T.**", self.run_cli("show", "--area", "tools")[1])

    def test_an_ambiguous_prefix_names_every_candidate(self):
        code, out, err = self.run_cli("show", "--area", "t")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("ambiguous: The ledger, The relay, Tools and plugins", err)
