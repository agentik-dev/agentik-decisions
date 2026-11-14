"""`rows` (agentik-hq design/16 section 4 items 5 to 7, packets rw2 and rw2b): each build
row's stage, read from its record folder and from git; `rows check` holds every row's records
against git; `rows close` writes a pushed row's `done` cell and its done line.

    decisions rows [check] [--json] [--root DIR] [REPO...]
    decisions rows close ROW [--withdrawn WHY] [--root DIR] [--repo DIR] [--dry-run] [-y]

DIR holds one folder a row, a folder holding `row.md`; the default is `history/rows` under
the working directory's git top, and DIR's git top is the home. A row's repo cell names the
home (`hq` or its short name), a REPO named by its short name, or, with none named, the
folder beside the home called `agentik-<cell>` or `<cell>`. The read and `check` write
nothing and fetch nothing: git is read through `backlog.Git`, `status` with
`--no-optional-locks`. `close` writes row.md and the home's done file, both or neither, and
runs no `git add` and no commit. Exit 0 with the rows shown, contradictions included; `rows
check` exits 1 when a row is stale; 2 for usage or no DIR, with `--json` an error object on
stdout, and for a close refused, declined or that cannot ask.
"""

import json
import os
import posixpath
import re
import shlex
import sys

from . import ask as ask_module
from .backlog import (CELL_LEVEL, DATE_WORD, DONE_FILE, HANDOFF, HEADING, HOME_CELL, LEVEL,
                      NICE, ROW_CELL, SHA_WORD, Git, build_order, building_red, done_red,
                      gathered, most_urgent, nice_items, short_name)
from .common import Refusal, commit_texts, git_top, held, read_text
from .speak import CONTROL, ESCAPE

__all__ = ["cmd_rows", "table", "asked", "KEYS", "SCHEMA"]

SCHEMA = "agentik.rows/1"
ROOT = os.path.join("history", "rows")
ROW, BRIEF, MERGE = "row.md", "brief.md", "merge.txt"
BUILD = re.compile(r"^build-([0-9]+)\.md$")
REVIEW = re.compile(r"^review-([0-9]+)\.md$")
GATE_EXIT = re.compile(r"^(\S+) exit (-?[0-9]+)\b")
GATE_RUNNING = re.compile(r"^(\S+) running\b")
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
FROM_HANDOFF = re.compile(r"^HANDOFF ([0-9]+)\b")
FROM_NICE = re.compile(r"^(\S+) (n[0-9]+(?:, ?n[0-9]+)*)\b")
PHASE_2 = "phase 2"
# Review 1 F4: R3's four stages, read by a cell's opening words.
STAGE = re.compile(r"^(first build|fix of review [0-9]+|phase 2|cut)(?![\w-])")
GATE_STATUS = "agentik session gate status"
UNREADABLE = "unreadable"
# R6: a row's keys, in this order; rw2b R8 adds `cut`.
KEYS = ("row", "repo", "level", "from", "depends_on", "waits", "state", "stale", "branch",
        "worktree", "tip", "dirty", "past", "record", "head", "gate", "ruling", "owed", "next",
        "cut")
# rw2b R8: a charter's name, `<date>-<n>.md` or `<date>-<n>-<chain>.md`, under SITTINGS.
CHARTER = re.compile(r"^([0-9]{4}-[0-9]{2}-[0-9]{2})-([0-9]+)(?:-[A-Za-z0-9][A-Za-z0-9._-]*)?"
                     r"\.md$")
SITTINGS = "history/sittings/"
SHOWN, LISTED, ACT_CAP = 3, 50, 100
# rw2b R1 and R7: the close's options, its question and its answers.
CLOSE_FLAGS = ("withdrawn", "repo", "dry_run", "yes")
QUESTION = "Write this? y for yes, n or Enter for no. "
YES = ("y", "yes")
CLOSED_CAP = 80
# Review 1 F1: the re-read and the write hold this lock in DIR, CLOSE_WAIT seconds at most.
CLOSE_LOCK, CLOSE_WAIT = ".rows-close.lock", 5.0
# Review 1 F2: what a WHY may not hold: the C0 and C1 controls and DEL (every
# `str.splitlines` break but two: LF, CR, VT, FF, FS, GS, RS, NEL), U+2028 and U+2029, and
# the zero-width and direction characters U+061C, U+180E, U+200B to U+200F, U+202A to U+202E,
# U+2060 to U+2064, U+2066 to U+206F and U+FEFF.
WHY_BAD = re.compile("[\x00-\x1f\x7f-\x9f\u061c\u180e\u200b-\u200f\u2028-\u202e"
                     "\u2060-\u2064\u2066-\u206f\ufeff]")


