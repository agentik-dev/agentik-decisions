"""bk1 (packet design/packets/bk1-reads-fit.md): `backlog`, `questions` and `expire` start every
repo's resolver child at once through `common.records_prime`, and one `rows` read asks git each
read-only question once. Every repo is made here under the temp folder, with made-up names; git
runs under the hermetic home, so no live config is read."""
import contextlib
import errno
import io
import json
import os
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from unittest import mock

import decisions
from decisions import backlog, common, expire, questions_read, rows as rows_module
from tests.hermetic import Hermetic
from tests.test_d39_backlog_check import QUESTIONS
from tests.test_rr4_records import KEY, NICE, git, write
from tests.test_rw2_rows import Rows
from tests.test_rw2b_close import Depot

NAMES = ("plum-1", "plum-2", "plum-3", "plum-4", "plum-5", "plum-6")
SLOW = "import time\ntime.sleep(0.3)\n" + common._CHILD


def unprimed():
    """The three callers with no prime, as at the pin: what each output is held against."""
    stack = contextlib.ExitStack()
    for module in (backlog, questions_read, expire):
        stack.enter_context(mock.patch.object(module, "records_prime", lambda folders: None,
                                              create=True))
    return stack


def spied(log):
    """`common._start` and `common._collect`, each logging its call to `log`."""
    stack = contextlib.ExitStack()
    start, collect = getattr(common, "_start", None), getattr(common, "_collect", None)

    def started(argv, **kwargs):
        child = start(argv, **kwargs)
        log.append(("start", argv[-1], child.pid))
        return child

    def collected(child, timeout):
        log.append(("collect", child.pid))
        return collect(child, timeout)

    stack.enter_context(mock.patch.object(common, "_start", started, create=True))
    stack.enter_context(mock.patch.object(common, "_collect", collected, create=True))
    return stack


class Many(Hermetic):
    """Six made-up repos, each with a NICE_TO_HAVE.md and an OPEN-QUESTIONS.md; the sixth keeps
    its records out, in a holder's `repos/plum-6`."""

    def setUp(self):
        super().setUp()
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="bk1-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repos = []
        hold = os.path.join(self.tmp, "hold")
        os.makedirs(os.path.join(hold, "repos", "plum-6"))
        git(hold, "init", "-q", "-b", "main")
        for name in NAMES:
            repo = os.path.join(self.tmp, "work", name)
            os.makedirs(repo)
            git(repo, "init", "-q", "-b", "main")
            home = os.path.join(hold, "repos", name) if name == "plum-6" else repo
            write(os.path.join(home, "NICE_TO_HAVE.md"), NICE)
            write(os.path.join(home, "OPEN-QUESTIONS.md"), QUESTIONS)
            write(os.path.join(repo, "README.md"), name + "\n")
            git(repo, "add", "README.md")
            git(repo, "commit", "-q", "-m", "start")
            self.repos.append(repo)
        git(self.repos[-1], "config", KEY, os.path.join(hold, "repos", "plum-6"))

    def run_cli(self, *argv):
        here = os.getcwd()
        os.chdir(self.repos[0])
        try:
            out, err = io.StringIO(), io.StringIO()
            code = decisions.main(list(argv), out=out, err=err)
        finally:
            os.chdir(here)
        return code, out.getvalue(), err.getvalue()


class Prime(Many):

    def test_six_slow_children_answer_within_a_second(self):
        code, plain, err = self.run_cli("backlog", "--json", *self.repos)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(json.loads(plain)["repos"]), 6)
        with mock.patch.object(common, "_CHILD", SLOW):
            start = time.monotonic()
            code, slow, err = self.run_cli("backlog", "--json", *self.repos)
            took = time.monotonic() - start
        self.assertEqual(code, 0, err)
        self.assertLess(took, 1.0)
        self.assertEqual(slow, plain)

    def test_one_hung_child_reads_timeout_and_none_is_left(self):
        pids = os.path.join(self.tmp, "pids")
        hung = ("import os, sys, time\nif sys.argv[2].endswith('plum-3'):\n"
                "    open(%r, 'a').write('%%d\\n' %% os.getpid())\n    time.sleep(30)\n"
                % pids) + common._CHILD
        keys = [os.path.realpath(r) for r in self.repos]
        want = {k: common._resolved(k) for k in keys}
        common.records_reset()
        self.addCleanup(common.records_reset)
        with mock.patch.object(common, "_CHILD", hung), mock.patch.object(common, "GIT_TIMEOUT", 2):
            start = time.monotonic()
            common.records_prime(self.repos)
            took = time.monotonic() - start
            for key in keys:
                got = common._RESOLVED[key]
                if key.endswith("plum-3"):
                    self.assertEqual(got, ({"state": "timeout", "repo": key}, []))
                else:
                    self.assertEqual(got, want[key])
            code, out, err = self.run_cli("backlog", "--json", *self.repos)
        self.assertLess(took, 3.0)
        self.assertEqual(code, 2, out + err)
        self.assertIn("did not say within 2 s where %s" % keys[2], err)
        with open(pids, encoding="utf-8") as handle:
            found = handle.read().split()
        self.assertEqual(len(found), 2, found)
        for pid in found:
            with self.assertRaises(ProcessLookupError):
                os.killpg(int(pid), 0)

    def test_questions_and_expire_start_every_child_first(self):
        three = self.repos[:2] + self.repos[-1:]
        for verb in (["questions"], ["questions", "--json"], ["expire", "--days", "14"],
                     ["expire", "--days", "14", "--json"]):
            with unprimed():
                pin = self.run_cli(*(verb + three))
            log = []
            with spied(log):
                now = self.run_cli(*(verb + three))
            self.assertEqual(now, pin, verb)
            self.assertEqual(pin[0], 0, pin)
            kinds = [e[0] for e in log]
            self.assertEqual(kinds, ["start"] * 3 + ["collect"] * 3, (verb, log))
            self.assertEqual([e[1] for e in log[:3]], [os.path.realpath(r) for r in three])

    def test_a_primed_key_is_not_resolved_again(self):
        common.records_reset()
        self.addCleanup(common.records_reset)
        log = []
        with spied(log):
            common.records_prime(self.repos[:2])
            common.records_prime(self.repos[:3])
            for repo in self.repos[:3]:
                common.records_answer(repo)
        self.assertEqual([e[0] for e in log], ["start", "start", "collect", "collect",
                                               "start", "collect"])

    def test_no_git_on_path_primes_nothing(self):
        common.records_reset()
        self.addCleanup(common.records_reset)
        with mock.patch.object(common.shutil, "which", lambda name: None):
            common.records_prime(self.repos)
        self.assertEqual(common._RESOLVED, {})



