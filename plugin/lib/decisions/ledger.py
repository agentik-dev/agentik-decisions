"""The ledger: one sectioned DECISIONS.md per repo, parsed and linted.

    ## In force      `### Every session` first when present, then `### <area>`;
                     each entry one line, `N. **Title.** paragraph (YYYY-MM-DD; source)`;
                     an hq's ledger may also hold `### Every session of the tree` (d36)
    ## Proposed      `N. **Title.** one sentence (proposed YYYY-MM-DD; OPEN-QUESTIONS.md)`
    ## Superseded    `- What: replaced by X (entry N), YYYY-MM-DD.` or `N. text`,
                     `merged into` or `lapsed with` in place of `replaced by`

Front matter, a title and prose may precede `## In force`. Proposed and
Superseded may be absent. Numbers are unique across the three sections; at
most 25 entries are in force. No count caps `Every session`: `render` measures the
file it checks against a ceiling in bytes instead (d36). A title ends in
`.`, `?` or `!` inside the bold; the `.` alone is dropped from `Entry.title`.
An unknown `## ` heading after a known one ends the section and the area
before it: a `N.` line under it is an entry with no section and no area, whose
number counts for the duplicate check and for `new`'s next number.

The line `<!-- decisions: legacy below -->` ends the parsed part (L4): the text
below it is an older ledger's, read by `show` and `find` and parsed as nothing.
`lint` adds the OPEN-QUESTIONS.md beside the ledger (L3).

The parser is tolerant, so `show` and `find` read a ledger the lint refuses;
each departure from the shape is one (line, message) in `Ledger.problems`.
"""

import collections
import os
import re
import shlex

from .common import Refusal, git_top, read_text
from . import questions

__all__ = ["Entry", "Area", "Ledger", "parse", "load", "locate", "where", "in_the_way", "display",
           "check_entry", "lint", "repeats", "sentences", "dropped", "unclosed",
           "final_parenthetical",
           "bold_title", "NAME", "IN_FORCE", "is_every", "is_tree", "ordered", "TITLES",
           "PROPOSED", "SUPERSEDED", "EVERY_SESSION", "TREE_SESSION", "IN_FORCE_CAP", "LEGACY"]

NAME = "DECISIONS.md"
IN_FORCE, PROPOSED, SUPERSEDED = "In force", "Proposed", "Superseded"
SECTIONS = (IN_FORCE, PROPOSED, SUPERSEDED)
EVERY_SESSION = "Every session"
# d36: an hq's ledger may hold this section; `render --scope tree` writes it alone into
# the CLAUDE.md of the folder that holds the hq's checkout, and the plain render leaves it out.
TREE_SESSION = "Every session of the tree"
# A ruling, not a measurement: example-mac entry 4 (2026-09-25), built by d17. d36 drops
# the count of seven under `Every session`; the ceilings in bytes are in `tree.CEILINGS`.
IN_FORCE_CAP = 25
# d36 (hq design/09 section 4): the ten behaviours' titles, in the order both blocks list
# their entries; an entry titled otherwise keeps its place after them, in ledger order.
TITLES = ("Writes", "Never run", "Devices", "Commits", "Pushes", "Never commit", "Helpers",
          "Budget", "Deciding and asking", "Changing these rules")
# The line that ends the parsed part of an older ledger (design d18 section 2, L4).
LEGACY = "<!-- decisions: legacy below -->"

HEADING = re.compile(r"^(#+)\s+(.*?)\s*$")
NUMBERED = re.compile(r"^(\d+)\.\s+(.*\S)\s*$")
BULLET = re.compile(r"^[-*]\s+(.*\S)\s*$")
# The bold title ends at the first `.**`, `?**` or `!**` followed by a space or
# the end (d-n3 item 2). A single `*` may sit inside it (a backticked `*.md`); a
# doubled one may not, since it would close the bold early.
TITLED = re.compile(r"^\*\*((?:[^*]|\*(?!\*))+?[.?!])\*\*(?=\s|$)(\s+(.*))?$")
ENDS = (".", "?", "!")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
# D22: a body that opens with a bold span, alone or after a number, repeats the title.
OPENS_BOLD = re.compile(r"^(?:\d+\.\s+)?\*\*")
# D22: the lint's name for each part of the shape a body repeats.
REPEATED = {"title": "bold title", "tail": "(date; source) tail"}
# A Superseded line names its fate (L2).
FATE = re.compile(r"\b(replaced by|superseded by|merged into|lapsed with)\b", re.IGNORECASE)
# A Proposed line's tail names the file its question sits in (d-n3 item 4).
ASKED_IN = "OPEN-QUESTIONS.md"

