"""d41: a question block carries its own base line, so the owner's typed lines are never
lost by `answer --pick` or by `ask`, whatever git holds."""

import io
import json
import os
import shutil
import tempfile
from unittest import mock

import decisions
from decisions import questions, speak
from tests import test_ask, test_new
from tests.test_answer_head import FOLLOW, TYPED, Repo
from tests.test_new import sha

PICK = ("9", "--pick", "Pin", "--source", "chat", "--no-entry")
OTHER = ("9", "--other", "Follow, but later", "--source", "chat", "--no-entry")
SECOND = "Revisit when 3.13 ships."
WARNING = ("ask: question 9 holds lines typed since it was written; run agentik decisions "
           "answer 9 --other for it first; not asked\n")


class Base(Repo, test_new.Base):
    """The sample ledger and questions, question 9 written by `new`, and test_ask's stub
    respeak; `ask` names its questions, so the sample's 8 is not asked."""

    new, rendered, ask = test_ask.Ask.new, test_ask.Ask.rendered, test_ask.Ask.ask

    def setUp(self):
        super().setUp()
        side = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, side)
        self.stub = os.path.join(side, "respeak")
        os.makedirs(os.path.join(self.stub, "scripts"))
        self.write(os.path.join(self.stub, "scripts", "respeak-render.sh"), test_ask.STUB)
        self.log, self.text = os.path.join(side, "log"), os.path.join(side, "text")
        self.env = {"RESPEAK_ROOT": self.stub, "STUB_LOG": self.log, "STUB_TEXT": self.text}
        # the sample's question 8, which its Proposed entry 8 names, has no base line
        shutil.copy(test_new.SAMPLE_QUESTIONS, self.questions)
        self.new("Pin the interpreter")

    def answer(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["answer"] + list(argv) + ["--ledger", self.ledger],
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def lint(self):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["render", "--lint", "--ledger", self.ledger], out=out, err=err)
        return code, out.getvalue() + err.getvalue()

    def swap(self, old, new, once=True):
        """`old` replaced by `new`: its one occurrence, else its first in question 9."""
        text = self.read(self.questions)
        if once:
            self.assertEqual(text.count(old), 1, old)
        at = text.index(old, text.index("## 9. "))
        self.write(self.questions, text[:at] + new + text[at + len(old):])

    def block(self, number=9):
        return next(b for b in questions.parse(self.read(self.questions)).blocks
                    if b.number == number)

    def bases(self):
        return [l for l in self.read(self.questions).splitlines()
                if l.startswith("<!-- decisions: base ")]

    def refused(self, argv, *named):
        before = sha(self.ledger), sha(self.questions)
        code, out, err = self.answer(*argv)
        self.assertEqual(code, 2, out + err)
        self.assertIn("typed since `new` or `ask` wrote it; pass --other", err)
        self.assertNotIn("commit", err)
        for text in named:
            self.assertIn(text, err)
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)

    def answered(self, *typed):
        code, out, err = self.answer(*OTHER)
        self.assertEqual(code, 0, err)
        text = self.read(self.questions)
        self.assertNotIn("## 9.", text)
        self.assertIn("- 9. Pin the interpreter: Other: Follow, but later; the owner's line: "
                      "%s (2026-09-28; chat)\n" % " ".join(typed), text)


class Line(Base):

    def test_new_writes_one_base_line_the_lint_takes(self):
        """Line 1."""
        self.assertEqual(len(self.bases()), 1)
        block = self.block()
        self.assertEqual(block.base, questions.digests(block.text))
        self.assertEqual(block.stray, ())
        self.assertNotIn("decisions: base", block.text)
        self.assertEqual(self.lint()[0], 0)

    def test_a_second_base_line_is_a_problem_a_typed_line_is_not(self):
        """Line 9."""
        base = self.bases()[0]
        self.swap(FOLLOW, "%s %s" % (FOLLOW, TYPED))
        self.assertEqual(self.lint()[0], 0)
        self.swap("**The choice.**", "%s\n\n**The choice.**" % base, once=False)
        code, said = self.lint()
        self.assertEqual(code, 1, said)
        self.assertIn("question 9: a second base line", said)


