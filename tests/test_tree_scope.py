"""d36: the tree's section, `render --scope tree`, the plain render without the tree, the
refusals over another's file, the ten titles' order, the two warnings and the ceilings
in loaded bytes (hq design/09 sections 1, 3 to 5, 7.2 and 9).

Every file a case writes is under its temp home: the tree's folder is
`<home>/work/orchard`, the hq's checkout `<home>/work/orchard/orchard-hq`."""

import io
import json
import os
import re
import shutil

import decisions
from decisions.render import BEGIN, END
from tests.hermetic import SAMPLE, Hermetic
from tests.test_answer_head import Repo, git
from tests.test_new import PARTS, SAMPLE_QUESTIONS
from tests.test_new import Base as NewBase

TREE_LEDGER = """# orchard-hq: what is settled

## In force

### Every session

1. **Plain words.** Every entry reads as plain present-tense English. (2026-09-01; the fixture)

### Every session of the tree

4. **Never commit.** No secret enters git, and no private name enters a public repo. (2026-11-11; the fixture)

2. **Commits.** Commit by explicit path, never with a sweep, since several sittings share a checkout. (2026-11-11; the fixture)

5. **Pushes.** The hq sitting pushes after a green check; no helper pushes. (2026-10-17; the fixture; amended 2026-10-20, answer 6; amended 2026-11-11, answer 7)

### Build

3. **One interpreter.** The tool runs under Python 3.12. (2026-09-03; the fixture)
"""

# hq design/09 section 5.2's first example, for this fixture's tree, repo and entries.
TREE_FILE = """<!-- ~/work/orchard/CLAUDE.md: loaded by every session started in a repo of this folder or in a worktree under one, and by their helpers.
     This file is in no repo. It is generated whole from orchard-hq's ledger, and orchard-hq's `make check` fails when it is absent or stale.
     Change it through /decisions:instruct. -->
# The orchard tree

<!-- BEGIN GENERATED: decisions -->
<!-- Generated from orchard-hq/DECISIONS.md by `agentik decisions render --scope tree`; edit the ledger and rerun it, never this block. -->
## Rules for every session in this tree

Each is an entry of `~/work/orchard/orchard-hq/DECISIONS.md`; `agentik decisions show N --ledger` with that path reads one.

2. **Commits.** Commit by explicit path, never with a sweep, since several sittings share a checkout. (2026-11-11)
5. **Pushes.** The hq sitting pushes after a green check; no helper pushes. (2026-10-17; amended 2 times, see the ledger)
4. **Never commit.** No secret enters git, and no private name enters a public repo. (2026-11-11)
<!-- END GENERATED: decisions -->
"""

# The sample's block as `render` wrote it at the pin, 497abb7, byte for byte.
SAMPLE_BLOCK = (
    "<!-- BEGIN GENERATED: decisions -->\n"
    "Generated from `DECISIONS.md` by `decisions render`; edit the ledger and rerun it, never "
    "this block.\n\n"
    "1. **Plain words.** Every entry reads as plain present-tense English. (2026-09-01)\n"
    "2. **Small ledgers.** A ledger holds at most 25 entries in force. (2026-09-02)\n\n"
    "The other entries in force, one line each; `decisions show N` reads one.\n\n"
    "- 3 One interpreter (Build)\n- 4 Tests first (Build)\n- 5 Make is the gate (Build tools)\n"
    "- 7 Releases follow the manifest (Release)\n"
    "<!-- END GENERATED: decisions -->\n")

LOADS = re.compile(r"^render: (\S+) loads ([\d,]+) B, comments aside and imports included; "
                   r"the ceiling for (.+?) is ([\d,]+) B(?:; over by ([\d,]+) B)?$", re.M)


def entry(n, title, words=8):
    return "%d. **%s.** %s (2026-11-11; the fixture)\n" % (n, title, " ".join(["word"] * words))


