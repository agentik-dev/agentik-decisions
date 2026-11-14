"""The Makefile's harness (ADV11-1, ADV11-2) and its `decisions` step.

Each test copies `Makefile`, `src/`, `plugin/lib/` and the harness (tests/run.py, gates.py,
skips.allow) into a temp repo and runs `make PY=<this python> <goal>` there.
`test` runs the runner and skip pin extracted at the base: HEAD on main, the
merge base with `main` on a branch, and no `main` is exit 2. Neither the
command line nor the environment moves the base; DECISIONS_BASE is the one
validated pin. `decisions` runs `render --check` when the repo keeps a ledger.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.hermetic import REPO, SAMPLE, Hermetic

PASSING = ("import unittest\n\n\nclass T(unittest.TestCase):\n"
           "    def test_runs(self):\n        self.assertTrue(True)\n")
SKIPPING = ("import unittest\n\n\nclass S(unittest.TestCase):\n"
            "    @unittest.skip('probe')\n    def test_skips(self):\n        pass\n")
FAILING = ("import unittest\n\n\nclass F(unittest.TestCase):\n"
           "    def test_fails(self):\n        self.fail('forged')\n")


class Install(unittest.TestCase):
    """d25: `make install` refuses a dirty tree, then runs the plugin's install-cli under PREFIX,
    by default HOME/.local; a clone of HEAD, a temp HOME, PATH=/usr/bin:/bin."""

    def setUp(self):
        self.t = os.path.realpath(tempfile.mkdtemp(prefix="decisions-install-"))
        self.addCleanup(shutil.rmtree, self.t, True)
        self.clone = os.path.join(self.t, "clone")
        subprocess.run(["git", "clone", "-q", REPO, self.clone], check=True, capture_output=True,
                       timeout=60)
        self.home = os.path.join(self.t, "home")
        os.makedirs(self.home)

    def make(self, *argv):
        return subprocess.run(["make", "-s", "install"] + list(argv), cwd=self.clone,
                              env={"HOME": self.home, "PATH": "/usr/bin:/bin"},
                              capture_output=True, text=True, timeout=120)

    def version(self, launcher):
        return subprocess.run([launcher, "--version"], env={"HOME": self.home, "PATH": "/usr/bin:/bin"},
                              capture_output=True, text=True, timeout=60).stdout

    def test_a_clean_tree_installs_under_home_then_prefix(self):
        run = self.make()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        bindir = os.path.join(self.home, ".local", "bin")
        self.assertTrue(os.path.islink(os.path.join(bindir, "decisions")))
        self.assertTrue(os.access(os.path.join(bindir, "agentik"), os.X_OK))
        self.assertTrue(self.version(os.path.join(bindir, "agentik-decisions")).startswith(
            "agentik-decisions "))
        prefix = os.path.join(self.t, "p")
        run = self.make("PREFIX=" + prefix)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(os.access(os.path.join(prefix, "bin", "agentik-decisions"), os.X_OK))
        self.assertTrue(os.path.isdir(os.path.join(prefix, "share", "agentik-decisions")))

    def test_a_dirty_tree_is_refused_and_writes_nothing(self):
        with open(os.path.join(self.clone, "stray"), "w", encoding="utf-8") as handle:
            handle.write("x\n")
        run = self.make()
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertIn("install: refused", run.stderr)
        self.assertEqual(os.listdir(self.home), [])


class Gate(Hermetic):

    BRANCH = "main"
    # True: the first commit holds no harness, and a second commit adds it
    HARNESS_LATER = False

    def setUp(self):
        super().setUp()
        self.root = tempfile.mkdtemp(prefix="decisions-makefile-")
        self.addCleanup(shutil.rmtree, self.root, True)
        shutil.copy(os.path.join(REPO, "Makefile"), self.root)
        for rel in ("src", os.path.join("plugin", "lib")):
            shutil.copytree(os.path.join(REPO, rel), os.path.join(self.root, rel),
                            ignore=shutil.ignore_patterns("__pycache__"))
        self.git("init", "-q", "-b", self.BRANCH)
        if self.HARNESS_LATER:
            self.commit("base")
        os.makedirs(os.path.join(self.root, "tests"))
        for name in ("run.py", "gates.py"):
            shutil.copy(os.path.join(REPO, "tests", name), os.path.join(self.root, "tests"))
        self.write(os.path.join("tests", "__init__.py"), "")
        self.write(os.path.join("tests", "skips.allow"), "# none\n")
        self.write(os.path.join("tests", "test_tiny.py"), PASSING)
        self.commit("harness")

    def git(self, *argv):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t"] + list(argv),
                              cwd=self.root, check=True, capture_output=True, text=True,
                              timeout=30).stdout.strip()

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def write(self, relpath, text):
        with open(os.path.join(self.root, relpath), "w", encoding="utf-8") as handle:
            handle.write(text)

    def make(self, *argv, env=None):
        environ = dict(os.environ, **(env or {}))
        return subprocess.run(["make", "--no-print-directory", "PY=" + sys.executable]
                              + list(argv), cwd=self.root, capture_output=True, text=True,
                              timeout=120, env=environ)

    def assertRecipe(self, run, code):
        """make exits 2 on any failed recipe; the recipe's own code is in `Error N`."""
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
        self.assertRegex(run.stderr, r"make: \*\*\* \[\w+\] Error %d\n" % code)


