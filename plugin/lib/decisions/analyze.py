"""`analyze`: what a repo's own history says, read from git; churn first (d29).

    analyze [churn] [REPO...] [--since Nd|YYYY-MM-DD] [--until YYYY-MM-DD] [--json]

The word after the verb names the analysis; a bare `analyze` runs every one,
today `churn` alone (a directory of that name is written `./churn`). Each REPO
is a directory, by default the working directory, read at its git top's HEAD.
The window is since <= committer time <= until: `--until` defaults to now,
`--since` to 14 days before it, a date is 00:00:00 UTC, and git gets both as
YYYY-MM-DDTHH:MM:SSZ.

Churn is accounting over building: four ratios from one `git log --numstat` and
NICE_TO_HAVE.md's snapshots. R1, records' share of lines; R2, record commits a
landing (a merge on HEAD's first-parent line); R3, commits a charter
(`history/sittings/*.md`) and the charter-only ones; R4, the backlog at `until`
and every 7 days before it. A value it cannot measure prints `-` and a
`not measured:` line, never a guess. Beside them, `block`: the bytes of the
CLAUDE.md block, loaded on every turn, at the first-parent commit at or before
`since` and `until`, null without a commit, a CLAUDE.md or a block; its text line,
`block  X B to Y B, +D B`, `-` for a null end, is left out when both are (d32).
The block is read from the commit's blob, so a CLAUDE.md that is a symlink reads
as no block.

It runs only `git rev-parse`, `log`, `rev-list` and `show`, each bounded at
`common.GIT_TIMEOUT`; it writes no file, takes no lock and ignores `--ledger`.
Exit 0 whenever the view printed, a repo outside a work tree, with no commit or
timed out included; 2 for usage, a bad window or an argument that is neither an
analysis nor a directory.
"""

import datetime
import fnmatch
import json
import os
import re
import statistics
import subprocess

from . import common
from .backlog import NICE, ROW_CELL, nice_items
from .common import Refusal
from .render import TARGET, block_bytes

__all__ = ["cmd_analyze", "ANALYSES", "path_class", "percent", "churn", "block_at"]

RECORD = ("charter", "history", "packets", "design", "handoff", "nice", "other")
BUILD = ("test", "product")
VENDOR_DIRS = ("vendor", "node_modules", "dist")
VENDOR_FILES = ("go.sum", "package-lock.json", "uv.lock")
ROOT_OTHER = ("DECISIONS.md", "OPEN-QUESTIONS.md", "CLAUDE.md", "DESIGN.md", "CHANGELOG.md",
              "README.md")
TEST_DIRS = ("tests", "test", "testdata")
TEST_FILES = ("test_*.py", "*_test.py", "conftest.py", "*_test.go", "*_test.sh")
CHARTER = re.compile(r"^history/sittings/[^/]+\.md$")
OVERFLOW = "history/NICE-overflow.md"
NUMSTAT = re.compile(r"^([0-9]+|-)\t([0-9]+|-)\t(.*)$", re.S)
STAMP = "%Y-%m-%dT%H:%M:%SZ"
DAYS = re.compile(r"^([0-9]+)d$")
DAY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
WEEK = datetime.timedelta(days=7)
NOT_COMPUTED = ["tokens", "account spend", "work redone at a respawn",
                "rows built and never landed"]
# The user's config never changes what is read: paths verbatim, the root commit's diff.
GIT = ["git", "-c", "core.quotepath=off", "-c", "log.showRoot=true"]


class TimedOut(Exception):
    """A git child past `common.GIT_TIMEOUT`; its one argument is the git verb."""


def path_class(path):
    """The class of a path from the repo root: the first rule of design section 2 that fits."""
    parts = path.split("/")
    name = parts[-1]
    if any(p in VENDOR_DIRS for p in parts[:-1]) or name in VENDOR_FILES:
        return "vendor"
    if path.startswith("history/sittings/"):
        return "charter"
    if parts[0] == "history" and len(parts) > 1:
        return "history"
    if path.startswith("design/packets/"):
        return "packets"
    if parts[0] in ("design", "docs") and len(parts) > 1:
        return "design"
    if path == "HANDOFF.md":
        return "handoff"
    if path == NICE:
        return "nice"
    if path in ROOT_OTHER:
        return "other"
    if any(p in TEST_DIRS for p in parts[:-1]) or \
            any(fnmatch.fnmatchcase(name, g) for g in TEST_FILES):
        return "test"
    return "product"