def loaded(text):
    """The bytes of `text` without its comments, each a run of whole lines here."""
    kept, inside = [], False
    for line in text.splitlines(keepends=True):
        if not inside and line.startswith("<!--"):
            inside = True
        if not inside:
            kept.append(line)
        if inside and line.rstrip().endswith("-->"):
            inside = False
    return len("".join(kept).encode())


class Tree(Hermetic):

    def setUp(self):
        super().setUp()
        self.home = os.environ["HOME"]
        self.folder = os.path.join(self.home, "work", "orchard")
        self.repo = os.path.join(self.folder, "orchard-hq")
        os.makedirs(self.repo)
        self.ledger = os.path.join(self.repo, "DECISIONS.md")
        self.target = os.path.join(self.folder, "CLAUDE.md")
        self.write(self.ledger, TREE_LEDGER)

    def run_cli(self, verb, *argv, ledger=None):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main([verb] + list(argv) + ["--ledger", ledger or self.ledger],
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def render(self, *argv, ledger=None):
        return self.run_cli("render", *argv, ledger=ledger)

    def read(self, path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    def write(self, path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def loads(self, out):
        """{the file's kind: (bytes, figure, over)} of each loaded-bytes line in `out`."""
        return {m.group(3): (int(m.group(2).replace(",", "")), int(m.group(4).replace(",", "")),
                             m.group(5) is not None) for m in LOADS.finditer(out)}


class Section(Tree):
    """R1: the section lints, and its entries are in force for show, find and audit."""

    def test_a_ledger_with_a_tree_section_lints(self):
        code, out, err = self.render("--lint")
        self.assertEqual(code, 0, out + err)
        self.assertNotRegex(out, r"DECISIONS\.md:\d+:")

    def test_the_tree_section_may_come_before_every_session(self):
        head = "# x\n\n## In force\n\n"
        tree = "### Every session of the tree\n\n" + entry(2, "Commits") + "\n"
        every = "### Every session\n\n" + entry(1, "Writes") + "\n"
        build = "### Build\n\n" + entry(3, "Tool")
        self.write(self.ledger, head + tree + every + build)
        code, out, err = self.render("--lint")
        self.assertEqual(code, 0, out + err)
        self.write(self.ledger, head + tree + build + "\n" + every)
        code, out, _ = self.render("--lint")
        self.assertEqual(code, 1, out)  # Every session still comes before every other area
        self.assertIn("`### Every session` comes first", out)

    def test_show_and_find_read_the_tree_entries(self):
        code, out, _ = self.run_cli("show", "5")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("## In force\n\n### Every session of the tree\n\n5. "), out)
        code, out, _ = self.run_cli("show", "--area", "every session of the tree")
        self.assertEqual(code, 0)
        self.assertEqual(out.count("\n4. ") + out.count("\n2. ") + out.count("\n5. "), 3, out)
        code, out, _ = self.run_cli("find", "sweep")
        self.assertEqual((code, out), (0, "2 Commits (Every session of the tree)\n"))

    def test_audit_lists_the_tree_entries_with_their_bytes(self):
        code, out, err = self.run_cli("audit", "--json")
        self.assertEqual(code, 0, err)
        view = json.loads(out)
        rows = {r["number"]: r["bytes"] for r in view["tree_session_entries"]}
        self.assertEqual(sorted(rows), [2, 4, 5])
        for line in TREE_FILE.splitlines():
            number = re.match(r"^(\d+)\. ", line)
            if number:
                self.assertEqual(rows[int(number.group(1))], len(line.encode()) + 1, line)
        self.assertIsNone(view["every_session_cap"])
        self.assertEqual([r["number"] for r in view["every_session_entries"]], [1])
        code, out, _ = self.run_cli("audit")
        self.assertIn("1 under Every session, 3 under Every session of the tree;", out)
        lines = out.splitlines()
        start = next(i for i, l in enumerate(lines) if l.startswith("Every session of the tree"))
        self.assertIn("the tree's", lines[start])
        self.assertTrue(lines[start + 1].startswith("4 Never commit  "), lines[start + 1])


class ScopeTree(Tree):
    """R2: the folder's file, whole, in section 5.2's form; --check holds it."""

    def test_scope_tree_writes_the_folders_file_and_check_passes(self):
        code, out, err = self.render("--scope", "tree")
        self.assertEqual(code, 0, err)
        self.assertIn("render: wrote ", out)
        self.assertEqual(self.read(self.target), TREE_FILE)
        self.assertEqual(sorted(os.listdir(self.folder)), ["CLAUDE.md", "orchard-hq"])
        code, out, err = self.render("--scope", "tree", "--check")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.render("--scope", "tree")[1].count("is fresh"), 1)

    def test_check_fails_on_an_absent_or_edited_folders_file(self):
        code, out, _ = self.render("--scope", "tree", "--check")
        self.assertEqual(code, 1)
        self.assertIn("is absent", out)
        self.assertFalse(os.path.exists(self.target))
        self.render("--scope", "tree")
        self.write(self.target, TREE_FILE.replace("no helper pushes", "a helper pushes"))
        code, out, _ = self.render("--scope", "tree", "--check")
        self.assertEqual(code, 1)
        self.assertIn("-5. **Pushes.** The hq sitting pushes after a green check; a helper", out)
        self.assertIn("a helper pushes", self.read(self.target))

    def test_into_writes_the_same_bytes_elsewhere(self):
        other = os.path.join(self.home, "scratch", "tree.md")
        os.makedirs(os.path.dirname(other))
        code, _, err = self.render("--scope", "tree", "--into", other)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(other), TREE_FILE)
        self.assertFalse(os.path.exists(self.target))
        self.assertEqual(self.render("--scope", "tree", "--into", other, "--check")[0], 0)

    def test_from_a_worktree_the_folder_is_the_main_checkouts(self):
        git(self.repo, "init", "-q", "--template=")
        git(self.repo, "add", "DECISIONS.md")
        git(self.repo, "commit", "-q", "-m", "the ledger")
        worktree = os.path.join(self.repo, ".claude", "worktrees", "row")
        git(self.repo, "worktree", "add", "-q", worktree, "-b", "row")
        code, _, err = self.render("--scope", "tree",
                                   ledger=os.path.join(worktree, "DECISIONS.md"))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(self.target), TREE_FILE)
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".claude", "worktrees",
                                                     "CLAUDE.md")))
        self.assertEqual(self.render("--scope", "tree", "--check")[0], 0)

    def test_a_ledger_without_the_section_is_refused(self):
        self.write(self.ledger, self.read(SAMPLE))
        for mode in ([], ["--check"], ["--lint"]):
            with self.subTest(mode=mode):
                code, out, err = self.render("--scope", "tree", *mode)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("no `### Every session of the tree`", err)
        self.assertFalse(os.path.exists(self.target))


