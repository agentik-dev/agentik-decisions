"""`answer` on a block with no base line (d42, which replaced d35's HEAD rule): every line
of it is the owner's, whatever git holds, so `--pick` is refused, naming no line, and
`--other` keeps every line in the Answered line, the stray lines first, then T. `Repo`
stays: the d41 and d42 cases commit through it."""

import io
import os
import shutil
import subprocess
import tempfile
from unittest import mock

import decisions
from tests.hermetic import SAMPLE
from tests.test_new import PARTS, SAMPLE_QUESTIONS, Base, sha

GIT = shutil.which("git") or "/usr/bin/git"
BOTH = ("DECISIONS.md", "OPEN-QUESTIONS.md")
PICK = ("9", "--pick", "Pin", "--source", "chat", "--no-entry")
OTHER = ("9", "--other", "Follow, but later", "--source", "chat", "--no-entry")
FOLLOW = "- **Follow.** Tracks releases."
TYPED = "THIS ONE, never before December"


def git(root, *args):
    """git in `root`, blind to the caller's git variables and to every config file."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.run([GIT, "-c", "user.name=f", "-c", "user.email=f",
                           "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]
                          + list(args), cwd=root, env=env, check=True,
                          capture_output=True, text=True).stdout


class Repo:
    """A git repo made once a class, its index holding both files and no commit yet, so
    a case's commit is one git child on a copy of it (d35: three a case took
    test_answer.py from 0.7 s to 12.8 s under load)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = tempfile.mkdtemp(prefix="decisions-d35-")
        cls.addClassCleanup(shutil.rmtree, root, True)
        git(root, "init", "-q", "--template=")
        for name in BOTH:
            open(os.path.join(root, name), "w").close()
        git(root, "add", *BOTH)
        cls.repo = os.path.join(root, ".git")

    def commit(self, *names, root=None):
        """HEAD holds `names`, both files by default, as they stand in `root`, `self.tmp`
        by default."""
        root = root or self.tmp
        if not os.path.isdir(os.path.join(root, ".git")):
            shutil.copytree(self.repo, os.path.join(root, ".git"))
        git(root, "commit", "-q", "--allow-empty", "-m", "the questions as they stand",
            *(("--",) + names if names else ("-a",)))


