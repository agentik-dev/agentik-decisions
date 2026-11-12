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
A repo absent or that git cannot read prints `not read: <name>`, the tree row's name;
with no repo read, no entry is marked P5 and P5 is named not detected. P5's files are
those git grep finds holding the word `entry`, `entries` or an alias, so a citation
wrapped across a line counts; a file that is not UTF-8 is read with replacement; `N to
M` and `N-M` name every number from N to M.

Every Every session entry prints first, marked or not (d34; ` none` only when there
is none), then each entry of `Every session of the tree`, labelled as the tree's (d36),
then the other entries in force that carry a mark, each with the bytes its
line costs in the block `render` writes into the CLAUDE.md beside the ledger, read
from `render.block`'s output with its line end, CRLF when that file keeps it; a tree
entry's bytes are its line's in the folder's file `render --scope tree` writes.
`--json` lists the first as `every_session_entries`, `marks` `[]` when none, and keeps
`candidates`, the marked entries, as d33 had it. The text ends naming the owner's way to act: `new`, `ask` and `answer`.

It parses the ledger tolerantly, as `show` does, and runs only `git rev-parse` and
`git --no-optional-locks grep`, each bounded at `common.GIT_TIMEOUT`; it writes no
file and takes no lock. Exit 0 whenever the view printed; 2 for usage, an unreadable
ledger or tree file, or a REPO that is not a directory.

    audit --edits C [REPO] [--json]

d37 (hq design/09 section 7.2, "The list that sees the rest"): each commit after C to
HEAD, oldest first, that touches a guarded path and whose subject does not begin
`instruct:`, one line each: the short sha, the subject, the guarded paths. Guarded, at
the checkout's top level only: `CLAUDE.md`, `CLAUDE.local.md`, `.claude/CLAUDE.md`,
`AGENTS.md`, `.claude/rules/**`, `DECISIONS.md` and `.claude/settings*.json`; a path
with a `tests`, `testdata` or `fixtures` folder is never guarded. It reads REPO, else
the folder of `--ledger`, else the working directory, at its git top, and needs no
ledger. It is a list: exit 0 whether or not it lists anything; a commit name git
cannot resolve there, or one that opens with `-`, exits 2. A merge lists no paths of
its own, so a hand edit is seen in the commit that made it.
"""

import fnmatch
import json
import os
import re
import subprocess

from . import common, render
from .common import Refusal, git_top, keeps_crlf, on_disk, read_text
from .ledger import (IN_FORCE, IN_FORCE_CAP, amended, display, final_parenthetical, is_tree,
                     load)
from .ledger import is_every as in_every

__all__ = ["cmd_audit", "cmd_edits", "edits", "guarded", "audit", "as_text", "tree_of",
           "MARKS", "OWNER"]

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
SPAN_TOKEN = re.compile(r"\d+|\bto\b|-", re.IGNORECASE)
DATE = re.compile(r"\d{4}\s*-\s*\d{1,2}\s*-\s*\d{1,2}")
RANGE_MAX = 99
NOT_DETECTED_P5 = "not detected: P5 (an entry nothing cites): no repo of the tree was read"
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
    """The numbers `text` cites. `N to M` and `N-M` name every number from N to M when
    N < M <= N + RANGE_MAX; a date's `YYYY-MM-DD` names its parts only."""
    found = set()
    for match in pattern.finditer(text):
        group = match.group(1)
        spans = not DATE.search(group)
        last, ranged = None, False
        for token in SPAN_TOKEN.findall(group):
            if not token.isdigit():
                ranged = True
                continue
            n = int(token)
            if spans and ranged and last is not None and last < n <= last + RANGE_MAX:
                found.update(range(last, n + 1))
            else:
                found.add(n)
            last, ranged = n, False
    return found


