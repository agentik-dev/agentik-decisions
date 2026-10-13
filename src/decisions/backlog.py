"""`backlog`: each repo's NICE_TO_HAVE.md, placed against its HANDOFF.md build
order (design d23 sections 1 to 4).

    decisions backlog [REPO...] [--json]

REPO is a directory, by default the git top level of the working directory (or
the working directory outside a work tree). The verb reads the two files and
nothing else: it writes nothing, takes no lock, runs no model, renders nothing
through respeak and ignores `--ledger`. An item's level is the session plugin's
S1 to S4; an unlevelled item is placed as S4 and printed `S4?`. Exit 0 whenever
the files could be read; 2 for usage, a REPO that is not a directory, or a file
unreadable or not UTF-8.
"""

import json
import os
import re

from .common import Refusal, git_top, read_text

__all__ = ["cmd_backlog", "nice_items", "build_order", "placement"]

NICE = "NICE_TO_HAVE.md"
HANDOFF = "HANDOFF.md"
MARKER = "<!-- decisions: build order -->"
TITLE = 80
LEAD = 120

LEVEL = re.compile(r"\bS([1-4])\b")
# The four forms a lead holds a level in (section 2); anything else is text.
FORMS = (re.compile(r"^S([1-4])$"), re.compile(r"^S([1-4]),"),
         re.compile(r"[,;] S([1-4])$"), re.compile(r"\(S([1-4])\)$"))
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
    """The level a lead holds in one of the four forms, the most urgent of two."""
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


def nice_items(text):
    """Each column-0 `- ` item of NICE_TO_HAVE.md, in file order, as a dict: line,
    title, level, level_from, spans."""
    items = []
    # the open headings, innermost last: [depth, heading level, sentence level, seen item]
    stack = []
    for n, kind, payload, joined in gathered(text):
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
    return items


def build_order(text):
    """(order, steps): order is {line, heading, open} or None; steps in file order,
    each {n, line, title, done, spans}. The first step shape found in the section, a
    `N. ` item or a numbered table row, wins; the other is ignored."""
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
    steps, shape = [], None
    for n, kind, payload, joined in rows[start + 1:]:
        if kind == "heading" and payload[0] <= 2:
            break
        if kind == "row" and not (payload and NUMBER.fullmatch(payload[0])):
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
                          "done": bool(DONE.search(lead)), "spans": spans(joined)})
        elif kind == "row":
            title = payload[1] if len(payload) > 1 else ""
            steps.append({"n": int(payload[0]), "line": n, "title": trimmed(title)[:TITLE],
                          "done": payload[-1].startswith("done"),
                          "spans": spans(" | ".join(payload))})
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


def view(repo):
    """The view of one repo, or None when it holds no NICE_TO_HAVE.md."""
    nice, handoff = os.path.join(repo, NICE), os.path.join(repo, HANDOFF)
    if not os.path.lexists(nice):
        return None
    items = nice_items(read_text(nice))
    has_handoff = os.path.lexists(handoff)
    order, steps = build_order(read_text(handoff)) if has_handoff else (None, [])
    rows = placement(items, steps)
    return {"repo": repo, "nice": nice, "handoff": handoff if has_handoff else None,
            "order": order, "steps": steps, "rows": rows}


def as_json(v):
    keys = ("rank", "line", "title", "level", "placed_as", "level_from", "after_step", "span")
    return {"repo": v["repo"], "nice": v["nice"], "handoff": v["handoff"], "order": v["order"],
            "steps": [{k: s[k] for k in ("n", "line", "title", "done")} for s in v["steps"]],
            "items": [{k: i[k] for k in keys} for kind, i in v["rows"] if kind == "item"]}


def as_text(v):
    name = os.path.basename(v["repo"])
    order = v["order"]
    if order:
        head = 'HANDOFF.md:%d "%s", %d open steps' % (order["line"], order["heading"],
                                                     order["open"])
    elif v["handoff"] is None:
        head = "none (no HANDOFF.md)"
    else:
        head = "none (no build-order section in HANDOFF.md)"
    lines = ["== %s  build order: %s" % (name, head)]
    items = 0
    bare = 0
    for kind, row in v["rows"]:
        if kind == "step":
            lines.append("step %d  HANDOFF.md:%d  %s" % (row["n"], row["line"], row["title"]))
        else:
            items += 1
            bare += row["level"] is None
            lines.append("%d %s  NICE_TO_HAVE.md:%d  %s" % (
                row["rank"], row["level"] or "S4?", row["line"], row["title"]))
    lines.append("%d of %d items carry no level (placed as S4)" % (bare, items))
    return lines


def cmd_backlog(args, out, err):
    names = list(getattr(args, "repos", None) or [])
    if not names:
        here = os.getcwd()
        names = [git_top(here) or here]
    repos = []
    for name in names:
        if not os.path.isdir(name):
            raise Refusal("backlog: %s is not a directory" % name)
        repos.append(os.path.realpath(name))
    views, skipped = [], []
    for repo in repos:
        v = view(repo)
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
