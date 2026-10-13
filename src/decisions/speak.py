"""respeak, found and run for `ask` (design d18 section 3).

decisions calls respeak, and respeak knows nothing of decisions; the plugin
declares no dependency. The root is `RESPEAK_ROOT`, else the highest version
under the plugin cache (`*/respeak/<version>/`, compared as a version tuple,
since a sort over whole paths is wrong). `scripts/readme-render` imports the
finder from here. The render runs once per `ask`, in technical mode, in a temp
dir away from the ledger, its source and output named OPEN-QUESTIONS.md so
respeak's scopes keyed on that name apply; the dir carries a copy of the repo's
`.claude/respeak/` and leaves with the run. Its `claude -p` child is a marked
session helper, one level below the caller and refused past depth 2 (d-n2 item
9). The renderer gates its own output with the measure and retries.
"""

import glob
import os
import re
import shutil
import subprocess
import tempfile

from .common import Refusal, bounded_err, git_top
from .questions import NAME

__all__ = ["CONTRACT", "RENDER", "RENDER_WALL", "HELPER_MAX_DEPTH", "respeak_root",
           "newest_root", "version_key", "helper_depth", "repo_config", "render_text"]

RENDER = os.path.join("scripts", "respeak-render.sh")
# The render is one model run with up to two rounds; past this wall its text stays.
RENDER_WALL = 600
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


def version_key(name):
    """The version tuple of a directory name, or None when it is not one."""
    try:
        return tuple(int(part) for part in name.split("."))
    except ValueError:
        return None


def newest_root(cache):
    """The highest-versioned `<cache>/*/respeak/<version>/` holding the renderer, or None."""
    found = []
    for path in glob.glob(os.path.join(cache, "*", "respeak", "*")):
        key = version_key(os.path.basename(path))
        if key is not None and os.path.isfile(os.path.join(path, RENDER)):
            found.append((key, path))
    return max(found)[1] if found else None


def respeak_root(environ, cache):
    """`RESPEAK_ROOT` when it holds the renderer, else the newest installed root, or None."""
    root = environ.get("RESPEAK_ROOT")
    if root:
        return root if os.path.isfile(os.path.join(root, RENDER)) else None
    return newest_root(cache)


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
