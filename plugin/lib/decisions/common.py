"""What every verb shares: the refusal, the bounded child, the git top, the
all-or-nothing write and the lock."""

import contextlib
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

__all__ = ["Refusal", "bounded", "bounded_err", "git_top", "read_text", "write_text", "commit_texts", "held",
           "keeps_crlf", "disk_text", "on_disk", "records_of", "records_answer", "records_repo", "records_reset",
           "records_prime", "git_memo", "read_only",
           "RECORDS_KEY", "GIT_TIMEOUT", "VERSION"]

# This package's version, one with the three manifests; `agentik-decisions --version`
# prints it and `doctor` compares the tool on PATH with it.
VERSION = "0.23.16"

# Every child this tool starts is bounded (ADV6-6): a hang is a Refusal or a
# warn, never a wait. The tests lower it.
GIT_TIMEOUT = 10
# Review 1 B1: the most resolver children `records_prime` keeps uncollected at once, each
# holding two pipes in this process, so a read stays far below a descriptor limit of 256.
PRIME_WIDTH = 16


class Refusal(Exception):
    """A usage error, an unreadable file or a verb's refusal: exit 2."""


def bounded(argv, timeout, **kwargs):
    """(returncode, stdout) of `argv`, killed as a process group past `timeout`.

    Its own session, so a grandchild holding the pipe dies with it; past the
    bound `subprocess.TimeoutExpired` propagates, and OSError does too. bk1 R3: inside
    `git_memo`, a read-only git call (`read_only`) with no option but `cwd` runs once a
    (argv, cwd) pair, its failure kept as itself."""
    memo = _GIT_MEMO
    if memo is None or set(kwargs) - {"cwd"} or not read_only(argv):
        return bounded_err(argv, timeout, **kwargs)[:2]
    key = (tuple(argv), kwargs.get("cwd"))
    if key not in memo:
        try:
            memo[key] = (bounded_err(argv, timeout, **kwargs)[:2], None)
        except (subprocess.TimeoutExpired, OSError) as exc:
            memo[key] = (None, exc)
    got, exc = memo[key]
    if exc is not None:
        raise exc
    return got


# bk1 R3: the git subcommands that cannot change a repo, and git's options before one that the
# memo reads past; `status` only under --no-optional-locks (else it may refresh the index),
# `worktree` only as `worktree list`.
_GIT_MEMO = None
READ_ONLY = ("diff", "diff-tree", "log", "merge-base", "rev-list", "rev-parse", "show")


def read_only(argv):
    """True where `argv` is a git call that reads and never writes."""
    if not argv or argv[0] != "git":
        return False
    at, unlocked = 1, False
    while at < len(argv) and argv[at].startswith("-"):
        if argv[at] in ("-C", "-c"):
            at += 2
        elif argv[at] == "--no-optional-locks":
            unlocked, at = True, at + 1
        else:
            return False
    if at >= len(argv):
        return False
    verb, rest = argv[at], list(argv[at + 1:])
    if verb in READ_ONLY:
        return True
    if verb == "status":
        return unlocked
    return verb == "worktree" and rest[:1] == ["list"]


@contextlib.contextmanager
def git_memo():
    """bk1 R3: while open, `bounded` asks each read-only git (argv, cwd) pair once; empty
    before and after, so no call outside it reads a memoized answer."""
    global _GIT_MEMO
    outer, _GIT_MEMO = _GIT_MEMO, {}
    try:
        yield
    finally:
        _GIT_MEMO = outer


def bounded_err(argv, timeout, **kwargs):
    """(returncode, stdout, stderr) of `argv`, bounded as `bounded` is; a byte that is
    not UTF-8 reads as U+FFFD, so a child's output never raises."""
    child = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, encoding="utf-8", errors="replace",
                             start_new_session=True, **kwargs)
    try:
        out, err = child.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except OSError:
            pass
        child.communicate()
        raise
    return child.returncode, out, err


def git_top(cwd):
    """The git top level above `cwd`, or None outside a work tree; a hang is a Refusal."""
    try:
        code, out = bounded(["git", "rev-parse", "--show-toplevel"], GIT_TIMEOUT, cwd=cwd)
    except subprocess.TimeoutExpired:
        raise Refusal("git rev-parse timed out after %d s in %s" % (GIT_TIMEOUT, cwd))
    except OSError:
        return None
    top = out.strip()
    return top if code == 0 and top else None