class RowsRefusal(Refusal):
    """A refusal with R6's code and remedy, for the `--json` error object."""

    def __init__(self, code, message, remedy):
        Refusal.__init__(self, message)
        self.code, self.remedy = code, remedy


def bare(cell):
    """R3: a cell less its backticks, stripped."""
    return cell.replace("`", "").strip()


def table_rows(lines):
    """(index, cells) of each body row of the first `| item | value |` table in `lines`,
    each cell less its backticks; rw2b R5 finds the `done` row by it."""
    inside = False
    for index, line in enumerate(lines):
        s = line.strip()
        if not s.startswith("|"):
            if inside:
                return
            continue
        body = s[1:-1] if s.endswith("|") and not s.endswith("\\|") else s[1:]
        cells = [bare(c) for c in ROW_CELL.split(body)]
        if not inside:
            inside = [c.lower() for c in cells[:2]] == ["item", "value"]
            continue
        if all(re.match(r"^:?-+:?$", c) for c in cells):
            continue
        yield index, cells


def table(text):
    """R3: {item: value} of the first `| item | value |` table, each value less its backticks."""
    found = {}
    for _index, cells in table_rows(text.splitlines()):
        # review 1 F5: the value is the second cell, whatever columns follow
        found.setdefault(cells[0].lower(), cells[1] if len(cells) > 1 else "")
    return found


def first(value):
    """The opening word of a cell, less one trailing `,`, `.`, `;` or `:`."""
    words = value.split()
    return words[0].rstrip(",.;:") if words else ""


def sha_of(value):
    word = first(value)
    return word if SHA_WORD.match(word) else None


def stage_of(value):
    """Review 1 F4: the stage by its opening words, else the cell as written."""
    m = STAGE.match(value)
    return m.group(1) if m else value


def gate_of(value):
    """R6: {id, exit} of `<id> exit <code>`, exit null for `<id> running`, else None."""
    m = GATE_EXIT.match(value)
    if m:
        return {"id": m.group(1), "exit": int(m.group(2))}
    m = GATE_RUNNING.match(value)
    if m and not value.startswith("none:"):
        return {"id": m.group(1), "exit": None}
    return None


def ruling_of(value):
    """The ruling's word: None when empty, else its opening word (`closed`, `fix`, ...)."""
    return first(value).lower() or None


def done_of(value):
    """R3: open, withdrawn, or closed with the date and sha when they are its first two words."""
    words = value.split()
    if not words:
        return {"state": "open", "date": None, "sha": None}
    if words[0].lower().rstrip(",.;:") == "withdrawn":
        return {"state": "withdrawn", "date": None, "sha": None}
    date = words[0] if DATE_WORD.match(words[0]) else None
    sha = first(words[1]) if date and len(words) > 1 else None
    return {"state": "closed", "date": date, "sha": sha if sha and SHA_WORD.match(sha) else None}


def names_of(value):
    """`depends_on`'s row names; `none` is none. Prose after `(` or `;` is no name."""
    head = re.split(r"[(;]", value, 1)[0]
    words = [w.rstrip(".") for w in re.split(r"[,\s]+", head)]
    return [w for w in words if w and w.lower() not in ("none", "and") and NAME.match(w)]


def owed_of(text):
    """R3: each `- [ ]` under `## Owed` is one owed."""
    count, inside = 0, False
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            inside = len(m.group(1)) == 2 and m.group(2).strip() == "Owed"
            continue
        if inside and line.startswith("- [ ]"):
            count += 1
    return count


def records(folder):
    """The row's records: row.md's cells, its builds and reviews by number, merge.txt."""
    text = read_text(os.path.join(folder, ROW))
    cells = table(text)
    builds, reviews = [], []
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        build, review = BUILD.match(name), REVIEW.match(name)
        if build and os.path.isfile(path):
            t = table(read_text(path))
            builds.append({"n": int(build.group(1)), "file": name, "stage": stage_of(t.get("stage", "")),
                           "head": sha_of(t.get("head", "")), "gate": gate_of(t.get("gate", ""))})
        elif review and os.path.isfile(path):
            t = table(read_text(path))
            span = first(t.get("slice", "")).split("..")
            ends = [e if SHA_WORD.match(e) else None for e in span] if len(span) == 2 else [None] * 2
            reviews.append({"n": int(review.group(1)), "file": name, "base": ends[0],
                            "end": ends[1], "blocks": t.get("blocks", ""),
                            "ruling": ruling_of(t.get("ruling", ""))})
    builds.sort(key=lambda b: b["n"])
    reviews.sort(key=lambda r: r["n"])
    return {"cells": cells, "builds": builds, "reviews": reviews, "owed": owed_of(text),
            "merge": os.path.isfile(os.path.join(folder, MERGE)),
            "done": done_of(cells.get("done", "")), "depends_on": names_of(cells.get("depends_on", ""))}