# number: an int, or None for an unnumbered Superseded line; title: the bold
# title without a final period (a `?` or `!` stays), else the text after the marker; body: the
# text after the marker; text: the line verbatim; section and area: None for an
# entry under an unknown `## ` heading (d-n3 fix round B1); heads: the heading
# lines it sits under, verbatim; line: 1-based.
Entry = collections.namedtuple("Entry", "number title body text section area heads line")
# name: the `###` heading's text; heads: `## In force` and the `###` line, verbatim.
Area = collections.namedtuple("Area", "name heads line")
# legacy: (the marker's 1-based line, the lines below it), or None.
Ledger = collections.namedtuple("Ledger", "path entries areas problems legacy")


def final_parenthetical(text):
    """The inside of the parenthetical `text` ends in, or None."""
    text = text.rstrip()
    if not text.endswith(")"):
        return None
    depth = 0
    for i in range(len(text) - 1, -1, -1):
        if text[i] == ")":
            depth += 1
        elif text[i] == "(":
            depth -= 1
            if depth == 0:
                return text[i + 1:-1]
    return None


def bold_title(title):
    """`title` bold, ending in a period unless it ends in `?` or `!` (d-n3 item 2)."""
    return "**%s**" % title if title.endswith(("?", "!")) else "**%s.**" % title


def repeats(body):
    """The parts of the entry shape `body` repeats, in order (D22): "title" when it
    opens with a bold span or `N. **`, "tail" when it ends in a parenthetical that
    opens with a date, then `;` or `,` and a source; [] for none. Only its start
    and its end are read, so a dated parenthetical or a `**` inside it is no repeat."""
    body = body.strip()
    found = ["title"] if OPENS_BOLD.match(body) else []
    tail = final_parenthetical(body)
    if tail is not None and questions.TAIL.match(tail.lstrip()):
        found.append("tail")
    return found


def sentences(paragraph):
    """`paragraph`'s sentences, in order, its whitespace runs one space: each is cut
    after a word that ends in `.`, `?` or `!`, and the words after the last cut are
    one more (d30 ruling 1)."""
    found, current = [], []
    for word in paragraph.split():
        current.append(word)
        if word.endswith(ENDS):
            found.append(" ".join(current))
            current = []
    if current:
        found.append(" ".join(current))
    return found


def dropped(old, new):
    """The sentences of `old` that `new` does not hold whole, between spaces or its
    ends, whitespace runs aside, in order (d30 ruling 1)."""
    held = " %s " % " ".join(new.split())
    return [s for s in sentences(old) if " %s " % s not in held]


def unclosed(body):
    """True when `body` holds a `(` followed at once by a date that no `)` closes, a
    `)` closing the nearest open `(` (d30 ruling 3)."""
    opened = []
    for i, char in enumerate(body):
        if char == "(":
            opened.append(i)
        elif char == ")" and opened:
            opened.pop()
    return any(DATE.match(body, i + 1) for i in opened)


# d31: an amendment opens `; amended DATE` (a `,` is read too) outside every nested
# parenthetical; form T2's combined clause stands for the older ones.
AMENDMENT = re.compile(r"[;,]\s*(?i:amended)\s+(\d{4}-\d{2}-\d{2})")
COMBINED = re.compile(r";\s*(?i:amended)\s+(?:once|(\d+)\s+times),\s*(\d{4}-\d{2}-\d{2})"
                      r"(?:\s+to\s+(\d{4}-\d{2}-\d{2}))?\s*(?=;|$)")


def amendments(tail):
    """(older, dated) of `tail`, read outside its nested parentheticals: `older` is
    (count, first date, last date) of a combined clause that sits before every dated
    amendment, else (0, None, None); `dated` is [(index of its separator, date)] of
    each `amended DATE`, in order (d31)."""
    older, dated, depth = (0, None, None), [], 0
    for i, char in enumerate(tail):
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(depth - 1, 0)
        elif char in ";," and depth == 0:
            combined = COMBINED.match(tail, i) if not dated and not older[0] else None
            found = AMENDMENT.match(tail, i)
            if combined:
                older = (int(combined.group(1) or 1), combined.group(2),
                         combined.group(3) or combined.group(2))
            elif found:
                dated.append((i, found.group(1)))
    return older, dated


