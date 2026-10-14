"""scripts/bounded (R6 C1, ADV10-1 to -3): exits, the lifeline, the flock, the wall, the stop line.

A unittest port of the session's tests/test_bounded.py at db648f3 (which imports
pytest, not carried here): each module-level test a same-named method of
BoundedTest, parametrize as subTest, tmp_path as tempfile.TemporaryDirectory.
"""
import fcntl
import os
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bounded"


def clean_env(**extra):
    """The caller's environment at depth 0: the gate's own bounded sets BOUNDED_DEPTH."""
    e = dict(os.environ, BOUNDED_GRACE="0.5")
    e.update(extra)
    e.pop("BOUNDED_DEPTH", None)
    return e


def run(*args, env=None, timeout=20):
    e = clean_env()
    e.update(env or {})
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True,
                          text=True, env=e, timeout=timeout)


def start(*args, cwd=None):
    """bounded in the background, its own session, stderr piped."""
    e = clean_env()
    return subprocess.Popen([sys.executable, str(SCRIPT), *args], env=e, cwd=cwd,
                            stderr=subprocess.PIPE, text=True)


def dead_pid():
    p = subprocess.Popen(["true"])
    p.wait()
    return p.pid


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def wait_for(pred, seconds):
    deadline = time.monotonic() + seconds
    while not pred() and time.monotonic() < deadline:
        time.sleep(0.05)
    return pred()


def lock_free(path):
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False
    finally:
        os.close(fd)


