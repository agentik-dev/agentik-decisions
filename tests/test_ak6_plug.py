"""Packet ak6: `describe`, `describe config` and the plug's shape of `doctor --json` and
`backlog --json`, read through the plugin's own launcher in a temp HOME (acceptance 1 to 8).

Every case runs `plugin/bin/agentik-decisions` with HOME and the `XDG_*` folders under one temp
folder and PATH `/usr/bin:/bin`, so no case reads the live state; the repos are made-up.
"""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest

from decisions import doctor, ledger, tree
from decisions.common import VERSION
from tests.hermetic import REPO, SAMPLE

D = os.path.join(REPO, "plugin", "bin", "agentik-decisions")
NICE = "# Nice to have\n\n- **S3 · tests: a bare item.** One line.\n"
ORDER = ("# Handoff\n\n## Build order\n\n| # | item | level | repo | where | state |\n"
         "|---|---|---|---|---|---|\n| 1 | a step | S3 | orchard | here | open |\n")
DESCRIBE_KEYS = ("schema", "ok", "tool", "version", "summary", "repo", "plugin", "needs", "verbs",
                 "reads")
SETTING_KEYS = {"key", "value", "default", "type", "choices", "summary", "source", "change",
                "live", "values"}
CHANGE_KEYS = {"kind", "command", "path", "block", "note"}
NINE = ["ledger", "respeak.root", "rows.root", "expire.days", "cap.in_force", "ceiling.global",
        "ceiling.tree", "ceiling.hq", "ceiling.repo"]
SUMMARIES = {  # R6, word for word
    "ledger": "The ledger every verb reads: DECISIONS.md at the git top level unless a flag "
              "names another.",
    "respeak.root": "Where `ask` finds respeak to render the owner's questions; without it the "
                    "text stays as written.",
    "rows.root": "The folder `rows` reads each build row's records from.",
    "expire.days": "The age, in days, past which `expire` takes an S4 item on no open step out "
                   "of the list.",
    "cap.in_force": "How many entries a ledger may hold in force before the lint refuses it.",
    "ceiling.global": "The bytes a user's global CLAUDE.md may load before `render --ceiling` "
                      "fails it.",
    "ceiling.tree": "The bytes a tree's CLAUDE.md may load before `render --ceiling` fails it.",
    "ceiling.hq": "The bytes an hq's CLAUDE.md may load before `render --ceiling` fails it.",
    "ceiling.repo": "The bytes a repo's CLAUDE.md may load before `render --ceiling` fails it.",
}


def git(cwd, *argv):
    subprocess.run(["git"] + list(argv), cwd=cwd, check=True, capture_output=True, timeout=30)


