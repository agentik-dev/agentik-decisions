"""`render`: the lint, then the generated block in a CLAUDE.md.

    render [--into PATH] [--check | --lint | --fold-tails]

The lint runs first in every mode, over the ledger and the OPEN-QUESTIONS.md
beside it: each problem prints `file:line: message` and the exit is 1. `--lint` stops there,
and when clean prints one line, `render: the block for PATH is N B; it is loaded on every
turn`, N the bytes of the block render would write there, CRLF counted when the target
keeps it (d32); a target whose markers render refuses gets one stderr line and no size, the
exit unchanged. Otherwise the block goes between
BEGIN and END in PATH (default: the CLAUDE.md beside the ledger), replacing a
stale block in place, or appended after one blank line when the markers are
absent. `--check` writes nothing: it prints the unified diff render would make
and exits 1 when the block is stale, 0 when it is fresh. A target that is the
ledger itself, by its path, a link or a hard link, is refused with exit 2. The write keeps
the target's line end and goes through a link to the file it names, and its line names the
block's growth in bytes on disk, `render: wrote PATH: X B to Y B, +D B; the block is loaded
on every turn`,
since every turn of every session loads it (d32); no cap is set, the number is the owner's.

The block: one line naming its source and the command that regenerates it;
the `Every session` entries, each number, title and paragraph word for word and
its tail cut to the first date and a count of its amendments, `(2026-09-21;
amended 2 times, see the ledger)` (d29 act 4; a tail that opens with no date is
written whole); then `- N Title (area)` for each other entry in force, under a
sentence saying `decisions show N` reads one. Proposed and Superseded entries
stay out. `--check` also passes a block that carries the whole tails, with one
stderr line saying how many bytes more, so a CLAUDE.md rendered before 0.14.0
stays fresh until `render` shortens it.
"""

import difflib
import os
import subprocess

from . import questions
from .ask import LOCK, NEW_WAIT
from .common import (GIT_TIMEOUT, Refusal, bounded, disk_text, held, keeps_crlf, on_disk,
                     read_text, write_text)
from .ledger import (DATE, EVERY_SESSION, IN_FORCE, amended, display, final_parenthetical,
                     folded, lint, load, parse)

__all__ = ["cmd_render", "block", "apply", "tilde", "is_ledger", "block_bytes", "growth",
           "tail_note", "BEGIN", "END", "TARGET"]

BEGIN = "<!-- BEGIN GENERATED: decisions -->"
END = "<!-- END GENERATED: decisions -->"
TARGET = "CLAUDE.md"


def short_tail(text):
    """An Every session line with its tail cut to its first date and the count of
    `amended <date>` in it; a line whose tail opens with no date stays whole."""
    text = text.rstrip()
    tail = final_parenthetical(text)
    first = DATE.match(tail.lstrip()) if tail is not None else None
    if first is None:
        return text
    return "%s (%s%s)" % (text[:-(len(tail) + 2)].rstrip(), first.group(0), tail_note(text))


def tail_note(text):
    """The note the block's short tail carries for the line `text`, `; amended once, see
    the ledger` or `; amended N times, see the ledger`, else "" (d32)."""
    tail = final_parenthetical(text.rstrip())
    if tail is None or DATE.match(tail.lstrip()) is None:
        return ""
    count = amended(tail)
    return "" if count == 0 else "; amended %s, see the ledger" % (
        "once" if count == 1 else "%d times" % count)


def block_bytes(text, crlf=False):
    """The bytes of the one block between the markers in `text`, both marker lines
    included, every line end CRLF when `crlf`, or None when `text` holds no such block
    (d32). A text read with its line ends kept is measured as it is on disk."""
    lines = text.splitlines(keepends=True)
    begins = [i for i, line in enumerate(lines) if line.strip() == BEGIN]
    ends = [i for i, line in enumerate(lines) if line.strip() == END]
    if len(begins) != 1 or len(ends) != 1 or ends[0] < begins[0]:
        return None
    return on_disk("".join(lines[begins[0]:ends[0] + 1]), crlf)


