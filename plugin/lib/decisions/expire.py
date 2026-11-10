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

Without `--write` it prints what would move and writes nothing. A bullet whose last
line is followed by a line at column 0 (a lazy continuation) is kept and listed with
that line, never moved. NICE_TO_HAVE.md is read as bytes and cut at `\n` alone: a
`\r` stays with its line and no line end is rewritten in either file. A line break
the parser sees that is not a `\n` (a U+2028, a form feed, a lone `\r`) is named
in the view, and `--write` refuses that repo.

With `--write`, every repo with something to move is checked before any is written:
HEAD holds the bytes the view was parsed from, no such line break, the archive reads;
else nothing is written (exit 2). Then, under the repo's lock, NICE_TO_HAVE.md is
read once as bytes, and those bytes are the ones compared (with the view's, so with
HEAD's blob), parsed and cut; the archive is read there too. The items' lines, with
a bullet's indented ones, are appended byte for byte to the archive under one dated
heading, rows under the NICE header, then bullets; the archive is made when absent
and its bytes are never rewritten. An item whose lines the archive already holds, as
one run of lines no indented line continues, is not appended again and leaves
NICE_TO_HAVE.md all the same, so a rerun never appends an item twice. Two atomic
replaces, no rollback: the archive first, then NICE_TO_HAVE.md, each through a temp
file in its own directory, flushed, then `os.replace`. A failed or stopped second
write leaves the items in both files and nothing lost; the next run finishes the
move. Exit 0 when the view printed or the move was made, 2 for usage, a REPO not a
directory, a file unreadable, a refusal or a failed write; never 1.
"""

import datetime
import json
import os
import re
import tempfile

from . import backlog
from .ask import LOCK, NEW_WAIT
from .common import Refusal, file_mode, git_top, held, read_text
from .render import head_holds

__all__ = ["cmd_expire", "expiring", "extents", "moved_bytes", "byte_lines", "parsed"]

ARCHIVE = os.path.join("history", "NICE-overflow.md")
DAYS = 14
MARKED = re.compile(r"^(?:\*\*)?Closed\b[^:]*:\s*(?:\*\*)?")
DATE = re.compile(r"\b([0-9]{4})-([0-9]{2})-([0-9]{2})\b")
ARCHIVE_HEAD = ("# NICE_TO_HAVE.md overflow\n\nItems moved out of NICE_TO_HAVE.md, appended "
                "and never edited: closed ones, and S4 ones past their days.\n")
ROW_HEAD = ("| id | level | area | finding | evidence | from |\n"
            "|---|---|---|---|---|---|\n")


def byte_lines(data):
    """`data` cut at b"\n" alone, each line keeping its own end; a `\r` stays with
    its line, and a last line with no `\n` stays as it is."""
    parts = data.split(b"\n")
    return [part + b"\n" for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def parsed(data):
    """(the text the parser reads, the first line where its lines are not the
    newline's lines, or None). The text is `data` as UTF-8 with one `\r` before each
    `\n` dropped, so a CRLF line parses as `backlog` reads it; any other break
    `str.splitlines` makes (U+2028, a form feed, a lone `\r`) splits a line the cut
    would not, and is named instead."""
    text = data.decode("utf-8")
    flat = "\n".join(p[:-1] if p.endswith("\r") else p for p in text.split("\n"))
    mine = flat.split("\n")
    if mine[-1] == "":
        mine.pop()
    theirs = flat.splitlines()
    if mine == theirs:
        return flat, None
    for n, (a, b) in enumerate(zip(mine, theirs), 1):
        if a != b:
            return flat, n
    return flat, min(len(mine), len(theirs)) + 1


def extents(found):
    """{first line: last line} of each bullet, from `backlog.blocks`' (line, kind,
    payload): its indented lines, and a blank line inside when an indented one follows
    (as `backlog.gathered` joins them)."""
    ends, current = {}, None
    for n, kind, _ in found:
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


def view_of(repo, ordered, text):
    """`backlog.view` of `text`, the bytes already read, so that nothing reads the file
    a second time."""
    items, closed = backlog.scanned(text)
    handoff = os.path.join(repo, backlog.HANDOFF)
    if ordered is None:
        has_handoff = os.path.lexists(handoff)
        steps = backlog.build_order(read_text(handoff))[1] if has_handoff else []
    else:
        steps = backlog.for_repo(ordered[2], repo)
    return backlog.placement(items, steps), closed


def disk_bytes(path):
    """The bytes of `path`, or a Refusal naming why they cannot be read."""
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError as exc:
        raise Refusal("%s: unreadable: %s" % (path, exc))


def expiring(repo, ordered, days, today):
    """The view of one repo, or None without NICE_TO_HAVE.md; its bytes are read once,
    kept as `data`, and parsed."""
    nice = os.path.join(repo, backlog.NICE)
    if not os.path.lexists(nice):
        return None
    data = disk_bytes(nice)
    try:
        text, breaks = parsed(data)
    except UnicodeDecodeError as exc:
        raise Refusal("%s: unreadable: %s" % (nice, exc))
    rows, closed = view_of(repo, ordered, text)
    lines = text.splitlines()
    found = list(backlog.blocks(text))
    payloads = {n: (k, p) for n, k, p in found}
    kinds = {n: k for n, k, _ in found}
    ends = extents(found)
    out, kept, undated, lazy = [], [], [], []

    def entry(n, level, reason, date, title, ident, after=None):
        e = {"line": n, "end": ends.get(n, n), "id": ident, "level": level,
             "reason": reason, "title": title,
             "date": date.isoformat() if date else None,
             "age": (today - date).days if date else None}
        if after is not None:
            e["after_step"] = after
        return e

    def moves(e):
        """`e` to move, or to keep and list when a column-0 line continues its bullet."""
        follows = e["end"] + 1
        if e["id"] is None and kinds.get(follows) == "prose":
            e["next"] = follows
            lazy.append(e)
        else:
            out.append(e)

    for n in closed:
        ident, title, date = described(lines, n, ends.get(n, n), payloads[n])
        moves(entry(n, None, "closed", date, title, ident))
    for kind, item in rows:
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
            moves(entry(n, item["level"], "aged", date, item["title"], ident))
        else:
            kept.append(entry(n, item["level"], "kept", date, item["title"], ident,
                              item["after_step"]))
    for found_list in (out, kept, lazy):
        found_list.sort(key=lambda e: e["line"])
    return {"repo": repo, "nice": nice, "archive": os.path.join(repo, ARCHIVE),
            "data": data, "breaks": breaks, "expired": out, "kept": kept, "lazy": lazy,
            "undated": sorted(undated), "moved": False, "bytes": None, "head": None}


def broken(data, n):
    """The refusal's words for line n of `data`, whose break is not a newline."""
    line = byte_lines(data)[n - 1].decode("utf-8", "replace")
    chars = [c for c in line.rstrip("\n") if ("a" + c + "a").splitlines() != ["a" + c + "a"]]
    return "NICE_TO_HAVE.md:%d breaks at %s, not at a newline" % (
        n, ", ".join("U+%04X" % ord(c) for c in chars[:1]) or "a line end")


def held_already(lines, index, item):
    """True when the archive's `lines` hold `item`'s, byte for byte, as one run of lines
    no indented line continues (so a bullet held only as the head of a longer one is
    not); `index` maps each line to where it stands."""
    k = len(item)
    for i in index.get(item[0], ()):
        if lines[i:i + k] != item:
            continue
        j = i + k
        while j < len(lines) and not lines[j].strip():
            j += 1
        if item[0].startswith(b"|") or j == len(lines) or lines[j][:1] not in b" \t":
            return True
    return False


def moved_bytes(v, data, old, days, today, sha):
    """(NICE_TO_HAVE.md's new bytes, the archive's new bytes or None when it gains
    nothing), cut from `data`; `old` is the archive's bytes, None when absent."""
    lines = byte_lines(data)
    whole = lambda x: x if x.endswith(b"\n") else x + b"\n"
    gone, rows, bullets = set(), [], []
    held, index = byte_lines(old or b""), {}
    for i, line in enumerate(held):
        index.setdefault(line, []).append(i)
    for e in v["expired"]:
        span = range(e["line"], e["end"] + 1)
        gone.update(span)
        item = [whole(lines[n - 1]) for n in span]
        if not held_already(held, index, item):
            (rows if e["id"] is not None else bullets).extend(item)
    nice = b"".join(line for n, line in enumerate(lines, 1) if n not in gone)
    if not rows and not bullets:
        return nice, None
    first = byte_lines(old)[0] if old else lines[0]
    eol = b"\r\n" if first.endswith(b"\r\n") else b"\n"
    ended = lambda text: text.replace("\n", eol.decode()).encode("utf-8")
    body = (ended(ROW_HEAD) + b"".join(rows) if rows else b"") + (
        (eol if rows else b"") + b"".join(bullets) if bullets else b"")
    heading = ended("## %s: `expire --days %d`, from %s\n" % (today.isoformat(), days, sha))
    head = old if old else ended(ARCHIVE_HEAD)
    return nice, head + (eol if head.endswith(b"\n") else eol + eol) + heading + eol + body


def archive_bytes(path):
    """The archive's bytes, None when absent; a Refusal when it cannot be read or its
    folder is not one."""
    folder = os.path.dirname(path)
    if os.path.lexists(folder) and not os.path.isdir(folder):
        raise Refusal("expire: %s is not a directory; nothing written" % folder)
    if not os.path.lexists(path):
        return None
    if not os.path.isfile(path):
        raise Refusal("%s: unreadable: not a file" % path)
    return disk_bytes(path)


def replaced(path, data):
    """`path` (through a link, the file it names) holds `data`: a temp file in its
    directory, flushed and synced, then `os.replace`. The temp goes on any failure or
    stop that lets this run on; an OSError is refused."""
    real = os.path.realpath(path)
    temp = None
    try:
        fd, temp = tempfile.mkstemp(prefix=".decisions-", dir=os.path.dirname(real))
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp, file_mode(real))
        os.replace(temp, real)
        temp = None
    except BaseException as exc:
        if temp is not None:
            try:
                os.unlink(temp)
            except OSError:
                pass
        if isinstance(exc, OSError):
            raise Refusal("%s: unwritable: %s" % (path, exc))
        raise


