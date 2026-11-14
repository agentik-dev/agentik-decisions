"""fk4: `ask` and the doctor find respeak by the suite's answer, not by the newest
cache folder (packet design/packets/fk4-decisions.md).

Each case builds a made-up home: roots under `<home>/.claude/plugins/cache/<marketplace>/
respeak/<version>/` holding `scripts/respeak-render.sh`, an `installed_plugins.json` beside
the cache, and a stub launcher at `<home>/.local/bin/agentik-suite` that logs its argv and
prints a canned answer. No test starts the real suite or reads the live home.
"""

import io
import json
import os
import time
import unittest
from unittest import mock

import decisions
from decisions import doctor, speak
from tests.hermetic import Hermetic

FORK, OWN = "respeak@acme-tools", "respeak@agentik"
TODAY = ("respeak not found (RESPEAK_ROOT or an installed plugin); optional: "
         "`ask` keeps its text unrendered, every other verb runs the same")
NOT_CHECKED = "not checked: say which with the suite's sources"
HINT = "agentik config suite.sources.respeak"
SOURCE_KEYS = ["kind", "plugin", "root", "version", "declared"]
OK = mock.Mock(return_value=("ok", "fine"))
OTHERS = dict(check_python=OK, check_tool=OK, check_marketplace=OK, check_plugin=OK,
              check_provider=OK, check_ledger=OK)