# rr4 (hq design/28 §3 items 12, 18): where a repo's records are, from commons' one resolver,
# `agentik_records`, beside this package in lib/. Each folder is resolved once a call: `main`
# empties the cache, so a test's second call reads the key again.
RECORDS_KEY = "agentik.records"
_RESOLVED = {}
WHY = {"unread": "git cannot read it as a path", "many": "it is set more than once",
       "relative": "it is not an absolute path", "missing": "it names no folder",
       "inside": "it lies inside the clone or one of its worktrees",
       "name": "its last name is not the clone's folder name",
       "holder": "the repository holding it declares its own records out"}


def records_reset():
    """Forget every answer, so the next call resolves afresh."""
    _RESOLVED.clear()


# review 1 C1: the resolver runs in a child of its own session, so GIT_TIMEOUT bounds the whole
# resolve and its git children die with it; the synced module stays as synced.
_CHILD = ("import json, sys\n"
          "sys.path.insert(0, sys.argv[1])\n"
          "import agentik_records as r\n"
          "try:\n"
          "    a = r.resolve(sys.argv[2])\n"
          "except r.NoRepo:\n"
          "    a = None\n"
          "v = r.values(sys.argv[2]) if a and a['state'] == 'broken' else []\n"
          "print(json.dumps({'answer': a, 'values': v}))\n")
_LIB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _git_above(folder):
    """True where a `.git`, a folder or a file, lies in `folder` or above it."""
    here = folder
    while True:
        if os.path.lexists(os.path.join(here, ".git")):
            return True
        up = os.path.dirname(here)
        if up == here:
            return False
        here = up


def _resolved(key):
    """(the resolver's answer for `key` or None for NoRepo, the key's values) from a bounded
    child; the answer `{"state": "timeout"}` past GIT_TIMEOUT, `{"state": "nogit"}` where git
    cannot answer for a folder a `.git` lies above (review 1 C2), None where none does or no
    git is on PATH: with none, `answer` and `ask` work as d41 and d42 made them, in the clone."""
    if shutil.which("git") is None:
        return None, []
    try:
        code, out = bounded(_child_argv(key), GIT_TIMEOUT, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"state": "timeout", "repo": key}, []
    except OSError:
        code, out = None, None
    return _answered(key, code, out)


def _child_argv(key):
    return [sys.executable or "/usr/bin/python3", "-I", "-S", "-c", _CHILD, _LIB, key]


def _answered(key, code, out):
    """What `_resolved` answers for `key` from its child's exit and output (None: it never ran)."""
    try:
        got = json.loads(out) if code == 0 else None
    except ValueError:
        got = None
    answer = got.get("answer") if isinstance(got, dict) else None
    if isinstance(answer, dict) and answer.get("state") in ("own", "out", "unset", "broken"):
        return answer, list(got.get("values") or [])
    if _git_above(key):
        return {"state": "nogit", "repo": key, "records": None, "holder": None,
                "prefix": None}, []
    return None, []


def records_answer(folder):
    """The resolver's `agentik.records/1` object for `folder`, or None where `folder` is in
    no git checkout (read as `own`, today's behaviour); one resolve a folder a call. Besides
    the resolver's four states, `timeout` and `nogit` (see `_resolved`)."""
    key = os.path.realpath(folder)
    if key not in _RESOLVED:
        _RESOLVED[key] = _resolved(key)
    return _RESOLVED[key][0]


def _start(argv, **kwargs):
    """A child started as `bounded_err` starts one, in its own session."""
    return subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", errors="replace",
                            start_new_session=True, **kwargs)


def _collect(child, timeout):
    """(returncode, stdout) of a started child within `timeout`; past it the child is killed
    with its group, reaped, and `subprocess.TimeoutExpired` propagates."""
    try:
        out, _ = child.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except OSError:
            pass
        child.communicate()
        raise
    return child.returncode, out