def growth(old, new, crlf=False):
    """`X B to Y B, +D B; the block is loaded on every turn`, the block in `old` then in
    `new`, a text without one counted 0 B (d32). `old` is the target as it is on disk,
    line ends kept; `new` is written with CRLF when `crlf` (F1)."""
    before, after = block_bytes(old) or 0, block_bytes(new, crlf) or 0
    return "%d B to %d B, %+d B; the block is loaded on every turn" % (before, after,
                                                                       after - before)


def tilde(path):
    """`path` absolute, with the home directory written `~`."""
    path, home = os.path.abspath(path), os.path.expanduser("~").rstrip(os.sep)
    return "~" + path[len(home):] if path.startswith(home + os.sep) else path


def is_ledger(target, ledger):
    """True when `target` is the ledger file: for a target that exists, the same file (a
    hard link, or another case on a case-insensitive disk); else the same resolved path."""
    if os.path.exists(target):
        try:
            return os.path.samefile(target, ledger)
        except OSError:
            return False
    return os.path.realpath(target) == os.path.realpath(ledger)


def fold_tails(text):
    """(`text` with the tail of each entry in force in form T2, the numbers folded,
    the numbers left because the latest amendment names no source) (d31)."""
    lines = text.splitlines(keepends=True)
    done, left = [], []
    for entry in parse(text).entries:
        tail = final_parenthetical(entry.body) if entry.section == IN_FORCE else None
        new = folded(tail) if tail is not None else None
        if new is None or new == tail:
            continue
        if not questions.TAIL.match(new):
            left.append(entry.number)
            continue
        line = lines[entry.line - 1]
        body = line.rstrip()
        lines[entry.line - 1] = "%s(%s)%s" % (body[:-(len(tail) + 2)], new, line[len(body):])
        done.append(entry.number)
    return "".join(lines), done, left


def head_holds(path, data):
    """The short sha of git's HEAD when its blob at the real path of `path` is `data`
    byte for byte, else None (d31). The claim itself is tested, since git's status is
    also empty for a file HEAD lacks: an untracked file git is told not to list, a
    name in another case, a link, an index told not to look."""
    real = os.path.realpath(path)
    where, name = os.path.dirname(real), os.path.basename(real)
    try:
        code, out = bounded(["git", "rev-parse", "--verify", "-q", "HEAD^{commit}"],
                            GIT_TIMEOUT, cwd=where)
        sha = out.strip()
        if code != 0 or not sha:
            return None
        blob = subprocess.run(["git", "cat-file", "blob", "%s:./%s" % (sha, name)],
                              cwd=where, capture_output=True, timeout=GIT_TIMEOUT)
        if blob.returncode != 0 or blob.stdout != data:
            return None
        code, out = bounded(["git", "rev-parse", "--short", sha], GIT_TIMEOUT, cwd=where)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.strip() if code == 0 and out.strip() else None


def cmd_fold(path, out, err):
    """`render --fold-tails`, after the lint and before the block (d31)."""
    name = display(path)
    with held(os.path.join(os.path.dirname(path), LOCK), NEW_WAIT, err):
        old = read_text(path)
        try:
            with open(path, "rb") as handle:
                data = handle.read()
        except OSError as exc:
            raise Refusal("%s: unreadable: %s" % (path, exc))
        new, done, left = fold_tails(old)
        for number in left:
            err.write("render: entry %d's latest amendment names no source, so its tail "
                      "stays as it stands\n" % number)
        if not done:
            out.write("render: no tail to fold in %s\n" % name)
            return
        sha = head_holds(path, data)
        if sha is None:
            raise Refusal("render: HEAD does not hold %s as it stands; commit it first; "
                          "nothing written" % name)
        problems = parse(new).problems
        if problems:
            raise Refusal("render: the folded ledger fails the lint; nothing written:\n"
                          + "\n".join("%s:%d: %s" % (name, n, m) for n, m in problems))
        write_text(path, new)
    out.write("render: folded the tails of %d entries in %s, %d B to %d B; %s holds them "
              "whole\n" % (len(done), name, len(old.encode()), len(new.encode()), sha))


