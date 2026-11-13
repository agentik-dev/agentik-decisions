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
         "Generated from `DECISIONS.md` by `decisions render`; edit the ledger and rerun it, "
         "never this block.\n"
         "<!-- END GENERATED: decisions -->\n")
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
    """Every file under `root`, `.git` aside, by its path and bytes; a link to nothing by
    what it names."""
    found = {}
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            path = os.path.join(folder, name)
            if not os.path.exists(path):
                found[os.path.relpath(path, root)] = "-> " + os.readlink(path)
                continue
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


class ReviewOne(Base):
    """Review 1's findings, each in its reproduction's shape."""

    def test_f1_another_ledgers_block_is_refused(self):
        os.mkdir(os.path.join(self.repo, "docs"))
        other = os.path.join(self.repo, "docs", "DECISIONS.md")
        with open(self.claude, "w", encoding="utf-8") as handle:
            handle.write("hand line\n")
        with open(other, "w", encoding="utf-8") as handle:
            handle.write(EMPTY)
        for argv in (NEW, ANSWER, ["render", "--into", self.claude]):
            code, _, err = self.run_cli(*(argv + ["--ledger", other]))
            self.assertEqual(code, 0, (argv, err))
        self.assertIn("1. **Indent.**", self.read(self.claude))
        before = snapshot(self.repo)
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 2, out)
        self.assertIn("another ledger's block", err)
        self.assertTrue(err.startswith("decisions: init: "), err)
        self.assertEqual(snapshot(self.repo), before)
        code, _, err = self.run_cli("render", "--check", "--ledger", other, "--into",
                                    self.claude)
        self.assertEqual(code, 0, err)

    def test_f2_a_failed_claude_write_leaves_no_ledger(self):
        ro = os.path.join(self.repo, "ro")
        os.mkdir(ro)
        with open(os.path.join(ro, "shared.md"), "w", encoding="utf-8") as handle:
            handle.write("hand\n")
        os.chmod(ro, 0o555)
        self.addCleanup(os.chmod, ro, 0o755)
        os.symlink(os.path.join("ro", "shared.md"), self.claude)
        before = snapshot(self.repo)
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 2, out)
        self.assertIn("unwritable", err)
        self.assertEqual(out, "")
        self.assertFalse(os.path.lexists(self.ledger))
        self.assertEqual(snapshot(self.repo), before)
        os.chmod(ro, 0o755)
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(self.ledger), EMPTY)
        self.assertEqual(self.read(self.claude), "hand\n\n" + BLOCK)

    def test_f3_a_ledger_named_claude_md_in_any_case(self):
        # by name, never by the disk, so it holds on a case-sensitive disk too
        os.mkdir(os.path.join(self.repo, "docs"))
        for name in ("claude.md", "Claude.MD", os.path.join("docs", "cLaUdE.md")):
            before = snapshot(self.repo)
            code, out, err = self.run_cli("init", "--ledger", name)
            self.assertEqual(code, 2, (name, out))
            self.assertIn("its own CLAUDE.md", err)
            self.assertEqual(snapshot(self.repo), before, name)

    def test_f4_a_folder_named_by_ledger_is_refused(self):
        os.mkdir(os.path.join(self.repo, "docs"))
        for name in ("sub/", "docs", "docs/"):
            before = snapshot(self.repo)
            code, out, err = self.run_cli("init", "--ledger", name)
            self.assertEqual(code, 2, (name, out))
            self.assertIn("folder", err)
            self.assertEqual(snapshot(self.repo), before, name)
            self.assertFalse(os.path.lexists(os.path.join(self.repo, "sub")))
        code, _, err = self.run_cli("show", "1", "--ledger", "sub/")
        self.assertEqual(code, 2)
        self.assertNotIn("init --ledger sub/", err)
        self.assertIn("sub/DECISIONS.md", err)
        code, out, _ = self.run_cli("init", "--help")
        self.assertIn("never a folder", out)

    def test_f5_init_and_the_no_ledger_line_agree(self):
        for kind, make, remove in (
                ("a link to nothing", lambda: os.symlink("gone.md", self.ledger), os.unlink),
                ("a folder", lambda: os.mkdir(self.ledger), os.rmdir)):
            make()
            code, _, shown = self.run_cli("show", "1")
            self.assertEqual(code, 2)
            self.assertIn(kind, shown)
            self.assertIn(INIT, shown)
            before = snapshot(self.repo)
            code, out, err = self.run_cli("init")
            self.assertEqual(code, 2, out)
            self.assertIn(kind, err)
            self.assertNotIn("already", err)
            self.assertIn("move it away", shown)
            self.assertIn("move it away", err)
            self.assertEqual(snapshot(self.repo), before, kind)
            remove(self.ledger)
            code, _, err = self.run_cli("init")
            self.assertEqual(code, 0, err)
            for path in (self.ledger, self.claude, self.gates):
                os.unlink(path)


