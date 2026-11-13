"""d40: six small mends, one class a ruling. R1 (n43): `head_holds` runs its git children
without git's repository variables, so a caller's `GIT_DIR` naming another repository does
not make that repository's HEAD the file's. Every file is made here under a temp folder."""

import io
import os
import shutil
import tempfile
from unittest import mock

import decisions
from decisions.render import head_holds
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
