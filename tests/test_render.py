"""`render` (A5, A6): the block between the markers, a stale block replaced in
place, the block appended when the markers are absent, `--check` writing
nothing, and the lint first in every mode."""

import hashlib
import io
import os
import shutil
import subprocess
import tempfile

import decisions
from decisions.render import BEGIN, END
from tests.hermetic import SAMPLE, Hermetic


def sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


class Base(Hermetic):

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.ledger = os.path.join(self.tmp, "DECISIONS.md")
        self.target = os.path.join(self.tmp, "CLAUDE.md")
        shutil.copy(SAMPLE, self.ledger)
        with open(self.ledger, encoding="utf-8") as handle:
            self.lines = handle.read().splitlines()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["render"] + list(argv) + ["--ledger", self.ledger],
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def read(self, path=None):
        with open(path or self.target, encoding="utf-8") as handle:
            return handle.read()

    def write(self, text, path=None):
        with open(path or self.target, "w", encoding="utf-8") as handle:
            handle.write(text)

    def line(self, prefix):
        return next(line for line in self.lines if line.startswith(prefix))

    def block(self):
        return ("%s\nGenerated from `DECISIONS.md` by `decisions render`; edit the ledger and "
                "rerun it, never this block.\n\n%s\n%s\n\nThe other entries in force, one line "
                "each; `decisions show N` reads one.\n\n- 3 One interpreter (Build)\n"
                "- 4 Tests first (Build)\n- 5 Make is the gate (Build tools)\n"
                "- 7 Releases follow the manifest (Release)\n%s\n"
                % (BEGIN, self.short("1. "), self.short("2. "), END))

    def short(self, prefix):
        """d29 act 4: the block cuts an Every session tail to its first date."""
        return self.line(prefix).replace("; the sample)", ")")


