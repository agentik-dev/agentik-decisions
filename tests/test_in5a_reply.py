"""in5a: `reply N (--pick L | --say T)` types the owner's answer onto question N's own answer
line, under `.new.lock`, and writes nothing else: no entry, no Answered line, no base line
moved, no other block touched."""

import fcntl
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
from unittest import mock

import decisions
from decisions import ask
from tests.hermetic import SAMPLE, Hermetic

ANSWER = "**Your answer:**"
DAY = "2026-09-28"
QUESTIONS = (
    ("Where the hay goes", "The barn, or the loft?",
     ["Barn: Keeps it dry by the gate.", "Loft: Frees the floor."], "The barn. It is nearer."),
    ("Which gate stays red", "The north gate, or the south one?",
     ["North gate: Faces the lane.", "South gate: Faces the pond.", "Neither: Paint both."],
     "The north gate. It is seen first."),
    ("When the goats eat", "At dawn, or at dusk?",
     ["Dawn: Before the milking.", "Dusk: After the field."], "Dawn. They graze after."),
)
HOLD = ("import fcntl, sys\nf = open(sys.argv[1], 'a')\nfcntl.flock(f, fcntl.LOCK_EX)\n"
        "print('held', flush=True)\nsys.stdin.read()\n")
LIB = os.path.dirname(os.path.dirname(os.path.abspath(decisions.__file__)))


def sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