class Repos(object):
    """R4: a repo cell's checkout, or why its rows are skipped; one `Git` a checkout."""

    def __init__(self, home, named):
        self.home, self.gits = home, {}
        self.named = None
        if named:
            self.named = {}
            for repo in named:
                real = os.path.realpath(repo)
                self.named.setdefault(short_name(real), real)

    def where(self, cell):
        cell = first(cell)
        if cell in (HOME_CELL, short_name(self.home)):
            path = self.home
        elif not cell:
            return None, "absent"
        elif self.named is not None:
            path = self.named.get(cell)
            if path is None:
                return None, "not named"
        else:
            parent = os.path.dirname(self.home)
            path = next((p for p in (os.path.join(parent, "agentik-" + cell),
                                     os.path.join(parent, cell)) if os.path.isdir(p)), None)
            if path is None:
                return None, "absent"
        if not os.path.isdir(path):
            return None, "absent"
        top = git_top(path)
        if not top or os.path.realpath(top) != os.path.realpath(path):
            return None, "no checkout"
        git = self.git(path)
        if git.tip("main") is None:
            return None, "no main"
        return path, None

    def git(self, path):
        if path not in self.gits:
            self.gits[path] = Git(path)
        return self.gits[path]


def ancestor(git, sha, ref):
    """True when the commit `sha` names is `ref` or an ancestor of it."""
    full = git.commit(sha) if sha else None
    return bool(full and ref and git.run("merge-base", "--is-ancestor", full, ref) is not None)


def worktree_of(git, branch):
    """The path of the worktree that has `branch` checked out, or None."""
    path = None
    for line in (git.run("worktree", "list", "--porcelain") or "").splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line == "branch refs/heads/" + branch:
            return path
    return None


def dirty_of(path):
    """The worktree's changed and untracked paths, read without the index lock."""
    out = Git(path).run("--no-optional-locks", "status", "--porcelain")
    return None if out is None else len([l for l in out.splitlines() if l.strip()])


def paths_of(path):
    """rw2b R8: the paths `dirty_of` counts, as git prints them, LISTED at most; porcelain v2,
    whose lines open with no space for `Git.run`'s strip to take."""
    out = Git(path).run("--no-optional-locks", "status", "--porcelain=v2")
    if out is None:
        return None
    found = []
    for line in out.splitlines():
        kind = line[:2]
        if kind == "1 ":
            parts = line.split(" ", 8)
        elif kind == "2 ":
            parts = line.split(" ", 9)
            parts[-1] = parts[-1].split("\t", 1)[0]
        elif kind == "u ":
            parts = line.split(" ", 10)
        elif kind in ("? ", "! "):
            parts = [line[2:]]
        else:
            continue
        found.append(parts[-1])
    return found[:LISTED]


def section_of(text, title):
    """rw2b R8: the lines under the `## <title>` heading up to the next heading, or None."""
    lines, inside, found = [], False, False
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            inside = len(m.group(1)) == 2 and m.group(2).strip() == title
            found = found or inside
            continue
        if inside:
            lines.append(line)
    return lines if found else None


def charter_of(git, base, tip):
    """rw2b R8: the newest charter the branch added or changed since `base`, by date and then
    by its number, or None."""
    if not base or not tip:
        return None
    out = git.run("diff", "--name-only", "--diff-filter=AM", base, tip, "--", SITTINGS)
    best = None
    for path in (out or "").splitlines():
        # review 1 F7: a charter lies directly in SITTINGS, never in a folder under it
        if posixpath.dirname(path) != SITTINGS.rstrip("/"):
            continue
        m = CHARTER.match(posixpath.basename(path))
        if m:
            key = (m.group(1), int(m.group(2)), path)
            best = key if best is None or key > best else best
    return best[2] if best else None


def cut_of(row, git, since):
    """rw2b R8: what a cut builder left: the charter on the tip, the commits past `since`,
    the worktree's loose paths."""
    tip = row["tip"]
    charter = charter_of(git, row["base"], tip)
    unchecked = next_act = None
    row["unchecked_count"] = 0
    if charter:
        text = git.run("show", "%s:%s" % (tip, charter)) or ""
        unchecked = [l.rstrip() for l in section_of(text, "Done-ness") or []
                     if l.startswith("- [ ]")]
        # review 1 F6: LISTED at most, as commits and paths; the text keeps the count
        row["unchecked_count"] = len(unchecked)
        unchecked = unchecked[:LISTED]
        act = next((l.strip() for l in section_of(text, "Next act") or [] if l.strip()), None)
        next_act = act[:ACT_CAP] if act else None
    commits = []
    out = git.run("log", "--format=%H%x1f%s", "-n", str(LISTED), "%s..%s" % (since, tip)) \
        if since and tip else None
    for line in (out or "").splitlines():
        sha, _, subject = line.partition("\x1f")
        commits.append({"sha": sha, "subject": subject})
    return {"charter": charter, "unchecked": unchecked, "next_act": next_act,
            "commits": commits,
            "paths": paths_of(row["worktree"]) if row["worktree"] else None}