class Render(Base):

    def test_the_block_between_the_markers(self):
        self.write("# Contract\n\nBefore.\n\n%s\nold\n%s\n\nAfter.\n" % (BEGIN, END))
        code, out, err = self.run_cli()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(), "# Contract\n\nBefore.\n\n" + self.block() + "\nAfter.\n")
        self.assertIn("render: wrote CLAUDE.md", out.replace(self.tmp + os.sep, ""))

    def test_proposed_and_superseded_stay_out(self):
        self.run_cli()
        text = self.read()
        for absent in ("A second interpreter", "separate files", "old gate"):
            self.assertNotIn(absent, text)

    def test_a_stale_block_is_replaced_in_place_and_a_rerun_is_fresh(self):
        self.write("Head.\n\n%s\n%s\nTail.\n" % (BEGIN, END))
        self.run_cli()
        self.assertEqual(self.read(), "Head.\n\n" + self.block() + "Tail.\n")
        before = sha(self.target)
        code, out, _ = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("is fresh", out)
        self.assertEqual(sha(self.target), before)

    def test_absent_markers_append_after_one_blank_line(self):
        self.write("# Contract\n\nText.\n\n\n")
        self.assertEqual(self.run_cli()[0], 0)
        self.assertEqual(self.read(), "# Contract\n\nText.\n\n" + self.block())

    def test_an_absent_target_is_made(self):
        self.assertEqual(self.run_cli()[0], 0)
        self.assertEqual(self.read(), self.block())

    def test_into_another_file_names_the_ledger_whole(self):
        home = os.environ["HOME"]
        repo = os.path.join(home, "code", "portfolio")
        os.makedirs(repo)
        shutil.move(self.ledger, os.path.join(repo, "DECISIONS.md"))
        self.ledger = os.path.join(repo, "DECISIONS.md")
        elsewhere = os.path.join(home, ".claude", "CLAUDE.md")
        os.makedirs(os.path.dirname(elsewhere))
        code, _, err = self.run_cli("--into", elsewhere)
        self.assertEqual(code, 0, err)
        text = self.read(elsewhere)
        self.assertEqual(text.splitlines()[1],
                         "Generated from `~/code/portfolio/DECISIONS.md` by `decisions render "
                         "--ledger ~/code/portfolio/DECISIONS.md --into ~/.claude/CLAUDE.md`; "
                         "edit the ledger and rerun it, never this block.")
        self.assertIn("`decisions show N --ledger ~/code/portfolio/DECISIONS.md` reads one", text)
        self.assertFalse(os.path.exists(os.path.join(repo, "CLAUDE.md")))

    def test_into_a_sibling_file_names_it(self):
        sibling = os.path.join(self.tmp, "AGENTS.md")
        self.assertEqual(self.run_cli("--into", sibling)[0], 0)
        self.assertIn("by `decisions render --into AGENTS.md`;", self.read(sibling))

    def test_malformed_markers_exit_2(self):
        self.write("%s\nno end\n" % BEGIN)
        self.assertEqual(self.run_cli()[0], 2)
        self.write("%s\n%s\n%s\n%s\n" % (BEGIN, END, BEGIN, END))
        self.assertEqual(self.run_cli()[0], 2)

    def test_a_crlf_target_keeps_crlf_outside_the_block(self):
        # F4: the file's own line ends stay outside the block, and the block takes them too
        text = "# Notes\nKeep this.\n\n%s\nold\n%s\n\nAfter.\n" % (BEGIN, END)
        with open(self.target, "wb") as handle:
            handle.write(text.replace("\n", "\r\n").encode("utf-8"))
        code, _, err = self.run_cli()
        self.assertEqual(code, 0, err)
        with open(self.target, "rb") as handle:
            data = handle.read()
        self.assertTrue(data.startswith(b"# Notes\r\nKeep this.\r\n\r\n"), data[:40])
        self.assertTrue(data.endswith(b"\r\n\r\nAfter.\r\n"), data[-40:])
        self.assertEqual(data.count(b"\n"), data.count(b"\r\n"))
        self.assertEqual(data.decode("utf-8").replace("\r\n", "\n"),
                         "# Notes\nKeep this.\n\n" + self.block() + "\nAfter.\n")
        self.assertEqual(self.run_cli("--check")[0], 0)

    def test_a_symlinked_target_stays_a_link(self):
        # F5: the write goes through the link to the file it names
        real = os.path.join(self.tmp, "shared", "CLAUDE.md")
        os.makedirs(os.path.dirname(real))
        self.write("# Shared\n", real)
        os.symlink(real, self.target)
        code, _, err = self.run_cli()
        self.assertEqual(code, 0, err)
        self.assertTrue(os.path.islink(self.target))
        self.assertEqual(os.readlink(self.target), real)
        self.assertEqual(self.read(real), "# Shared\n\n" + self.block())

    def test_into_the_ledger_itself_exits_2(self):
        # F6: the ledger is never a target, by its own path or by a link to it
        before = sha(self.ledger)
        link = os.path.join(self.tmp, "link.md")
        os.symlink(self.ledger, link)
        for into in (self.ledger, link):
            for mode in ([], ["--check"]):
                with self.subTest(into=into, mode=mode):
                    code, out, err = self.run_cli("--into", into, *mode)
                    self.assertEqual((code, out), (2, ""))
                    self.assertIn("the ledger itself", err)
                    self.assertEqual(sha(self.ledger), before)

    def test_into_the_ledger_by_another_name_exits_2(self):
        # B1 (d-n1 review): a hard link to the ledger, or its name in another case on a
        # case-insensitive disk, is the ledger too; the ledger and the link stay intact
        before, inode = sha(self.ledger), os.stat(self.ledger).st_ino
        hard = os.path.join(self.tmp, "hard.md")
        os.link(self.ledger, hard)
        names = [hard]
        other_case = os.path.join(self.tmp, "decisions.md")
        if os.path.exists(other_case):
            names.append(other_case)
        for into in names:
            with self.subTest(into=os.path.basename(into)):
                code, out, err = self.run_cli("--into", into)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("the ledger itself", err)
                self.assertEqual(sha(self.ledger), before)
                self.assertEqual(os.stat(hard).st_ino, inode)


