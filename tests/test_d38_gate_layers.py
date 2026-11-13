"""d38 (agentik-hq entry 31): `list_gate` writes the layer a target belongs to (its
checkout's list, the owner's for a file under the config folder, else the list of a folder
below the home folder, else the owner's); `render --lint` warns, its exit unchanged, on a
checkout's line that reaches outside it and on an owner's line that a lower layer owns; a
new list's header names no hq and no design record. Every file is under the temp home."""

import io
import os
import shutil
from unittest import mock

import decisions
from decisions.render import GATES
from tests.hermetic import SAMPLE, Hermetic
from tests.test_tree_scope import Tree


def lines(path):
    with open(path, encoding="utf-8") as handle:
        return [l.strip() for l in handle if l.strip() and not l.startswith("#")]


def lists_under(root):
    return sorted(os.path.join(d, n) for d, _, names in os.walk(root) for n in names
                  if n == GATES)


class FolderLayer(Tree):
    """Acceptance 1: a tree folder's file goes to that folder's list, relative to it."""

    def test_scope_tree_lists_the_folders_file_in_the_folders_list(self):
        for _ in range(2):
            code, _, err = self.render("--scope", "tree", "--into", self.target)
            self.assertEqual(code, 0, err)
        self.assertEqual(lines(os.path.join(self.folder, ".claude", GATES)), ["CLAUDE.md"])
        self.assertFalse(os.path.exists(os.path.join(self.home, ".claude", GATES)))

    def test_scope_tree_lint_warns_on_the_owners_copy(self):
        self.assertEqual(self.render("--scope", "tree", "--into", self.target)[0], 0)
        owner = os.path.join(self.home, ".claude", GATES)
        os.makedirs(os.path.dirname(owner), exist_ok=True)
        with open(owner, "w", encoding="utf-8") as handle:
            handle.write("~/work/orchard/CLAUDE.md\n")
        code, _, err = self.render("--scope", "tree", "--lint")
        self.assertEqual(code, 0, err)
        self.assertEqual(len([l for l in err.splitlines() if GATES in l]), 1, err)


class Home(Hermetic):
    """A checkout two folders below the temp home, its ledger the sample."""

    def setUp(self):
        super().setUp()
        self.home = os.environ["HOME"]
        self.repo = os.path.join(self.home, "work", "orchard", "pear")
        os.makedirs(os.path.join(self.repo, ".git"))
        self.ledger = os.path.join(self.repo, "DECISIONS.md")
        shutil.copy(SAMPLE, self.ledger)
        self.owner = os.path.join(self.home, ".claude", GATES)

    def render(self, *argv, ledger=None):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["render"] + list(argv) + ["--ledger", ledger or self.ledger],
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()


class Layers(Home):
    """Acceptance 2 and 6: the checkout's and the owner's lists as at the pin, fixtures
    nowhere, and a new list's header names no hq."""

    def test_a_checkout_keeps_its_own_list(self):
        self.assertEqual(self.render()[0], 0)
        self.assertEqual(lists_under(self.home), [os.path.join(self.repo, ".claude", GATES)])
        self.assertEqual(lines(os.path.join(self.repo, ".claude", GATES)), ["CLAUDE.md"])

    def test_the_config_folder_keeps_the_owners_list(self):
        target = os.path.join(self.home, ".claude", "CLAUDE.md")
        os.makedirs(os.path.dirname(target))
        self.assertEqual(self.render("--into", target)[0], 0)
        self.assertEqual(lists_under(self.home), [self.owner])
        self.assertEqual(lines(self.owner), ["~/.claude/CLAUDE.md"])

    def test_the_home_folders_own_file_goes_to_the_owners_list(self):
        self.assertEqual(self.render("--into", os.path.join(self.home, "CLAUDE.md"))[0], 0)
        self.assertEqual(lines(self.owner), ["~/CLAUDE.md"])

    def test_a_fixture_in_no_checkout_is_listed_nowhere(self):
        into = os.path.join(self.home, "work", "tests", "fixtures", "CLAUDE.md")
        os.makedirs(os.path.dirname(into))
        self.assertEqual(self.render("--into", into)[0], 0)
        self.assertEqual(lists_under(self.home), [])

    def test_a_new_lists_header_names_no_hq(self):
        self.assertEqual(self.render()[0], 0)
        with open(os.path.join(self.repo, ".claude", GATES), encoding="utf-8") as handle:
            head = [l for l in handle if l.startswith("#")]
        self.assertTrue(head)
        self.assertNotIn("hq", "".join(head).lower())
        self.assertNotIn("design/", "".join(head))


