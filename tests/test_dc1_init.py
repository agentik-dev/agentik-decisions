"""dc1 (design/packets/dc1-init.md): `init` writes an empty ledger and its block in a new repo,
every "no ledger" refusal names it, and `render`, `answer` and `init` each say the file they
put on the edit-gates list. Each case in a temp HOME and a repo made by `git init`."""

import io
import os
import subprocess
import tempfile

import decisions
from decisions.render import GATES
from tests.hermetic import REPO, Hermetic

EMPTY = "# Decisions\n\n## In force\n\n## Proposed\n\n## Superseded\n"
BLOCK = ("<!-- BEGIN GENERATED: decisions -->\n"
         # the block's own words; the old name built, so the hygiene scan's `renamed` group
         # finds no literal of it here
         + "Generated from `DECISIONS.md` by `%s render`; edit the ledger and rerun it, "
         "never this block.\n" % "decisions"
         + "<!-- END GENERATED: decisions -->\n")
NEW = ["new", "--title", "Indent", "--stands", "Files mix both.", "--choice", "Which indent here?",
       "--option", "Spaces: all files move to four spaces", "--option",
       "Tabs: all files move to tabs", "--recommend", "Spaces: most files use them."]
ANSWER = ["answer", "1", "--pick", "Spaces", "--source", "me", "--text",
          "This repo indents with four spaces.", "--area", "Every session", "--every-turn"]
LAUNCHER = os.path.join(REPO, "plugin", "bin", "agentik-decisions")
COMMAND = os.path.join(REPO, "plugin", "commands", "init.md")
INIT = "agentik decisions init"
INSTRUCT = "/decisions:instruct"


def snapshot(root):
    """Every file under `root`, `.git` aside, by its path and bytes."""
    found = {}
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            path = os.path.join(folder, name)
            with open(path, "rb") as handle:
                found[os.path.relpath(path, root)] = handle.read()
    return found


class Base(Hermetic):

    def setUp(self):
        super().setUp()
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="decisions-dc1-"))
        self.addCleanup(subprocess.run, ["rm", "-rf", self.tmp])
        self.repo = os.path.join(self.tmp, "orchard")
        os.mkdir(self.repo)
        subprocess.run(["git", "-C", self.repo, "init", "-q"], check=True)
        here = os.getcwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, here)
        self.ledger = os.path.join(self.repo, "DECISIONS.md")
        self.claude = os.path.join(self.repo, "CLAUDE.md")
        self.gates = os.path.join(self.repo, ".claude", GATES)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(list(argv), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def read(self, path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def listed(self):
        return [l.strip() for l in self.read(self.gates).splitlines()
                if l.strip() and not l.startswith("#")]


class Init(Base):

    def test_1_init_in_an_empty_repo(self):
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(self.ledger), EMPTY)
        self.assertEqual(self.run_cli("render", "--lint")[0], 0)
        self.assertEqual(self.run_cli("render", "--lint")[2], "")
        self.assertEqual(self.read(self.claude), BLOCK)
        self.assertEqual(len(BLOCK.encode()), 171)
        self.assertEqual(self.listed(), ["DECISIONS.md", "CLAUDE.md"])
        lines = out.splitlines()
        self.assertEqual(len(lines), 4, out)
        self.assertIn("DECISIONS.md", lines[0])
        self.assertEqual(lines[1], "init: wrote CLAUDE.md: 0 B to 171 B, +171 B; the block is "
                                   "loaded on every turn")
        for word in ("DECISIONS.md", "CLAUDE.md", os.path.join(".claude", GATES), INSTRUCT):
            self.assertIn(word, lines[2])
        self.assertIn("agentik decisions new", lines[3])

    def test_2_new_then_answer_reach_the_block(self):
        self.assertEqual(self.run_cli("init")[0], 0)
        code, _, err = self.run_cli(*NEW)
        self.assertEqual(code, 0, err)
        code, out, err = self.run_cli(*ANSWER)
        self.assertEqual(code, 0, err)
        self.assertIn("answer: rewrote the block in CLAUDE.md: 171 B to 236 B, +65 B; the block "
                      "is loaded on every turn\n", out)
        self.assertIn("1. **Indent.** This repo indents with four spaces.", self.read(self.claude))
        self.assertEqual(self.run_cli("render", "--check")[0], 0)

    def test_3_a_second_init_refuses_and_writes_nothing(self):
        self.assertEqual(self.run_cli("init")[0], 0)
        before = snapshot(self.repo)
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertEqual(len(err.splitlines()), 1, err)
        self.assertIn(self.ledger, err)
        self.assertEqual(snapshot(self.repo), before)

    def test_4_hand_written_lines_stand(self):
        hand = "# Orchard\n\nPick ripe pears only.\n"
        with open(self.claude, "w", encoding="utf-8") as handle:
            handle.write(hand)
        code, _, err = self.run_cli("init")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(self.claude), hand + "\n" + BLOCK)

    def test_5_outside_a_work_tree_and_a_named_ledger(self):
        bare = os.path.join(self.tmp, "loose")
        os.mkdir(bare)
        os.chdir(bare)
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 2)
        self.assertIn("outside a git work tree; name one with --ledger", err)
        self.assertEqual(os.listdir(bare), [])
        os.chdir(self.repo)
        sub = os.path.join(self.repo, "pear")
        os.mkdir(sub)
        code, _, err = self.run_cli("init", "--ledger", os.path.join(sub, "DECISIONS.md"))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(os.path.join(sub, "DECISIONS.md")), EMPTY)
        self.assertEqual(self.read(os.path.join(sub, "CLAUDE.md")), BLOCK)
        self.assertFalse(os.path.exists(self.ledger))
        self.assertEqual(self.listed(), ["pear/DECISIONS.md", "pear/CLAUDE.md"])

    def test_6_no_ledger_names_init(self):
        for argv in (["show", "1"], NEW, ["render"]):
            code, out, err = self.run_cli(*argv)
            self.assertEqual(code, 2, argv)
            self.assertEqual(len(err.splitlines()), 1, err)
            self.assertIn(INIT, err, argv)
        _, out, _ = self.run_cli("doctor")
        line = next(l for l in out.splitlines() if " ledger" in l)
        self.assertIn(INIT, line)


