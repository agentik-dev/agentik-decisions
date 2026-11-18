"""rr4: decisions finds a repo's records through commons' resolver (hq design/28 §3 items
12 and 18). Each case builds a temp clone `widget` and a temp holder whose `repos/widget`
holds the records, then reads or writes in the four states: `own` (no key), `out` (the key
resolves), `unset` (the tree declares `records: out`, no key) and `broken` (a key that does
not resolve). Git runs under the hermetic home, so no live config is read."""
import io
import json
import os
import shutil
import subprocess
import tempfile

import decisions
from decisions import ask
from unittest import mock
from tests.hermetic import Hermetic, SAMPLE
from tests.test_expire import HEADER, ago, row
from tests.test_new import PARTS

GIT = shutil.which("git") or "/usr/bin/git"
KEY = "agentik.records"
NICE = ("# Nice to have\n\n## Rows\n\n" + HEADER
        + row("n1", "S4", "`a.py`", "an old S4 on no step", ago(40)))
ROW = ("# Row r1: a made-up row\n\n| item | value |\n|---|---|\n| repo | hq |\n| level | S3 |\n"
       "| from | the hand |\n| base | main |\n| depends_on | none |\n| done |  |\n\n"
       "Prose.\n\n## Owed\n- nothing\n")


def git(cwd, *args):
    return subprocess.run([GIT, "-c", "user.name=f", "-c", "user.email=f", "-C", cwd] + list(args),
                          check=True, capture_output=True, text=True).stdout


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class Records(Hermetic):

    def setUp(self):
        super().setUp()
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="rr4-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = os.path.join(self.tmp, "work", "widget")
        os.makedirs(self.repo)
        git(self.repo, "init", "-q", "-b", "main")
        write(os.path.join(self.repo, "README.md"), "widget\n")
        git(self.repo, "add", "README.md")
        git(self.repo, "commit", "-q", "-m", "start")
        self.hold = os.path.join(self.tmp, "hold")
        self.records = os.path.join(self.hold, "repos", "widget")
        os.makedirs(self.records)
        git(self.hold, "init", "-q", "-b", "main")
        write(os.path.join(self.hold, "README.md"), "hold\n")
        git(self.hold, "add", "README.md")
        git(self.hold, "commit", "-q", "-m", "start")
        patcher = mock.patch.object(ask, "today", lambda: "2026-09-28")
        patcher.start()
        self.addCleanup(patcher.stop)

    def out(self, folder=None):
        git(self.repo, "config", KEY, folder or self.records)

    def unset(self):
        write(os.path.join(self.repo, ".hygiene-allow"), "records: out\n")
        git(self.repo, "add", ".hygiene-allow")
        git(self.repo, "commit", "-q", "-m", "declare")

    def broken(self):
        git(self.repo, "config", KEY, "rel/widget")

    def run_cli(self, *argv, cwd=None):
        here = os.getcwd()
        os.chdir(cwd or self.repo)
        try:
            out, err = io.StringIO(), io.StringIO()
            code = decisions.main(list(argv), out=out, err=err)
        finally:
            os.chdir(here)
        return code, out.getvalue(), err.getvalue()

    def refused_broken(self, *argv):
        code, _, err = self.run_cli(*argv)
        self.assertEqual(code, 2, err)
        self.assertIn(KEY, err)
        self.assertIn("'rel/widget'", err)
        self.assertIn("(relative)", err)
        self.assertEqual(len(err.strip().splitlines()), 1, err)

    def ledger(self):
        path = os.path.join(self.repo, "DECISIONS.md")
        shutil.copy(SAMPLE, path)
        return path


