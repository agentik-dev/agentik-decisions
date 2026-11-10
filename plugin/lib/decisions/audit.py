"""`audit`: the ledger's retire and rewrite candidates; it edits nothing (d33).

    audit [REPO...] [--tree FILE] [--json]

The marks are hq design/08 section 4's. P1, the ledger at its cap of 25 in force, in
the head line; P2, an entry amended three or more times; P3, a tail saying the entry
moved (`moved from` or `moved here`), its clause quoted; P4, a tail longer than its
paragraph, in bytes; P5, an entry nothing cites: no tracked text file of the tree but
the ledger, and no other entry's line; P6, a backticked path with a `/` that resolves
under none of the ledger's top, the tree's repos and the top's parent, or `decisions
VERB` for a verb this tool lacks; P8, two entries sharing most title words, printed
under `Leads, for a reader to confirm:` and never a mark. P7, a subject that is
process and not product (hq entry 7), is a reader's judgement: the tool names it as
not detected.

The tree is each REPO directory, plus the repos of `--tree FILE`, a file of the shape
`{"repos": [{"name": N, "path": P}]}` (a relative path, or a name without one,
resolves against the directory above the file's); with neither, the ledger's git top.
A repo absent or that git cannot read prints `not read: <name>`; with no repo read, no
entry is marked P5.

The Every session entries print first, then the other entries in force, each with
the bytes its line costs in the block `render` writes into the CLAUDE.md beside the
ledger, read from `render.block`'s output with its line end, CRLF when that file
keeps it. The text ends naming the owner's way to act: `new`, `ask` and `answer`.

It parses the ledger tolerantly, as `show` does, and runs only `git rev-parse` and
`git --no-optional-locks grep`, each bounded at `common.GIT_TIMEOUT`; it writes no
file and takes no lock. Exit 0 whenever the view printed; 2 for usage, an unreadable
ledger or tree file, or a REPO that is not a directory.
"""

import json
import os
import re
import subprocess

from . import common, render
from .common import Refusal, git_top, keeps_crlf, on_disk, read_text
from .ledger import (EVERY_SESSION, EVERY_SESSION_CAP, IN_FORCE, IN_FORCE_CAP, amended,
                     display, final_parenthetical, load)

__all__ = ["cmd_audit", "audit", "as_text", "tree_of", "MARKS", "OWNER"]

MARKS = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")
AMENDED_AT = 3
MOVED = re.compile(r"\bmoved (?:from|here)\b", re.IGNORECASE)
TICKED = re.compile(r"`([^`]+)`")
PLACEHOLDER = re.compile("[<>*{}$=\\s]|\\.\\.\\.|…")
# A first segment with a dot names a host (`example.com/x`), not a path.
HOST = re.compile(r"^[a-z0-9-]+\.[a-z0-9.-]+/", re.IGNORECASE)
VERB = re.compile(r"^(?:agentik\s+)?decisions\s+([a-z][a-z-]*)\b")
WORD = re.compile(r"[a-z0-9]+")
STOP = frozenset("a an the and or of to in on for by is are be its it one each every no not "
                 "with as at from this that what who which how where when s".split())
ERE_SPECIAL = re.compile(r"([.^$*+?()\[\]{}|\\])")
NOT_DETECTED = ("not detected: P7 (a subject that is process, not product; hq entry 7): "
                "a reader confirms it")
OWNER = ("audit edits nothing. The owner acts in one batch: `agentik decisions new` puts each "
         "retire or rewrite question, `ask` asks them, `answer` enters each: a rewrite is "
         "`answer N --amends M --shorter`, a retire moves the entry's line under "
         "`## Superseded`.")


def aliases_of(top):
    """The names a citation may give the ledger's repo: its directory's name and, for
    `X-hq`, `X` and `hq`."""
    name = os.path.basename(top.rstrip(os.sep))
    found = [name]
    if name.endswith("-hq") and len(name) > 3:
        found += [name[:-3], "hq"]
    return found


def cites_pattern(aliases):
    """`entry N`, `entries N, M and K`, `<alias> N`, `<alias> entry N`, any case."""
    names = "|".join(re.escape(a) for a in sorted(set(aliases), key=len, reverse=True))
    return re.compile(r"(?<![\w-])(?:entry|entries|%s)(?:\s+entry|\s+entries)?\s+"
                      r"(\d+(?:\s*(?:,|and|or|to|-)\s*\d+)*)" % names, re.IGNORECASE)


def cited_numbers(text, pattern):
    found = set()
    for match in pattern.finditer(text):
        found.update(int(n) for n in re.findall(r"\d+", match.group(1)))
    return found


