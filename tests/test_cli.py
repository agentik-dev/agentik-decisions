"""The CLI (A1, d18, d23): exactly show, find, new, ask, answer, render, doctor and backlog; each dropped verb
exits 2 as unknown; the ledger found at the git top, or named by --ledger."""

import io
import os
import shutil
import subprocess
import sys
import tempfile

import decisions
from tests.hermetic import REPO, SAMPLE, Hermetic

VERBS = ("show", "find", "new", "ask", "answer", "render", "doctor", "backlog")
DROPPED = ("scope", "rule", "against", "supersede", "convert", "stats", "init", "check",
           "index")


class Verbs(Hermetic):

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        return decisions.main(list(argv), out=out, err=err), out.getvalue(), err.getvalue()

    def test_help_lists_the_eight_verbs(self):
        code, out, _ = self.run_cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("{%s}" % ",".join(VERBS), out)
        self.assertEqual(list(decisions.VERBS), list(VERBS))

    def test_each_dropped_verb_exits_2_as_unknown(self):
        for verb in DROPPED:
            with self.subTest(verb=verb):
                code, out, err = self.run_cli(verb)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("invalid choice: '%s'" % verb, err)

    def test_no_verb_exits_2(self):
        code, _, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("name a verb: %s" % ", ".join(VERBS), err)

    def test_doc_lines_within_100_characters(self):
        # d18 1a obs: the docstring `--help` prints keeps every line within 100 characters
        long = [line for line in decisions.cli.__doc__.splitlines() if len(line) > 100]
        self.assertEqual(long, [])

    def test_find_help_says_area_or_section(self):
        # d-n3 item 5 (F14): `find` prints the area for an entry in force, else the section.
        code, out, _ = self.run_cli("find", "--help")
        self.assertEqual(code, 0)
        self.assertIn("N Title (area or section)", " ".join(out.split()))
        self.assertIn("N Title (area or section)", decisions.cli.__doc__)
        self.assertNotIn("N Title (section)", decisions.cli.__doc__)

    def test_answer_needs_area_amends_or_no_entry(self):
        # d-n3 item 6 (1b F5): the lands group is required, so argparse refuses with exit 2.
        code, out, err = self.run_cli("answer", "9", "--pick", "Pin", "--source", "s",
                                      "--text", "T.", "--ledger", SAMPLE)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("one of the arguments --area --amends --no-entry is required", err)
        usage = " ".join(self.run_cli("answer", "--help")[1].split())
        self.assertIn("(--area A | --amends M | --no-entry)", usage)
        self.assertNotIn("[--area A | --amends M | --no-entry]", usage)

    def test_the_runner_prints_help(self):
        run = subprocess.run([sys.executable, os.path.join(REPO, "src", "decisions.py"), "--help"],
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("{%s}" % ",".join(VERBS), run.stdout)


class Locate(Hermetic):

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.cwd = os.getcwd()
        self.addCleanup(os.chdir, self.cwd)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        return decisions.main(list(argv), out=out, err=err), out.getvalue(), err.getvalue()

    def test_the_ledger_at_the_git_top(self):
        subprocess.run(["git", "init", "-q", self.tmp], check=True, timeout=30)
        shutil.copy(SAMPLE, os.path.join(self.tmp, "DECISIONS.md"))
        os.makedirs(os.path.join(self.tmp, "a", "b"))
        os.chdir(os.path.join(self.tmp, "a", "b"))
        code, out, err = self.run_cli("find", "plain")
        self.assertEqual((code, out), (0, "1 Plain words (Every session)\n"), err)

    def test_a_git_top_without_a_ledger_exits_2(self):
        subprocess.run(["git", "init", "-q", self.tmp], check=True, timeout=30)
        os.chdir(self.tmp)
        code, _, err = self.run_cli("show", "1")
        self.assertEqual(code, 2)
        self.assertIn("no ledger at", err)

    def test_outside_a_work_tree_names_the_flag(self):
        os.chdir(self.tmp)
        code, _, err = self.run_cli("show", "1")
        self.assertEqual(code, 2)
        self.assertIn("name one with --ledger", err)

    def test_the_flag_before_or_after_the_verb(self):
        ledger = os.path.join(self.tmp, "any-name.md")
        shutil.copy(SAMPLE, ledger)
        os.chdir(self.tmp)
        self.assertEqual(self.run_cli("--ledger", ledger, "find", "plain")[0], 0)
        self.assertEqual(self.run_cli("find", "plain", "--ledger", "any-name.md")[1],
                         "1 Plain words (Every session)\n")
        self.assertEqual(self.run_cli("render", "--lint", "--ledger", ledger)[0], 0)
