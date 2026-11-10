"""`expire`: move each repo's closed NICE items, and its old S4 ones, out of
NICE_TO_HAVE.md into `history/NICE-overflow.md`, appended byte for byte (d34).

    expire [REPO...] [--order FILE] [--days N] [--write] [--json]

It reads NICE_TO_HAVE.md as `backlog` does and places it against HANDOFF.md, or
`--order FILE`, the same way. An item expires when it is closed (a lead `backlog`
reads as closed: the one form to write is `Closed YYYY-MM-DD <sha, history file or void>: `
opening the `finding` cell or the bullet, then the finding's lead), or when it is
open, placed as S4 (S4 or no level), follows no open step, and its date is more than
N days old (14 by default). Its date is the first valid YYYY-MM-DD of a row's `from`
cell, else of a bullet's text; an open item with none never expires. An S1 to S3
item, or one on an open step's path, older than N days is listed as kept, to lift
into HANDOFF.md or to close.

Without `--write` it prints what would move and writes nothing. With it, every repo
with something to move is checked before any is written: HEAD holds its
NICE_TO_HAVE.md byte for byte, and both files read; else nothing is written (exit 2).
Then, under the repo's lock, both files are read again (changed: refused), and one
`commit_texts` replaces the archive, then NICE_TO_HAVE.md: the items' lines, with a
bullet's indented ones, leave NICE_TO_HAVE.md, no other byte moving, and are
appended byte for byte to the archive under one dated heading, rows under the NICE
header, then bullets; the archive is made when absent and never rewritten. A failed
replace puts back what was replaced. A run killed between the two replaces leaves
the items in both files; the next run finds the archive ending with this very move
(the same HEAD, the same lines) and replaces NICE_TO_HAVE.md alone, so no item is
appended twice. Exit 0 when the view printed or the move was made, 2 for usage, a
REPO not a directory, a file unreadable, a refusal or a failed write; never 1.
"""

import datetime
import json
import os
import re

from . import backlog
from .ask import LOCK, NEW_WAIT
from .common import Refusal, commit_texts, disk_text, git_top, held, read_text
from .render import head_holds

__all__ = ["cmd_expire", "expiring", "extents", "moved_texts"]

ARCHIVE = os.path.join("history", "NICE-overflow.md")
DAYS = 14
MARKED = re.compile(r"^(?:\*\*)?Closed\b[^:]*:\s*(?:\*\*)?")
DATE = re.compile(r"\b([0-9]{4})-([0-9]{2})-([0-9]{2})\b")
ARCHIVE_HEAD = ("# NICE_TO_HAVE.md overflow\n\nItems moved out of NICE_TO_HAVE.md, appended "
                "and never edited: closed ones, and S4 ones past their days.\n")
ROW_HEAD = ("| id | level | area | finding | evidence | from |\n"
            "|---|---|---|---|---|---|\n")


def extents(text):
    """{first line: last line} of each bullet: its indented lines, and a blank line
    inside when an indented one follows (as `backlog.gathered` joins them)."""
    ends, current = {}, None
    for n, kind, _ in backlog.blocks(text):
        if kind == "more" and current is not None:
            ends[current] = n
            continue
        if kind == "blank":
            continue
        current = n if kind == "bullet" else None
        if current is not None:
            ends[n] = n
    return ends


def first_date(text):
    """The first valid YYYY-MM-DD in `text`, or None."""
    for m in DATE.finditer(text or ""):
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            continue
    return None


def title_of(text):
    """The lead of a finding, after a `Closed <date> <what>: ` marker when it opens one."""
    m = MARKED.match(text)
    return backlog.trimmed(backlog.lead_of(text[m.end():] if m else text))[:backlog.TITLE]


def described(lines, n, end, payload):
    """(id, title, date) of the item at line n: a row's from its cells, a bullet's
    from its text, its indented lines included."""
    kind, value = payload
    if kind == "row":
        cells = (list(value) + [""] * 6)[:6]
        return cells[0], title_of(cells[3]), first_date(cells[5])
    joined = " ".join(lines[n - 1:end])
    return None, title_of(value), first_date(joined[2:])


