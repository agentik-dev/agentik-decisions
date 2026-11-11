"""`answer` and git's copy of the question (d35): a line of block N that HEAD's copy of
OPEN-QUESTIONS.md lacks is the owner's until git holds it, so `--pick` is refused and
`--other` keeps it in the Answered line; with no copy of question N in HEAD, `answer`
cannot tell what was typed and writes nothing."""

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
        """A fresh ledger with question 9 open and nothing committed."""
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

    def answer(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["answer"] + list(argv) + ["--ledger", self.ledger],
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def swap(self, old, new):
        text = self.read(self.questions)
        self.assertEqual(text.count(old), 1, old)
        self.write(self.questions, text.replace(old, new))

    def refused(self, argv, *named):
        """`answer argv` exits 2, names each of `named`, and changes neither file."""
        before = sha(self.ledger), sha(self.questions)
        code, out, err = self.answer(*argv)
        self.assertEqual(code, 2, out + err)
        self.assertIn("nothing written", err)
        for text in named:
            self.assertIn(text, err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        return err

    # the three doors of NICE n2 and n17 that the review's probe reproduced (B, C, D)

    def test_text_at_the_end_of_an_option_line_refuses_pick(self):
        self.swap(FOLLOW, "%s %s" % (FOLLOW, TYPED))
        self.refused(PICK, "%s %s" % (FOLLOW, TYPED), "--other")

    def test_a_line_typed_into_a_parts_paragraph_refuses_pick(self):
        self.swap("Revisit when 3.13 ships.", "Revisit when 3.13 ships.\nNo: follow, " + TYPED)
        self.refused(PICK, "No: follow, " + TYPED)

    def test_an_option_line_of_the_owners_own_refuses_pick(self):
        own = "- **Neither.** Close it, " + TYPED
        self.swap(FOLLOW, "%s\n%s" % (FOLLOW, own))
        self.refused(PICK, own)
        self.refused(("9", "--pick", "Neither", "--source", "chat", "--no-entry"), own)

    def test_a_line_typed_under_the_report_refuses_pick(self):
        self.new("Name the gate", "--report", "The probe's page.")
        self.commit()
        text = self.read(self.questions)
        line = next(l for l in text.splitlines() if l.startswith("**Report.**"))
        self.swap(line, "%s\nRead it, %s" % (line, TYPED))
        self.refused(("10", "--pick", "Pin", "--source", "chat", "--no-entry"),
                     "Read it, " + TYPED)

    def test_other_keeps_each_line_head_lacks_in_the_answered_line(self):
        self.swap(FOLLOW, "%s %s" % (FOLLOW, TYPED))
        code, out, err = self.answer(*OTHER)
        self.assertEqual(code, 0, err)
        text = self.read(self.questions)
        self.assertNotIn("## 9.", text)
        self.assertIn("- 9. Pin the interpreter: Other: Follow, but later; the owner's line: "
                      "%s %s (2026-09-28; chat)\n" % (FOLLOW, TYPED), text)

    def test_a_block_reworded_since_its_commit_refuses_pick_until_head_holds_it(self):
        new = "**Where things stand.** The tool runs on Python 3.12 today."
        self.swap("**Where things stand.** The tool runs under 3.12.", new)
        err = self.refused(PICK, new)
        self.assertIn("commit", err)
        self.commit()
        self.assertEqual(self.answer(*PICK)[0], 0)

    def test_no_copy_of_the_question_in_head_refuses_pick_and_other(self):
        def no_tree():
            pass

        def no_commit():
            git(self.tmp, "init", "-q")

        def untracked():
            self.commit("DECISIONS.md")

        def put_since():
            self.commit()
            self.new("Name the gate")

        for scene, number in ((no_tree, "9"), (no_commit, "9"), (untracked, "9"),
                              (put_since, "10")):
            with self.subTest(scene=scene.__name__):
                self.scene()
                scene()
                for argv in (PICK, OTHER):
                    err = self.refused((number,) + argv[1:], "commit")
                    self.assertIn("question %s" % number, err)
                    self.assertIn("read the block first: a commit makes every line in it the "
                                  "block's own, so words the owner typed there are carried in "
                                  "--other's text; then commit OPEN-QUESTIONS.md and run this "
                                  "again; nothing written", err)

    # the refuter's round 1: the name git tracks, and git's own variables (F1, F3)

    def test_a_name_head_tracks_under_another_case_is_read_when_it_is_the_only_one(self):
        def track_as(*names):
            blob = git(self.tmp, "hash-object", "-w", "OPEN-QUESTIONS.md").strip()
            git(self.tmp, "rm", "-q", "--cached", "OPEN-QUESTIONS.md")
            for name in names:
                git(self.tmp, "update-index", "--add", "--cacheinfo",
                    "100644,%s,%s" % (blob, name))
            git(self.tmp, "commit", "-q", "-m", "the questions under another case")

        with self.subTest(names="one"):
            track_as("open-questions.md")
            code, out, err = self.answer(*PICK)
            self.assertEqual(code, 0, err)
            self.assertIn("- 9. Pin the interpreter: Pin (2026-09-28; chat)\n",
                          self.read(self.questions))
        with self.subTest(names="two"):
            self.scene()
            self.commit()
            track_as("open-questions.md", "Open-Questions.md")
            for argv in (PICK, OTHER):
                self.refused(argv, "HEAD does not hold OPEN-QUESTIONS.md", "commit")

    def test_git_dir_naming_another_repo_reads_the_head_of_the_files_own(self):
        typed = "%s %s" % (FOLLOW, TYPED)
        self.swap(FOLLOW, typed)
        other = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, other, True)
        for name in BOTH:
            shutil.copy(os.path.join(self.tmp, name), other)
        self.commit(root=other)
        with mock.patch.dict(os.environ, {"GIT_DIR": os.path.join(other, ".git")}):
            self.refused(PICK, typed, "--other")
        self.assertIn(typed, self.read(self.questions))

    def test_a_clean_block_in_a_subdirectory_takes_pick_under_a_hooks_git_dir(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        sub = os.path.join(root, "q")
        os.mkdir(sub)
        for name in BOTH:
            shutil.copy(os.path.join(self.tmp, name), sub)
        self.ledger, self.questions = (os.path.join(sub, name) for name in BOTH)
        git(root, "init", "-q", "--template=")
        git(root, "add", "q")
        git(root, "commit", "-q", "-m", "the questions in a subdirectory")
        with mock.patch.dict(os.environ, {"GIT_DIR": ".git"}):
            code, out, err = self.answer(*PICK)
        self.assertEqual(code, 0, err)
        self.assertIn("- 9. Pin the interpreter: Pin (2026-09-28; chat)\n",
                      self.read(self.questions))

    def test_no_commit_while_git_dir_names_a_repo_with_one_refuses(self):
        other = self.tmp
        self.scene()
        git(self.tmp, "init", "-q", "--template=")
        with mock.patch.dict(os.environ, {"GIT_DIR": os.path.join(other, ".git")}):
            for argv in (PICK, OTHER):
                self.refused(argv, "no commit to read there", "question 9")

    def test_git_that_cannot_run_refuses(self):
        empty = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, empty, True)
        with mock.patch.dict(os.environ, {"PATH": empty}):
            self.refused(PICK, "git")
            self.refused(OTHER, "git")

    # what stays as it is

    def test_a_block_as_head_holds_it_takes_pick_whatever_its_spacing(self):
        self.swap("**The choice.** Pin 3.12", "**The choice.**  Pin 3.12")
        self.swap(FOLLOW, FOLLOW + "   ")
        code, out, err = self.answer(*PICK)
        self.assertEqual(code, 0, err)
        self.assertIn("- 9. Pin the interpreter: Pin (2026-09-28; chat)\n",
                      self.read(self.questions))

    def test_typed_text_that_head_holds_leaves_with_the_block_and_git_keeps_it(self):
        self.swap(FOLLOW, "%s %s" % (FOLLOW, TYPED))
        self.commit()
        self.assertEqual(self.answer(*PICK)[0], 0)
        self.assertNotIn(TYPED, self.read(self.questions))
        self.assertIn(TYPED, git(self.tmp, "show", "HEAD:OPEN-QUESTIONS.md"))

    def test_a_line_no_part_takes_keeps_d30s_refusal_and_enters_once(self):
        loose = "A loose line, typed by the owner."
        self.swap(FOLLOW + "\n\n", "%s\n\n%s\n\n" % (FOLLOW, loose))
        self.refused(PICK, "no part of its block takes", loose)
        code, out, err = self.answer(*OTHER)
        self.assertEqual(code, 0, err)
        answered = [l for l in self.read(self.questions).splitlines() if l.startswith("- 9.")]
        self.assertEqual(len(answered), 1)
        self.assertEqual(answered[0].count(loose), 1)