def percent(part, whole):
    """`part` of `whole` as a whole percent, half up."""
    return (200 * part + whole) // (2 * whole)


def tenths(part, whole):
    """`part` over `whole` with one decimal, half up, as text."""
    return "%d.%d" % divmod((20 * part + whole) // (2 * whole), 10)


def number(value):
    """A median as JSON keeps it: whole as an int, else the float."""
    return int(value) if value == int(value) else value


def shown(value):
    return "-" if value is None else ("%d" % value if value == int(value) else "%.1f" % value)


def git(top, *args):
    """(code, stdout) of `git args` in `top`, bounded; past the bound, TimedOut(verb)."""
    try:
        return common.bounded(GIT + list(args), common.GIT_TIMEOUT, cwd=top)
    except subprocess.TimeoutExpired:
        raise TimedOut(args[0])
    except OSError as exc:
        raise Refusal("analyze: cannot run git: %s" % exc)


def day(text, flag):
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise Refusal("analyze: %s %s is no date" % (flag, text))


def window(since, until, now=None):
    """(start, end) as naive UTC datetimes; a Refusal for a bad value or since after until."""
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None, microsecond=0)
    if until is None:
        end = now
    elif DAY.match(until):
        end = day(until, "--until")
    else:
        raise Refusal("analyze: --until takes YYYY-MM-DD, not %s" % until)
    if since is None:
        start = end - datetime.timedelta(days=14)
    elif DAYS.match(since):
        start = end - datetime.timedelta(days=int(DAYS.match(since).group(1)))
    elif DAY.match(since):
        start = day(since, "--since")
    else:
        raise Refusal("analyze: --since takes Nd or YYYY-MM-DD, not %s" % since)
    if start > end:
        raise Refusal("analyze: --since %s is after --until %s"
                      % (start.strftime(STAMP), end.strftime(STAMP)))
    return start, end


def numstat(out):
    """[(sha, [(added, deleted, path)])] of `git log --format=%x01%H --numstat -z`; a
    rename gives its new path, a binary file 0 lines."""
    found = []
    for chunk in out.split("\x01")[1:]:
        tokens = chunk.split("\0")
        sha = tokens[0][:40]
        tokens = [tokens[0][40:]] + tokens[1:]
        paths, i = [], 0
        while i < len(tokens):
            m = NUMSTAT.match(tokens[i].lstrip("\n"))
            if not m:
                i += 1
                continue
            added, deleted, path = m.groups()
            if path == "" and i + 2 < len(tokens):
                path = tokens[i + 2]
                i += 2
            paths.append((0 if added == "-" else int(added), 0 if deleted == "-" else int(deleted),
                          path))
            i += 1
        found.append((sha, paths))
    return found


def median_max(counts):
    if not counts:
        return None, None
    return number(statistics.median(counts)), max(counts)


def overflow_ids(text):
    """The first cell of each table row of history/NICE-overflow.md."""
    return {ROW_CELL.split(line.strip().strip("|"))[0].strip()
            for line in text.splitlines() if line.lstrip().startswith("|")}


def snapshots(top, head, start, end):
    """R4's snapshots, oldest first, and the ids of each one in rows."""
    points, at = [], end
    while at >= start:
        points.append(at)
        at -= WEEK
    snaps, ids = [], []
    for at in reversed(points):
        code, out = git(top, "rev-list", "-1", "--first-parent", "--before=" + at.strftime(STAMP),
                        head)
        sha = out.strip() if code == 0 else ""
        snap = {"at": at.strftime(STAMP), "commit": sha or None, "form": None, "items": None}
        found = None
        if sha:
            code, text = git(top, "show", "%s:%s" % (sha, NICE))
            if code == 0:
                items = nice_items(text)
                rows = all("id" in i for i in items)
                snap["form"], snap["items"] = ("rows" if rows else "bullets"), len(items)
                found = {i["id"] for i in items} if rows else None
        snaps.append(snap)
        ids.append(found)
    return snaps, ids


