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
from decisions.render import head_holds
from tests import gates
from tests.hermetic import Hermetic
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