def width():
    return getattr(common, "PRIME_WIDTH", 16)


def limited(limit):
    """A child's start that lowers its soft descriptor limit to `limit`."""
    def lower():
        hard = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        resource.setrlimit(resource.RLIMIT_NOFILE, (limit, hard))
    return lower


class Window(Hermetic):
    """review 1 B1: the prime holds at most PRIME_WIDTH children, a failed start caches nothing,
    and every start sits inside the cleanup. Plain made-up repos, each with a NICE_TO_HAVE.md."""

    def setUp(self):
        super().setUp()
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="bk1w-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        common.records_reset()
        self.addCleanup(common.records_reset)

    def made(self, count, git_init=True):
        repos = []
        for n in range(count):
            repo = os.path.join(self.tmp, "pear-%03d" % n)
            os.makedirs(repo)
            if git_init:
                git(repo, "init", "-q", "-b", "main")
                write(os.path.join(repo, "NICE_TO_HAVE.md"), NICE)
            repos.append(repo)
        return repos

    def child(self, argv, limit=None, cwd=None):
        env = dict(os.environ, PYTHONPATH=common._LIB)
        return subprocess.run([sys.executable] + argv, cwd=cwd or self.tmp, env=env,
                              capture_output=True, text=True, timeout=120,
                              preexec_fn=limited(limit) if limit else None)

    def test_backlog_reads_twelve_repos_at_a_limit_of_24(self):
        repos = self.made(12)
        argv = ["-m", "decisions", "backlog", "--json"] + repos
        plain = self.child(argv, cwd=repos[0])
        tight = self.child(argv, limit=24, cwd=repos[0])
        self.assertEqual(plain.returncode, 0, plain.stderr)
        self.assertEqual(len(json.loads(plain.stdout)["repos"]), 12)
        self.assertEqual((tight.returncode, tight.stdout, tight.stderr),
                         (plain.returncode, plain.stdout, plain.stderr))

    def test_sixty_repos_answer_own_at_a_limit_of_64(self):
        repos = self.made(60, git_init=False)
        for repo in repos:
            git(repo, "init", "-q", "-b", "main")
        script = ("import json, sys\nfrom decisions import common\n"
                  "common.records_prime(sys.argv[1:])\n"
                  "print(json.dumps([(common.records_answer(r) or {}).get('state')"
                  " for r in sys.argv[1:]]))\n")
        got = self.child(["-c", script] + repos, limit=64)
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertEqual(json.loads(got.stdout), ["own"] * 60)

    def test_never_more_than_the_width_uncollected(self):
        folders = self.made(40, git_init=False)
        log = []
        with spied(log):
            common.records_prime(folders)
        live, most = set(), 0
        for entry in log:
            if entry[0] == "start":
                live.add(entry[2])
            else:
                live.discard(entry[1])
            most = max(most, len(live))
        self.assertEqual(most, width(), log)
        self.assertEqual(sorted(e[1] for e in log if e[0] == "start"), folders)
        self.assertEqual(len([e for e in log if e[0] == "collect"]), 40)
        self.assertEqual(sorted(common._RESOLVED), folders)

    def test_a_failed_start_caches_nothing(self):
        repos = self.made(6)
        keys = [os.path.realpath(r) for r in repos]
        want = {k: common._resolved(k) for k in keys}
        common.records_reset()
        real, collect, log = common._start, common._collect, []

        def start(argv, **kwargs):
            if argv[-1] == keys[3]:
                log.append("fail")
                raise OSError(errno.EMFILE, "Too many open files")
            log.append("start")
            return real(argv, **kwargs)

        def collected(child, timeout):
            log.append("collect")
            return collect(child, timeout)
        with mock.patch.object(common, "_start", start), \
                mock.patch.object(common, "_collect", collected):
            common.records_prime(repos)
        self.assertEqual(log, ["start"] * 3 + ["fail"] + ["collect"] * 3 + ["start"] * 2
                         + ["collect"] * 2)
        self.assertNotIn(keys[3], common._RESOLVED)
        self.assertEqual({k: common._RESOLVED[k] for k in keys if k != keys[3]},
                         {k: want[k] for k in keys if k != keys[3]})
        self.assertEqual(common.records_answer(repos[3]), want[keys[3]][0])
        self.assertEqual(common._RESOLVED[keys[3]], want[keys[3]])

    def test_an_interrupt_in_the_starts_leaves_no_child(self):
        repos = self.made(6, git_init=False)
        real, children = common._start, []

        def start(argv, **kwargs):
            if len(children) == 2:
                raise KeyboardInterrupt
            child = real(argv, **kwargs)
            children.append(child)
            self.addCleanup(lambda: child.poll() is None and os.killpg(child.pid, 9))
            return child
        with mock.patch.object(common, "_CHILD", "import time\ntime.sleep(30)\n"), \
                mock.patch.object(common, "_start", start):
            with self.assertRaises(KeyboardInterrupt):
                common.records_prime(repos)
        self.assertEqual(len(children), 2)
        for child in children:
            self.assertIsNotNone(child.returncode)
            with self.assertRaises(ProcessLookupError):
                os.killpg(child.pid, 0)

    def test_each_child_has_its_own_wall(self):
        repos = self.made(2, git_init=False)
        keys = [os.path.realpath(r) for r in repos]
        want = {k: common._resolved(k) for k in keys}
        common.records_reset()
        slow = "import time\ntime.sleep(1.2)\n" + common._CHILD
        with mock.patch.object(common, "_CHILD", slow), \
                mock.patch.object(common, "GIT_TIMEOUT", 2), \
                mock.patch.object(common, "PRIME_WIDTH", 1, create=True):
            common.records_prime(repos)
        self.assertEqual({k: common._RESOLVED[k] for k in keys}, want)


