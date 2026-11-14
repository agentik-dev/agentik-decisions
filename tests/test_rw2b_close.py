"""rw2b (agentik-hq design/16 section 4 items 6 and 7): `rows close ROW` writes a pushed row's
`done` cell and its line in the home's done file, both or neither; `--withdrawn WHY` gives a
row up; and the read shows what a cut builder's charter left. The home `depot`, its member
`agentik-crate` and every row are made here under the temp folder, with made-up names."""

import io
import os
from unittest import mock

import decisions
from decisions import ask, rows as rows_module
from decisions.rows import KEYS
from tests.test_d39_backlog_check import DATE, commit, git
from tests.test_rw2_rows import Rows

GO = "go with close"


class TTY(io.StringIO):
    """A stderr that says it is a terminal."""

    def isatty(self):
        return True


class Stdin(object):
    """A stdin that is a terminal and answers `line`, or raises it when it is an exception."""

    def __init__(self, line):
        self.line = line

    def isatty(self):
        return True

    def readline(self):
        if isinstance(self.line, BaseException):
            raise self.line
        return self.line


class Depot(Rows):
    """The home `depot` holds `history/rows`; `agentik-crate` beside it holds the branches."""

    def setUp(self):
        super().setUp()
        self.hq = os.path.join(self.tmp, "depot")
        self.pear = os.path.join(self.tmp, "agentik-crate")
        for repo in (self.hq, self.pear):
            os.makedirs(repo)
            git(repo, "init", "-q")
            commit(repo, "start.txt")
        self.root = os.path.join(self.hq, "history", "rows")
        os.makedirs(self.root)
        self.done = os.path.join(os.path.realpath(self.hq), "history", "handoff-done.md")

    def crate(self, name, **kw):
        kw.setdefault("repo", "crate")
        self.row(name, **kw)

    def path(self, name):
        return os.path.join(os.path.realpath(self.root), name, "row.md")

    def text(self, name):
        with open(self.path(name), encoding="utf-8", newline="") as handle:
            return handle.read()

    def pushed(self, name, owed=("- [x] its line in the done file",), push=True, **kw):
        """A row of `name` built, merged `--no-ff` into main and, with `push`, pushed."""
        tip = self.on_branch(name, name + "-1.txt")
        self.crate(name, owed=owed, **kw)
        self.build(name, 1, tip)
        git(self.pear, "merge", "-q", "--no-ff", "-m", "Merge %s: the crate" % name, name)
        if push:
            git(self.pear, "update-ref", "refs/remotes/origin/main", "main")
        return "%s %s" % (DATE, git(self.pear, "rev-parse", "main")[:7])

    def close(self, *argv, err=None):
        """(exit, stdout, stderr) of `rows --root ROOT ARGV...`, ARGV in the order given."""
        out, err = io.StringIO(), err if err is not None else io.StringIO()
        code = decisions.main(["rows", "--root", self.root] + list(argv), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def snapshot(self, *names):
        found = [self.text(n) for n in names]
        if os.path.exists(self.done):
            with open(self.done, "rb") as handle:
                found.append(handle.read())
        else:
            found.append(None)
        return found

    def lines(self, name, cell, line=None):
        first = "rows close %s: %s: done %s" % (name, self.path(name), cell)
        if line is None:
            return [first]
        return [first, "rows close %s: %s: %s" % (name, self.done, line)]


class Close(Depot):
    """Acceptance 1 and 2: `-y` writes both; `--dry-run`, with or without `-y`, writes none."""

    def test_close_y_writes_the_cell_and_the_done_line(self):
        cell = self.pushed("p1-crate")
        before = self.text("p1-crate")
        self.assertIn("p1-crate", self.view())
        line = "p1-crate: a made-up row, done %s" % cell
        code, out, err = self.close("close", "p1-crate", "-y")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out.splitlines(), self.lines("p1-crate", cell, line)
                         + ["rows close: p1-crate closed"])
        self.assertEqual(self.text("p1-crate"),
                         before.replace("| done |  |\n", "| done | %s |\n" % cell))
        with open(self.done, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), line + "\n")
        self.assertNotIn("p1-crate", self.view())

    def test_words_and_options_in_any_order(self):
        cell = self.pushed("p1-crate")
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["rows", "--yes", "close", "--root", self.root, "p1-crate"],
                              out=out, err=err)
        self.assertEqual(code, 0, err.getvalue())
        self.assertEqual(out.getvalue().splitlines()[-1], "rows close: p1-crate closed")
        self.assertIn("| done | %s |" % cell, self.text("p1-crate"))

    def test_dry_run_writes_nothing(self):
        cell = self.pushed("p1-crate")
        line = "p1-crate: a made-up row, done %s" % cell
        before = self.snapshot("p1-crate")
        for argv in (["close", "p1-crate", "--dry-run"], ["--dry-run", "close", "p1-crate", "-y"]):
            code, out, err = self.close(*argv)
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(out.splitlines(), self.lines("p1-crate", cell, line)
                             + ["rows close: dry run, nothing written"])
            self.assertEqual(self.snapshot("p1-crate"), before)

    def test_repo_named_by_its_checkout(self):
        cell = self.pushed("p1-crate", repo="crate-elsewhere")
        code, _, err = self.close("close", "p1-crate", "-y")
        self.assertEqual(code, 2)
        self.assertEqual(err, "decisions: rows close: p1-crate's repo is not found (absent); "
                              "name its checkout with --repo DIR\n")
        code, out, err = self.close("close", "p1-crate", "--repo", self.pear, "-y")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("| done | %s |" % cell, self.text("p1-crate"))