class BoundedTest(unittest.TestCase):
    def test_usage_is_1(self):
        for args in [[], ["--"], ["true"], ["--wall", "x", "--", "true"],
                     ["--bogus", "--", "true"], ["--lock", "--", "true"]]:
            with self.subTest(args=args):
                p = run(*args)
                assert p.returncode == 1, p.stderr
                assert "usage" in p.stderr

    def test_caller_group_sigkill_reaches_the_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # ADV10-1: the relay SIGKILLs the verify line's group; the suite under it must die too.
            pidfile, lock = tmp_path / "suite", tmp_path / ".check.lock"
            inner = "echo $$ > %s; exec sleep 30" % pidfile
            line = "%s %s --lock %s --wall 600 -- sh -c %s; true" % (
                shlex.quote(sys.executable), shlex.quote(str(SCRIPT)), shlex.quote(str(lock)),
                shlex.quote(inner))
            caller = subprocess.Popen(["sh", "-c", line], start_new_session=True,
                                      env=clean_env())
            assert wait_for(lambda: pidfile.exists() and pidfile.read_text().strip(), 10)
            suite = int(pidfile.read_text())
            assert alive(suite)
            os.killpg(caller.pid, signal.SIGKILL)
            caller.wait(timeout=5)
            assert wait_for(lambda: not alive(suite), 2), "the suite outlived its caller"
            assert wait_for(lambda: lock_free(lock), 2), "the lock outlived the suite"

    def test_wall_counts_the_load_wait(self):
        # ADV10-1: the load wait spends the wall; it never adds to it.
        t0 = time.monotonic()
        p = run("--wall", "1", "--load", "1", "--", "true",
                env={"BOUNDED_LOADAVG": "999", "BOUNDED_LOAD_POLL": "0.05",
                     "BOUNDED_LOAD_MAX": "600"})
        assert time.monotonic() - t0 < 3
        assert p.returncode == 2, p.stderr
        assert p.stderr.splitlines()[-1] == "bounded: stop: load"

    def test_lock_exclusive_under_takeover(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # ADV10-2: contenders over one lock, a dead holder's leftover included: one holds.
            lock, held = tmp_path / ".check.lock", tmp_path / "held"
            lock.write_text("%d %d\n" % (dead_pid(), int(time.time()) - 5000))
            cmd = "echo $$ >> %s; sleep 2" % held
            procs = [start("--lock", str(lock), "--", "sh", "-c", cmd) for _ in range(4)]
            codes = sorted(p.wait(timeout=20) for p in procs)
            assert codes == [0, 2, 2, 2], codes
            assert len(held.read_text().split()) == 1
            assert lock_free(lock)

    def test_live_holder_refuses_at_any_age(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            lock = tmp_path / ".check.lock"
            holder = start("--lock", str(lock), "--", "sleep", "30")
            try:
                assert wait_for(lambda: lock.exists() and lock.read_text().strip() and not lock_free(lock), 10)
                # the owner line only feeds the message: an ancient start changes nothing
                lock.write_text("%d %d\n" % (holder.pid, int(time.time()) - 100000))
                p = run("--lock", str(lock), "--", "true")
                assert p.returncode == 2 and "held" in p.stderr
            finally:
                holder.terminate()
                holder.wait(timeout=5)
            assert wait_for(lambda: lock_free(lock), 2)
            # a mkdir-era lock directory: a live owner refuses, a dead one is removed
            legacy = tmp_path / "legacy.lock"
            legacy.mkdir()
            (legacy / "owner").write_text("%d %d\n" % (os.getpid(), int(time.time()) - 100000))
            p = run("--lock", str(legacy), "--", "true")
            assert p.returncode == 2 and legacy.is_dir()
            (legacy / "owner").write_text("%d %d\n" % (dead_pid(), int(time.time())))
            p = run("--lock", str(legacy), "--", "true")
            assert p.returncode == 0, p.stderr
            assert not legacy.is_dir()

    def test_stop_line_names_the_reason(self):
        for reason in ["lock", "load", "wall"]:
            with self.subTest(reason=reason):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = Path(tmp)
                    # ADV10-3: a refused or walled gate says so on its last line, so it reads unrun, not red.
                    lock = tmp_path / ".check.lock"
                    holder = None
                    if reason == "lock":
                        holder = start("--lock", str(lock), "--", "sleep", "30")
                        assert wait_for(lambda: lock.exists() and not lock_free(lock), 10)
                        p, code = run("--lock", str(lock), "--", "true"), 2
                    elif reason == "load":
                        t0 = time.monotonic()
                        p = run("--lock", str(lock), "--load", "1", "--", "true",
                                env={"BOUNDED_LOADAVG": str(10.0 * (os.cpu_count() or 1)),
                                     "BOUNDED_LOAD_POLL": "0.1", "BOUNDED_LOAD_MAX": "0.3"})
                        code = 2
                        assert time.monotonic() - t0 < 5
                        assert lock_free(lock)
                    else:
                        # the grandchild ignores TERM, so only the group SIGKILL after the grace ends it
                        pidfile = tmp_path / "grandchild"
                        script = "sh -c 'trap \"\" TERM; sleep 30' & echo $! > %s; wait" % pidfile
                        t0 = time.monotonic()
                        p, code = run("--wall", "1", "--", "sh", "-c", script), 124
                        assert time.monotonic() - t0 < 6
                        assert wait_for(lambda: not alive(int(pidfile.read_text())), 3)
                    if holder:
                        holder.terminate()
                        holder.wait(timeout=5)
                    assert p.returncode == code, p.stderr
                    assert p.stderr.splitlines()[-1] == "bounded: stop: %s" % reason

    def test_makefile_gate_is_bounded(self):
        text = (ROOT / "Makefile").read_text()
        # 840 s plus the grace fits inside the relay's 900 s timeout (ADV10-1)
        assert ("scripts/bounded --lock .check.lock --wall 840 --load 4 -- $(MAKE) check-unlocked"
                in text)
        # the README render spawns `claude -p`: walled like the gate (ADV10-6); this repo's
        # line, not the session's 600 s and --load 4 (d15: its 900 s waits for §5's next fold)
        assert "scripts/bounded --wall 900 -- $(PY) scripts/readme-render" in text
        # agentik-r1 5.2: the plugin only; the repo keeps no marketplace of its own
        assert text.count("scripts/bounded --wall 60 -- claude plugin validate") == 1
        assert "scripts/bounded --wall 60 -- claude plugin validate plugin/\n" in text
        assert ".check.lock" in (ROOT / ".gitignore").read_text().split()

    def test_sigterm_without_wall_exits_143(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # the exits: the command's own passes through (folded here so the README's count holds)
            assert run("--", "sh", "-c", "exit 7").returncode == 7
            assert run("--wall", "10", "--", "true").returncode == 0
            # a load under the ceiling runs the command and keeps its exit
            assert run("--load", "4", "--", "sh", "-c", "exit 3",
                       env={"BOUNDED_LOADAVG": "0"}).returncode == 3
            # d12: the handler never waits under the main thread's waitpid lock; 128+15, no traceback
            pidfile = tmp_path / "pid"
            p = start("--", "sh", "-c", 'echo $$ > "$0"; exec sleep 30', str(pidfile))
            assert wait_for(lambda: pidfile.exists() and pidfile.read_text().strip(), 5)
            child = int(pidfile.read_text())
            p.send_signal(signal.SIGTERM)
            _, err = p.communicate(timeout=10)
            assert p.returncode == 143, err
            assert "Traceback" not in err
            assert wait_for(lambda: not alive(child), 2)

    def test_bounded_refuses_nonfinite(self):
        for value in ["nan", "inf", "-inf"]:
            with self.subTest(value=value):
                # ADV11-10: a wall or load that is not finite is no wall and no breaker
                for flag in ("--wall", "--load"):
                    p = run(flag, value, "--", "true")
                    assert p.returncode == 1, p.stderr
                    assert "usage" in p.stderr

    def test_stopped_guardian_does_not_leak_the_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # ADV11-1: a stopped guardian; the fallback kills the reported group, never the guardian alone
            pidfile, lock = tmp_path / "suite", tmp_path / ".check.lock"
            p = subprocess.Popen([sys.executable, str(SCRIPT), "--lock", str(lock), "--wall", "3", "--",
                                  "sh", "-c", 'echo $$ > "$0"; exec sleep 77.7', str(pidfile)],
                                 env=clean_env(BOUNDED_GRACE="1"), stderr=subprocess.PIPE, text=True)
            assert wait_for(lambda: pidfile.exists() and pidfile.read_text().strip(), 5)
            suite = int(pidfile.read_text())
            time.sleep(max(0.0, 1.0 - 0.1))
            guardian = int(lock.read_text().split()[0])
            os.kill(guardian, signal.SIGSTOP)
            try:
                _, err = p.communicate(timeout=15)
                suite_alive = alive(suite)
            finally:
                for sig in (signal.SIGKILL, signal.SIGCONT):
                    try:
                        os.kill(guardian, sig)
                    except ProcessLookupError:
                        pass
                try:
                    os.kill(suite, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            assert p.returncode == 124, err
            assert not suite_alive, "the suite outlived bounded"
            assert lock_free(lock)

    def test_nested_stop_line_is_not_the_gates(self):
        # ADV11-2: an inner wall is a plain red; only the outermost stop reads unrun
        inner = "%s %s --wall 1 -- sleep 5" % (shlex.quote(sys.executable), shlex.quote(str(SCRIPT)))
        p = run("--", "sh", "-c", inner)
        assert p.returncode == 124, p.stderr
        assert "bounded: nested stop: wall" in p.stderr.splitlines()
        assert not [l for l in p.stderr.splitlines() if l.startswith("bounded: stop:")]

    def test_no_survivor_check_greps_the_machine(self):
        # the review of the sibling plugin, ADV11-4: survivors by pidfile, never by a name over every process
        hits = [p.name for p in (ROOT / "tests").rglob("*.py")
                if "pg" "rep" in p.read_text()]
        assert not hits


if __name__ == "__main__":
    unittest.main()
