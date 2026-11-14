"""dc3 (design/packets/dc3-claude-md-audit.md): `init` and `render` say what a hand-kept
CLAUDE.md loads and name `/decisions:audit-claude-md`; the skill's page. Each case in a temp
HOME and a repo made by `git init`; the ledger is written as a fixture."""

import hashlib
import os
import re
import shlex

from decisions.cli import build_parser
from tests.test_dc1_init import Base, snapshot
from tests.test_instruct import EIGHT
from tests.test_plugin import PLUGIN, description_of, read, split_frontmatter

F = "# Mine\n\n<!-- a note for people -->\nNever push on a Friday.\n@docs/extra.md\n"
EXTRA = "one line of extra\nand two lines\n"
L = ("# Decisions\n\n## In force\n\n### Every session\n\n"
     "1. **Indent.** This repo indents with four spaces. (2026-11-13; me)\n\n"
     "## Proposed\n\n## Superseded\n")
BEGIN = "<!-- BEGIN GENERATED: decisions -->"
END = "<!-- END GENERATED: decisions -->"
STALE = BEGIN + "\nold text\n" + END + "\n"
LINE = ("%s: %s loads %s B of hand-written text on every turn of every session started here; "
        "/decisions:audit-claude-md goes through it with you and finds the lines no session "
        "acts on and the rules that belong in the ledger\n")
REFUSAL = ("decisions: render: CLAUDE.md holds no generated block, and render only rewrites a "
           "block that is there; nothing written; `agentik decisions init` adds it\n")
GATED = ("now on the edit-gates list .claude/edit-gates: a session changes %s through "
         "/decisions:instruct, never by its own edit; deleting %s line there lifts the gate\n")
NEXT = ("init: next, `agentik decisions new` records a question; its answer becomes an entry "
        "and reaches CLAUDE.md\n")
PAGE = os.path.join(PLUGIN, "skills", "audit-claude-md", "SKILL.md")
# the sha256 of the brief's page, word for word (R3)
PAGE_SHA = "e25c490dc7efa00ec1c25da216bfe24c36966e617ceea35b87f8415613298750"
NAMES = ("rule", "twice", "stale", "one act", "in the repo", "for people", "import", "keeps")
PIN_DESCRIPTIONS = 483  # the bytes test_instruct's sum counts at ab7b4f5

# measured at ab7b4f5 (0.22.5) by the same fixtures: acceptance line 4
LOADS = ("render: CLAUDE.md loads 246 B, comments aside and imports included; the ceiling for "
         "a repo's file is 3,072 B\n")
PIN = {
    ("render", "--check"): (1, "render: CLAUDE.md holds no generated block; `agentik decisions "
                               "init` adds it\n" + LOADS, ""),
    ("render", "--lint"): (
        0, "render: the block for CLAUDE.md is 236 B; it is loaded on every turn\n" + LOADS,
        "render: warning: entry 1 under `Every session` is titled `Indent`, none of the ten "
        "titles; it keeps its place after them\n"
        "render: warning: the ten titles, in their order: Writes, Never run, Devices, Commits, "
        "Pushes, Never commit, Helpers, Budget, Deciding and asking, Changing these rules\n"
        "render: warning: CLAUDE.md:4: a hand-written line holds `never`; a rule lives in the "
        "ledger, and render puts it in the block\n"),
}
PIN_STALE = (0, "render: wrote CLAUDE.md: 79 B to 236 B, +157 B; the block is loaded on every "
                "turn\nrender: CLAUDE.md is " + GATED % ("it", "its"), "")
PIN_FRESH = (0, "render: CLAUDE.md is fresh\n", "")
PIN_ANSWER = (0, "answer: 2, Short; entry 2 under `### Every session` in DECISIONS.md\n"
                 "answer: rewrote the block in CLAUDE.md: 236 B to 285 B, +49 B; the block is "
                 "loaded on every turn\nanswer: DECISIONS.md is " + GATED % ("it", "its"), "")