def is_cut(row):
    """rw2b R8: `building`, or `to fix` with commits past its record."""
    return row["state"] == "building" or (row["state"] == "to fix" and (row["past"] or 0) > 0)


def cut_lines(row):
    """rw2b R8: the text's lines of a cut row, SHOWN of each and a count."""
    cut = row["cut"]
    if cut["charter"]:
        lines = ["  charter %s: %d unchecked; next act: %s"
                 % (cut["charter"], max(row.get("unchecked_count") or 0, len(cut["unchecked"])),
                    cut["next_act"] or "none")]
    else:
        lines = ["  charter: none on %s" % row["branch"]]
    shown_commits = cut["commits"][:SHOWN]
    lines.extend("  past: %s %s" % (c["sha"][:7], c["subject"]) for c in shown_commits)
    more = max(row["past"] or 0, len(cut["commits"])) - len(shown_commits)
    if more > 0:
        lines.append("  past: and %d more" % more)
    paths = cut["paths"] or []
    if paths:
        line = "  dirty: " + ", ".join(paths[:SHOWN])
        more = max(row["dirty"] or 0, len(paths)) - len(paths[:SHOWN])
        lines.append(line + (" and %d more" % more if more > 0 else ""))
    return lines


def facts(row, git):
    """Pass 1: the git facts of an open row: tip, merge base, landing, pushed."""
    branch = row["branch"]
    tip = git.tip(branch)
    _red, landing, date = building_red(git, branch)
    second = None
    if landing:
        second = next((p[1] for s, p, _, _ in git.line() if s == landing and len(p) > 1), None)
    main = git.tip("main")
    base = git.run("merge-base", main, tip) if tip else None
    pushed = bool(landing) and git.run("merge-base", "--is-ancestor", landing,
                                       "refs/remotes/origin/main") is not None
    row.update(tip=tip, main=main, base=base, landing=landing, landed_on=date,
               second=second, pushed=pushed)


def covers(git, review, build):
    """R5: a review covers a build whose head is its slice's end or an ancestor of it."""
    end = git.commit(review["end"]) if review["end"] else None
    return bool(build["head"] and end and ancestor(git, build["head"], end))


def judged(row, git, build):
    """R5's table from `ruling` down, on `build`: (word, text, command, record file)."""
    reviews = row["rec"]["reviews"]
    review = next((r for r in reversed(reviews) if covers(git, r, build)), None)
    if review is None:
        last = reviews[-1]["end"] if reviews and reviews[-1]["end"] else row["base"]
        span = "%s..%s" % ((last or "?")[:7], (build["head"] or "?")[:7])
        return "built", "review %d: %s" % (len(reviews) + 1, span), None, build["file"]
    path = os.path.join(row["folder"], review["file"])
    if review["ruling"] == "fix":
        return "to fix", "%s: %s" % (row["branch"], review["blocks"] or "none"), None, \
            review["file"]
    if review["ruling"] != "closed":
        return "to rule", path, None, review["file"]
    merge = os.path.join(row["folder"], MERGE)
    current = row["base"] is not None and row["base"] == row["main"]
    if current and row["rec"]["merge"]:
        # review 1 F2: each part quoted for a POSIX shell, so a pasted line is four words
        command = "agentik session gate land " + " ".join(
            shlex.quote(part) for part in (row["path"], row["branch"], row["tip"], merge))
        return "ready", None, command, MERGE
    if row["tip"] and not current:
        return "reviewed", "phase 2: merge main into %s" % row["branch"], None, review["file"]
    return "reviewed", merge, None, review["file"]


def word(row, git):
    """R5: (word, text, command, record) for an open row, its `waits` already read."""
    rec = row["rec"]
    builds = rec["builds"]
    if row["landing"]:
        record = builds[-1]["file"] if builds else ROW
        if row["pushed"]:
            owed = rec["owed"]
            text = ("%d owed" % owed if owed else
                    "type done: %s %s" % (row["landed_on"], row["landing"][:7]))
            return "pushed", text, None, record
        return "landed", "push %s's main" % short_name(row["path"]), None, record
    if row["tip"] is None and not builds:
        if row["waits"]:
            return "waits", ", ".join(row["waits"]), None, ROW
        return "briefed", os.path.join(row["folder"], BRIEF), None, ROW
    if not builds:
        return "building", None, GATE_STATUS, ROW
    got = judged(row, git, builds[-1])
    if got[0] == "built" and builds[-1]["stage"] == PHASE_2:
        other = next((b for b in reversed(builds) if b["stage"] != PHASE_2), None)
        again = judged(row, git, other) if other else None
        if again and again[0] in ("reviewed", "ready"):
            return again
    return got