class PlainRender(Tree):
    """R3: the plain render leaves the tree out; without the section it is as at the pin."""

    def test_the_plain_render_omits_the_tree(self):
        code, _, err = self.render()
        self.assertEqual(code, 0, err)
        text = self.read(os.path.join(self.repo, "CLAUDE.md"))
        for absent in ("Commits", "Pushes", "Never commit", "sweep", "- 2 ", "- 4 ", "- 5 ",
                       "Every session of the tree"):
            self.assertNotIn(absent, text)
        self.assertIn("1. **Plain words.**", text)
        self.assertIn("- 3 One interpreter (Build)\n", text)
        self.assertFalse(os.path.exists(self.target))

    def test_a_ledger_without_the_section_renders_as_at_the_pin(self):
        self.write(self.ledger, self.read(SAMPLE))
        code, _, err = self.render()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read(os.path.join(self.repo, "CLAUDE.md")), SAMPLE_BLOCK)


class Refusals(Tree):
    """R4: never over another ledger's block, never over a hand-written file."""

    def other_ledger(self):
        other = os.path.join(self.home, "work", "pear", "pear-hq", "DECISIONS.md")
        self.write(other, TREE_LEDGER.replace("orchard-hq", "pear-hq"))
        return other

    def test_into_a_block_from_another_ledger_is_refused(self):
        other = self.other_ledger()
        shared = os.path.join(self.home, "work", "shared.md")
        self.write(shared, "# Shared\n")
        self.assertEqual(self.render("--into", shared, ledger=other)[0], 0)
        before = self.read(shared)
        for mode in ([], ["--check"]):
            with self.subTest(mode=mode):
                code, out, err = self.render("--into", shared, *mode)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("~/work/pear/pear-hq/DECISIONS.md", err)
                self.assertIn("~/work/orchard/orchard-hq/DECISIONS.md", err)
                self.assertEqual(self.read(shared), before)
        # its own ledger rewrites it
        self.assertEqual(self.render("--into", shared, ledger=other)[0], 0)

    def test_scope_tree_into_another_ledgers_tree_file_is_refused(self):
        other = self.other_ledger()
        into = os.path.join(self.home, "work", "tree.md")
        self.assertEqual(self.render("--scope", "tree", "--into", into, ledger=other)[0], 0)
        before = self.read(into)
        code, out, err = self.render("--scope", "tree", "--into", into)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("~/work/pear/pear-hq/DECISIONS.md", err)
        self.assertIn("~/work/orchard/orchard-hq/DECISIONS.md", err)
        self.assertEqual(self.read(into), before)

    def test_scope_tree_never_replaces_a_hand_written_file(self):
        for text in ("# Our folder\n\nHand-written notes.\n",
                     "# Notes\n\n%s\nGenerated from `DECISIONS.md` by a render.\n%s\n" % (BEGIN, END)):
            with self.subTest(text=text[:12]):
                self.write(self.target, text)
                for mode in ([], ["--check"]):
                    code, out, err = self.render("--scope", "tree", *mode)
                    self.assertEqual((code, out), (2, ""))
                    self.assertIn("is not a tree's file", err)
                    self.assertIn("never replaced", err)
                    self.assertEqual(self.read(self.target), text)


