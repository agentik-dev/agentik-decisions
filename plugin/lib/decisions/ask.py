"""`new`: the four-part question for the owner, and its Proposed line.

    new --title T --stands S --choice C --option "L: E" ... --recommend R [--report P]

Appends `## N. T` to the OPEN-QUESTIONS.md beside the ledger, before
`## Decided without asking` when that heading exists, trailing text after it
allowed, with four bold-labelled paragraphs, an optional **Report.** paragraph
and an empty **Your answer:** line. The third label holds the options, one
bullet each, the first marked ` (Recommended)`. Then appends `N. **T.** <the
recommendation's first sentence> (proposed YYYY-MM-DD; OPEN-QUESTIONS.md)`
under `## Proposed`, creating that section before `## Superseded` when it is
absent; a title ending in `?` or `!` takes no period, and the first sentence
runs past `e.g.`, `i.e.`, `etc.` and `vs.`. N is one more than the highest
number in the ledger, its `N.` lines below the legacy marker included, and in
OPEN-QUESTIONS.md. The read, the number and both writes run
under `.new.lock` beside the ledger, and both files are written or neither is.
An empty part, a choice not ending in `?`, a count of options outside 2 to 4,
a label over five words (the first over four, since it takes ` (Recommended)`),
empty, holding `(Recommended)` or labelled "Other", an empty effect, a sixth
open question, or a title the ledger's lint cannot take, writes nothing.
"""

import datetime
import os
import re

from .common import Refusal, commit_texts, held, read_text
from .ledger import (LEGACY, PROPOSED, SUPERSEDED, bold_title, check_entry, display, parse,
                     section_of)
from .questions import (ANSWERED, ANSWERED_LINE, DECIDED, LABELS, OPEN_CAP, OPTIONS_MAX,
                        OPTIONS_MIN, RECOMMENDED)
from . import questions as questions_file

__all__ = ["cmd_new", "question", "insert_question", "insert_proposed", "next_number",
           "parse_options", "option_lines", "QUESTIONS", "FRESH", "PARTS", "LOCK",
           "NEW_WAIT"]

QUESTIONS = questions_file.NAME
# The lock beside the ledger that the read, the number and both writes run under
# (ADV6-8, ADV11-4); a live holder is waited on up to NEW_WAIT seconds.
LOCK = ".new.lock"
NEW_WAIT = 5.0
FRESH = "# Decisions for the owner\n\n%s\n" % DECIDED
# (argument, the bold label its paragraph opens with) for the three prose parts
PARTS = (("stands", LABELS[0]), ("choice", LABELS[1]), ("recommend", LABELS[3]))
# AskUserQuestion advises a label within five words (design d18 section 1.1); the
# first takes ` (Recommended)`, so it holds four (d-n2 item 7). AskUserQuestion adds
# "Other" itself, so no option takes that label.
LABEL_WORDS, FIRST_LABEL_WORDS = 5, 4
OTHER = "other"
# Punctuation and emphasis around a label, dropped before it meets OTHER (d-n2 fix round N2).
AROUND = re.compile(r"^[\W_]+|[\W_]+$")
QUESTION = re.compile(r"^## (\d+)\.\s")
# An entry line below the legacy marker, which the parser does not read (d-n2 item 2).
LEGACY_ENTRY = re.compile(r"^(\d+)\.\s")
# The first sentence: it ends at `.`, `!` or `?` before a space or the end, but
# not at the period of `e.g.`, `i.e.`, `etc.` or `vs.` (d-n3 item 2). `ask`'s
# selector takes it too.
SENTENCE = re.compile(r"^(.+?(?:[!?]|(?<!\be\.g)(?<!\bi\.e)(?<!\betc)(?<!\bvs)\.))(?=\s|$)",
                      re.IGNORECASE)


def today():
    return datetime.date.today().isoformat()


def clean(text):
    """`text` on one line: every run of whitespace one space."""
    return " ".join((text or "").split())


def legacy_numbers(ledger_text):
    """The numbers of the `N.` lines below the legacy marker."""
    lines = ledger_text.splitlines()
    marker = next((i for i, l in enumerate(lines) if l.strip() == LEGACY), len(lines))
    return [int(m.group(1)) for m in map(LEGACY_ENTRY.match, lines[marker + 1:]) if m]


def next_number(ledger, questions_text, ledger_text=""):
    """One more than the highest number in the ledger (its legacy part read from
    `ledger_text`), the open questions and the Answered lines, so an answered
    number stays retired."""
    numbers = [e.number for e in ledger.entries if e.number is not None]
    numbers += legacy_numbers(ledger_text)
    numbers += [int(m.group(1)) for m in map(QUESTION.match, questions_text.splitlines()) if m]
    answered = questions_file.parse(questions_text).answered
    numbers += [int(m.group(1)) for m in (ANSWERED_LINE.match(t) for _n, t in answered) if m]
    return max(numbers, default=0) + 1


def parse_options(raw):
    """[(label, effect)] from each `Label: effect`, split at the first `: `; a
    Refusal naming the first option that breaks the shape."""
    if not OPTIONS_MIN <= len(raw) <= OPTIONS_MAX:
        raise Refusal("new: %d option(s); `new` takes %d to %d options; nothing written"
                      % (len(raw), OPTIONS_MIN, OPTIONS_MAX))
    options = []
    for item in raw:
        label, _, effect = item.partition(": ")
        label, effect = clean(label), clean(effect)
        label = label[:-1] if label.endswith(".") else label
        if not label:
            problem = "empty label"
        elif "(recommended)" in label.lower():
            problem = "a label may not hold (Recommended); the first option is the recommendation"
        elif AROUND.sub("", label).lower() == OTHER:
            problem = 'AskUserQuestion adds "Other" itself; name the option for what it does'
        elif not options and len(label.split()) > FIRST_LABEL_WORDS:
            problem = "a first label over four words; ` (Recommended)` follows it"
        elif len(label.split()) > LABEL_WORDS:
            problem = "a label over five words"
        elif not effect:
            problem = "empty effect; write `Label: effect`"
        elif label.lower() in (l.lower() for l, _e in options):
            problem = "the same label as another option, ignoring case"
        else:
            options.append((label, effect))
            continue
        raise Refusal("new: option %r: %s; nothing written" % (item, problem))
    return options


