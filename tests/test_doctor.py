#!/usr/bin/env python3
"""`doctor`: a fake `pyenv` on a temp PATH, a temp HOME and XDG_STATE_HOME;
the resolved file in range, out of range and absent; the ledger clean, absent
and refused by the lint; the exit and `--json`."""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import decisions
from tests.hermetic import REPO, SAMPLE, Hermetic
from decisions import doctor
from decisions.doctor import in_range


MANIFEST = os.path.join(REPO, "plugin", ".claude-plugin", "plugin.json")


def current():
    """This package's version, as the plugin manifest names it."""
    with open(MANIFEST, encoding="utf-8") as handle:
        return json.load(handle)["version"]


def write(path, text, mode=0o644):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.chmod(path, mode)


class Doctor(Hermetic):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.home = os.path.join(self.tmp, "home")
        self.bin = os.path.join(self.tmp, "bin")
        self.state = os.path.join(self.tmp, "state")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.bin)
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        shutil.copy(SAMPLE, os.path.join(self.repo, "DECISIONS.md"))
        self.pyenv_list("  3.12.7\n  3.13.1\n  3.14.7\n  3.15.0a1\n  3.14-dev\n  pypy3.10-7.3.17\n")
        self.env = {"HOME": self.home, "PATH": self.bin + os.pathsep + "/usr/bin:/bin",
                    "XDG_STATE_HOME": self.state, "CLAUDE_CODE_SESSION_ID": "s1"}
        self.prefix = os.path.join(self.home, ".pyenv", "versions", "agentik-decisions")

    def pyenv_list(self, listing):
        write(os.path.join(self.bin, "pyenv"),
              "#!/bin/sh\ncat <<'END'\n%sEND\n" % listing, 0o755)

    def resolved(self, version, folder=doctor.SESSION_STATE[0]):
        write(os.path.join(self.state, folder, "sessions", "s1", "resolved.json"),
              json.dumps({"provider": {"plugin": "session", "version": version, "profile": "p"},
                          "decisions": {}}))

    def checks(self):
        with mock.patch.object(sys, "prefix", self.prefix):
            got, provider = doctor.run_checks(cwd=self.repo, env=self.env)
        return {name: (status, detail) for name, status, detail in got}, provider

    def test_newer_python_warns(self):
        got, _ = self.checks()
        self.assertEqual(got["python"][0], "warn")
        self.assertIn("newer python available: 3.14.7", got["python"][1])

    def test_current_python_is_ok(self):
        self.pyenv_list("  3.12.1\n  %d.%d.%d\n" % sys.version_info[:3])
        self.assertEqual(self.checks()[0]["python"][0], "ok")

    def test_python_outside_pyenv_fails(self):
        self.prefix = "/usr"
        self.assertEqual(self.checks()[0]["python"][0], "fail")

    def test_pyenv_absent_warns(self):
        os.remove(os.path.join(self.bin, "pyenv"))
        got = self.checks()[0]["python"]
        self.assertEqual(got[0], "warn")
        self.assertIn("pyenv not on PATH", got[1])

    def test_a_hung_pyenv_warns(self):
        """ADV6-6: a pyenv that hangs (and a grandchild holding its pipe) is a bounded warn."""
        write(os.path.join(self.bin, "pyenv"), "#!/bin/sh\nsleep 30\necho 3.99.0\n", 0o755)
        start = time.monotonic()
        with mock.patch.object(doctor, "PYENV_TIMEOUT", 1):
            got = self.checks()[0]["python"]
        self.assertLess(time.monotonic() - start, 10)
        self.assertEqual(got[0], "warn")
        self.assertIn("pyenv install --list timed out after 1 s", got[1])

    def test_tool_marketplace_and_plugin(self):
        got, _ = self.checks()
        for name in ("tool", "marketplace", "plugin"):
            self.assertEqual(got[name][0], "warn", name)
        # agentik-r1 c7 c9: the old entry point and the old IDs alone are a warn until r2
        self.tool("echo 'agentik-decisions %s'" % current(), name=doctor.ALIAS)
        self.plugins(doctor.OLD_MARKETPLACE, doctor.OLD_PLUGIN)
        got, _ = self.checks()
        for name, said in (("tool", "alias only; make install"), ("marketplace", "only the old"),
                           ("plugin", "only the old")):
            self.assertEqual(got[name][0], "warn", name)
            self.assertIn(said, got[name][1])
        self.tool("echo 'agentik-decisions %s'" % current())
        self.plugins(doctor.MARKETPLACE, doctor.PLUGIN)
        got, _ = self.checks()
        for name in ("tool", "marketplace", "plugin"):
            self.assertEqual(got[name][0], "ok", name)
        self.assertEqual((doctor.MARKETPLACE, doctor.PLUGIN, doctor.TOOL),
                         ("agentik", "decisions@agentik", "agentik-decisions"))

    def plugins(self, marketplace, plugin):
        write(os.path.join(self.home, ".claude", "plugins", "known_marketplaces.json"),
              json.dumps({marketplace: {}}))
        write(os.path.join(self.home, ".claude", "plugins", "installed_plugins.json"),
              json.dumps({"version": 2, "plugins": {plugin: []}}))

    def tool(self, body, name=doctor.TOOL):
        write(os.path.join(self.bin, name), "#!/bin/sh\n%s\n" % body, 0o755)

    def test_a_stale_tool_warns(self):
        # F15: the tool on PATH names its version; another version than this package's warns
        self.tool("echo 'agentik-decisions 0.0.1'")
        got = self.checks()[0]["tool"]
        self.assertEqual(got[0], "warn")
        for part in ("0.0.1", current(), "make install"):
            self.assertIn(part, got[1])
        self.tool("echo 'usage: agentik decisions' >&2\nexit 2")
        got = self.checks()[0]["tool"]
        self.assertEqual(got[0], "warn")
        self.assertIn("make install", got[1])
        self.tool("echo 'agentik-decisions %s'" % current())
        self.assertEqual(self.checks()[0]["tool"][0], "ok")

    def test_the_tool_runs_without_pythonpath(self):
        # B2 (d-n1 review): a PYTHONPATH naming a checkout would make the installed tool
        # import it and name the checkout's version, so the tool runs without it
        self.tool('echo "agentik-decisions %s${PYTHONPATH:+ PYTHONPATH=$PYTHONPATH}'
                  '${PYTHONHOME:+ PYTHONHOME=$PYTHONHOME}"' % current())
        self.env.update(PYTHONPATH="src", PYTHONHOME="/nowhere")
        got = self.checks()[0]["tool"]
        self.assertEqual(got[0], "ok", got[1])

    def test_undecodable_or_endless_tool_output_warns(self):
        # B3 (d-n1 review): bytes that are not UTF-8 and output without end are a warn,
        # read only so far, and doctor's exit stays its own
        self.tool(r"printf '\377\376\375\n'")
        got = self.checks()[0]["tool"]
        self.assertEqual(got[0], "warn")
        self.assertIn("make install", got[1])
        with mock.patch.dict(os.environ, self.env, clear=True), \
                mock.patch.object(sys, "prefix", self.prefix):
            code = decisions.main(["doctor", "--ledger", os.path.join(self.repo, "DECISIONS.md")],
                                  out=io.StringIO(), err=io.StringIO())
        self.assertEqual(code, 0)
        self.tool("while :; do echo decisions; done")
        start = time.monotonic()
        with mock.patch.object(doctor, "TOOL_TIMEOUT", 8):
            got = self.checks()[0]["tool"]
        self.assertLess(time.monotonic() - start, 5)
        self.assertEqual(got[0], "warn")

    def test_a_hung_tool_warns(self):
        # B3: a tool that hangs, with a grandchild holding its pipe, is a bounded warn
        self.tool("sleep 30 &\nsleep 30")
        start = time.monotonic()
        with mock.patch.object(doctor, "TOOL_TIMEOUT", 1):
            got = self.checks()[0]["tool"]
        self.assertLess(time.monotonic() - start, 10)
        self.assertEqual(got[0], "warn")
        self.assertIn("timed out after 1 s", got[1])

    def test_a_named_missing_ledger_fails(self):
        # F16: a `--ledger` naming an absent file is a fail, so doctor exits 2
        absent = os.path.join(self.tmp, "absent", "DECISIONS.md")
        with mock.patch.object(sys, "prefix", self.prefix):
            got, _ = doctor.run_checks(cwd=self.repo, env=self.env, ledger=absent)
        got = {name: (status, detail) for name, status, detail in got}
        self.assertEqual(got["ledger"][0], "fail")
        self.assertIn("no ledger at", got["ledger"][1])
        with mock.patch.dict(os.environ, self.env, clear=True), \
                mock.patch.object(sys, "prefix", self.prefix):
            code = decisions.main(["doctor", "--ledger", absent], out=io.StringIO(),
                                  err=io.StringIO())
        self.assertEqual(code, 2)

    def test_a_uv_tool_python_is_ok(self):
        # the python row: `make install` runs the tool under uv, so a uv tool at 3.12+ is ok
        prefix = os.path.join(self.home, ".local", "share", "uv", "tools", "agentik-decisions")
        os.makedirs(prefix)
        status, detail = doctor.check_python(self.env, prefix=prefix, version=(3, 13, 15))
        self.assertEqual(status, "ok", detail)
        self.assertIn("uv tool", detail)
        self.assertEqual(doctor.check_python(self.env, prefix=prefix, version=(3, 11, 9))[0],
                         "fail")
        moved = os.path.join(self.tmp, "uv-tools", "agentik-decisions")
        os.makedirs(moved)
        env = dict(self.env, UV_TOOL_DIR=os.path.dirname(moved))
        self.assertEqual(doctor.check_python(env, prefix=moved, version=(3, 12, 0))[0], "ok")
        self.assertEqual(doctor.check_python(self.env, prefix=moved, version=(3, 12, 0))[0],
                         "fail")

    def test_provider_absent(self):
        got, provider = self.checks()
        self.assertEqual(got["provider"], ("ok", "none (standalone)"))
        self.assertEqual(provider, "none")

    def test_provider_in_range(self):
        self.resolved("2.1.0")
        got, provider = self.checks()
        self.assertEqual(got["provider"][0], "ok")
        self.assertEqual(provider, "session 2.1.0, profile p")

    def test_provider_out_of_range(self):
        self.resolved("3.0.0")
        got, provider = self.checks()
        self.assertEqual(got["provider"][0], "warn")
        self.assertIn("running standalone", got["provider"][1])
        self.assertEqual(provider, "none")

    def test_provider_new_folder_else_the_old(self):
        # agentik-r1 c1, ruling 1: the old state folder is read while the new one is absent
        self.resolved("2.1.0", folder=doctor.SESSION_STATE[1])
        got, provider = self.checks()
        self.assertEqual((got["provider"][0], provider), ("ok", "session 2.1.0, profile p"))
        os.makedirs(os.path.join(self.state, doctor.SESSION_STATE[0]))
        self.assertEqual(self.checks()[1], "none")
        self.resolved("2.2.0")
        self.assertEqual(self.checks()[1], "session 2.2.0, profile p")
        self.assertEqual(doctor.SESSION_STATE[0], "agentik-session")

    def test_provider_unparsable_warns(self):
        write(os.path.join(self.state, doctor.SESSION_STATE[0], "sessions", "s1", "resolved.json"),
              "{not json")
        got, provider = self.checks()
        self.assertEqual(got["provider"][0], "warn")
        self.assertEqual(provider, "none")

    def test_ledger_clean(self):
        got = self.checks()[0]["ledger"]
        self.assertEqual(got[0], "ok")
        self.assertIn("9 entries, lint clean", got[1])

    def test_ledger_absent_warns(self):
        os.remove(os.path.join(self.repo, "DECISIONS.md"))
        got = self.checks()[0]["ledger"]
        self.assertEqual(got[0], "warn")
        self.assertIn("no ledger at", got[1])

    def test_ledger_refused_by_the_lint_fails(self):
        with open(os.path.join(self.repo, "DECISIONS.md"), "a", encoding="utf-8") as handle:
            handle.write("\n## Notes\n")
        got = self.checks()[0]["ledger"]
        self.assertEqual(got[0], "fail")
        self.assertIn("1 lint problems (agentik decisions render --lint)", got[1])

    def test_exit_and_json(self):
        write(os.path.join(self.bin, doctor.TOOL), "#!/bin/sh\n", 0o755)
        out = io.StringIO()
        with mock.patch.dict(os.environ, self.env, clear=True), \
                mock.patch.object(sys, "prefix", self.prefix):
            ledger = os.path.join(self.repo, "DECISIONS.md")
            code = decisions.main(["doctor", "--json", "--ledger", ledger], out=out,
                                  err=io.StringIO())
            text_out = io.StringIO()
            self.assertEqual(decisions.main(["--ledger", ledger, "doctor"], out=text_out,
                                            err=io.StringIO()), 0)
        self.assertEqual(code, 0)
        data = json.loads(out.getvalue())
        self.assertEqual([c["name"] for c in data["checks"]],
                         ["python", "tool", "marketplace", "plugin", "provider", "ledger",
                          "respeak"])
        self.assertEqual(data["provider"], "none")
        self.assertTrue(text_out.getvalue().startswith("warn python: newer python available"))

    def test_a_fail_exits_2(self):
        self.prefix = "/usr"
        with mock.patch.dict(os.environ, self.env, clear=True), \
                mock.patch.object(sys, "prefix", self.prefix):
            code = decisions.main(["doctor", "--ledger", os.path.join(self.repo, "DECISIONS.md")],
                                  out=io.StringIO(), err=io.StringIO())
        self.assertEqual(code, 2)


class Range(Hermetic):
    def test_in_range(self):
        for version, want in (("2.0.0-alpha.1", True), ("2.0.0-alpha.2", True),
                              ("2.0.0-beta", True), ("2.0.0", True), ("2.9.9", True),
                              ("2.0.0-alpha.0", False), ("2.0.0-alpha", False),
                              ("1.9.9", False), ("3.0.0", False)):
            with self.subTest(version=version):
                self.assertEqual(in_range(version), want)

    def test_unparsable(self):
        with self.assertRaises(ValueError):
            in_range("2.x")


if __name__ == "__main__":
    unittest.main()