def tree_of(args, ledger_path):
    """(repos to read, repos absent, {path: the name its `not read:` line prints}), from
    REPO..., `--tree FILE`, else the ledger's top. A tree row's name is its `name`."""
    names = list(getattr(args, "repos", None) or [])
    for name in names:
        if not os.path.isdir(name):
            raise Refusal("audit: %s is not a directory" % name)
    repos, missing = [os.path.realpath(n) for n in names], []
    shown = {r: os.path.basename(r) for r in repos}
    tree = getattr(args, "tree", None)
    if tree is not None:
        if not os.path.isfile(tree):
            raise Refusal("audit: --tree %s is not a file" % tree)
        try:
            rows = json.loads(read_text(tree))["repos"]
            wanted = [(os.path.expanduser(row.get("path") or row["name"]), str(row["name"]))
                      for row in rows]
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise Refusal('audit: --tree %s is not {"repos": [{"name": N, "path": P}]}: %s'
                          % (tree, exc))
        root = os.path.dirname(os.path.dirname(os.path.realpath(tree)))
        for path, name in wanted:
            path = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path))
            if path not in repos and path not in missing:
                (repos if os.path.isdir(path) else missing).append(path)
                shown[path] = name
    if not names and tree is None:
        here = os.path.dirname(os.path.realpath(ledger_path))
        repos = [os.path.realpath(git_top(here) or here)]
        shown = {repos[0]: os.path.basename(repos[0])}
    return repos, missing, shown


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
    # The word alone picks a file, so `entry` ending a line and its number on the next
    # still pick it; the Python pattern decides what is cited (d33 fold, F2).
    ere = "(entry|entries|%s)([[:space:]]|$)" % "|".join(
        ERE_SPECIAL.sub(r"\\\1", a) for a in aliases)
    unread = []
    for repo in repos:
        inside = real.startswith(repo.rstrip(os.sep) + os.sep)
        files = grep_files(repo, ere, [os.path.relpath(real, repo)] if inside else [])
        if files is None:
            unread.append(repo)
            continue
        for name in files:
            # A file that is not UTF-8 is read with replacement: its citations count (F1).
            try:
                with open(name, encoding="utf-8", errors="replace") as handle:
                    text = handle.read()
            except OSError:
                continue
            cited |= cited_numbers(text, pattern)
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
    every = {e.number for e in in_force if in_every(e)}
    tree = {e.number for e in in_force if is_tree(e)}
    real = os.path.realpath(path)
    top = os.path.realpath(git_top(os.path.dirname(real)) or os.path.dirname(real))
    target = os.path.join(os.path.dirname(path), render.TARGET)
    crlf = keeps_crlf(target)
    generated = render.block(ledger, path, target)
    costs = block_lines(generated, crlf)
    if tree:
        # d36: a tree entry costs its line in the folder's file, every turn of the tree
        tree_target, tree_text = render.tree_file(ledger, path)
        costs.update({(False, n): b for (is_line, n), b in
                      block_lines(tree_text, keeps_crlf(tree_target)).items()
                      if is_line and n in tree})
    cited, unread = citations(in_force, real, top, repos)
    any_read = len(unread) < len(repos)
    roots = [top] + [r for r in repos if r != top] + [os.path.dirname(top)]
    candidates, every_rows, tree_rows = [], [], []
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
        row = {"number": entry.number, "title": entry.title, "area": entry.area,
               "every_session": is_every, "tree": entry.number in tree,
               "bytes": costs.get((is_every, entry.number), 0),
               "marks": [{"mark": m, "lead": False, "evidence": e} for m, e in marks]}
        if is_every:
            # d34: every Every session entry prints with its bytes, marked or not.
            every_rows.append(row)
        if row["tree"]:
            # d36: so does every entry of the tree's section, labelled as the tree's
            tree_rows.append(row)
        if marks:
            candidates.append(row)
    candidates.sort(key=lambda c: (not c["every_session"], not c["tree"]))
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
            # d36: no count caps Every session; the key stays, as d34 kept every key
            "every_session_cap": None, "every_session_entries": every_rows,
            "tree_session": len(tree), "tree_session_entries": tree_rows,
            "block_bytes": render.block_bytes(generated, crlf) or 0,
            "candidates": candidates, "leads": leads,
            "not_detected": ["P7"] if any_read else ["P5", "P7"],
            "tree": [r for r in repos if r not in unread], "not_read": missing + unread}


def as_text(v, names=None):
    """The text view; `names` maps a repo's path to the name its row gives it."""
    def name(path):
        return (names or {}).get(path) or os.path.basename(path)
    lines = ["audit: %s: %d of %d in force%s, %d under Every session%s; the block is "
             "%s B, loaded on every turn" % (
                 display(v["ledger"]), v["in_force"], v["cap"],
                 " (P1, at the cap)" if v["at_cap"] else "", v["every_session"],
                 ", %d under Every session of the tree" % v["tree_session"]
                 if v.get("tree_session") else "", "{:,}".format(v["block_bytes"]))]
    groups = [("Every session, paid every turn:", "every")]
    if v.get("tree_session"):
        groups.append(("Every session of the tree, the tree's, paid every turn in each of "
                       "its repos:", "tree"))
    for title, group in groups + [("Other entries in force:", "other")]:
        rows = (v["every_session_entries"] if group == "every" else
                v["tree_session_entries"] if group == "tree" else
                [c for c in v["candidates"] if not c["every_session"] and not c["tree"]])
        lines.append(title + ("" if rows else " none"))
        for c in rows:
            lines.append("%d %s  %d B" % (c["number"], c["title"], c["bytes"]) + (
                "  " + "; ".join("%s %s" % (m["mark"], m["evidence"]) for m in c["marks"])
                if c["marks"] else ""))
    lines.append("Leads, for a reader to confirm:" + ("" if v["leads"] else " none"))
    for lead in v["leads"]:
        lines.append("P8 %d %s / %d %s: share %s" % (
            lead["numbers"][0], lead["titles"][0], lead["numbers"][1], lead["titles"][1],
            ", ".join(lead["shared"])))
    if "P5" in v["not_detected"]:
        lines.append(NOT_DETECTED_P5)
    lines.append(NOT_DETECTED)
    lines.append("tree: %s" % (", ".join(name(r) for r in v["tree"]) or "none"))
    if v["not_read"]:
        lines.append("not read: %s" % ", ".join(name(r) for r in v["not_read"]))
    lines.append(OWNER)
    return "\n".join(lines) + "\n"


