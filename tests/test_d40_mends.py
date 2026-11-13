"""d40: six small mends, one class a ruling. R1 (n43): `head_holds` runs its git children
without git's repository variables, so a caller's `GIT_DIR` naming another repository does
not make that repository's HEAD the file's. Every file is made here under a temp folder."""

import contextlib
import io
import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

import decisions
from decisions.render import GATES, head_holds, list_gate
from tests import gates
from tests.hermetic import Hermetic
from tests.test_d38_gate_layers import Home
from tests.test_expire import Fixture, git, repo_at
from tests.test_render import FIXTURE


def other_repo(case):
    """Another repository, holding a different DECISIONS.md and NICE_TO_HAVE.md."""
    root = tempfile.mkdtemp(prefix="decisions-d40-")
    case.addCleanup(shutil.rmtree, root, True)
    return repo_at(os.path.join(root, "other"),
                   {"DECISIONS.md": "# other\n", "NICE_TO_HAVE.md": "# other\n"})


class GitVariables(Hermetic):
    """R1: the ledger's own repository answers, whatever `GIT_DIR` says."""

    def setUp(self):
        super().setUp()
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.ledger = os.path.join(self.tmp, "DECISIONS.md")
        with open(self.ledger, "w", encoding="utf-8") as handle:
            handle.write(FIXTURE)
        git(self.tmp, "init", "-q")
        git(self.tmp, "add", "DECISIONS.md")
        git(self.tmp, "commit", "-q", "-m", "the ledger")
        self.elsewhere = other_repo(self)

    def test_head_holds_reads_the_files_own_repository(self):
        with open(self.ledger, "rb") as handle:
            data = handle.read()
        with mock.patch.dict(os.environ, {"GIT_DIR": os.path.join(self.elsewhere, ".git")}):
            self.assertIsNotNone(head_holds(self.ledger, data))

    def test_fold_tails_reads_the_files_own_head(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"GIT_DIR": os.path.join(self.elsewhere, ".git")}):
            code = decisions.main(["render", "--fold-tails", "--ledger", self.ledger],
                                  out=out, err=err)
        self.assertEqual(code, 0, err.getvalue())
        self.assertIn("holds them whole", out.getvalue())


class ExpireGitVariables(Fixture):

    def test_expire_write_reads_the_files_own_head(self):
        elsewhere = other_repo(self)
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"GIT_DIR": os.path.join(elsewhere, ".git")}):
            code = decisions.main(["expire", self.repo, "--write"], out=out, err=err)
        self.assertEqual(code, 0, err.getvalue())


class GatesWalkThePlugin(unittest.TestCase):
    """R2 (n1): `plugin/lib` is under the syntax and pyflakes gates, and the shebang gate of
    `src/decisions.py` is gone. Run in a temp folder holding only the folders it walks."""

    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        for folder in ("src", "tests", os.path.join("plugin", "lib", "pkg")):
            os.makedirs(os.path.join(self.tmp, folder))
        before = os.getcwd()
        self.addCleanup(os.chdir, before)
        os.chdir(self.tmp)

    def put(self, name, text):
        with open(os.path.join(self.tmp, name), "w", encoding="utf-8") as handle:
            handle.write(text)

    def test_the_syntax_gate_refuses_newer_syntax_under_plugin_lib(self):
        self.put(os.path.join("plugin", "lib", "pkg", "new.py"),
                 "try:\n    pass\nexcept ValueError, TypeError:\n    pass\n")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = gates.syntax_gate()
        self.assertEqual(status, 1)
        self.assertIn(os.path.join("plugin", "lib", "pkg", "new.py"), err.getvalue())

    def test_the_pyflakes_gate_walks_plugin_lib(self):
        walked = []

        def check(roots, reporter):
            walked.extend(roots)
            return 0

        fake = types.SimpleNamespace(api=types.SimpleNamespace(checkRecursive=check),
                                     reporter=types.SimpleNamespace(
                                         Reporter=lambda out, err: None))
        modules = {"pyflakes": fake, "pyflakes.api": fake.api,
                   "pyflakes.reporter": fake.reporter}
        with mock.patch.dict(sys.modules, modules), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gates.pyflakes_gate(), 0)
        self.assertIn(os.path.join("plugin", "lib"), walked)

    def test_no_shebang_gate_remains(self):
        self.put("skips.allow", "1 pyflakes absent\n")
        with contextlib.redirect_stdout(io.StringIO()):
            status = gates.main(["--skips-allow", "skips.allow"])
        self.assertEqual(status, 0)
        self.assertFalse(hasattr(gates, "shebang_gate"))