class Reply(Hermetic):

    def setUp(self):
        super().setUp()
        self.home = os.path.realpath(os.environ["HOME"])
        self.pear = os.path.join(self.home, "pear")
        os.makedirs(self.pear)
        self.ledger = os.path.join(self.pear, "DECISIONS.md")
        self.file = os.path.join(self.pear, "OPEN-QUESTIONS.md")
        shutil.copy(SAMPLE, self.ledger)
        self.numbers = []
        for title, choice, options, recommend in QUESTIONS:
            argv = ["new", "--title", title, "--stands", "The yard is full.", "--choice", choice,
                    "--recommend", recommend, "--ledger", self.ledger]
            for option in options:
                argv += ["--option", option]
            with mock.patch.object(ask, "today", lambda: DAY):
                code, out, err = self.run_tool(*argv)
            self.assertEqual(code, 0, out + err)
            self.numbers.append(int(out.split(":")[1].split(",")[0]))
        self.n = self.numbers[1]
        self.stdin = mock.patch.object(sys, "stdin", io.StringIO(""))
        self.stdin.start()
        self.addCleanup(self.stdin.stop)

    def read(self, path):
        with open(path, encoding="utf-8", newline="") as handle:
            return handle.read()

    def write(self, path, text):
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)

    def run_tool(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(list(argv), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def reply(self, *argv):
        return self.run_tool("reply", *[str(a) for a in argv], "--ledger", self.ledger)

    def block(self, text, number):
        return next(b for b in decisions.questions.parse(text).blocks if b.number == number)

    def changed(self, before, after):
        """The (old, new) line pairs that differ; the line count is held equal."""
        old, new = before.splitlines(), after.splitlines()
        self.assertEqual(len(old), len(new))
        return [(a, b) for a, b in zip(old, new) if a != b]

    def typed(self, number):
        got = self.run_tool("questions", self.pear, "--json")
        self.assertEqual(got[0], 0, got)
        view = json.loads(got[1])
        return next(q for q in view["repos"][0]["questions"] if q["n"] == number)

    def refused(self, argv, *says):
        q, l = self.read(self.file), self.read(self.ledger)
        code, out, err = self.reply(*argv)
        self.assertEqual((code, out), (1, ""), err)
        self.assertEqual(len(err.strip().splitlines()), 1, err)
        self.assertIn("question %d" % argv[0], err)
        for said in says:
            self.assertIn(said, err)
        self.assertEqual((self.read(self.file), self.read(self.ledger)), (q, l))
        self.assertFalse(os.path.exists(os.path.join(self.pear, ".new.lock")))
        return err

    def fill(self, number, line, under=None):
        """Block `number` with `line` in place of its answer line, and `under` after it."""
        text = self.read(self.file)
        b = self.block(text, number)
        lines = text.splitlines(keepends=True)
        i = next(i for i in range(b.start, b.stop) if lines[i].startswith(ANSWER))
        lines[i] = line + "\n" + ("" if under is None else under + "\n")
        self.write(self.file, "".join(lines))


class Line1Pick(Reply):

    def test_1_pick_writes_one_line(self):
        q, l = self.read(self.file), self.read(self.ledger)
        base = self.block(q, self.n).base
        code, out, err = self.reply(self.n, "--pick", "north gate.", "--yes")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "question %d: your answer is on its line; the sitting enters it "
                         "with agentik decisions answer %d\n" % (self.n, self.n))
        now = self.read(self.file)
        self.assertEqual(self.changed(q, now), [(ANSWER, ANSWER + " North gate")])
        self.assertEqual(self.read(self.ledger), l)
        self.assertEqual(self.block(now, self.n).base, base)
        for number in (self.numbers[0], self.numbers[2]):
            self.assertEqual(self.block(now, number).text, self.block(q, number).text)
        self.assertFalse(os.path.exists(os.path.join(self.pear, ".new.lock")))
        seen = self.typed(self.n)
        self.assertEqual((seen["state"], seen["typed"]), ("answered", "North gate"))
        self.assertEqual(self.typed(self.numbers[0])["state"], "open")

    def test_1_answer_enters_it_and_refuses_another(self):
        self.assertEqual(self.reply(self.n, "--pick", "North Gate (Recommended)", "--yes")[0], 0)
        code, _out, err = self.run_tool("answer", str(self.n), "--pick", "South gate",
                                        "--source", "chat", "--no-entry", "--ledger", self.ledger)
        self.assertEqual(code, 2)
        self.assertIn("names the option `North gate`", err)
        code, out, err = self.run_tool("answer", str(self.n), "--pick", "North gate",
                                       "--source", "chat", "--no-entry", "--ledger", self.ledger)
        self.assertEqual(code, 0, out + err)
        self.assertIn(": North gate (", self.read(self.file))
        self.assertNotIn("## %d." % self.n, self.read(self.file))

    def test_1_the_label_as_the_block_spells_it(self):
        self.assertEqual(self.reply(self.numbers[0], "--pick", "*barn*", "--yes")[0], 0)
        self.assertEqual(self.block(self.read(self.file), self.numbers[0]).answer, "Barn")


class Line2Say(Reply):

    def test_2_say_writes_one_line(self):
        q, l = self.read(self.file), self.read(self.ledger)
        code, out, err = self.reply(self.n, "--say", "  Paint the east one, it is new  ", "--yes")
        self.assertEqual((code, err), (0, ""))
        now = self.read(self.file)
        self.assertEqual(self.changed(q, now),
                         [(ANSWER, ANSWER + " Paint the east one, it is new")])
        self.assertEqual(self.read(self.ledger), l)
        self.assertEqual(self.typed(self.n)["typed"], "Paint the east one, it is new")
        code, out, err = self.run_tool("answer", str(self.n), "--other", "The east gate",
                                       "--source", "chat", "--no-entry", "--ledger", self.ledger)
        self.assertEqual(code, 0, out + err)
        self.assertIn("Other: The east gate; the owner's line: Paint the east one, it is new (",
                      self.read(self.file))

    def test_2_a_line_typed_above_does_not_stop_it(self):
        text = self.read(self.file)
        b = self.block(text, self.n)
        self.write(self.file, text.replace(b.text.splitlines()[1],
                                           b.text.splitlines()[1] + "\nThe lane floods.", 1))
        q = self.read(self.file)
        self.assertEqual(self.reply(self.n, "--say", "North, once dry", "--yes")[0], 0)
        self.assertEqual(self.changed(q, self.read(self.file)),
                         [(ANSWER, ANSWER + " North, once dry")])
        self.assertIn("The lane floods.", self.read(self.file))


class Line3Filled(Reply):

    def test_3_text_on_the_answer_line(self):
        self.fill(self.n, ANSWER + " North gate")
        self.refused([self.n, "--pick", "South gate", "--yes"], "answer %d" % self.n)
        self.refused([self.n, "--say", "south", "--yes"], "answer %d" % self.n)

    def test_3_text_under_the_answer_line(self):
        self.fill(self.n, ANSWER, "south, I think")
        self.refused([self.n, "--say", "south", "--yes"], "answer %d" % self.n)


class Line4Refused(Reply):

    def test_4_no_base_line(self):
        text = self.read(self.file)
        b = self.block(text, self.n)
        base = "<!-- decisions: base %s -->\n" % " ".join(b.base)
        self.write(self.file, text.replace(base, "", 1))
        self.refused([self.n, "--pick", "North gate", "--yes"], "base line")

    def test_4_two_base_lines(self):
        text = self.read(self.file)
        b = self.block(text, self.n)
        base = "<!-- decisions: base %s -->\n" % " ".join(b.base)
        self.write(self.file, text.replace(base, base + "\n" + base, 1))
        self.refused([self.n, "--pick", "North gate", "--yes"], "base line")

    def test_4_no_block(self):
        self.refused([99, "--pick", "North gate", "--yes"], "no open question 99")

    def test_4_unknown_label(self):
        self.refused([self.n, "--pick", "East gate", "--yes"],
                     "North gate, South gate, Neither")

    def test_4_ambiguous_label(self):
        text = self.read(self.file)
        self.write(self.file, text.replace("- **Neither.** Paint both.",
                                           "- **North gate..** Paint both.", 1))
        self.assertEqual(self.block(self.read(self.file), self.n).options[2][0], "North gate.")
        self.refused([self.n, "--pick", "*north gate*", "--yes"], "`North gate`, `North gate.`")

    def test_4_say_refusals(self):
        self.refused([self.n, "--say", "   ", "--yes"], "empty")
        self.refused([self.n, "--say", "north\nsouth", "--yes"], "newline")
        self.refused([self.n, "--say", "north south", "--yes"], "newline")
        self.refused([self.n, "--say", "north\tsouth", "--yes"], "control character")
        self.refused([self.n, "--say", "é" * 1001, "--yes"], "2,000 bytes")
        self.assertEqual(self.reply(self.n, "--say", "é" * 1000, "--yes")[0], 0)

    def test_4_a_lint_problem_in_the_block(self):
        text = self.read(self.file)
        self.write(self.file, text.replace("- **Neither.** Paint both.\n", "", 1)
                   .replace("- **South gate.** Faces the pond.\n", "", 1))
        self.refused([self.n, "--say", "north", "--yes"], "options under the third label")

    def test_4_neither_or_both_is_usage(self):
        q = self.read(self.file)
        self.assertEqual(self.reply(self.n, "--yes")[0], 2)
        self.assertEqual(self.reply(self.n, "--pick", "North gate", "--say", "x", "--yes")[0], 2)
        self.assertEqual(self.read(self.file), q)

    def test_4_no_questions_file(self):
        os.remove(self.file)
        code, out, err = self.reply(self.n, "--say", "north", "--yes")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("question %d" % self.n, err)
        self.assertIn("OPEN-QUESTIONS.md", err)
        self.assertFalse(os.path.exists(self.file))


class Line5Lock(Reply):

    def test_5_a_held_lock_refuses_as_new_does(self):
        lock = os.path.join(self.pear, ".new.lock")
        fd = os.open(lock, os.O_CREAT | os.O_RDWR, 0o644)
        self.addCleanup(os.close, fd)
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.write(fd, b"4242\n")
        q = self.read(self.file)
        with mock.patch.object(ask, "NEW_WAIT", 0.2):
            code, out, err = self.reply(self.n, "--pick", "North gate", "--yes")
            new = self.run_tool("new", "--title", "One more", "--stands", "S.", "--choice",
                                "C?", "--option", "A: a.", "--option", "B: b.", "--recommend",
                                "A.", "--ledger", self.ledger)
        self.assertEqual((code, out), (1, ""))
        held = ".new.lock is held by pid 4242"
        self.assertIn(held, err)
        self.assertIn(held, new[2])
        self.assertEqual(self.read(self.file), q)

    def test_5_a_stand_in_for_ask_holding_its_render(self):
        lock = os.path.join(self.pear, ".new.lock")
        holder = subprocess.Popen([sys.executable, "-c", HOLD, lock], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE)
        self.addCleanup(holder.wait)
        self.addCleanup(holder.stdin.close)
        self.addCleanup(holder.stdout.close)
        self.assertEqual(holder.stdout.readline().strip(), b"held")
        q = self.read(self.file)
        with mock.patch.object(ask, "NEW_WAIT", 0.2):
            code, out, err = self.reply(self.n, "--say", "north", "--yes")
        self.assertEqual((code, out), (1, ""))
        self.assertIn(".new.lock is held by pid", err)
        self.assertEqual(self.read(self.file), q)

    def test_5_no_lock_is_left(self):
        self.assertEqual(self.reply(self.n, "--say", "north", "--yes")[0], 0)
        self.assertFalse(os.path.exists(os.path.join(self.pear, ".new.lock")))


class Line6Ask(Reply):

    def test_6_dry_run(self):
        q = self.read(self.file)
        code, out, err = self.reply(self.n, "--pick", "south gate", "--dry-run")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("- %s\n" % ANSWER, out)
        self.assertIn("+ %s South gate\n" % ANSWER, out)
        self.assertIn("nothing written", out)
        self.assertEqual(self.read(self.file), q)
        self.assertFalse(os.path.exists(os.path.join(self.pear, ".new.lock")))

    def test_6_no_terminal_and_no_yes(self):
        self.refused([self.n, "--say", "north"], "--yes")

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

    def test_6_on_a_terminal_n_writes_nothing(self):
        q = self.read(self.file)
        code, out, err = self.pty(b"n\n")
        self.assertEqual(code, 1, out + err)
        self.assertIn("+ %s north\n" % ANSWER, out)
        self.assertIn("[y/N]", err)
        self.assertIn("declined", err)
        self.assertEqual(self.read(self.file), q)

    def test_6_on_a_terminal_y_writes(self):
        q = self.read(self.file)
        code, out, err = self.pty(b"y\n")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.changed(q, self.read(self.file)), [(ANSWER, ANSWER + " north")])
        self.assertIn("your answer is on its line", out)
