"""`backlog`: each repo's NICE_TO_HAVE.md, placed against its HANDOFF.md build
order (design d23 sections 1 to 4); its items are column-0 bullets and the rows of
a table under NICE_HEADER (d26, agentik-hq design/05 section 2).

    decisions backlog [REPO...] [--order FILE] [--json]

REPO is a directory, by default the git top level of the working directory (or
the working directory outside a work tree). The verb reads the two files and
nothing else: it writes nothing, takes no lock, runs no model, renders nothing
through respeak and ignores `--ledger`. `--order FILE` (d26) reads FILE as the one
HANDOFF.md of every REPO, each REPO taking only the steps whose `repo` cell is its
directory name less `agentik-`, or `suite`; a table with no `repo` column gives every
REPO every step. An item's level is the session plugin's
S1 to S4; an unlevelled item is placed as S4 and printed `S4?`. Exit 0 whenever
the files could be read; 2 for usage, a REPO that is not a directory, or a file
unreadable or not UTF-8.
"""

import json
import os
import re
import subprocess

from .common import (GIT_TIMEOUT, Refusal, bounded, commit_texts, disk_text, git_top,
                     read_text)

__all__ = ["cmd_backlog", "nice_items", "build_order", "placement"]

NICE = "NICE_TO_HAVE.md"
HANDOFF = "HANDOFF.md"
PREFIX_NAME = "agentik-"
SUITE = "suite"
MARKER = "<!-- decisions: build order -->"
TITLE = 80
LEAD = 120

# d31 (b3): a count before the token (`0 S1, 10 S4`, a heading's tally) is no level.
LEVEL = re.compile(r"(?<![0-9] )\bS([1-4])\b")
# d31 (b3): a closed lead: `**Closed`, `~~`, `[x]`, or a bare `Closed` and a date.
CLOSED = re.compile(r"^(?:\*\*Closed\b|~~|\[[xX]\]|Closed [0-9]{4}-[0-9]{2}-[0-9]{2}\b)")
# The five forms a lead holds a level in (section 2); anything else is text. The
# fifth (d24) is the level at the lead's head, then a middle dot, U+00B7, between
# two spaces: `S3·x` is text. It goes last, so FORMS[0] keeps its title rule.
FORMS = (re.compile(r"^S([1-4])$"), re.compile(r"^S([1-4]),"),
         re.compile(r"[,;] S([1-4])$"), re.compile(r"\(S([1-4])\)$"),
         re.compile(r"^S([1-4]) · "))