def backlog(top, head, start, end):
    """R4: {snapshots, filed, closed, moved, rising} and its `not measured:` reason or None."""
    snaps, ids = snapshots(top, head, start, end)
    nice = {"snapshots": snaps, "filed": None, "closed": None, "moved": None, "rising": None}
    why = None
    for snap in (snaps[0], snaps[-1]):
        if snap["form"] != "rows":
            date = snap["at"][:10]
            why = ("R4 filed and closed (bullets at %s: a bullet has no id)" % date
                   if snap["form"] == "bullets" else
                   "R4 filed and closed (no %s at %s)" % (NICE, date))
            break
    if why is None and len(snaps) < 2:
        why = "R4 filed and closed (one snapshot: the window is under 7 days)"
    if why is None:
        code, text = git(top, "show", "%s:%s" % (snaps[-1]["commit"], OVERFLOW))
        over = overflow_ids(text) if code == 0 else set()
        gone = ids[0] - ids[-1]
        nice["filed"] = len(ids[-1] - ids[0])
        nice["moved"] = len(gone & over)
        nice["closed"] = len(gone) - nice["moved"]
    if len(snaps) >= 3 and all(s["form"] == "rows" for s in snaps):
        counts = [s["items"] for s in snaps]
        nice["rising"] = all(a < b for a, b in zip(counts, counts[1:]))
    return nice, why


def block_at(top, head, at):
    """The bytes of the CLAUDE.md block at the first-parent commit at or before `at`, both
    marker lines included, or None: no commit, no CLAUDE.md or no block (d32)."""
    code, out = git(top, "rev-list", "-1", "--first-parent", "--before=" + at.strftime(STAMP),
                    head)
    sha = out.strip() if code == 0 else ""
    if not sha:
        return None
    code, text = git(top, "show", "%s:%s" % (sha, TARGET))
    return block_bytes(text) if code == 0 else None


def measure(top, start, end):
    """One repo's churn, or a {repo, why} when it has no commit."""
    since, until = start.strftime(STAMP), end.strftime(STAMP)
    code, out = git(top, "rev-parse", "--verify", "-q", "HEAD")
    head = out.strip() if code == 0 else ""
    if not head:
        return {"repo": top, "why": "no commit"}
    code, out = git(top, "log", head, "--no-merges", "--numstat", "-M", "-z", "--no-ext-diff",
                    "--no-textconv", "--format=%x01%H", "--since=" + since, "--until=" + until)
    if code != 0:
        return {"repo": top, "why": "git log exited %d" % code}
    commits = numstat(out)
    lines = dict.fromkeys(RECORD + BUILD, 0)
    vendor = record_commits = alone_commits = 0
    charters = {}
    for _sha, paths in commits:
        kept = [(a + d, p, path_class(p)) for a, d, p in paths]
        vendor += sum(n for n, _p, c in kept if c == "vendor")
        kept = [k for k in kept if k[2] != "vendor"]
        for n, _p, c in kept:
            lines[c] += n
        if kept and all(c in RECORD for _n, _p, c in kept):
            record_commits += 1
        alone = bool(kept) and all(CHARTER.match(p) for _n, p, _c in kept)
        alone_commits += alone
        for p in {p for _n, p, _c in kept if CHARTER.match(p)}:
            counts = charters.setdefault(p, [0, 0])
            counts[0] += 1
            counts[1] += alone
    code, out = git(top, "rev-list", "--count", "--merges", "--first-parent", "--since=" + since,
                    "--until=" + until, head)
    landings = int(out.strip()) if code == 0 and out.strip().isdigit() else 0
    touched_median, touched_max = median_max([c[0] for c in charters.values()])
    alone_median, alone_max = median_max([c[1] for c in charters.values()])
    nice, why = backlog(top, head, start, end)
    record, build = sum(lines[c] for c in RECORD), sum(lines[c] for c in BUILD)
    not_measured = []
    if record + build == 0:
        not_measured.append("R1 (no line changed)")
    if landings == 0:
        not_measured.append("R2 (no merge on the first-parent line)")
    if not charters:
        not_measured.append("R3 (no charter changed)")
    if why:
        not_measured.append(why)
    return {"repo": top, "head": head, "commits": len(commits), "landings": landings,
            "lines": lines, "vendor": vendor, "record_commits": record_commits,
            "charters": {"count": len(charters), "median": touched_median, "max": touched_max,
                         "alone": {"commits": alone_commits, "median": alone_median,
                                   "max": alone_max}},
            "nice": nice, "block": {"start": block_at(top, head, start),
                                    "end": block_at(top, head, end)},
            "not_measured": not_measured}


def read_repo(path, start, end):
    """A repo's churn, or {repo, why} when it is skipped."""
    real = os.path.realpath(path)
    try:
        code, out = git(real, "rev-parse", "--show-toplevel")
        top = out.strip() if code == 0 else ""
        if not top:
            return {"repo": real, "why": "not a git work tree"}
        return measure(os.path.realpath(top), start, end)
    except TimedOut as exc:
        return {"repo": real, "why": "timed out after %d s (git %s)"
                % (common.GIT_TIMEOUT, exc.args[0])}


