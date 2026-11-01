"""`answer`: the owner's answer to question N, recorded (design d18 section 1.2).

    answer N (--pick L | --other T) --source S [--text P]
           (--area A | --amends M [--shorter] | --no-entry) [--into PATH]

`--pick` matches an option's label, ignoring case and ` (Recommended)`;
`--other` carries the owner's free text, restated. With `--area A` entry N is
written last under the `###` heading A names as `show --area` resolves it (an
exact name, else a unique prefix, a leading "The" left out of either; the headings
below the legacy marker do not count, and `Every session` matches only whole):
A is stripped of spaces and leading `#`s, a newline in it and two prefix matches
are refused,
a name no heading matches is a new `### A`, last under `## In force`, and the
success line names the heading. The title takes a period unless it ends in `?`
or `!`. `--amends M` replaces entry M's paragraph with `--text`, the whole
paragraph in force after the answer, adds to its tail an amendment and prints
`replaced:` with the old paragraph; an entry whose tail is missing or does not
open with a date is refused, and a paragraph under half the old one's length
is refused unless `--shorter`, which is valid only with `--amends`; `--no-entry`
writes no entry. One of the three is required: argparse refuses with exit 2.
`--text` is the body only, in both modes (D22): `answer` writes the bold title
and the `(DATE; source)` tail, and `--amends` keeps M's own, so a `--text` that
opens with a bold title or ends in a dated tail is refused. Every run removes
question N and its Proposed line and adds `- N. Title: LABEL (DATE; S)` under `## Answered`. The
run holds `.new.lock`, lints both texts (an open count over the cap, which the
answer lowers, is no refusal), and writes both files or neither;
then it rewrites the CLAUDE.md block, beside the ledger or at `--into`, when
that file holds the GENERATED markers; a target that is the ledger itself is
refused with exit 2 before anything is written. Once both files are written the answer
stands: a block that cannot be rewritten is a warning on stderr naming the
`agentik decisions render` command, with the `--ledger` and `--into` the answer used,
and the exit stays 0.
"""

import os
import shlex

from . import ask, questions
from .common import Refusal, commit_texts, held, read_text, write_text
from .ledger import (DATE, EVERY_SESSION, IN_FORCE, LEGACY, PROPOSED, TITLED, bold_title, display,
                     final_parenthetical, load, parse, repeats)
from .lookup import pick_area
from .render import BEGIN, END, TARGET, apply, block, is_ledger

__all__ = ["cmd_answer", "insert_entry", "amend_entry", "drop_line"]

# D22: how a refusal names each part of the shape a `--text` repeats.
REFUSED = {"title": "opens with a bold title", "tail": "ends in a (date; source) tail"}


def gapped(lines, last, new):
    """`lines` with `new` after index `last`, a blank line before it."""
    if not lines[last].endswith("\n"):
        lines[last] += "\n"
    return lines[:last + 1] + ["\n"] + new + lines[last + 1:]


def insert_entry(text, ledger, area, line):
    """`text` with `line` last under `### area` (its name ignoring case), else under a
    new `### area`, last under `## In force`."""
    lines = text.splitlines(keepends=True)
    stops = [i for i, l in enumerate(lines) if l.startswith("#") or l.strip() == LEGACY]
    found = next((a for a in ledger.areas if a.name.lower() == area.lower()), None)
    if found:
        start = found.line - 1
        stop = next((i for i in stops if i > start), len(lines))
        last = max(i for i in range(start, stop) if lines[i].strip())
        return "".join(gapped(lines, last, [line + "\n"]))
    head = next((i for i, l in enumerate(lines) if l.startswith("## ")
                 and l[3:].strip().lower() == IN_FORCE.lower()), None)
    if head is None:
        raise Refusal("answer: the ledger has no `## In force`; nothing written")
    stop = next((i for i in stops if i > head and not lines[i].startswith("### ")), len(lines))
    last = max(i for i in range(head, stop) if lines[i].strip())
    return "".join(gapped(lines, last, ["### %s\n" % area, "\n", line + "\n"]))


