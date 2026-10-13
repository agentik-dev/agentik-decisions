"""ADV6-5: a skip is a gate that did not run, never a pass.

`tests/gates.py` passes pyflakes absent only when `tests/skips.allow` lists it;
`tests/run.py` runs the suite and exits 1 on a skip reason the file does not
list.  Every allow file here is a temp file.
"""

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

from tests import gates

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AllowFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, self.tmp)

    def allow(self, text):
        path = os.path.join(self.tmp, "skips.allow")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path


class ReadAllow(AllowFile):
    def test_comments_and_blanks_dropped(self):
        path = self.allow("# a comment\n\n1 pyflakes absent\n  2 spaced reason  \n")
        self.assertEqual(gates.read_allow(path), {"pyflakes absent": 1, "spaced reason": 2})

    def test_a_line_without_a_count_raises(self):
        path = self.allow("# a comment\n1 pyflakes absent\nspaced reason\n")
        with self.assertRaises(gates.AllowError) as caught:
            gates.read_allow(path)
        self.assertEqual(str(caught.exception), "%s:3: no count" % path)

    def test_missing_file_allows_nothing(self):
        self.assertEqual(gates.read_allow(os.path.join(self.tmp, "absent")), {})

    def test_checked_in_file_allows_no_skip(self):
        # pyflakes is installed by `make venv` (ruling 6 of 2026-09-23 14:55): its absence is
        # no longer allowed; the legacy tests' pin left with the legacy reader (d17)
        allowed = gates.read_allow(os.path.join(REPO, "tests", "skips.allow"))
        self.assertEqual(allowed, {})


class PyflakesAbsent(AllowFile):
    def run_gate(self, path):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(sys.modules, {"pyflakes": None}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = gates.pyflakes_gate(path)
        return status, out.getvalue(), err.getvalue()

    def test_listed_passes_and_says_so(self):
        status, out, _ = self.run_gate(self.allow("1 pyflakes absent\n"))
        self.assertEqual(status, 0)
        self.assertEqual(out, "gate: pyflakes absent, allowed by %s\n" % os.path.join(self.tmp, "skips.allow"))

    def test_a_line_without_a_count_refuses(self):
        status, out, err = self.run_gate(self.allow("pyflakes absent\n"))
        self.assertEqual((status, out), (1, ""))
        self.assertIn(":1: no count", err)

    def test_unlisted_refuses(self):
        status, out, err = self.run_gate(self.allow("# nothing\n"))
        self.assertEqual(status, 1)
        self.assertEqual(out, "")
        self.assertIn("gate: pyflakes absent, not in ", err)


MODULE = textwrap.dedent('''
    import unittest

    class T(unittest.TestCase):
        def test_runs(self):
            pass

        @unittest.skip("listed reason")
        def test_listed(self):
            pass

        @unittest.skip("other reason")
        def test_other(self):
            pass
''')


class Runner(AllowFile):
    def run_runner(self, allow_text):
        with open(os.path.join(self.tmp, "skipmod.py"), "w", encoding="utf-8") as fh:
            fh.write(MODULE)
        env = dict(os.environ, PYTHONPATH=self.tmp)
        proc = subprocess.run(
            [sys.executable, os.path.join(REPO, "tests", "run.py"),
             "--skips-allow", self.allow(allow_text), "skipmod"],
            cwd=self.tmp, env=env, capture_output=True, text=True, timeout=60)
        return proc.returncode, proc.stdout

    def test_every_reason_listed_exits_0(self):
        code, out = self.run_runner("1 listed reason\n1 other reason\n")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[-1], "skips: 2 allowed")

    def test_an_unlisted_reason_exits_1_naming_it(self):
        code, out = self.run_runner("1 listed reason\n")
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), ["skips: other reason counted 1, pinned 0"])

    def test_a_named_module_counts_at_most_the_pin(self):
        code, out = self.run_runner("5 listed reason\n1 other reason\n")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[-1], "skips: 2 allowed")


EXPECTED = textwrap.dedent('''
    import unittest

    class T(unittest.TestCase):
        def test_runs(self):
            pass

        @unittest.expectedFailure
        def test_fails(self):
            self.assertEqual(1, 2)

        @unittest.expectedFailure
        def test_passes(self):
            pass
''')


class Expected(AllowFile):
    """ADV11-5: an expected failure or an unexpected success fails the suite."""

    def run_runner(self, name):
        with open(os.path.join(self.tmp, "expmod.py"), "w", encoding="utf-8") as fh:
            fh.write(EXPECTED)
        env = dict(os.environ, PYTHONPATH=self.tmp)
        proc = subprocess.run(
            [sys.executable, os.path.join(REPO, "tests", "run.py"),
             "--skips-allow", self.allow(""), "expmod.T." + name],
            cwd=self.tmp, env=env, capture_output=True, text=True, timeout=60)
        return proc.returncode, proc.stdout

    def test_an_expected_failure_exits_1(self):
        code, out = self.run_runner("test_fails")
        self.assertEqual(code, 1, out)
        self.assertIn("expected: expmod.T.test_fails is an expected failure", out)

    def test_an_unexpected_success_exits_1(self):
        code, out = self.run_runner("test_passes")
        self.assertEqual(code, 1, out)
        self.assertIn("expected: expmod.T.test_passes is an unexpected success", out)


class SkipCount(AllowFile):
    """ADV10-4: under discovery each reason's count matches its pin exactly."""

    def discover(self, allow_text):
        tests = os.path.join(self.tmp, "tests")
        os.makedirs(tests)
        open(os.path.join(tests, "__init__.py"), "w").close()
        with open(os.path.join(tests, "test_skipmod.py"), "w", encoding="utf-8") as fh:
            fh.write(MODULE)
        proc = subprocess.run(
            [sys.executable, os.path.join(REPO, "tests", "run.py"),
             "--skips-allow", self.allow(allow_text)],
            cwd=self.tmp, capture_output=True, text=True, timeout=60)
        return proc.returncode, proc.stdout.splitlines()

    def test_exact_counts_pass(self):
        self.assertEqual(self.discover("1 listed reason\n1 other reason\n"),
                         (0, ["skips: 2 allowed"]))

    def test_an_extra_skip_exits_1(self):
        code, out = self.discover("1 listed reason\n0 other reason\n")
        self.assertEqual((code, out), (1, ["skips: other reason counted 1, pinned 0"]))

    def test_a_missing_skip_exits_1(self):
        code, out = self.discover("2 listed reason\n1 other reason\n")
        self.assertEqual((code, out), (1, ["skips: listed reason counted 1, pinned 2"]))

    def test_a_line_without_a_count_exits_1(self):
        code, out = self.discover("# pins\nlisted reason\n1 other reason\n")
        self.assertEqual(code, 1)
        self.assertEqual(out, ["skips: %s:2: no count" % os.path.join(self.tmp, "skips.allow")])

    def test_the_gates_skip_is_not_the_suites(self):
        code, out = self.discover("1 listed reason\n1 other reason\n1 pyflakes absent\n")
        self.assertEqual((code, out), (0, ["skips: 2 allowed"]))


if __name__ == "__main__":
    unittest.main()
