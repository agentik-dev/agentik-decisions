"""d37: the lane for changing an instruction (hq design/09 sections 7.1 to 7.4).

`answer --preview` prints what an answer would write and writes nothing; `audit --edits`
lists the commits that changed instruction text outside the lane; the `instruct` skill
and its command; the plugin's description bytes under the ceiling.

Every file a case writes is under its temp folder."""

import hashlib
import io
import json
import os
import re
import shutil
import tempfile

import decisions
from tests.hermetic import Hermetic
from tests.test_answer_head import Repo, git
from tests.test_new import PARTS, SAMPLE_QUESTIONS
from tests.test_new import Base as NewBase
from tests.test_plugin import PLUGIN, description_of, read, split_frontmatter

INSTRUCT = os.path.join(PLUGIN, "skills", "instruct", "SKILL.md")
COMMAND = os.path.join(PLUGIN, "commands", "instruct.md")
DESCRIPTIONS_CEILING = 1024

# The eight tests of the instruction audit, word for word; the skill's page is their copy.
EIGHT = (
    "1. **It changes what an agent does on an ordinary turn.** A rule for one act (cutting a "
    "packet, landing, an install) moves to the page that act reads, and one line with the "
    "trigger stays.",
    "2. **It is said once** across the chain a session loads: the global file, the repo's "
    "file and its rendered block. Remove the copy; keep the one nearest the rule's owner.",
    "3. **An absolute rule carries its scope and its reason** in a few words. Keep \"never\" "
    "where the rule guards real harm; do not soften it to \"ask first\". Where a hook or a "
    "check enforces it, one line is enough. A rule with a real exception names the exception.",
    "4. **Nothing describes history:** no dates of moves, former names, version history, "
    "finished briefs, or cautions about things that are gone. Check that each path and "
    "command named still exists.",
    "5. **No budget figure and no size cap is told to a writer.** Say what belongs in the "
    "thing; keep the cap in the checker. Do not ask for \"one sentence\" or \"N words\".",
    "6. **No line tells the model to think harder, to answer without thinking, or to write "
    "out its reasoning.**",
    "7. **A line that tells the model to delegate says when not to and what it costs.** No "
    "\"use proactively\" without a bound.",
    "8. **An \"Every session\" entry binds every turn.** An entry that binds one kind of work "
    "moves to an area section, so the block shows only its title. The owner's word is needed "
    "for a ledger move; a paste line from the owner counts.",
)

TREE = ("### Every session of the tree\n\n20. **Pushes.** No helper pushes. "
        "(2026-10-17; the fixture)\n\n### Build\n")

LOADS = re.compile(r"^answer --preview: (\S+) loads ([\d,]+) B now and ([\d,]+) B after, "
                   r"([+-][\d,]+) B; the ceiling for (.+?) is ([\d,]+) B", re.M)


def tree_hashes(root):
    """{relative path: sha256} of every file under `root`, .git included."""
    found = {}
    for top, _dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(top, name)
            with open(path, "rb") as handle:
                found[os.path.relpath(path, root)] = hashlib.sha256(handle.read()).hexdigest()
    return found