GUARDED = ("CLAUDE.md", "CLAUDE.local.md", ".claude/CLAUDE.md", "AGENTS.md", "DECISIONS.md")
NEVER_GUARDED = ("tests", "testdata", "fixtures")
LANE = "instruct:"


def guarded(path):
    """True for a path, relative to the checkout's top, that holds instruction text (d37)."""
    parts = path.split("/")
    if any(part in NEVER_GUARDED for part in parts[:-1]):
        return False
    if path in GUARDED or path.startswith(".claude/rules/"):
        return True
    return len(parts) == 2 and parts[0] == ".claude" and fnmatch.fnmatchcase(
        parts[1], "settings*.json")


def edits(repo, commit):
    """(C's full sha, [{sha, short, subject, paths}]): each commit after `commit` to HEAD
    in `repo`, oldest first, that touches a guarded path, its subject not `instruct:`."""
    if not commit or commit.startswith("-"):
        raise Refusal("audit: --edits %r is no commit name" % commit)

    def run(argv):
        try:
            return common.bounded(["git", "--no-optional-locks", "-c", "core.quotepath=off"]
                                  + argv, common.GIT_TIMEOUT, cwd=repo)
        except subprocess.TimeoutExpired:
            raise Refusal("audit: git timed out after %d s in %s" % (common.GIT_TIMEOUT, repo))
        except OSError as exc:
            raise Refusal("audit: git cannot run in %s: %s" % (repo, exc))

    code, out = run(["rev-parse", "--verify", "--quiet", "%s^{commit}" % commit])
    sha = out.strip()
    if code != 0 or not sha:
        raise Refusal("audit: --edits %s names no commit in %s" % (commit, display(repo)))
    code, out = run(["log", "--reverse", "--no-renames", "-z", "--format=%x1e%H%x1f%h%x1f%s",
                     "--name-only", "%s..HEAD" % sha])
    if code != 0:
        raise Refusal("audit: git log cannot read %s..HEAD in %s" % (commit, display(repo)))
    rows = []
    for record in out.split("\x1e")[1:]:
        head, _, names = record.partition("\0")
        full, short, subject = (head.split("\x1f") + ["", ""])[:3]
        paths = [p for p in (n.strip("\n") for n in names.split("\0")) if p and guarded(p)]
        if paths and not subject.startswith(LANE):
            rows.append({"sha": full, "short": short, "subject": subject,
                         "paths": sorted(set(paths), key=paths.index)})
    return sha, rows


def cmd_edits(args, out, err):
    """`audit --edits C [REPO]` (d37): the list, exit 0."""
    names = list(getattr(args, "repos", None) or [])
    if len(names) > 1 or getattr(args, "tree", None) is not None:
        raise Refusal("audit: --edits reads one repo; name at most one REPO and no --tree")
    if names:
        if not os.path.isdir(names[0]):
            raise Refusal("audit: %s is not a directory" % names[0])
        where = names[0]
    elif getattr(args, "ledger", None):
        where = os.path.dirname(os.path.abspath(os.path.expanduser(args.ledger)))
    else:
        where = os.getcwd()
    repo = git_top(where) if os.path.isdir(where) else None
    if repo is None:
        raise Refusal("audit: --edits reads a git checkout, and %s is in none" % display(where))
    sha, rows = edits(repo, args.edits)
    if getattr(args, "json", False):
        out.write(json.dumps({"repo": repo, "after": sha, "edits": [
            {"sha": r["sha"], "subject": r["subject"], "paths": r["paths"]} for r in rows]},
            indent=2) + "\n")
        return 0
    if not rows:
        out.write("audit --edits: no commit after %s touches instruction text without an "
                  "`%s` subject\n" % (args.edits, LANE))
        return 0
    out.write("audit --edits: %d commit%s after %s touch instruction text without an `%s` "
              "subject; read each\n" % (len(rows), "" if len(rows) == 1 else "s", args.edits,
                                        LANE))
    for r in rows:
        out.write("%s %s  %s\n" % (r["short"], r["subject"], ", ".join(r["paths"])))
    return 0


def cmd_audit(args, path, out, err):
    from .cli import VERBS
    repos, missing, names = tree_of(args, path)
    v = audit(path, repos, missing, set(VERBS))
    out.write(json.dumps(v, indent=2) + "\n" if getattr(args, "json", False)
              else as_text(v, names))
    return 0
