"""The hermetic base for every test that calls `decisions.main` (ADV6-4).

`main` finds the ledger at the git top of the cwd and `doctor` reads
`os.environ`, `HOME` and the session's resolved file, so a test that inherits
the caller's environment reads live state: a `CLAUDE_CODE_SESSION_ID` with a
`resolved.json`, a `GIT_DIR` naming another repository. `Hermetic.setUp`
clears the environment to a temp `HOME`, `XDG_STATE_HOME` and `XDG_CONFIG_HOME`
and the caller's `PATH`, and guards `open` so that no test reads or writes this checkout's own
ledger, its OPEN-QUESTIONS.md or its CLAUDE.md.

A fixture folder inside this clone is this clone's for the records resolver
(design/28): a verb handed one reads the clone's records, which in a clone whose
records are out live in another repository. `outside` and `fixture_outside` hand
a test a copy in no repository instead.
"""

import builtins
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = tuple(os.path.join(os.path.realpath(REPO), name)
             for name in ("DECISIONS.md", "OPEN-QUESTIONS.md", "CLAUDE.md"))
SAMPLE = os.path.join(REPO, "tests", "fixtures", "sectioned", "DECISIONS.md")

__all__ = ["Hermetic", "REPO", "LIVE", "SAMPLE", "outside"]


def in_a_repository(folder):
    """True when git finds `folder` inside a work tree, read with no GIT_* variable."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    found = subprocess.run(["git", "-C", folder, "rev-parse", "--is-inside-work-tree"],
                           env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           text=True, timeout=30)
    return found.returncode == 0 and found.stdout.strip() == "true"


def outside(source):
    """(root, copy): the folder `source` copied as `root/<its name>`, `root` a new temp
    folder in no repository, which the caller removes. Raises when the temp folder is
    inside one, since a verb would then read that repository's records."""
    root = tempfile.mkdtemp(prefix="decisions-fixture-")
    if in_a_repository(root):
        shutil.rmtree(root, True)
        raise RuntimeError("the temp folder is inside a repository: %s" % root)
    copy = os.path.join(root, os.path.basename(os.path.normpath(source)))
    shutil.copytree(source, copy)
    return root, copy


def live(file):
    """True when `file` names this checkout's ledger, questions or CLAUDE.md."""
    if not isinstance(file, (str, bytes, os.PathLike)):
        return False
    return os.path.realpath(os.fsdecode(file)) in LIVE


def guard(real):
    def guarded(file, *args, **kwargs):
        if live(file):
            raise AssertionError("a hermetic test opened the live checkout: %s" % file)
        return real(file, *args, **kwargs)
    return guarded


def guard_replace(real):
    """`os.replace` onto a live path raises: the tool writes by one rename."""
    def guarded(src, dst, *args, **kwargs):
        if live(dst):
            raise AssertionError("a hermetic test wrote the live checkout: %s" % dst)
        return real(src, dst, *args, **kwargs)
    return guarded


class Hermetic(unittest.TestCase):

    def setUp(self):
        super().setUp()
        tmp = tempfile.mkdtemp(prefix="decisions-hermetic-")
        self.addCleanup(shutil.rmtree, tmp, True)
        env = {"HOME": os.path.join(tmp, "home"),
               "XDG_STATE_HOME": os.path.join(tmp, "state"),
               "XDG_CONFIG_HOME": os.path.join(tmp, "config"),
               "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        for name in ("HOME", "XDG_STATE_HOME", "XDG_CONFIG_HOME"):
            os.makedirs(env[name])
        for patcher in (mock.patch.dict(os.environ, env, clear=True),
                        mock.patch("io.open", guard(io.open)),
                        mock.patch("builtins.open", guard(builtins.open)),
                        mock.patch("os.replace", guard_replace(os.replace))):
            patcher.start()
            self.addCleanup(patcher.stop)

    def fixture_outside(self, source):
        """A copy of the fixture folder `source` in no repository, removed at cleanup."""
        root, copy = outside(source)
        self.addCleanup(shutil.rmtree, root, True)
        return copy
