"""`render`: the lint, then the generated block in a CLAUDE.md.

    render [--scope tree] [--into PATH] [--check | --lint | --fold-tails] [--ceiling]

d36: the block lists the `Every session` entries in the ten titles' order (`ledger.TITLES`),
others after in ledger order, and leaves the tree's section out, its entries and titles
both. `--scope tree` writes that section alone, the whole file, as `tree.tree_text` makes
it, into the CLAUDE.md of the folder that holds the main checkout, or PATH; it refuses a
ledger without the section, and a target that exists and is not a tree's file this ledger
wrote; `--check` exits 1 when that file is absent or differs. Either scope refuses a target
whose block names another ledger. `--check` and `--lint` print the file's loaded bytes
beside its ceiling (`tree.CEILINGS`), and exit 1 over it only under `--ceiling`; `--lint`
warns on stderr, its exit unchanged, on a title outside the ten, on a rule word in a
hand-written line outside the block, and (d38) on a line of the ledger's checkout's
edit-gates list that reaches outside the checkout or of the owner's list that a checkout's
or a folder's list owns.

The lint runs first in every mode, over the ledger and the OPEN-QUESTIONS.md
beside it: each problem prints `file:line: message` and the exit is 1. `--lint` stops there,
and when clean prints one line, `render: the block for PATH is N B; it is loaded on every
turn`, N the bytes of the block render would write there, CRLF counted when the target
keeps it (d32); a target whose markers render refuses gets one stderr line and no size, the
exit unchanged. Otherwise the block goes between
BEGIN and END in PATH (default: the CLAUDE.md beside the ledger), replacing a
stale block in place. dc2: render rewrites a block that is there and never adds one: a
target that is absent or holds no marker line (a fenced example is none) gets nothing, and
the run refuses, exit 2, with `render: PATH is absent` or `holds no generated block`, `and
render only rewrites a block that is there; nothing written;` and the act that adds it,
`agentik decisions init` for the CLAUDE.md beside the ledger (`--ledger` as the run named
it), else the two marker lines; `--fold-tails` refuses so before it folds. dc3: before it
refuses a CLAUDE.md, in any folder, that holds hand-written lines, stdout says what they
load, comments aside and imports included, and names `/decisions:audit-claude-md`; a target
of another name gets no such line. `--lint --draft DRAFT` also prints what the target would
load with DRAFT's text in its place, `render: as drafted in DRAFT, PATH would load N B, ...`:
the target's own block put in DRAFT's block or appended, imports read from the target's
folder; it writes nothing, and refuses, exit 2, without `--lint`, under `--scope tree`, and
a DRAFT that is absent, a folder, unreadable or holds markers that are not one block. `--check` writes
nothing: it prints the unified diff render would make and exits 1 when the block is stale,
0 when it is fresh; on a target with no block, in place of the diff, `render: PATH STATE;
NEXT`, then the loaded bytes, exit 1. A target that is the
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
import shlex
import subprocess
import sys

from . import questions
from .ask import LOCK, NEW_WAIT
from .common import (GIT_TIMEOUT, Refusal, bounded, disk_text, held, keeps_crlf, on_disk,
                     read_text, write_text)
from .ledger import (DATE, IN_FORCE, TREE_SESSION, amended, display, final_parenthetical,
                     folded, is_every, is_tree, lint, load, ordered, parse)
from .tree import tilde as real_tilde
from .tree import (REPO_VARIABLES, SCOPE_COMMAND, canonical, ceiling_for, is_tree_file, loaded_bytes,
                   markers, named_ledger, rule_words, strip_comments, title_warnings, tree_text)

__all__ = ["cmd_render", "block", "apply", "tilde", "is_ledger", "block_bytes", "growth",
           "tail_note", "tree_file", "list_gate", "gate_said", "holds_markers", "invited",
           "hand_said", "BEGIN", "END", "TARGET", "GATES"]

BEGIN = "<!-- BEGIN GENERATED: decisions -->"
END = "<!-- END GENERATED: decisions -->"
TARGET = "CLAUDE.md"


GATES = "edit-gates"
GATE_EXEMPT = frozenset({"tests", "testdata", "fixtures"})
GATES_HEAD = ("# The edit gates: the files below are refused to an edit tool and a shell write;\n"
              "# change one through the instruct skill. A path or glob a line; `agentik\n"
              "# decisions render` and `answer` add the files they write.\n")


def _checkout_top(path):
    """The nearest folder above `path` that holds a `.git`, a worktree's file included."""
    folder = os.path.dirname(path)
    while True:
        if os.path.lexists(os.path.join(folder, ".git")):
            return folder
        up = os.path.dirname(folder)
        if up == folder:
            return None
        folder = up