class Source(Hermetic):

    def setUp(self):
        super().setUp()
        self.home = os.environ["HOME"]
        self.env = {"HOME": self.home, "PATH": "/usr/bin:/bin"}
        self.cache = os.path.join(self.home, ".claude", "plugins", "cache")
        self.log = os.path.join(self.home, "suite.log")
        os.makedirs(self.cache)

    # -- the made-up home ------------------------------------------------------------

    def root(self, marketplace, version):
        root = os.path.join(self.cache, marketplace, "respeak", version)
        os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
        with open(os.path.join(root, speak.RENDER), "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\n")
        return root

    def installed(self, *entries):
        """`installed_plugins.json` with (id, root, version, scope) entries."""
        plugins = {}
        for ident, root, version, scope in entries:
            plugins.setdefault(ident, []).append({"scope": scope, "installPath": root,
                                                  "version": version})
        with open(os.path.join(self.cache, os.pardir, "installed_plugins.json"), "w",
                  encoding="utf-8") as handle:
            json.dump({"version": 2, "plugins": plugins}, handle)

    def stub(self, body):
        """The launcher: logs its argv, then runs `body` (shell)."""
        path = os.path.join(self.home, ".local", "bin", "agentik-suite")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\necho \"$*\" >> '%s'\n%s\n" % (self.log, body))
        os.chmod(path, 0o755)

    def answers(self, row):
        """A stub printing one `agentik.sources/1` answer whose one row is `row`."""
        text = json.dumps({"schema": "agentik.sources/1", "ok": True, "tool": "suite",
                           "tools": [dict({"name": "respeak"}, **row)]})
        answer = os.path.join(self.home, "answer.json")
        with open(answer, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
        self.stub("cat '%s'" % answer)

    def row(self, kind, plugin=None, root=None, version=None, found=True, declared=None,
            seen=()):
        return {"kind": kind, "plugin": plugin, "root": root, "version": version,
                "found": found, "declared": declared, "seen": list(seen)}

    def logged(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as handle:
            return handle.read().splitlines()

    # -- the readers -----------------------------------------------------------------

    def found(self, env=None):
        return speak.respeak_root(env or self.env, self.cache)

    def doctor_json(self, env=None):
        out = io.StringIO()
        with mock.patch.multiple(doctor, **OTHERS), \
                mock.patch.dict(os.environ, env or self.env, clear=True):
            self.assertEqual(decisions.main(["doctor", "--json"], out=out, err=io.StringIO()), 0)
        check, = [c for c in json.loads(out.getvalue())["checks"] if c["name"] == "respeak"]
        return check

    def doctor_text(self, env=None):
        out = io.StringIO()
        with mock.patch.multiple(doctor, **OTHERS), \
                mock.patch.dict(os.environ, env or self.env, clear=True):
            self.assertEqual(decisions.main(["doctor"], out=out, err=io.StringIO()), 0)
        line, = [x for x in out.getvalue().splitlines() if " respeak: " in x]
        return line

    # -- line 1 ----------------------------------------------------------------------

    def test_1_a_fork_at_an_odd_version_stands_by_the_read(self):
        fork = self.root("acme-tools", "0.12.6-acme.1")
        self.installed((FORK, fork, "0.12.6-acme.1", "user"))
        self.answers(self.row("plugin", FORK, fork, "0.12.6-acme.1", seen=[
            {"plugin": FORK, "version": "0.12.6-acme.1", "scope": "user", "root": fork}]))
        self.assertEqual(self.found(), fork)
        self.assertEqual(doctor.check_respeak(self.env)[0], "ok")
        self.assertEqual(self.logged(), ["describe sources --json respeak"] * 2)

    # -- line 2 ----------------------------------------------------------------------

    def test_2_a_fork_keeps_its_name_out_of_the_detail(self):
        fork = self.root("acme-tools", "0.12.6")
        self.installed((FORK, fork, "0.12.6", "user"))
        self.answers(self.row("plugin", FORK, fork, "0.12.6"))
        self.assertEqual(self.found(), fork)
        check = self.doctor_json()
        self.assertEqual(check["status"], "ok")
        self.assertNotIn("acme", check["detail"])
        self.assertNotIn("acme", check["remedy"] or "")
        self.assertEqual(list(check["source"]), SOURCE_KEYS)
        self.assertEqual(check["source"], {"kind": "plugin", "plugin": FORK, "root": fork,
                                           "version": "0.12.6", "declared": None})
        self.assertIn(fork, self.doctor_text())

    def test_2_a_folder_a_line_names_stands(self):
        folder = os.path.join(self.home, "work", "respeak")
        os.makedirs(os.path.join(folder, "scripts"))
        open(os.path.join(folder, speak.RENDER), "w").close()
        declared = {"path": os.path.join(self.home, "suite.toml"), "line": 4}
        self.answers(self.row("folder", None, folder, "0.13.0", declared=declared))
        self.assertEqual(self.found(), folder)
        check = self.doctor_json()
        self.assertEqual((check["status"], check["source"]["kind"]), ("ok", "folder"))
        self.assertNotIn(folder, check["detail"])
        self.assertIn(folder, self.doctor_text())

    # -- line 3 ----------------------------------------------------------------------

    def test_3_a_leftover_folder_reads_absent(self):
        self.root("agentik", "0.12.6")
        self.answers(self.row("absent", found=False))
        self.assertIsNone(self.found())
        self.assertEqual(doctor.check_respeak(self.env), ("warn", TODAY))

    # -- line 4 ----------------------------------------------------------------------

    def test_4_two_installed_and_none_chosen(self):
        own, fork = self.root("agentik", "0.12.6"), self.root("acme-tools", "0.12.7")
        self.installed((OWN, own, "0.12.6", "user"), (FORK, fork, "0.12.7", "user"))
        self.answers(self.row("undecided", found=False, seen=[
            {"plugin": OWN, "version": "0.12.6", "scope": "user", "root": own},
            {"plugin": FORK, "version": "0.12.7", "scope": "user", "root": fork}]))
        self.assertIsNone(self.found())
        check = self.doctor_json()
        self.assertEqual(check["status"], "warn")
        self.assertEqual(check["remedy"], HINT)
        self.assertNotIn("acme", check["detail"])
        self.assertIn("2", check["detail"])

    # -- R6: a line that does not stand ----------------------------------------------

    def test_a_line_whose_plugin_or_folder_is_gone_names_the_line(self):
        declared = {"path": os.path.join(self.home, "suite.toml"), "line": 7}
        for kind, plugin in (("plugin", FORK), ("folder", None)):
            with self.subTest(kind=kind):
                self.answers(self.row(kind, plugin, os.path.join(self.home, "gone"), None,
                                      found=False, declared=declared))
                self.assertIsNone(self.found())
                status, detail = doctor.check_respeak(self.env)
                self.assertEqual(status, "warn")
                self.assertIn("%s:7" % declared["path"], detail)
                self.assertNotIn("acme", detail)

    def test_a_read_naming_a_root_with_no_renderer_gives_none(self):
        bare = os.path.join(self.cache, "acme-tools", "respeak", "0.12.6")
        os.makedirs(bare)
        self.root("agentik", "0.12.6")       # no other folder fills in
        self.answers(self.row("plugin", FORK, bare, "0.12.6"))
        self.assertIsNone(self.found())
        self.assertEqual(doctor.check_respeak(self.env)[0], "warn")

    # -- line 5 ----------------------------------------------------------------------

    def launchers(self):
        """Each launcher whose answer does not count: (name, set it up)."""
        def answer(text):
            path = os.path.join(self.home, "answer.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
            self.stub("cat '%s'" % path)
        good = {"schema": "agentik.sources/1", "ok": True,
                "tools": [self.row("absent", found=False)]}
        return [
            ("no launcher", lambda: None),
            ("exit 2", lambda: self.stub("echo 'usage' >&2; exit 2")),
            ("ok false", lambda: answer(json.dumps(dict(good, ok=False)))),
            ("another schema", lambda: answer(json.dumps(dict(good, schema="agentik.x/1")))),
            ("two rows", lambda: answer(json.dumps(dict(good, tools=good["tools"] * 2)))),
            ("no JSON", lambda: answer("respeak: absent\n")),
            ("exit 1 with an answer", lambda: self.stub("echo '%s'; exit 1" % json.dumps(good))),
            ("sleeps", lambda: self.stub("sleep 30")),
            ("floods", lambda: self.stub("yes '{'")),
        ]

    def homes(self):
        """(name, set it up, the root it gives, the doctor's words)."""
        def alone(version, scope="user"):
            def build():
                fork = self.root("acme-tools", version)
                self.installed((FORK, fork, version, scope))
                return fork
            return build

        def both():
            self.installed((OWN, self.root("agentik", "0.12.6"), "0.12.6", "user"),
                           (FORK, self.root("acme-tools", "0.12.7"), "0.12.7", "managed"))

        return [("the fork at 0.12.6", alone("0.12.6"), True, None),
                ("the fork at 0.12.6-acme.1", alone("0.12.6-acme.1"), True, None),
                ("the fork at scope project", alone("0.12.6", "project"), False, TODAY),
                ("both", both, False, NOT_CHECKED),
                ("a leftover folder", lambda: self.root("agentik", "0.12.6") and None, False,
                 TODAY)]

    def test_5_with_no_answer_the_file_decides(self):
        for launcher, set_launcher in self.launchers():
            for home, build, gives, words in self.homes():
                with self.subTest(launcher=launcher, home=home), \
                        mock.patch.object(speak, "SOURCES_WALL", 1), \
                        mock.patch.object(speak, "SOURCES_BYTES", 1 << 16):
                    self.reset()
                    want = build()
                    set_launcher()
                    start = time.monotonic()
                    self.assertEqual(self.found(), want if gives else None)
                    status, detail = doctor.check_respeak(self.env)
                    self.assertLess(time.monotonic() - start, 6)
                    self.assertEqual(status, "ok" if gives else "warn")
                    if words == TODAY:
                        self.assertEqual(detail, TODAY)
                    elif words:
                        self.assertIn(words, detail)
                        self.assertNotIn("acme", detail)

    def reset(self):
        import shutil
        for path in (os.path.join(self.home, ".claude"), os.path.join(self.home, ".local"),
                     self.log):
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
        os.makedirs(self.cache)

    # -- line 6 ----------------------------------------------------------------------

    def test_6_the_variable_first_and_said(self):
        mine = os.path.join(self.home, "mine")
        os.makedirs(os.path.join(mine, "scripts"))
        open(os.path.join(mine, speak.RENDER), "w").close()
        bare = os.path.join(self.home, "bare")
        os.makedirs(bare)
        for home, build, _gives, _words in self.homes():
            with self.subTest(home=home):
                self.reset()
                build()
                self.answers(self.row("absent", found=False))
                env = dict(self.env, RESPEAK_ROOT=mine)
                self.assertEqual(self.found(env), mine)
                status, detail = doctor.check_respeak(env)
                self.assertEqual(status, "ok")
                self.assertIn(mine, detail)
                self.assertIn("RESPEAK_ROOT", detail)
                self.assertIsNone(self.doctor_json(env)["source"])
                self.assertIsNone(self.found(dict(self.env, RESPEAK_ROOT=bare)))
                self.assertEqual(doctor.check_respeak(dict(self.env, RESPEAK_ROOT=bare)),
                                 ("warn", TODAY))
                self.assertEqual(self.logged(), [])

    # -- line 7 ----------------------------------------------------------------------

    def test_7_our_own_alone_by_the_read_and_by_the_file(self):
        own = self.root("agentik", "0.12.6")
        self.installed((OWN, own, "0.12.6", "user"))
        for how in ("read", "file"):
            with self.subTest(how=how):
                if how == "read":
                    self.answers(self.row("own", OWN, own, "0.12.6"))
                else:
                    os.remove(os.path.join(self.home, ".local", "bin", "agentik-suite"))
                self.assertEqual(self.found(), own)
                self.assertEqual(doctor.check_respeak(self.env), ("ok", own))
                check = self.doctor_json()
                self.assertEqual((check["detail"], check["source"]), (own, None))

    # -- review 1 --------------------------------------------------------------------

    def test_r1f1_describe_config_starts_the_launcher_once(self):
        from decisions import plug
        own = self.root("agentik", "0.12.6")
        self.answers(self.row("own", OWN, own, "0.12.6"))
        mine = os.path.join(self.home, "mine")
        os.makedirs(os.path.join(mine, "scripts"))
        open(os.path.join(mine, speak.RENDER), "w").close()
        for env, want in ((self.env, own), (dict(self.env, RESPEAK_ROOT=mine), mine)):
            with self.subTest(variable="RESPEAK_ROOT" in env):
                if os.path.exists(self.log):
                    os.remove(self.log)
                setting, = plug.config("respeak.root", cwd=self.home, env=env)["settings"]
                self.assertEqual(setting["value"], want)
                self.assertEqual(setting["values"][0], {"layer": "default", "value": own})
                self.assertEqual(self.logged(), ["describe sources --json respeak"])

    # -- line 8 ----------------------------------------------------------------------

    def test_8_the_newest_folder_rule_is_gone(self):
        self.assertFalse(hasattr(speak, "newest_root"))
        self.assertFalse(hasattr(speak, "version_key"))
        self.assertNotIn("newest_root", speak.__all__)
        self.assertNotIn("version_key", speak.__all__)


if __name__ == "__main__":
    unittest.main()
