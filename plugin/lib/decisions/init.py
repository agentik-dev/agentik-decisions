"""`init` (dc1): an empty ledger where `locate` finds none, and its block in the CLAUDE.md
beside it, written by `render`'s own `block` and `apply`; both files go on the edit-gates
list, and the run says so. It refuses, writing nothing, where a ledger already is and
outside a git work tree with no `--ledger`."""

import os

from .common import Refusal, disk_text, keeps_crlf, read_text, write_text
from .ledger import IN_FORCE, PROPOSED, SUPERSEDED, display, load, where
from .render import TARGET, apply, block, gate_said, growth, is_ledger, list_gate

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
    if is_ledger(target, path):
        raise Refusal("init: the ledger %s would be its own CLAUDE.md; nothing written"
                      % display(path))
    old = read_text(target) if os.path.exists(target) else ""
    apply(old, "", display(target))  # markers that are not one block refuse before a write
    was, crlf = disk_text(target), keeps_crlf(target)
    write_text(path, EMPTY)
    out.write("init: wrote %s: # Decisions and its three sections, empty\n" % display(path))
    new = apply(old, block(load(path), path, target), display(target))
    write_text(target, new)
    out.write("init: wrote %s: %s\n" % (display(target), growth(was, new, crlf)))
    gate_said(out, "init", [(path, list_gate(path, err, "init")),
                            (target, list_gate(target, err, "init"))])
    out.write("init: next, `agentik decisions new` records a question; its answer becomes "
              "an entry and reaches %s\n" % display(target))
    return 0