class Lane(Repo, NewBase):
    """A repo with question 9 open, its CLAUDE.md rendered, and both files committed."""

    LEDGER_EDIT = None

    def setUp(self):
        super().setUp()
        self.root = self.where()
        if self.root != self.tmp:
            os.makedirs(self.root)
            shutil.move(self.ledger, os.path.join(self.root, "DECISIONS.md"))
            self.ledger = os.path.join(self.root, "DECISIONS.md")
            self.questions = os.path.join(self.root, "OPEN-QUESTIONS.md")
        shutil.copy(SAMPLE_QUESTIONS, self.questions)
        if self.LEDGER_EDIT:
            self.write(self.ledger, self.read(self.ledger).replace("### Build\n",
                                                                   self.LEDGER_EDIT, 1))
        code, out, err = self.run_cli(*PARTS)
        self.assertEqual(code, 0, err)
        self.q = re.search(r"new: (\d+)", out).group(1)
        out = io.StringIO()
        self.assertEqual(decisions.main(["render", "--ledger", self.ledger], out=out,
                                        err=io.StringIO()), 0, out.getvalue())
        self.commit(root=self.root)

    def where(self):
        return self.tmp

    def answer(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["answer"] + list(argv) + ["--ledger", self.ledger],
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def loads(self, out):
        return {m.group(1): m.groups()[1:] for m in LOADS.finditer(out)}


class Preview(Lane):
    """R1: `answer --preview` prints the entry, each block's diff and the bytes, and
    writes nothing."""

    PICK = ("9", "--pick", "Pin", "--source", "s")

    def test_preview_writes_nothing(self):
        before = tree_hashes(self.tmp)
        code, out, err = self.answer(*(self.PICK + ("--text", "Pin 3.12.", "--area", "Build",
                                                    "--preview")))
        self.assertEqual(code, 0, out + err)
        self.assertEqual(tree_hashes(self.tmp), before)

    def test_preview_prints_the_entry_the_diff_and_the_bytes(self):
        code, out, err = self.answer(*(self.PICK + ("--text", "Pin 3.12.", "--area", "Build",
                                                    "--preview")))
        self.assertEqual(code, 0, out + err)
        self.assertIn("nothing written", out)
        self.assertIn("9. **Pin the interpreter.** Pin 3.12. (2026-09-28; the owner's answer "
                      "to decision 9, s)", out)
        self.assertIn("+- 9 Pin the interpreter (Build)", out)
        self.assertRegex(out, r"(?m)^--- \S*CLAUDE\.md$")
        loads = self.loads(out)
        self.assertEqual(len(loads), 1, out)
        now, after, delta, kind, figure = list(loads.values())[0]
        self.assertEqual(kind, "a repo's file")
        self.assertEqual(int(after.replace(",", "")) - int(now.replace(",", "")),
                         int(delta.replace(",", "")))
        self.assertGreater(int(delta.replace(",", "")), 0)

    def test_the_answer_after_a_preview_writes_what_it_showed(self):
        argv = self.PICK + ("--text", "Pin 3.12.", "--area", "Build")
        code, out, _ = self.answer(*(argv + ("--preview",)))
        self.assertEqual(code, 0)
        shown = next(l for l in out.splitlines() if l.startswith("9. **Pin"))
        code, _, err = self.answer(*argv)
        self.assertEqual(code, 0, err)
        self.assertIn(shown + "\n", self.read(self.ledger))

    def test_preview_of_an_amendment_shows_the_every_session_diff(self):
        code, out, err = self.answer(*(self.PICK + ("--add", "It holds for comments too.",
                                                    "--amends", "1", "--every-turn",
                                                    "--preview")))
        self.assertEqual(code, 0, out + err)
        self.assertIn("-1. **Plain words.** Every entry reads as plain present-tense English. "
                      "(2026-09-01)", out)
        self.assertIn("+1. **Plain words.** Every entry reads as plain present-tense English. "
                      "It holds for comments too. (2026-09-01; amended once, see the ledger)",
                      out)

    def test_preview_of_no_entry_names_none(self):
        before = tree_hashes(self.tmp)
        code, out, err = self.answer(*(self.PICK + ("--no-entry", "--preview")))
        self.assertEqual(code, 0, out + err)
        self.assertIn("no entry", out)
        self.assertEqual(tree_hashes(self.tmp), before)

    def refused_alike(self, argv):
        """`answer argv` and `answer argv --preview` exit 2 with the same stderr, and
        neither writes."""
        before = tree_hashes(self.tmp)
        shown = self.answer(*(argv + ("--preview",)))
        self.assertEqual(tree_hashes(self.tmp), before)
        real = self.answer(*argv)
        self.assertEqual(tree_hashes(self.tmp), before)
        self.assertEqual(real[0], 2, real)
        self.assertEqual(shown, real)

    def test_a_refused_growth_is_refused_in_preview(self):
        self.refused_alike(self.PICK + ("--add", "It holds for comments too.", "--amends", "1"))

    def test_an_unknown_option_is_refused_in_preview(self):
        self.refused_alike(("9", "--pick", "Nope", "--source", "s", "--no-entry"))

    def test_a_text_with_a_tail_is_refused_in_preview(self):
        self.refused_alike(self.PICK + ("--text", "Pin. (2026-09-28; s)", "--area", "Build"))


class TreePreview(Lane):
    """R1: an entry in the tree's section also shows the folder's file."""

    LEDGER_EDIT = TREE

    def where(self):
        return os.path.join(self.tmp, "orchard", "orchard-hq")

    def test_preview_shows_the_tree_file(self):
        before = tree_hashes(self.tmp)
        code, out, err = self.answer(self.q, "--pick", "Pin", "--source", "s", "--text",
                                     "Pin 3.12.", "--area", "Every session of the tree",
                                     "--every-turn", "--preview")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(tree_hashes(self.tmp), before)
        self.assertIn("+%s. **Pin the interpreter.** Pin 3.12. (2026-09-28)" % self.q, out)
        kinds = {v[3] for v in self.loads(out).values()}
        self.assertEqual(kinds, {"an hq's file", "a tree's file"}, out)

    def test_growth_of_the_tree_file_is_refused_in_preview(self):
        argv = (self.q, "--pick", "Pin", "--source", "s", "--text", "Pin 3.12.", "--area",
                "Every session of the tree")
        shown = self.answer(*(argv + ("--preview",)))
        self.assertEqual(shown, self.answer(*argv))
        self.assertEqual(shown[0], 2)
        self.assertIn("to the tree's file", shown[2])


class Edits(Hermetic):
    """R2: `audit --edits C` lists the commits after C that touch a guarded path without
    an `instruct:` subject; a list, exit 0."""

    def setUp(self):
        super().setUp()
        self.repo = tempfile.mkdtemp(prefix="decisions-d37-")
        self.addCleanup(shutil.rmtree, self.repo, True)
        git(self.repo, "init", "-q", "--template=")
        self.base = self.change("start", "README.md")

    def change(self, subject, *paths):
        for path in paths:
            full = os.path.join(self.repo, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "a", encoding="utf-8") as handle:
                handle.write("%s\n" % subject)
        git(self.repo, "add", "--", *paths)
        git(self.repo, "commit", "-q", "-m", subject)
        return git(self.repo, "rev-parse", "--short", "HEAD").strip()

    def edits(self, name, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["audit", "--edits=%s" % name] + list(argv) + [self.repo],
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def test_lists_hand_edits_and_omits_the_lane_and_the_fixtures(self):
        hand = self.change("tighten the file by hand", "CLAUDE.md")
        self.change("instruct: Commits: the reason added", "DECISIONS.md", "CLAUDE.md")
        self.change("a fixture's ledger", "tests/fixtures/DECISIONS.md")
        self.change("code only", "src/tool.py")
        self.change("a nested file is not the checkout's", "docs/CLAUDE.md")
        settings = self.change("a hook added", ".claude/settings.local.json")
        rules = self.change("a rule file", ".claude/rules/style.md", "AGENTS.md")
        code, out, err = self.edits(self.base)
        self.assertEqual(code, 0, err)
        rows = [l for l in out.splitlines() if re.match(r"^[0-9a-f]{7,} ", l)]
        self.assertEqual([r.split()[0] for r in rows], [hand, settings, rules], out)
        self.assertIn("tighten the file by hand", rows[0])
        self.assertTrue(rows[0].endswith("CLAUDE.md"), rows[0])
        self.assertIn(".claude/rules/style.md", rows[2])
        self.assertIn("AGENTS.md", rows[2])
        self.assertNotIn("instruct:", out.split("\n", 1)[1])

    def test_an_empty_list_exits_zero(self):
        self.change("instruct: Writes: narrowed", "DECISIONS.md")
        code, out, err = self.edits(self.base)
        self.assertEqual(code, 0, err)
        self.assertIn("no commit", out)

    def test_json(self):
        hand = self.change("by hand", "CLAUDE.local.md")
        code, out, err = self.edits(self.base, "--json")
        self.assertEqual(code, 0, err)
        view = json.loads(out)
        self.assertEqual([(e["sha"][:len(hand)], e["subject"], e["paths"])
                          for e in view["edits"]], [(hand, "by hand", ["CLAUDE.local.md"])])

    def test_a_bad_commit_name_is_refused(self):
        for name in ("no-such-commit", "-p"):
            code, out, err = self.edits(name)
            self.assertEqual((code, out), (2, ""), name)
            self.assertIn(name, err)

    def test_no_ledger_needed(self):
        self.assertFalse(os.path.exists(os.path.join(self.repo, "DECISIONS.md")))
        self.assertEqual(self.edits(self.base)[0], 0)


class Skill(Hermetic):
    """R3, R4, R5, R6: the skill's page, its command and the descriptions' bytes."""

    def page(self):
        return " ".join(read(INSTRUCT).split())

    def test_the_skill_holds_the_eight_tests(self):
        text = self.page()
        for test in EIGHT:
            self.assertIn(" ".join(test.split()), text, test[:40])

    def test_the_skill_names_the_flow_and_the_lane(self):
        front, _ = split_frontmatter(read(INSTRUCT))
        self.assertIn("name: instruct", front)
        text = self.page()
        for needed in ("`agentik decisions answer --preview`", "`agentik decisions find <word>`",
                       "`agentik decisions new`", "`agentik decisions render --check`",
                       "`agentik decisions audit --edits <commit>`",
                       "`instruct: <title>: <what changed>`",
                       # the chain's three ledgers, by how each is found
                       "`Generated from`", "`Each is an entry of`"):
            self.assertIn(needed, text, needed)

    def test_the_where_table_reads_each_live_value(self):
        lines = read(INSTRUCT).splitlines()
        head = next(i for i, l in enumerate(lines) if l.startswith("| name |"))
        self.assertIn("| shown by |", lines[head])
        rows = [l for l in lines[head + 2:] if l.startswith("|")]
        self.assertGreaterEqual(len(rows), 10)
        column = lines[head].split("|").index(" shown by ")
        for row in rows:
            self.assertIn("`", row.split("|")[column], row)

    def test_the_skill_states_no_byte_figure(self):
        text = read(INSTRUCT)
        self.assertIsNone(re.search(r"\d[\d,]*\s*(B|KB|bytes)\b", text))
        self.assertNotIn("~/code", text)

    def test_the_command_is_the_owners_alone(self):
        front, body = split_frontmatter(read(COMMAND))
        self.assertIn("disable-model-invocation: true", front)
        self.assertTrue(any(l.startswith("argument-hint:") and "adopt <file>" in l
                            and "where" in l for l in front), front)
        self.assertTrue(description_of(front))

    def test_the_descriptions_stay_under_the_ceiling(self):
        total, counted = 0, []
        names = [os.path.join(PLUGIN, "skills", d, "SKILL.md")
                 for d in sorted(os.listdir(os.path.join(PLUGIN, "skills")))]
        names += [os.path.join(PLUGIN, "commands", c)
                  for c in sorted(os.listdir(os.path.join(PLUGIN, "commands")))]
        for name in names:
            front, _ = split_frontmatter(read(name))
            if "disable-model-invocation: true" in front:
                continue
            total += len(description_of(front).encode())
            counted.append(os.path.relpath(name, PLUGIN))
        self.assertIn(os.path.join("skills", "instruct", "SKILL.md"), counted)
        self.assertLess(total, DESCRIPTIONS_CEILING, counted)
