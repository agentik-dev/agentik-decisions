"""rr4, the fix of review 1 (C1 to C5): the resolver is bounded, a checkout git cannot answer
for falls back to no clone, `rows` reads a chain-named charter from the records, and a REPO
given as a subfolder or a link of a repo whose records are out is that repo, read once. Each
case reproduces one of review 1's probes in a temp clone and a temp holder."""
import io
import json
import os
import time
from unittest import mock

import decisions
from decisions import common
from tests import test_rr4_records as rr4
from tests.test_new import PARTS
from tests import test_rw2b_close as rw2b
from tests.test_rr4_records import KEY, NICE, Records, git, read, write


class FakeGit(Records):
    """A `git` first on PATH: `body` runs before it hands the call to the real one."""

    def fake(self, body):
        folder = os.path.join(self.tmp, "fake")
        path = os.path.join(folder, "git")
        write(path, "#!/bin/sh\n%s\nexec %s \"$@\"\n" % (body, rr4.GIT))
        os.chmod(path, 0o755)
        return mock.patch.dict(os.environ, {"PATH": folder + os.pathsep + os.environ["PATH"]})


class Bounded(FakeGit):
    """F1: a git that hangs on `worktree` made every verb wait; now GIT_TIMEOUT bounds it."""

    def hung(self, *argv):
        pids = os.path.join(self.tmp, "pids")
        body = ('for a in "$@"; do [ "$a" = worktree ] && echo $$ >> %s && exec sleep 8; done'
                % pids)
        with self.fake(body), mock.patch.object(common, "GIT_TIMEOUT", 1):
            start = time.monotonic()
            code, out, err = self.run_cli(*argv)
            took = time.monotonic() - start
        self.assertLess(took, 5, err)
        self.assertEqual(code, 2, out + err)
        self.assertIn("did not say within 1 s", err)
        self.assertEqual(len(err.strip().splitlines()), 1, err)
        for pid in read(pids).split():
            for _ in range(50):
                try:
                    os.kill(int(pid), 0)
                except ProcessLookupError:
                    break
                time.sleep(0.02)
            else:
                self.fail("git %s outlived the call" % pid)

    def test_a_read_past_the_bound_refuses(self):
        self.out()
        write(os.path.join(self.records, "NICE_TO_HAVE.md"), NICE)
        self.hung("backlog")

    def test_a_write_past_the_bound_refuses(self):
        self.ledger()
        self.hung("new", *PARTS)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "OPEN-QUESTIONS.md")))


class NoFallBack(FakeGit):
    """F4: a git that fails made a repo whose key is set read and write its clone."""

    def failing(self):
        return self.fake("exit 128")

    def test_a_write_refuses_and_writes_nothing(self):
        self.out()
        ledger = self.ledger()
        before = read(ledger)
        with self.failing():
            code, out, err = self.run_cli("new", "--ledger", ledger, *PARTS)
        self.assertEqual(code, 2, out + err)
        self.assertIn("git cannot say where", err)
        self.assertEqual(len(err.strip().splitlines()), 1, err)
        self.assertEqual(read(ledger), before)
        self.assertEqual(sorted(os.listdir(self.repo)), [".git", "DECISIONS.md", "README.md"])
        self.assertFalse(os.listdir(self.records))

    def test_a_read_finds_no_record_in_the_clone(self):
        self.out()
        write(os.path.join(self.repo, "NICE_TO_HAVE.md"), NICE)
        with self.failing():
            code, out, err = self.run_cli("backlog", self.repo)
        self.assertEqual(code, 0, err)
        self.assertNotIn("an old S4 on no step", out)
        self.assertIn("no NICE_TO_HAVE.md", out)

    def test_no_git_above_reads_as_own(self):
        plain = os.path.join(self.tmp, "plain")
        write(os.path.join(plain, "NICE_TO_HAVE.md"), NICE)
        with self.failing():
            code, out, err = self.run_cli("backlog", plain, cwd=plain)
        self.assertEqual(code, 0, err)
        self.assertIn("an old S4 on no step", out)


