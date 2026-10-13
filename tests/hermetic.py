"""The hermetic base for every test that calls `decisions.main` (ADV6-4).

`main` finds the ledger at the git top of the cwd and `doctor` reads
`os.environ`, `HOME` and the session's resolved file, so a test that inherits
the caller's environment reads live state: a `CLAUDE_CODE_SESSION_ID` with a
`resolved.json`, a `GIT_DIR` naming another repository. `Hermetic.setUp`
clears the environment to a temp `HOME`, `XDG_STATE_HOME` and `XDG_CONFIG_HOME`
and the caller's `PATH`, and guards `open` so that no test reads or writes this checkout's own
ledger, its OPEN-QUESTIONS.md or its CLAUDE.md.
"""

import builtins
import io
import os
import shutil
import tempfile
import unittest
from unittest import mock

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = tuple(os.path.join(os.path.realpath(REPO), name)
             for name in ("DECISIONS.md", "OPEN-QUESTIONS.md", "CLAUDE.md"))
SAMPLE = os.path.join(REPO, "tests", "fixtures", "sectioned", "DECISIONS.md")

__all__ = ["Hermetic", "REPO", "LIVE", "SAMPLE"]


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