def _owner_folder():
    """The owner's config folder: `CLAUDE_CONFIG_DIR`, else `~/.claude`."""
    moved = os.environ.get("CLAUDE_CONFIG_DIR")
    return os.path.abspath(os.path.expanduser(moved) if moved else
                           os.path.join(os.path.expanduser("~"), ".claude"))


def _owners(path):
    """`path` lies under the owner's config folder, or under `~/.claude` when it moved."""
    return any(_below(path, f) for f in (_owner_folder(),
                                         os.path.join(os.path.expanduser("~"), ".claude")))


def _below(path, folder):
    """`path` is strictly below `folder`, by its spelling or by both real paths."""
    pairs = ((os.path.abspath(path), os.path.abspath(folder)),
             (os.path.realpath(path), os.path.realpath(folder)))
    return any(p.startswith(f.rstrip(os.sep) + os.sep) for p, f in pairs)


def _gate_line(target):
    """(list, line) for `target` by `list_gate`'s layers, or None for an exempt file."""
    home = os.path.expanduser("~").rstrip(os.sep)
    spelled = os.path.abspath(target)
    # d39 R7: the owner's folders are tested on the spelled path first, so the owner's file
    # that is a link into a checkout (a dotfiles one) stays the owner's; the spelled pair
    # alone (r1 F2), so a config folder that links into a checkout does not take a file
    # spelled inside that checkout.
    owners = (_owner_folder(), os.path.join(home, ".claude"))
    if any(spelled.startswith(os.path.abspath(f).rstrip(os.sep) + os.sep) for f in owners) \
            and not GATE_EXEMPT.intersection(spelled.split(os.sep)[:-1]):
        return os.path.join(_owner_folder(), GATES), (
            "~/" + spelled[len(home) + 1:] if spelled.startswith(home + os.sep) else spelled)
    real = os.path.realpath(target)
    top = _checkout_top(real)  # r1: a link into a checkout is that checkout's file
    target = real if top is not None else spelled
    top = top if top is not None else _checkout_top(target)
    folder = os.path.dirname(target)
    if top is not None:
        parts = os.path.relpath(target, top).split(os.sep)
        if GATE_EXEMPT.intersection(parts[:-1]):
            return None
        return os.path.join(top, ".claude", GATES), "/".join(parts)
    if GATE_EXEMPT.intersection(target.split(os.sep)[:-1]):
        return None
    if not _owners(target) and _below(folder, home):
        return os.path.join(folder, ".claude", GATES), os.path.basename(target)
    return os.path.join(_owner_folder(), GATES), (
        "~/" + target[len(home) + 1:] if target.startswith(home + os.sep) else target)


def _spelled(path):
    """`path` by its real path, the home folder written as the user spells it, then as
    `display` writes it."""
    real = os.path.realpath(path)
    spelled_home = os.path.expanduser("~").rstrip(os.sep)
    # a home of `/` spells as "", and realpath("") is the working folder: no rewrite then
    real_home = os.path.realpath(spelled_home).rstrip(os.sep) if spelled_home else ""
    if spelled_home and real_home and real.startswith(real_home + os.sep):
        real = spelled_home + real[len(real_home):]
    return display(real)