def records_prime(folders):
    """bk1 R1: resolve every folder not yet cached at once, caching exactly what `_resolved`
    answers for each; a key never primed resolves as before. Review 1 B1: at most
    PRIME_WIDTH children are uncollected at a time, each under GIT_TIMEOUT from its own
    start (G1); a start that fails caches nothing, so the unprimed path resolves that key,
    and every running child is collected before the next start (G2); every start is inside
    the `finally` that kills and reaps what is left (G3)."""
    if shutil.which("git") is None:
        return
    keys = []
    for folder in folders:
        key = os.path.realpath(folder)
        if os.path.isdir(key) and key not in _RESOLVED and key not in keys:
            keys.append(key)
    started, drain = [], False
    try:
        while keys or started:
            if keys and not drain and len(started) < PRIME_WIDTH:
                key = keys.pop(0)
                try:
                    child = _start(_child_argv(key), stdin=subprocess.DEVNULL)
                except OSError:
                    drain = True  # left uncached: records_answer resolves it as unprimed
                else:
                    started.append((key, child, time.monotonic()))
                continue
            if not started:
                drain = False
                continue
            key, child, begun = started[0]
            left = max(GIT_TIMEOUT - (time.monotonic() - begun), 0)
            if child.poll() is not None:
                left = max(left, 1.0)  # done before the wall: read what it wrote
            try:
                code, out = _collect(child, left)
            except subprocess.TimeoutExpired:
                _RESOLVED[key] = ({"state": "timeout", "repo": key}, [])
            else:
                _RESOLVED[key] = _answered(key, code, out)
            started.pop(0)
    finally:
        for _, child, _ in started:  # an interrupt leaves no child behind
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except OSError:
                pass
            child.communicate()


def records_repo(folder):
    """review 1 C4: (the key a REPO argument is read once by, the folder to read it as). A
    repo whose records are out is keyed by its records folder and read at its git top, so a
    subfolder or a link of it is that repo; any other folder is its own realpath, as today."""
    real = os.path.realpath(folder)
    answer = records_answer(real) if os.path.isdir(real) else None
    if answer is None or answer["state"] != "out":
        return real, real
    top = git_top(real)
    return os.path.realpath(answer["records"]), os.path.realpath(top) if top else real


def _shown(value):
    return "".join(c if c.isprintable() else "\\x%02x" % ord(c) for c in value)


def records_of(folder, verb, write=False):
    """D2: the folder holding the records of `folder`'s repo. `own` (or no checkout) gives
    `folder` back unchanged; `out`, the key's folder; `unset`, None for a read, a Refusal for a
    write; `broken`, a Refusal naming the key, its values and the reason."""
    answer = records_answer(folder)
    if answer is None or answer["state"] == "own":
        return folder
    if answer["state"] == "out":
        return answer["records"]
    if answer["state"] == "timeout":
        raise Refusal("%s: git did not say within %d s where %s keeps its records (the key %s); "
                      "no record read or written" % (verb, GIT_TIMEOUT, answer["repo"], RECORDS_KEY))
    if answer["state"] == "nogit":
        if not write:
            return None
        raise Refusal("%s: git cannot say where %s keeps its records (the key %s); nothing "
                      "written" % (verb, answer["repo"], RECORDS_KEY))
    if answer["state"] == "unset":
        if not write:
            return None
        raise Refusal("%s: this repo keeps its records out of its tree and the key %s is not "
                      "set in its clone; set it with `git config %s <folder>`; nothing written"
                      % (verb, RECORDS_KEY, RECORDS_KEY))
    values = _RESOLVED[os.path.realpath(folder)][1]
    shown = ", ".join("'%s'" % _shown(v) for v in values) or "none"
    raise Refusal("%s: the key %s (%s) does not resolve: %s (%s); no record read or written"
                  % (verb, RECORDS_KEY, shown, WHY.get(answer["why"], answer["why"]),
                     answer["why"]))


def read_text(path):
    """The text of `path`, or a Refusal naming why it cannot be read."""
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise Refusal("%s: unreadable: %s" % (path, exc))


def file_mode(path):
    """The mode `path` has, or the mode a new file gets under the umask."""
    try:
        return os.stat(path).st_mode & 0o7777
    except OSError:
        umask = os.umask(0)
        os.umask(umask)
        return 0o666 & ~umask


def line_end(raw):
    """The line end of the bytes `raw`: its first line's, CRLF or LF; LF when it has none."""
    index = raw.find(b"\n")
    return "\r\n" if index > 0 and raw[index - 1:index] == b"\r" else "\n"


def keeps_crlf(path):
    """True when a write to `path` keeps CRLF: the file it names exists and its first line
    ends in CRLF, the rule `commit_texts` applies (d32 fold, F1)."""
    try:
        with open(os.path.realpath(path), "rb") as handle:
            return line_end(handle.read()) == "\r\n"
    except OSError:
        return False


def disk_text(path):
    """The text of `path` with its line ends as they are on disk, "" when it is absent."""
    if not os.path.exists(path):
        return ""
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise Refusal("%s: unreadable: %s" % (path, exc))