class Refused(Depot):
    """Acceptance 3: each refusal of R1 to R4 by its words, exit 2, both files' bytes kept."""

    def refused(self, argv, message, names=("p1-crate",)):
        before = self.snapshot(*names)
        code, out, err = self.close(*argv)
        self.assertEqual((code, out, err), (2, "", "decisions: %s\n" % message))
        self.assertEqual(self.snapshot(*names), before)

    def test_r1_the_form(self):
        self.pushed("p1-crate")
        self.pushed("p2-crate")
        self.refused(["close"], "rows close: name one row")
        self.refused(["close", "p1-crate", "p2-crate"], "rows close: one row a call")
        self.refused(["close", "p1-crate", "--json"], "rows close takes no --json")
        rule = "rows: --withdrawn, --repo, --dry-run and -y go with close"
        for argv in (["--dry-run"], ["-y"], ["check", "--yes"], ["--repo", self.pear],
                     ["--withdrawn", "gone"]):
            self.refused(argv, rule)
        why = "rows close: --withdrawn takes one line of words with no | in it"
        for text in ("", "   ", "one | two", "one\ntwo", "one\rtwo"):
            self.refused(["close", "p1-crate", "--withdrawn", text, "-y"], why)

    def test_r2_the_row(self):
        self.pushed("p1-crate")
        root = os.path.realpath(self.root)
        self.refused(["close", "p0-crate", "-y"], "rows close: no row p0-crate under %s" % root)
        for name in ("p1|crate", "../depot", "p1\x1b[2Jcrate", ".hidden"):
            self.refused(["close", name, "-y"], "rows close: no such row under %s" % root)
        self.put(os.path.join(self.root, "p3-crate", "row.md"),
                 "# Row p3-crate: no done\n\n| item | value |\n|---|---|\n| repo | crate |\n\n"
                 "| done | 2026-11-01 abc1234 |\n")
        self.refused(["close", "p3-crate", "-y"], "rows close: %s has no done cell; nothing "
                     "written" % self.path("p3-crate"), names=("p1-crate", "p3-crate"))

    def test_r3_the_repo(self):
        self.pushed("p1-crate", repo="plum")
        self.refused(["close", "p1-crate", "-y"], "rows close: p1-crate's repo is not found "
                     "(absent); name its checkout with --repo DIR")
        plain = os.path.join(self.tmp, "plain")
        os.makedirs(plain)
        self.refused(["close", "p1-crate", "--repo", plain, "-y"],
                     "rows close: --repo %s is no checkout with a main" % plain)

    def test_r4_when_it_closes(self):
        self.pushed("p1-crate", push=False)
        self.refused(["close", "p1-crate", "-y"],
                     "rows close: p1-crate is landed, not pushed; nothing written")
        self.on_branch("p2-crate", "p2-1.txt")
        self.crate("p2-crate")
        self.refused(["close", "p2-crate", "-y"],
                     "rows close: p2-crate is building, not pushed; nothing written",
                     names=("p2-crate",))
        self.crate("p3-crate")
        self.refused(["close", "p3-crate", "-y"],
                     "rows close: p3-crate is briefed, not pushed; nothing written",
                     names=("p3-crate",))
        self.crate("p4-crate", depends="p3-crate")
        self.refused(["close", "p4-crate", "-y"],
                     "rows close: p4-crate is waits, not pushed; nothing written",
                     names=("p4-crate",))
        self.pushed("p5-crate", owed=("- [ ] the install", "- [x] the push", "- [ ] the line"))
        self.refused(["close", "p5-crate", "-y"],
                     "rows close: p5-crate has 2 open under ## Owed; nothing written",
                     names=("p5-crate",))