def amended(tail):
    """How many amendments `tail` names: its combined clause's count and each
    `amended DATE` (d31)."""
    older, dated = amendments(tail)
    return older[0] + len(dated)


def folded(tail, amendment=None):
    """`tail` in form T2 (d31): its first date; one clause for the older amendments,
    `amended once, DATE` or `amended K times, DATE to DATE`; then the latest whole, to
    the tail's end. With `amendment`, a `DATE, source`, every amendment `tail` holds
    is older and `amendment` is the latest. A tail that opens with no date, or holds
    no `amended DATE` when no `amendment` is given, comes back as it is."""
    first = DATE.match(tail.lstrip())
    older, dated = amendments(tail)
    if first is None or not (dated or amendment):
        return tail
    if amendment:
        latest, before = "amended %s" % amendment, dated
    else:
        latest, before = tail[dated[-1][0] + 1:].strip(), dated[:-1]
    count = older[0] + len(before)
    start = older[1] or (before[0][1] if before else None)
    end = before[-1][1] if before else older[2]
    parts = [first.group(0)]
    if count == 1:
        parts.append("amended once, %s" % start)
    elif count > 1:
        parts.append("amended %d times, %s to %s" % (count, start, end))
    return "; ".join(parts + [latest])


def is_every(entry):
    """True for an entry in force under `### Every session`."""
    return entry.section == IN_FORCE and (entry.area or "").lower() == EVERY_SESSION.lower()


def is_tree(entry):
    """True for an entry in force under `### Every session of the tree` (d36)."""
    return entry.section == IN_FORCE and (entry.area or "").lower() == TREE_SESSION.lower()


def title_rank(title):
    """The index of `title` in TITLES, its case and runs of spaces aside, else None."""
    want = " ".join(title.split()).lower()
    return next((i for i, t in enumerate(TITLES) if t.lower() == want), None)


def ordered(entries):
    """`entries` in the order of the ten titles, then each other one in ledger order (d36)."""
    ranked = [(title_rank(e.title), i, e) for i, e in enumerate(entries)]
    known = sorted((r, i, e) for r, i, e in ranked if r is not None)
    return [e for _r, _i, e in known] + [e for r, _i, e in ranked if r is None]


def section_of(name):
    """The canonical section a `##` heading names, or None."""
    for section in SECTIONS:
        if name.strip().lower() == section.lower():
            return section
    return None


def check_entry(section, number, rest, problems, n):
    """The title of an entry line, adding a shape problem when it has one."""
    titled = TITLED.match(rest)
    title = titled.group(1).strip() if titled else rest
    if section == SUPERSEDED:
        if not DATE.search(rest) or not FATE.search(rest):
            problems.append((n, "%s: a Superseded line holds a date and names its fate: "
                                "`replaced by`, `merged into` or `lapsed with`"
                             % ("a line" if number is None else "entry %d" % number)))
        return title[:-1] if titled and title.endswith(".") else title
    if not titled or not title.endswith(ENDS) or not (titled.group(3) or "").strip():
        problems.append((n, "entry %s: the shape is `N. **Title.** text`, the title "
                            "ending in `.`, `?` or `!` inside the bold" % number))
        return title
    tail = final_parenthetical(rest)
    # d-n3 items 9 and 11: the date opens the tail, and `amended DATE` names no source.
    if section == IN_FORCE and (tail is None or not DATE.search(tail)):
        problems.append((n, "entry %s: it does not end in a parenthetical holding a date"
                            % number))
    elif section == IN_FORCE and not questions.TAIL.match(tail.lstrip()):
        problems.append((n, "entry %s: its tail names a source after the date: "
                            "`(YYYY-MM-DD; source)`" % number))
    if section == PROPOSED and (tail is None or not tail.startswith("proposed ")
                                or not DATE.search(tail)):
        problems.append((n, "entry %s: a Proposed line ends in `(proposed YYYY-MM-DD; ...)`"
                            % number))
    elif section == PROPOSED and ASKED_IN not in tail:
        problems.append((n, "entry %s: a Proposed line names `%s` in its tail"
                            % (number, ASKED_IN)))
    # D22: the body between the title and the final tail repeats neither.
    body = titled.group(3).rstrip()
    between = body[:-(len(tail) + 2)] if tail is not None else body
    if section == IN_FORCE and tail is not None and not between.strip():
        problems.append((n, "entry %s: its body is only its parenthetical; the paragraph "
                            "sits between the title and the tail" % number))
    for part in repeats(between):
        problems.append((n, "entry %s: its %s appears twice" % (number, REPEATED[part])))
    return title[:-1] if title.endswith(".") else title