class Order(Tree):
    """R5: both blocks list their entries in the ten titles' order, others after."""

    def test_the_ten_titles_order_both_blocks(self):
        text = ("# x\n\n## In force\n\n### Every session\n\n"
                + entry(11, "Budget") + entry(12, "Plain words") + entry(13, "Writes")
                + entry(14, "Another") + entry(15, "Helpers")
                + "\n### Every session of the tree\n\n"
                + entry(21, "Never commit") + entry(22, "Local rule") + entry(23, "Never run"))
        self.write(self.ledger, text)
        self.assertEqual(self.render()[0], 0)
        block = self.read(os.path.join(self.repo, "CLAUDE.md"))
        self.assertEqual(re.findall(r"^(\d+)\. ", block, re.M), ["13", "15", "11", "12", "14"])
        self.assertEqual(self.render("--scope", "tree")[0], 0)
        self.assertEqual(re.findall(r"^(\d+)\. ", self.read(self.target), re.M),
                         ["23", "21", "22"])


class Warnings(Tree):
    """R5: two warnings on --lint, its exit unchanged."""

    def test_a_title_outside_the_ten_warns(self):
        code, out, err = self.render("--lint")
        self.assertEqual(code, 0)
        self.assertIn("render: warning: entry 1 under `Every session` is titled `Plain words`",
                      err)
        self.assertNotIn("`Commits`", err)
        self.assertEqual(err.count("render: warning:"), 2, err)
        self.assertIn("render: warning: the ten titles, in their order: Writes, Never run,", err)

    def test_a_rule_word_in_a_hand_written_line_warns(self):
        target = os.path.join(self.repo, "CLAUDE.md")
        self.write(target, "# orchard-hq\n\nAlways run the gate first.\nRead the README.\n"
                   "<!-- a comment may say never or must -->\n```\nnever inside a fence\n```\n"
                   "A tool that only reads.\nNevertheless, mustard.\n")
        self.assertEqual(self.render()[0], 0)
        code, out, err = self.render("--lint")
        self.assertEqual(code, 0)
        found = re.findall(r"CLAUDE\.md:(\d+): a hand-written line holds (.+?);", err)
        self.assertEqual(found, [("3", "`always`"), ("9", "`only`")])
        self.assertEqual(self.render("--lint", "--ceiling")[0], 0)