def level_red(row, repos):
    """R7: `level <L> differs from <from>'s <M>`, or None when the source holds no level."""
    source, level = row["rec"]["cells"].get("from", ""), first(row["level"])
    m = FROM_HANDOFF.match(source)
    found = None
    if m:
        path = os.path.join(repos.home, HANDOFF)
        if not os.path.isfile(path):
            return None
        text = read_text(path)
        step = next((s for s in build_order(text)[1] if s["n"] == int(m.group(1))), None)
        if step is None:
            return None
        for n, kind, payload, joined in gathered(text):
            if n == step["line"]:
                cells = payload if kind == "row" else []
                found = most_urgent([c.group(1) for c in map(CELL_LEVEL.match, cells) if c]
                                    or LEVEL.findall(joined or ""))
                break
    else:
        m = FROM_NICE.match(source)
        if not m:
            return None
        where, _why = repos.where(m.group(1))
        path = os.path.join(where, NICE) if where else None
        if not path or not os.path.isfile(path):
            return None
        ids = set(i.strip() for i in m.group(2).split(","))
        found = most_urgent([i["level"][1:] for i in nice_items(read_text(path))
                             if i.get("id") in ids and i["level"]])
    if found is None or found == level:
        return None
    return "level %s differs from %s's %s" % (level, m.group(0), found)


def stale_of(row, git, repos):
    """R7's contradictions of an open row, in order."""
    out, rec, branch = [], row["rec"], row["branch"]
    if row["tip"] is None and not row["landing"]:
        if rec["builds"]:
            out.append("branch %s is gone and no merge names it" % branch)
    else:
        ref = row["tip"] or row["second"]
        for b in rec["builds"]:
            if b["head"] and not ancestor(git, b["head"], ref):
                out.append("head %s of %s is not on %s" % (b["head"], b["file"], branch))
        for r in rec["reviews"]:
            if r["end"] and not ancestor(git, r["end"], ref):
                out.append("slice end %s of %s is not on %s" % (r["end"], r["file"], branch))
    red = level_red(row, repos)
    if red:
        out.append(red)
    return out


def row_of(name, folder, rec):
    """A row as the read holds it, before its repo and git are read."""
    cells = rec["cells"]
    return {"row": name, "folder": folder, "rec": rec, "repo": cells.get("repo", ""),
            "level": cells.get("level", ""), "branch": first(cells.get("branch", "")) or name}


def gathered_rows(root, repos, closed):
    """(open rows, closed rows, skipped) of the folders under `root`; withdrawn ones are none."""
    opened, shut, skipped = [], [], []
    for name in sorted(os.listdir(root)):
        folder = os.path.join(root, name)
        if not os.path.isfile(os.path.join(folder, ROW)):
            continue
        try:
            rec = records(folder)
        except (Refusal, OSError):
            # review 1 L1: a record that is not text skips its row; the read goes on
            skipped.append((None, UNREADABLE, name))
            continue
        if rec["done"]["state"] == "withdrawn":
            continue
        row = row_of(name, folder, rec)
        is_open = rec["done"]["state"] == "open"
        if not is_open and not closed:
            row["path"] = None
            shut.append(row)
            continue
        path, why = repos.where(row["repo"])
        row["path"] = path
        if path is None:
            skipped.append((first(row["repo"]), why, name))
            if not is_open:
                shut.append(row)
            continue
        (opened if is_open else shut).append(row)
    return opened, shut, skipped


def shown(row):
    """R6's object of an open row."""
    command = row["next"][1]
    return {"row": row["row"], "repo": row["repo"], "level": row["level"],
            "from": row["rec"]["cells"].get("from", ""), "depends_on": row["rec"]["depends_on"],
            "waits": row["waits"], "state": row["state"], "stale": row["stale"],
            "branch": row["branch"], "worktree": row["worktree"], "tip": row["tip"],
            "dirty": row["dirty"], "past": row["past"], "record": row["record"],
            "head": row["head"], "gate": row["gate"], "ruling": row["ruling"],
            "owed": row["rec"]["owed"], "next": {"text": row["next"][0], "command": command},
            "cut": row["cut"]}