class Pick(Base):

    def test_words_committed_by_path_still_refuse_pick(self):
        """Lines 2 and 3: the fault at the pin, `--pick` exited 0 and lost the words."""
        self.commit()
        self.swap(FOLLOW, "%s %s" % (FOLLOW, TYPED))
        self.swap("**Your answer:**", "**Your answer:** Pin", once=False)
        self.commit("OPEN-QUESTIONS.md")
        self.refused(PICK, "%s %s" % (FOLLOW, TYPED))
        code, out, err = self.answer(*OTHER)
        self.assertEqual(code, 0, err)
        self.assertIn("Other: Follow, but later; the owner's line: %s %s Pin (2026-09-28; chat)"
                      % (FOLLOW, TYPED), self.read(self.questions))

    def test_three_orders_keep_each_line_once(self):
        """Line 4: type, commit, type, commit; commit, type; type alone."""
        one, two = "%s %s" % (FOLLOW, TYPED), "No, not before 3.14"
        orders = {"twice": True, "after": False, "alone": None}
        for name, early in orders.items():
            with self.subTest(order=name):
                self.setUp()
                if early is False:
                    self.commit()
                self.swap(FOLLOW, one)
                if early:
                    self.commit()
                self.swap(SECOND, "%s\n%s" % (SECOND, two))
                if early:
                    self.commit()
                self.refused(PICK, one, two)
                self.answered(one, two)

    def test_no_git_repository_and_no_git_on_path_pick(self):
        """Line 5: a block with a base line runs no git."""
        code, out, err = self.answer(*PICK)
        self.assertEqual(code, 0, err)
        self.setUp()
        self.commit()
        empty = tempfile.mkdtemp()
        self.addCleanup(os.rmdir, empty)
        # d42 R3: `answer` runs no git for any block, so `head_block` is gone
        with mock.patch.dict(os.environ, {"PATH": empty}):
            code, out, err = self.answer(*PICK)
        self.assertEqual(code, 0, err)
        self.assertIn("answer: 9, Pin", out)


class Asked(Base):

    def capture(self):
        seen = []
        real = speak.render_text

        def render(text, *args, **kwargs):
            seen.append(text)
            return real(text, *args, **kwargs)
        return seen, mock.patch.object(speak, "render_text", render)

    def test_a_typed_block_is_not_rendered_written_or_asked(self):
        """Line 6: at the pin the block was rewritten and the words were gone."""
        self.rendered(reword=(9,))
        self.swap(FOLLOW, "%s %s" % (FOLLOW, TYPED))
        before = sha(self.ledger), sha(self.questions)
        code, out, err = self.ask("9")
        self.assertEqual((code, err), (0, WARNING))
        self.assertEqual(json.loads(out), [])
        self.assertEqual((sha(self.ledger), sha(self.questions)), before)
        self.assertFalse(os.path.exists(self.log))

    def test_a_clean_block_is_rendered_without_its_base_and_stamped(self):
        """Line 7."""
        self.rendered(reword=(9,))
        seen, patch = self.capture()
        with patch:
            code, out, err = self.ask("9")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(len(seen), 1)
        self.assertNotIn("decisions: base", seen[0])
        self.assertIn("Keep 3.12 pinned.", self.read(self.questions))
        block = self.block()
        self.assertEqual((len(self.bases()), block.base), (1, questions.digests(block.text)))
        code, out, err = self.answer(*PICK)
        self.assertEqual(code, 0, err)

    def test_a_block_with_no_base_line(self):
        """Line 8, rewritten by d42 (rulings 3 to 5): a block with no base line is not
        asked, stamped or written, HEAD holding it or not, and `--pick` is refused."""
        self.restamp(unstamp=True)
        self.commit()
        self.new("Pin it again")
        self.restamp(unstamp=True)
        self.assertEqual(self.bases(), [])
        before = sha(self.questions)
        code, out, err = self.ask("9", "10", env={})
        self.assertEqual(code, 0)
        self.assertEqual(err, "".join(
            "ask: question %d has no base line, or more than one, so its lines cannot be told "
            "from typed ones; run agentik decisions answer %d --other for it first; not "
            "asked\n" % (n, n) for n in (9, 10)))
        self.assertEqual(json.loads(out), [])
        self.assertEqual(sha(self.questions), before)
        code, out, err = self.answer(*PICK)
        self.assertEqual(code, 2, err)
        self.assertIn("has no base line, or more than one", err)
        self.assertEqual(sha(self.questions), before)

    def test_a_failed_stamp_warns_and_exits_0(self):
        """Ruling 6: a base line that cannot be written is a warning, exit 0; d42: the
        block's base holds a digest of a line deleted since, so `ask` stamps it again."""
        base = self.bases()[0]
        self.swap(base, base[:-len(" -->")] + " deadbeef -->")
        before = sha(self.questions)
        with mock.patch("os.replace", side_effect=PermissionError(1, "Operation not permitted")):
            code, out, err = self.ask("9", env={})
        self.assertEqual(code, 0, err)
        self.assertEqual(err.count("the questions stay as written"), 2, err)
        self.assertEqual(sha(self.questions), before)
        self.assertEqual(json.loads(out)[0]["questions"][0]["header"], "Decision 9")
