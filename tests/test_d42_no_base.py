"""d42: a block with no base line, or with more than one, is the owner's line by line;
`answer --pick` refuses it, `--other` keeps every line of it, `ask` leaves it alone, and
no verb reads git for it."""

import json
import os
import shutil
import tempfile
from unittest import mock

from decisions import questions
from tests.test_answer_head import FOLLOW, TYPED
from tests.test_d41_base import OTHER, PICK, Base
from tests.test_new import sha

NO_BASE = ("answer: question 9's block has no base line, or more than one, so answer cannot "
           "tell its lines from typed ones; pass --other, which keeps them in the Answered line; "
           "nothing written")
SKIP = ("ask: question %d has no base line, or more than one, so its lines cannot be told from "
        "typed ones; run agentik decisions answer %d --other for it first; not asked\n")
WORDS = "%s %s" % (FOLLOW, TYPED)
SHAPED = "<!-- decisions: base deadbeef -->"


class NoBase(Base):

    def type_words(self):
        self.swap(FOLLOW, WORDS)

    def base_line(self):
        return self.bases()[0]

    def whole(self):
        """W for question 9 as it stands: every non-blank line above its answer line,
        stripped, the stray lines first, each once (d42 ruling 4)."""
        block = self.block()
        lines = []
        for line in block.text.splitlines():
            if line.startswith(questions.ANSWER):
                break
            if line.strip():
                lines.append(line.strip())
        rest = [line for line in lines if line not in block.stray]
        return " ".join(list(block.stray) + rest + ([block.answer] if block.answer else []))

    def open_nine(self):
        """Question 9's open block, or None; its heading may sit in an Answered line."""
        return next((b for b in questions.parse(self.read(self.questions)).blocks
                     if b.number == 9), None)

    def no_base_pick(self):
        before = sha(self.ledger), sha(self.questions)
        code, out, err = self.answer(*PICK)
        self.assertEqual(code, 2, out + err)
        self.assertIn(NO_BASE, err)
        self.assertNotIn(TYPED, err)
        self.assertNotIn("git", err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)

    def kept_whole(self, *held):
        expected = self.whole()
        for text in held:
            self.assertIn(text, expected)
        code, out, err = self.answer(*OTHER)
        self.assertEqual(code, 0, err)
        text = self.read(self.questions)
        self.assertIsNone(self.open_nine())
        self.assertIn("- 9. Pin the interpreter: Other: Follow, but later; the owner's line: "
                      "%s (2026-09-28; chat)\n" % expected, text)

    def not_asked(self, *numbers):
        before = sha(self.ledger), sha(self.questions)
        code, out, err = self.ask(*(numbers or ("9",)))
        self.assertEqual((code, err), (0, SKIP % (9, 9)))
        self.assertEqual(json.loads(out), [])
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        self.assertFalse(os.path.exists(self.log))

    def never_based(self, commit=True):
        """Line 3's block: never a base line, words typed, the file committed by path."""
        self.restamp(unstamp=True)
        if commit:
            self.commit()
        self.type_words()
        if commit:
            self.commit("OPEN-QUESTIONS.md")
        self.rendered(reword=(9,))
        self.write(self.text, self.read(self.text).replace(" " + TYPED, ""))


class Damaged(NoBase):

    def test_a_base_line_cut_by_a_digit_is_a_line_like_any_other(self):
        """Line 1: at the pin `ask` stamped a base holding the typed line's digest."""
        self.commit()
        self.type_words()
        base = self.base_line()
        self.swap(base, base[:-5] + base[-4:])
        self.commit("OPEN-QUESTIONS.md")
        self.assertIsNone(self.block().base)
        self.rendered(reword=(9,))
        self.not_asked()
        self.no_base_pick()
        self.kept_whole(WORDS, base[:-5] + base[-4:])

    def test_a_deleted_base_line_refuses_pick_and_other_keeps_the_words(self):
        """Line 2: at the pin `--pick` exited 0 and the words were in neither file."""
        self.commit()
        self.type_words()
        self.swap(self.base_line() + "\n\n", "")
        self.commit("OPEN-QUESTIONS.md")
        self.no_base_pick()
        self.kept_whole(WORDS, "## 9. Pin the interpreter")


