"""in5d: on the path that asks, `reply` shows the line before and after on stderr, the
stream its question is on, and nothing of it on stdout; `--dry-run` and `--yes` print as
at 0.23.18, byte for byte."""

import os
import subprocess
import sys

from tests.test_in5a_reply import ANSWER, LIB, Reply

# 0.23.18's output, captured on these stand-ins before the change; %s is the questions
# file's path, as `display` gives it for a file under the hermetic home.
DRY_PICK = ("question 10, %s line 36:\n- **Your answer:**\n+ **Your answer:** South gate\n"
            "reply: dry run, nothing written\n")
DRY_SAY = ("question 10, %s line 36:\n- **Your answer:**\n+ **Your answer:** north\n"
           "reply: dry run, nothing written\n")
YES_OUT = ("question 10: your answer is on its line; the sitting enters it with agentik "
           "decisions answer 10\n")
# the child runs in the ledger's folder, so `display` gives the file's name alone
SHOWN = ("question 10, OPEN-QUESTIONS.md line 36:\n- **Your answer:**\n"
         "+ **Your answer:** north\n")
ASKED = "write it on question 10's answer line? [y/N] "


class Line1AskedOnErr(Reply):

    def pty(self, typed):
        master, slave = os.openpty()
        env = dict(os.environ, PYTHONPATH=LIB)
        child = subprocess.Popen([sys.executable, "-m", "decisions", "reply", str(self.n),
                                  "--say", "north", "--ledger", self.ledger], stdin=slave,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                                 cwd=self.pear)
        os.close(slave)
        self.addCleanup(os.close, master)
        os.write(master, typed)
        out, err = child.communicate(timeout=60)
        return child.returncode, out.decode(), err.decode()

    def test_1_the_lines_are_on_err_before_the_question(self):
        self.assertEqual(self.n, 10)
        # `n` first: it writes nothing, so `y` then finds the line empty
        for typed, code_wanted, out_wanted in ((b"n\n", 1, ""), (b"y\n", 0, YES_OUT)):
            with self.subTest(typed=typed):
                q = self.read(self.file)
                code, out, err = self.pty(typed)
                self.assertEqual(code, code_wanted, out + err)
                self.assertTrue(err.startswith(SHOWN + ASKED), err)
                self.assertNotIn(ANSWER, out)
                self.assertEqual(out, out_wanted)
                if code_wanted == 1:
                    self.assertIn("declined", err)
                    self.assertEqual(self.read(self.file), q)


class Line2AsAtThePin(Reply):

    def test_2_dry_run_as_at_the_pin(self):
        self.assertEqual(self.n, 10)
        self.assertEqual(self.reply(self.n, "--pick", "south gate", "--dry-run"),
                         (0, DRY_PICK % self.file, ""))
        self.assertEqual(self.reply(self.n, "--say", "north", "--dry-run"),
                         (0, DRY_SAY % self.file, ""))

    def test_2_yes_as_at_the_pin(self):
        self.assertEqual(self.reply(self.n, "--say", "north", "--yes"), (0, YES_OUT, ""))
