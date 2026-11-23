"""`init` (dc1, dc2): an empty ledger where `locate` finds none, and its block in the CLAUDE.md
beside it, written by `render`'s own `block` and `apply`; both files go on the edit-gates
list, and the run says so. Where a ledger is already there and that CLAUDE.md holds no block
or is absent (dc2 R4), it lints the ledger as `render` does, then adds the block rendered
from it under the file's own lines, the ledger untouched, and lists CLAUDE.md alone; `render`
only rewrites a block that is there. dc3: after the gate's line, a CLAUDE.md that held
hand-written lines is said with what they load and the skill that audits them. It refuses, writing nothing, where a ledger and its
block are both there, where a folder or a link to nothing stands at the ledger's path,
outside a git work tree with no `--ledger`, and where the CLAUDE.md holds markers that are
not one block or a block another ledger rendered."""

import os

from .common import Refusal, commit_texts, disk_text, keeps_crlf, read_text
from .ledger import (IN_FORCE, PROPOSED, SUPERSEDED, display, in_the_way, lint, parse,
                     where)
from .render import (TARGET, apply, block, gate_said, growth, hand_said, holds_markers,
                     is_ledger, list_gate, one_block, refuse_another)

__all__ = ["cmd_init", "EMPTY"]

EMPTY = "# Decisions\n\n## %s\n\n## %s\n\n## %s\n" % (IN_FORCE, PROPOSED, SUPERSEDED)


def cmd_init(args, out, err):
    path = where(getattr(args, "ledger", None), os.getcwd())
    if os.path.lexists(path):
        way = in_the_way(path)  # dc1 r1 F4, F5: a folder or a link to nothing is said
        if way:
            raise Refusal("init: %s; nothing written" % way)
        return add_block(path, out, err)
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        raise Refusal("init: %s is no folder; nothing written" % folder)
    target = os.path.join(folder, TARGET)
    # dc1 r1 F3: by name, never by the disk, so `claude.md` refuses on a disk of either case
    if os.path.basename(path).casefold() == TARGET.casefold() or is_ledger(target, path):
        raise Refusal("init: the ledger %s would be its own CLAUDE.md; nothing written"
                      % display(path))
    old = read_text(target) if os.path.exists(target) else ""
    apply(old, "", display(target))  # markers that are not one block refuse before a write
    refuse_another(old, target, path, "init")  # d36 ruling 4 (dc1 r1 F1)
    was, crlf = disk_text(target), keeps_crlf(target)
    new = apply(old, block(parse(EMPTY, display(path)), path, target), display(target))
    one_block(new, display(target), "init")  # a text with not one block is never written
    commit_texts([(path, EMPTY), (target, new)])  # both or neither (dc1 r1 F2)
    out.write("init: wrote %s: # Decisions and its three sections, empty\n" % display(path))
    out.write("init: wrote %s: %s\n" % (display(target), growth(was, new, crlf)))
    gate_said(out, "init", [(path, list_gate(path, err, "init")),
                            (target, list_gate(target, err, "init"))])
    hand_said(out, "init", target, old)  # dc3 R2
    next_act(out, target)
    return 0


def next_act(out, target):
    out.write("init: next, `agentik decisions new` records a question; its answer becomes "
              "an entry and reaches %s\n" % display(target))


def add_block(path, out, err):
    """dc2 R4: the block from the ledger at `path`, which is there, into the CLAUDE.md beside
    it when that file holds no block or is absent; the pin's refusal where it holds one."""
    already = Refusal("init: a ledger is already at %s; nothing written" % path)
    target = os.path.join(os.path.dirname(path), TARGET)
    if not os.path.isfile(path) or os.path.basename(path).casefold() == TARGET.casefold() \
            or is_ledger(target, path):
        raise already
    old = read_text(target) if os.path.exists(target) else ""
    if holds_markers(old):
        apply(old, "", display(target))  # markers that are not one block say so
        raise already
    ledger, problems = lint(path)
    if problems:
        for name, line, message in problems:
            out.write("%s:%d: %s\n" % (name, line, message))
        return 1
    refuse_another(old, target, path, "init")
    was, crlf = disk_text(target), keeps_crlf(target)
    new = apply(old, block(ledger, path, target), display(target))
    one_block(new, display(target), "init")  # a text with not one block is never written
    commit_texts([(target, new)])
    out.write("init: %s is already there; it stays as it is\n" % display(path))
    out.write("init: wrote %s: %s\n" % (display(target), growth(was, new, crlf)))
    gate_said(out, "init", [(target, list_gate(target, err, "init"))])
    hand_said(out, "init", target, old)  # dc3 R2
    next_act(out, target)
    return 0