class Never(NoBase):

    def capture(self):
        from tests.test_d41_base import Asked
        return Asked.capture(self)

    def test_a_block_that_never_had_one(self):
        """Line 3: at the pin `--pick` exited 0 and `ask` reworded the block over the
        words."""
        self.never_based()
        self.no_base_pick()
        self.not_asked()
        self.new("Name the gate")
        self.rendered(reword=(10,))
        before = self.block().text
        seen, patch = self.capture()
        with patch:
            code, out, err = self.ask("9", "10")
        self.assertEqual((code, err), (0, SKIP % (9, 9)))
        self.assertEqual(len(seen), 1)
        self.assertNotIn("## 9.", seen[0])
        self.assertIn("## 10.", seen[0])
        self.assertEqual([q["header"] for q in json.loads(out)[0]["questions"]],
                         ["Decision 10"])
        self.assertEqual(self.block().text, before)
        self.assertIsNone(self.block().base)
        self.kept_whole(WORDS)

    def test_no_git_repository_and_no_git_on_path(self):
        """Line 4: at the pin both answers exited 2, "git holds no copy"."""
        empty = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, empty)
        for scene in ("no repository", "git off PATH"):
            with self.subTest(scene=scene):
                self.setUp()
                self.never_based(commit=scene != "no repository")
                self.assertFalse(scene == "no repository"
                                 and os.path.exists(os.path.join(self.tmp, ".git")))
                path = empty if scene == "git off PATH" else os.environ["PATH"]
                with mock.patch.dict(os.environ, {"PATH": path}):
                    self.no_base_pick()
                    self.not_asked()
                    self.kept_whole(WORDS)


class Shaped(NoBase):

    def test_a_second_base_shaped_line_bare_and_fenced(self):
        """Line 5: at the pin `--pick` exited 0 and the line was in neither file."""
        for name, typed in (("bare", SHAPED), ("fenced", "```\n%s\n```" % SHAPED)):
            with self.subTest(shape=name):
                self.setUp()
                self.swap("**Recommendation.**", "%s\n\n**Recommendation.**" % typed, once=False)
                self.assertIsNone(self.block().base)
                self.assertIn(SHAPED, self.block().text)
                self.assertEqual(self.lint()[0], 1)
                self.no_base_pick()
                self.kept_whole(SHAPED, self.base_line(), *typed.splitlines())


class Asked(NoBase):

    def test_a_clean_block_with_no_base_that_head_holds_is_not_asked(self):
        """Line 6: at the pin it was asked and stamped."""
        self.restamp(unstamp=True)
        self.commit()
        self.rendered(reword=(9,))
        self.not_asked()
        self.assertIsNone(self.block().base)

    def test_the_warning_comes_after_the_answered_skip(self):
        self.restamp(unstamp=True)
        self.swap("**Your answer:**", "**Your answer:** Pin", once=False)
        code, out, err = self.ask("9")
        self.assertEqual(code, 0)
        self.assertIn("ask: question 9 is answered on its", err)
        self.assertNotIn("no base line", err)


class NoGit(NoBase):

    def test_answer_and_ask_never_call_git(self):
        """Line 7: at the pin a block with none called git twice under `ask` and once
        under `answer`."""
        bin_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, bin_dir)
        log = os.path.join(bin_dir, "calls")
        self.write(os.path.join(bin_dir, "git"), "#!/bin/sh\necho \"$*\" >> '%s'\nexit 1\n"
                   % log)
        os.chmod(os.path.join(bin_dir, "git"), 0o755)
        for scene in ("based", "none"):
            with self.subTest(scene=scene):
                self.setUp()
                if scene == "none":
                    self.restamp(unstamp=True)
                self.commit()
                with mock.patch.dict(os.environ, {"PATH": bin_dir + ":/usr/bin:/bin"}):
                    self.assertEqual(self.ask("9", env={})[0], 0)
                    self.answer(*PICK)
                    self.answer(*OTHER)
                self.assertIsNone(self.open_nine())
                self.assertFalse(os.path.exists(log), scene)