def amend_entry(text, ledger, number, paragraph, amendment, shorter=False):
    """(`text` with entry `number`'s paragraph replaced, the old paragraph); its tail
    gains `amendment` after what it holds, so an earlier amendment is never dropped.
    An entry whose tail is missing or does not open with a date is refused, and a
    `paragraph` under half the old one's length, both after `ask.clean`, is refused
    unless `shorter`."""
    entry = next((e for e in ledger.entries if e.section == IN_FORCE and e.number == number),
                 None)
    if entry is None:
        raise Refusal("answer: no entry %d in force to amend; nothing written" % number)
    titled = TITLED.match(entry.body)
    if titled is None:
        raise Refusal("answer: entry %d has no bold title to keep; nothing written" % number)
    tail = final_parenthetical(entry.body)
    if tail is None or not DATE.match(tail.lstrip()):
        # d-n3 item 11 (2a F7, D19): no `(; amended DATE, ...)`.
        raise Refusal("answer: entry %d has no tail that opens with a date, so no amendment "
                      "can follow it; nothing written" % number)
    old = (titled.group(3) or "").rstrip()
    old = old[:-(len(tail) + 2)].rstrip()
    new_len, old_len = len(ask.clean(paragraph)), len(ask.clean(old))
    if 2 * new_len < old_len and not shorter:
        raise Refusal("answer: the new paragraph of entry %d is %d characters, under half the "
                      "old one's %d; --text is the whole paragraph in force after the answer; "
                      "the old paragraph follows; pass --shorter to cut it; nothing written:\n%s"
                      % (number, new_len, old_len, old))
    lines = text.splitlines(keepends=True)
    lines[entry.line - 1] = "%d. **%s** %s (%s; amended %s)\n" % (
        number, titled.group(1), paragraph, tail, amendment)
    return "".join(lines), old


def drop_line(text, index):
    """`text` without line `index` and the blank line before it."""
    lines = text.splitlines(keepends=True)
    start = index - 1 if index > 0 and not lines[index - 1].strip() else index
    return "".join(lines[:start] + lines[index + 1:])


def pick(block, args):
    if args.other is not None:
        other = ask.clean(args.other)
        if not other:
            raise Refusal("answer: empty --other; nothing written")
        return "Other: " + other
    wanted = ask.clean(args.pick).lower()
    marker = questions.RECOMMENDED.lower()
    wanted = wanted[:-len(marker)] if wanted.endswith(marker) else wanted
    for label, _marked, _effect in block.options:
        if label.lower() == wanted:
            return label
    raise Refusal("answer: question %d has no option %r; its options are %s; nothing written"
                  % (block.number, args.pick, ", ".join(l for l, _m, _e in block.options)))


