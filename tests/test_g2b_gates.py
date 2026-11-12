"""g2b (hq design/09 section 7.2): `render` and `answer` name the files they write in the
scope's edit-gates list, once, never one under a `tests`, `testdata` or `fixtures` folder;
the instruct skill's steps 6 and 7 write a gated file through the session plugin's lane."""

import io
import os
import shutil
from unittest import mock

import decisions
from decisions.render import GATES
from tests.test_answer_head import Repo
from tests.test_new import PARTS, SAMPLE_QUESTIONS
from tests.test_new import Base as NewBase
from tests.test_instruct import INSTRUCT, read, split_frontmatter
from tests.test_render import Base


def lines(path):
    with open(path, encoding="utf-8") as handle:
        return [l.strip() for l in handle if l.strip() and not l.startswith("#")]


class RenderLists(Base):

    def setUp(self):
        super().setUp()
        os.mkdir(os.path.join(self.tmp, ".git"))
        self.gates = os.path.join(self.tmp, ".claude", GATES)
        self.user = os.path.join(os.environ["HOME"], ".claude", GATES)

    def test_render_into_twice_lists_its_target_once(self):
        for _ in range(2):
            code, _, err = self.run_cli("--into", self.target)
            self.assertEqual(code, 0, err)
        self.assertEqual(lines(self.gates), ["CLAUDE.md"])
        self.assertFalse(os.path.exists(self.user))

    def test_the_default_target_and_a_sibling_are_listed(self):
        self.assertEqual(self.run_cli()[0], 0)
        self.assertEqual(self.run_cli("--into", os.path.join(self.tmp, "AGENTS.md"))[0], 0)
        self.assertEqual(lines(self.gates), ["CLAUDE.md", "AGENTS.md"])

    def test_a_target_under_tests_fixtures_is_never_listed(self):
        for folder in (("tests", "fixtures"), ("testdata",), ("fixtures", "deep")):
            into = os.path.join(self.tmp, *folder, "CLAUDE.md")
            os.makedirs(os.path.dirname(into))
            code, _, err = self.run_cli("--into", into)
            self.assertEqual(code, 0, err)
            self.assertTrue(os.path.exists(into))
        self.assertFalse(os.path.exists(self.gates))
        self.assertFalse(os.path.exists(self.user))

    def test_check_and_lint_list_nothing(self):
        self.write("x\n")
        self.run_cli("--check")
        self.run_cli("--lint")
        self.assertFalse(os.path.exists(self.gates))

    def test_a_kept_list_keeps_its_lines(self):
        os.makedirs(os.path.dirname(self.gates))
        with open(self.gates, "w", encoding="utf-8") as handle:
            handle.write("# the owner's\nAGENTS.md")
        self.assertEqual(self.run_cli()[0], 0)
        with open(self.gates, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "# the owner's\nAGENTS.md\nCLAUDE.md\n")


class UserList(Base):
    """A file in no checkout (the global file, a tree folder's) goes to the user's list."""

    def into_home(self, env=None):
        home = os.environ["HOME"]
        target = os.path.join(home, ".claude", "CLAUDE.md")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with mock.patch.dict(os.environ, env or {}):
            code, _, err = self.run_cli("--into", target)
        self.assertEqual(code, 0, err)
        return home

    def test_the_global_file_goes_to_the_users_list(self):
        home = self.into_home()
        self.into_home()
        self.assertEqual(lines(os.path.join(home, ".claude", GATES)), ["~/.claude/CLAUDE.md"])

    def test_the_config_dir_moves_the_list(self):
        moved = os.path.join(self.tmp, "moved")
        home = self.into_home({"CLAUDE_CONFIG_DIR": moved})
        self.assertEqual(lines(os.path.join(moved, GATES)), ["~/.claude/CLAUDE.md"])
        self.assertFalse(os.path.exists(os.path.join(home, ".claude", GATES)))

    def test_a_tree_folders_file_outside_home_is_absolute(self):
        code, _, err = self.run_cli()
        self.assertEqual(code, 0, err)
        self.assertEqual(lines(os.path.join(os.environ["HOME"], ".claude", GATES)),
                         [os.path.abspath(self.target)])


class AnswerLists(Repo, NewBase):
    """As test_answer's TurnAnswer sets up: a git repo, its CLAUDE.md rendered, one question."""

    def setUp(self):
        super().setUp()
        shutil.copy(SAMPLE_QUESTIONS, self.questions)
        self.claude = os.path.join(self.tmp, "CLAUDE.md")
        self.write(self.claude, "# Notes\n")
        self.assertEqual(decisions.main(["render", "--ledger", self.ledger], out=io.StringIO(),
                                        err=io.StringIO()), 0)
        argv = list(PARTS)
        argv[argv.index("--title") + 1] = "Pin the interpreter"
        code, _, err = self.run_cli(*argv)
        self.assertEqual(code, 0, err)
        self.commit()
        gates = os.path.join(self.tmp, ".claude", GATES)
        if os.path.exists(gates):
            os.remove(gates)              # what render listed; the answer lists its own

    def answer(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["answer"] + list(argv) + ["--ledger", self.ledger],
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def test_answer_lists_the_ledger_and_its_block(self):
        code, out, err = self.answer("9", "--pick", "pin", "--source", "s", "--text", "Pin it.",
                                     "--area", "Build")
        self.assertEqual(code, 0, err)
        gates = os.path.join(self.tmp, ".claude", GATES)
        self.assertEqual(sorted(lines(gates)), ["CLAUDE.md", "DECISIONS.md"])


class Skill(Base):

    def test_steps_6_and_7_name_the_lane(self):
        front, _ = split_frontmatter(read(INSTRUCT))
        allowed = next(l for l in front if l.startswith("allowed-tools:"))
        self.assertIn("Bash(agentik session gates*)", allowed)
        text = " ".join(read(INSTRUCT).split())
        for needed in ("`agentik session gates write <file> --from <draft> --preview`",
                       "`--expect <hash>`", "sent you here", "asks at once"):
            self.assertIn(needed, text, needed)
        self.assertNotIn("which the guard puts in front of the owner", text)