def list_gate(target, err=None, verb="render"):
    """g2b, d38: name `target` once in its layer's edit-gates list, so the session plugin's
    gate refuses an edit of it: a file in a checkout (found from its real path) in that
    checkout's `.claude/edit-gates`, relative to its top level; else a file under the owner's
    config folder (or `~/.claude`) in the owner's list, as `~/` under the home folder; else
    a file whose folder is below the home folder (a tree folder's) in that folder's
    `.claude/edit-gates`, by its name; else the owner's list, absolute. Never a file under a
    `tests`, `testdata` or `fixtures` folder. Never raises: a list it cannot write is one
    warning on `err` (r1 F2). Returns the list written, or None."""
    gates = None
    try:
        found = _gate_line(target)
        if found is None:
            return None
        gates, line = found
        old = read_text(gates) if os.path.exists(gates) else None
        if old is not None and line in (l.strip() for l in old.splitlines()):
            return None
        text = GATES_HEAD if old is None else (old if old.endswith("\n") or not old
                                               else old + "\n")
        os.makedirs(os.path.dirname(gates), exist_ok=True)
        write_text(gates, text + line + "\n")
        return gates
    except (OSError, ValueError, Refusal) as why:
        # n81: target and list are spelled one way, by real path under the home folder's real
        # path; a line that could not be made names the target once
        what = ("%s cannot be written" % _spelled(gates) if gates is not None
                else "its line cannot be resolved")
        (err or sys.stderr).write("%s: warning: %s is not listed: %s (%s)\n"
                                  % (verb, _spelled(target), what, why))
        return None


def gate_said(out, verb, listed):
    """dc1 R4: one line on `out` for each list in `listed`, (target, list) pairs as
    `list_gate` returned them, naming the files it now holds; None, a list not written,
    says nothing."""
    lists = []
    for target, gates in listed:
        if gates is None:
            continue
        found = next((names for g, names in lists if g == gates), None)
        if found is None:
            lists.append((gates, [_spelled(target)]))
        else:
            found.append(_spelled(target))
    for gates, names in lists:
        one = len(names) == 1
        out.write("%s: %s %s now on the edit-gates list %s: a session changes %s through "
                  "/decisions:instruct, never by its own edit; deleting %s line there lifts "
                  "the gate\n" % (verb, " and ".join(names), "is" if one else "are",
                                    _spelled(gates), "it" if one else "them",
                                    "its" if one else "a file's"))


def _list_lines(gates):
    """(number, line) of each non-comment line of the list `gates`; none when it is absent."""
    try:
        if os.path.isfile(gates):
            with open(gates, encoding="utf-8", errors="replace") as handle:  # n80
                text = handle.read()
        else:
            text = ""
    except OSError:
        return []
    return [(n, l.strip()) for n, l in enumerate(text.splitlines(), 1)
            if l.strip() and not l.strip().startswith("#")]


def _checkout_warning(gates, top, up, n, line, keep):
    first = os.path.join(up, line.split("/")[0])
    if line.startswith(("/", "~", "..")):  # n79: before a NUL line is skipped
        return ["%s:%d: `%s` reaches outside the checkout; %s"
                % (real_tilde(gates), n, line.replace("\0", "\\0"), keep)]
    if "\0" in line:  # no path call takes a NUL, and a line with none is not worth a warning
        return []
    # a U+FFFD is a byte the list could not decode (n80), so no folder was named by it
    if "\ufffd" not in line and line.split("/")[0] not in ("", ".") and first != top \
            and os.path.isdir(first) \
            and not os.path.lexists(os.path.join(top, line.split("/")[0])):
        return ["%s:%d: `%s` names %s, a folder beside the checkout; %s"
                % (real_tilde(gates), n, line, real_tilde(first), keep)]
    return []


def _lower_layer(line, home):
    """The checkout or the listed folder below the home folder that owns an owner's line."""
    full = home + line[1:] if line.startswith("~/") else line
    if not full.startswith("/") or _owners(full):
        return None
    layer, folder = _checkout_top(full), os.path.dirname(full)
    while layer is None and _below(folder, home):
        if os.path.isfile(os.path.join(folder, ".claude", GATES)):
            layer = folder
        folder = os.path.dirname(folder)
    return layer