def summed(read):
    """`all`, the sums of R1 and R2's counts, when two or more repos were read."""
    if len(read) < 2:
        return None
    lines = dict.fromkeys(RECORD + BUILD, 0)
    for r in read:
        for c, n in r["lines"].items():
            lines[c] += n
    return {"commits": sum(r["commits"] for r in read),
            "landings": sum(r["landings"] for r in read),
            "lines": lines, "record_commits": sum(r["record_commits"] for r in read)}


def churn(paths, start, end):
    """The churn analysis' JSON value over the directories `paths`, in their order."""
    results = [read_repo(p, start, end) for p in paths]
    read = [r for r in results if "why" not in r]
    return {"repos": read, "all": summed(read),
            "skipped": [r for r in results if "why" in r], "not_computed": list(NOT_COMPUTED),
            "order": results}


def counts_text(v):
    """R1 and R2 of a repo or of `all`, as the `==` line prints them."""
    record = sum(v["lines"][c] for c in RECORD)
    total = record + sum(v["lines"][c] for c in BUILD)
    r1 = "records %d%% of %d lines" % (percent(record, total), total) if total else "records -"
    r2 = tenths(v["record_commits"], v["landings"]) if v["landings"] else "-"
    return "commits %d  landings %d  %s  record commits %d, %s a landing" % (
        v["commits"], v["landings"], r1, v["record_commits"], r2)


def nice_text(nice):
    tokens = ["-" if s["form"] is None else "%d%s" % (s["items"], "b" if s["form"] == "bullets"
                                                       else "") for s in nice["snapshots"]]
    if nice["filed"] is not None:
        tokens.append("+%d -%d" % (nice["filed"], nice["closed"]))
        if nice["moved"]:
            tokens.append("moved %d" % nice["moved"])
    if nice["rising"]:
        tokens.append("rising")
    return "NICE " + " ".join(tokens)


def churn_text(value, start, end):
    lines = ["churn  %s..%s" % (start.strftime(STAMP), end.strftime(STAMP))]
    for r in value["order"]:
        name = os.path.basename(r["repo"])
        if "why" in r:
            lines.append("== %s  %s" % (name, r["why"]))
            continue
        ch = r["charters"]
        r3 = ("charters %d: median %s commits, %s charter-only"
              % (ch["count"], shown(ch["median"]), shown(ch["alone"]["median"]))
              if ch["count"] else "charters -")
        lines.append("== %s  %s  %s  %s" % (name, counts_text(r), r3, nice_text(r["nice"])))
        was, now = r["block"]["start"], r["block"]["end"]
        if was is not None or now is not None:
            lines.append("block  %s to %s%s" % tuple(
                ["-" if v is None else "%d B" % v for v in (was, now)]
                + ["" if None in (was, now) else ", %+d B" % (now - was)]))
        lines.extend("not measured: " + why for why in r["not_measured"])
    if value["all"] is not None:
        lines.append("== all %d  %s" % (len(value["repos"]), counts_text(value["all"])))
    lines.append("not computed: " + ", ".join(value["not_computed"]))
    return lines


ANALYSES = {"churn": (churn, churn_text)}


def cmd_analyze(args, out, err):
    names = list(getattr(args, "repos", None) or [])
    chosen = list(ANALYSES)
    if names and names[0] in ANALYSES:
        chosen = [names.pop(0)]
    start, end = window(getattr(args, "since", None), getattr(args, "until", None))
    if not names:
        names = [os.getcwd()]
    for name in names:
        if not os.path.isdir(name):
            raise Refusal("analyze: %s is neither an analysis (%s) nor a directory"
                          % (name, ", ".join(ANALYSES)))
    values = {}
    for word in chosen:
        values[word] = ANALYSES[word][0](names, start, end)
    if getattr(args, "json", False):
        doc = {"since": start.strftime(STAMP), "until": end.strftime(STAMP)}
        for word, value in values.items():
            doc[word] = {k: v for k, v in value.items() if k != "order"}
        out.write(json.dumps(doc, indent=2) + "\n")
        return 0
    out.write("\n\n".join("\n".join(ANALYSES[word][1](value, start, end))
                          for word, value in values.items()) + "\n")
    return 0