def line_of(row):
    """R8: one line a row, a part with nothing to say left out."""
    parts = [row["row"], ("%s %s" % (first(row["level"]), first(row["repo"]))).strip(),
             row["state"]]
    if row["tip"]:
        parts.append("tip %s%s" % (row["tip"][:7], " +%d" % row["past"] if row["past"] else ""))
    if row["dirty"]:
        parts.append("dirty %d" % row["dirty"])
    gate = row["gate"]
    if gate:
        parts.append("gate %s %s" % (gate["id"], "running" if gate["exit"] is None
                                     else "exit %d" % gate["exit"]))
    text, command = row["next"]
    if command or text:
        parts.append("next: %s" % (command or text))
    return "  ".join(p for p in parts if p)


def clean(line):
    """Review 1 F3: a text line less its terminal escapes and control characters, as
    speak.py cleans the renderer's line; `--json` carries them as JSON escapes."""
    return CONTROL.sub("", ESCAPE.sub("", line))


def skipped_of(skipped):
    """[{repo, why, rows}] in first-seen order."""
    out = []
    for repo, why, name in skipped:
        group = next((g for g in out if g["repo"] == repo and g["why"] == why), None)
        if group is None:
            group = {"repo": repo, "why": why, "rows": []}
            out.append(group)
        group["rows"].append(name)
    return out


def root_of(args):
    """R2: DIR, or `history/rows` under the working directory's git top; and its git top."""
    root = getattr(args, "root", None)
    if root is None:
        top = git_top(os.getcwd())
        if top is None:
            raise RowsRefusal("no-root", "rows: no --root DIR and no git checkout here",
                              "name the folder of row folders with --root DIR")
        root = os.path.join(top, ROOT)
    if not os.path.isdir(root):
        raise RowsRefusal("no-root", "rows: %s is not a directory" % root,
                          "name the folder of row folders with --root DIR")
    root = os.path.realpath(root)
    home = git_top(root)
    if home is None:
        raise RowsRefusal("no-home", "rows: %s is in no git checkout" % root,
                          "put the row folders inside the home's checkout")
    return root, os.path.realpath(home)


def read(args):
    """The verb's whole read: (root, home, open rows, closed rows, skipped groups)."""
    words = list(getattr(args, "words", None) or [])
    check = bool(words) and words[0] == "check"
    if any(getattr(args, k, None) not in (None, False) for k in CLOSE_FLAGS):
        raise RowsRefusal("usage", "rows: --withdrawn, --repo, --dry-run and -y go with close",
                          "name close first: rows close ROW")
    root, home = root_of(args)
    repos = Repos(home, words[1:] if check else words)
    opened, shut, skipped = gathered_rows(root, repos, check)
    for row in opened:
        facts(row, repos.git(row["path"]))
    landed = set(r["row"] for r in opened if r["landing"])
    landed |= set(r["row"] for r in shut)
    known = set(r["row"] for r in opened) | landed | set(n for _, _, n in skipped)
    for row in opened:
        git = repos.git(row["path"])
        rec = row["rec"]
        row["waits"] = [d for d in rec["depends_on"] if d in known and d not in landed]
        row["state"], text, command, row["record"] = word(row, git)
        row["next"] = (text, command)
        row["stale"] = stale_of(row, git, repos)
        builds = rec["builds"]
        row["head"] = builds[-1]["head"] if builds else None
        row["gate"] = builds[-1]["gate"] if builds else None
        row["ruling"] = rec["reviews"][-1]["ruling"] if rec["reviews"] else None
        row["worktree"] = worktree_of(git, row["branch"]) if row["tip"] else None
        row["dirty"] = dirty_of(row["worktree"]) if row["worktree"] else None
        since = git.commit(row["head"]) if row["head"] else row["base"]
        count = git.run("rev-list", "--count", "%s..%s" % (since, row["tip"])) \
            if since and row["tip"] else None
        row["past"] = int(count) if count and count.isdigit() else None
        row["cut"] = cut_of(row, git, since) if is_cut(row) else None
    for row in shut:
        row["stale"] = []
        sha = row["rec"]["done"]["sha"]
        if check and sha and row["path"]:
            red = done_red(repos.git(row["path"]), sha, row["path"] == home)
            if red:
                row["stale"].append("done " + red[len("stale: "):])
    return check, root, home, opened, shut, skipped_of(skipped)