def gate_warnings(path):
    """d38 R2, for `--lint`: a line of the ledger's checkout's list that is absolute, starts
    with `~` or `..`, or whose first segment names a folder beside the checkout; a `/` or
    `~/` line of the owner's list, outside its config folder, that lies in a checkout or
    under a folder below the home folder that holds its own list."""
    found, top = [], _checkout_top(os.path.abspath(path))
    keep = "a checkout's list holds its own files, relative to its top level"
    if top is not None:
        gates, up = os.path.join(top, ".claude", GATES), os.path.dirname(top)
        for n, line in _list_lines(gates):
            try:
                found.extend(_checkout_warning(gates, top, up, n, line, keep))
            except (OSError, ValueError):
                continue  # r1 F1: a path call that fails drops this line's check only
    home = os.path.expanduser("~").rstrip(os.sep)
    owner = os.path.join(_owner_folder(), GATES)
    for n, line in _list_lines(owner):
        if "\0" in line:
            continue
        try:
            layer = _lower_layer(line, home)
        except (OSError, ValueError):
            continue  # r1 F1
        if layer is not None:
            found.append("%s:%d: `%s` lies under %s, a layer with a list of its own; the "
                         "owner's list holds the user-scoped files" % (real_tilde(owner), n,
                                                                      line, real_tilde(layer)))
    return found


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
    begins, ends = markers(lines, BEGIN, END)
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
    # git's repository variables are dropped from each child (n43), so HEAD is the repository
    # that holds the file, whatever a hook or a caller exports
    env = {key: value for key, value in os.environ.items() if key not in REPO_VARIABLES}
    try:
        code, out = bounded(["git", "rev-parse", "--verify", "-q", "HEAD^{commit}"],
                            GIT_TIMEOUT, cwd=where, env=env)
        sha = out.strip()
        if code != 0 or not sha:
            return None
        blob = subprocess.run(["git", "cat-file", "blob", "%s:./%s" % (sha, name)],
                              cwd=where, env=env, capture_output=True, timeout=GIT_TIMEOUT)
        if blob.returncode != 0 or blob.stdout != data:
            return None
        code, out = bounded(["git", "rev-parse", "--short", sha], GIT_TIMEOUT, cwd=where,
                            env=env)
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
    # d36: the Every session entries in the ten titles' order; the tree's section is the
    # folder's file's, never this block's, so its entries and titles both stay out
    every = [e.text if tails else short_tail(e.text)
             for e in ordered([e for e in in_force if is_every(e)])]
    others = ["- %d %s (%s)" % (e.number, e.title, e.area) for e in in_force
              if not is_every(e) and not is_tree(e)]
    if every:
        pieces.append("\n".join(every))
    if others:
        pieces.append("The other entries in force, one line each; `%s` reads one." % show)
        pieces.append("\n".join(others))
    return "%s\n%s\n%s\n" % (BEGIN, "\n\n".join(pieces), END)


def apply(text, generated, target=TARGET):
    """`text` with `generated` between the markers, or appended when they are absent;
    marker lines inside a code fence are an example, never the block (dc1 r2 F4)."""
    lines = text.splitlines(keepends=True)
    begins, ends = markers(lines, BEGIN, END)
    if not begins and not ends:
        return generated if not text.strip() else text.rstrip("\n") + "\n\n" + generated
    if len(begins) != 1 or len(ends) != 1 or ends[0] < begins[0]:
        raise Refusal("%s: the GENERATED markers are not one BEGIN before one END" % target)
    return "".join(lines[:begins[0]]) + generated + "".join(lines[ends[0] + 1:])


def holds_markers(text):
    """True when `text` holds a BEGIN or an END line by `markers`; a fenced example is none
    (dc1 r2 F4). Markers that are not one block are `apply`'s to refuse."""
    begins, ends = markers(text.splitlines(), BEGIN, END)
    return bool(begins or ends)


def invited(target, path, named=None):
    """dc2 R2: (what `target` is, the act that gives it a block) for a target that holds no
    block. The CLAUDE.md beside the ledger at `path`, however it was named, takes its block
    from `init`, with `--ledger` when the run named one (`named`, quoted as `locate` does);
    any other file takes it once it holds the two marker lines."""
    state = "holds no generated block" if os.path.exists(target) else "is absent"
    here = os.path.realpath(os.path.dirname(os.path.abspath(target)))
    if os.path.basename(target) == TARGET and \
            here == os.path.realpath(os.path.dirname(os.path.abspath(path))):
        return state, "`agentik decisions init%s` adds it" % (
            " --ledger %s" % shlex.quote(named) if named else "")
    return state, ("a file takes the block once it holds the two marker lines, `%s` then "
                   "`%s`, each alone on a line" % (BEGIN, END))


