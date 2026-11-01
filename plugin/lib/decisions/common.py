"""What every verb shares: the refusal, the bounded child, the git top, the
all-or-nothing write and the lock."""

import contextlib
import fcntl
import os
import re
import signal
import subprocess
import tempfile
import time

__all__ = ["Refusal", "bounded", "bounded_err", "git_top", "read_text", "write_text", "commit_texts", "held",
           "GIT_TIMEOUT", "VERSION"]

# This package's version, one with the three manifests; `agentik-decisions --version`
# prints it and `doctor` compares the tool on PATH with it.
VERSION = "0.9.0"

# Every child this tool starts is bounded (ADV6-6): a hang is a Refusal or a
# warn, never a wait. The tests lower it.
GIT_TIMEOUT = 10


class Refusal(Exception):
    """A usage error, an unreadable file or a verb's refusal: exit 2."""


def bounded(argv, timeout, **kwargs):
    """(returncode, stdout) of `argv`, killed as a process group past `timeout`.

    Its own session, so a grandchild holding the pipe dies with it; past the
    bound `subprocess.TimeoutExpired` propagates, and OSError does too."""
    return bounded_err(argv, timeout, **kwargs)[:2]


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


def commit_texts(texts):
    """Write every `(path, text)` or none (ADV6-9).

    A path that is a link is written through it: the file it names is replaced
    and the link stays (F5). A file whose first line ends in CRLF gets every
    line end in CRLF; a new file, or one in LF, gets LF (F4). Every text goes
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
        if original is not None and line_end(original) == "\r\n":
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