def cmd_rows(args, out, err):
    """`rows [check] [--json] [--root DIR] [REPO...]`: 0, or 1 when `check` finds a stale row."""
    words = list(getattr(args, "words", None) or [])
    if words and words[0] == "close":
        return cmd_close(args, words[1:], out, err)
    as_json = bool(getattr(args, "json", False))
    try:
        check, root, home, opened, shut, skipped = read(args)
    except RowsRefusal as exc:
        if not as_json:
            raise
        out.write(json.dumps({"schema": SCHEMA, "ok": False, "error": {
            "code": exc.code, "message": str(exc), "remedy": exc.remedy}}, indent=2) + "\n")
        return 2
    except Refusal as exc:
        if not as_json:
            raise
        out.write(json.dumps({"schema": SCHEMA, "ok": False, "error": {
            "code": "refused", "message": str(exc), "remedy": "read the message"}},
            indent=2) + "\n")
        return 2
    walked = [r for r in opened + shut if r["path"] is not None] if check else opened
    stale = [{"row": r["row"], "what": what} for r in sorted(walked, key=lambda r: r["row"])
             for what in r["stale"]]
    reds = len(set(s["row"] for s in stale))
    if as_json:
        got = {"schema": SCHEMA, "ok": True, "root": root, "home": home,
               "rows": [shown(r) for r in opened], "skipped": skipped}
        if check:
            got.update(checked=len(walked), stale=stale)
        out.write(json.dumps(got, indent=2) + "\n")
        return 1 if check and reds else 0
    lines = []
    if check:
        lines.extend("%s  stale: %s" % (s["row"], s["what"]) for s in stale)
    else:
        for row in opened:
            lines.append(line_of(row))
            lines.extend("  stale: %s" % what for what in row["stale"])
            if row["cut"]:
                lines.extend(cut_lines(row))
    for group in skipped:
        lines.append("skipped (%s): %s%s" % (group["why"], "" if group["repo"] is None
                                             else group["repo"] + ": ", ", ".join(group["rows"])))
    if check:
        lines.append("checked %d rows under %s: %d stale" % (len(walked), root, reds))
    elif not opened:
        lines.append("no open rows under %s" % root)
    out.write("\n".join(clean(line) for line in lines) + "\n")
    return 1 if check and reds else 0


def refused(message):
    """rw2b R1 to R4: a close's refusal, its line through `clean`."""
    return Refusal(clean(message))


def is_tty(stream):
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError, OSError):
        return False


def asked(stdin_tty, stderr_tty, reader, err):
    """rw2b R7: True for `y` or `yes` in any case, False for anything else, an end of file or
    an interrupt; None, nothing asked, unless stdin and stderr are both terminals."""
    if not (stdin_tty and stderr_tty):
        return None
    err.write(QUESTION)
    err.flush()
    try:
        answer = reader()
    except (EOFError, KeyboardInterrupt):
        answer = None
    if not answer:
        err.write("\n")
    return bool(answer) and answer.strip().lower() in YES


def snapshot(path):
    """Review 1 F1: (the bytes of `path` or None when absent, its text with its line ends),
    from one read; a Refusal naming why it cannot be read."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except FileNotFoundError:
        return None, ""
    except OSError as exc:
        raise Refusal("%s: unreadable: %s" % (path, exc))
    try:
        return raw, raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Refusal("%s: unreadable: %s" % (path, exc))


def with_cell(text, cell):
    """rw2b R5: `text` with the first table's `done` row as `| done | <cell> |`, its line end
    and every other byte kept; None when it has no `done` row."""
    lines = text.splitlines(True)
    for index, cells in table_rows(lines):
        if cells[0].lower() == "done":
            line = lines[index]
            body = line.rstrip("\r\n")
            lines[index] = "| done | %s |%s" % (cell, line[len(body):])
            return "".join(lines)
    return None


def waits_of(row, root, repos):
    """The read's `waits` for one row: its `depends_on` rows with a folder that have not
    landed, read only when the word could be `waits`."""
    rec = row["rec"]
    if row["landing"] or row["tip"] is not None or rec["builds"] or not rec["depends_on"]:
        return []
    opened, shut, skipped = gathered_rows(root, repos, False)
    landed = set(r["row"] for r in shut)
    for dep in opened:
        if dep["row"] in rec["depends_on"]:
            facts(dep, repos.git(dep["path"]))
            if dep["landing"]:
                landed.add(dep["row"])
    known = set(r["row"] for r in opened) | landed | set(n for _, _, n in skipped)
    return [d for d in rec["depends_on"] if d in known and d not in landed]


def checkout_of(args, row, home):
    """rw2b R3: the row's checkout, `--repo DIR` whatever its name, else `Repos.where`."""
    named = getattr(args, "repo", None)
    if named is not None:
        real = os.path.realpath(named)
        top = git_top(real) if os.path.isdir(real) else None
        if not top or os.path.realpath(top) != real or Git(real).tip("main") is None:
            raise refused("rows close: --repo %s is no checkout with a main" % named)
        return real
    path, why = Repos(home, None).where(row["repo"])
    if path is None:
        raise refused("rows close: %s's repo is not found (%s); name its checkout with "
                      "--repo DIR" % (row["row"], why))
    return path