class Fixture(Base):

    def setUp(self):
        super().setUp()
        os.mkdir(os.path.join(self.repo, "docs"))
        self.write(os.path.join(self.repo, "docs", "extra.md"), EXTRA)
        self.assertEqual(len(EXTRA.encode()), 32)

    def write(self, path, text):
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)


class Audit(Fixture):

    def test_1_init_says_what_the_hand_text_loads(self):
        both = "DECISIONS.md and CLAUDE.md are " + GATED % ("them", "a file's")
        for ledger, gate in ((None, "init: " + both),
                             (L, "init: CLAUDE.md is " + GATED % ("it", "its"))):
            with self.subTest(ledger=bool(ledger)):
                for name in ("DECISIONS.md", "CLAUDE.md", ".claude/edit-gates"):
                    if os.path.lexists(os.path.join(self.repo, name)):
                        os.unlink(os.path.join(self.repo, name))
                if ledger:
                    self.write(self.ledger, ledger)
                self.write(self.claude, F)
                code, out, err = self.run_cli("init")
                self.assertEqual((code, err), (0, ""), out)
                lines = out.splitlines(keepends=True)
                self.assertEqual(lines[-3:], [gate, LINE % ("init", "CLAUDE.md", "79"), NEXT])
                self.assertEqual(len(lines), 5, out)

    def test_1_a_large_text_prints_its_figure_with_a_comma(self):
        self.write(self.claude, "# Mine\n\n" + "A line a session reads here.\n" * 40)
        code, out, err = self.run_cli("init")
        self.assertEqual(code, 0, err)
        self.assertIn(LINE % ("init", "CLAUDE.md", "1,168"), out)

    def test_2_render_says_it_then_refuses(self):
        self.write(self.ledger, L)
        self.write(self.claude, F)
        before = snapshot(self.tmp)
        self.assertEqual(self.run_cli("render"),
                         (2, LINE % ("render", "CLAUDE.md", "79"), REFUSAL))
        self.assertEqual(snapshot(self.tmp), before)

    def test_3_no_line_where_no_hand_text(self):
        code, out, err = self.run_cli("init")  # an empty repo
        self.assertEqual(code, 0, err)
        self.assertNotIn("hand-written text", out)
        for name, text in (("empty", ""), ("blank lines", "\n\n\n"),
                           ("a comment alone", "<!-- a note for people -->\n"),
                           ("absent", None)):
            for verb in ("init", "render"):
                with self.subTest(name=name, verb=verb):
                    for path in ("DECISIONS.md", "CLAUDE.md", ".claude/edit-gates"):
                        if os.path.lexists(os.path.join(self.repo, path)):
                            os.unlink(os.path.join(self.repo, path))
                    if verb == "render":
                        self.write(self.ledger, L)
                    if text is not None:
                        self.write(self.claude, text)
                    elif verb == "init":
                        continue  # init over no CLAUDE.md is line 3's empty repo
                    code, out, err = self.run_cli(verb)
                    self.assertEqual(code, 2 if verb == "render" else 0, err)
                    self.assertNotIn("hand-written text", out + err)

    def test_4_the_other_modes_print_as_at_the_pin(self):
        self.write(self.ledger, L)
        self.write(self.claude, F)
        for argv, said in PIN.items():
            before = snapshot(self.tmp)
            self.assertEqual(self.run_cli(*argv), said, argv)
            self.assertEqual(snapshot(self.tmp), before, argv)
        self.write(self.claude, F + "\n" + STALE)
        self.assertEqual(self.run_cli("render"), PIN_STALE)
        self.assertEqual(self.run_cli("render"), PIN_FRESH)
        code, out, err = self.run_cli(
            "new", "--title", "Width", "--stands", "Lines run long.", "--choice",
            "Which width here?", "--option", "Short: lines stop at eighty",
            "--option", "Long: lines stop at a hundred", "--recommend", "Short: most do.")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.run_cli("answer", "2", "--pick", "Short", "--source", "me",
                                      "--text", "Lines stop at eighty.", "--area",
                                      "Every session", "--every-turn"), PIN_ANSWER)