class Check(Base):
    """A6: the diff, exit 1 stale and 0 fresh, and the file's hash unchanged."""

    def test_stale_prints_the_diff_exits_1_and_writes_nothing(self):
        self.write("Head.\n\n%s\nold line\n%s\n" % (BEGIN, END))
        before = sha(self.target)
        code, out, _ = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("-old line\n", out)
        self.assertIn("+- 3 One interpreter (Build)\n", out)
        self.assertIn("CLAUDE.md (rendered)", out)
        self.assertEqual(sha(self.target), before)

    def test_fresh_exits_0_prints_nothing_and_writes_nothing(self):
        self.write("Head.\n\n" + self.block())
        before = sha(self.target)
        self.assertEqual(self.run_cli("--check")[:2], (0, ""))
        self.assertEqual(sha(self.target), before)

    def test_absent_markers_or_target_read_stale(self):
        self.write("Head.\n")
        before = sha(self.target)
        self.assertEqual(self.run_cli("--check")[0], 1)
        self.assertEqual(sha(self.target), before)
        os.remove(self.target)
        self.assertEqual(self.run_cli("--check")[0], 1)
        self.assertFalse(os.path.exists(self.target))

    def test_check_and_lint_exclude_each_other(self):
        self.assertEqual(self.run_cli("--check", "--lint")[0], 2)


class LintFirst(Base):
    """A lint problem prints `file:line: message` and exits 1 in every mode."""

    def setUp(self):
        super().setUp()
        with open(self.ledger, "a", encoding="utf-8") as handle:
            handle.write("\n## Notes\n")
        self.write("Head.\n\n%s\nold\n%s\n" % (BEGIN, END))
        self.before = sha(self.target)

    def test_every_mode_exits_1_and_writes_nothing(self):
        want = "%s:%d: unknown section `## Notes`" % (self.ledger, len(self.lines) + 2)
        for mode in ([], ["--check"], ["--lint"]):
            with self.subTest(mode=mode):
                code, out, _ = self.run_cli(*mode)
                self.assertEqual(code, 1)
                self.assertTrue(out.startswith(want), out)
                self.assertEqual(sha(self.target), self.before)

    def test_lint_alone_on_a_clean_ledger(self):
        shutil.copy(SAMPLE, self.ledger)
        self.assertEqual(self.run_cli("--lint")[:2], (0, ""))
        self.assertEqual(sha(self.target), self.before)


# d29 act 4 (audit d2): design/d29-churn.md section 6's three tails.
TAILS = """# Decisions

## In force

### Every session

1. **The gate runs every check.** Every landing runs the full check through the gate queue. (2026-09-21; the owner; amended 2026-10-01, answer 3; amended 2026-10-05, answer 4)
2. **Records are tables.** A record is one table. (2026-10-02; the owner)
4. **A builder never pushes.** The coordinator pushes after a green check. (2026-10-03 and 2026-10-04; the owner; amended 2026-10-06, answer 5)

### The tool

3. **One verb reads git.** The churn view reads git and writes nothing. (2026-11-09; the owner)
"""
SHORT = ("1. **The gate runs every check.** Every landing runs the full check through the gate "
         "queue. (2026-09-21; amended 2 times, see the ledger)\n"
         "2. **Records are tables.** A record is one table. (2026-10-02)\n"
         "4. **A builder never pushes.** The coordinator pushes after a green check. "
         "(2026-10-03; amended once, see the ledger)\n")