class Head(Repo, Base):

    def setUp(self):
        super().setUp()
        self.scene()
        self.commit()

    def scene(self):
        """A fresh ledger with question 9 open, no base line in any block, committed."""
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.ledger = os.path.join(self.tmp, "DECISIONS.md")
        self.questions = os.path.join(self.tmp, "OPEN-QUESTIONS.md")
        shutil.copy(SAMPLE, self.ledger)
        shutil.copy(SAMPLE_QUESTIONS, self.questions)
        self.new()

    def new(self, title=None, *extra):
        argv = list(PARTS) + list(extra)
        if title:
            argv[argv.index("--title") + 1] = title
        code, _, err = self.run_cli(*argv)
        self.assertEqual(code, 0, err)
        # d42: these cases hold blocks with no base line, as written before d41
        self.restamp(unstamp=True)

    def answer(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["answer"] + list(argv) + ["--ledger", self.ledger],
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def swap(self, old, new):
        text = self.read(self.questions)
        self.assertEqual(text.count(old), 1, old)
        self.write(self.questions, text.replace(old, new))

    def refused(self, argv=PICK, number=9):
        """`answer argv` exits 2 with d42's refusal, names no line, and changes neither
        file."""
        before = sha(self.ledger), sha(self.questions)
        code, out, err = self.answer(*argv)
        self.assertEqual(code, 2, out + err)
        self.assertIn("answer: question %d's block has no base line, or more than one, so "
                      "answer cannot tell its lines from typed ones; pass --other, which keeps "
                      "them in the Answered line; nothing written\n" % number, err)
        self.assertEqual(err.count("\n"), 1, err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)

    def whole(self, number=9, typed=""):
        """W: every non-blank line of block `number` above its answer line, stripped, the
        stray lines first, then T."""
        block = next(b for b in decisions.questions.parse(self.read(self.questions)).blocks
                     if b.number == number)
        lines = [line.strip() for line in
                 block.text.split(decisions.questions.ANSWER)[0].splitlines() if line.strip()]
        return " ".join(list(block.stray) + [l for l in lines if l not in block.stray]
                        + ([typed] if typed else []))

    def answered(self, expected, title="Pin the interpreter", number=9):
        code, out, err = self.answer(*((str(number),) + OTHER[1:]))
        self.assertEqual(code, 0, err)
        answered = [l for l in self.read(self.questions).splitlines()
                    if l.startswith("- %d." % number)]
        self.assertEqual(answered, ["- %d. %s: Other: Follow, but later; the owner's line: %s "
                                    "(2026-09-28; chat)" % (number, title, expected)])

    # every line is the owner's: the doors of NICE n2 and n17, then d42's own

    def test_text_at_the_end_of_an_option_line_refuses_pick(self):
        self.swap(FOLLOW, "%s %s" % (FOLLOW, TYPED))
        self.refused()
        self.answered(self.whole())
        self.assertIn(TYPED, self.read(self.questions))

    def test_a_line_typed_into_a_parts_paragraph_refuses_pick(self):
        self.swap("Revisit when 3.13 ships.", "Revisit when 3.13 ships.\nNo: follow, " + TYPED)
        self.refused()
        self.answered(self.whole())

    def test_an_option_line_of_the_owners_own_refuses_pick(self):
        own = "- **Neither.** Close it, " + TYPED
        self.swap(FOLLOW, "%s\n%s" % (FOLLOW, own))
        self.refused()
        self.refused(("9", "--pick", "Neither", "--source", "chat", "--no-entry"))

    def test_a_line_typed_under_the_report_refuses_pick(self):
        self.new("Name the gate", "--report", "The probe's page.")
        self.commit()
        text = self.read(self.questions)
        line = next(l for l in text.splitlines() if l.startswith("**Report.**"))
        self.swap(line, "%s\nRead it, %s" % (line, TYPED))
        self.refused(("10", "--pick", "Pin", "--source", "chat", "--no-entry"), 10)
        self.assertIn("Read it, " + TYPED, self.whole(10))
        self.answered(self.whole(10), "Name the gate", 10)

    def test_a_clean_block_that_head_holds_refuses_pick_and_other_keeps_it_whole(self):
        """d42 ruling 1: a commit is no evidence; the heading is in W, untrimmed."""
        self.refused()
        expected = self.whole()
        self.assertTrue(expected.startswith("## 9. Pin the interpreter **Where things stand.**"))
        self.answered(expected)

    def test_an_unknown_pick_is_refused_first(self):
        code, out, err = self.answer("9", "--pick", "Nope", "--source", "chat", "--no-entry")
        self.assertEqual(code, 2, err)
        self.assertIn("has no option 'Nope'", err)

    def test_no_repository_no_commit_and_no_git_read_nothing(self):
        def no_tree():
            pass

        def no_commit():
            git(self.tmp, "init", "-q")

        def untracked():
            self.commit("DECISIONS.md")

        for scene in (no_tree, no_commit, untracked):
            with self.subTest(scene=scene.__name__):
                self.scene()
                scene()
                self.refused()
                self.answered(self.whole())
        with self.subTest(scene="git off PATH"):
            self.scene()
            empty = tempfile.mkdtemp()
            self.addCleanup(shutil.rmtree, empty, True)
            with mock.patch.dict(os.environ, {"PATH": empty}):
                self.refused()
                self.answered(self.whole())

    def test_text_on_the_answer_line_that_names_an_option_takes_other_whole(self):
        """d28's `--pick` of the named option needs a base line; `--other` keeps T last."""
        text = self.read(self.questions)
        at = text.index("**Your answer:**", text.index("## 9."))
        self.write(self.questions, text[:at] + "**Your answer:** Pin" + text[at + 16:])
        self.refused()
        self.answered(self.whole(typed="Pin"))

    def test_a_line_no_part_takes_comes_first_and_enters_once(self):
        loose = "A loose line, typed by the owner."
        self.swap(FOLLOW + "\n\n", "%s\n\n%s\n\n" % (FOLLOW, loose))
        self.refused()
        expected = self.whole()
        self.assertTrue(expected.startswith(loose + " ## 9."), expected)
        self.assertEqual(expected.count(loose), 1)
        self.answered(expected)