class NoMain(Gate):

    BRANCH = "trunk"

    def test_no_main_fails_early(self):
        run = self.make("test")
        self.assertRecipe(run, 2)
        self.assertIn("harness: no merge base with main", run.stderr)
        self.assertNotIn("tests/run.py at", run.stdout)


class OnMain(Gate):

    def test_main_runs_the_harness_at_head(self):
        run = self.make("test")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("test: tests/run.py at %s" % self.git("rev-parse", "HEAD"), run.stdout)


class OverrideIgnored(Gate):

    def setUp(self):
        super().setUp()
        self.git("checkout", "-qb", "work")
        self.base = self.git("rev-parse", "HEAD")

    def test_the_command_line_is_ignored(self):
        run = self.make("-n", "test", "HARNESS_REV=bogus")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertNotIn("bogus", run.stdout)
        self.assertIn('harness="%s"' % self.base, run.stdout)

    def test_the_environment_is_ignored(self):
        run = self.make("-n", "test", env={"HARNESS_REV": "bogus"})
        self.assertNotIn("bogus", run.stdout)


class Harness(Gate):
    """ADV11-1: the base's runner and skip pin over the branch tree."""

    HARNESS_LATER = True

    def setUp(self):
        super().setUp()
        self.git("checkout", "-qb", "work")
        self.base = self.git("rev-parse", "HEAD")

    def forge_runner(self):
        """A branch whose runner passes anything, and a failing test beside it."""
        self.write(os.path.join("tests", "run.py"), "import sys\nsys.exit(0)\n")
        self.write(os.path.join("tests", "test_forged.py"), FAILING)

    def test_a_forged_runner_on_the_branch_reads_red(self):
        self.forge_runner()
        self.commit("forged runner")
        run = self.make("test")
        self.assertRecipe(run, 1)
        self.assertIn("FAILED", run.stderr)

    def test_a_moved_main_under_the_pin_reads_red(self):
        self.forge_runner()
        self.commit("forged")
        self.git("update-ref", "refs/heads/main", "HEAD")
        moved = self.make("test")
        self.assertEqual(moved.returncode, 0, moved.stdout + moved.stderr)
        run = self.make("test", env={"DECISIONS_BASE": self.base})
        self.assertRecipe(run, 1)

    def test_a_pin_off_the_history_is_two(self):
        self.git("checkout", "-q", "--orphan", "side")
        self.commit("off the history")
        side = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "work")
        run = self.make("test", env={"DECISIONS_BASE": side})
        self.assertRecipe(run, 2)
        self.assertIn("DECISIONS_BASE %s is not an ancestor of HEAD" % side, run.stderr)
        bogus = self.make("test", "DECISIONS_BASE=no-such-rev")
        self.assertRecipe(bogus, 2)
        self.assertIn("DECISIONS_BASE no-such-rev is not a commit", bogus.stderr)

    def test_the_base_skip_pin_wins(self):
        green = self.make("test")
        self.assertEqual(green.returncode, 0, green.stdout + green.stderr)
        self.write(os.path.join("tests", "skips.allow"), "1 probe\n")
        self.write(os.path.join("tests", "test_skip.py"), SKIPPING)
        self.commit("raise the pin")
        run = self.make("test")
        self.assertRecipe(run, 1)
        self.assertIn("skips: probe counted 1, pinned 0", run.stdout)

    def test_a_harness_path_absent_at_the_base_is_two(self):
        first = self.git("rev-list", "--max-parents=0", "HEAD")
        run = self.make("test", env={"DECISIONS_BASE": first})
        self.assertRecipe(run, 2)
        self.assertIn("harness: tests/run.py absent at %s" % first, run.stderr)


class DecisionsStep(Gate):
    """`make decisions`: absent ledger says so; fresh is 0; stale is red with the diff."""

    def test_no_ledger(self):
        run = self.make("decisions")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("decisions: no DECISIONS.md, no block to check", run.stdout)

    def test_fresh_then_stale(self):
        shutil.copy(SAMPLE, os.path.join(self.root, "DECISIONS.md"))
        # dc2 R7: init adds the block; render rewrites one that is there
        render = subprocess.run([sys.executable, "src/decisions.py", "init", "--ledger",
                                 "DECISIONS.md"], cwd=self.root, capture_output=True, text=True,
                                timeout=60)
        self.assertEqual(render.returncode, 0, render.stderr)
        fresh = self.make("decisions")
        self.assertEqual(fresh.returncode, 0, fresh.stdout + fresh.stderr)
        self.assertIn("decisions: render --check", fresh.stdout)
        claude = os.path.join(self.root, "CLAUDE.md")
        with open(claude, encoding="utf-8") as handle:
            text = handle.read()
        with open(claude, "w", encoding="utf-8") as handle:
            handle.write(text.replace("- 4 Tests first (Build)\n", ""))
        red = self.make("decisions")
        self.assertRecipe(red, 1)
        self.assertIn("+- 4 Tests first (Build)", red.stdout)