def closing(args, row, root, home, text, old, err):
    """rw2b R3 to R5: (cell, the done file's new text or None, its line) of a pushed row
    that owes nothing; each contradiction one stderr line."""
    name = row["row"]
    row["path"] = checkout_of(args, row, home)
    repos = Repos(home, None)
    git = repos.git(row["path"])
    facts(row, git)
    row["waits"] = waits_of(row, root, repos)
    state = word(row, git)[0]
    if state != "pushed":
        raise refused("rows close: %s is %s, not pushed; nothing written" % (name, state))
    if row["rec"]["owed"]:
        raise refused("rows close: %s has %d open under ## Owed; nothing written"
                      % (name, row["rec"]["owed"]))
    for what in stale_of(row, git, repos):
        err.write(clean("rows close %s: stale: %s" % (name, what)) + "\n")
    sha7 = row["landing"][:7]
    cell = "%s %s" % (row["landed_on"], sha7)
    if re.search(r"(?<![0-9A-Za-z])" + sha7, old):
        return cell, None, "holds %s already, no line" % sha7
    lines = text.splitlines()
    prefix = "# Row %s: " % name
    title = lines[0][len(prefix):].strip() if lines and lines[0].startswith(prefix) else ""
    entry = "%s: %s, done %s" % (name, title, cell) if title else "%s, done %s" % (name, cell)
    last = next((l for l in reversed(old.splitlines()) if l.strip()), "")
    entry = ("- " if last.startswith("- ") else "") + entry
    sep = "" if not old or old.endswith("\n") else "\n"
    return cell, old + sep + entry + "\n", entry


def cmd_close(args, names, out, err):
    """rw2b: `rows close ROW [--withdrawn WHY] [--root DIR] [--repo DIR] [--dry-run] [-y]`:
    0 written, dry or closed already; a Refusal, exit 2, for the rest."""
    if getattr(args, "json", False):
        raise Refusal("rows close takes no --json")
    if not names:
        raise Refusal("rows close: name one row")
    if len(names) > 1:
        raise Refusal("rows close: one row a call")
    why = getattr(args, "withdrawn", None)
    if why is not None:
        why = why.strip()
        if not why or "|" in why or WHY_BAD.search(why):
            raise Refusal("rows close: --withdrawn takes one line of words with no | in it")
    root, home = root_of(args)
    name = names[0]
    if not NAME.fullmatch(name):
        raise refused("rows close: no such row under %s" % root)
    folder = os.path.join(root, name)
    path = os.path.join(folder, ROW)
    if not os.path.isfile(path):
        raise refused("rows close: no row %s under %s" % (name, root))
    # review 1 F1: what the close shows and writes comes from this one read of each file
    row_raw, text = snapshot(path)
    rec = records(folder)
    if "done" not in rec["cells"]:
        raise refused("rows close: %s has no done cell; nothing written" % path)
    if rec["done"]["state"] != "open":
        out.write(clean("rows close: %s is closed already: %s"
                        % (name, rec["cells"]["done"][:CLOSED_CAP])) + "\n")
        return 0
    done = os.path.join(home, DONE_FILE)
    shown = [(path, row_raw)]
    if why is not None:
        cell, done_text, entry = "withdrawn %s: %s" % (ask_module.today(), why), None, None
    else:
        done_raw, old = snapshot(done)
        shown.append((done, done_raw))
        cell, done_text, entry = closing(args, row_of(name, folder, rec), root, home, text, old,
                                         err)
    row_text = with_cell(text, cell)
    if row_text is None:
        raise refused("rows close: %s has no done cell; nothing written" % path)
    lines = ["rows close %s: %s: done %s" % (name, path, cell)]
    if entry is not None:
        lines.append("rows close %s: %s: %s" % (name, done, entry))
    out.write("".join(clean(line) + "\n" for line in lines))
    if getattr(args, "dry_run", False):
        out.write("rows close: dry run, nothing written\n")
        return 0
    if not getattr(args, "yes", False):
        out.flush()
        got = asked(is_tty(sys.stdin), is_tty(err), sys.stdin.readline, err)
        if got is None:
            raise Refusal("rows close: nothing written, since it cannot ask here; run it "
                          "again with -y")
        if not got:
            raise Refusal("rows close: declined, nothing written")
    texts = [(path, row_text)]
    if done_text is not None:
        texts.append((done, done_text))
    # review 1 F1: under the lock, each file read again just before the write; a change since
    # the read above refuses, so a close never writes over a hand's edit or another close's
    with held(os.path.join(root, CLOSE_LOCK), CLOSE_WAIT, err):
        for file, raw in shown:
            if snapshot(file)[0] != raw:
                raise refused("rows close: %s changed since the close read it; nothing "
                              "written; run the close again" % file)
        if done_text is not None:
            os.makedirs(os.path.dirname(done), exist_ok=True)
        commit_texts(texts)
    out.write(clean("rows close: %s %s" % (name, "withdrawn" if why is not None else "closed"))
              + "\n")
    return 0