def on_disk(text, crlf):
    """The bytes `text` takes once written: UTF-8, every line end CRLF when `crlf`."""
    return len((re.sub(r"\r?\n", "\r\n", text) if crlf else text).encode())


def commit_texts(texts, as_read=False):
    """Write every `(path, text)` or none (ADV6-9).

    A path that is a link is written through it: the file it names is replaced
    and the link stays (F5). A file whose first line ends in CRLF gets every
    line end in CRLF; a new file, or one in LF, gets LF (F4). With `as_read`,
    every text is written with its line ends as it holds them, none changed
    (`reply`, in5a review 1 F2: a text read with `disk_text` keeps a file of
    mixed line ends as it was). Every text goes
    to a temp file beside the file it replaces first; then the temps replace
    their files in order. On any failure the temps go, every file already
    replaced gets its original bytes back (a file that did not exist is
    removed), and the write is refused."""
    targets, originals = [], []
    for path, text in texts:
        real = os.path.realpath(path)
        try:
            with open(real, "rb") as handle:
                original = handle.read()
        except FileNotFoundError:
            original = None
        except OSError as exc:
            raise Refusal("%s: unreadable: %s" % (path, exc))
        if not as_read and original is not None and line_end(original) == "\r\n":
            text = re.sub(r"\r?\n", "\r\n", text)
        originals.append(original)
        targets.append((path, real, text))
    temps, replaced, current = [], [], None
    try:
        for path, real, text in targets:
            current = path
            fd, temp = tempfile.mkstemp(prefix=".decisions-", dir=os.path.dirname(real))
            temps.append(temp)
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp, file_mode(real))
        for (path, real, _text), temp in zip(targets, temps):
            current = path
            os.replace(temp, real)
            replaced.append(real)
    except OSError as exc:
        for temp in temps:
            if os.path.exists(temp):
                try:
                    os.unlink(temp)
                except OSError:
                    pass
        for (_path, real, _text), original in zip(targets, originals):
            if real not in replaced:
                continue
            try:
                if original is None:
                    os.unlink(real)
                else:
                    with open(real, "wb") as handle:
                        handle.write(original)
            except OSError:
                pass
        raise Refusal("%s: unwritable: %s" % (current, exc))


def write_text(path, text):
    """Replace `path` with `text` in one rename, keeping its mode, its line end and a link."""
    commit_texts([(path, text)])


def running(pid):
    """False only when no process `pid` exists; a pid we may not signal is alive."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def flocked(fd):
    """True when this descriptor now holds the flock (non-blocking)."""
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return False
    return True


def own_inode(fd, path):
    """True while `path` still names the file open on `fd` (not unlinked, not replaced)."""
    try:
        return os.fstat(fd).st_ino == os.stat(path).st_ino
    except OSError:
        return False


def holder(path):
    """The pid written in the lock at `path`, or None."""
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read().strip()
    except (OSError, UnicodeDecodeError):
        return None
    return int(text) if text.isdigit() and int(text) > 0 else None


@contextlib.contextmanager
def held(path, wait, err):
    """The lock file `path` under an `fcntl.flock`, removed on exit (ADV6-8, ADV11-4).

    The flock is the truth: the kernel drops a dead holder's, so two takeovers
    cannot both hold. Once locked, the path must still name the locked inode
    (the previous holder may have removed it), else the open is retried. A live
    holder is waited on up to `wait` seconds, then refused naming the file, its
    pid and its age; a dead holder's pid gets one line on `err`. On exit the
    path is removed only while it is still this holder's inode."""
    name = os.path.basename(path)
    deadline = time.monotonic() + wait
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
        except OSError as exc:
            raise Refusal("%s: unwritable: %s" % (path, exc))
        if flocked(fd):
            if own_inode(fd, path):
                break
            os.close(fd)
            continue
        os.close(fd)
        if time.monotonic() >= deadline:
            try:
                age = "%.1fs" % (time.time() - os.stat(path).st_mtime)
            except OSError:
                age = "unknown"
            raise Refusal("%s is held by pid %s, age %s; waited %.1fs"
                          % (name, holder(path) or "unknown", age, wait))
        time.sleep(0.05)
    try:
        pid = holder(path)
        if pid is not None and not running(pid):
            err.write("decisions: took over %s from dead pid %d\n" % (name, pid))
        os.ftruncate(fd, 0)
        os.write(fd, ("%d\n" % os.getpid()).encode("ascii"))
        yield
    finally:
        try:
            if own_inode(fd, path):
                os.unlink(path)
        except OSError:
            pass
        os.close(fd)