class Tails(Base):

    def setUp(self):
        super().setUp()
        self.write(TAILS, self.ledger)
        self.led = decisions.ledger.load(self.ledger)

    def blocks(self):
        return (decisions.render.block(self.led, self.ledger, self.target),
                decisions.render.block(self.led, self.ledger, self.target, tails=True))

    def test_tails_short_in_the_block(self):
        short, whole = self.blocks()
        self.assertIn(SHORT, short)
        self.assertIn("\n- 3 One verb reads git (The tool)\n", short)
        self.assertEqual(len(whole.encode()) - len(short.encode()), 75)
        for line in TAILS.splitlines()[5:8]:
            self.assertIn(line, whole)

    def test_tails_whole_form_checks_fresh(self):
        self.write("# Notes\n\n" + self.blocks()[1])
        before = sha(self.target)
        code, out, err = self.run_cli("--check")
        self.assertEqual((code, out), (0, ""), err)
        self.assertEqual(err, "render: CLAUDE.md carries the entries' whole tails, 75 B more; "
                              "run render to shorten it\n")
        self.assertEqual(sha(self.target), before)

    def test_tails_stale_still_exits_1(self):
        self.write("# Notes\n\n" + self.blocks()[1])
        self.write(TAILS.replace("one table.", "one table, never a list."), self.ledger)
        code, out, _ = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("never a list", out)

    def test_tails_render_rewrites_then_fresh(self):
        self.write("# Notes\n\n" + self.blocks()[1])
        code, out, err = self.run_cli()
        self.assertEqual(code, 0, err)
        self.assertIn("render: wrote", out)
        self.assertIn(SHORT, self.read())
        self.assertEqual(self.run_cli("--check"), (0, "", ""))


# d31, the T2 fixture (F2): entry 1 holds four amendments, two moves and nested parentheticals with
# dates; 3 holds an `amended` decoy in its paragraph and one in a nested parenthetical;
# 5's one amendment names no source; the Superseded line holds two and is no entry in force.
HEAD1 = ("1. **The gate runs every check.** Every landing runs the full check (never a part "
         "of it) through the gate queue. ")
OLD1 = ("(2026-09-21; moved from the old ledger's entry 12, 2026-09-29; the doctrine is "
        "`design/88.md`; amended 2026-09-29, the owner's word, sitting 2026-09-29-1; amended "
        "2026-10-10, the answer to question 1 (recorded 2026-10-10 in the charter); amended "
        "2026-10-13, the owner's word at 14:15; moved back, 2026-10-30; amended 2026-10-31, "
        "the owner's word, design/03 §10 question 2 (see (2026-10-30) there); the default moved)")
NEW1 = ("(2026-09-21; amended 3 times, 2026-09-29 to 2026-10-13; amended 2026-10-31, "
        "the owner's word, design/03 §10 question 2 (see (2026-10-30) there); the default moved)")
HEAD4 = "4. **A builder never pushes.** The coordinator pushes after a green check. "
OLD4 = "(2026-10-03 and 2026-10-04; the owner; amended 2026-10-06, answer 5)"
NEW4 = "(2026-10-03; amended 2026-10-06, answer 5)"
HEAD3 = ("3. **One verb reads git.** The churn view reads git (since 2026-11-09; amended "
         "2026-01-01, a decoy) and writes nothing. ")
OLD3 = ("(2026-11-09; the owner (asked 2026-11-08; amended 2026-11-08, a nested decoy); "
        "amended 2026-11-10, answer 7; amended 2026-11-11, answer 8 (design/04 (2026-11-10)))")
NEW3 = "(2026-11-09; amended once, 2026-11-10; amended 2026-11-11, answer 8 (design/04 (2026-11-10)))"
LINE5 = ("5. **One interpreter.** The tool runs under Python 3.12. (2026-09-03; the sample, "
         "amended 2026-09-10 (twice))")
SHAPE = """# Decisions

## In force

### Every session

%s%s
2. **Records are tables.** A record is one table. (2026-10-02; the owner)
%s%s

### The tool

%s%s
%s

## Superseded

6. The old gate named by hand: replaced by make (entry 1), 2026-09-05 (2026-09-01; the owner; amended 2026-09-02, a; amended 2026-09-03, b).
"""
FIXTURE = SHAPE % (HEAD1, OLD1, HEAD4, OLD4, HEAD3, OLD3, LINE5)
FOLDED = SHAPE % (HEAD1, NEW1, HEAD4, NEW4, HEAD3, NEW3, LINE5)
# What the fold cuts from the Every session tails, entries 1 and 4: the measure.
CUT = len((OLD1 + OLD4).encode()) - len((NEW1 + NEW4).encode())