def option_lines(options):
    """The bullets under the third label, the first marked ` (Recommended)`."""
    return "\n".join("- **%s%s.** %s" % (label, RECOMMENDED if i == 0 else "", effect)
                     for i, (label, effect) in enumerate(options))


def open_count(questions_text):
    return len(questions_file.parse(questions_text).blocks)


def question(number, title, parts, options, report=None):
    """The question's text: its heading, the four parts, the report, the answer line."""
    pieces = ["## %d. %s" % (number, title),
              "**%s** %s" % (LABELS[0], parts["stands"]),
              "**%s** %s" % (LABELS[1], parts["choice"]),
              "**%s**\n\n%s" % (LABELS[2], option_lines(options)),
              "**%s** %s" % (LABELS[3], parts["recommend"])]
    if report:
        pieces.append("**Report.** %s" % report)
    pieces.append("**Your answer:**")
    return "\n\n".join(pieces) + "\n"


def insert_question(text, written):
    """`text` with `written` before `## Decided without asking` or `## Answered`,
    else at the end."""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if questions_file.is_decided(line) or line.rstrip() == ANSWERED:
            before, after = "".join(lines[:i]).rstrip("\n"), "".join(lines[i:])
            return (before + "\n\n" if before else "") + written + "\n" + after
    return (text.rstrip("\n") + "\n\n" if text.strip() else "") + written


def insert_proposed(text, line):
    """`text` with `line` last under `## Proposed`, the section made when absent;
    above the legacy marker when the ledger holds one (L4)."""
    lines = text.splitlines(keepends=True)
    marker = next((i for i, l in enumerate(lines) if l.strip() == LEGACY), None)
    if marker is not None:
        above = insert_proposed("".join(lines[:marker]).rstrip("\n") + "\n", line)
        return above + "\n" + "".join(lines[marker:])
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    heads = [(i, section_of(l.rstrip()[3:])) for i, l in enumerate(lines)
             if l.startswith("## ")]
    proposed = [i for i, name in heads if name == PROPOSED]
    if proposed:
        start = proposed[0]
        end = next((i for i, _ in heads if i > start), len(lines))
        last = max(i for i in range(start, end) if lines[i].strip())
        return "".join(lines[:last + 1] + ["\n", line + "\n"] + lines[last + 1:])
    superseded = [i for i, name in heads if name == SUPERSEDED]
    if superseded:
        at = superseded[0]
        gap = ["\n"] if at > 0 and lines[at - 1].strip() else []
        return "".join(lines[:at] + gap + ["## %s\n" % PROPOSED, "\n", line + "\n", "\n"]
                       + lines[at:])
    return "".join(lines).rstrip("\n") + "\n\n## %s\n\n%s\n" % (PROPOSED, line)


def proposed_line(number, heading, sentence):
    """The Proposed line for `number`, when the ledger's lint takes it with `heading`
    as its title; else a Refusal, before anything is written (F1)."""
    rest = "%s %s (proposed %s; %s)" % (bold_title(heading), sentence, today(), QUESTIONS)
    problems = []
    if check_entry(PROPOSED, number, rest, problems, 1) != heading or problems:
        raise Refusal("new: the ledger's lint cannot take the title %r (it may hold a single "
                      "`*` but not `**`, and needs text before its period); nothing written"
                      % heading)
    return "%d. %s" % (number, rest)


def cmd_new(args, path, out, err):
    title = clean(args.title)
    parts = {name: clean(getattr(args, name)) for name, _ in PARTS}
    empty = ["--title"] if not title else []
    empty += ["--%s" % name for name, _ in PARTS if not parts[name]]
    report = None
    if args.report is not None:
        report = clean(args.report)
        if not report:
            empty.append("--report")
    if empty:
        raise Refusal("new: empty part: %s; nothing written" % ", ".join(empty))
    if not parts["choice"].endswith("?"):
        raise Refusal("new: the choice must end in `?`; nothing written")
    options = parse_options(args.options or [])
    heading = title[:-1] if title.endswith(".") else title
    sentence = SENTENCE.match(parts["recommend"])
    sentence = sentence.group(1) if sentence else parts["recommend"]
    proposed_line(0, heading, sentence)
    questions = os.path.join(os.path.dirname(path), QUESTIONS)
    with held(os.path.join(os.path.dirname(path), LOCK), NEW_WAIT, err):
        ledger_text = read_text(path)
        old_questions = read_text(questions) if os.path.exists(questions) else FRESH
        if open_count(old_questions) >= OPEN_CAP:
            raise Refusal("new: five questions are open in %s; ask them before a sixth; "
                          "nothing written" % display(questions))
        number = next_number(parse(ledger_text), old_questions, ledger_text)
        line = proposed_line(number, heading, sentence)
        commit_texts([(questions, insert_question(old_questions,
                                                  question(number, title, parts, options,
                                                           report))),
                      (path, insert_proposed(ledger_text, line))])
    out.write("new: %d, `## %d. %s` in %s and a Proposed line in %s\n"
              % (number, number, title, display(questions), display(path)))
    return 0