class Page(Fixture):

    def text(self):
        return read(PAGE)

    def test_5_the_page_is_the_rulings_text(self):
        with open(PAGE, "rb") as handle:
            self.assertEqual(hashlib.sha256(handle.read()).hexdigest(), PAGE_SHA)
        front, _ = split_frontmatter(self.text())
        self.assertIn("name: audit-claude-md", front)
        self.assertIn("disable-model-invocation: true", front)
        self.assertTrue(description_of(front))

    def test_5_the_descriptions_sum_is_the_pins(self):
        total = 0
        names = [os.path.join(PLUGIN, "skills", d, "SKILL.md")
                 for d in sorted(os.listdir(os.path.join(PLUGIN, "skills")))]
        names += [os.path.join(PLUGIN, "commands", c)
                  for c in sorted(os.listdir(os.path.join(PLUGIN, "commands")))]
        for name in names:
            front, _ = split_frontmatter(read(name))
            if "disable-model-invocation: true" not in front:
                total += len(description_of(front).encode())
        self.assertIn(PAGE, names)
        self.assertEqual(total, PIN_DESCRIPTIONS)

    def test_6_each_command_the_page_names_is_the_tools(self):
        parser = build_parser()
        verbs = next(a for a in parser._actions if a.dest == "verb").choices
        verb, seen = None, 0
        for span in re.findall(r"`([^`]+)`", self.text()):
            try:
                words = shlex.split(span.replace("<", "'<").replace(">", ">'"))
            except ValueError:
                continue
            if words and words[0].startswith("agentik") and words[:2] != ["agentik",
                                                                        "decisions"]:
                verb = None  # another tool's command; its flags are not this tool's
                continue
            if words[:2] == ["agentik", "decisions"]:
                verb = words[2]
                self.assertIn(verb, verbs, span)
                flags = words[3:]
                seen += 1
            elif words and words[0].startswith("--") and verb:
                flags = words  # a flag beside the command before it
            else:
                continue
            for word in flags:
                if word.startswith("--"):
                    self.assertIn(word, verbs[verb]._option_string_actions, span)
        self.assertGreaterEqual(seen, 6)

    def test_6_the_measures_the_walk_runs(self):
        self.write(self.ledger, L)
        self.write(self.claude, F)
        draft = os.path.join(self.tmp, "draft.md")
        self.write(draft, "# Mine\n")
        before = snapshot(self.tmp)
        for argv in (["render", "--lint"], ["render", "--lint", "--into", draft]):
            code, out, err = self.run_cli(*argv)
            self.assertEqual(code, 0, err)
            self.assertRegex(out, r"(?m)^render: \S+ loads [\d,]+ B, ", argv)
        self.assertEqual(snapshot(self.tmp), before)

    def test_7_the_page_names_the_eight_and_no_figure(self):
        text = self.text()
        for name in NAMES:
            self.assertIn("**%s**" % name, text, name)
        self.assertIsNone(re.search(r"\d[\d,]*\s*(B|KB|bytes)\b", text))
        flat = " ".join(text.split())
        for test in EIGHT:
            sentence = re.match(r"\d\. \*\*(.+?)\*\*", test).group(1)
            self.assertNotIn(sentence, flat, sentence)

    def test_7_each_command_named_is_the_plugins(self):
        said = self.text() + LINE + GATED
        named = set(re.findall(r"(?<![\w/-])/?decisions:([a-z][\w-]*)", said))
        self.assertIn("audit-claude-md", named)
        for name in named:
            self.assertTrue(os.path.isfile(os.path.join(PLUGIN, "commands", name + ".md"))
                            or os.path.isfile(os.path.join(PLUGIN, "skills", name, "SKILL.md")),
                            name)
