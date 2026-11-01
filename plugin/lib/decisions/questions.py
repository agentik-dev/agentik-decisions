"""The OPEN-QUESTIONS.md beside a ledger: its open question blocks, the lines
under `## Decided without asking` and `## Answered`, and each departure from
the shape `new` writes (the lint's L3, design d18 section 2).

    # Decisions for the owner ...    the first H1
    ## N. Title                      a block: the four bold labels in order, 2 to 4
                                     options under the third, the first alone
                                     marked ` (Recommended)`, a **Your answer:** line
    ## Decided without asking        an optional paragraph, then `- ` bullets
    ## Answered                      an optional paragraph, then bullets
                                     `- N. Title: LABEL (YYYY-MM-DD; source)`

At most five blocks are open, and no two share a number or, within one block,
an option label ignoring case. Front matter between `---` lines is skipped as
the ledger's parser skips it, and a `## ` line inside a code fence is text. A
`## Decided without asking` heading may carry trailing text. The text helpers
return the file with a block replaced or removed, or an Answered line added.
"""

import collections
import re

from . import ledger

__all__ = ["Block", "Questions", "parse", "replace_block", "remove_block", "add_answered",
           "option_label", "is_decided", "HEAD", "DECIDED", "ANSWERED", "ANSWER", "LABELS",
           "RECOMMENDED", "OPEN_CAP", "OPTIONS_MIN", "OPTIONS_MAX", "TAIL", "ANSWERED_LINE", "NAME"]

NAME = "OPEN-QUESTIONS.md"
HEAD = "# Decisions for the owner"
DECIDED = "## Decided without asking"
ANSWERED = "## Answered"
ANSWER = "**Your answer:**"
# The four bold labels of a block, in order; the third holds the options.
LABELS = ("Where things stand.", "The choice.", "What each answer sets in motion.",
          "Recommendation.")
RECOMMENDED = " (Recommended)"
# AskUserQuestion takes 2 to 4 options (design d18 section 1.1); entry 1 of the
# cross-repo ledger asks once per session in one batch, so at most five are open.
OPTIONS_MIN, OPTIONS_MAX, OPEN_CAP = 2, 4, 5

QUESTION = re.compile(r"^## (\d+)\.\s+(.*?)\s*$")
OPTION = re.compile(r"^- \*\*(.+?)\.\*\*(?:\s+(.*?))?\s*$")
LISTED = re.compile(r"^(\d+[.)]|[*+])\s")
ANSWERED_LINE = re.compile(r"^- (\d+)\.\s")
# A tail names a source after its date: a `;` or a `,`, then text (L1, L3). A
# clock time may follow the date (`2026-09-25 ~16:15; source`), and `and` may join
# a second date (`2026-09-22 and 2026-09-23; source`, d-n3's probe of the real
# ledgers). `amended DATE`, in any case, names no source (d-n3 item 9), but a
# source may follow it (`2026-09-28; amended 2026-09-29; the owner's word`).
STAMP = r"\d{4}-\d{2}-\d{2}(?:\s+~?\d{1,2}:\d{2})?"
AMENDED = r"(?i:amended)\b"
TAIL = re.compile(r"%s(?:\s+and\s+%s)*[;,]\s*(?:%s\s+%s\s*[;,]\s*)*(?!%s)\S"
                  % (STAMP, STAMP, AMENDED, STAMP, AMENDED))
# A fence opens and closes a code block, whose `## ` lines are text (d-n3 item 10).
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")

# number, title; start: the heading's index, 0-based; stop: the next `## `
# heading's index or the line count; text: the block without trailing blanks;
# labels: the bold labels in the order found; options: (label, marked, effect);
# parts: each label's paragraph on one line; answer: the text after
# **Your answer:**, or None when the line is absent.
Block = collections.namedtuple("Block",
                               "number title start stop text labels options parts answer")
# decided, answered: (1-based line, text) per non-blank line; problems: (line, message).
Questions = collections.namedtuple("Questions", "blocks decided answered problems")


def option_label(label):
    """`label` without its ` (Recommended)` marker."""
    return label[:-len(RECOMMENDED)] if label.endswith(RECOMMENDED) else label


def is_decided(line):
    """True when `line` opens with the `## Decided without asking` heading, so
    trailing text is allowed (d-n3 item 3)."""
    return line.startswith(DECIDED)


def body_start(lines):
    """(the index of the first line after the front matter, whether it closes): the
    front matter is skipped as `ledger.parse` skips it, an unclosed one to the end."""
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return i + 1, True
        return len(lines), False
    return 0, True


def closing(lines, i, mark):
    """The index of the fence that closes the one at `i`: its own character, at
    least as long (d-n3 fix round); None when none does."""
    for j in range(i + 1, len(lines)):
        found = FENCE.match(lines[j])
        if found and found.group(1)[0] == mark[0] and len(found.group(1)) >= len(mark):
            return j
    return None


def headings(lines, start=0):
    """(the index of each `## ` line from `start` outside a closed code fence, the
    index of the first fence never closed or None). A fence never closed is text,
    so it hides none of the lines after it."""
    found, unclosed, i = [], None, start
    while i < len(lines):
        opened = FENCE.match(lines[i])
        if opened:
            close = closing(lines, i, opened.group(1))
            if close is not None:
                i = close + 1
                continue
            unclosed = i if unclosed is None else unclosed
        elif lines[i].startswith("## "):
            found.append(i)
        i += 1
    return found, unclosed


