"""`expire` (d34): a repo's closed NICE items, and its open S4 ones older than N days
on no open step, leave NICE_TO_HAVE.md for history/NICE-overflow.md, appended byte for
byte; a dry view by default; `--write` only once HEAD holds the file. Fixtures are
small repos built in temp directories, dated against today."""

import builtins
import datetime
import importlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import types
from collections import Counter
from unittest import mock

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


class Fixture(Hermetic):

    def setUp(self):
        super().setUp()
        self.fresh()

    def fresh(self):
        """A new temp directory holding the repo `tool`, its two files committed."""
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


class Expire(Fixture):

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
        self.assertEqual(sorted(v["repos"][0]), ["archive", "breaks", "bytes", "expired", "head",
                                                "kept", "lazy", "moved", "nice", "repo",
                                                "undated"])
        self.assertEqual((v["repos"][0]["breaks"], v["repos"][0]["lazy"]), (None, []))
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


class Stopped(Exception):
    """A stop no `except OSError` catches, as a kill leaves the files: no rollback runs."""


class ExpireLosesNothing(Fixture):
    """`--write` stopped or failed at each replace: NICE_TO_HAVE.md and the archive
    are each whole-old or whole-new, every line is in one of them, and the next run
    finishes the move without appending an item twice."""

    def read(self, path):
        if not os.path.exists(path):
            return None
        with open(path, "rb") as handle:
            return handle.read()

    def write_failing(self, at, fault):
        """`--write` with the at-th `os.replace` raising `fault`."""
        real, calls = os.replace, []

        def replace(src, dst):
            calls.append(dst)
            if len(calls) == at:
                raise fault
            return real(src, dst)

        with mock.patch("decisions.common.os.replace", replace):
            try:
                code, _, self.err = self.run_cli(self.repo, "--write")
                return code
            except Stopped:
                return None

    def finished(self):
        """NICE_TO_HAVE.md and the archive after one clean `--write` from this state."""
        code, _, err = self.run_cli(self.repo, "--write")
        self.assertEqual(code, 0, err)
        return self.read(self.nice), self.read(self.archive)

    def check_stop(self, at, fault, archive_before):
        old_nice = self.read(self.nice)
        code = self.write_failing(at, fault)
        nice, archive = self.read(self.nice), self.read(self.archive)
        self.assertEqual(nice, old_nice)
        done_nice, done_archive = self.finished()
        self.assertIn(archive, (archive_before, done_archive))
        if isinstance(fault, OSError):
            # No rollback: a failed first write leaves the archive as it was, a
            # failed second one leaves the items in both files.
            self.assertEqual(code, 2)
            self.assertEqual(archive == archive_before, at == 1)
            leftovers = [n for _, _, names in os.walk(self.repo)
                         for n in names if n.startswith(".decisions-")]
            self.assertEqual(leftovers, [])
        lines = old_nice.splitlines(keepends=True)
        self.assertTrue(all(x in done_nice or x in done_archive for x in lines))
        self.assertEqual(done_archive.count(lines[9]), 1)
        before = snapshot(self.top)
        self.assertEqual(self.run_cli(self.repo, "--write")[0], 0)
        self.assertEqual(self.read(self.nice), done_nice)
        self.assertEqual(self.read(self.archive), done_archive)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "expired")
        before = snapshot(self.top)
        code, out, _ = self.run_cli(self.repo, "--write")
        self.assertEqual((code, snapshot(self.top) == before), (0, True))
        self.assertTrue(out.startswith("== tool  expire: 0 closed, 0 S4"))

    def test_a_failed_replace_loses_nothing_and_leaves_no_temp(self):
        for at in (1, 2):
            with self.subTest(at=at):
                self.fresh()
                self.check_stop(at, OSError(28, "No space left on device"), None)

    def test_a_stop_at_either_replace_loses_nothing_and_appends_once(self):
        for at in (1, 2):
            with self.subTest(at=at):
                self.fresh()
                self.check_stop(at, Stopped(), None)

    def test_a_stop_with_an_archive_it_keeps_appends_once(self):
        os.makedirs(os.path.dirname(self.archive))
        with open(self.archive, "w", encoding="utf-8") as handle:
            handle.write("# kept\n\n- an older note, 2026-01-01\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "an archive")
        self.check_stop(2, Stopped(), self.read(self.archive))

    def test_crlf_lines_move_byte_for_byte(self):
        crlf = NICE.replace("\n", "\r\n")
        root = repo_at(os.path.join(self.top, "crlf"), {"NICE_TO_HAVE.md": crlf,
                                                         "HANDOFF.md": HANDOFF})
        code, _, err = self.run_cli(root, "--write")
        self.assertEqual(code, 0, err)
        lines = crlf.encode().splitlines(keepends=True)
        nice = self.read(os.path.join(root, "NICE_TO_HAVE.md"))
        archive = self.read(os.path.join(root, "history", "NICE-overflow.md"))
        gone = {9, 10, 15, 19, 20, 21}
        self.assertEqual(nice, b"".join(x for i, x in enumerate(lines, 1) if i not in gone))
        self.assertTrue(all(lines[n - 1] in archive for n in gone))
        # The lines the archive writes of its own take the line end of NICE's first.
        self.assertEqual([x for x in nl_lines(archive) if not x.endswith(b"\r\n")], [])



def nl_lines(data):
    """`data` cut at b"\n" alone, each line keeping it."""
    parts = data.split(b"\n")
    return [p + b"\n" for p in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def structural(line):
    """A line `expire` writes of its own: blank, a heading, the archive's lead, the
    NICE header."""
    return (not line.strip() or line.startswith((b"#", b"| id |", b"|---", b"Items moved")))


class Later(datetime.date):
    """`datetime.date` with today one day on."""

    @classmethod
    def today(cls):
        return TODAY + datetime.timedelta(days=1)


class ExpireFold(Fixture):
    """The refuter's reproductions (round 1), each a case: one read under the lock,
    bytes cut at a newline alone, two replaces with no rollback, a rerun that never
    appends an item twice, a bullet with a column-0 line kept."""

    read = ExpireLosesNothing.read
    write_failing = ExpireLosesNothing.write_failing

    def write_bytes(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(data)

    def at_repo(self, nice, archive=None, commit=True):
        """The fixture repo with `nice` (and `archive`) committed, or the archive left
        uncommitted when `commit` is false."""
        self.write_bytes(self.nice, nice)
        if archive is not None:
            self.write_bytes(self.archive, archive)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "shape")
        if archive is not None and not commit:
            git(self.repo, "rm", "-q", "--cached", os.path.relpath(self.archive, self.repo))
            git(self.repo, "commit", "-q", "-m", "archive out")

    def whole(self, nice_before, archive_before):
        """NICE before is NICE now plus the lines the archive gained, line for line, and
        no line of NICE before is twice in the archive."""
        nice, archive = self.read(self.nice), self.read(self.archive) or b""
        before, after, removed, i = nl_lines(nice_before), nl_lines(nice), [], 0
        for line in before:
            if i < len(after) and after[i] == line:
                i += 1
            else:
                removed.append(line if line.endswith(b"\n") else line + b"\n")
        self.assertEqual(i, len(after), "NICE now is not NICE before less some lines")
        old = archive_before or b""
        self.assertTrue(archive.startswith(old), "the archive's old bytes moved")
        gained = Counter(nl_lines(archive[len(old):]))
        self.assertEqual(Counter(removed) - gained, Counter(), "a moved line is lost")
        self.assertEqual([x for x in gained - Counter(removed) if not structural(x)], [])
        held_now, held_then = Counter(nl_lines(archive)), Counter(nl_lines(old))
        for line in removed:
            if not structural(line):
                self.assertEqual(held_now[line], held_then[line] + removed.count(line), line)
        return removed

    def stopped_then(self, *argv, **patches):
        """A stop between the two replaces, then `--write` again with `argv`."""
        nice, archive = self.read(self.nice), self.read(self.archive)
        self.write_failing(2, Stopped())
        if patches.get("commit"):
            git(self.repo, "add", "-A")
            git(self.repo, "commit", "-q", "-m", "the archive")
        code, _, err = self.run_cli(self.repo, "--write", *argv)
        self.assertEqual(code, 0, err)
        return self.whole(nice, archive)

    def test_f1_a_rerun_after_a_commit_appends_nothing_twice(self):
        removed = self.stopped_then(commit=True)
        self.assertEqual(len(removed), 6)

    def test_f1_a_rerun_with_other_days_appends_nothing_twice(self):
        removed = self.stopped_then("--days", "13")
        self.assertIn(nl_lines(NICE.encode())[10], removed)

    def test_f1_a_rerun_on_a_later_day_appends_nothing_twice(self):
        nice, archive = self.read(self.nice), self.read(self.archive)
        self.write_failing(2, Stopped())
        with mock.patch("decisions.expire.datetime", types.SimpleNamespace(date=Later)):
            self.assertEqual(self.run_cli(self.repo, "--write")[0], 0)
        self.assertIn(nl_lines(NICE.encode())[10], self.whole(nice, archive))

    def test_f1_an_item_held_only_as_the_head_of_another_is_appended(self):
        struck = nl_lines(NICE.encode())[20]
        for archive, appended in ((b"# kept\n\n" + struck + b"  with more.\n", 1),
                                  (b"# kept\n\n" + struck + b"\n  apart, more.\n", 1),
                                  (b"# kept\n\n" + struck + b"- another note\n", 0)):
            with self.subTest(archive=archive):
                self.fresh()
                self.at_repo(NICE.encode(), archive)
                self.assertEqual(self.run_cli(self.repo, "--write")[0], 0)
                self.assertEqual(self.read(self.archive).count(struck), 1 + appended)
                self.assertNotIn(struck, self.read(self.nice))

    def test_f2_a_line_break_not_at_a_newline_refuses(self):
        for char, line, shape in ((" ", 9, NICE.replace("the old lead", "the old lead")),
                                  ("\x0c", 19, NICE.replace("it says\n", "it\x0csays\n"))):
            with self.subTest(char=char):
                self.fresh()
                self.at_repo(shape.encode())
                before = snapshot(self.top)
                code, _, err = self.run_cli(self.repo, "--write")
                self.assertEqual(code, 2)
                self.assertIn("NICE_TO_HAVE.md:%d" % line, err)
                self.assertIn("U+%04X" % ord(char), err)
                self.assertEqual(snapshot(self.top), before)
                self.assertEqual(self.view()["repos"][0]["breaks"], line)
                code, out, _ = self.run_cli(self.repo)
                self.assertIn("--write refuses this repo: NICE_TO_HAVE.md:%d" % line, out)

    def test_f3_mixed_line_ends_keep_every_byte(self):
        mixed = NICE.replace("\n", "\r\n", 1).encode()
        old = b"# kept\r\n\r\n- an older note, 2026-01-01\n- and another\n"
        self.at_repo(mixed, old, commit=False)
        self.assertEqual(self.run_cli(self.repo, "--write")[0], 0)
        self.assertEqual(len(self.whole(mixed, old)), 6)
        self.assertEqual(self.read(self.nice).count(b"\r\n"), 1)

    def swap(self):
        """The closed n1 and the fresh n3 trade places, committed."""
        lines = nl_lines(self.read(self.nice))
        lines[8], lines[10] = lines[10], lines[8]
        self.write_bytes(self.nice, b"".join(lines))
        git(self.repo, "commit", "-q", "-am", "swap")

    def test_f4_a_commit_inside_the_run_moves_no_wrong_line(self):
        fresh = nl_lines(NICE.encode())[10]
        for where in ("decisions.backlog.view", "decisions.expire.checked",
                      "decisions.expire.held"):
            with self.subTest(where=where):
                self.fresh()
                module, name = where.rsplit(".", 1)
                real = getattr(importlib.import_module(module), name)
                calls = []

                def hooked(*args, real=real, **kwargs):
                    """The swap just after the hooked call reads or checks."""
                    result = real(*args, **kwargs)
                    if not calls:
                        calls.append(1)
                        self.swap()
                    return result

                with mock.patch(where, hooked):
                    code, _, err = self.run_cli(self.repo, "--write")
                self.assertIn(code, (0, 2), err)
                self.assertNotIn(fresh, self.read(self.archive) or b"")
                self.assertIn(fresh, self.read(self.nice))

    def test_f5_a_failed_second_write_loses_no_earlier_move(self):
        old = b"# kept\n\n- an item moved on an earlier day\n"
        real_open = builtins.open

        def opened(path, mode="r", *args, **kwargs):
            """A stop at the first in-place write of the archive, once truncated."""
            handle = real_open(path, mode, *args, **kwargs)
            if "w" in mode and str(path).endswith("NICE-overflow.md"):
                handle.close()
                raise Stopped()
            return handle

        for fault, inside in ((OSError(28, "No space left on device"), False),
                              (Stopped(), False), (OSError(28, "No space"), True)):
            with self.subTest(fault=type(fault).__name__, inside=inside):
                self.fresh()
                self.at_repo(NICE.encode(), old, commit=False)
                with mock.patch("builtins.open", opened if inside else real_open):
                    code = self.write_failing(2, fault)
                self.assertIn(code, (2, None) if inside else (
                    2 if isinstance(fault, OSError) else None,))
                if code == 2:
                    self.assertIn("run --write again to finish", self.err)
                    self.assertNotIn("nothing written", self.err)
                self.assertEqual(self.read(self.nice), NICE.encode())
                self.assertTrue(self.read(self.archive).startswith(old))
                leftovers = [n for _, _, names in os.walk(self.repo)
                             for n in names if n.startswith(".decisions-")]
                self.assertEqual(leftovers, [])
                self.assertEqual(self.run_cli(self.repo, "--write")[0], 0)
                self.assertEqual(len(self.whole(NICE.encode(), old)), 6)

    def test_f6_a_bullet_with_a_column_zero_line_is_kept_and_listed(self):
        lazy = NICE + "- An old note, %s, that wraps\nonto a second line at column 0.\n" % ago(30)
        self.at_repo(lazy.encode())
        v = self.view()["repos"][0]
        self.assertEqual([(e["line"], e["next"]) for e in v["lazy"]], [(23, 24)])
        self.assertNotIn(23, self.lines(self.view(), "expired"))
        out = self.run_cli(self.repo)[1]
        self.assertIn("NICE_TO_HAVE.md:23", out)
        self.assertEqual(self.run_cli(self.repo, "--write")[0], 0)
        self.assertIn(b"that wraps\nonto a second line at column 0.\n", self.read(self.nice))
        self.assertNotIn(b"that wraps", self.read(self.archive))
        self.whole(lazy.encode(), None)

    def test_f7_a_last_line_with_no_newline_gains_one_in_the_archive(self):
        tail = "- ~~Another struck note.~~ %s" % ago(2)
        self.at_repo((NICE + tail).encode())
        self.assertEqual(self.run_cli(self.repo, "--write")[0], 0)
        self.assertTrue(self.read(self.archive).endswith(tail.encode() + b"\n"))
        self.assertEqual(self.read(self.nice), b"".join(
            x for i, x in enumerate(nl_lines(NICE.encode()), 1) if i not in {9, 10, 15, 19, 20, 21}))
        self.whole((NICE + tail).encode(), None)

    def test_f7_an_edit_at_the_lock_is_read_there(self):
        for which in ("nice", "archive", "head"):
            with self.subTest(which=which):
                self.fresh()
                real, path = decisions.expire.held, getattr(self, which, None)

                def hooked(*args, path=path, **kwargs):
                    if path is None:
                        git(self.repo, "rm", "-q", "--cached", "NICE_TO_HAVE.md")
                        git(self.repo, "commit", "-q", "-m", "untracked, the bytes kept")
                    else:
                        with open(path, "ab") as handle:
                            handle.write(b"- edited under the run\n")
                    return real(*args, **kwargs)

                os.makedirs(os.path.dirname(self.archive), exist_ok=True)
                with mock.patch("decisions.expire.held", hooked):
                    code, _, err = self.run_cli(self.repo, "--write")
                if which != "archive":
                    self.assertEqual((code, self.read(self.archive)), (2, None))
                    self.assertIn("changed under the run" if path else "HEAD does not hold",
                                  err)
                else:
                    self.assertEqual(code, 0, err)
                    self.assertTrue(self.read(self.archive).startswith(
                        b"- edited under the run\n\n## "))


class ExpireFoldTwo(Fixture):
    """The refuter's reproductions (round 2), each a case: an archive whose real path
    lies outside the repo is refused before any write; a repo named twice is taken
    once; a broken line in any repo given refuses every repo; the mode of each file is
    kept; an archive line holding a lone CR holds no item."""

    read = ExpireLosesNothing.read
    write_bytes = ExpireFold.write_bytes
    at_repo = ExpireFold.at_repo
    struck = nl_lines(NICE.encode())[20]

    def other(self, name, nice=NICE):
        return repo_at(os.path.join(self.top, name), {"NICE_TO_HAVE.md": nice, "HANDOFF.md": HANDOFF})

    def linked(self, repo, target):
        os.makedirs(os.path.join(repo, "history"), exist_ok=True)
        os.symlink(target, os.path.join(repo, "history", "NICE-overflow.md"))

    def test_r2_f1_an_archive_outside_the_repo_is_refused_before_any_write(self):
        shared = os.path.join(self.top, "shared.md")
        self.write_bytes(shared, b"# NICE_TO_HAVE.md overflow\n")
        other, clean = self.other("other"), self.other("clean")
        self.linked(self.repo, shared)
        self.linked(other, shared)
        before = snapshot(self.top)
        for argv in ((self.repo,), (other,), (self.repo, other), (clean, other)):
            with self.subTest(argv=argv):
                code, _, err = self.run_cli(*argv + ("--write",))
                self.assertEqual(code, 2)
                self.assertIn("lies outside", err)
                self.assertIn("nothing written", err)
                self.assertEqual(snapshot(self.top), before)
        code, _, err = self.run_cli(self.repo, "--write")
        self.assertEqual(err.strip(), "decisions: expire: %s: its real path %s lies outside %s; "
                         "nothing written" % (os.path.realpath(self.repo) + "/history/NICE-overflow.md",
                                              os.path.realpath(shared), os.path.realpath(self.repo)))
        self.fresh()
        outside = os.path.join(self.top, "elsewhere")
        os.makedirs(outside)
        os.symlink(outside, os.path.join(self.repo, "history"))
        before = snapshot(self.top)
        code, _, err = self.run_cli(self.repo, "--write")
        self.assertEqual((code, snapshot(self.top)), (2, before))
        self.assertIn("lies outside", err)

    def test_r2_f1_a_link_inside_the_repo_keeps_working(self):
        os.makedirs(os.path.join(self.repo, "notes"))
        self.write_bytes(os.path.join(self.repo, "notes", "overflow.md"), b"# kept\n")
        self.linked(self.repo, os.path.join("..", "notes", "overflow.md"))
        code, _, err = self.run_cli(self.repo, "--write")
        self.assertEqual(code, 0, err)
        self.assertTrue(os.path.islink(self.archive))
        self.assertIn(self.struck, self.read(os.path.join(self.repo, "notes", "overflow.md")))
        self.assertNotIn(self.struck, self.read(self.nice))

    def test_r2_f2_a_repo_named_twice_is_taken_once(self):
        for spelling in ("same", "slash", "link"):
            with self.subTest(spelling=spelling):
                self.fresh()
                second = {"same": self.repo, "slash": self.repo + "/",
                          "link": os.path.join(self.top, "alias")}[spelling]
                if spelling == "link":
                    os.symlink(self.repo, second)
                code, out, err = self.run_cli(self.repo, second, "--write")
                self.assertEqual(code, 0, err)
                self.assertEqual(out.count("== tool "), 1)
                self.assertEqual(out.count("expire: moved "), 1)
                self.assertEqual(self.read(self.archive).count(self.struck), 1)
                self.assertNotIn(self.struck, self.read(self.nice))
        self.fresh()
        code, out, err = self.run_cli(self.repo, self.repo + "/", "--write", "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual([r["moved"] for r in json.loads(out)["repos"]], [True])

    def test_r2_f3_a_break_in_a_repo_with_nothing_to_move_refuses_every_repo(self):
        quiet = self.other("quiet", "# N\n\n- A fresh note,\x0c %s.\n" % ago(1))
        self.assertEqual(self.view(quiet)["repos"][0]["expired"], [])
        before = snapshot(self.top)
        code, _, err = self.run_cli(self.repo, quiet, "--write")
        self.assertEqual((code, snapshot(self.top)), (2, before))
        self.assertIn("%s: NICE_TO_HAVE.md:3 breaks at U+000C" % os.path.realpath(quiet), err)
        self.assertIn("nothing written", err)

    def test_r2_f9_the_mode_of_each_file_is_kept(self):
        umask = os.umask(0)
        os.umask(umask)
        for old in (None, b"# kept\n"):
            with self.subTest(archive=old):
                self.fresh()
                os.chmod(self.nice, 0o640)
                if old is not None:
                    self.write_bytes(self.archive, old)
                    os.chmod(self.archive, 0o604)
                self.assertEqual(self.run_cli(self.repo, "--write")[0], 0)
                mode = lambda p: os.stat(p).st_mode & 0o7777
                self.assertEqual(mode(self.nice), 0o640)
                self.assertEqual(mode(self.archive), 0o666 & ~umask if old is None else 0o604)

    def test_r2_f9_an_archive_line_with_a_lone_cr_holds_no_item(self):
        old = b"# kept\n\nan older note\r" + self.struck
        self.at_repo(NICE.encode(), old)
        self.assertEqual(self.run_cli(self.repo, "--write")[0], 0)
        archive = self.read(self.archive)
        self.assertTrue(archive.startswith(old))
        self.assertEqual(archive.count(self.struck), 2)
        self.assertNotIn(self.struck, self.read(self.nice))