def checked(v):
    """Every check before any write (ruling 5), after every repo's line breaks: HEAD
    holds the very bytes the view parsed, and the archive reads."""
    v["head"] = head_holds(v["nice"], v["data"])
    if v["head"] is None:
        raise Refusal("expire: HEAD does not hold %s as it stands; commit it first; "
                      "nothing written" % v["nice"])
    archive_bytes(v["archive"])


def moved(v, days, today, err):
    """The move of one checked repo, under its lock: NICE_TO_HAVE.md read once there,
    the archive first, then NICE_TO_HAVE.md, each replaced whole; no rollback."""
    with held(os.path.join(v["repo"], LOCK), NEW_WAIT, err):
        data = disk_bytes(v["nice"])
        if data != v["data"]:
            raise Refusal("expire: %s changed under the run" % v["nice"])
        v["head"] = head_holds(v["nice"], data)
        if v["head"] is None:
            raise Refusal("expire: HEAD does not hold %s as it stands" % v["nice"])
        old = archive_bytes(v["archive"])
        nice, archive = moved_bytes(v, data, old, days, today, v["head"])
        if archive is not None:
            try:
                os.makedirs(os.path.dirname(v["archive"]), exist_ok=True)
            except OSError as exc:
                raise Refusal("%s: unwritable: %s" % (v["archive"], exc))
            replaced(v["archive"], archive)
            v["archived"] = True
        try:
            replaced(v["nice"], nice)
        except Refusal as exc:
            raise Refusal("%s; %s holds the items and so does NICE_TO_HAVE.md: run "
                          "--write again to finish" % (exc, ARCHIVE)
                          if archive is not None else str(exc))
    v["moved"] = True
    v["bytes"] = [len(data), len(nice)]


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
    if v["breaks"] is not None:
        lines.append("--write refuses this repo: %s" % broken(v["data"], v["breaks"]))
    if v["lazy"]:
        lines.append("kept, a line at column 0 continues the bullet: indent that line, "
                     "or put a blank line before it, to let it move")
        for e in v["lazy"]:
            lines.append("%s  NICE_TO_HAVE.md:%d  %s  (column 0 at :%d)" % (
                e["reason"], e["line"], e["title"], e["next"]))
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
    keys = ("repo", "nice", "archive", "expired", "kept", "lazy", "undated", "breaks", "moved",
            "bytes", "head")
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
        for v in views:
            if v["breaks"] is not None:
                raise Refusal("expire: %s: %s; nothing written"
                              % (v["repo"], broken(v["data"], v["breaks"])))
        todo = [v for v in views if v["expired"]]
        for v in todo:
            checked(v)
        for v in todo:
            try:
                moved(v, days, today, err)
            except Refusal as exc:
                done = [os.path.basename(w["repo"]) for w in todo if w["moved"]]
                tail = ("moved already: " + ", ".join(done) if done
                        else None if v.get("archived") else "nothing written")
                raise Refusal("%s; %s" % (exc, tail) if tail else str(exc))
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