def expiring(repo, ordered, days, today):
    """The view of one repo, or None without NICE_TO_HAVE.md."""
    v = backlog.view(repo, ordered)
    if v is None:
        return None
    text = read_text(v["nice"])
    lines = text.splitlines()
    payloads = {n: (k, p) for n, k, p in backlog.blocks(text)}
    ends = extents(text)
    out, kept, undated = [], [], []

    def entry(n, level, reason, date, title, ident, after=None):
        e = {"line": n, "end": ends.get(n, n), "id": ident, "level": level,
             "reason": reason, "title": title,
             "date": date.isoformat() if date else None,
             "age": (today - date).days if date else None}
        if after is not None:
            e["after_step"] = after
        return e

    for n in v["closed"]:
        ident, title, date = described(lines, n, ends.get(n, n), payloads[n])
        out.append(entry(n, None, "closed", date, title, ident))
    for kind, item in v["rows"]:
        if kind != "item":
            continue
        n = item["line"]
        ident, _, date = described(lines, n, ends.get(n, n), payloads[n])
        if date is None:
            undated.append(n)
            continue
        if (today - date).days <= days:
            continue
        if item["placed_as"] == "S4" and item["after_step"] is None:
            out.append(entry(n, item["level"], "aged", date, item["title"], ident))
        else:
            kept.append(entry(n, item["level"], "kept", date, item["title"], ident,
                              item["after_step"]))
    out.sort(key=lambda e: e["line"])
    kept.sort(key=lambda e: e["line"])
    return {"repo": repo, "nice": v["nice"], "archive": os.path.join(repo, ARCHIVE),
            "text": text, "expired": out, "kept": kept, "undated": sorted(undated),
            "moved": False, "bytes": None, "head": None}


def section(v, raw, days, today, sha):
    """(the new NICE text, this move's heading, its body), cut from `raw`, the file's
    text with its line ends as on disk: `str.splitlines` counts a CRLF as one break, as
    `backlog` counts the text read with them made LF, so the line numbers agree."""
    lines = raw.splitlines(keepends=True)
    gone = set()
    for e in v["expired"]:
        gone.update(range(e["line"], e["end"] + 1))
    ending = lambda x: x if x.endswith(("\n", "\r")) else x + "\n"
    rows = [ending(lines[n - 1]) for e in v["expired"] if e["id"] is not None
            for n in range(e["line"], e["end"] + 1)]
    bullets = [ending(lines[n - 1]) for e in v["expired"] if e["id"] is None
               for n in range(e["line"], e["end"] + 1)]
    nice = "".join(line for i, line in enumerate(lines, 1) if i not in gone)
    heading = "## %s: `expire --days %d`, from %s\n" % (today.isoformat(), days, sha)
    body = (ROW_HEAD + "".join(rows) if rows else "") + (
        ("\n" if rows else "") + "".join(bullets) if bullets else "")
    return nice, heading, body


def holds_already(old, days, sha, body):
    """True when the archive ends with this very move: a heading `expire --days N`
    from the same HEAD, then the same lines. A run killed after the archive's replace
    and before NICE_TO_HAVE.md's leaves that; the rerun then appends nothing."""
    flat = lambda x: x.replace("\r\n", "\n")
    pattern = (r"(?:\A|\n)## [0-9]{4}-[0-9]{2}-[0-9]{2}: `expire --days %d`, from %s\n\n"
               % (days, re.escape(sha))) + re.escape(flat(body)) + r"\Z"
    return re.search(pattern, flat(old)) is not None


def moved_texts(v, raw, old, days, today, sha):
    """(the new NICE text, the new archive text) for a view with items to move; `old`
    is the archive as on disk, None when absent, and comes back as it is when it holds
    this move already."""
    nice, heading, body = section(v, raw, days, today, sha)
    if old is not None and holds_already(old, days, sha, body):
        return nice, old
    old = ARCHIVE_HEAD if old is None else old
    return nice, old + ("\n" if old.endswith("\n") else "\n\n") + heading + "\n" + body


def disk_bytes(path):
    """The bytes of `path`, or a Refusal naming why they cannot be read."""
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError as exc:
        raise Refusal("%s: unreadable: %s" % (path, exc))


def archive_as_is(path):
    """The archive's text as on disk, None when absent; a Refusal when it cannot be
    read or its folder is not one."""
    folder = os.path.dirname(path)
    if os.path.lexists(folder) and not os.path.isdir(folder):
        raise Refusal("expire: %s is not a directory; nothing written" % folder)
    if not os.path.lexists(path):
        return None
    if not os.path.isfile(path):
        raise Refusal("%s: unreadable: not a file" % path)
    return disk_text(path)


def checked(v, days, today):
    """Every check before any write (ruling 5): HEAD holds NICE_TO_HAVE.md as it
    stands, the view was read from those very bytes, and the archive reads."""
    data = disk_bytes(v["nice"])
    v["head"] = head_holds(v["nice"], data)
    if v["head"] is None:
        raise Refusal("expire: HEAD does not hold %s as it stands; commit it first; "
                      "nothing written" % v["nice"])
    try:
        raw = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Refusal("%s: unreadable: %s" % (v["nice"], exc))
    if raw.replace("\r\n", "\n").replace("\r", "\n") != v["text"]:
        raise Refusal("expire: %s changed under the run; nothing written" % v["nice"])
    v["data"], v["old"] = data, archive_as_is(v["archive"])
    v["texts"] = moved_texts(v, raw, v["old"], days, today, v["head"])


