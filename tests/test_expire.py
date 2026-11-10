"""`expire` (d34): a repo's closed NICE items, and its open S4 ones older than N days
on no open step, leave NICE_TO_HAVE.md for history/NICE-overflow.md, appended byte for
byte; a dry view by default; `--write` only once HEAD holds the file. Fixtures are
small repos built in temp directories, dated against today."""

import datetime
import io
import json
import os
import shutil
import subprocess
import tempfile

import decisions
from tests.hermetic import Hermetic

GIT = shutil.which("git") or "/usr/bin/git"
TODAY = datetime.date.today()


def ago(days):
    return (TODAY - datetime.timedelta(days=days)).isoformat()


HEADER = ("| id | level | area | finding | evidence | from |\n"
          "|---|---|---|---|---|---|\n")


def row(ident, level, area, finding, date):
    return "| %s | %s | %s | %s | `x.py:1` | %s, a review |\n" % (ident, level, area, finding, date)


NICE = ("# Nice to have\n\nFindings that block nothing; the archive is "
        "history/NICE-overflow.md.\n\n## Rows\n\n" + HEADER
        + row("n1", "S4", "`a.py`", "Closed %s abc1234: the old lead" % ago(1), ago(1))
        + row("n2", "S4", "`b.py`", "an old S4 on no step", ago(15))
        + row("n3", "S4", "`c.py`", "an S4 at the bound", ago(14))
        + row("n4", "S3", "`d.py`", "an old S3", ago(40))
        + row("n5", "S4", "`on/path.py`", "an old S4 on an open step's path", ago(40))
        + row("n6", "S4", "`e.py`", "an S4 with no date", "the review")
        + row("n7", "S4", "`gone/step.py`", "an old S4 on a done step's path", ago(40))
        + "\n## Bullets\n\n"
        + "- An unlevelled old note, %s: it says\n  more on a second line.\n" % ago(30)
        + "- ~~A struck note.~~ %s\n" % ago(2)
        + "- S2: a fresh S2 note, %s.\n" % ago(3))
HANDOFF = ("# Handoff\n\nThe build order.\n\n<!-- decisions: build order -->\n\n"
           "## The build order\n\n| # | item | level | repo | where | state |\n"
           "|---|---|---|---|---|---|\n"
           "| 1 | the open step | S3 | tool | `on/path.py` | open |\n"
           "| 2 | the done step | S3 | tool | `gone/step.py` | done 2026-01-01 abc |\n")


def git(root, *args):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.run([GIT, "-c", "user.name=f", "-c", "user.email=f",
                           "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]
                          + list(args), cwd=root, env=env, check=True,
                          capture_output=True, text=True).stdout


def repo_at(root, files):
    os.makedirs(root, exist_ok=True)
    for path, text in files.items():
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "fixture")
    return root


def snapshot(top):
    found = {}
    for where, dirs, names in os.walk(top):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in names:
            path = os.path.join(where, name)
            with open(path, "rb") as handle:
                found[path] = handle.read()
    return found


