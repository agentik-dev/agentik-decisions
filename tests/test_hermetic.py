"""The suite reads no live state (ADV6-4): a hostile environment around the
CLI test classes changes nothing, and the guard on the live checkout fires."""

import io
import json
import os
import pathlib
import shutil
import tempfile
import unittest
from unittest import mock

from decisions import doctor
from tests.hermetic import Hermetic, LIVE, REPO

# The CLI test classes that read and write through `decisions.main`.
CLASSES = ["tests.test_lookup.Show", "tests.test_lookup.Find", "tests.test_lookup.TheArea",
           "tests.test_new.New", "tests.test_new.Titles", "tests.test_new.AllOrNothing",
           "tests.test_render.Render", "tests.test_render.Check", "tests.test_render.LintFirst",
           "tests.test_cli.Verbs", "tests.test_cli.Locate"]


class NoLiveState(unittest.TestCase):
    """A session id with a hostile resolved.json, and a GIT_DIR naming another repo."""

    def test_the_cli_classes_pass_unchanged(self):
        tmp = tempfile.mkdtemp(prefix="decisions-hostile-")
        self.addCleanup(shutil.rmtree, tmp)
        # agentik-r1 c1: the old state folder, which doctor reads while the new one is absent
        resolved = os.path.join(tmp, doctor.SESSION_STATE[1], "sessions", "x", "resolved.json")
        os.makedirs(os.path.dirname(resolved))
        with open(resolved, "w", encoding="utf-8") as handle:
            json.dump({"provider": {"plugin": "session", "version": "2.0.0"},
                       "decisions": {"ledger": "hostile"}}, handle)
        hostile = {"CLAUDE_CODE_SESSION_ID": "x", "XDG_STATE_HOME": tmp,
                   "GIT_DIR": os.path.join(REPO, ".git")}
        suite = unittest.defaultTestLoader.loadTestsFromNames(CLASSES)
        stream = io.StringIO()
        with mock.patch.dict(os.environ, hostile):
            result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
        self.assertTrue(result.wasSuccessful(), stream.getvalue()[-2000:])
        self.assertGreater(result.testsRun, 40)


class GuardFires(Hermetic):
    """Opening this checkout's ledger, questions or CLAUDE.md inside a Hermetic test raises."""

    def test_open(self):
        for path in LIVE:
            with self.subTest(path=path):
                with self.assertRaises(AssertionError):
                    open(path, encoding="utf-8")

    def test_pathlib(self):
        with self.assertRaises(AssertionError):
            pathlib.Path(REPO, "CLAUDE.md").read_text(encoding="utf-8")

    def test_relative_from_the_repo(self):
        cwd = os.getcwd()
        os.chdir(REPO)
        self.addCleanup(os.chdir, cwd)
        with self.assertRaises(AssertionError):
            open("DECISIONS.md", "w", encoding="utf-8")

    def test_a_rename_onto_the_live_checkout(self):
        with self.assertRaises(AssertionError):
            os.replace(os.path.join(REPO, "absent"), LIVE[0])

    def test_the_environment_is_cleared(self):
        self.assertEqual(sorted(os.environ),
                         ["HOME", "PATH", "XDG_CONFIG_HOME", "XDG_STATE_HOME"])
        self.assertTrue(os.environ["HOME"].startswith(tempfile.gettempdir()))

    def test_xdg_config_home_is_a_temp_dir(self):
        # d18 2a obs: XDG_CONFIG_HOME is set to a temp dir, not cleared to fall back on HOME
        config = os.environ.get("XDG_CONFIG_HOME")
        self.assertIsNotNone(config)
        self.assertTrue(os.path.isdir(config))
        self.assertTrue(config.startswith(tempfile.gettempdir()))

    def test_other_paths_open(self):
        with open(os.path.join(REPO, "Makefile"), encoding="utf-8") as handle:
            self.assertIn("check:", handle.read())


if __name__ == "__main__":
    unittest.main()