class Ceilings(Tree):
    """R6: no count of seven; each file's loaded bytes beside its ceiling."""

    def test_eight_every_session_entries_lint(self):
        self.write(self.ledger, "# x\n\n## In force\n\n### Every session\n\n"
                   + "".join(entry(n, "Rule %d" % n) for n in range(1, 9)))
        code, out, err = self.render("--lint")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.render()[0], 0)

    def check_both(self, kind, figure, args, ledger=None):
        """--lint and --check print `kind` at `figure`; over it, exit 0, and 1 with --ceiling."""
        for mode in (["--lint"], ["--check"]):
            with self.subTest(kind=kind, mode=mode):
                code, out, err = self.render(*(args + mode), ledger=ledger)
                self.assertEqual(code, 0, out + err)
                size, shown, over = self.loads(out)[kind]
                self.assertEqual((shown, over), (figure, True))
                self.assertGreater(size, figure)
                self.assertEqual(self.render(*(args + mode + ["--ceiling"]), ledger=ledger)[0], 1)

    def test_a_repos_file(self):
        plain = os.path.join(self.home, "work", "plain", "DECISIONS.md")
        self.write(plain, self.read(SAMPLE))
        claude = os.path.join(os.path.dirname(plain), "CLAUDE.md")
        self.write(claude, "# plain\n")
        self.assertEqual(self.render(ledger=plain)[0], 0)
        code, out, _ = self.render("--check", "--ceiling", ledger=plain)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.loads(out)["a repo's file"][1:], (3072, False))
        self.write(claude, "# plain\n\n" + "Hand text.\n" * 300 + self.read(claude)[8:])
        self.check_both("a repo's file", 3072, [], ledger=plain)

    def test_an_hqs_file(self):
        claude = os.path.join(self.repo, "CLAUDE.md")
        self.write(claude, "# orchard-hq\n")
        self.assertEqual(self.render()[0], 0)
        code, out, _ = self.render("--check", "--ceiling")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.loads(out)["an hq's file"][1:], (4096, False))
        self.write(claude, "# orchard-hq\n\n" + "Hand text.\n" * 400 + self.read(claude)[13:])
        self.check_both("an hq's file", 4096, [])

    def test_a_trees_file(self):
        self.render("--scope", "tree")
        code, out, _ = self.render("--scope", "tree", "--check", "--ceiling")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.loads(out)["a tree's file"], (loaded(TREE_FILE), 1536, False))
        self.write(self.ledger, TREE_LEDGER.replace("### Build", entry(6, "Helpers", 300)
                                                    + "\n### Build"))
        self.render("--scope", "tree")
        self.check_both("a tree's file", 1536, ["--scope", "tree"])

    def test_the_macs_global_file(self):
        mac = os.path.join(self.home, ".claude", "CLAUDE.md")
        self.write(mac, "# This Mac\n")
        args = ["--into", mac]
        self.assertEqual(self.render(*args)[0], 0)
        code, out, _ = self.render(*(args + ["--check", "--ceiling"]))
        self.assertEqual(code, 0, out)
        self.assertEqual(self.loads(out)["the Mac's global file"][1:], (6144, False))
        self.write(mac, "# This Mac\n\n" + "Hand text.\n" * 600 + self.read(mac)[11:])
        self.check_both("the Mac's global file", 6144, args)

    def test_an_import_counts_and_a_comment_does_not(self):
        claude = os.path.join(self.repo, "CLAUDE.md")
        notes = os.path.join(self.repo, "notes.md")
        deeper = os.path.join(self.repo, "deeper.md")
        self.write(notes, "\n".join(["Notes for every turn.", "<!-- a hidden line",
                                     "     on two lines -->", "@deeper.md", ""]))
        self.write(deeper, "Deeper.\n")
        hand = "\n".join(["# orchard-hq", "<!-- a comment that never loads -->", "@notes.md",
                          "`@absent.md` in a code span, and @missing.md, load nothing.", ""])
        self.write(claude, hand)
        self.assertEqual(self.render()[0], 0)
        whole = self.read(claude)
        code, out, _ = self.render("--check")
        self.assertEqual(code, 0, out)
        kept = "\n".join(["Notes for every turn.", "@deeper.md", ""])
        want = loaded(whole) + len(kept.encode()) + len("Deeper.\n".encode())
        self.assertEqual(self.loads(out)["an hq's file"][0], want)
        self.assertNotEqual(loaded(whole), len(whole.encode()))

    def test_ceiling_goes_with_check_or_lint(self):
        code, out, err = self.render("--ceiling")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("--ceiling goes with --check or --lint", err)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "CLAUDE.md")))


