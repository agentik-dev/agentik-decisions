"""`render`: the lint, then the generated block in a CLAUDE.md.

    render [--into PATH] [--check | --lint]

The lint runs first in every mode, over the ledger and the OPEN-QUESTIONS.md
beside it: each problem prints `file:line: message` and the exit is 1. `--lint` stops there. Otherwise the block goes between
BEGIN and END in PATH (default: the CLAUDE.md beside the ledger), replacing a
stale block in place, or appended after one blank line when the markers are
absent. `--check` writes nothing: it prints the unified diff render would make
and exits 1 when the block is stale, 0 when it is fresh. A target that is the
ledger itself, by its path, a link or a hard link, is refused with exit 2. The write keeps
the target's line end and goes through a link to the file it names.

The block: one line naming its source and the command that regenerates it;
the `Every session` entries verbatim; then `- N Title (area)` for each other
entry in force, under a sentence saying `decisions show N` reads one.
Proposed and Superseded entries stay out.
"""

import difflib
import os

from .common import Refusal, read_text, write_text
from .ledger import EVERY_SESSION, IN_FORCE, display, lint

__all__ = ["cmd_render", "block", "apply", "tilde", "is_ledger", "BEGIN", "END", "TARGET"]

BEGIN = "<!-- BEGIN GENERATED: decisions -->"
END = "<!-- END GENERATED: decisions -->"
TARGET = "CLAUDE.md"


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


def block(ledger, path, target):
    """The block, markers included, for the ledger at `path` rendered into `target`.

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
    every = [e.text for e in in_force if (e.area or "").lower() == EVERY_SESSION.lower()]
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
    if args.lint:
        return 0
    target = os.path.abspath(os.path.expanduser(args.into)) if args.into else \
        os.path.join(os.path.dirname(path), TARGET)
    if is_ledger(target, path):
        raise Refusal("render: the target %s is the ledger itself; nothing written"
                      % display(target))
    old = read_text(target) if os.path.exists(target) else ""
    new = apply(old, block(ledger, path, target), display(target))
    if args.check:
        if new == old:
            return 0
        name = display(target)
        out.writelines(difflib.unified_diff(old.splitlines(keepends=True),
                                            new.splitlines(keepends=True),
                                            name, name + " (rendered)"))
        return 1
    if new == old:
        out.write("render: %s is fresh\n" % display(target))
        return 0
    write_text(target, new)
    out.write("render: wrote %s\n" % display(target))
    return 0