class DoneFile(Depot):
    """Acceptance 4: the done file made, a bullet after a bullet, a sha held, another title."""

    def test_a_bullet_after_a_bullet(self):
        cell = self.pushed("p1-crate")
        self.put(self.done, "# Done\n\n- 7 an older row, done 2026-10-01 abc1234\n\n")
        code, out, _ = self.close("close", "p1-crate", "-y")
        self.assertEqual(code, 0)
        line = "- p1-crate: a made-up row, done %s" % cell
        self.assertEqual(out.splitlines()[1], "rows close p1-crate: %s: %s" % (self.done, line))
        with open(self.done, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "# Done\n\n- 7 an older row, done 2026-10-01 "
                             "abc1234\n\n" + line + "\n")

    def test_a_file_with_no_last_newline(self):
        cell = self.pushed("p1-crate")
        self.put(self.done, "7 an older row, done 2026-10-01 abc1234")
        self.assertEqual(self.close("close", "p1-crate", "-y")[0], 0)
        with open(self.done, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "7 an older row, done 2026-10-01 abc1234\n"
                             "p1-crate: a made-up row, done %s\n" % cell)

    def test_a_sha_held_adds_no_line(self):
        cell = self.pushed("p1-crate")
        sha7 = cell.split()[1]
        held = "- 75 the crate's row, done %s `%s` (by hand)\n" % (DATE, sha7)
        self.put(self.done, held)
        before = self.text("p1-crate")
        code, out, _ = self.close("close", "p1-crate", "-y")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            "rows close p1-crate: %s: done %s" % (self.path("p1-crate"), cell),
            "rows close p1-crate: %s: holds %s already, no line" % (self.done, sha7),
            "rows close: p1-crate closed"])
        with open(self.done, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), held)
        self.assertEqual(self.text("p1-crate"),
                         before.replace("| done |  |\n", "| done | %s |\n" % cell))

    def test_a_first_line_of_another_shape(self):
        cell = self.pushed("p1-crate")
        self.put(self.path("p1-crate"), self.text("p1-crate").replace(
            "# Row p1-crate: a made-up row", "# The crate's row"))
        code, out, _ = self.close("close", "p1-crate", "-y")
        self.assertEqual(code, 0)
        with open(self.done, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "p1-crate, done %s\n" % cell)

    def test_crlf_and_every_other_byte_kept(self):
        cell = self.pushed("p1-crate")
        text = self.text("p1-crate").replace("\n", "\r\n")
        text = text.replace("| done |  |", "|  Done | `` |   ")
        self.put(self.path("p1-crate"), text)
        self.assertEqual(self.close("close", "p1-crate", "-y")[0], 0)
        self.assertEqual(self.text("p1-crate"),
                         text.replace("|  Done | `` |   \r\n", "| done | %s |\r\n" % cell))