def block(ledger, path, target, tails=False):
    """The block, markers included, for the ledger at `path` rendered into `target`;
    `tails` keeps each Every session entry's whole tail, the form before 0.14.0.

    Beside its ledger the block names both by their basenames; elsewhere, as
    `~/.claude/CLAUDE.md` for a portfolio ledger, it names both whole, and the
    commands carry `--ledger`, so they run from any directory."""
    here = os.path.dirname(os.path.abspath(target))
    beside = os.path.realpath(os.path.dirname(os.path.abspath(path))) == os.path.realpath(here)
    source = os.path.basename(path) if beside else tilde(path)
    command, show = "decisions render", "decisions show N"
    if not beside:
        command += " --ledger %s --into %s" % (source, tilde(target))
        show += " --ledger %s" % source
    elif os.path.basename(target) != TARGET:
        command += " --into %s" % os.path.basename(target)
    pieces = ["Generated from `%s` by `%s`; edit the ledger and rerun it, never this block."
              % (source, command)]
    in_force = [e for e in ledger.entries if e.section == IN_FORCE]
    every = [e.text if tails else short_tail(e.text) for e in in_force
             if (e.area or "").lower() == EVERY_SESSION.lower()]
    others = ["- %d %s (%s)" % (e.number, e.title, e.area) for e in in_force
              if (e.area or "").lower() != EVERY_SESSION.lower()]
    if every:
        pieces.append("\n".join(every))
    if others:
        pieces.append("The other entries in force, one line each; `%s` reads one." % show)
        pieces.append("\n".join(others))
    return "%s\n%s\n%s\n" % (BEGIN, "\n\n".join(pieces), END)


def apply(text, generated, target=TARGET):
    """`text` with `generated` between the markers, or appended when they are absent."""
    lines = text.splitlines(keepends=True)
    begins = [i for i, line in enumerate(lines) if line.strip() == BEGIN]
    ends = [i for i, line in enumerate(lines) if line.strip() == END]
    if not begins and not ends:
        return generated if not text.strip() else text.rstrip("\n") + "\n\n" + generated
    if len(begins) != 1 or len(ends) != 1 or ends[0] < begins[0]:
        raise Refusal("%s: the GENERATED markers are not one BEGIN before one END" % target)
    return "".join(lines[:begins[0]]) + generated + "".join(lines[ends[0] + 1:])


def cmd_render(args, path, out, err):
    ledger, problems = lint(path)
    if problems:
        for name, line, message in problems:
            out.write("%s:%d: %s\n" % (name, line, message))
        return 1
    target = os.path.abspath(os.path.expanduser(args.into)) if args.into else \
        os.path.join(os.path.dirname(path), TARGET)
    if args.lint:
        # d32: the measure, the bytes of the block render would write there, CRLF counted
        # when the target keeps it; a target render refuses gets no size (F4)
        try:
            text = read_text(target) if os.path.exists(target) else ""
        except Refusal:
            text = ""  # unreadable here, measured as before; render itself refuses it
        try:
            apply(text, "", display(target))
        except Refusal:
            err.write("render: %s: its GENERATED markers are not one block, so no size\n"
                      % display(target))
            return 0
        out.write("render: the block for %s is %d B; it is loaded on every turn\n"
                  % (display(target), on_disk(block(ledger, path, target),
                                             keeps_crlf(target))))
        return 0
    if is_ledger(target, path):
        raise Refusal("render: the target %s is the ledger itself; nothing written"
                      % display(target))
    old = read_text(target) if os.path.exists(target) else ""
    was = disk_text(target)
    if getattr(args, "fold_tails", False):
        apply(old, "", display(target))  # a target refused is refused before the fold
        cmd_fold(path, out, err)
        ledger = load(path)
    new = apply(old, block(ledger, path, target), display(target))
    if args.check:
        if new == old:
            return 0
        whole = block(ledger, path, target, tails=True)
        if apply(old, whole, display(target)) == old:
            more = len(whole.encode()) - len(block(ledger, path, target).encode())
            err.write("render: %s carries the entries' whole tails, %d B more; run render to "
                      "shorten it\n" % (os.path.basename(target), more))
            return 0
        name = display(target)
        out.writelines(difflib.unified_diff(old.splitlines(keepends=True),
                                            new.splitlines(keepends=True),
                                            name, name + " (rendered)"))
        return 1
    if new == old:
        out.write("render: %s is fresh\n" % display(target))
        return 0
    crlf = keeps_crlf(target)
    write_text(target, new)
    out.write("render: wrote %s: %s\n" % (display(target), growth(was, new, crlf)))
    return 0