def parse(text, path=NAME):
    """The Ledger of `text`; `path` names it in the problems."""
    lines = text.splitlines()
    entries, areas, problems = [], [], []
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
        else:
            problems.append((1, "the front matter has no closing `---`"))
            start = len(lines)
    marker = next((i for i in range(start, len(lines)) if lines[i].strip() == LEGACY), None)
    stop = len(lines) if marker is None else marker
    legacy = None if marker is None else (marker + 1, lines[marker + 1:])
    section, section_head, area = None, None, None
    # The unknown `## ` line the entries below sit under, when it follows a known one.
    orphan = None
    seen = []
    for i in range(start, stop):
        n, line = i + 1, lines[i].rstrip()
        if not line.strip():
            continue
        heading = HEADING.match(line)
        if heading:
            level, name = len(heading.group(1)), heading.group(2)
            if level == 1:
                if seen:
                    problems.append((n, "a level-1 heading inside the sections"))
                continue
            if level == 2:
                found = section_of(name)
                if found is None:
                    problems.append((n, "unknown section `## %s`; the sections are "
                                        "In force, Proposed and Superseded" % name))
                    # d-n3 item 1 (F7): no entry after it lands in the section or the area
                    # before it; fix round B1: its `N.` lines stay entries, for the numbers.
                    section, section_head, area = None, None, None
                    orphan = line if seen else None
                    continue
                if found in seen:
                    problems.append((n, "a second `## %s`" % found))
                elif seen and SECTIONS.index(found) < SECTIONS.index(seen[-1]):
                    problems.append((n, "`## %s` comes before `## %s`" % (found, seen[-1])))
                seen.append(found)
                section, section_head, area, orphan = found, line, None, None
                continue
            if level == 3 and section == IN_FORCE:
                if any(a.name.lower() == name.lower() for a in areas):
                    problems.append((n, "a second `### %s`" % name))
                # d36: the tree's section may sit anywhere under `## In force`
                if name.lower() == EVERY_SESSION.lower() and any(
                        a.name.lower() != TREE_SESSION.lower() for a in areas):
                    problems.append((n, "`### %s` comes first under `## In force`"
                                        % EVERY_SESSION))
                area = Area(name, (section_head, line), n)
                areas.append(area)
                continue
            problems.append((n, "a level-%d heading outside `## In force`" % level
                             if level == 3 else "a level-%d heading in the ledger" % level))
            continue
        if section is None:
            numbered = NUMBERED.match(line) if orphan else None
            if numbered:
                number, rest = int(numbered.group(1)), numbered.group(2)
                entries.append(Entry(number, check_entry(None, number, rest, [], n), rest, line,
                                     None, None, (orphan,), n))
            continue
        numbered = NUMBERED.match(line)
        bullet = BULLET.match(line) if section == SUPERSEDED else None
        if not numbered and not bullet:
            problems.append((n, "a line in `## %s` that is not an entry" % section))
            continue
        number = int(numbered.group(1)) if numbered else None
        rest = numbered.group(2) if numbered else bullet.group(1)
        title = check_entry(section, number, rest, problems, n)
        if section == IN_FORCE and area is None:
            problems.append((n, "entry %d sits outside a `###` subsection" % number))
        heads = area.heads if (section == IN_FORCE and area) else (section_head,)
        entries.append(Entry(number, title, rest, line, section,
                             area.name if (section == IN_FORCE and area) else None,
                             heads, n))
    if IN_FORCE not in seen:
        problems.append((1, "no `## In force` section"))
    first = {}
    for entry in entries:
        if entry.number is None:
            continue
        if entry.number in first:
            problems.append((entry.line, "entry %d repeats the number of line %d"
                             % (entry.number, first[entry.number])))
        else:
            first[entry.number] = entry.line
    in_force = [e for e in entries if e.section == IN_FORCE]
    if len(in_force) > IN_FORCE_CAP:
        problems.append((in_force[IN_FORCE_CAP].line, "%d entries in force; the cap is %d"
                         % (len(in_force), IN_FORCE_CAP)))
    problems.sort()
    return Ledger(path, entries, areas, problems, legacy)


