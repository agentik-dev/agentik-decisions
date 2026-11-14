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
# dc2 R7: render rewrites a block that is there, so a file render writes holds these first
MARKED = BLOCK.splitlines(keepends=True)[0] + BLOCK.splitlines(keepends=True)[-1]


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
        with open(self.claude, "w", encoding="utf-8") as handle:
            handle.write(MARKED)
        code, out, err = self.run_cli("render")
        self.assertEqual(code, 0, err)
        said = self.said(out)
        self.assertEqual(len(said), 1, out)
        self.assertIn("CLAUDE.md", said[0])
        self.assertIn(os.path.join(".claude", GATES), said[0])
        self.assertNotIn("DECISIONS.md", said[0])
        self.assertEqual(self.said(self.run_cli("render")[1]), [])
        with open(self.claude, "w", encoding="utf-8") as handle:
            handle.write(MARKED)
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

    def test_8_answer_without_markers_names_init(self):
        self.assertEqual(self.run_cli(*NEW)[0], 0)
        code, out, err = self.run_cli("answer", "1", "--pick", "Spaces", "--source", "me",
                                      "--text", "Four spaces.", "--area", "Style")
        self.assertEqual(code, 0, err)
        line = next(l for l in err.splitlines() if "GENERATED markers" in l)
        self.assertIn("`agentik decisions init` adds it", line)  # dc2 R5
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
            handle.write("hand line\n\n" + MARKED)
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
        code, out, err = self.run_cli("init")  # dc2 R7: the append is init's
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(self.claude), self.FENCED + "\n" + BLOCK)
        self.assertIn("init: wrote CLAUDE.md: 0 B to 171 B, +171 B;", out)

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

    def test_r2_f2_a_dot_part_or_a_step_out_of_nothing_refuses(self):
        dotted = (os.path.join("sub", "."), os.path.join("sub", ".."),
                  os.path.join("gone", "..", "sub"))
        for made in (False, True):
            if made:
                os.mkdir(os.path.join(self.repo, "sub"))
            for name in dotted:
                before = snapshot(self.repo)
                code, out, err = self.run_cli("init", "--ledger", name)
                self.assertEqual(code, 2, (name, out))
                self.assertTrue(err.startswith("decisions: no ledger: --ledger "), err)
                self.assertEqual(snapshot(self.repo), before, name)
                self.assertFalse(os.path.isfile(os.path.join(self.repo, "sub")), name)
                self.assertFalse(os.path.lexists(self.ledger), name)
        self.assertEqual(self.run_cli("init")[0], 0)
        self.assertEqual(self.run_cli("show", "1", "--ledger", dotted[0])[0], 2)
        os.mkdir(os.path.join(self.repo, "docs"))
        code, _, err = self.run_cli("render", "--lint", "--ledger",
                                    os.path.join("docs", "..", "DECISIONS.md"))
        self.assertEqual(code, 0, err)


MARK_BEGIN = BLOCK.splitlines()[0]
MARK_END = BLOCK.splitlines()[-1]


def outside_closed_fences(text):
    """(BEGIN lines, END lines) of `text` outside a closed code fence, by a scan of its own:
    fence lines pair up in turn by their mark, and a last one with no partner is no fence."""
    lines = text.splitlines()
    spans, held = [], {}
    for i, line in enumerate(lines):
        stripped = line.lstrip(" ")
        if len(line) - len(stripped) <= 3 and stripped[:3] in ("```", "~~~"):
            mark = stripped[0]
            if mark in held:
                spans.append((held.pop(mark), i))
            elif not held:
                held[mark] = i
    inside = {i for a, b in spans for i in range(a, b + 1)}
    return ([i for i, l in enumerate(lines) if l.strip() == MARK_BEGIN and i not in inside],
            [i for i, l in enumerate(lines) if l.strip() == MARK_END and i not in inside])


