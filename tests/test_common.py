"""The shared helpers: the bounded child (ADV6-6), the git top, the one-rename write."""

import os
import shutil
import stat
import tempfile
import time
from unittest import mock

from decisions import common
from decisions.common import Refusal
from tests.hermetic import Hermetic


class Bounded(Hermetic):
    """git's child is bounded; a hang is a Refusal, killed as a group."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        fake = os.path.join(self.tmp, "bin", "git")
        os.makedirs(os.path.dirname(fake))
        with open(fake, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\nsleep 30\n")
        os.chmod(fake, 0o755)
        self.path = os.path.dirname(fake) + os.pathsep + "/usr/bin:/bin"

    def test_a_hung_git_is_a_refusal(self):
        start = time.monotonic()
        with mock.patch.dict(os.environ, {"PATH": self.path}), \
                mock.patch.object(common, "GIT_TIMEOUT", 1):
            with self.assertRaises(Refusal) as caught:
                common.git_top(self.tmp)
        self.assertLess(time.monotonic() - start, 10)
        self.assertIn("git rev-parse timed out after 1 s", str(caught.exception))

    def test_bounded_returns_the_output(self):
        self.assertEqual(common.bounded(["/bin/echo", "x"], 5), (0, "x\n"))

    def test_outside_a_work_tree_is_none(self):
        self.assertIsNone(common.git_top(self.tmp))


class Write(Hermetic):

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_the_mode_survives_and_no_temp_is_left(self):
        path = os.path.join(self.tmp, "f.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("old\n")
        os.chmod(path, 0o640)
        common.write_text(path, "new\n")
        self.assertEqual(common.read_text(path), "new\n")
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o640)
        self.assertEqual(os.listdir(self.tmp), ["f.md"])

    def test_an_unreadable_file_is_a_refusal(self):
        with self.assertRaises(Refusal):
            common.read_text(os.path.join(self.tmp, "absent.md"))