class AskAnswer(Records):

    def test_out_new_ask_answer_use_the_records(self):
        self.out()
        ledger = self.ledger()
        code, _, err = self.run_cli("new", *PARTS)
        self.assertEqual(code, 0, err)
        questions = os.path.join(self.records, "OPEN-QUESTIONS.md")
        self.assertIn("## 9. Pin the interpreter", read(questions))
        self.assertFalse(os.path.exists(os.path.join(self.repo, "OPEN-QUESTIONS.md")))
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".new.lock")))
        self.assertIn("9. **Pin the interpreter.**", read(ledger))
        code, out, err = self.run_cli("ask")
        self.assertEqual(code, 0, err)
        self.assertIn('"header": "Decision 9"', out)
        # the lint pairs entry 9 with the records' question; the sample's own entry 8 has none
        code, out, err = self.run_cli("render", "--lint")
        self.assertIn("entry 8: a Proposed line with no question", out + err)
        self.assertNotIn("entry 9", out + err)
        code, out, err = self.run_cli("answer", "9", "--pick", "Pin", "--source", "s1",
                                      "--text", "Pin 3.12.", "--area", "build")
        self.assertEqual(code, 0, err)
        self.assertNotIn("## 9.", read(questions))
        self.assertIn("**Pin the interpreter.** Pin 3.12.", read(ledger))
        self.assertFalse(os.path.exists(os.path.join(self.repo, "OPEN-QUESTIONS.md")))

    def test_own_new_writes_beside_the_ledger(self):
        self.ledger()
        code, _, err = self.run_cli("new", *PARTS)
        self.assertEqual(code, 0, err)
        self.assertTrue(os.path.isfile(os.path.join(self.repo, "OPEN-QUESTIONS.md")))
        self.assertFalse(os.listdir(self.records))

    def test_unset_new_refuses_naming_the_key(self):
        self.unset()
        ledger = self.ledger()
        before = read(ledger)
        code, _, err = self.run_cli("new", *PARTS)
        self.assertEqual(code, 2, err)
        self.assertIn(KEY, err)
        self.assertIn("not set", err)
        self.assertEqual(read(ledger), before)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "OPEN-QUESTIONS.md")))

    def test_broken_new_ask_answer_refuse(self):
        self.broken()
        self.ledger()
        self.refused_broken("new", *PARTS)
        self.refused_broken("ask")
        self.refused_broken("answer", "9", "--pick", "Pin", "--source", "s1", "--text", "P.",
                            "--area", "build")
        self.assertFalse(os.path.exists(os.path.join(self.repo, "OPEN-QUESTIONS.md")))

    def test_an_explicit_ledger_wins_in_out(self):
        self.out()
        elsewhere = os.path.join(self.tmp, "loose", "DECISIONS.md")
        os.makedirs(os.path.dirname(elsewhere))
        shutil.copy(SAMPLE, elsewhere)
        code, _, err = self.run_cli("new", *(list(PARTS) + ["--ledger", elsewhere]))
        self.assertEqual(code, 0, err)
        self.assertTrue(os.path.isfile(os.path.join(os.path.dirname(elsewhere),
                                                    "OPEN-QUESTIONS.md")))
        self.assertFalse(os.listdir(self.records))


class Questions(Records):

    def setUp(self):
        super().setUp()
        self.ledger()

    def asked(self, folder):
        here = os.path.join(self.tmp, "seed")
        os.makedirs(here)
        shutil.copy(SAMPLE, os.path.join(here, "DECISIONS.md"))
        code, _, err = self.run_cli("new", *(list(PARTS) + ["--ledger", os.path.join(
            here, "DECISIONS.md")]), cwd=here)
        self.assertEqual(code, 0, err)
        shutil.copy(os.path.join(here, "OPEN-QUESTIONS.md"), os.path.join(folder,
                                                                         "OPEN-QUESTIONS.md"))

    def test_out_reads_the_records_file(self):
        self.out()
        self.asked(self.records)
        code, out, err = self.run_cli("questions", "--json")
        self.assertEqual(code, 0, err)
        view = json.loads(out)["repos"][0]
        self.assertEqual(view["file"], os.path.join(self.records, "OPEN-QUESTIONS.md"))
        self.assertEqual([q["n"] for q in view["questions"]], [9])

    def test_unset_finds_none(self):
        self.unset()
        self.asked(self.repo)  # a stray file in the tree is no record of a repo that keeps none
        code, out, err = self.run_cli("questions")
        self.assertEqual(code, 0, err)
        self.assertIn("skipped (no OPEN-QUESTIONS.md): widget", out)

    def test_broken_refuses(self):
        self.broken()
        self.refused_broken("questions")