class Lists(Home):
    """R4 to R6 (n79, n80, n81): what `render --lint` reads from a list and how the
    cannot-be-listed warning spells its paths."""

    def put(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(data)

    def checkout_list(self, data):
        self.put(os.path.join(self.repo, ".claude", GATES), data)
        code, _, err = self.render("--lint")
        self.assertEqual(code, 0, err)
        return [l for l in err.splitlines() if GATES in l]

    def test_r4_a_nul_line_with_an_outside_prefix_warns_once(self):
        warned = self.checkout_list(b"/abs\x00x\n")
        self.assertEqual(len(warned), 1, warned)
        self.assertIn("reaches outside the checkout", warned[0])
        for line in (b"~/x\x00y\n", b"../plum\x00x\n"):
            self.assertEqual(len(self.checkout_list(line)), 1, line)

    def test_r4_a_nul_line_with_no_such_prefix_is_skipped_silently(self):
        os.makedirs(os.path.join(os.path.dirname(self.repo), "plum"))
        self.assertEqual(self.checkout_list(b"CLAUDE.md\nplum\x00x\ndocs\x00y\n"), [])
        self.put(self.owner, b"~/work/orchard/pear/x\x00y\n")
        self.assertEqual([l for l in self.render("--lint")[2].splitlines() if GATES in l], [])

    def test_r5_an_undecodable_byte_silences_no_other_line(self):
        warned = self.checkout_list(b"CLAUDE.md\n\xff\n/abs/x\n")
        self.assertEqual(len(warned), 1, warned)
        self.assertIn(":3:", warned[0])
        self.put(self.owner, b"\xff\n~/work/orchard/pear/z\n")
        owner = [l for l in self.render("--lint")[2].splitlines() if "lies under" in l]
        self.assertEqual(len(owner), 1, owner)

    def test_r6_the_warning_spells_target_and_list_one_way(self):
        os.makedirs(os.path.join(self.repo, "sub"))
        link = os.path.join(self.home, "link")
        os.symlink(os.path.join(self.repo, "sub"), link)
        self.put(os.path.join(self.repo, ".claude"), b"")
        code, _, err = self.render("--into", os.path.join(link, "CLAUDE.md"))
        self.assertEqual(code, 0, err)
        warned = [l for l in err.splitlines() if "warning" in l]
        self.assertEqual(len(warned), 1, err)
        self.assertNotIn("link", warned[0])
        self.assertIn("is not listed: ~/work/orchard/pear/.claude/%s cannot be written" % GATES,
                      warned[0])
        self.assertIn("~/work/orchard/pear/sub/CLAUDE.md is not listed", warned[0])

    def test_r6_a_line_that_cannot_be_made_says_it_cannot_be_resolved(self):
        target = os.path.join(self.home, "work", "orchard", "pear", "CLAUDE.md")
        err = io.StringIO()
        with mock.patch("decisions.render._gate_line", side_effect=OSError("too many links")):
            self.assertIsNone(list_gate(target, err))
        text = err.getvalue()
        self.assertEqual(text.count("CLAUDE.md"), 1, text)
        self.assertIn("is not listed: its line cannot be resolved (too many links)", text)