def counted(log):
    """`common.bounded_err` logging each run's (argv, cwd) and whether a memo is open."""
    real = common.bounded_err

    def spy(argv, timeout, **kwargs):
        log.append((tuple(argv), kwargs.get("cwd"), getattr(common, "_GIT_MEMO", None) is not None))
        return real(argv, timeout, **kwargs)
    return mock.patch.object(common, "bounded_err", spy)


class Memo(Rows):
    """Rows in the home `orchard-hq` and in its member `pear`, read through one `rows --json`."""

    def test_one_read_asks_each_pair_once(self):
        tip = self.on_branch("p3-basket", "basket-1.txt")
        self.row("p3-basket")
        self.build("p3-basket", 1, tip)
        base = self.base("p3-basket")
        self.review("p3-basket", 1, "%s..%s" % (base[:7], tip[:7]), ruling="closed: all mended")
        self.row("p4-shed", repo="hq")
        self.row("p5-ladder", depends="p3-basket", branch="p1-live")
        self.on_branch("h1-gate", "gate.txt", repo=self.hq)
        self.row("h1-gate", repo="hq", branch="h1-gate")
        with mock.patch.object(rows_module, "git_memo", contextlib.nullcontext, create=True):
            pin = self.rows("--json")
        log = []
        with counted(log):
            now = self.rows("--json")
        self.assertEqual(now, pin)
        self.assertEqual(now[0], 0, now)
        got = json.loads(now[1])
        self.assertEqual(sorted(r["row"] for r in got["rows"]),
                         ["h1-gate", "p3-basket", "p4-shed", "p5-ladder"])
        self.assertEqual(got["skipped"], [])
        pairs = [(argv, cwd) for argv, cwd, _ in log if argv[0] == "git"]
        twice = sorted(set(p for p in pairs if pairs.count(p) > 1))
        self.assertEqual(twice, [])
        self.assertGreater(len(pairs), 10)
        self.assertIsNone(getattr(common, "_GIT_MEMO", None))


class Fresh(Depot):

    def test_close_after_a_read_runs_its_git_fresh(self):
        cell = self.pushed("p1-crate")
        read_log, close_log = [], []
        with counted(read_log):
            self.assertIn("p1-crate", self.view())
        self.assertIsNone(getattr(common, "_GIT_MEMO", None))
        with counted(close_log):
            code, out, err = self.close("close", "p1-crate", "--dry-run")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("done %s" % cell, out)
        asked = set((argv, cwd) for argv, cwd, _ in read_log)
        again = [(argv, cwd) for argv, cwd, _ in close_log if (argv, cwd) in asked]
        self.assertTrue(again, close_log)
        self.assertEqual([m for _, _, m in close_log], [False] * len(close_log))
