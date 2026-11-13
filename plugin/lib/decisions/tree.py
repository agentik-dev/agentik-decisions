"""The tree's file and the loaded bytes of a CLAUDE.md (d36, hq design/09 sections 1, 3 to 5).

An hq's ledger holds `### Every session of the tree`. `render --scope tree` writes that
section alone into the CLAUDE.md of the folder that holds the ledger's repo: from a
worktree, the folder that holds the main checkout. The file is generated whole, a
comment, a title and the block; the tree's name is the folder's, the repo's name is the
main checkout's, and the ledger's path is written with `~` when it is under the home
folder. The text never depends on `--into`, so a file written there is the folder's
file byte for byte.

A CLAUDE.md's loaded bytes are counted as Claude Code loads it: each block-level HTML
comment outside a code fence goes, whole lines and all, and each `@path` import that
names a file, outside a code fence or span, adds that file's loaded bytes, to a depth of
four, each file once. The ceilings are in CEILINGS and nowhere else.
"""

import os
import re
import subprocess

from .common import GIT_TIMEOUT, bounded
from .ledger import TITLES, TREE_SESSION, is_every, is_tree, ordered

__all__ = ["CEILINGS", "ceiling_for", "loaded_bytes", "strip_comments", "checkout",
           "canonical", "folder_file", "tree_text", "named_ledger", "is_tree_file",
           "rule_words", "title_warnings", "SCOPE_COMMAND"]

# d36 ruling 6: the one place the figures live; no text a model loads repeats them.
CEILINGS = {"global": (6144, "the Mac's global file"),
            "tree": (1536, "a tree's file"),
            "hq": (4096, "an hq's file"),
            "repo": (3072, "a repo's file")}
IMPORT_DEPTH = 4
SCOPE_COMMAND = "agentik decisions render --scope tree"
FENCE = re.compile(r"^\s{0,3}(```+|~~~+)")
IMPORT = re.compile(r"(?:(?<=\s)|^)@((?:~/|\.{0,2}/)?[^\s`'\"()<>\[\]]+)")
CODE_SPAN = re.compile(r"`[^`]*`")
RULE_WORD = re.compile(r"\b(never|always|must|only)\b", re.IGNORECASE)
# The repo variables git honours: dropped, so the ledger's own repository answers.
REPO_VARIABLES = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
                  "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE")


def strip_comments(text):
    """`text` without its block-level HTML comments (hq design/09 F4): a line that opens
    with `<!--` outside a code fence goes with every line to the one that holds `-->`;
    text after the `-->` stays."""
    lines = text.splitlines(keepends=True)
    kept, fence, i = [], None, 0
    while i < len(lines):
        line = lines[i]
        opened = FENCE.match(line)
        if opened:
            mark = opened.group(1)[0]
            fence = None if fence == mark else (fence or mark)
        if fence is None and not opened and line.lstrip().startswith("<!--"):
            j, seen = i, line[line.find("<!--") + 4:]
            while "-->" not in seen and j < len(lines) - 1:
                j += 1
                seen = lines[j]
            rest = seen.split("-->", 1)[1] if "-->" in seen else ""
            if rest.strip():
                kept.append(rest)
            i = j + 1
            continue
        kept.append(line)
        i += 1
    return "".join(kept)


def imports(text):
    """The `@path` names of `text`, outside code fences and code spans, in order."""
    found, fence = [], None
    for line in text.splitlines():
        opened = FENCE.match(line)
        if opened:
            mark = opened.group(1)[0]
            fence = None if fence == mark else (fence or mark)
            continue
        if fence is None:
            found += IMPORT.findall(CODE_SPAN.sub(" ", line))
    return found


