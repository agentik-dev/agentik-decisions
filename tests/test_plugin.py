"""The plugin subtree (A8, d18, d23): the six commands, the two skills, respeak's
include file, no hook and no scripts, no data, and one version across the three manifests."""

import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugin")
SKILL = os.path.join(PLUGIN, "skills", "decisions", "SKILL.md")
ASK = os.path.join(PLUGIN, "skills", "ask", "SKILL.md")
COMMANDS = ("answer.md", "backlog.md", "find.md", "new.md", "render.md", "show.md")
VERSION = "0.9.0"
DESCRIBED = ("plugin/.claude-plugin/plugin.json",
             "pyproject.toml", "CLAUDE.md", "design/readme/source.md", "README.md",
             "src/decisions/__init__.py", "src/decisions/cli.py")


def split_frontmatter(text):
    """Return (frontmatter lines, body lines) of a markdown file."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return [], lines
    end = lines.index("---", 1)
    return lines[1:end], lines[end + 1:]


def description_of(front):
    """The frontmatter description, folded (`>`) or inline."""
    out = []
    grabbing = False
    for line in front:
        if line.startswith("description:"):
            value = line[len("description:"):].strip()
            if value not in (">", "|", ">-", "|-"):
                return value.strip("\"'")
            grabbing = True
            continue
        if grabbing:
            if line.startswith(" "):
                out.append(line.strip())
            else:
                break
    return " ".join(out)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class StructureTest(unittest.TestCase):

    def test_exactly_the_six_commands(self):
        self.assertEqual(sorted(os.listdir(os.path.join(PLUGIN, "commands"))), list(COMMANDS))

    def test_commands_under_thirty_lines_each_running_its_verb(self):
        for name in COMMANDS:
            text = read(os.path.join(PLUGIN, "commands", name))
            self.assertLess(len(text.splitlines()), 30, name)
            front, _ = split_frontmatter(text)
            self.assertIn("allowed-tools: Bash(agentik-decisions *)", front, name)
            self.assertTrue(description_of(front), name)
            self.assertIn("`agentik-decisions %s $ARGUMENTS`" % name[:-3], text, name)

    def test_no_hook_and_no_scripts(self):
        # d23 section 6: respeak's include file is the one file beside the two directories.
        self.assertEqual(sorted(os.listdir(PLUGIN)),
                         [".claude-plugin", "commands", "respeak-include.md", "skills"])

    def test_skill_sizes(self):
        front, body = split_frontmatter(read(SKILL))
        self.assertIn("name: decisions", front)
        self.assertIn("allowed-tools: Bash(agentik-decisions *)", front)
        description = description_of(front)
        self.assertTrue(description)
        self.assertLess(len(description), 200)
        self.assertLess(len(body), 500)

    def test_skill_serves_the_verbs_and_nothing_dropped(self):
        text = read(SKILL)
        for verb in ("show", "find", "new", "ask", "answer", "render", "backlog"):
            self.assertIn("`agentik-decisions %s" % verb, text, verb)
        for dropped in ("scope", "supersede", "INDEX.md", "governs", "hook", "front matter",
                        "decisions/", "record"):
            self.assertNotIn(dropped, text, dropped)
        self.assertIn("`agentik-decisions answer --amends`, on the owner's answer", text)
        self.assertNotIn("never edits", text)

    def test_ask_skill_drives_the_selector(self):
        """d18 section 1: the skill serves /decisions:ask, so no command shares its name."""
        self.assertEqual(sorted(os.listdir(os.path.join(PLUGIN, "skills"))), ["ask", "decisions"])
        front, body = split_frontmatter(read(ASK))
        self.assertIn("name: ask", front)
        self.assertIn("allowed-tools: Bash(agentik-decisions *), AskUserQuestion", front)
        self.assertLess(len(description_of(front)), 200)
        self.assertLess(len(body), 60)
        text = "\n".join(body)
        for needed in ("`agentik-decisions ask`", "`agentik-decisions answer N (--pick LABEL | --other TEXT)",
                       "back to back in one turn", "`afkTimeoutMs` is no answer",
                       "**Your answer:**"):
            self.assertIn(needed, text, needed)

    def test_ask_skill_names_source_and_area_choice(self):
        """d-n2 item 11 (L40, L51): the skill says what `--source` carries and how to pick
        `--area`, and enters a filled **Your answer:** line before it asks."""
        text = " ".join(read(ASK).split())
        for needed in ("`--source` carries", "the owner's word",
                       "which `agentik-decisions show --area NAME` lists, exiting 2, when NAME "
                       "matches none",
                       "run `agentik-decisions answer N` for it first"):
            self.assertIn(needed, text, needed)

    def test_answer_pages_carry_into(self):
        """Round 2 F1: the cross-repo ledger's block lives in the user-level CLAUDE.md, so
        both pages that run `answer` name `--into` and the skill says when to pass it."""
        front, _ = split_frontmatter(read(os.path.join(PLUGIN, "commands", "answer.md")))
        self.assertIn("| --no-entry) [--into PATH]", "\n".join(front))
        text = read(ASK)
        self.assertIn("| --no-entry) [--into PATH]`", text)
        for needed in ("user-level CLAUDE.md", "the same `--into` that `agentik-decisions render` uses"):
            self.assertIn(needed, " ".join(text.split()), needed)

    def test_one_version_in_the_three_manifests(self):
        # agentik-r1 5.2: the repo has no marketplace of its own; agentik-commons' lists it
        self.assertFalse(os.path.exists(os.path.join(ROOT, ".claude-plugin", "marketplace.json")))
        plugin = json.loads(read(os.path.join(PLUGIN, ".claude-plugin", "plugin.json")))
        project = re.search(r'(?m)^version = "([^"]+)"$', read(os.path.join(ROOT, "pyproject.toml")))
        self.assertEqual(plugin["version"], VERSION)
        self.assertEqual(project.group(1), VERSION)
        # d-n1: `agentik-decisions --version` and doctor's tool row read the package's own copy
        self.assertEqual(re.search(r'(?m)^VERSION = "([^"]+)"$', read(os.path.join(
            ROOT, "src", "decisions", "common.py"))).group(1), VERSION)

    def test_descriptions_name_six_verbs_plus_doctor(self):
        """F8: entry 4 of the cross-repo ledger names six verbs, the five commands and
        the ask skill; `doctor` stands beside them, never among them."""
        served = sorted([name[:-3] for name in COMMANDS if name != "backlog.md"] + ["ask"])
        self.assertEqual(served, ["answer", "ask", "find", "new", "render", "show"])
        for rel in DESCRIBED:
            text = read(os.path.join(ROOT, rel))
            with self.subTest(rel=rel):
                wrong = re.search(r"(?i)\b(four|five|seven) verbs\b[^.\n]*", text)
                self.assertIsNone(wrong, wrong and wrong.group(0))
                # A sentence runs to a period that no word follows, so `.md` stays inside.
                sentence = re.search(r"(?i)\bsix verbs\b(?:[^.]|\.(?=\w))*", text)
                self.assertIsNotNone(sentence, "no 'six verbs'")
                head = re.split(r"\bplus\b", sentence.group(0))[0]
                self.assertNotIn("doctor", head, sentence.group(0))
                if ":" in head:
                    for verb in served:
                        self.assertIn(verb, head, sentence.group(0))
                    self.assertIsNotNone(re.search(r"plus `?doctor`?", sentence.group(0)),
                                         sentence.group(0))

    def test_no_data_in_plugin(self):
        # The skill's own directory, skills/decisions/, is the layout's; any
        # other directory named decisions/ would be a repo's data.
        skill_dir = os.path.dirname(SKILL)
        for dirpath, dirnames, filenames in os.walk(PLUGIN):
            for name in dirnames:
                path = os.path.join(dirpath, name)
                if name == "decisions" and path != skill_dir:
                    self.fail("data directory in the plugin: %s" % path)
            self.assertNotIn("DECISIONS.md", filenames)


if __name__ == "__main__":
    unittest.main()
