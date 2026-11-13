"""`init` (dc1): an empty ledger where `locate` finds none, and its block in the CLAUDE.md
beside it, written by `render`'s own `block` and `apply`; both files go on the edit-gates
list, and the run says so. It refuses, writing nothing, where a ledger already is,
outside a git work tree with no `--ledger`, and where the CLAUDE.md holds a block another
ledger rendered."""

import os

from .common import Refusal, commit_texts, disk_text, keeps_crlf, read_text
from .ledger import IN_FORCE, PROPOSED, SUPERSEDED, display, parse, where
from .render import (TARGET, apply, block, gate_said, growth, is_ledger, list_gate,
                     refuse_another)

__all__ = ["cmd_init", "EMPTY"]

EMPTY = "# Decisions\n\n## %s\n\n## %s\n\n## %s\n" % (IN_FORCE, PROPOSED, SUPERSEDED)


def cmd_init(args, out, err):
    path = where(getattr(args, "ledger", None), os.getcwd())
    if os.path.lexists(path):
        raise Refusal("init: a ledger is already at %s; nothing written" % path)
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
    commit_texts([(path, EMPTY), (target, new)])  # both or neither (dc1 r1 F2)
    out.write("init: wrote %s: # Decisions and its three sections, empty\n" % display(path))
    out.write("init: wrote %s: %s\n" % (display(target), growth(was, new, crlf)))
    gate_said(out, "init", [(path, list_gate(path, err, "init")),
                            (target, list_gate(target, err, "init"))])
    out.write("init: next, `agentik decisions new` records a question; its answer becomes "
              "an entry and reaches %s\n" % display(target))
    return 0