def loaded_bytes(path, text=None, seen=None, depth=0):
    """The bytes the file at `path` loads, `text` standing for its content when given:
    its own bytes, comments aside, and each import's that names a file (hq design/09 F3,
    F4). A file counts once; an import past depth four, or of no file, counts nothing."""
    seen = set() if seen is None else seen
    real = os.path.realpath(path)
    seen.add(real)
    if text is None:
        try:
            with open(real, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            return 0
    total = len(strip_comments(text).encode())
    if depth >= IMPORT_DEPTH:
        return total
    here = os.path.dirname(real)
    for name in imports(strip_comments(text)):
        name = name.rstrip(".,;:")
        place = os.path.expanduser(name) if name.startswith("~") else os.path.join(here, name)
        if os.path.isfile(place) and os.path.realpath(place) not in seen:
            total += loaded_bytes(place, None, seen, depth + 1)
    return total


def global_file(target):
    """True for a CLAUDE.md directly in the home folder's `.claude`."""
    home = os.path.join(os.path.expanduser("~"), ".claude")
    return (os.path.basename(target) == "CLAUDE.md"
            and os.path.realpath(os.path.dirname(os.path.abspath(target)))
            == os.path.realpath(home))


def ceiling_for(target, ledger, tree):
    """(figure, the file's kind) for `target`: the Mac's global file, a tree's file when
    `tree`, an hq's when `ledger` holds a tree section, else a repo's (d36 ruling 6)."""
    if tree:
        return CEILINGS["tree"]
    if global_file(target):
        return CEILINGS["global"]
    if any(a.name.lower() == TREE_SESSION.lower() for a in ledger.areas):
        return CEILINGS["hq"]
    return CEILINGS["repo"]


def git(argv, where):
    """git's stripped stdout in `where`, git's repo variables dropped; None on a failure."""
    env = {k: v for k, v in os.environ.items() if k not in REPO_VARIABLES}
    try:
        code, out = bounded(["git"] + argv, GIT_TIMEOUT, cwd=where, env=env)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.strip() if code == 0 and out.strip() else None


def checkout(path):
    """(the main checkout's real path, the ledger's path relative to its work tree) for
    the ledger at `path`; outside git, its directory. From a worktree, the main checkout
    is the one that holds the common git directory."""
    real = os.path.realpath(path)
    here = os.path.dirname(real)
    top = git(["rev-parse", "--show-toplevel"], here)
    if top is None:
        return here, os.path.basename(real)
    top = os.path.realpath(top)
    common = git(["rev-parse", "--path-format=absolute", "--git-common-dir"], here)
    main = top
    if common is not None and os.path.basename(common.rstrip(os.sep)) == ".git":
        main = os.path.realpath(os.path.dirname(common.rstrip(os.sep)))
    return main, os.path.relpath(real, top)


def canonical(path):
    """The real path of the ledger at `path` as the main checkout holds it."""
    main, rel = checkout(path)
    return os.path.join(main, rel)


def folder_file(path):
    """The CLAUDE.md of the folder that holds the main checkout of the ledger at `path`."""
    return os.path.join(os.path.dirname(checkout(path)[0]), "CLAUDE.md")


def tilde(path):
    """`path`, real, with the home folder written `~` when it is under it."""
    real, home = os.path.realpath(path), os.path.realpath(os.path.expanduser("~"))
    return "~" + real[len(home):] if real.startswith(home.rstrip(os.sep) + os.sep) else real


def tree_text(ledger, path, short_tail, begin, end):
    """(the folder's file, its whole text) for the ledger at `path`: hq design/09 section
    5.2's first example, each entry of the tree's section in the ten titles' order, its
    tail cut by `short_tail`."""
    main, rel = checkout(path)
    folder = os.path.dirname(main)
    target = os.path.join(folder, "CLAUDE.md")
    repo, tree = os.path.basename(main), os.path.basename(folder)
    source = "%s/%s" % (repo, rel.replace(os.sep, "/"))
    entries = [short_tail(e.text) for e in ordered([e for e in ledger.entries if is_tree(e)])]
    text = (
        "<!-- %s: loaded by every session started in a repo of this folder or in a worktree "
        "under one, and by their helpers.\n"
        "     This file is in no repo. It is generated whole from %s's ledger, and %s's "
        "`make check` fails when it is absent or stale.\n"
        "     Change it through /decisions:instruct. -->\n"
        "# The %s tree\n\n"
        "%s\n"
        "<!-- Generated from %s by `%s`; edit the ledger and rerun it, never this block. -->\n"
        "## Rules for every session in this tree\n\n"
        "Each is an entry of `%s`; `agentik decisions show N --ledger` with that path reads "
        "one.\n\n"
        "%s"
        "%s\n" % (tilde(target), repo, repo, tree, begin, source, SCOPE_COMMAND,
                  tilde(os.path.join(main, rel)),
                  "".join(e + "\n" for e in entries), end))
    return target, text


ENTRY_OF = re.compile(r"^Each is an entry of `([^`]+)`;")
SOURCE = re.compile(r"^(?:<!--\s*)?Generated from `([^`]+)` by `")


def markers(lines, begin, end):
    """(the BEGIN rows, the END rows) of `lines`, each a list of indexes; a marker line
    inside a code fence outside the block is an example, never a marker (dc1 r2 F4)."""
    begins, ends, fence, inside = [], [], None, False
    for i, line in enumerate(lines):
        if fence is None and line.strip() == begin:
            begins.append(i)
            inside = True
            continue
        if fence is None and line.strip() == end:
            ends.append(i)
            inside = False
            continue
        opened = None if inside else FENCE.match(line)
        if opened:
            mark = opened.group(1)[0]
            fence = None if fence == mark else (fence or mark)
    return begins, ends


def block_lines(text, begin, end):
    """The lines strictly between the one BEGIN and the one END of `text`, or None."""
    lines = text.splitlines()
    begins, ends = markers(lines, begin, end)
    if len(begins) != 1 or len(ends) != 1 or ends[0] < begins[0]:
        return None
    return lines[begins[0] + 1:ends[0]]


def is_tree_file(text, begin, end):
    """True when `text` holds one block written by `render --scope tree`."""
    inside = block_lines(text, begin, end)
    return inside is not None and any(SCOPE_COMMAND in line for line in inside[:1])


def named_ledger(text, target, begin, end):
    """The real path of the ledger the block in `text` names as its source, or None when
    it names none: a tree file's `Each is an entry of` path, else the `Generated from`
    path, resolved against the folder of the file `target` is, through any link, when it
    is relative (dc1 r2 F1: a link's own folder may hold another ledger, or none)."""
    inside = block_lines(text, begin, end)
    if not inside:
        return None
    for line in inside:
        found = ENTRY_OF.match(line.strip()) if is_tree_file(text, begin, end) else \
            SOURCE.match(line.strip())
        if found:
            name = os.path.expanduser(found.group(1))
            if not os.path.isabs(name):
                name = os.path.join(os.path.dirname(os.path.realpath(target)), name)
            return os.path.realpath(name)
    return None


def outside_lines(text, begin, end):
    """(1-based number, line) of each line of `text` outside the block, an HTML comment
    and a code fence."""
    lines = text.splitlines()
    inside = False
    fence, comment = None, False
    found = []
    for n, line in enumerate(lines, 1):
        if fence is None and not comment and line.strip() == begin:
            inside = True
            continue
        if fence is None and not comment and line.strip() == end:
            inside = False
            continue
        if inside:
            continue
        opened = FENCE.match(line)
        if opened and not comment:
            mark = opened.group(1)[0]
            fence = None if fence == mark else (fence or mark)
            continue
        if fence is not None:
            continue
        visible = ""
        rest = line
        while rest:
            if comment:
                close = rest.find("-->")
                if close < 0:
                    rest = ""
                    break
                rest, comment = rest[close + 3:], False
                continue
            start = rest.find("<!--")
            if start < 0:
                visible += rest
                break
            visible += rest[:start]
            rest, comment = rest[start + 4:], True
        if visible.strip():
            found.append((n, visible))
    return found


def rule_words(text, begin, end):
    """(line number, [words]) for each hand-written line of `text`, outside its block, an
    HTML comment and a code fence, that holds `never`, `always`, `must` or `only` whole."""
    found = []
    for n, line in outside_lines(text, begin, end):
        words = [w.lower() for w in RULE_WORD.findall(line)]
        if words:
            found.append((n, sorted(set(words), key=words.index)))
    return found


def title_warnings(ledger):
    """One line for each entry under `Every session` or the tree's section whose title is
    none of the ten (d36 ruling 5)."""
    known = {t.lower() for t in TITLES}
    lines = []
    for entry in ledger.entries:
        if (is_every(entry) or is_tree(entry)) and \
                " ".join(entry.title.split()).lower() not in known:
            lines.append("entry %d under `%s` is titled `%s`, none of the ten titles; it "
                         "keeps its place after them" % (entry.number, entry.area, entry.title))
    if lines:
        lines.append("the ten titles, in their order: %s" % ", ".join(TITLES))
    return lines