class Withdrawn(Depot):
    """Acceptance 5: `--withdrawn WHY` on any open row; the read then skips the folder."""

    def test_withdrawn_on_a_building_row_that_owes(self):
        self.on_branch("p2-crate", "p2-1.txt")
        self.crate("p2-crate", owed=("- [ ] the tests", "- [ ] the gate"))
        before = self.text("p2-crate")
        cell = "withdrawn %s: superseded by p9" % ask.today()
        code, out, err = self.close("close", "p2-crate", "--withdrawn", "superseded by p9", "-y")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out.splitlines(), self.lines("p2-crate", cell)
                         + ["rows close: p2-crate withdrawn"])
        self.assertEqual(self.text("p2-crate"),
                         before.replace("| done |  |\n", "| done | %s |\n" % cell))
        self.assertFalse(os.path.exists(self.done))
        self.assertNotIn("p2-crate", self.view())
        git(self.pear, "branch", "-q", "-D", "p2-crate")
        code, out = self.checked()
        self.assertEqual((code, out), (0, "checked 0 rows under %s: 0 stale\n"
                                       % os.path.realpath(self.root)))

    def test_withdrawn_reads_no_repo(self):
        self.crate("p2-crate", repo="plum")
        code, out, _ = self.close("close", "p2-crate", "--withdrawn", "the plum is gone",
                                  "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[-1], "rows close: dry run, nothing written")


class Asked(Depot):
    """Acceptance 6: with neither flag, the question at a terminal, and none elsewhere."""

    def test_no_terminal_writes_nothing(self):
        cell = self.pushed("p1-crate")
        before = self.snapshot("p1-crate")
        code, out, err = self.close("close", "p1-crate")
        self.assertEqual(code, 2)
        self.assertEqual(out.splitlines(), self.lines(
            "p1-crate", cell, "p1-crate: a made-up row, done %s" % cell))
        self.assertEqual(err, "decisions: rows close: nothing written, since it cannot ask "
                              "here; run it again with -y\n")
        self.assertEqual(self.snapshot("p1-crate"), before)

    def test_the_question_held_with_no_pty(self):
        question = "Write this? y for yes, n or Enter for no. "
        for line, want in (("y\n", True), ("YES\n", True), (" Yes \n", True), ("\n", False),
                           ("n\n", False), ("", False), (EOFError(), False),
                           (KeyboardInterrupt(), False)):
            err = io.StringIO()
            got = rows_module.asked(True, True, Stdin(line).readline, err)
            self.assertEqual(got, want, repr(line))
            self.assertTrue(err.getvalue().startswith(question), repr(line))
        for ttys in ((False, True), (True, False), (False, False)):
            err = io.StringIO()
            self.assertIsNone(rows_module.asked(ttys[0], ttys[1], Stdin("y\n").readline, err))
            self.assertEqual(err.getvalue(), "")

    def test_the_question_at_a_terminal(self):
        cell = self.pushed("p1-crate")
        before = self.snapshot("p1-crate")
        with mock.patch.object(rows_module.sys, "stdin", Stdin("\n")):
            code, out, err = self.close("close", "p1-crate", err=TTY())
        self.assertEqual(code, 2)
        self.assertEqual(err, "Write this? y for yes, n or Enter for no. "
                              "decisions: rows close: declined, nothing written\n")
        self.assertEqual(self.snapshot("p1-crate"), before)
        with mock.patch.object(rows_module.sys, "stdin", Stdin("y\n")):
            code, out, err = self.close("close", "p1-crate", err=TTY())
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines()[-1], "rows close: p1-crate closed")
        self.assertIn("| done | %s |" % cell, self.text("p1-crate"))


class BothOrNeither(Depot):
    """Acceptance 7: a write that fails on the done file leaves row.md's bytes."""

    def test_a_failed_replace_of_the_done_file(self):
        self.pushed("p1-crate")
        before = self.snapshot("p1-crate")
        real = os.replace

        def failing(src, dst, *args, **kwargs):
            if os.path.realpath(dst) == os.path.realpath(self.done):
                raise OSError("the disk is full")
            return real(src, dst, *args, **kwargs)

        with mock.patch("os.replace", failing):
            code, out, err = self.close("close", "p1-crate", "-y")
        self.assertEqual(code, 2)
        self.assertIn("unwritable", err)
        self.assertNotIn("closed", out)
        self.assertEqual(self.snapshot("p1-crate"), before)
        self.assertEqual(sorted(os.listdir(os.path.dirname(self.done))), ["rows"])

    def test_a_done_file_that_cannot_be_read(self):
        self.pushed("p1-crate")
        os.makedirs(self.done)
        before = self.text("p1-crate")
        code, _, err = self.close("close", "p1-crate", "-y")
        self.assertEqual(code, 2)
        self.assertIn("unreadable", err)
        self.assertEqual(self.text("p1-crate"), before)


class Already(Depot):
    """Acceptance 8: a closed or withdrawn row is closed already; a contradiction blocks
    nothing."""

    def test_closed_and_withdrawn_rows(self):
        for name, cell in (("p1-crate", "2026-11-01 abc1234"),
                           ("p2-crate", "withdrawn 2026-11-01: the owner chose another way"),
                           ("p3-crate", "landed, pushed " + "and more words " * 8)):
            self.crate(name, done=cell)
            before = self.snapshot(name)
            code, out, err = self.close("close", name, "-y")
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(out, "rows close: %s is closed already: %s\n" % (name, cell[:80]))
            self.assertEqual(self.snapshot(name), before)

    def test_a_contradiction_prints_and_closes(self):
        side = self.on_branch("side", "side.txt")
        cell = self.pushed("p1-crate")
        self.build("p1-crate", 2, side[:7], stage="fix of review 1")
        code, out, err = self.close("close", "p1-crate", "-y")
        self.assertEqual(code, 0)
        self.assertEqual(err, "rows close p1-crate: stale: head %s of build-2.md is not on "
                              "p1-crate\n" % side[:7])
        self.assertIn("| done | %s |" % cell, self.text("p1-crate"))