def cmd_answer(args, path, out, err):
    number, source = args.number, ask.clean(args.source)
    text = ask.clean(args.text) if args.text is not None else ""
    if args.area is not None and ("\n" in args.area or "\r" in args.area):
        raise Refusal("answer: --area holds a newline; name one heading; nothing written")
    area = ask.clean(args.area).lstrip("#").strip() if args.area is not None else None
    if not source:
        raise Refusal("answer: empty --source; nothing written")
    if area is not None and not area:
        raise Refusal("answer: empty --area; nothing written")
    if not (area or args.amends is not None or args.no_entry):
        raise Refusal("answer: name --area A, --amends M or --no-entry; nothing written")
    if not args.no_entry and not text:
        raise Refusal("answer: --text is required unless --no-entry; nothing written")
    if args.shorter and args.amends is None:
        raise Refusal("answer: --shorter is valid only with --amends; nothing written")
    repeated = [] if args.no_entry else repeats(text)
    if repeated:
        raise Refusal("answer: --text %s; --text is the body only: answer writes the bold "
                      "title and the (date; source) tail, and --amends keeps the entry's own; "
                      "pass the text between them; nothing written"
                      % " and ".join(REFUSED[part] for part in repeated))
    target = os.path.abspath(os.path.expanduser(args.into)) if args.into else \
        os.path.join(os.path.dirname(path), TARGET)
    if is_ledger(target, path):
        raise Refusal("answer: the target %s is the ledger itself; nothing written"
                      % display(target))
    path_q = os.path.join(os.path.dirname(path), ask.QUESTIONS)
    date = ask.today()
    with held(os.path.join(os.path.dirname(path), ask.LOCK), ask.NEW_WAIT, err):
        if not os.path.exists(path_q):
            raise Refusal("answer: no %s beside the ledger" % display(path_q))
        ledger_text, old_q = read_text(path), read_text(path_q)
        found = next((b for b in questions.parse(old_q).blocks if b.number == number), None)
        if found is None:
            raise Refusal("answer: no open question %d in %s" % (number, display(path_q)))
        label = pick(found, args)
        title = found.title[:-1] if found.title.endswith(".") else found.title
        ledger = parse(ledger_text)
        proposed = next((e for e in ledger.entries
                         if e.section == PROPOSED and e.number == number), None)
        new_ledger = drop_line(ledger_text, proposed.line - 1) if proposed else ledger_text
        cause = "the owner's answer to decision %d, %s" % (number, source)
        replaced = None
        if args.no_entry:
            done = "no entry"
        elif args.amends is not None:
            new_ledger, replaced = amend_entry(new_ledger, parse(new_ledger), args.amends, text,
                                               "%s, %s" % (date, cause), args.shorter)
            done = "entry %d amended" % args.amends
        else:
            line = "%d. %s %s (%s; %s)" % (number, bold_title(title), text, date, cause)
            current = parse(new_ledger)
            try:
                found_area = pick_area(current, area, "answer", legacy=False, absent=True,
                                       whole=(EVERY_SESSION.lower(),))
            except Refusal as exc:
                raise Refusal("%s; nothing written" % exc)
            heading = found_area.name if found_area else area
            new_ledger = insert_entry(new_ledger, current, heading, line)
            done = "entry %d under `### %s`" % (number, heading)
        new_q = questions.add_answered(questions.remove_block(old_q, found),
                                       "- %d. %s: %s (%s; %s)" % (number, title, label, date,
                                                                   source))
        problems = [(display(path), n, m) for n, m in parse(new_ledger).problems]
        # An answer removes one block, so it lowers the open count: a count over the cap
        # (left by a merge) is the old file's problem, not this answer's, and never refuses it.
        over = "questions open; the cap is %d" % questions.OPEN_CAP
        problems += [(display(path_q), n, m) for n, m in questions.parse(new_q).problems
                     if over not in m]
        if problems:
            raise Refusal("answer: the result fails the lint; nothing written:\n" + "\n".join(
                "%s:%d: %s" % p for p in problems))
        commit_texts([(path_q, new_q), (path, new_ledger)])
    out.write("answer: %d, %s; %s in %s\n" % (number, label, done, display(path)))
    if replaced is not None:
        out.write("replaced: %s\n" % replaced)
    try:
        rewrite_block(path, target, out, err)
    except Refusal as exc:
        # d18 1a obs: both files are written, so the answer stands; the block is a warning.
        command = "agentik decisions render"
        for flag, value in (("--ledger", getattr(args, "ledger", None)), ("--into", args.into)):
            if value:
                command += " %s %s" % (flag, shlex.quote(value))
        err.write("answer: warning: the answer is written, but the block in %s is not: %s; "
                  "`%s` rewrites it\n" % (display(target), exc, command))
    return 0


def rewrite_block(path, target, out, err):
    """The CLAUDE.md block at `target` rewritten from the ledger at `path`, when it has markers."""
    old = read_text(target) if os.path.exists(target) else ""
    lines = [line.strip() for line in old.splitlines()]
    if BEGIN not in lines or END not in lines:
        err.write("answer: %s holds no GENERATED markers; the block is left as it is\n"
                  % display(target))
        return
    new = apply(old, block(load(path), path, target), display(target))
    if new != old:
        write_text(target, new)
        out.write("answer: rewrote the block in %s\n" % display(target))