class OutCharter(rw2b.Depot):
    """F2: in `out`, `rows` read only a charter named for the whole row."""

    tree_of, text_of = rw2b.Cut.tree_of, rw2b.Cut.text_of  # the helpers, not Cut's cases

    def records(self):
        rec = os.path.join(os.path.realpath(self.tmp), "hold", "agentik-crate")
        os.makedirs(os.path.join(rec, "history", "sittings"))
        git(self.pear, "config", KEY, rec)
        return rec

    def charter_for(self, row, *names):
        self.tree_of(row)
        rec = self.records()
        for name in names:
            write(os.path.join(rec, "history", "sittings", name),
                  rw2b.CHARTER.format(name=name, unchecked="- [ ] the tests\n", next_act=""))
        self.crate(row)
        return self.view()[row]["cut"]["charter"]

    def test_a_chain_named_charter(self):
        self.assertEqual(self.charter_for("p5-crate", "2026-11-14-14-p5.md"),
                         "history/sittings/2026-11-14-14-p5.md")

    def test_a_plain_charter(self):
        self.assertEqual(self.charter_for("p7-crate", "2026-11-14-3.md"),
                         "history/sittings/2026-11-14-3.md")

    def test_the_newest_and_never_another_chains(self):
        self.assertEqual(self.charter_for("p5-crate", "2026-11-14-2-p5.md", "2026-11-14-14-p5.md",
                                          "2026-11-15-1-p6.md", "2026-11-14-9-p5-crate.md"),
                         "history/sittings/2026-11-14-14-p5.md")

    def test_the_text_reads_its_unchecked_line(self):
        self.charter_for("p5-crate", "2026-11-14-14-p5.md")
        self.assertEqual(self.view()["p5-crate"]["cut"]["unchecked"], ["- [ ] the tests"])
        self.assertIn("  charter history/sittings/2026-11-14-14-p5.md: 1 unchecked; next act: none",
                      self.text_of("p5-crate"))


class OutClose(rw2b.Depot):
    """Review 1: no case for `rows close` in `out`; its done file goes to the records."""

    def test_close_writes_the_done_file_in_the_records(self):
        rec = os.path.join(os.path.realpath(self.tmp), "hold", "depot")
        os.makedirs(os.path.join(rec, "history", "rows"))
        git(self.hq, "config", KEY, rec)
        self.root = os.path.join(rec, "history", "rows")
        self.pushed("p1-crate")
        here = os.getcwd()
        os.chdir(self.hq)
        try:
            out, err = io.StringIO(), io.StringIO()
            code = decisions.main(["rows", "close", "p1-crate", "-y"], out=out, err=err)
        finally:
            os.chdir(here)
        self.assertEqual(code, 0, err.getvalue())
        self.assertTrue(os.path.isfile(os.path.join(rec, "history", "handoff-done.md")))
        self.assertFalse(os.path.exists(os.path.join(self.hq, "history", "handoff-done.md")))


class OneRepoOnce(Records):
    """F3: a REPO given as a subfolder stayed a repo of its own in `out`."""

    def setUp(self):
        super().setUp()
        self.sub = os.path.join(self.repo, "sub")
        os.makedirs(self.sub)
        self.link = os.path.join(self.tmp, "link")
        os.symlink(self.repo, self.link)

    def nice(self):
        write(os.path.join(self.records, "NICE_TO_HAVE.md"), NICE)
        git(self.hold, "add", "repos/widget/NICE_TO_HAVE.md")
        git(self.hold, "commit", "-q", "-m", "nice")

    def test_backlog_reads_a_subfolder_and_a_link_once(self):
        self.out()
        self.nice()
        code, out, err = self.run_cli("backlog", self.repo, self.sub, self.link)
        self.assertEqual(code, 0, err)
        heads = [l for l in out.splitlines() if l.startswith("== ")]
        self.assertEqual(len(heads), 1, out)
        self.assertTrue(heads[0].startswith("== widget  "), out)
        self.assertEqual(out.count("an old S4 on no step"), 1, out)

    def test_expire_moves_once(self):
        self.out()
        self.nice()
        code, out, err = self.run_cli("expire", "--days", "14", "--write", self.repo, self.sub)
        self.assertEqual(code, 0, err)
        overflow = read(os.path.join(self.records, "history", "NICE-overflow.md"))
        self.assertEqual(overflow.count("an old S4 on no step"), 1)

    def test_questions_pairs_the_repos_ledger(self):
        self.out()
        self.ledger()
        rr4.Questions.asked(self, self.records)
        code, whole, err = self.run_cli("questions", "--json", self.repo)
        self.assertEqual(code, 0, err)
        code, both, err = self.run_cli("questions", "--json", self.repo, self.sub)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(both), json.loads(whole))
        code, alone, err = self.run_cli("questions", "--json", self.sub)
        self.assertEqual(json.loads(alone), json.loads(whole))

    def test_own_keeps_the_subfolder_apart(self):
        write(os.path.join(self.repo, "NICE_TO_HAVE.md"), NICE)
        code, out, err = self.run_cli("backlog", self.repo, self.sub)
        self.assertEqual(code, 0, err)
        self.assertIn("sub", out.replace("== widget", ""))
