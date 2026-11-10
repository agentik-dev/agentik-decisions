"""`audit` (d33): the ledger's retire and rewrite candidates, marks P1 to P8 of hq
design/08 section 4, on small fixture ledgers built in temp directories. The verb
prints candidates and writes nothing; the Every session entries print first, each
with the bytes it costs in the rendered block; the text ends naming the owner's way
to act (`new`, `ask`, `answer`)."""

import io
import json
import os
import shutil
import subprocess
import tempfile

import decisions
from decisions import render
from decisions.common import read_text
from decisions.ledger import parse
from tests.hermetic import Hermetic

GIT = shutil.which("git") or "/usr/bin/git"
HEAD = "# Decisions\n\n## In force\n\n"


def entry(n, title, body, tail):
    return "%d. **%s.** %s (%s)\n" % (n, title, body, tail)


def filler(start, count, area="The work"):
    """`count` plain entries from `start` under `### area`: no mark among them."""
    lines = ["### %s\n\n" % area]
    for n in range(start, start + count):
        lines.append(entry(n, "Plain rule %s" % chr(ord("a") + n % 26),
                           "The tool keeps rule %d as a plain product rule." % n,
                           "2026-10-01; the owner"))
    return "".join(lines) + "\n"


def tree_repo(root, files):
    """A git repo at `root` holding `files`, committed, with no global config."""
    os.makedirs(root, exist_ok=True)
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    for path, text in files.items():
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(text)
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "fixture"]):
        subprocess.run([GIT, "-c", "user.name=f", "-c", "user.email=f",
                        "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"] + args,
                       cwd=root, env=env, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def snapshot(top):
    found = {}
    for where, _, names in os.walk(top):
        for name in names:
            path = os.path.join(where, name)
            with open(path, "rb") as handle:
                found[path] = (handle.read(), os.stat(path).st_mtime_ns)
    return found


EVERY = ("### Every session\n\n"
         + entry(1, "Short rule", "One sentence.",
                 "2026-09-01; amended 2026-09-02, a; amended 2026-09-03, b; "
                 "amended 2026-09-04, c")
         + entry(2, "Clean rule", "The tool reads one file and prints one line.",
                 "2026-09-01; the owner") + "\n")
OTHERS = ("### The work\n\n"
          + entry(3, "Moved rule", "The tool prints the moved rule whole.",
                  "2026-09-29; moved from atlas entry 1, 2026-09-29")
          + entry(4, "Here rule", "The tool prints the rule that came here.",
                  "2026-10-17; atlas entry 26 until 2026-10-17, moved here under entry 4")
          + entry(5, "Mentions move", "A file moved from one place to another stays one file.",
                  "2026-10-01; the owner")
          + entry(6, "Long tail", "Short body.",
                  "2026-10-01; the owner's answer to decision 9, recorded in a very long "
                  "source clause")
          + entry(7, "Folded tail", "The tool folds the tail of an entry amended often.",
                  "2026-09-25; amended 2 times, 2026-10-13 to 2026-11-01; amended 2026-11-09, "
                  "the owner")
          + entry(8, "Two amends", "The tool keeps an entry amended twice as it stands.",
                  "2026-09-25; amended 2026-10-01, a; amended 2026-10-02, b")
          + entry(9, "Gone path", "The tool reads `docs/gone.md` and `docs/here.md`.",
                  "2026-10-01; the owner")
          + entry(10, "Gone verb", "Run `agentik decisions frobnicate` after "
                  "`agentik decisions render` and `agentik decisions show N`.", "2026-10-01; the owner")
          + entry(11, "Placeholder path", "A charter is `history/sittings/<date>-<n>.md`.",
                  "2026-10-01; the owner")
          + entry(12, "The session budget ceiling", "The tool counts turns.",
                  "2026-10-01; the owner")
          + entry(13, "The session budget", "The tool counts tokens.", "2026-10-01; the owner")
          + "\n")


class Audit(Hermetic):

    def setUp(self):
        super().setUp()
        self.top = tempfile.mkdtemp(prefix="decisions-d33-")
        self.addCleanup(shutil.rmtree, self.top, True)
        self.repo = os.path.join(self.top, "ledger-hq")
        tree_repo(self.repo, {"DECISIONS.md": HEAD + EVERY + OTHERS,
                              "docs/here.md": "x\n",
                              "notes.md": "See entry 1, entries 2, 3 and 5; hq 6.\n"})
        self.ledger = os.path.join(self.repo, "DECISIONS.md")

    def run_cli(self, *argv, ledger=None):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["--ledger", ledger or self.ledger, "audit"] + list(argv),
                              out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def text(self, *argv, ledger=None):
        code, out, err = self.run_cli(*argv, ledger=ledger)
        self.assertEqual(code, 0, err)
        return out

    def view(self, *argv, ledger=None):
        return json.loads(self.text("--json", *argv, ledger=ledger))

    def marks(self, view, number):
        for found in view["candidates"]:
            if found["number"] == number:
                return [m["mark"] for m in found["marks"]]
        return []

    # P1: the ledger at its cap of 25 in force.
    def test_p1_at_the_cap(self):
        full = os.path.join(self.top, "full.md")
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(HEAD + filler(1, 25))
        self.assertTrue(self.view(ledger=full)["at_cap"])
        self.assertIn("25 of 25 in force (P1, at the cap)", self.text(ledger=full))
        under = os.path.join(self.top, "under.md")
        with open(under, "w", encoding="utf-8") as handle:
            handle.write(HEAD + filler(1, 24))
        self.assertFalse(self.view(ledger=under)["at_cap"])
        self.assertNotIn("P1", self.text(ledger=under))

    # P2: amended three or more times, either tail form.
    def test_p2_amended_three_times(self):
        view = self.view()
        self.assertIn("P2", self.marks(view, 1))
        self.assertIn("P2", self.marks(view, 7))
        self.assertNotIn("P2", self.marks(view, 8))

    # P3: a tail that says the entry moved; a body that says "moved from" is no mark.
    def test_p3_moved_tail(self):
        view = self.view()
        self.assertIn("P3", self.marks(view, 3))
        self.assertIn("P3", self.marks(view, 4))
        self.assertNotIn("P3", self.marks(view, 5))

    # P4: a tail longer than its body, in bytes.
    def test_p4_tail_longer_than_body(self):
        view = self.view()
        self.assertIn("P4", self.marks(view, 6))
        self.assertNotIn("P4", self.marks(view, 2))

    # P5: an entry no file of the tree cites; its own line is no citation.
    def test_p5_uncited_in_the_tree(self):
        other = os.path.join(self.top, "other")
        tree_repo(other, {"README.md": "ledger-hq entry 7 and ledger 8 and hq 9.\n"})
        view = self.view(self.repo, other)
        cited = (1, 2, 3, 5, 6, 7, 8, 9)
        for n in cited:
            self.assertNotIn("P5", self.marks(view, n), n)
        for n in (4, 10, 11, 12, 13):
            self.assertIn("P5", self.marks(view, n), n)
        # Alone, the ledger's repo is the tree: other's citations of 7 to 9 are not read.
        alone = self.view()
        self.assertIn("P5", self.marks(alone, 7))

    def test_p5_tree_file_of_suite_shape(self):
        other = os.path.join(self.top, "other")
        tree_repo(other, {"README.md": "ledger-hq entry 7.\n"})
        tree = os.path.join(self.repo, "suite.json")
        with open(tree, "w", encoding="utf-8") as handle:
            json.dump({"repos": [{"name": "ledger-hq"}, {"name": "other"},
                                 {"name": "absent"}]}, handle)
        view = self.view("--tree", tree)
        self.assertNotIn("P5", self.marks(view, 7))
        self.assertEqual([os.path.basename(r) for r in view["tree"]], ["ledger-hq", "other"])
        self.assertEqual([os.path.basename(r) for r in view["not_read"]], ["absent"])
        self.assertIn("not read: absent", self.text("--tree", tree))

    # P6: a backticked path that resolves nowhere, or a decisions verb the tool lacks.
    def test_p6_gone_path_and_verb(self):
        view = self.view()
        self.assertIn("P6", self.marks(view, 9))
        self.assertIn("P6", self.marks(view, 10))
        self.assertNotIn("P6", self.marks(view, 11))
        found = [c for c in view["candidates"] if c["number"] == 9][0]
        evidence = " ".join(m["evidence"] for m in found["marks"] if m["mark"] == "P6")
        self.assertIn("docs/gone.md", evidence)
        self.assertNotIn("docs/here.md", evidence)
        found = [c for c in view["candidates"] if c["number"] == 10][0]
        evidence = " ".join(m["evidence"] for m in found["marks"] if m["mark"] == "P6")
        self.assertIn("frobnicate", evidence)
        self.assertNotIn("render", evidence)

    # P7: the tool does not detect it; it says so, and names the reader who confirms it.
    def test_p7_named_not_detected(self):
        view = self.view()
        self.assertIn("P7", view["not_detected"])
        self.assertTrue(all(m["mark"] != "P7" for c in view["candidates"] for m in c["marks"]))
        self.assertIn("not detected: P7", self.text())

    # P8: two entries sharing most title words, printed as a lead, never a candidate.
    def test_p8_title_overlap_is_a_lead(self):
        view = self.view()
        pairs = [tuple(lead["numbers"]) for lead in view["leads"] if lead["mark"] == "P8"]
        self.assertIn((12, 13), pairs)
        self.assertNotIn("P8", self.marks(view, 12))
        out = self.text()
        self.assertIn("Leads, for a reader to confirm:", out)
        self.assertLess(out.index("Leads, for a reader to confirm:"), out.index("P8 12"))

    # Ordering 1: Every session candidates first, each with its bytes in the block.
    def test_every_session_first_with_block_bytes(self):
        view = self.view()
        numbers = [c["number"] for c in view["candidates"]]
        self.assertEqual(numbers[0], 1)
        self.assertTrue(view["candidates"][0]["every_session"])
        block = render.block(parse(read_text(self.ledger)),
                             self.ledger, os.path.join(self.repo, "CLAUDE.md"))
        line = [x for x in block.splitlines() if x.startswith("1. **Short rule.**")][0]
        self.assertEqual(view["candidates"][0]["bytes"], len(line.encode()) + 1)
        other = [c for c in view["candidates"] if c["number"] == 3][0]
        self.assertEqual(other["bytes"], len("- 3 Moved rule (The work)\n".encode()))
        out = self.text()
        self.assertLess(out.index("Every session, paid every turn:"),
                        out.index("Other entries in force:"))
        self.assertIn("1 Short rule  %d B" % (len(line.encode()) + 1), out)
        self.assertLess(out.index("1 Short rule"), out.index("3 Moved rule"))

    # Ordering 2: it edits nothing, and its text ends naming new, ask and answer.
    def test_writes_nothing_and_ends_with_the_owner_way(self):
        before = snapshot(self.top)
        out = self.text()
        self.text("--json")
        self.assertEqual(snapshot(self.top), before)
        last = out.rstrip("\n").splitlines()[-1]
        for word in ("audit edits nothing", "`agentik decisions new`", "`ask`", "`answer`",
                     "--amends", "## Superseded"):
            self.assertIn(word, last)

    def test_exit_two_for_usage(self):
        code, _, err = self.run_cli(os.path.join(self.top, "nowhere"))
        self.assertEqual((code, "audit: %s is not a directory" % os.path.join(self.top, "nowhere")
                          in err), (2, True))
        code, _, err = self.run_cli("--tree", os.path.join(self.top, "none.json"))
        self.assertEqual((code, "audit: --tree" in err), (2, True))
        self.assertEqual(self.run_cli(ledger=os.path.join(self.top, "absent.md"))[0], 2)
