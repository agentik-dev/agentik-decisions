"""respeak, found and run for `ask` (design d18 section 3).

decisions calls respeak, and respeak knows nothing of decisions; the plugin
declares no dependency. The root is `RESPEAK_ROOT`, else the suite's answer,
`$HOME/.local/bin/agentik-suite describe sources --json respeak`, else, with no
launcher or an answer that does not count, the one respeak at scope user or
managed in `installed_plugins.json` beside the plugin cache (packet fk4); a root
counts only when it holds the renderer, and no other folder fills in.
`scripts/readme-render` imports the finder from here. The render runs once per `ask`, in technical mode, in a temp
dir away from the ledger, its source and output named OPEN-QUESTIONS.md so
respeak's scopes keyed on that name apply; the dir carries a copy of the repo's
`.claude/respeak/` and leaves with the run. Its `claude -p` child is a marked
session helper, one level below the caller and refused past depth 2 (d-n2 item
9). The renderer gates its own output with the measure and retries.
"""

import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import time

from .common import Refusal, bounded_err, git_top
from .questions import NAME

__all__ = ["CONTRACT", "RENDER", "RENDER_WALL", "HELPER_MAX_DEPTH", "respeak_root",
           "respeak_source", "read_sources", "helper_depth", "repo_config", "render_text"]

