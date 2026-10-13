"""`render` (A5, A6): the block between the markers, a stale block replaced in
place, the block appended when the markers are absent, `--check` writing
nothing, and the lint first in every mode."""

import hashlib
import io
import os
import shutil
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
                % (BEGIN, self.line("1. "), self.line("2. "), END))


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