def hand_said(out, verb, target, text):
    """dc3 R1, R2: what `text`, the file at `target` as its owner wrote it, loads, comments
    aside and imports included, and the skill that audits it; said only when the target is
    a CLAUDE.md (review 1, R1-F2) and the text, comments aside, holds a line that is not
    blank."""
    if os.path.basename(target) != TARGET or \
            not any(line.strip() for line in strip_comments(text).splitlines()):
        return
    out.write("%s: %s loads %s B of hand-written text on every turn of every session started "
              "here; /decisions:audit-claude-md goes through it with you and finds the lines "
              "no session acts on and the rules that belong in the ledger\n"
              % (verb, display(target), "{:,}".format(loaded_bytes(target, text))))


def one_block(text, target, verb):
    """The backstop (dc1 r3 F1): `text`, about to be written to `target`, must hold exactly
    one BEGIN and one END in order by `markers`, or `verb` refuses and writes nothing."""
    begins, ends = markers(text.splitlines(), BEGIN, END)
    if len(begins) != 1 or len(ends) != 1 or ends[0] < begins[0]:
        raise Refusal("%s: %s: its block could not be placed; nothing written; check for a "
                      "code fence left open above it, close it, and run `%s` again"
                      % (verb, target, verb))


def tree_file(ledger, path):
    """(the folder's file, its whole text) `render --scope tree` writes for the ledger at
    `path` (d36 ruling 2)."""
    return tree_text(ledger, path, short_tail, BEGIN, END)


def read_draft(draft):
    """dc3 review 1, R1-F1: the text of the draft at `draft`, or a Refusal in render's voice
    for one that is absent, a folder, unreadable, or holds markers that are not one block."""
    name = display(draft)
    if os.path.isdir(draft):
        raise Refusal("render: the draft %s is a folder; nothing written" % name)
    if not os.path.exists(draft):
        raise Refusal("render: the draft %s is absent; nothing written" % name)
    try:
        text = read_text(draft)
        apply(text, "", name)
    except Refusal as why:
        raise Refusal("render: the draft %s; nothing written" % why)
    return text


def measure(out, target, text, ledger, tree, draft=None):
    """Print the bytes `text`, the file at `target`, loads beside its ceiling (d36 ruling
    6); True when it is over. With `draft`, the line says `text` is the target as drafted
    there (dc3 review 1, R1-F1)."""
    figure, kind = ceiling_for(target, ledger, tree)
    size = loaded_bytes(target, text)
    said = ("as drafted in %s, %s would load" % (display(draft), display(target)) if draft
            else "%s loads" % display(target))
    out.write("render: %s %s B, comments aside and imports included; the ceiling for "
              "%s is %s B%s\n" % (said, "{:,}".format(size), kind,
                                  "{:,}".format(figure),
                                  "; over by {:,} B".format(size - figure)
                                  if size > figure else ""))
    return size > figure


def warn(err, lines):
    for line in lines:
        err.write("render: warning: %s\n" % line)


def refuse_another(text, target, path, verb="render"):
    """d36 ruling 4: refuse a target whose generated block names another ledger. A named
    path that holds no ledger now is this ledger before its repo moved, so the block is
    refreshed as at the pin (d36 r1 F1). `verb` names the act refused (`init`, dc1 r1 F1)."""
    named = named_ledger(text, target, BEGIN, END)
    if named is None or not os.path.isfile(named) or named == os.path.realpath(path) \
            or canonical(named) == canonical(path):
        return
    raise Refusal("%s: the block in %s was generated from %s, not from %s, and %s "
                  "never writes over another ledger's block; nothing written"
                  % (verb, display(target), real_tilde(named), real_tilde(path), verb))


def other_tree(folder):
    """A direct child of `folder` that is no checkout and holds a checkout, or None."""
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return None
    for name in names:
        child = os.path.join(folder, name)
        if not os.path.isdir(child) or os.path.exists(os.path.join(child, ".git")):
            continue
        try:
            inner = os.listdir(child)
        except OSError:
            continue
        if any(os.path.exists(os.path.join(child, n, ".git")) for n in inner):
            return child
    return None


