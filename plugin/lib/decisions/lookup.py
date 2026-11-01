"""`show` and `find`: entries read out of the ledger verbatim.

    show <n>...        each entry verbatim, under its section heading
    show --area NAME   a whole `###` subsection; NAME is a case-insensitive
                       prefix of its heading, an exact match first, and a
                       leading "The " in the heading may be left out
    find WORD          `N Title (area or section)` for each entry whose title or
                       body holds WORD, case-insensitively: the area for an entry
                       in force, else its section; no match prints nothing

Below the legacy marker (L4) an older ledger's text is read, never parsed:
`find` prints `L<line> <heading> (legacy)` for each block there that holds
WORD (a paragraph, a list item or a heading; `-` when no heading precedes it),
and `show --area` also matches its headings, printing a heading and the text
under it up to the next heading of its level or above.
"""

import re

from .common import Refusal
from .ledger import HEADING, IN_FORCE, Area, load

__all__ = ["cmd_show", "cmd_find", "excerpt", "title_line", "pick_area", "area_keys",
           "legacy_areas", "legacy_blocks"]

ITEM = re.compile(r"^\s{0,3}([-*+]|\d+[.)])\s")


def excerpt(entries):
    """The entries as a ledger excerpt: each heading once, blank lines between."""
    pieces, last = [], ()
    for entry in entries:
        common = 0
        while (common < min(len(entry.heads), len(last))
               and entry.heads[common] == last[common]):
            common += 1
        pieces.extend(entry.heads[common:])
        pieces.append(entry.text)
        last = entry.heads
    return "\n\n".join(pieces) + "\n" if pieces else ""


def area_keys(area):
    """The names an area answers to: its heading, and the heading without a leading "The "."""
    name = area.name.lower()
    return (name, name[4:]) if name.startswith("the ") else (name,)


def legacy_areas(ledger):
    """(Area, level) for each heading below the legacy marker, in order."""
    if ledger.legacy is None:
        return []
    marker, lines = ledger.legacy
    found = []
    for i, line in enumerate(lines):
        heading = HEADING.match(line.rstrip())
        if heading:
            found.append((Area(heading.group(2), (line.rstrip(),), marker + 1 + i),
                          len(heading.group(1))))
    return found


def legacy_blocks(ledger):
    """(line, heading, text) for each paragraph, list item and heading below the marker."""
    if ledger.legacy is None:
        return []
    marker, lines = ledger.legacy
    blocks, heading, current = [], "-", None
    for i, line in enumerate(lines):
        n, found = marker + 1 + i, HEADING.match(line.rstrip())
        if found:
            heading, current = found.group(2), None
            blocks.append([n, heading, line])
        elif not line.strip():
            current = None
        elif current is None or ITEM.match(line):
            current = [n, heading, line]
            blocks.append(current)
        else:
            current[2] += "\n" + line
    return [tuple(b) for b in blocks]


def legacy_text(ledger, area, level):
    """The heading `area` and the text under it, up to the next heading of `level` or above."""
    marker, lines = ledger.legacy
    start = area.line - marker - 1
    stop = next((i for i in range(start + 1, len(lines)) if HEADING.match(lines[i].rstrip())
                 and len(HEADING.match(lines[i].rstrip()).group(1)) <= level), len(lines))
    return "\n".join(l.rstrip() for l in lines[start:stop]).rstrip("\n") + "\n"


def pick_area(ledger, name, verb="show", legacy=True, absent=False, whole=()):
    """The Area `name` names, case-insensitively: an exact name first, else a unique
    prefix; a leading "The " in the heading or in `name` may be left out (`relay`,
    `### The relay`; `the monitoring`, `### Monitoring`). A heading named in `whole`,
    lower case, matches only by its whole name (`answer` passes `every session`).
    The headings below the legacy marker count unless `legacy` is false; `answer`
    passes false and `absent`, so a name no heading matches returns None (d-n3 item 7).
    Two prefix matches, or none without `absent`, are a Refusal naming `verb`."""
    want = " ".join(name.split()).lower()
    if not want:
        raise Refusal("%s: --area needs a name" % verb)
    areas = list(ledger.areas)
    if legacy:
        areas += [a for a, _level in legacy_areas(ledger)]
    wants = (want, want[4:]) if want.startswith("the ") and want[4:] else (want,)
    exact = [a for a in areas if any(w in area_keys(a) for w in wants)]
    if exact:
        return exact[0]
    found = [a for a in areas if a.name.lower() not in whole
             and any(k.startswith(w) for k in area_keys(a) for w in wants)]
    if len(found) == 1:
        return found[0]
    names = ", ".join(a.name for a in (found or areas)) or "none"
    if found:
        raise Refusal("%s: area `%s` is ambiguous: %s" % (verb, name, names))
    if absent:
        return None
    raise Refusal("%s: no area `%s` in %s; the areas are: %s" % (verb, name, ledger.path, names))


def cmd_show(args, path, out, err):
    ledger = load(path)
    if bool(args.numbers) == bool(args.area is not None):
        raise Refusal("show: name entry numbers or --area, not both or neither")
    if args.area is not None:
        area = pick_area(ledger, args.area)
        levels = {a.line: level for a, level in legacy_areas(ledger)}
        if area.line in levels:
            out.write(legacy_text(ledger, area, levels[area.line]))
            return 0
        entries = [e for e in ledger.entries if e.section == IN_FORCE and e.area == area.name]
        out.write(excerpt(entries) if entries else "\n\n".join(area.heads) + "\n")
        return 0
    by_number = {}
    for entry in ledger.entries:
        if entry.number is not None:
            by_number.setdefault(entry.number, entry)
    missing = [n for n in args.numbers if n not in by_number]
    if missing:
        raise Refusal("show: no entry %s in %s" % (", ".join(map(str, missing)), ledger.path))
    out.write(excerpt([by_number[n] for n in args.numbers]))
    return 0


def title_line(entry):
    """`N Title (area or section)`: the area for an entry in force, else its section,
    else the unknown `## ` heading it sits under (d-n3 fix round B1)."""
    label = entry.area if (entry.section == IN_FORCE and entry.area) else entry.section
    if label is None:
        label = HEADING.match(entry.heads[0]).group(2)
    number = "-" if entry.number is None else str(entry.number)
    return "%s %s (%s)" % (number, entry.title, label)


def cmd_find(args, path, out, err):
    word = args.word.strip().lower()
    if not word:
        raise Refusal("find: name a word")
    ledger = load(path)
    for entry in ledger.entries:
        if word in entry.body.lower():
            out.write(title_line(entry) + "\n")
    for line, heading, text in legacy_blocks(ledger):
        if word in text.lower():
            out.write("L%d %s (legacy)\n" % (line, heading))
    return 0