class Lint(Home):
    """Acceptance 3 to 5: the two warnings, one a line, and the exit as at the pin."""

    HEAD = "# a hand comment naming ../x and /y\n"

    def lint(self):
        code, _, err = self.render("--lint")
        return code, [l for l in err.splitlines() if GATES in l]

    def put(self, path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(self.HEAD + text)

    def test_a_checkouts_list_reaching_out_warns_once_a_line(self):
        os.makedirs(os.path.join(os.path.dirname(self.repo), "plum"))
        before = self.render("--lint")[0]
        self.put(os.path.join(self.repo, ".claude", GATES),
                 "CLAUDE.md\n../plum/CLAUDE.md\n/abs/x\n~/x\nplum/x\ndocs/*.md\n")
        code, warned = self.lint()
        self.assertEqual(code, before)
        self.assertEqual(len(warned), 4, warned)
        for n, word in zip((3, 4, 5, 6), ("../plum/CLAUDE.md", "/abs/x", "~/x", "plum/x")):
            self.assertTrue(any(":%d:" % n in w and word in w for w in warned), (n, warned))

    def test_a_clean_checkout_list_warns_nothing(self):
        os.makedirs(os.path.join(self.repo, "plum"))
        os.makedirs(os.path.join(os.path.dirname(self.repo), "plum"))
        self.put(os.path.join(self.repo, ".claude", GATES), "CLAUDE.md\nplum/x\n")
        self.assertEqual(self.lint()[1], [])

    def test_the_owners_list_warns_on_a_lower_layers_file(self):
        before = self.render("--lint")[0]
        os.makedirs(os.path.join(self.home, "notes", "deep"))
        self.put(os.path.join(self.home, "notes", ".claude", GATES), "*/CLAUDE.md\n")
        self.put(self.owner, "~/.claude/CLAUDE.md\n~/.claude/hooks/**\n"
                 "~/work/orchard/pear/AGENTS.md\n~/notes/deep/CLAUDE.md\n~/elsewhere/x\n")
        code, warned = self.lint()
        self.assertEqual(code, before)
        self.assertEqual(len(warned), 2, warned)
        self.assertTrue(any(":4:" in w and "pear/AGENTS.md" in w for w in warned), warned)
        self.assertTrue(any(":5:" in w and "notes/deep" in w for w in warned), warned)

    def test_the_moved_config_folder_is_the_owners(self):
        moved = os.path.join(self.home, "conf")
        self.put(os.path.join(moved, GATES), "~/conf/CLAUDE.md\n~/work/orchard/pear/x\n")
        self.put(self.owner, "~/work/orchard/pear/y\n")
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": moved}):
            warned = self.lint()[1]
        self.assertEqual(len(warned), 1, warned)
        self.assertIn("pear/x", warned[0])

    def test_no_list_no_warning(self):
        self.assertEqual(self.lint()[1], [])
        self.put(self.owner, "~/work/orchard/pear/x\n")
        self.assertEqual(len(self.lint()[1]), 1)


class Round1(Home):
    """d38 r1: F1, a NUL in a list changes neither `--lint`'s exit nor raises; F2, a list
    that cannot be written is one warning and the render's own exit; the symlink note, the
    checkout is found from the target's real path."""

    def put(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(data)

    def test_f1_a_nul_in_either_list_drops_that_line_only(self):
        before = self.render("--lint")[0]
        self.put(self.owner, b"~/work/orchard/pear/x\x00y\n~/work/orchard/pear/z\n")
        self.put(os.path.join(self.repo, ".claude", GATES), b"/abs\x00x\nCLAUDE.md\n")
        code, _, err = self.render("--lint")
        self.assertEqual(code, before, err)
        warned = [l for l in err.splitlines() if GATES in l]
        self.assertEqual(len(warned), 1, err)
        self.assertIn("pear/z", warned[0])

    def test_f2_a_folder_list_that_cannot_be_made_warns_and_exits_0(self):
        folder = os.path.join(self.home, "work", "blocked")
        self.put(os.path.join(folder, ".claude"), b"")
        target = os.path.join(folder, "CLAUDE.md")
        code, out, err = self.render("--into", target)
        self.assertEqual(code, 0, err)
        self.assertIn("render: wrote", out)
        self.assertTrue(os.path.exists(target))
        warned = [l for l in err.splitlines() if "warning" in l]
        self.assertEqual(len(warned), 1, err)
        self.assertIn(os.path.join("blocked", ".claude", GATES), warned[0])

    def test_f2_a_checkout_list_that_cannot_be_made_warns_and_exits_0(self):
        self.put(os.path.join(self.repo, ".claude"), b"")
        code, _, err = self.render()
        self.assertEqual(code, 0, err)
        self.assertEqual(len([l for l in err.splitlines() if "warning" in l]), 1, err)

    def test_a_link_into_a_checkout_lists_at_its_top_level(self):
        os.makedirs(os.path.join(self.repo, "sub"))
        link = os.path.join(self.home, "link")
        os.symlink(os.path.join(self.repo, "sub"), link)
        code, _, err = self.render("--into", os.path.join(link, "CLAUDE.md"))
        self.assertEqual(code, 0, err)
        self.assertEqual(lines(os.path.join(self.repo, ".claude", GATES)), ["sub/CLAUDE.md"])
        self.assertFalse(os.path.exists(os.path.join(self.repo, "sub", ".claude")))
        self.assertFalse(os.path.exists(self.owner))