RENDER = os.path.join("scripts", "respeak-render.sh")
# The render is one model run with up to two rounds; past this wall its text stays.
RENDER_WALL = 600
# fk4 R2: the suite's finder, at the launcher's fixed place (never PATH), its answer
# read whole under a wall; past SOURCES_BYTES it is a flood and does not count.
LAUNCHER = os.path.join(".local", "bin", "agentik-suite")
SOURCES_SCHEMA = "agentik.sources/1"
SOURCES_WALL = 5
SOURCES_BYTES = 1 << 20
KINDS = ("own", "plugin", "folder", "undecided", "absent")
# fk4 R3: with no answer, the file's rule over the entries of this name at these scopes.
INSTALLED = "installed_plugins.json"
NAME_RESPEAK = "respeak"
OWN = "respeak@agentik"
SCOPES = ("user", "managed")
# relay-r1 section 10, as scripts/readme-render reads it: a helper runs as
# CLAUDE_SESSION_DEPTH=d+1 CLAUDE_SESSION_HELPER=1 and is refused past depth 2.
HELPER_MAX_DEPTH = 2
# The repo's respeak configuration, copied into the render's temp dir.
CONFIG = os.path.join(".claude", "respeak")
# A render inside a render: decisions' own mark, and respeak's own guard. The
# renderer refuses to start under RESPEAK_RENDER_DEPTH and sets it for its own
# runner, so it is checked here and never set for the child.
GUARDS = ("RESPEAK_DEPTH", "RESPEAK_RENDER_DEPTH")
# The renderer's first stderr line in a warning: its terminal escapes (OSC, CSI and
# the two-byte ones) and other control characters dropped, at most LINE_CAP
# characters (d-n2 fix round N1).
ESCAPE = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?|\x1b\[[0-?]*[ -/]*[@-~]|\x1b[@-_]?")
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
LINE_CAP = 200
# The contract travels with the package, since the installed tool cannot read the
# plugin's files (design d18 section 6).
CONTRACT = """\
Rewrite only the prose. Keep exactly, character for character:
- every heading line, `## N. Title`, and the blocks in their order;
- every number;
- every bold label that opens a line: **Where things stand.**, **The choice.**,
  **What each answer sets in motion.**, **Recommendation.**, **Report.**, and
  **Your answer:** with any text after it;
- each option bullet's bold label and the ` (Recommended)` marker on the first.
The options stay one `- ` bullet a line under the third label, and the choice
ends in `?`. Add nothing before the first heading and nothing after the last block.
"""


def has_renderer(root):
    """True when `root` is a path holding the renderer."""
    return isinstance(root, str) and bool(root) and os.path.isfile(os.path.join(root, RENDER))


def _found(by, root, kind=None, plugin=None, version=None, declared=None, seen=()):
    return {"by": by, "root": root, "kind": kind, "plugin": plugin, "version": version,
            "declared": declared, "seen": list(seen)}


def _text(value):
    return value if isinstance(value, str) and value else None


def _seen(rows):
    """The `seen` list's well-formed rows, each with its four keys."""
    if not isinstance(rows, list):
        return []
    return [{key: row.get(key) for key in ("plugin", "version", "scope", "root")}
            for row in rows if isinstance(row, dict)]


def _declared(value):
    """`{"path", "line"}` when the answer gives a path and a line number, else None."""
    if (isinstance(value, dict) and _text(value.get("path"))
            and isinstance(value.get("line"), int) and not isinstance(value.get("line"), bool)):
        return {"path": value["path"], "line": value["line"]}
    return None


def _drain(child, got, cap):
    """Read the child's stdout into `got` until EOF or past `cap` bytes."""
    size, fd = 0, child.stdout.fileno()
    while size <= cap:
        try:
            chunk = os.read(fd, 65536)
        except OSError:
            break
        if not chunk:
            got.append(None)
            return
        got.append(chunk)
        size += len(chunk)


def _kill(child):
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except OSError:
        pass
    child.wait()


def read_sources(environ):
    """The suite's row for respeak (R2), or None when its answer does not count: no
    HOME or no launcher, an exit other than 0, past SOURCES_WALL, over SOURCES_BYTES, or stdout
    not one `agentik.sources/1` object with `ok` true and one row in `tools`."""
    home = environ.get("HOME")
    if not home:            # `$HOME/.local/bin`: with no HOME, no launcher is asked
        return None
    launcher = os.path.join(home, LAUNCHER)
    if not os.path.isfile(launcher):
        return None
    try:
        child = subprocess.Popen([launcher, "describe", "sources", "--json", "respeak"],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, env=dict(environ),
                                 start_new_session=True)
    except (OSError, ValueError):
        return None
    try:
        deadline = time.monotonic() + SOURCES_WALL
        got = []
        reader = threading.Thread(target=_drain, args=(child, got, SOURCES_BYTES), daemon=True)
        reader.start()
        reader.join(SOURCES_WALL)
        if reader.is_alive() or not got or got[-1] is not None:
            _kill(child)        # past the wall, or over the cap
            reader.join(1)
            return None
        try:
            code = child.wait(max(deadline - time.monotonic(), 0.01))
        except subprocess.TimeoutExpired:
            _kill(child)
            return None
    finally:
        child.stdout.close()
    if code != 0:
        return None
    try:
        answer = json.loads(b"".join(got[:-1]).decode("utf-8"))
    except (ValueError, RecursionError, MemoryError):
        return None
    if not (isinstance(answer, dict) and answer.get("schema") == SOURCES_SCHEMA
            and answer.get("ok") is True and isinstance(answer.get("tools"), list)
            and len(answer["tools"]) == 1 and isinstance(answer["tools"][0], dict)
            and answer["tools"][0].get("kind") in KINDS):
        return None
    return answer["tools"][0]


def _from_file(cache):
    """R3: the respeak entries at scope user or managed in `installed_plugins.json`
    beside `cache`; one stands, two or more are undecided, none is absent."""
    path = os.path.join(os.path.dirname(os.path.normpath(cache)), INSTALLED)
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError, RecursionError, MemoryError):
        data = None
    plugins = data.get("plugins") if isinstance(data, dict) else None
    seen = []
    for ident, entries in (plugins.items() if isinstance(plugins, dict) else ()):
        if not (isinstance(ident, str) and ident.split("@")[0] == NAME_RESPEAK
                and isinstance(entries, list)):
            continue
        for entry in entries:
            if isinstance(entry, dict) and entry.get("scope") in SCOPES:
                seen.append({"plugin": ident, "version": entry.get("version"),
                             "scope": entry["scope"], "root": entry.get("installPath")})
    if len(seen) == 1:
        one = seen[0]
        root = _text(one["root"])
        return _found("file", root if has_renderer(root) else None,
                      "own" if one["plugin"] == OWN else "plugin", one["plugin"],
                      _text(one["version"]), None, seen)
    return _found("file", None, "undecided" if seen else "absent", seen=seen)