SENTENCE = re.compile(r"\bEach line(?: below)? is S([1-4])\.")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^(```|~~~)")
BOLD = re.compile(r"^\*\*(.+?)\*\*")
SPAN = re.compile(r"`([^`]+)`")
CUT = re.compile(r":[0-9]+(?:-[0-9]+)?$")
EXTENSION = re.compile(r"\.[A-Za-z][A-Za-z0-9]{0,4}$")
STEP = re.compile(r"^([0-9]+)\. (.*)$")
# ASCII digits only: `¹` passes str.isdigit() and fails int(), `١` matches \d
NUMBER = re.compile(r"[0-9]+")
ROW_CELL = re.compile(r"(?<!\\)\|")
PREFIX = re.compile(r"(?i)^(build order|open work|next work|next\b)")
DONE = re.compile(r"\bdone\b|\bDECIDED\b")
# d26: a NICE table is this exact header row, then a separator row of as many cells;
# its level is the `level` cell alone, `^S[1-4]$`, anything else unlevelled
NICE_HEADER = ["id", "level", "area", "finding", "evidence", "from"]
SEPARATOR = re.compile(r"^:?-+:?$")
CELL_LEVEL = re.compile(r"^S([1-4])$")


def blocks(text):
    """(line number, kind, payload) for each line outside front matter and fences:
    `heading` (depth, title), `bullet` (text after `- `), `step` (n, text), `row`
    (cells), `more` (an indented line), `blank`, else `prose` (the line)."""
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
    fenced = False
    for i in range(start, len(lines)):
        line, n = lines[i], i + 1
        if FENCE.match(line):
            fenced = not fenced
            yield n, "prose", line
            continue
        if fenced:
            continue
        if not line.strip():
            yield n, "blank", None
        elif line[0] in " \t":
            yield n, "more", line.strip()
        elif line.startswith("- "):
            yield n, "bullet", line[2:].strip()
        elif HEADING.match(line):
            m = HEADING.match(line)
            yield n, "heading", (len(m.group(1)), m.group(2))
        elif STEP.match(line):
            m = STEP.match(line)
            yield n, "step", (int(m.group(1)), m.group(2).strip())
        elif line.startswith("|"):
            body = line.strip()
            body = body[1:-1] if body.endswith("|") and not body.endswith("\\|") else body[1:]
            yield n, "row", [cell.strip() for cell in ROW_CELL.split(body)]
        else:
            yield n, "prose", line


def gathered(text):
    """[(line, kind, payload, joined text)] with each bullet's and step's indented
    lines joined to it; a blank line inside stays inside when an indented one follows."""
    out, current = [], None
    for n, kind, payload in blocks(text):
        if kind == "more" and current is not None:
            current[3] += " " + payload
            continue
        if kind == "blank":
            continue
        current = None
        if kind == "bullet":
            current = [n, kind, payload, payload]
        elif kind == "step":
            current = [n, kind, payload, payload[1]]
        out.append(current if current is not None else [n, kind, payload, None])
    return out


def most_urgent(found):
    return "S%d" % min(int(x) for x in found) if found else None


def lead_of(text):
    """The bold lead, else the text to the first `: ` or `. `, else 120 characters."""
    m = BOLD.match(text)
    if m:
        return m.group(1)
    cuts = [i for i in (text.find(": "), text.find(". ")) if i >= 0]
    return text[:min(cuts)] if cuts else text[:LEAD]


def trimmed(lead):
    lead = lead.strip()
    if lead.endswith((".", ",")):
        lead = lead[:-1].rstrip()
    return lead


def lead_level(lead):
    """The level a lead holds in one of the five forms, the most urgent of two."""
    lead = trimmed(lead)
    return most_urgent([m.group(1) for form in FORMS for m in [form.search(lead)] if m])


def spans(text):
    """The backticked spans holding `/` or a file extension, each with a trailing
    `:N` or `:N-M` cut, in order and once each."""
    out = []
    for span in SPAN.findall(text or ""):
        span = CUT.sub("", span.strip())
        if span and ("/" in span or EXTENSION.search(span)) and span not in out:
            out.append(span)
    return out


def row_item(n, cells):
    """A NICE row as an item (d26): the level from its `level` cell (level_from
    `cell`), the title the lead of `finding` as a bullet's, the spans of `area`,
    `finding` and `evidence` in that order, and its `id`; a cell keeps its `\\|`."""
    cells = (list(cells) + [""] * len(NICE_HEADER))[:len(NICE_HEADER)]
    ident, cell, area, finding, evidence = cells[:5]
    m = CELL_LEVEL.match(cell)
    level = "S" + m.group(1) if m else None
    found = []
    for part in (area, finding, evidence):
        for span in spans(part):
            if span not in found:
                found.append(span)
    return {"line": n, "id": ident, "title": trimmed(lead_of(finding))[:TITLE],
            "level": level, "level_from": "cell" if level else None, "spans": found}


def scanned(text):
    """Each column-0 `- ` item of NICE_TO_HAVE.md and each row of a NICE_HEADER
    table, in file order, as a dict: line, title, level, level_from, spans; a row's
    also id. A row never takes a heading's or a sentence's level, nor marks one seen."""
    items, closed = [], []
    # the open headings, innermost last: [depth, heading level, sentence level, seen item]
    stack = []
    # the table being read, its rows on consecutive lines: [next line, header, body]
    table = None
    for n, kind, payload, joined in gathered(text):
        if kind == "row":
            if table is None or n != table[0]:
                table = [n + 1, payload, False]
            elif not table[2]:
                nice = (table[1] == NICE_HEADER and len(payload) == len(NICE_HEADER)
                        and all(SEPARATOR.match(c) for c in payload))
                table = [n + 1, NICE_HEADER if nice else None, True]
            else:
                table[0] = n + 1
                if table[1] is not None:
                    cells = (list(payload) + [""] * len(NICE_HEADER))[:len(NICE_HEADER)]
                    if CLOSED.match(cells[0]) or CLOSED.match(cells[3]):
                        closed.append(n)
                    else:
                        items.append(row_item(n, payload))
            continue
        table = None
        if kind == "heading":
            depth, title = payload
            while stack and stack[-1][0] >= depth:
                stack.pop()
            level = most_urgent(LEVEL.findall(title)) if depth in (2, 3) else None
            stack.append([depth, level, None, False])
        elif kind in ("prose", "more") and stack and not stack[-1][3]:
            found = SENTENCE.findall(payload)
            if found:
                held = [stack[-1][2][1:]] if stack[-1][2] else []
                stack[-1][2] = most_urgent(found + held)
        elif kind == "bullet":
            if stack:
                stack[-1][3] = True
            if CLOSED.match(joined):
                closed.append(n)
                continue
            lead = lead_of(joined)
            level, source = lead_level(lead), "lead"
            if level is None:
                level = next((s[2] for s in reversed(stack) if s[2]), None)
                source = "sentence"
            if level is None:
                level = next((s[1] for s in reversed(stack) if s[1]), None)
                source = "heading"
            title = trimmed(lead)
            if FORMS[0].search(title):
                # a bare `S4: ...` lead: the title is the lead of what follows it
                bold = BOLD.match(joined)
                rest = joined[bold.end() if bold else len(lead):].lstrip(" :.")
                title = trimmed(lead_of(rest)) if rest else title
            items.append({"line": n, "title": title[:TITLE], "level": level,
                          "level_from": source if level else None, "spans": spans(joined)})
    return items, closed


def nice_items(text):
    """The open items of NICE_TO_HAVE.md: `scanned` without its closed lines (d31)."""
    return scanned(text)[0]


def build_order(text):
    """(order, steps): order is {line, heading, open} or None; steps in file order,
    each {n, line, title, done, spans, repo}. The first step shape found in the section, a
    `N. ` item or a numbered table row, wins; the other is ignored. A row's repo is its
    cell under the `repo` column of the header above its table's separator, else None."""
    rows = gathered(text)
    marker = next((n for n, kind, payload, _ in rows if kind == "prose"
                   and payload.strip() == MARKER), None)
    start = None
    for i, (n, kind, payload, _) in enumerate(rows):
        if kind != "heading" or payload[0] != 2:
            continue
        if (marker is not None and n > marker) or (marker is None and PREFIX.match(payload[1])):
            start = i
            break
    if start is None:
        return None, []
    steps, shape, header, last = [], None, None, None
    for n, kind, payload, joined in rows[start + 1:]:
        if kind == "heading" and payload[0] <= 2:
            break
        if kind == "row" and not (payload and NUMBER.fullmatch(payload[0])):
            if payload and all(SEPARATOR.match(c) for c in payload):
                header = last
            else:
                last = payload
            continue
        if kind in ("step", "row"):
            shape = shape or kind
            if kind != shape:
                continue
        if kind == "step":
            number, body = payload
            m = BOLD.match(joined)
            title = m.group(1) if m else joined[:TITLE]
            cut = joined.find(". ")
            lead = (joined[:cut] if cut >= 0 else joined)[:LEAD]
            steps.append({"n": number, "line": n, "title": trimmed(title)[:TITLE],
                          "done": bool(DONE.search(lead)), "spans": spans(joined),
                          "repo": None})
        elif kind == "row":
            title = payload[1] if len(payload) > 1 else ""
            column = header.index("repo") if header and "repo" in header else None
            repo = None if column is None else (payload[column] if column < len(payload) else "")
            state = header.index("state") if header and "state" in header else -1
            steps.append({"n": int(payload[0]), "line": n, "title": trimmed(title)[:TITLE],
                          "done": payload[-1].startswith("done"),
                          "spans": spans(" | ".join(payload)), "repo": repo,
                          "item": title,
                          "state": payload[state] if state < len(payload) else ""})
    heading = rows[start]
    order = {"line": heading[0], "heading": heading[2][1],
             "open": sum(1 for s in steps if not s["done"])}
    return order, steps


def placement(items, steps):
    """[("step", step) | ("item", item)] in placement order (section 4); each item
    gains rank, placed_as, after_step and span."""
    opened = [s for s in steps if not s["done"]]
    front = ([i for i in items if i["level"] == "S1"] + [i for i in items if i["level"] == "S2"])
    attached = [[] for _ in opened]
    tail3, tail4 = [], []
    for item in items:
        item["after_step"], item["span"] = None, None
        if item["level"] in ("S1", "S2"):
            continue
        for k, step in enumerate(opened):
            shared = next((s for s in item["spans"] if s in step["spans"]), None)
            if shared:
                item["after_step"], item["span"] = step["n"], shared
                attached[k].append(item)
                break
        else:
            (tail3 if item["level"] == "S3" else tail4).append(item)
    rows = [("item", i) for i in front]
    for step, group in zip(opened, attached):
        rows.append(("step", step))
        rows.extend(("item", i) for i in group)
    rows.extend(("item", i) for i in tail3 + tail4)
    rank = 0
    for kind, item in rows:
        if kind == "item":
            rank += 1
            item["rank"], item["placed_as"] = rank, item["level"] or "S4"
    return rows


def short_name(repo):
    """The repo's directory name less a leading `agentik-` (d26)."""
    name = os.path.basename(repo)
    return name[len(PREFIX_NAME):] if name.startswith(PREFIX_NAME) else name


def for_repo(steps, repo):
    """The steps of an `--order` FILE that `repo` takes: those with no repo column,
    and those whose cell is its short name or `suite`."""
    names = (short_name(repo), SUITE)
    return [s for s in steps if s["repo"] is None or s["repo"] in names]


def view(repo, ordered=None):
    """The view of one repo, or None when it holds no NICE_TO_HAVE.md; `ordered`,
    (path, order, steps) of an `--order` FILE, stands for the repo's HANDOFF.md."""
    nice, handoff = os.path.join(repo, NICE), os.path.join(repo, HANDOFF)
    if not os.path.lexists(nice):
        return None
    items, closed = scanned(read_text(nice))
    if ordered is None:
        has_handoff = os.path.lexists(handoff)
        order, steps = build_order(read_text(handoff)) if has_handoff else (None, [])
        handoff = handoff if has_handoff else None
    else:
        handoff, order, steps = ordered
        steps = for_repo(steps, repo)
        if order:
            order = dict(order, open=sum(1 for s in steps if not s["done"]))
    rows = placement(items, steps)
    return {"repo": repo, "nice": nice, "handoff": handoff, "order": order,
            "steps": steps, "rows": rows, "ordered": ordered is not None,
            "closed": closed}


def as_json(v):
    keys = ("rank", "line", "title", "level", "placed_as", "level_from", "after_step", "span")
    return {"repo": v["repo"], "nice": v["nice"], "handoff": v["handoff"], "order": v["order"],
            "steps": [{k: s[k] for k in ("n", "line", "title", "done") + (
                ("repo",) if v["ordered"] else ())} for s in v["steps"]],
            "items": [dict({k: i[k] for k in keys}, **({"id": i["id"]} if "id" in i else {}))
                      for kind, i in v["rows"] if kind == "item"],
            "closed": v["closed"]}


def as_text(v):
    name = os.path.basename(v["repo"])
    order = v["order"]
    doc = os.path.basename(v["handoff"]) if v["handoff"] else HANDOFF
    if order:
        head = '%s:%d "%s", %d open steps' % (doc, order["line"], order["heading"],
                                             order["open"])
    elif v["handoff"] is None:
        head = "none (no HANDOFF.md)"
    else:
        head = "none (no build-order section in %s)" % doc
    lines = ["== %s  build order: %s" % (name, head)]
    items = 0
    bare = 0
    for kind, row in v["rows"]:
        if kind == "step":
            lines.append("step %d  %s:%d  %s" % (row["n"], doc, row["line"], row["title"]))
        else:
            items += 1
            bare += row["level"] is None
            lines.append("%d %s  NICE_TO_HAVE.md:%d  %s" % (
                row["rank"], row["level"] or "S4?", row["line"],
                row["id"] + "  " + row["title"] if "id" in row else row["title"]))
    lines.append("%d of %d items carry no level (placed as S4)" % (bare, items))
    if v["closed"]:
        lines.append("%d closed, not placed" % len(v["closed"]))
    return lines


def cmd_backlog(args, out, err):
    if getattr(args, "write", False) and not getattr(args, "check", False):
        raise Refusal("backlog: --write takes --check")
    if getattr(args, "check", False):
        return cmd_check(args, out, err)
    names = list(getattr(args, "repos", None) or [])
    if not names:
        here = os.getcwd()
        names = [git_top(here) or here]
    repos = []
    for name in names:
        if not os.path.isdir(name):
            raise Refusal("backlog: %s is not a directory" % name)
        repos.append(os.path.realpath(name))
    ordered, order_file = None, getattr(args, "order", None)
    if order_file is not None:
        if not os.path.isfile(order_file):
            raise Refusal("backlog: --order %s is not a file" % order_file)
        path = os.path.realpath(order_file)
        ordered = (path,) + build_order(read_text(path))
    views, skipped = [], []
    for repo in repos:
        v = view(repo, ordered)
        if v is None:
            skipped.append(repo)
        else:
            views.append(v)
    if getattr(args, "json", False):
        out.write(json.dumps({"repos": [as_json(v) for v in views], "skipped": skipped},
                             indent=2) + "\n")
        return 0
    blocks_out = ["\n".join(as_text(v)) for v in views]
    if skipped and len(repos) == 1:
        blocks_out.append("== %s  no NICE_TO_HAVE.md" % os.path.basename(skipped[0]))
    elif skipped:
        blocks_out.append("skipped (no NICE_TO_HAVE.md): %s"
                          % ", ".join(os.path.basename(s) for s in skipped))
    out.write("\n\n".join(blocks_out) + ("\n" if blocks_out else ""))
    return 0


# d39 (agentik-hq design/14 §3.2, §3.3): `--check` holds each row's state cell against git,
# read with `git -C <repo>` and never written, fetched or checked out; no gate ledger, no
# relay state. A row's repo is a REPO by its short name; an `hq` or `suite` row, or one
# whose cell is FILE's checkout's own short name, is read in FILE's checkout.
HOME_CELL = "hq"
QUESTIONS = "OPEN-QUESTIONS.md"
DONE_FILE = os.path.join("history", "handoff-done.md")
DATE_WORD = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
SHA_WORD = re.compile(r"^[0-9a-fA-F]{7,40}$")
# A branch's whole name in a merge's subject: the next character is none a name may hold
# (`g2` never matches `g2b-edit-gates`; a name never ends in `.`).
NAME_END = r"(?![\w/+@-]|\.\w)"
SKIP_WHY = "repo not named or absent"


def reference(cell, names):
    """R1: the reference a state cell's first words make (free text may follow after `;`):
    `waiting:` on `owner <n>`, `row <n>`, `the owner:` (tried first) or `<repo> <branch>`
    with `<repo>` one of `names`, the table's repo column; `building [<repo>] <branch>`;
    `done <date> <sha>`; `watch:`; else its first word."""
    head = cell.split(";", 1)[0].strip()
    words = [w.rstrip(",") for w in head.split()]
    if head.startswith("waiting:"):
        rest = head[len("waiting:"):].strip()
        w = [x.rstrip(",.") for x in rest.split()]
        if rest.startswith("the owner:"):
            return {"kind": "waiting", "on": "the owner"}
        if len(w) >= 2 and w[0] in ("owner", "row") and w[1].isdigit():
            return {"kind": "waiting", "on": w[0], "n": int(w[1])}
        if len(w) >= 2 and w[0] in names:
            return {"kind": "waiting", "on": "branch", "repo": w[0], "branch": w[1]}
        return {"kind": "waiting", "on": None}
    if words[:1] == ["building"] and len(words) >= 2:
        if len(words) >= 3 and words[1] in names:
            return {"kind": "building", "repo": words[1], "branch": words[2]}
        return {"kind": "building", "repo": None, "branch": words[1]}
    if words[:1] == ["done"]:
        date = words[1] if len(words) > 1 and DATE_WORD.match(words[1]) else None
        sha = words[2] if date and len(words) > 2 and SHA_WORD.match(words[2]) else None
        return {"kind": "done", "date": date, "sha": sha}
    if head.startswith("watch:"):
        return {"kind": "watch"}
    return {"kind": words[0].rstrip(":") if words else None}


def said(ref):
    """The reference's own words, the text view's second column."""
    if ref["kind"] == "building":
        return "building " + " ".join(w for w in (ref["repo"], ref["branch"]) if w)
    if ref["kind"] == "done":
        return "done %s %s" % (ref["date"], ref["sha"])
    if ref.get("on") == "branch":
        return "waiting: %s %s" % (ref["repo"], ref["branch"])
    if ref.get("on") in ("owner", "row"):
        return "waiting: %s %d" % (ref["on"], ref["n"])
    return ref["kind"] or ""


class Git(object):
    """One repo read through `git -C`: main's first-parent line and its branches, cached."""

    def __init__(self, repo):
        self.repo, self._line = repo, None

    def run(self, *argv):
        try:
            code, out = bounded(["git", "-C", self.repo, "-c", "log.showSignature=false"]
                                + list(argv), GIT_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise Refusal("git timed out after %d s in %s" % (GIT_TIMEOUT, self.repo))
        except OSError as exc:
            raise Refusal("git cannot run in %s: %s" % (self.repo, exc))
        return out.strip() if code == 0 else None

    def commit(self, rev):
        return self.run("rev-parse", "--verify", "--quiet", rev + "^{commit}")

    def tip(self, branch):
        return self.commit("refs/heads/" + branch)

    def line(self):
        """[(sha, parents, committer date, subject)] of main's first-parent line, newest first;
        main is `main` when it is a branch, else HEAD."""
        if self._line is None:
            main = "refs/heads/main" if self.tip("main") else "HEAD"
            out = self.run("log", "--first-parent", "--date=short",
                           "--format=%H%x1f%P%x1f%cd%x1f%s", main, "--")
            self._line = []
            for record in (out or "").splitlines():
                parts = record.split("\x1f")
                if len(parts) == 4:
                    self._line.append((parts[0], parts[1].split(), parts[2], parts[3]))
        return self._line


def building_red(git, branch):
    """R3: `stale: landed <sha> <date>` for the newest merge on main's first-parent line whose
    subject opens `merge <branch>` or `Merge <branch>`, or whose second parent is the branch's
    tip; else `stale: branch gone` when the branch is absent; else None."""
    named = re.compile(r"^[mM]erge %s%s" % (re.escape(branch), NAME_END))
    tip = git.tip(branch)
    for sha, parents, date, subject in git.line():
        if len(parents) > 1 and (named.match(subject) or (tip and parents[1] == tip)):
            return "stale: landed %s %s" % (sha[:7], date), sha, date
    return ("stale: branch gone" if tip is None else None), None, None


def done_red(git, sha, plain):
    """R3: the sha is on main's first-parent line, a merge or, when `plain`, any commit."""
    full = git.commit(sha)
    parents = next((p for s, p, _, _ in git.line() if s == full), None) if full else None
    if parents is None:
        return "stale: %s is not on main's first-parent line" % sha
    if len(parents) < 2 and not plain:
        return "stale: %s is not a merge" % sha
    return None


def answered(path):
    """The numbers listed under `## Answered` of the OPEN-QUESTIONS.md at `path`."""
    if not os.path.isfile(path):
        return set()
    found, inside = set(), False
    for line in read_text(path).splitlines():
        m = HEADING.match(line)
        if m and len(m.group(1)) <= 2:
            inside = m.group(2).strip().startswith("Answered")
            continue
        n = re.match(r"^(?:- )?([0-9]+)\.", line) if inside else None
        if n:
            found.add(int(n.group(1)))
    return found


def checked(path, steps, repos, home):
    """R2 to R4: one result a table row of FILE at `path`."""
    rows = [s for s in steps if "state" in s]
    names = set(s["repo"] for s in rows if s["repo"])
    numbers = set(s["n"] for s in rows)
    homes = (HOME_CELL, SUITE) + ((short_name(home),) if home else ())
    by_name = {}
    for repo in repos:
        if os.path.isdir(repo) and git_top(repo):
            by_name.setdefault(short_name(repo), os.path.realpath(repo))
    gits = {}

    def checkout(name):
        where = home if (name is None or name in homes) else by_name.get(name)
        if where is not None and where not in gits:
            gits[where] = Git(where)
        return where

    done_of = answered(os.path.join(os.path.dirname(path), QUESTIONS))
    results = []
    for s in rows:
        ref = reference(s["state"], names)
        row = {"n": s["n"], "line": s["line"], "repo": s["repo"], "item": s["item"],
               "cell": s["state"], "reference": ref, "checked_in": None, "red": None,
               "skipped": None, "landed": None}
        results.append(row)
        kind, on = ref["kind"], ref.get("on")
        if kind == "waiting" and on == "owner":
            row["red"] = "answered" if ref["n"] in done_of else None
            continue
        if kind == "waiting" and on == "row":
            row["red"] = None if ref["n"] in numbers else "resolved"
            continue
        branch = ref.get("branch") if kind == "building" or on == "branch" else None
        if branch is None and not (kind == "done" and ref["sha"]):
            continue
        where = checkout(ref.get("repo") or s["repo"])
        if where is None:
            row["skipped"] = SKIP_WHY
            continue
        row["checked_in"] = where
        if branch is not None:
            row["red"], sha, date = building_red(gits[where], branch)
            row["landed"] = {"sha": sha[:7], "date": date} if sha else None
        else:
            plain = s["repo"] is not None and s["repo"] in homes and s["repo"] != SUITE
            row["red"] = done_red(gits[where], ref["sha"], plain)
    return results


def moved(path, results):
    """R5: (HANDOFF text, done file path, its text) with each landed `building` row moved out,
    every other byte kept; None when no row landed. Its line is `<#> <item>, done <date>
    <sha>`, a bullet when the done file's last line is one."""
    landed = [r for r in results if r["landed"] and r["reference"]["kind"] == "building"]
    if not landed:
        return None
    lines = disk_text(path).split("\n")
    done = os.path.join(os.path.dirname(path), DONE_FILE)
    old = disk_text(done)
    last = next((l for l in reversed(old.splitlines()) if l.strip()), "")
    bullet = "- " if last.startswith("- ") else ""
    added = []
    for r in sorted(landed, key=lambda r: r["line"], reverse=True):
        cells = [c.strip() for c in ROW_CELL.split(lines[r["line"] - 1].strip().strip("|"))]
        if not cells or cells[0] != str(r["n"]):
            raise Refusal("backlog: %s:%d is not row %d; nothing written"
                          % (path, r["line"], r["n"]))
        del lines[r["line"] - 1]
        r["cell"] = "done %s %s" % (r["landed"]["date"], r["landed"]["sha"])
        added.insert(0, "%s%d %s, %s" % (bullet, r["n"], r["item"], r["cell"]))
    sep = "" if not old or old.endswith("\n") else "\n"
    return "\n".join(lines), done, old + sep + "".join(a + "\n" for a in added)


def cmd_check(args, out, err):
    """`backlog --check --order FILE [REPO...] [--write] [--json]` (d39): exit 1 on a stale
    cell left, 0 on none; a REPO absent is no usage error, its rows are skipped."""
    order_file = getattr(args, "order", None)
    if order_file is None:
        raise Refusal("backlog: --check takes --order FILE")
    if not os.path.isfile(order_file):
        raise Refusal("backlog: --order %s is not a file" % order_file)
    path = os.path.realpath(order_file)
    _order, steps = build_order(read_text(path))
    home = git_top(os.path.dirname(path))
    home = os.path.realpath(home) if home else None
    repos = list(getattr(args, "repos", None) or [])
    results = checked(path, steps, repos, home)
    written = []
    if getattr(args, "write", False):
        change = moved(path, results)
        if change is not None:
            text, done, done_text = change
            os.makedirs(os.path.dirname(done), exist_ok=True)
            commit_texts([(path, text), (done, done_text)])
            written = [r["n"] for r in results if r["landed"]
                       and r["reference"]["kind"] == "building"]
    left = [r for r in results if r["red"] and r["n"] not in written]
    if getattr(args, "json", False):
        keys = ("n", "repo", "cell", "reference", "checked_in", "red", "skipped")
        out.write(json.dumps({"handoff": path, "checkout": home,
                              "rows": [dict({k: r[k] for k in keys},
                                            written=r["n"] in written) for r in results],
                              "stale": len(left), "written": written}, indent=2) + "\n")
        return 1 if left else 0
    lines = []
    for r in results:
        if r["red"]:
            lines.append("%d  %s  %s%s" % (r["n"], said(r["reference"]), r["red"],
                                           "; moved to %s" % DONE_FILE if r["n"] in written
                                           else ""))
    skipped = [r for r in results if r["skipped"]]
    if skipped:
        lines.append("skipped (%s): %s" % (SKIP_WHY, ", ".join(
            "%d %s" % (r["n"], r["reference"].get("repo") or r["repo"]) for r in skipped)))
    lines.append("checked %d rows of %s: %d stale" % (len(results), os.path.basename(path),
                                                       len(left)))
    out.write("\n".join(lines) + "\n")
    return 1 if left else 0