class ReviewThree(Base):
    """R3-F1: a code fence that never closes fences nothing, so the block below it is seen."""

    OPEN = "# Hand\n```\nnever closed\n"
    FOUR = "# Hand\n````\n```\n````\n"
    TILDE = "# Hand\n~~~\nnever closed\n"
    OPEN_PAIR = "# Hand\n```\n" + MARK_BEGIN + "\nan example\n" + MARK_END + "\nnever closed\n"
    CLOSED_PAIR = "# Hand\n```\n" + MARK_BEGIN + "\nan example\n" + MARK_END + "\n```\ntext\n"
    COMMENT = "# Hand\n<!-- never closed\nmore\n"

    def put(self, hand, real=True):
        with open(self.claude, "w", encoding="utf-8") as handle:
            handle.write(hand + ("\n" + BLOCK if real else ""))
        with open(self.ledger, "w", encoding="utf-8") as handle:
            handle.write(EMPTY)

    def kept_whole(self, hand):
        """`render` twice: the second says fresh, the bytes are the same, one block shows."""
        self.put(hand)
        first = self.run_cli("render")
        self.assertEqual(first[0], 0, first)
        once = self.read(self.claude)
        code, out, err = self.run_cli("render")
        self.assertEqual(code, 0, err)
        self.assertIn("render: CLAUDE.md is fresh", out)
        self.assertEqual(self.read(self.claude), once)
        begins, ends = outside_closed_fences(once)
        self.assertEqual((len(begins), len(ends)), (1, 1), once)
        self.assertEqual(once, hand + "\n" + BLOCK)
        before = snapshot(self.repo)
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 2, out)
        self.assertIn("already", err)
        self.assertEqual(snapshot(self.repo), before)
        # init where the ledger is gone: the one block is found, not another appended
        os.remove(self.ledger)
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(self.claude), once)

    def test_r3_f1_an_open_backtick_fence_hides_nothing(self):
        self.kept_whole(self.OPEN)

    def test_r3_f1_a_four_backtick_fence_over_one_three_backtick_line(self):
        self.kept_whole(self.FOUR)

    def test_r3_f1_an_open_tilde_fence_hides_nothing(self):
        self.kept_whole(self.TILDE)

    def test_r3_f1_hand_text_alone_gets_one_block_from_init_and_render(self):
        for hand in (self.OPEN, self.FOUR, self.TILDE):
            for name in os.listdir(self.repo):
                if name != ".git":
                    path = os.path.join(self.repo, name)
                    subprocess.run(["rm", "-rf", path])
            with open(self.claude, "w", encoding="utf-8") as handle:
                handle.write(hand)
            code, out, err = self.run_cli("init")
            self.assertEqual(code, 0, err)
            once = self.read(self.claude)
            self.assertEqual(once, hand + "\n" + BLOCK)
            code, out, err = self.run_cli("render")
            self.assertEqual(code, 0, err)
            self.assertIn("render: CLAUDE.md is fresh", out)
            self.assertEqual(self.read(self.claude), once)

    def test_r3_f1_an_open_fence_over_an_example_pair_and_a_block_refuses(self):
        # as at 10f2c5d: no fence is open, so two blocks stand and nothing is written
        self.put(self.OPEN_PAIR)
        before = snapshot(self.repo)
        for argv in (["render"], ["render", "--check"]):
            code, out, err = self.run_cli(*argv)
            self.assertEqual(code, 2, (argv, out))
            self.assertIn("not one BEGIN before one END", err)
            self.assertEqual(snapshot(self.repo), before)
        self.assertEqual(outside_closed_fences(self.read(self.claude)),
                         ([2, 7], [4, 9]))

    def test_r3_f1_a_closed_fence_with_an_example_pair_stays_an_example(self):
        self.kept_whole(self.CLOSED_PAIR)
        self.assertEqual(self.read(self.claude).count(MARK_BEGIN), 2)

    def test_r3_f1_an_unclosed_html_comment_over_the_block_is_as_at_10f2c5d(self):
        # 10f2c5d: `markers` had no comment, the block was seen, `render` read it fresh;
        # `outside_lines` skips a line in an open comment and reads the same block
        self.kept_whole(self.COMMENT)
        from decisions.tree import markers, outside_lines
        text = self.read(self.claude)
        self.assertEqual(markers(text.splitlines(), MARK_BEGIN, MARK_END), ([4], [6]))
        self.assertEqual(outside_lines(text, MARK_BEGIN, MARK_END), [(1, "# Hand")])

    def test_r3_f1_outside_lines_reads_an_open_fence_as_none(self):
        from decisions.tree import outside_lines
        hand = "# Hand\n```\nnever closed\n"
        self.assertEqual([n for n, _ in outside_lines(hand + "\n" + BLOCK, MARK_BEGIN,
                                                      MARK_END)], [1, 2, 3])
        closed = "# Hand\n```\nshown\n```\nafter\n"
        self.assertEqual([n for n, _ in outside_lines(closed + "\n" + BLOCK, MARK_BEGIN,
                                                      MARK_END)], [1, 5])

    def test_r3_f1_backstop_refuses_a_text_that_holds_not_one_block(self):
        import decisions.init
        import decisions.render
        self.put("# Hand\n\n" + MARKED, real=False)  # dc2 R7: a block there to rewrite
        real = decisions.render.apply

        def twice(text, generated, target=None):
            return real(text, generated, target) + generated

        for module, argv in ((decisions.render, ["render"]), (decisions.init, ["init"])):
            if argv == ["init"]:
                os.remove(self.ledger)
            before = snapshot(self.repo)
            held = module.apply
            module.apply = lambda text, generated, target=None: (
                twice(text, generated, target) if generated else real(text, generated, target))
            try:
                code, out, err = self.run_cli(*argv)
            finally:
                module.apply = held
            self.assertEqual(code, 2, (argv, out))
            self.assertIn("CLAUDE.md: its block could not be placed", err)
            self.assertIn("a code fence left open above it", err)
            self.assertIn("nothing written", err)
            self.assertEqual(snapshot(self.repo), before, argv)