class BacklogExpire(Records):

    def test_out_reads_and_moves_in_the_records(self):
        self.out()
        write(os.path.join(self.records, "NICE_TO_HAVE.md"), NICE)
        git(self.hold, "add", "repos/widget/NICE_TO_HAVE.md")
        git(self.hold, "commit", "-q", "-m", "nice")
        code, out, err = self.run_cli("backlog")
        self.assertEqual(code, 0, err)
        self.assertIn("an old S4 on no step", out)
        code, out, err = self.run_cli("expire", "--days", "14", "--write")
        self.assertEqual(code, 0, err)
        self.assertIn("an old S4 on no step",
                      read(os.path.join(self.records, "history", "NICE-overflow.md")))
        self.assertNotIn("an old S4", read(os.path.join(self.records, "NICE_TO_HAVE.md")))
        self.assertFalse(os.path.exists(os.path.join(self.repo, "history")))

    def test_own_reads_the_tree(self):
        write(os.path.join(self.repo, "NICE_TO_HAVE.md"), NICE)
        write(os.path.join(self.records, "NICE_TO_HAVE.md"), "# Nice to have\n")
        code, out, err = self.run_cli("backlog")
        self.assertEqual(code, 0, err)
        self.assertIn("an old S4 on no step", out)

    def test_unset_reads_none_and_its_write_refuses(self):
        self.unset()
        code, out, err = self.run_cli("backlog")
        self.assertEqual(code, 0, err)
        self.assertIn("== widget  no NICE_TO_HAVE.md", out)
        code, _, err = self.run_cli("expire", "--write")
        self.assertEqual(code, 2, err)
        self.assertIn(KEY, err)

    def test_broken_refuses(self):
        self.broken()
        self.refused_broken("backlog")
        self.refused_broken("expire")


class Rows(Records):

    def test_out_reads_the_records_rows(self):
        self.out()
        write(os.path.join(self.records, "history", "rows", "r1", "row.md"), ROW)
        code, out, err = self.run_cli("rows")
        self.assertEqual(code, 0, err)
        self.assertIn("r1", out)

    def test_an_explicit_root_wins_in_out(self):
        self.out()
        os.makedirs(os.path.join(self.records, "history", "rows"))
        write(os.path.join(self.repo, "history", "rows", "r2", "row.md"),
              ROW.replace("Row r1", "Row r2"))
        code, out, err = self.run_cli("rows", "--root", os.path.join(self.repo, "history", "rows"))
        self.assertEqual(code, 0, err)
        self.assertIn("r2", out)

    def test_unset_and_broken_refuse(self):
        self.unset()
        code, _, err = self.run_cli("rows")
        self.assertEqual(code, 2, err)
        self.assertIn(KEY, err)
        self.broken()
        self.refused_broken("rows")


class Analyze(Records):

    def test_out_with_a_holder_dates_by_its_commits(self):
        self.out()
        write(os.path.join(self.records, "NICE_TO_HAVE.md"), NICE)
        git(self.hold, "add", "repos/widget/NICE_TO_HAVE.md")
        git(self.hold, "commit", "-q", "-m", "nice")
        code, out, err = self.run_cli("analyze", "churn")
        self.assertEqual(code, 0, err)
        self.assertTrue(any(l.startswith("== widget") and l.endswith("NICE - - 1")
                            for l in out.splitlines()), out)
        said = [l for l in out.splitlines() if l.startswith("records  out at %s" % self.records)]
        self.assertEqual(len(said), 1, out)
        self.assertIn("dated by the holder's commits (%s)" % self.hold, said[0])

    def test_out_with_no_holder_takes_no_snapshot(self):
        plain = os.path.join(self.tmp, "plain", "widget")
        os.makedirs(plain)
        write(os.path.join(plain, "NICE_TO_HAVE.md"), NICE)
        self.out(plain)
        code, out, err = self.run_cli("analyze", "churn")
        self.assertEqual(code, 0, err)
        self.assertIn("not measured: R4 (the records at %s are in no git repository: no "
                      "snapshot)" % plain, out.splitlines())
        self.assertIn("records  out at %s, in no git repository" % plain, out.splitlines())

    def test_unset_and_broken(self):
        self.unset()
        code, out, err = self.run_cli("analyze", "churn")
        self.assertEqual(code, 0, err)
        self.assertIn("not measured: R4 (no records here: the key %s is not set)" % KEY, out)
        self.broken()
        self.refused_broken("analyze", "churn")