def where(ledger=None, cwd=None):
    """The ledger's place, there or not: `ledger` when named, else DECISIONS.md at the git
    top of `cwd`; outside a git work tree with none named, a refusal."""
    cwd = os.getcwd() if cwd is None else cwd
    if ledger and ledger.endswith(tuple(filter(None, (os.sep, os.altsep)))):
        # dc1 r1 F4: --ledger names the ledger's file, never a folder
        raise Refusal("no ledger: --ledger %s names a folder; name the ledger's file, as %s"
                      % (shlex.quote(ledger), shlex.quote(ledger + NAME)))
    if ledger:
        return os.path.abspath(os.path.join(cwd, os.path.expanduser(ledger)))
    top = git_top(cwd)
    if not top:
        raise Refusal("no ledger: %s is outside a git work tree; name one with --ledger" % cwd)
    return os.path.join(top, NAME)


def in_the_way(path):
    """What stands at `path` when it is there and no ledger's file, in words, else None:
    `init` refuses with it, and `locate`'s refusal says the same (dc1 r1 F4, F5)."""
    if os.path.isdir(path):
        kind = "a folder"
    elif os.path.islink(path) and not os.path.exists(path):
        kind = "a link to nothing"
    elif os.path.lexists(path) and not os.path.isfile(path):
        kind = "no regular file"
    else:
        return None
    return "%s is %s, not a ledger; move it away or name a file with --ledger" % (path, kind)


def locate(ledger=None, cwd=None):
    """The ledger's path, by `where`; a refusal when no file is there, naming `init`."""
    path = where(ledger, cwd)
    if not os.path.isfile(path):
        way = in_the_way(path)
        if way:
            # dc1 r1 F5: what stands there, so the act it names can run
            raise Refusal("no ledger: %s; then `agentik decisions init` makes one" % way)
        # dc1 R5: the refusal names the next act
        raise Refusal("no ledger at %s; `agentik decisions init%s` makes one"
                      % (path, " --ledger %s" % shlex.quote(ledger) if ledger else ""))
    return path


def display(path, cwd=None):
    """`path` relative to `cwd` when below it, else under `~`, else absolute."""
    cwd = os.getcwd() if cwd is None else cwd
    path = os.path.abspath(path)
    rel = os.path.relpath(path, cwd)
    if not rel.startswith(os.pardir):
        return rel
    home = os.path.expanduser("~")
    if path.startswith(home.rstrip(os.sep) + os.sep):
        return "~" + os.sep + os.path.relpath(path, home)
    return path


def load(path, cwd=None):
    """The Ledger at `path`, its problems naming it as `display` does."""
    return parse(read_text(path), display(path, cwd))


def lint(path, cwd=None):
    """The Ledger at `path` and each lint problem as (file, line, message): the
    ledger's own, then those of the OPEN-QUESTIONS.md beside it when present (L3),
    whose questions and Proposed lines match one to one."""
    found = load(path, cwd)
    problems = [(found.path, n, m) for n, m in found.problems]
    beside = os.path.join(os.path.dirname(os.path.abspath(path)), questions.NAME)
    if not os.path.isfile(beside):
        return found, problems
    name = display(beside, cwd)
    parsed = questions.parse(read_text(beside))
    problems += [(name, n, m) for n, m in parsed.problems]
    asked = {b.number: b for b in parsed.blocks}
    proposed = {e.number: e for e in found.entries if e.section == PROPOSED}
    for number in sorted(set(asked) - set(proposed)):
        problems.append((name, asked[number].start + 1, "question %d has no Proposed line "
                         "in %s" % (number, NAME)))
    for number in sorted(set(proposed) - set(asked)):
        problems.append((found.path, proposed[number].line, "entry %d: a Proposed line with "
                         "no question in %s" % (number, questions.NAME)))
    return found, problems