def respeak_source(environ, cache):
    """The respeak `ask` renders through and how it was found (R1 to R5): a dict of
    `by` (`variable`, `read` or `file`), `root` (None when none stands and renders),
    and the source's `kind`, `plugin`, `version`, `declared` and `seen`."""
    named = environ.get("RESPEAK_ROOT")
    if named:
        return _found("variable", named if has_renderer(named) else None)
    row = read_sources(environ)
    if row is None:
        return _from_file(cache)
    kind, root, plugin = row["kind"], _text(row.get("root")), _text(row.get("plugin"))
    if kind == "own" and plugin != OWN:     # review 1: `own` is respeak's own id alone
        kind = "plugin"
    stands = kind in ("own", "plugin", "folder") and row.get("found") is True
    return _found("read", root if stands and os.path.isabs(root or "") and has_renderer(root)
                  else None, kind, plugin, _text(row.get("version")),
                  _declared(row.get("declared")), _seen(row.get("seen")))


def respeak_root(environ, cache):
    """The root `respeak_source` gives, or None."""
    return respeak_source(environ, cache)["root"]


def helper_depth(environ):
    """(d + 1, None), d being CLAUDE_SESSION_DEPTH (unset or empty: 0), or (None, why)
    when it is no count or d + 1 passes HELPER_MAX_DEPTH."""
    raw = environ.get("CLAUDE_SESSION_DEPTH", "")
    if raw and not re.fullmatch(r"[0-9]+", raw):
        return None, "CLAUDE_SESSION_DEPTH %r is not a non-negative integer" % raw
    depth = int(raw or "0") + 1
    if depth > HELPER_MAX_DEPTH:
        return None, "CLAUDE_SESSION_DEPTH %s: a helper is refused past depth %d" % (
            raw, HELPER_MAX_DEPTH)
    return depth, None


def repo_config(where):
    """The nearest `.claude/respeak/` from `where` up to its git top (`where` alone
    outside a work tree), or None."""
    try:
        top = git_top(where)
    except Refusal:
        top = None
    here = os.path.realpath(where)
    top = os.path.realpath(top) if top else here
    while True:
        found = os.path.join(here, CONFIG)
        if os.path.isdir(found):
            return found
        if here == top or os.path.dirname(here) == here:
            return None
        here = os.path.dirname(here)


def first_line(text):
    """The first non-blank line of `text`, its escapes and control characters dropped,
    stripped and capped at LINE_CAP characters, or ''."""
    for line in (text or "").splitlines():
        line = CONTROL.sub("", ESCAPE.sub("", line)).strip()
        if line:
            return line if len(line) <= LINE_CAP else line[:LINE_CAP - 1] + "\u2026"
    return ""


def render_text(text, where, root, environ):
    """(`text` rendered, None), or (None, why not). The temps sit in one temp dir
    away from `where`, which carries a copy of the repo's respeak configuration
    and leaves with the run."""
    for guard in GUARDS:
        if environ.get(guard):
            return None, "%s is set (a render inside a render)" % guard
    depth, why = helper_depth(environ)
    if why:
        return None, why
    try:
        temp = tempfile.mkdtemp(prefix="decisions-ask-")
    except OSError as exc:
        return None, "no temp dir for the render: %s" % exc
    try:
        source, contract = os.path.join(temp, NAME), os.path.join(temp, "contract.txt")
        out = os.path.join(temp, "out", NAME)
        try:
            config = repo_config(where)
            if config:
                shutil.copytree(config, os.path.join(temp, CONFIG), symlinks=True)
            os.mkdir(os.path.dirname(out))
            for path, body in ((source, text), (contract, CONTRACT)):
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(body)
        except (OSError, shutil.Error) as exc:
            return None, "the render's temp dir cannot be filled: %s" % exc
        env = dict(environ, RESPEAK_DEPTH="1", CLAUDE_PLUGIN_ROOT=root,
                   CLAUDE_SESSION_HELPER="1", CLAUDE_SESSION_DEPTH=str(depth))
        try:
            code, _, said = bounded_err(["bash", os.path.join(root, RENDER), "--mode",
                                         "technical", "--source", source, "--out", out,
                                         "--contract", contract, "--max-rounds", "2"],
                                        RENDER_WALL, cwd=temp, env=env)
        except subprocess.TimeoutExpired:
            return None, "the render took over %d s" % RENDER_WALL
        except OSError as exc:
            return None, "the render did not start: %s" % exc
        if code != 0:
            said = first_line(said)
            return None, "the render exited %d%s" % (code, ": " + said if said else "")
        try:
            with open(out, encoding="utf-8") as handle:
                return handle.read(), None
        except (OSError, UnicodeDecodeError) as exc:
            return None, "the render exited 0 but its output is unreadable: %s" % (
                exc.__class__.__name__)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