def cmd_tree(args, ledger, path, out, err, ceiling):
    """`render --scope tree` (d36 ruling 2): the tree's section alone, the file whole."""
    # d36 r1 F2: an emptied section still has its file, with no entry in its block
    if not any(a.name.lower() == TREE_SESSION.lower() for a in ledger.areas):
        raise Refusal("render: %s holds no `### %s`, so it has no tree's file to write; "
                      "nothing written" % (display(path), TREE_SESSION))
    if getattr(args, "fold_tails", False):
        raise Refusal("render: --fold-tails rewrites the ledger and the repo's block; run it "
                      "without --scope tree")
    folder, text = tree_file(ledger, path)
    target = os.path.abspath(os.path.expanduser(args.into)) if args.into else folder
    if not args.into and not args.lint:
        other = other_tree(os.path.dirname(folder))
        if other is not None:
            # d36 r1 F3: a file here would load in every session of that other tree too
            raise Refusal("render: %s holds %s, a folder of checkouts that is another tree's, "
                          "so a CLAUDE.md in %s would load in every session of that tree too; "
                          "nothing written; --into FILE writes it elsewhere on purpose"
                          % (real_tilde(os.path.dirname(folder)), real_tilde(other),
                             real_tilde(os.path.dirname(folder))))
    if args.lint:
        warn(err, title_warnings(ledger))
        warn(err, gate_warnings(path))
        out.write("render: the block for %s is %d B; it is loaded on every turn\n"
                  % (display(target), block_bytes(text) or 0))
        return 1 if measure(out, target, text, ledger, True) and ceiling else 0
    if is_ledger(target, path):
        raise Refusal("render: the target %s is the ledger itself; nothing written"
                      % display(target))
    old = read_text(target) if os.path.exists(target) else None
    if old is not None:
        if not is_tree_file(old, BEGIN, END):
            raise Refusal("render: %s exists and is not a tree's file written by `%s`; a "
                          "hand-written file is never replaced; nothing written"
                          % (display(target), SCOPE_COMMAND))
        refuse_another(old, target, path)
        if named_ledger(old, target, BEGIN, END) is None:
            raise Refusal("render: %s names no ledger, so it is not %s's tree file; nothing "
                          "written" % (display(target), real_tilde(path)))
    if args.check:
        if old is None:
            out.write("render: %s is absent; `%s` writes it\n" % (display(target),
                                                                   SCOPE_COMMAND))
            measure(out, target, text, ledger, True)
            return 1
        stale = old != text
        if stale:
            name = display(target)
            out.writelines(difflib.unified_diff(old.splitlines(keepends=True),
                                                text.splitlines(keepends=True),
                                                name, name + " (rendered)"))
        over = measure(out, target, text, ledger, True)
        return 1 if stale or (over and ceiling) else 0
    if old == text:
        out.write("render: %s is fresh\n" % display(target))
        gate_said(out, "render", [(target, list_gate(target, err))])
        return 0
    was, crlf = disk_text(target), keeps_crlf(target)
    write_text(target, text)
    gates = list_gate(target, err)
    out.write("render: wrote %s: %s\n" % (display(target), growth(was, text, crlf)))
    gate_said(out, "render", [(target, gates)])
    return 0