# The tree entry is 20, so `new` puts question 21.
Q = "21"


class Answers(Repo, NewBase):
    """R1: an answer enters or moves an entry into the tree's section, by `--area` and
    by `--amends M --move-to A`, the tree's file guarded as the block is."""

    TREE = ("### Every session of the tree\n\n20. **Pushes.** No helper pushes. "
            "(2026-10-17; the fixture)\n\n### Build\n")

    def setUp(self):
        super().setUp()
        shutil.copy(SAMPLE_QUESTIONS, self.questions)
        self.write(self.ledger, self.read(self.ledger).replace("### Build\n", self.TREE, 1))
        code, _, err = self.run_cli(*PARTS)
        self.assertEqual(code, 0, err)
        self.commit()

    def answer(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["answer"] + list(argv) + ["--ledger", self.ledger],
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def section(self, name):
        text = self.read(self.ledger)
        start = text.index("### %s\n" % name)
        return text[start:text.index("###", start + 4)]

    def test_area_enters_the_tree_by_its_whole_name(self):
        argv = (Q, "--pick", "Pin", "--source", "s", "--text", "Pin 3.12.", "--area",
                "every session of the tree")
        code, out, err = self.answer(*argv)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("to the tree's file", err)
        code, out, err = self.answer(*(argv + ("--every-turn",)))
        self.assertEqual(code, 0, err)
        self.assertIn("entry 21 under `### Every session of the tree`", out)
        self.assertIn("21. **Pin the interpreter.** Pin 3.12.", self.section(
            "Every session of the tree"))
        self.assertIn("render --scope tree", err)

    def test_a_prefix_never_reaches_the_tree(self):
        code, out, err = self.answer(Q, "--pick", "Pin", "--source", "s", "--text",
                                     "Pin 3.12.", "--area", "every session of")
        self.assertEqual(code, 0, err)
        self.assertNotIn("Pin 3.12.", self.section("Every session of the tree"))

    def test_amends_moves_an_entry_into_the_tree(self):
        para = "The tool runs under Python 3.12 from the standard library alone."
        code, out, err = self.answer(Q, "--pick", "Pin", "--source", "s", "--text", para,
                                     "--amends", "3", "--move-to", "Every session of the tree",
                                     "--every-turn")
        self.assertEqual(code, 0, err)
        self.assertIn("entry 3 amended, under `### Every session of the tree`", out)
        self.assertIn("3. **One interpreter.** %s (2026-09-03;" % para,
                      self.section("Every session of the tree"))
        self.assertNotIn("3. **One interpreter.**", self.section("Build"))
        out = io.StringIO()
        self.assertEqual(decisions.main(["render", "--lint", "--ledger", self.ledger], out=out,
                                        err=io.StringIO()), 0, out.getvalue())

    def test_move_to_needs_amends(self):
        code, out, err = self.answer(Q, "--pick", "Pin", "--source", "s", "--text", "Pin.",
                                     "--area", "Build", "--move-to", "Build")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("--move-to is valid only with --amends", err)