class T2(Hermetic):

    def setUp(self):
        super().setUp()
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.ledger = os.path.join(self.tmp, "DECISIONS.md")
        self.target = os.path.join(self.tmp, "CLAUDE.md")
        self.write(FIXTURE, self.ledger)
        self.git("init", "-q")
        self.commit()

    def git(self, *argv):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=fixture",
                               "-c", "commit.gpgsign=false"] + list(argv), cwd=self.tmp,
                              check=True, capture_output=True, text=True).stdout

    def commit(self):
        self.git("add", "DECISIONS.md")
        self.git("commit", "-q", "-m", "the ledger")

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["render"] + list(argv) + ["--ledger", self.ledger],
                              out=out, err=err)
        return (code, out.getvalue().replace(self.tmp + os.sep, ""),
                err.getvalue().replace(self.tmp + os.sep, ""))

    def read(self, path=None):
        with open(path or self.ledger, encoding="utf-8") as handle:
            return handle.read()

    def write(self, text, path=None):
        with open(path or self.target, "w", encoding="utf-8") as handle:
            handle.write(text)

    def blocks(self):
        led = decisions.ledger.load(self.ledger)
        return (decisions.render.block(led, self.ledger, self.target),
                decisions.render.block(led, self.ledger, self.target, tails=True))

    def test_t2_lint_reads_the_form(self):
        self.write(FOLDED, self.ledger)
        self.assertEqual(self.run_cli("--lint"), (0, "", ""))

    def test_t2_fold_is_lossless(self):
        code, out, err = self.run_cli("--fold-tails")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(), FOLDED)
        sha = self.git("rev-parse", "--short", "HEAD").strip()
        self.assertIn("render: folded the tails of 3 entries in DECISIONS.md, %d B to %d B; %s "
                      "holds them whole\n" % (len(FIXTURE.encode()), len(FOLDED.encode()), sha),
                      out)
        # what the form keeps, entry by entry: the line up to its tail, the first date,
        # the count, and the latest amendment to the tail's end
        final, led = decisions.ledger.final_parenthetical, decisions.ledger
        old, new = led.parse(FIXTURE).entries, led.parse(self.read()).entries
        self.assertEqual(len(old), len(new))
        for a, b in zip(old, new):
            if a.section != led.IN_FORCE:
                self.assertEqual(a.text, b.text)
                continue
            before, after = final(a.body), final(b.body)
            self.assertEqual(a.text[:-(len(before) + 2)], b.text[:-(len(after) + 2)])
            self.assertEqual(before[:10], after[:10])
            self.assertEqual(led.amended(before), led.amended(after))
            dated = led.amendments(before)[1]
            if dated:
                self.assertTrue(after.endswith(before[dated[-1][0] + 1:]), a.number)
        self.assertEqual([led.amended(final(e.body)) for e in new[:5]], [4, 0, 1, 2, 1])
        # what it cuts, git holds: HEAD's ledger is the fixture, every tail whole
        self.assertEqual(self.git("show", "HEAD:DECISIONS.md"), FIXTURE)

    def test_t2_fold_is_idempotent(self):
        self.assertEqual(self.run_cli("--fold-tails")[0], 0)
        once = self.read()
        # again at once, the fold uncommitted: nothing to cut, so nothing to refuse
        code, out, err = self.run_cli("--fold-tails")
        self.assertEqual(code, 0, err)
        self.assertIn("render: no tail to fold in DECISIONS.md\n", out)
        self.assertEqual(self.read(), once)
        self.commit()
        self.assertEqual(self.run_cli("--fold-tails")[0], 0)
        self.assertEqual(self.read(), once)
        self.assertEqual(self.git("status", "--porcelain", "--", "DECISIONS.md"), "")

    def test_t2_fold_keeps_nested_parentheses_and_dates(self):
        code, out, err = self.run_cli("--fold-tails")
        self.assertEqual(code, 0, err)
        lines = self.read().splitlines()
        self.assertIn(HEAD1 + NEW1, lines)
        self.assertIn(HEAD3 + NEW3, lines)
        # an amendment that names no source keeps its tail, and stderr says so
        self.assertIn(LINE5, lines)
        self.assertEqual(err, "render: entry 5's latest amendment names no source, so its tail "
                              "stays as it stands\n")
        for entry in decisions.ledger.parse(self.read()).entries:
            self.assertFalse(decisions.ledger.unclosed(entry.body), entry.number)
        self.assertEqual(self.run_cli("--lint"), (0, "", ""))

    def test_t2_fold_then_check_passes(self):
        self.write("# Contract\n\n%s\nold\n%s\n" % (BEGIN, END))
        self.assertEqual(self.run_cli()[0], 0)
        code, out, err = self.run_cli("--fold-tails")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.run_cli("--check")[:2], (0, ""))
        self.assertEqual(self.run_cli("--lint"), (0, "", ""))

    def test_t2_block_keeps_its_count(self):
        short, whole = self.blocks()
        self.write(FOLDED, self.ledger)
        short_after, whole_after = self.blocks()
        # d29's short block reads the same count from a T2 tail: a fold moves no byte of it
        self.assertIn("gate queue. (2026-09-21; amended 4 times, see the ledger)\n", short_after)
        self.assertEqual(short_after, short)
        # the whole-tail form, a block rendered before 0.14.0, loses what the tails lost
        self.assertEqual(len(whole.encode()) - len(whole_after.encode()), CUT)
        self.assertEqual(CUT, 279)

    def test_t2_fold_refuses_what_head_does_not_hold(self):
        changed = FIXTURE.replace("one table.", "one table, never a list.")
        self.write(changed, self.ledger)
        code, out, err = self.run_cli("--fold-tails")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("HEAD does not hold DECISIONS.md as it stands; commit it first; "
                      "nothing written", err)
        self.assertEqual(self.read(), changed)
        # no git at all: the same refusal
        shutil.rmtree(os.path.join(self.tmp, ".git"))
        self.assertEqual(self.run_cli("--fold-tails")[0], 2)
        self.assertEqual(self.read(), changed)

    def assert_refused(self):
        before = self.read()
        code, out, err = self.run_cli("--fold-tails")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("HEAD does not hold", err)
        self.assertEqual(self.read(), before)

    def test_fold_refuses_an_untracked_ledger_git_does_not_list(self):
        # status.showUntrackedFiles=no empties `git status` for a file HEAD lacks
        self.git("rm", "-q", "--cached", "DECISIONS.md")
        self.git("commit", "-q", "-m", "untrack")
        self.git("config", "status.showUntrackedFiles", "no")
        self.assert_refused()

    def test_fold_refuses_a_changed_ledger_named_in_another_case(self):
        self.write(FIXTURE.replace("one table.", "one table, never a list."), self.ledger)
        self.ledger = os.path.join(self.tmp, "decisions.md")
        if not os.path.exists(self.ledger):
            self.skipTest("a case-sensitive disk")
        self.assert_refused()

    def test_fold_refuses_through_a_tracked_link(self):
        real = os.path.join(self.tmp, "real")
        os.mkdir(real)
        os.rename(self.ledger, os.path.join(real, "DECISIONS.md"))
        os.symlink(os.path.join("real", "DECISIONS.md"), self.ledger)
        self.git("add", "-A", "DECISIONS.md")
        self.git("commit", "-q", "-m", "the link")
        self.assert_refused()

    def test_fold_refuses_a_ledger_git_is_told_not_to_look_at(self):
        changed = FIXTURE.replace("one table.", "one table, never a list.")
        for flag in ("--assume-unchanged", "--skip-worktree"):
            self.git("update-index", flag, "DECISIONS.md")
            self.write(changed, self.ledger)
            self.assert_refused()
            self.git("update-index", flag.replace("--", "--no-"), "DECISIONS.md")
            self.git("checkout", "--", "DECISIONS.md")

    def test_fold_writes_nothing_for_a_refused_target(self):
        for into, why in ((self.ledger, "is the ledger itself"),
                          (self.target, "GENERATED markers are not one BEGIN")):
            if into == self.target:
                self.write("%s\nno end\n" % BEGIN)
            code, out, err = self.run_cli("--fold-tails", "--into", into)
            self.assertEqual((code, out), (2, ""))
            self.assertIn(why, err)
            self.assertEqual(self.read(), FIXTURE)