def cmd_render(args, path, out, err):
    ledger, problems = lint(path)
    if problems:
        for name, line, message in problems:
            out.write("%s:%d: %s\n" % (name, line, message))
        return 1
    ceiling = getattr(args, "ceiling", False)
    if ceiling and not (args.check or args.lint):
        raise Refusal("render: --ceiling goes with --check or --lint; nothing written")
    draft = getattr(args, "draft", None)
    if draft is not None and not args.lint:
        raise Refusal("render: --draft goes with --lint; nothing written")
    if draft is not None and getattr(args, "scope", None) == "tree":
        raise Refusal("render: --draft measures the repo's block, not --scope tree; nothing "
                      "written")
    if getattr(args, "scope", None) == "tree":
        return cmd_tree(args, ledger, path, out, err, ceiling)
    target = os.path.abspath(os.path.expanduser(args.into)) if args.into else \
        os.path.join(os.path.dirname(path), TARGET)
    if args.lint:
        drafted = read_draft(os.path.abspath(os.path.expanduser(draft))) \
            if draft is not None else None
        warn(err, title_warnings(ledger))
        warn(err, gate_warnings(path))
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
        generated = block(ledger, path, target)
        out.write("render: the block for %s is %d B; it is loaded on every turn\n"
                  % (display(target), on_disk(generated, keeps_crlf(target))))
        # d36 ruling 5: a rule word in a hand-written line outside the block
        warn(err, ["%s:%d: a hand-written line holds %s; a rule lives in the ledger, and "
                   "render puts it in the block" % (display(target), n, ", ".join(
                       "`%s`" % w for w in words)) for n, words in rule_words(text, BEGIN, END)])
        over = measure(out, target, apply(text, generated, display(target)), ledger, False)
        if drafted is not None:
            # R1-F1: the draft in the target's place, its block and its folder's imports
            measure(out, target, apply(drafted, generated, display(draft)), ledger, False,
                    os.path.abspath(os.path.expanduser(draft)))
        return 1 if over and ceiling else 0
    if is_ledger(target, path):
        raise Refusal("render: the target %s is the ledger itself; nothing written"
                      % display(target))
    old = read_text(target) if os.path.exists(target) else ""
    away = os.path.dirname(os.path.realpath(target)) != \
        os.path.realpath(os.path.dirname(target))
    if args.into or away:
        # d36 r1 F1: the default target, beside the ledger, is never refused, as at the pin;
        # dc1 r2 F1: one that is a link to a file in another folder is not beside it
        refuse_another(old, target, path)
        if is_tree_file(old, BEGIN, END):
            # d36 r1 F4: the repo's block never takes the place of a tree's block
            raise Refusal("render: %s is a tree's file, written by `%s`; the repo's block "
                          "never replaces it; nothing written" % (display(target),
                                                                  SCOPE_COMMAND))
    if not holds_markers(old):
        # dc2 R1 to R3: render rewrites a block that is there and never adds one
        state, after = invited(target, path, getattr(args, "ledger", None))
        if args.check:
            out.write("render: %s %s; %s\n" % (display(target), state, after))
            measure(out, target, apply(old, block(ledger, path, target), display(target)),
                    ledger, False)
            return 1
        hand_said(out, "render", target, old)  # dc3 R2: before the refusal
        raise Refusal("render: %s %s, and render only rewrites a block that is there; "
                      "nothing written; %s" % (display(target), state, after))
    was = disk_text(target)
    if getattr(args, "fold_tails", False):
        apply(old, "", display(target))  # a target refused is refused before the fold
        cmd_fold(path, out, err)
        ledger = load(path)
    new = apply(old, block(ledger, path, target), display(target))
    if args.check:
        return check(old, new, ledger, path, target, out, err, ceiling)
    if new == old:
        out.write("render: %s is fresh\n" % display(target))
        gate_said(out, "render", [(target, list_gate(target, err))])
        return 0
    crlf = keeps_crlf(target)
    one_block(new, display(target), "render")
    write_text(target, new)
    gates = list_gate(target, err)
    out.write("render: wrote %s: %s\n" % (display(target), growth(was, new, crlf)))
    gate_said(out, "render", [(target, gates)])
    return 0


def check(old, new, ledger, path, target, out, err, ceiling):
    """`render --check`: the diff and exit 1 when stale; then the loaded bytes beside the
    ceiling, exit 1 over it under `--ceiling` (d36 ruling 6)."""
    code = 0
    if new != old:
        whole = block(ledger, path, target, tails=True)
        if apply(old, whole, display(target)) == old:
            more = len(whole.encode()) - len(block(ledger, path, target).encode())
            err.write("render: %s carries the entries' whole tails, %d B more; run render to "
                      "shorten it\n" % (os.path.basename(target), more))
        else:
            name = display(target)
            out.writelines(difflib.unified_diff(old.splitlines(keepends=True),
                                                new.splitlines(keepends=True),
                                                name, name + " (rendered)"))
            code = 1
    over = measure(out, target, new, ledger, False)
    return 1 if code or (over and ceiling) else 0