def make_block(number, title, start, stop, lines):
    body = [i for i in range(start + 1, stop) if lines[i].strip()]
    end = body[-1] + 1 if body else start + 1
    labels, options, parts, answer, current, third = [], [], {}, None, None, False
    for i in range(start + 1, stop):
        line = lines[i].rstrip()
        if not line.strip():
            current = None
            continue
        label = next((l for l in LABELS if line.startswith("**%s**" % l)), None)
        if label:
            labels.append(label)
            third, current = label == LABELS[2], label
            parts[label] = line[len(label) + 4:].strip()
            continue
        if line.startswith(ANSWER):
            answer, third, current = line[len(ANSWER):].strip(), False, None
            continue
        if line.startswith("**"):
            third, current = False, None
            continue
        option = OPTION.match(line)
        if third and option:
            marked = option.group(1).endswith(RECOMMENDED)
            options.append((option_label(option.group(1)), marked, option.group(2) or ""))
            current = None
        elif current:
            parts[current] = (parts[current] + " " + line.strip()).strip()
    return Block(number, title, start, stop, "\n".join(l.rstrip() for l in lines[start:end]),
                 labels, options, parts, answer)


def check_list(rows, name, problems, tail):
    """An optional paragraph, then `- ` bullets (and their indented lines) only."""
    bullets = False
    for n, line in rows:
        if line.startswith("- "):
            bullets = True
            if tail and not TAIL.search(ledger.final_parenthetical(line) or ""):
                problems.append((n, "a line under `%s` ends in `(YYYY-MM-DD; source)`" % name))
        elif LISTED.match(line) or (bullets and not line.startswith(" ")):
            problems.append((n, "a line under `%s` that is not a `- ` bullet" % name))


def parse(text):
    """The Questions of `text`."""
    lines = text.splitlines()
    start, closed = body_start(lines)
    heads, unclosed = headings(lines, start)
    heads.append(len(lines))
    h1 = next((i for i in range(start, len(lines)) if lines[i].startswith("# ")), None)
    problems = [] if closed else [(1, "the front matter has no closing `---`")]
    if unclosed is not None:
        problems.append((unclosed + 1, "a code fence that is never closed"))
    if h1 is None or not lines[h1].startswith(HEAD):
        problems.append((1 if h1 is None else h1 + 1, "the first H1 does not start with `%s`"
                         % HEAD))
    blocks, decided, answered = [], [], []
    for start, stop in zip(heads, heads[1:]):
        head = lines[start].rstrip()
        rows = [(i + 1, lines[i].rstrip()) for i in range(start + 1, stop) if lines[i].strip()]
        found = QUESTION.match(head)
        if found:
            blocks.append(make_block(int(found.group(1)), found.group(2), start, stop, lines))
        elif is_decided(head):
            decided += rows
        elif head == ANSWERED:
            answered += rows
    numbered = set()
    for block in blocks:
        n, where = block.start + 1, "question %d" % block.number
        if block.number in numbered:
            problems.append((n, "%s: a second block numbered %d" % (where, block.number)))
        numbered.add(block.number)
        if block.labels != list(LABELS):
            problems.append((n, "%s: the four labels in order: %s" % (where, ", ".join(
                "**%s**" % l for l in LABELS))))
        if not OPTIONS_MIN <= len(block.options) <= OPTIONS_MAX:
            problems.append((n, "%s: %d options under the third label; 2 to 4 are asked"
                             % (where, len(block.options))))
        elif [m for _l, m, _e in block.options] != [True] + [False] * (len(block.options) - 1):
            problems.append((n, "%s: the first option alone is marked (Recommended)" % where))
        labels = set()
        for label, _marked, _effect in block.options:
            if label.lower() in labels:
                problems.append((n, "%s: two options share the label `%s`, ignoring case"
                                 % (where, label)))
            labels.add(label.lower())
        if block.answer is None:
            problems.append((n, "%s: no `%s` line" % (where, ANSWER)))
    if len(blocks) > OPEN_CAP:
        problems.append((blocks[OPEN_CAP].start + 1, "%d questions open; the cap is %d"
                         % (len(blocks), OPEN_CAP)))
    check_list(decided, DECIDED[3:], problems, False)
    check_list(answered, ANSWERED[3:], problems, True)
    problems.sort()
    return Questions(blocks, decided, answered, problems)


def replace_block(text, block, written):
    """`text` with `block` replaced by `written`, the lines after it kept."""
    lines = text.splitlines(keepends=True)
    after = "".join(lines[block.stop:])
    return "".join(lines[:block.start]) + written.rstrip("\n") + "\n" + (
        "\n" + after if after.strip() else "")


def remove_block(text, block):
    """`text` without `block` and the blank lines after it."""
    lines = text.splitlines(keepends=True)
    return ("".join(lines[:block.start]) + "".join(lines[block.stop:])).rstrip("\n") + "\n"


def add_answered(text, line):
    """`text` with `line` last under `## Answered`, the section made at the end."""
    lines = text.splitlines(keepends=True)
    at = next((i for i, l in enumerate(lines) if l.rstrip() == ANSWERED), None)
    if at is None:
        return text.rstrip("\n") + "\n\n%s\n\n%s\n" % (ANSWERED, line)
    stop = next((i for i in range(at + 1, len(lines)) if lines[i].startswith("## ")),
                len(lines))
    last = max(i for i in range(at, stop) if lines[i].strip())
    if not lines[last].endswith("\n"):
        lines[last] += "\n"
    gap = [] if last > at else ["\n"]
    return "".join(lines[:last + 1] + gap + [line + "\n"] + lines[last + 1:])