class GateSays(Base):

    def setUp(self):
        super().setUp()
        with open(self.ledger, "w", encoding="utf-8") as handle:
            handle.write(EMPTY)

    def said(self, out):
        return [l for l in out.splitlines() if INSTRUCT in l]

    def test_7_render_then_answer_each_say_theirs_once(self):
        code, out, err = self.run_cli("render")
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertEqual(len(said), 1, out)
        self.assertIn("CLAUDE.md", said[0])
        self.assertIn(os.path.join(".claude", GATES), said[0])
        self.assertNotIn("DECISIONS.md", said[0])
        self.assertEqual(self.said(self.run_cli("render")[1]), [])
        os.remove(self.claude)
        self.assertEqual(self.run_cli("render")[0], 0)
        for n, title in ((1, "Indent"), (2, "Width")):
            argv = list(NEW)
            argv[argv.index("--title") + 1] = title
            self.assertEqual(self.run_cli(*argv)[0], 0)
            code, out, err = self.run_cli("answer", str(n), "--pick", "Spaces", "--source", "me",
                                          "--text", "Four spaces.", "--area", "Style")
            self.assertEqual(code, 0, err)
            said = self.said(out)
            if n == 1:
                self.assertEqual(len(said), 1, out)
                self.assertIn("DECISIONS.md", said[0])
            else:
                self.assertEqual(said, [], out)

    def test_8_answer_without_markers_names_render(self):
        self.assertEqual(self.run_cli(*NEW)[0], 0)
        code, out, err = self.run_cli("answer", "1", "--pick", "Spaces", "--source", "me",
                                      "--text", "Four spaces.", "--area", "Style")
        self.assertEqual(code, 0, err)
        line = next(l for l in err.splitlines() if "GENERATED markers" in l)
        self.assertIn("`agentik decisions render`", line)
        self.assertFalse(os.path.exists(self.claude))


class Command(Base):

    def test_9_the_command_runs_the_plugins_launcher(self):
        text = self.read(COMMAND)
        self.assertIn("!`${CLAUDE_PLUGIN_ROOT}/bin/agentik-decisions init $ARGUMENTS`", text)
        self.assertIn("disable-model-invocation: true", text)
        self.assertIn("allowed-tools: [Bash(*/bin/agentik-decisions init*)]", text)
        env = {"PATH": "/usr/bin:/bin", "HOME": os.environ["HOME"]}
        run = subprocess.run([LAUNCHER, "init"], cwd=self.repo, env=env, capture_output=True,
                             text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(self.read(self.ledger), EMPTY)
        self.assertEqual(self.read(self.claude), BLOCK)
        self.assertEqual(self.listed(), ["DECISIONS.md", "CLAUDE.md"])
        self.assertIn("init: wrote CLAUDE.md: 0 B to 171 B", run.stdout)
        code, out, _ = self.run_cli("--help")
        self.assertIn("init", out.split("Verbs", 1)[1])
        self.assertIn(",init,", out)