class Expire(Hermetic):

    def setUp(self):
        super().setUp()
        self.top = tempfile.mkdtemp(prefix="decisions-d34-")
        self.addCleanup(shutil.rmtree, self.top, True)
        self.repo = repo_at(os.path.join(self.top, "tool"),
                            {"NICE_TO_HAVE.md": NICE, "HANDOFF.md": HANDOFF})
        self.nice = os.path.join(self.repo, "NICE_TO_HAVE.md")
        self.archive = os.path.join(self.repo, "history", "NICE-overflow.md")

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = decisions.main(["expire"] + list(argv), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def view(self, *argv):
        code, out, err = self.run_cli(*(argv or (self.repo,)) + ("--json",))
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def lines(self, view, key):
        return [e["line"] for e in view["repos"][0][key]]

    def test_closed_items_expire_whatever_their_date(self):
        v = self.view()
        closed = [e for e in v["repos"][0]["expired"] if e["reason"] == "closed"]
        self.assertEqual([(e["line"], e["id"]) for e in closed], [(9, "n1"), (21, None)])
        self.assertEqual(closed[0]["title"], "the old lead")

    def test_old_s4_and_unlevelled_expire_past_the_bound(self):
        v = self.view()
        aged = [(e["line"], e["level"], e["age"]) for e in v["repos"][0]["expired"]
                if e["reason"] == "aged"]
        self.assertEqual(aged, [(10, "S4", 15), (15, "S4", 40), (19, None, 30)])
        self.assertNotIn(11, self.lines(v, "expired"))
        v = self.view(self.repo, "--days", "30")
        self.assertEqual([e["line"] for e in v["repos"][0]["expired"]
                          if e["reason"] == "aged"], [15])

    def test_s1_to_s3_and_an_open_steps_path_are_kept_and_listed(self):
        v = self.view()
        kept = v["repos"][0]["kept"]
        self.assertEqual([(e["line"], e["level"]) for e in kept], [(12, "S3"), (13, "S4")])
        self.assertEqual(kept[1]["after_step"], 1)
        code, out, _ = self.run_cli(self.repo)
        self.assertIn("kept, older than 14 days (S1 to S3, or on an open step's path): "
                      "lift each into HANDOFF.md or close it", out)
        self.assertIn("S3 %s 40d  NICE_TO_HAVE.md:12  n4  an old S3" % ago(40), out)

    def test_an_item_with_no_date_never_expires(self):
        v = self.view(self.repo, "--days", "1")
        self.assertEqual(v["repos"][0]["undated"], [14])
        self.assertNotIn(14, self.lines(v, "expired"))

    def test_dry_by_default_writes_nothing(self):
        before = snapshot(self.top)
        code, out, _ = self.run_cli(self.repo)
        self.assertEqual(code, 0)
        self.assertEqual(snapshot(self.top), before)
        self.assertTrue(out.splitlines()[0].startswith(
            "== tool  expire: 2 closed, 3 S4 older than 14 days on no open step"))
        self.assertEqual(out.splitlines()[-1], "dry: nothing written; --write moves these 5, "
                         "appended byte for byte, to history/NICE-overflow.md")
        self.assertFalse(self.view()["write"])

    def test_write_moves_each_line_byte_for_byte(self):
        old = NICE.splitlines(keepends=True)
        gone = {9, 10, 15, 19, 20, 21}
        code, out, err = self.run_cli(self.repo, "--write")
        self.assertEqual(code, 0, err)
        with open(self.nice, encoding="utf-8", newline="") as handle:
            self.assertEqual(handle.read(), "".join(x for i, x in enumerate(old, 1)
                                                    if i not in gone))
        with open(self.archive, encoding="utf-8", newline="") as handle:
            archive = handle.read()
        self.assertTrue(archive.startswith("# NICE_TO_HAVE.md overflow\n"))
        self.assertIn("## %s: `expire --days 14`, from " % TODAY.isoformat(), archive)
        moved = "".join(old[n - 1] for n in (9, 10, 15))
        self.assertIn(HEADER + moved, archive)
        self.assertIn("".join(old[n - 1] for n in (19, 20, 21)), archive)
        sha = git(self.repo, "rev-parse", "--short", "HEAD").strip()
        self.assertEqual(out.splitlines()[-1], "expire: moved 5 items from NICE_TO_HAVE.md (%s B to %s B) to "
                         "history/NICE-overflow.md; %s holds them too"
                         % ("{:,}".format(len(NICE.encode())),
                            "{:,}".format(len(NICE.encode()) - len(
                                "".join(old[n - 1] for n in gone).encode())), sha))

    def test_write_again_moves_nothing(self):
        self.run_cli(self.repo, "--write")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "expired")
        before = snapshot(self.top)
        code, out, _ = self.run_cli(self.repo, "--write")
        self.assertEqual((code, snapshot(self.top) == before), (0, True))
        self.assertTrue(out.startswith("== tool  expire: 0 closed, 0 S4"))

    def test_write_appends_to_an_archive_it_keeps(self):
        os.makedirs(os.path.dirname(self.archive))
        with open(self.archive, "w", encoding="utf-8") as handle:
            handle.write("# kept\n\n| n0 | S4 | x | an older row | y | 2026-01-01 |")
        self.assertEqual(self.run_cli(self.repo, "--write")[0], 0)
        with open(self.archive, encoding="utf-8") as handle:
            archive = handle.read()
        self.assertTrue(archive.startswith(
            "# kept\n\n| n0 | S4 | x | an older row | y | 2026-01-01 |\n\n## "))
        self.assertNotIn("# NICE_TO_HAVE.md overflow", archive)

    def test_write_refuses_unless_head_holds_the_file(self):
        clean = repo_at(os.path.join(self.top, "clean"), {"NICE_TO_HAVE.md": NICE})
        with open(self.nice, "a", encoding="utf-8") as handle:
            handle.write("- An edit HEAD lacks, %s.\n" % ago(90))
        before = snapshot(self.top)
        code, _, err = self.run_cli(clean, self.repo, "--write")
        self.assertEqual(code, 2)
        self.assertIn("HEAD does not hold %s as it stands; commit it first; nothing written"
                      % os.path.realpath(self.nice), err)
        self.assertEqual(snapshot(self.top), before)

    def test_json_names_each_move(self):
        v = self.view()
        self.assertEqual(sorted(v), ["days", "repos", "skipped", "today", "write"])
        self.assertEqual(sorted(v["repos"][0]), ["archive", "bytes", "expired", "head", "kept",
                                                "moved", "nice", "repo", "undated"])
        first = v["repos"][0]["expired"][0]
        self.assertEqual(sorted(first), ["age", "date", "end", "id", "level", "line",
                                         "reason", "title"])
        self.assertEqual([(e["line"], e["end"]) for e in v["repos"][0]["expired"]][-2],
                         (19, 20))

    def test_order_file_stands_for_the_handoff(self):
        order = os.path.join(self.top, "ORDER.md")
        with open(order, "w", encoding="utf-8") as handle:
            handle.write(HANDOFF.replace("on/path.py", "elsewhere.py"))
        v = self.view(self.repo, "--order", order)
        self.assertIn(13, self.lines(v, "expired"))

    def test_exit_two_for_usage(self):
        nowhere = os.path.join(self.top, "nowhere")
        code, _, err = self.run_cli(nowhere)
        self.assertEqual((code, "expire: %s is not a directory" % nowhere in err), (2, True))
        code, _, err = self.run_cli(self.repo, "--order", nowhere)
        self.assertEqual((code, "expire: --order" in err), (2, True))
        self.assertEqual(self.run_cli(self.repo, "--days", "0")[0], 2)
        self.assertEqual(self.run_cli(self.repo, "--days", "x")[0], 2)