CHARTER = """# Sitting {name}: a made-up sitting

| item | value |
|---|---|
| goal | the crate |

## Done-ness
- [x] the packet
{unchecked}
## Handover
- decide, owner: none
{next_act}"""


class Cut(Depot):
    """Acceptance 9: a cut builder's charter, commits and loose paths, from the branch."""

    def charter(self, tree, name, unchecked=(), next_act=None):
        path = os.path.join(tree, "history", "sittings", name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        act = "" if next_act is None else "\n## Next act\n\n%s\n" % next_act
        self.put(path, CHARTER.format(name=name, unchecked="".join(u + "\n" for u in unchecked),
                                      next_act=act))
        git(tree, "add", path)
        git(tree, "commit", "-q", "-m", "the charter " + name)

    def tree_of(self, branch):
        tree = os.path.join(self.tmp, "crate-" + branch)
        git(self.pear, "worktree", "add", "-q", "-b", branch, tree, "main")
        return tree

    def text_of(self, name):
        code, out, _ = self.rows()
        self.assertEqual(code, 0)
        lines = out.splitlines()
        at = next(i for i, l in enumerate(lines) if l.startswith(name + "  "))
        got = [lines[at]]
        for line in lines[at + 1:]:
            if not line.startswith("  "):
                break
            got.append(line)
        return got

    def test_a_building_row_with_two_charters(self):
        tree = self.tree_of("p5-crate")
        act = "write the tests of acceptance 9, then the read of the charter " + "x" * 60
        self.charter(tree, "2026-11-14-9.md", unchecked=("- [ ] the old one",),
                     next_act="the old act")
        self.charter(tree, "2026-11-14-14-p5.md", unchecked=("- [ ] the tests", "- [ ] the gate"),
                     next_act=act)
        for n in (1, 2, 3):
            commit(tree, "p5-%d.txt" % n)
        self.put(os.path.join(tree, "history", "sittings", "2026-11-14-14-p5.md"), "changed\n")
        for n in (1, 2, 3):
            self.put(os.path.join(tree, "loose-%d.txt" % n), "loose\n")
        self.crate("p5-crate")
        got = self.view()["p5-crate"]
        self.assertEqual(tuple(got), KEYS)
        self.assertEqual((got["state"], got["past"], got["dirty"]), ("building", 5, 4))
        cut = got["cut"]
        self.assertEqual(sorted(cut), ["charter", "commits", "next_act", "paths", "unchecked"])
        self.assertEqual(cut["charter"], "history/sittings/2026-11-14-14-p5.md")
        self.assertEqual(cut["unchecked"], ["- [ ] the tests", "- [ ] the gate"])
        self.assertEqual(cut["next_act"], act[:100])
        log = git(self.pear, "log", "--format=%H %s", "main..p5-crate").splitlines()
        self.assertEqual([c["sha"] + " " + c["subject"] for c in cut["commits"]], log)
        self.assertEqual(cut["paths"], ["history/sittings/2026-11-14-14-p5.md", "loose-1.txt",
                                        "loose-2.txt", "loose-3.txt"])
        line = self.text_of("p5-crate")
        self.assertEqual(line[1:], [
            "  charter history/sittings/2026-11-14-14-p5.md: 2 unchecked; next act: %s"
            % act[:100]] + ["  past: %s" % l[:7] + l[40:] for l in log[:3]] + [
            "  past: and 2 more",
            "  dirty: history/sittings/2026-11-14-14-p5.md, loose-1.txt, loose-2.txt and 1 more"])

    def test_a_charter_merged_in_from_main_is_not_read(self):
        tree = self.tree_of("p6-crate")
        self.charter(tree, "2026-11-14-2.md", unchecked=("- [ ] the tests",))
        main_tree = os.path.join(self.tmp, "crate-main")
        git(self.pear, "worktree", "add", "-q", "--detach", main_tree, "main")
        self.charter(main_tree, "2026-11-15-1.md", unchecked=("- [ ] main's", "- [ ] own"),
                     next_act="main's act")
        git(self.pear, "update-ref", "refs/heads/main", git(main_tree, "rev-parse", "HEAD"))
        git(tree, "merge", "-q", "--no-ff", "-m", "Merge main into p6-crate", "main")
        self.crate("p6-crate")
        cut = self.view()["p6-crate"]["cut"]
        self.assertEqual(cut["charter"], "history/sittings/2026-11-14-2.md")
        self.assertEqual((cut["unchecked"], cut["next_act"]), (["- [ ] the tests"], None))
        self.assertEqual(self.text_of("p6-crate")[1],
                         "  charter history/sittings/2026-11-14-2.md: 1 unchecked; next act: none")

    def test_no_charter(self):
        self.on_branch("p7-crate", "p7-1.txt")
        self.crate("p7-crate")
        cut = self.view()["p7-crate"]["cut"]
        self.assertEqual((cut["charter"], cut["unchecked"], cut["next_act"], cut["paths"]),
                         (None, None, None, None))
        self.assertEqual(len(cut["commits"]), 1)
        self.assertEqual(self.text_of("p7-crate")[1:], [
            "  charter: none on p7-crate",
            "  past: %s add p7-1.txt" % git(self.pear, "rev-parse", "p7-crate")[:7]])

    def test_built_and_to_fix(self):
        tip = self.on_branch("p8-crate", "p8-1.txt")
        self.crate("p8-crate")
        self.build("p8-crate", 1, tip)
        got = self.view()["p8-crate"]
        self.assertEqual((got["state"], got["cut"]), ("built", None))
        self.review("p8-crate", 1, "%s..%s" % (self.base("p8-crate")[:7], tip[:7]),
                    ruling="fix: F1")
        got = self.view()["p8-crate"]
        self.assertEqual((got["state"], got["past"], got["cut"]), ("to fix", 0, None))
        self.assertEqual(len(self.text_of("p8-crate")), 1)
        tip2 = self.on_branch("p8-crate", "p8-2.txt")
        got = self.view()["p8-crate"]
        self.assertEqual((got["state"], got["past"]), ("to fix", 1))
        self.assertEqual(got["cut"]["commits"], [{"sha": tip2, "subject": "add p8-2.txt"}])
        self.assertEqual(self.text_of("p8-crate")[1:], [
            "  charter: none on p8-crate", "  past: %s add p8-2.txt" % tip2[:7]])


# Acceptance 10: the text of `rows` and `rows check` at the pin, 1ace01a, for rows of every
# word that holds no `cut`; <root> is the rows folder, <crate> the member's checkout.
PIN_ROWS = """\
b1-crate  S3 crate  briefed  next: <root>/b1-crate/brief.md
f1-crate  S3 crate  to fix  tip eff98d7  gate 20261113-0001 exit 0  next: f1-crate: F1
k1-crate  S2 crate  built  tip a82ee67  gate 20261114-0001 running  next: review 1: 388cb8b..a82ee67
l1-crate  S3 crate  landed  tip ed36685  gate 20261113-0001 exit 0  next: push crate's main
r1-crate  S3 crate  to rule  tip 9c60c08  gate 20261113-0001 exit 0  next: <root>/r1-crate/review-1.md
s1-crate  S3 crate  pushed  tip 5d44350  gate 20261113-0001 exit 0  next: 1 owed
t1-crate  S3 crate  pushed  tip 2e65c27  gate 20261113-0001 exit 0  next: type done: 2026-11-10 88ce55b
v1-crate  S3 crate  reviewed  tip 6d5f127  gate 20261113-0001 exit 0  next: phase 2: merge main into v1-crate
w1-crate  S3 crate  waits  next: b1-crate
skipped (absent): plum: m1-plum
"""
PIN_CHECK = """\
c1-crate  stale: done abc1234 is not on main's first-parent line
skipped (absent): plum: m1-plum
checked 10 rows under <root>: 1 stale
"""


class Pin(Depot):
    """Acceptance 10: every other row's lines keep their bytes."""

    def every_word(self):
        self.crate("b1-crate")
        self.crate("w1-crate", depends="b1-crate")
        tip = self.on_branch("k1-crate", "k1.txt")
        self.crate("k1-crate", level="S2")
        self.build("k1-crate", 1, tip, gate="20261114-0001 running")
        for name, ruling in (("r1-crate", ""), ("f1-crate", "fix: F1"), ("v1-crate", "closed")):
            tip = self.on_branch(name, name + ".txt")
            self.crate(name)
            self.build(name, 1, tip)
            self.review(name, 1, "%s..%s" % (self.base(name)[:7], tip[:7]), blocks="F1",
                        ruling=ruling)
        self.pushed("s1-crate", owed=("- [ ] the install",))
        self.pushed("t1-crate")
        self.pushed("l1-crate", push=False)
        self.crate("c1-crate", done="2026-11-01 abc1234")
        self.crate("x1-crate", done="withdrawn 2026-11-01: gone")
        self.crate("m1-plum", repo="plum")

    def normal(self, text):
        return text.replace(os.path.realpath(self.root), "<root>").replace(
            os.path.realpath(self.pear), "<crate>")

    def test_every_other_word_keeps_its_bytes(self):
        self.every_word()
        code, out, _ = self.rows()
        self.assertEqual((code, self.normal(out)), (0, PIN_ROWS))
        code, out = self.checked()
        self.assertEqual((code, self.normal(out)), (1, PIN_CHECK))


class Review1(Depot):
    """Review 1's mends: F1 nothing written from a read made before the question, F2 no WHY
    of several lines, F6 `cut.unchecked` capped, F7 a charter directly in history/sittings/."""

    def test_f1_a_change_made_while_the_question_waits(self):
        self.pushed("p1-crate")
        self.put(self.done, "- older: a row, done 2026-11-01 1111111\n")
        path, done = self.path("p1-crate"), self.done

        class Edit(Stdin):
            def readline(stdin):
                with open(path, "a", encoding="utf-8") as handle:
                    handle.write("- [ ] owed added by another sitting\n")
                with open(done, "a", encoding="utf-8") as handle:
                    handle.write("- other: written meanwhile\n")
                return "y\n"

        with mock.patch.object(rows_module.sys, "stdin", Edit("y\n")):
            code, out, err = self.close("close", "p1-crate", err=TTY())
        self.assertEqual(code, 2, out)
        self.assertTrue(err.endswith("decisions: rows close: %s changed since the close read "
                                     "it; nothing written; run the close again\n" % path), err)
        self.assertNotIn("closed", out)
        self.assertIn("- [ ] owed added by another sitting", self.text("p1-crate"))
        self.assertIn("| done |  |", self.text("p1-crate"))
        with open(done, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "- older: a row, done 2026-11-01 1111111\n"
                             "- other: written meanwhile\n")

    def test_f1_the_done_file_changed_alone(self):
        cell = self.pushed("p1-crate")
        before = self.text("p1-crate")
        done = self.done

        class Edit(Stdin):
            def readline(stdin):
                with open(done, "w", encoding="utf-8") as handle:
                    handle.write("- other: written meanwhile\n")
                return "y\n"

        with mock.patch.object(rows_module.sys, "stdin", Edit("y\n")):
            code, out, err = self.close("close", "p1-crate", err=TTY())
        self.assertEqual(code, 2, out)
        self.assertTrue(err.endswith("decisions: rows close: %s changed since the close read "
                                     "it; nothing written; run the close again\n" % done), err)
        self.assertEqual(self.text("p1-crate"), before)
        self.assertNotIn(cell.split()[1], open(done, encoding="utf-8").read())

    def test_f1_a_close_inside_a_close(self):
        self.pushed("a1-crate")
        cell2 = self.pushed("a2-crate")
        me, inner = self, []

        class Other(Stdin):
            def readline(stdin):
                inner.append(me.close("close", "a2-crate", "-y"))
                return "y\n"

        with mock.patch.object(rows_module.sys, "stdin", Other("y\n")):
            code, out, err = self.close("close", "a1-crate", err=TTY())
        self.assertEqual(inner[0][0], 0, inner)
        self.assertEqual(inner[0][1].splitlines()[-1], "rows close: a2-crate closed")
        self.assertEqual(code, 2, out)
        self.assertIn("%s changed since the close read it" % self.done, err)
        with open(self.done, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "a2-crate: a made-up row, done %s\n" % cell2)
        self.assertIn("| done |  |", self.text("a1-crate"))
        self.assertEqual(sorted(self.view()), ["a1-crate"])
        code, out, _ = self.close("close", "a1-crate", "-y")
        self.assertEqual(code, 0, out)
        with open(self.done, encoding="utf-8") as handle:
            self.assertEqual(len(handle.read().splitlines()), 2)

    def test_f1_the_write_holds_the_lock(self):
        from decisions.common import held
        self.pushed("p1-crate")
        before = self.snapshot("p1-crate")
        lock = os.path.join(os.path.realpath(self.root), rows_module.CLOSE_LOCK)
        with mock.patch.object(rows_module, "CLOSE_WAIT", 0.2), held(lock, 1.0, io.StringIO()):
            code, out, err = self.close("close", "p1-crate", "-y")
        self.assertEqual(code, 2, out)
        self.assertIn("%s is held by pid %d" % (rows_module.CLOSE_LOCK, os.getpid()), err)
        self.assertEqual(self.snapshot("p1-crate"), before)
        self.assertFalse(os.path.exists(lock))
        self.assertEqual(self.close("close", "p1-crate", "-y")[0], 0)
        self.assertFalse(os.path.exists(lock))

    def test_f2_no_why_of_several_lines_or_hidden_characters(self):
        self.crate("p2-crate")
        before = self.snapshot("p2-crate")
        why = "rows close: --withdrawn takes one line of words with no | in it"
        breaks = [c for c in map(chr, range(0x110000)) if len(("a%sb" % c).splitlines()) > 1]
        hidden = ["؜", "᠎", "​", "‌", "‍", "‎", "‏",
                  "‪", "‫", "‬", "‭", "‮", "⁠", "⁡",
                  "⁢", "⁣", "⁤", "⁦", "⁧", "⁨", "⁩",
                  "﻿"]
        self.assertIn(" ", breaks)
        for char in breaks + hidden:
            code, out, err = self.close("close", "p2-crate", "--withdrawn", "a%sb" % char, "-y")
            self.assertEqual((code, out, err), (2, "", "decisions: %s\n" % why), repr(char))
        self.assertEqual(self.snapshot("p2-crate"), before)

    def test_f2_a_done_row_above_repo_and_branch_reads_whole(self):
        self.put(self.path("p3-crate"), "# Row p3-crate: a made-up row\n\n| item | value |\n"
                 "|---|---|\n| done | |\n| repo | crate |\n| branch | p3-other |\n")
        code, out, err = self.close("close", "p3-crate", "--withdrawn",
                                    "superseded by p9, a café — résumé", "-y")
        self.assertEqual((code, err), (0, ""), out)
        cells = rows_module.table(self.text("p3-crate"))
        self.assertEqual(sorted(cells), ["branch", "done", "repo"])
        self.assertEqual((cells["repo"], cells["branch"]), ("crate", "p3-other"))
        self.assertTrue(cells["done"].endswith("superseded by p9, a café — "
                                               "résumé"))

    def test_f6_unchecked_capped(self):
        tree = Cut.tree_of(self, "p5-crate")
        Cut.charter(self, tree, "2026-11-14-3.md",
                    unchecked=["- [ ] box %d" % n for n in range(70)])
        self.crate("p5-crate")
        cut = self.view()["p5-crate"]["cut"]
        self.assertEqual(cut["unchecked"], ["- [ ] box %d" % n for n in range(50)])
        line = Cut.text_of(self, "p5-crate")[1]
        self.assertEqual(line, "  charter history/sittings/2026-11-14-3.md: 70 unchecked; "
                               "next act: none")

    def test_f7_a_charter_lies_directly_in_history_sittings(self):
        tree = Cut.tree_of(self, "c1-crate")
        Cut.charter(self, tree, "2026-11-14-2.md", unchecked=("- [ ] the real one",),
                    next_act="the real act")
        for rel, text in (("zz/2026-11-14-2.md", "# a copy\n\n## Next act\nzz copy\n"),
                          ("archive/old/2099-01-01-1.md", "# not a charter\n")):
            path = os.path.join(tree, "history", "sittings", rel)
            os.makedirs(os.path.dirname(path))
            self.put(path, text)
            git(tree, "add", path)
            git(tree, "commit", "-q", "-m", "add " + rel)
        self.crate("c1-crate")
        cut = self.view()["c1-crate"]["cut"]
        self.assertEqual((cut["charter"], cut["unchecked"], cut["next_act"]),
                         ("history/sittings/2026-11-14-2.md", ["- [ ] the real one"],
                          "the real act"))
