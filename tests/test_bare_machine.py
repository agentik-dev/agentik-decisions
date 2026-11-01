"""Packet d25: the plugin on a bare machine (hq design/04 section 7's test, item 5).

`git archive HEAD plugin`, the whole plugin, goes into a temp home as a marketplace's cache would
hold it, and runs with the env exactly HOME, PATH=/usr/bin:/bin, CLAUDE_PLUGIN_ROOT and
CLAUDE_PLUGIN_DATA, from a temp git repo whose cwd holds a decoy package: no clone path, no venv,
no launcher. The verbs go through plugin/bin/agentik-decisions; then install-cli writes a
launcher under the temp home, never the real one.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

from tests.hermetic import REPO, SAMPLE

ASK_LINE = "ask: no respeak (RESPEAK_ROOT or an installed plugin); the questions stay as written\n"
NICE = "# Nice to have\n\n- **S3 · tests: a bare item.** One line.\n"


class BareMachine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.t = os.path.realpath(tempfile.mkdtemp(prefix="decisions-bare-"))
        cls.addClassCleanup(shutil.rmtree, cls.t, True)
        manifest = subprocess.run(["git", "show", "HEAD:plugin/.claude-plugin/plugin.json"],
                                  cwd=REPO, check=True, capture_output=True, text=True).stdout
        cls.version = json.loads(manifest)["version"]
        cls.plugin = os.path.join(cls.t, ".claude", "plugins", "cache", "agentik", "decisions",
                                  cls.version)
        os.makedirs(cls.plugin)
        tar = subprocess.run(["git", "archive", "HEAD", "plugin"], cwd=REPO, check=True,
                             capture_output=True).stdout
        subprocess.run(["tar", "-x", "--strip-components", "1", "-C", cls.plugin], input=tar,
                       check=True)
        cls.data = os.path.join(cls.t, ".claude", "plugins", "data", "decisions-agentik")
        os.makedirs(cls.data)
        cls.repo = os.path.join(cls.t, "repo")
        os.makedirs(os.path.join(cls.repo, "decisions"))
        subprocess.run(["git", "init", "-q"], cwd=cls.repo, check=True, env=cls.env())
        # the sample ledger and its questions file, so the lint holds before and after
        for name in ("DECISIONS.md", "OPEN-QUESTIONS.md"):
            shutil.copy(os.path.join(os.path.dirname(SAMPLE), name), os.path.join(cls.repo, name))
        with open(os.path.join(cls.repo, "NICE_TO_HAVE.md"), "w", encoding="utf-8") as handle:
            handle.write(NICE)
        # the decoys: -I keeps the cwd off sys.path, so neither may ever load
        for rel in (os.path.join("decisions", "__init__.py"), "agentik_install.py"):
            with open(os.path.join(cls.repo, rel), "w", encoding="utf-8") as handle:
                handle.write("raise SystemExit('decoy %s imported')\n" % rel)

    @classmethod
    def env(cls):
        return {"HOME": cls.t, "PATH": "/usr/bin:/bin", "CLAUDE_PLUGIN_ROOT": cls.plugin,
                "CLAUDE_PLUGIN_DATA": cls.data}

    def tool(self, *argv, exe=None):
        return subprocess.run([exe or os.path.join(self.plugin, "bin", "agentik-decisions")]
                              + list(argv), cwd=self.repo, env=self.env(), capture_output=True,
                              text=True, timeout=60)

    def ok(self, run):
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertNotIn("decoy", run.stdout + run.stderr)
        return run

    def test_1_the_verbs_through_the_plugins_launcher(self):
        self.assertIn("**Plain words.**", self.ok(self.tool("show", "1")).stdout)
        self.assertEqual(self.ok(self.tool("find", "Plain")).stdout,
                         "1 Plain words (Every session)\n")
        made = self.ok(self.tool("new", "--title", "Bare", "--stands", "s", "--choice", "c?",
                                 "--option", "A: a.", "--option", "B: b.",
                                 "--recommend", "Yes."))
        number = re.search(r"\b(\d+)\b", made.stdout).group(1)
        asked = self.ok(self.tool("ask"))
        self.assertTrue(asked.stderr.endswith(ASK_LINE), asked.stderr)
        self.assertIn('"header": "Decision %s"' % number, asked.stdout)
        self.ok(self.tool("answer", number, "--pick", "A (Recommended)", "--source", "the bare test",
                          "--text", "Bare holds.", "--area", "build"))
        self.assertIn("Bare holds.", self.ok(self.tool("show", number)).stdout)
        self.ok(self.tool("render"))
        self.ok(self.tool("render", "--check"))
        self.assertIn("bare item", self.ok(self.tool("backlog")).stdout)
        self.assertEqual(self.ok(self.tool("--version")).stdout,
                         "agentik-decisions %s\n" % self.version)

    def test_2_install_cli_under_the_temp_home(self):
        self.ok(self.tool("install-cli"))
        bindir = os.path.join(self.t, ".local", "bin")
        launcher = os.path.join(bindir, "agentik-decisions")
        alias = os.path.join(bindir, "decisions")
        self.assertTrue(os.path.islink(alias))
        self.assertEqual(os.path.realpath(alias), os.path.realpath(launcher))
        with open(launcher, encoding="utf-8") as handle:
            self.assertIn("\nVERSION=%s\n" % self.version, handle.read())
        for exe in (launcher, alias):
            self.assertEqual(self.ok(self.tool("--version", exe=exe)).stdout,
                             "agentik-decisions %s\n" % self.version)
        self.assertIn("**Plain words.**", self.ok(self.tool("show", "1", exe=launcher)).stdout)
        self.assertTrue(os.access(os.path.join(bindir, "agentik"), os.X_OK))
        # no clone path anywhere the install wrote
        for top, _dirs, files in os.walk(os.path.join(self.t, ".local")):
            for name in files:
                path = os.path.join(top, name)
                if not os.path.islink(path):
                    with open(path, "rb") as handle:
                        self.assertNotIn(REPO.encode(), handle.read(), path)


if __name__ == "__main__":
    unittest.main()