class ReviewTwo(Base):
    """Review 2's findings, each in its reproduction's shape."""

    def top_holds_entry_one(self):
        with open(self.claude, "w", encoding="utf-8") as handle:
            handle.write("hand line\n")
        for argv in (["init"], NEW, ANSWER):
            code, _, err = self.run_cli(*argv)
            self.assertEqual(code, 0, (argv, err))
        self.assertIn("1. **Indent.**", self.read(self.claude))
        os.mkdir(os.path.join(self.repo, "x"))
        os.symlink(os.path.join("..", "CLAUDE.md"), os.path.join(self.repo, "x", "CLAUDE.md"))
        return os.path.join("x", "DECISIONS.md")

    def test_r2_f1_init_over_a_linked_claude_md_refuses(self):
        named = self.top_holds_entry_one()
        before = snapshot(self.repo)
        code, out, err = self.run_cli("init", "--ledger", named)
        self.assertEqual(code, 2, out)
        self.assertIn("another ledger's block", err)
        self.assertEqual(snapshot(self.repo), before)
        self.assertFalse(os.path.lexists(os.path.join(self.repo, named)))
        self.assertEqual(self.run_cli("render", "--check")[0], 0)

    def test_r2_f1_render_over_a_linked_claude_md_refuses(self):
        named = self.top_holds_entry_one()
        with open(os.path.join(self.repo, named), "w", encoding="utf-8") as handle:
            handle.write(EMPTY)
        before = snapshot(self.repo)
        code, out, err = self.run_cli("render", "--ledger", named)
        self.assertEqual(code, 2, out)
        self.assertIn("another ledger's block", err)
        self.assertEqual(snapshot(self.repo), before)
        self.assertEqual(self.run_cli("render", "--check")[0], 0)

    FENCED = ("# Notes\nThe tool fills a block shaped like this one:\n```\n"
              "<!-- BEGIN GENERATED: decisions -->\nmy own example text, kept by hand\n"
              "<!-- END GENERATED: decisions -->\n```\nLast hand line.\n")
    TILDES = ("\nAnd in tildes:\n~~~ markdown\n<!-- BEGIN GENERATED: decisions -->\n"
              "a second example\n<!-- END GENERATED: decisions -->\n~~~\n")

    def test_r2_f4_init_reads_fenced_markers_as_no_block(self):
        with open(self.claude, "w", encoding="utf-8") as handle:
            handle.write(self.FENCED)
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(self.claude), self.FENCED + "\n" + BLOCK)
        self.assertIn("init: wrote CLAUDE.md: 0 B to 171 B, +171 B;", out)

    def test_r2_f4_render_reads_fenced_markers_as_no_block(self):
        with open(self.claude, "w", encoding="utf-8") as handle:
            handle.write(self.FENCED)
        with open(self.ledger, "w", encoding="utf-8") as handle:
            handle.write(EMPTY)
        code, out, err = self.run_cli("render", "--check")
        self.assertEqual(code, 1, err)
        self.assertNotIn("-my own example text", out)
        code, out, err = self.run_cli("render")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(self.claude), self.FENCED + "\n" + BLOCK)
        self.assertIn("render: wrote CLAUDE.md: 0 B to 171 B, +171 B;", out)

    def test_r2_f4_a_real_block_beside_fenced_examples(self):
        with open(self.claude, "w", encoding="utf-8") as handle:
            handle.write(self.FENCED)
        self.assertEqual(self.run_cli("init")[0], 0)
        with open(self.claude, "a", encoding="utf-8") as handle:
            handle.write(self.TILDES)
        for argv in (NEW, ANSWER):
            code, _, err = self.run_cli(*argv)
            self.assertEqual(code, 0, (argv, err))
        text = self.read(self.claude)
        self.assertTrue(text.startswith(self.FENCED), text)
        self.assertTrue(text.endswith(self.TILDES), text)
        self.assertIn("1. **Indent.** This repo indents with four spaces.", text)
        self.assertEqual(self.run_cli("render", "--check")[0], 0)
        code, out, err = self.run_cli("render", "--lint")
        self.assertEqual(code, 0, err)
        self.assertIn("render: the block for CLAUDE.md is 236 B", out)

    def test_r2_f4_answer_makes_no_block_from_a_fenced_example(self):
        with open(self.claude, "w", encoding="utf-8") as handle:
            handle.write(self.FENCED)
        with open(self.ledger, "w", encoding="utf-8") as handle:
            handle.write(EMPTY)
        for argv in (NEW, ANSWER):
            code, _, err = self.run_cli(*argv)
            self.assertEqual(code, 0, (argv, err))
        self.assertIn("holds no GENERATED markers", err)
        self.assertEqual(self.read(self.claude), self.FENCED)

    def test_r2_f3_a_trailing_slash_on_an_existing_ledger_reads_it(self):
        self.assertEqual(self.run_cli("init")[0], 0)
        for argv in (["render", "--lint"], ["render"], ["doctor"]):
            plain = self.run_cli(*(argv + ["--ledger", "DECISIONS.md"]))
            slash = self.run_cli(*(argv + ["--ledger", "DECISIONS.md" + os.sep]))
            self.assertEqual(slash[0], plain[0], (argv, slash))
            self.assertNotIn("names a folder", slash[1] + slash[2])
        code, out, err = self.run_cli("render", "--ledger", "DECISIONS.md" + os.sep)
        self.assertEqual(code, 0, err)
        self.assertIn("render: CLAUDE.md is fresh", out)
        before = snapshot(self.repo)
        code, out, err = self.run_cli("init", "--ledger", "DECISIONS.md" + os.sep)
        self.assertEqual(code, 2, out)
        self.assertIn("already", err)
        self.assertEqual(snapshot(self.repo), before)