def moved(v, err):
    """The move of one checked repo, under its lock, both files read again first."""
    with held(os.path.join(v["repo"], LOCK), NEW_WAIT, err):
        if (disk_bytes(v["nice"]) != v["data"]
                or archive_as_is(v["archive"]) != v["old"]):
            raise Refusal("expire: %s or %s changed under the run" % (v["nice"], v["archive"]))
        nice, archive = v["texts"]
        try:
            os.makedirs(os.path.dirname(v["archive"]), exist_ok=True)
        except OSError as exc:
            raise Refusal("%s: unwritable: %s" % (v["archive"], exc))
        # Archive first: a stop between the replaces leaves the items in both files.
        texts = [(v["nice"], nice)] if archive == v["old"] else [
            (v["archive"], archive), (v["nice"], nice)]
        commit_texts(texts)
    v["moved"] = True
    v["bytes"] = [len(v["data"]), len(disk_bytes(v["nice"]))]


def as_text(v, days, write):
    name = os.path.basename(v["repo"])
    closed = sum(1 for e in v["expired"] if e["reason"] == "closed")
    aged = len(v["expired"]) - closed
    lines = ["== %s  expire: %d closed, %d S4 older than %d days on no open step" % (
        name, closed, aged, days)]
    for e in v["expired"]:
        what = "closed" if e["reason"] == "closed" else "%s %s %dd" % (
            e["level"] or "S4?", e["date"], e["age"])
        lines.append("%s  NICE_TO_HAVE.md:%d  %s" % (
            what, e["line"], (e["id"] + "  " if e["id"] else "") + e["title"]))
    if v["kept"]:
        lines.append("kept, older than %d days (S1 to S3, or on an open step's path): "
                     "lift each into HANDOFF.md or close it" % days)
        for e in v["kept"]:
            lines.append("%s %s %dd  NICE_TO_HAVE.md:%d  %s" % (
                e["level"], e["date"], e["age"], e["line"],
                (e["id"] + "  " if e["id"] else "") + e["title"]))
    if v["undated"]:
        lines.append("%d with no date, never expire: NICE_TO_HAVE.md:%s" % (
            len(v["undated"]), ",".join(str(n) for n in v["undated"])))
    if v["moved"]:
        lines.append("expire: moved %d items from NICE_TO_HAVE.md (%s B to %s B) to %s; "
                     "%s holds them too" % (len(v["expired"]), "{:,}".format(v["bytes"][0]),
                                            "{:,}".format(v["bytes"][1]), ARCHIVE, v["head"]))
    elif v["expired"] and not write:
        lines.append("dry: nothing written; --write moves these %d, appended byte for byte, "
                     "to %s" % (len(v["expired"]), ARCHIVE))
    return lines


def as_json(v):
    keys = ("repo", "nice", "archive", "expired", "kept", "undated", "moved", "bytes", "head")
    return {k: v[k] for k in keys}


def cmd_expire(args, out, err):
    names = list(getattr(args, "repos", None) or [])
    if not names:
        here = os.getcwd()
        names = [git_top(here) or here]
    repos = []
    for name in names:
        if not os.path.isdir(name):
            raise Refusal("expire: %s is not a directory" % name)
        repos.append(os.path.realpath(name))
    ordered, order_file = None, getattr(args, "order", None)
    if order_file is not None:
        if not os.path.isfile(order_file):
            raise Refusal("expire: --order %s is not a file" % order_file)
        path = os.path.realpath(order_file)
        ordered = (path,) + backlog.build_order(read_text(path))
    days, write = args.days, getattr(args, "write", False)
    if days < 1:
        raise Refusal("expire: --days %d is under 1" % days)
    today = datetime.date.today()
    views, skipped = [], []
    for repo in repos:
        v = expiring(repo, ordered, days, today)
        (skipped if v is None else views).append(repo if v is None else v)
    if write:
        todo = [v for v in views if v["expired"]]
        for v in todo:
            checked(v, days, today)
        for v in todo:
            try:
                moved(v, err)
            except Refusal as exc:
                done = [os.path.basename(w["repo"]) for w in todo if w["moved"]]
                raise Refusal("%s; %s" % (exc, "moved already: " + ", ".join(done)
                                          if done else "nothing written"))
    if getattr(args, "json", False):
        out.write(json.dumps({"days": days, "today": today.isoformat(), "write": write,
                              "repos": [as_json(v) for v in views], "skipped": skipped},
                             indent=2) + "\n")
        return 0
    blocks_out = ["\n".join(as_text(v, days, write)) for v in views]
    if skipped:
        blocks_out.append("skipped (no NICE_TO_HAVE.md): %s"
                          % ", ".join(os.path.basename(s) for s in skipped))
    out.write("\n\n".join(blocks_out) + ("\n" if blocks_out else ""))
    return 0