def tree_of(args, ledger_path):
    """(repos to read, repos absent), from REPO..., `--tree FILE`, else the ledger's top."""
    names = list(getattr(args, "repos", None) or [])
    for name in names:
        if not os.path.isdir(name):
            raise Refusal("audit: %s is not a directory" % name)
    repos, missing = [os.path.realpath(n) for n in names], []
    tree = getattr(args, "tree", None)
    if tree is not None:
        if not os.path.isfile(tree):
            raise Refusal("audit: --tree %s is not a file" % tree)
        try:
            rows = json.loads(read_text(tree))["repos"]
            wanted = [os.path.expanduser(row.get("path") or row["name"]) for row in rows]
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise Refusal('audit: --tree %s is not {"repos": [{"name": N, "path": P}]}: %s'
                          % (tree, exc))
        root = os.path.dirname(os.path.dirname(os.path.realpath(tree)))
        for path in wanted:
            path = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path))
            if path not in repos and path not in missing:
                (repos if os.path.isdir(path) else missing).append(path)
    if not names and tree is None:
        here = os.path.dirname(os.path.realpath(ledger_path))
        repos = [os.path.realpath(git_top(here) or here)]
    return repos, missing


def grep_files(repo, ere, exclude):
    """The tracked text files of `repo` that `git grep -E` matches, `exclude` left out;
    None when git cannot read `repo` or timed out."""
    argv = ["git", "--no-optional-locks", "-c", "core.quotepath=off", "grep", "-I", "-i",
            "-l", "-z", "-E", "-e", ere, "--", "."] + [":(exclude)%s" % e for e in exclude]
    try:
        code, out = common.bounded(argv, common.GIT_TIMEOUT, cwd=repo)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if code not in (0, 1):
        return None
    return [os.path.join(repo, p) for p in out.split("\0") if p]


def citations(entries, real, top, repos):
    """(the numbers something cites, the repos git could not read): every other
    entry's line, then each tracked text file of `repos` but the ledger."""
    aliases = aliases_of(top)
    pattern = cites_pattern(aliases)
    cited = set()
    for entry in entries:
        cited |= cited_numbers(entry.text, pattern) - {entry.number}
    ere = "(entry|entries|%s)[[:space:]]+[0-9]" % "|".join(
        ERE_SPECIAL.sub(r"\\\1", a) for a in aliases)
    unread = []
    for repo in repos:
        inside = real.startswith(repo.rstrip(os.sep) + os.sep)
        files = grep_files(repo, ere, [os.path.relpath(real, repo)] if inside else [])
        if files is None:
            unread.append(repo)
            continue
        for name in files:
            try:
                cited |= cited_numbers(read_text(name), pattern)
            except Refusal:
                continue
    return cited, unread


def gone(entry, roots, verbs):
    """The backticked paths and decisions verbs of `entry` that resolve nowhere."""
    missing = []
    for token in TICKED.findall(entry.body):
        token = token.strip()
        verb = VERB.match(token)
        if verb:
            if verb.group(1) not in verbs:
                missing.append(token)
            continue
        if "/" not in token or PLACEHOLDER.search(token) or "://" in token \
                or token.startswith(("-", "#")) or HOST.match(token):
            continue
        clean = re.sub(r":\d.*$", "", token).rstrip("/") or "/"
        if clean.startswith("~"):
            places = [os.path.expanduser(clean)]
        elif os.path.isabs(clean):
            places = [clean]
        else:
            places = [os.path.join(r, clean) for r in roots]
        if not any(os.path.exists(p) for p in places):
            missing.append(token)
    return missing


def paragraph_and_tail(entry):
    """(the paragraph after the bold title, without its tail; the tail or "")."""
    body = entry.body.rstrip()
    tail = final_parenthetical(body)
    if tail is not None:
        body = body[:len(body) - len(tail) - 2]
    if body.startswith("**") and "** " in body:
        body = body.split("** ", 1)[1]
    return body.strip(), tail or ""


def block_lines(generated, crlf):
    """{(every session?, number): the bytes of its line in `generated`, line end included}."""
    found = {}
    for line in generated.split("\n"):
        every = re.match(r"^(\d+)\.\s", line)
        other = re.match(r"^- (\d+) ", line)
        if every or other:
            found[(bool(every), int((every or other).group(1)))] = on_disk(line + "\n", crlf)
    return found


def title_words(title):
    return {w for w in WORD.findall(title.lower()) if w not in STOP}