class Plug(unittest.TestCase):

    def setUp(self):
        self.t = os.path.realpath(tempfile.mkdtemp(prefix="decisions-ak6-"))
        self.addCleanup(shutil.rmtree, self.t, True)
        self.home = os.path.join(self.t, "home")
        self.env = {"HOME": self.home, "PATH": "/usr/bin:/bin",
                    "XDG_CACHE_HOME": os.path.join(self.home, ".cache"),
                    "XDG_CONFIG_HOME": os.path.join(self.home, ".config"),
                    "XDG_STATE_HOME": os.path.join(self.home, ".local", "state"),
                    "XDG_DATA_HOME": os.path.join(self.home, ".local", "share")}
        os.makedirs(self.home)
        self.repo = os.path.join(self.t, "orchard")
        os.makedirs(os.path.join(self.repo, "history", "rows"))
        git(self.repo, "init", "-q")
        for name in ("DECISIONS.md", "OPEN-QUESTIONS.md"):
            shutil.copy(os.path.join(os.path.dirname(SAMPLE), name), os.path.join(self.repo, name))
        self.put(os.path.join(self.repo, "NICE_TO_HAVE.md"), NICE)
        self.bare = os.path.join(self.t, "loose")
        os.makedirs(self.bare)

    def put(self, path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def run_d(self, *argv, cwd=None, env=None):
        return subprocess.run([D] + list(argv), cwd=cwd or self.repo, env=env or self.env,
                              capture_output=True, timeout=60)

    def answer(self, *argv, cwd=None, env=None, code=0):
        run = self.run_d(*argv, cwd=cwd, env=env)
        self.assertEqual(run.returncode, code, run.stdout + run.stderr)
        self.assertNotIn(b"\x1b", run.stdout)
        self.assertTrue(run.stdout.endswith(b"}\n"), run.stdout)
        return json.loads(run.stdout.decode("utf-8"))

    def config(self, *key, cwd=None, env=None):
        got = self.answer("describe", "config", "--json", *key, cwd=cwd, env=env)
        self.assertEqual(list(got)[:3], ["schema", "ok", "tool"])
        self.assertEqual((got["schema"], got["ok"], got["tool"]), ("agentik.config/1", True,
                                                                   "decisions"))
        self.assertEqual(got["warnings"], [])
        return got


class Describe(Plug):
    """Acceptance 1, and the contract's §7 items 1 and 2."""

    def test_describe_json(self):
        start = time.monotonic()
        got = self.answer("describe", "--json")
        self.assertLess(time.monotonic() - start, 1.0)
        self.assertEqual(list(got), list(DESCRIBE_KEYS))
        self.assertEqual((got["schema"], got["ok"], got["tool"], got["plugin"]),
                         ("agentik.describe/1", True, "decisions", "decisions@agentik"))
        self.assertEqual(got["version"], VERSION)
        self.assertLess(len(got["summary"]), 80)
        self.assertRegex(got["repo"], r"^[a-z0-9-]+/agentik-decisions$")
        self.assertEqual([(n["name"], n["kind"], n["optional"]) for n in got["needs"]],
                         [("git", "program", False), ("respeak@agentik", "plugin", True)])
        names = [v["name"] for v in got["verbs"]]
        self.assertEqual(names[-2:], ["describe", "install-cli"])
        self.assertEqual([v["name"] for v in got["verbs"] if v["top"]], ["rows"])
        for verb in got["verbs"]:
            self.assertEqual(set(verb), {"name", "summary", "top"})
            self.assertTrue(verb["summary"] and ";" not in verb["summary"], verb)
        self.assertEqual([(r["kind"], r["name"], r["argv"]) for r in got["reads"]],
                         [("config", "settings", ["describe", "config", "--json"]),
                          ("doctor", "doctor", ["doctor", "--json"]),
                          ("status", "backlog", ["backlog", "--json"]),
                          ("status", "rows", ["rows", "--json"]),
                          ("status", "questions", ["questions", "--json"])])

    def test_describe_without_json_or_with_another_word_exits_2(self):
        for argv in (["describe"], ["describe", "nosuch", "--json"], ["describe", "config"]):
            with self.subTest(argv=argv):
                run = self.run_d(*argv)
                self.assertEqual((run.returncode, run.stdout), (2, b""))
                lines = run.stderr.decode().splitlines()
                self.assertEqual(len(lines), 1, lines)
                self.assertIn("describe --json", lines[0])

    def test_every_read_prints_schema_and_ok(self):
        for read in self.answer("describe", "--json")["reads"]:
            with self.subTest(read=read["name"]):
                run = self.run_d(*read["argv"])
                self.assertNotEqual(run.returncode, 2, run.stdout + run.stderr)
                got = json.loads(run.stdout.decode("utf-8"))
                self.assertEqual(list(got)[:2], ["schema", "ok"])
                self.assertIs(got["ok"], True)


class Config(Plug):
    """Acceptance 2 to 5, and the contract's §7 items 3, 5 and 9."""

    def test_in_a_repo_with_a_ledger(self):
        got = self.config()
        self.assertEqual(got["layers"], [
            {"name": "default", "path": None, "present": True, "travels": False},
            {"name": "env", "path": None, "present": False, "travels": False}])
        settings = {s["key"]: s for s in got["settings"]}
        self.assertEqual([s["key"] for s in got["settings"]], NINE)
        layers = {layer["name"] for layer in got["layers"]}
        for s in got["settings"]:
            with self.subTest(key=s["key"]):
                self.assertEqual(set(s), SETTING_KEYS)
                self.assertEqual(set(s["change"]), CHANGE_KEYS)
                self.assertEqual(set(s["source"]), {"layer", "path", "line"})
                self.assertIs(s["live"], True)
                self.assertLess(len(s["summary"]), 100)
                self.assertEqual(s["summary"], SUMMARIES[s["key"]])
                self.assertIn(s["source"]["layer"], layers)
                self.assertTrue(all(v["layer"] in layers for v in s["values"]))
                path = s["source"]["path"]
                self.assertFalse(path and path.startswith(self.home), path)
        found = settings["ledger"]
        self.assertEqual(found["value"], os.path.join(self.repo, "DECISIONS.md"))
        self.assertEqual((found["type"], found["default"], found["source"]["layer"],
                          found["change"]["kind"]), ("path", None, "default", "launch"))
        self.assertEqual(found["change"]["command"], "agentik decisions --ledger VALUE show 1")
        self.assertEqual(settings["rows.root"]["value"],
                         os.path.join(self.repo, "history", "rows"))
        days = settings["expire.days"]
        self.assertEqual((days["value"], days["default"], days["type"], days["change"]["command"]),
                         (14, 14, "integer", "agentik decisions expire --days VALUE"))
        cap = settings["cap.in_force"]
        self.assertEqual((cap["value"], cap["default"], cap["change"]["kind"]),
                         (ledger.IN_FORCE_CAP, 25, "fixed"))
        self.assertEqual(cap["change"]["note"], "The figure is the tool's own; a release changes it.")
        for name, (figure, _) in tree.CEILINGS.items():
            ceiling = settings["ceiling." + name]
            self.assertEqual((ceiling["value"], ceiling["default"], ceiling["change"]["kind"]),
                             (figure, figure, "fixed"))

    def test_outside_a_work_tree(self):
        got = self.config(cwd=self.bare)
        settings = {s["key"]: s for s in got["settings"]}
        self.assertEqual(list(settings), NINE)
        self.assertIsNone(settings["ledger"]["value"])
        self.assertIsNone(settings["rows.root"]["value"])

    def test_respeak_root_from_the_variable_and_unset(self):
        root = os.path.join(self.t, "made-up-respeak")
        self.put(os.path.join(root, "scripts", "respeak-render.sh"), "#!/bin/sh\n")
        got = self.config(env=dict(self.env, RESPEAK_ROOT=root))
        found = next(s for s in got["settings"] if s["key"] == "respeak.root")
        self.assertEqual(found["value"], root)
        self.assertEqual(found["source"], {"layer": "env", "path": None, "line": None})
        self.assertEqual(found["values"], [{"layer": "env", "value": root}])
        self.assertIs(next(x for x in got["layers"] if x["name"] == "env")["present"], True)
        found = next(s for s in self.config()["settings"] if s["key"] == "respeak.root")
        self.assertIsNone(found["value"])
        self.assertEqual(found["source"]["layer"], "default")

    def test_a_keyed_read(self):
        got = self.config("expire.days")
        self.assertEqual([s["key"] for s in got["settings"]], ["expire.days"])
        self.assertEqual(len(got["layers"]), 2)
        self.assertEqual(self.config("nosuch")["settings"], [])


class Doctor(Plug):
    """Acceptance 6: the doctor read in the contract's §5 shape; its text and exit stand."""

    def test_doctor_json(self):
        run = self.run_d("doctor", "--json")
        got = json.loads(run.stdout.decode("utf-8"))
        self.assertEqual(list(got), ["schema", "ok", "tool", "failed", "warned", "checks",
                                     "provider"])
        self.assertEqual((got["schema"], got["ok"], got["tool"], got["provider"]),
                         ("agentik.doctor/1", True, "decisions", "none"))
        statuses = [c["status"] for c in got["checks"]]
        self.assertEqual((got["failed"], got["warned"]),
                         (statuses.count("fail"), statuses.count("warn")))
        checks = {c["name"]: c for c in got["checks"]}
        for check in got["checks"]:
            self.assertEqual(list(check), ["name", "status", "detail", "remedy"])
            if check["status"] == "ok":
                self.assertIsNone(check["remedy"], check)
        self.assertEqual(checks["marketplace"]["remedy"], doctor.MARKETPLACE_HINT)
        self.assertEqual(checks["plugin"]["remedy"], doctor.PLUGIN_HINT)
        self.assertEqual(checks["tool"]["status"], "warn")
        self.assertEqual(checks["tool"]["remedy"], "/decisions:install-cli")
        self.assertIsNone(checks["provider"]["remedy"])
        text = self.run_d("doctor")
        self.assertEqual(text.stdout.decode().splitlines(),
                         ["%s %s: %s" % (c["status"], c["name"], c["detail"])
                          for c in got["checks"]])
        self.assertEqual((run.returncode, text.returncode), (2 * bool(got["failed"]),) * 2)

    def test_a_ledger_that_does_not_lint_names_the_lint(self):
        with open(os.path.join(self.repo, "DECISIONS.md"), "a", encoding="utf-8") as handle:
            handle.write("\n## Notes\n")
        run = self.run_d("doctor", "--json")
        got = json.loads(run.stdout.decode("utf-8"))
        found = next(c for c in got["checks"] if c["name"] == "ledger")
        self.assertEqual((run.returncode, found["status"], found["remedy"], got["failed"]),
                         (2, "fail", "agentik decisions render --lint", 1))


class Backlog(Plug):
    """Acceptance 7: both forms open with `schema` and `ok`; the pin's keys follow."""

    def test_backlog_json(self):
        got = self.answer("backlog", ".", "--json")
        self.assertEqual(list(got), ["schema", "ok", "repos", "skipped"])
        self.assertEqual((got["schema"], got["ok"]), ("agentik.decisions.backlog/1", True))
        self.assertEqual([r["repo"] for r in got["repos"]], [self.repo])
        order = os.path.join(self.t, "HANDOFF.md")
        self.put(order, ORDER)
        got = self.answer("backlog", "--json", "--order", order, self.repo)
        self.assertEqual(list(got), ["schema", "ok", "repos", "skipped"])
        self.assertEqual(got["repos"][0]["handoff"], order)

    def test_backlog_check_json(self):
        order = os.path.join(self.repo, "HANDOFF.md")
        self.put(order, ORDER)
        got = self.answer("backlog", "--check", "--order", order, "--json")
        self.assertEqual(list(got), ["schema", "ok", "handoff", "checkout", "rows", "stale",
                                     "written"])
        self.assertEqual(got["schema"], "agentik.decisions.backlog/1")


class ReadOnly(Plug):
    """Acceptance 8: lines 1 to 5 leave HOME outside the cache and the repo as they were."""

    def snapshot(self):
        cache = os.path.join(self.env["XDG_CACHE_HOME"], "agentik")
        found = {}
        for top in (self.home, self.repo):
            for folder, dirs, files in os.walk(top):
                if os.path.realpath(folder) == cache:
                    dirs[:] = []
                    continue
                for name in files + [d for d in dirs if os.path.islink(os.path.join(folder, d))]:
                    path = os.path.join(folder, name)
                    with open(path, "rb") as handle:
                        found[path] = hashlib.sha256(handle.read()).hexdigest()
                found[folder] = "dir"
        return found

    def test_the_reads_write_nothing(self):
        root = os.path.join(self.t, "made-up-respeak")
        self.put(os.path.join(root, "scripts", "respeak-render.sh"), "#!/bin/sh\n")
        self.run_d("--version")   # the cache's bytecode, written once before the snapshot
        before = self.snapshot()
        for argv, env in ((["describe", "--json"], None), (["describe"], None),
                          (["describe", "config", "--json"], None),
                          (["describe", "config", "--json"], dict(self.env, RESPEAK_ROOT=root)),
                          (["describe", "config", "--json", "expire.days"], None),
                          (["describe", "config", "--json", "nosuch"], None)):
            self.run_d(*argv, env=env)
            self.run_d(*argv, env=env, cwd=self.bare)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