def audit(path, repos, missing, verbs):
    """The view `--json` prints (packet d33 section 3)."""
    ledger = load(path)
    in_force = [e for e in ledger.entries if e.section == IN_FORCE]
    every = {e.number for e in in_force if (e.area or "").lower() == EVERY_SESSION.lower()}
    real = os.path.realpath(path)
    top = os.path.realpath(git_top(os.path.dirname(real)) or os.path.dirname(real))
    target = os.path.join(os.path.dirname(path), render.TARGET)
    crlf = keeps_crlf(target)
    generated = render.block(ledger, path, target)
    costs = block_lines(generated, crlf)
    cited, unread = citations(in_force, real, top, repos)
    any_read = len(unread) < len(repos)
    roots = [top] + [r for r in repos if r != top] + [os.path.dirname(top)]
    candidates = []
    for entry in in_force:
        is_every = entry.number in every
        paragraph, tail = paragraph_and_tail(entry)
        marks = []
        count = amended(tail)
        if count >= AMENDED_AT:
            marks.append(("P2", "amended %d times" % count))
        moved = MOVED.search(tail)
        if moved:
            start = tail.rfind(";", 0, moved.start()) + 1
            marks.append(("P3", '"%s"' % tail[start:].split(";")[0].strip()))
        tail_b, body_b = len(tail.encode()), len(paragraph.encode())
        if tail_b > body_b:
            marks.append(("P4", "tail %d B, paragraph %d B" % (tail_b, body_b)))
        if any_read and entry.number not in cited:
            marks.append(("P5", "nothing in the tree cites it"))
        lost = gone(entry, roots, verbs)
        if lost:
            marks.append(("P6", "gone: " + ", ".join(lost)))
        if marks:
            candidates.append({"number": entry.number, "title": entry.title,
                               "area": entry.area, "every_session": is_every,
                               "bytes": costs.get((is_every, entry.number), 0),
                               "marks": [{"mark": m, "lead": False, "evidence": e}
                                         for m, e in marks]})
    candidates.sort(key=lambda c: not c["every_session"])
    leads = []
    words = [(e, title_words(e.title)) for e in in_force]
    for i, (a, wa) in enumerate(words):
        for b, wb in words[i + 1:]:
            shared = wa & wb
            if len(shared) >= 2 and 2 * len(shared) > min(len(wa), len(wb)):
                leads.append({"mark": "P8", "lead": True, "numbers": [a.number, b.number],
                              "titles": [a.title, b.title], "shared": sorted(shared)})
    return {"ledger": path, "in_force": len(in_force), "cap": IN_FORCE_CAP,
            "at_cap": len(in_force) >= IN_FORCE_CAP, "every_session": len(every),
            "every_session_cap": EVERY_SESSION_CAP,
            "block_bytes": render.block_bytes(generated, crlf) or 0,
            "candidates": candidates, "leads": leads, "not_detected": ["P7"],
            "tree": [r for r in repos if r not in unread], "not_read": missing + unread}


def as_text(v):
    lines = ["audit: %s: %d of %d in force%s, %d of %d under Every session; the block is "
             "%s B, loaded on every turn" % (
                 display(v["ledger"]), v["in_force"], v["cap"],
                 " (P1, at the cap)" if v["at_cap"] else "", v["every_session"],
                 v["every_session_cap"], "{:,}".format(v["block_bytes"]))]
    for title, every in (("Every session, paid every turn:", True),
                         ("Other entries in force:", False)):
        rows = [c for c in v["candidates"] if c["every_session"] == every]
        lines.append(title + ("" if rows else " none"))
        for c in rows:
            lines.append("%d %s  %d B  %s" % (c["number"], c["title"], c["bytes"], "; ".join(
                "%s %s" % (m["mark"], m["evidence"]) for m in c["marks"])))
    lines.append("Leads, for a reader to confirm:" + ("" if v["leads"] else " none"))
    for lead in v["leads"]:
        lines.append("P8 %d %s / %d %s: share %s" % (
            lead["numbers"][0], lead["titles"][0], lead["numbers"][1], lead["titles"][1],
            ", ".join(lead["shared"])))
    lines.append(NOT_DETECTED)
    lines.append("tree: %s" % (", ".join(os.path.basename(r) for r in v["tree"]) or "none"))
    if v["not_read"]:
        lines.append("not read: %s" % ", ".join(os.path.basename(r) for r in v["not_read"]))
    lines.append(OWNER)
    return "\n".join(lines) + "\n"


def cmd_audit(args, path, out, err):
    from .cli import VERBS
    repos, missing = tree_of(args, path)
    v = audit(path, repos, missing, set(VERBS))
    out.write(json.dumps(v, indent=2) + "\n" if getattr(args, "json", False) else as_text(v))
    return 0
