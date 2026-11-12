"""`answer`: the owner's answer to question N, recorded (design d18 section 1.2).

    answer N (--pick L | --other T) --source S [--text P | --add S]
           (--area A | --amends M [--shorter] [--move-to A] | --no-entry) [--into PATH]
           [--every-turn] [--preview]

`--pick` matches an option's label, ignoring case and ` (Recommended)`;
`--other` carries the owner's free text, restated. The owner's typed text T, the
rest of the block's **Your answer:** line and every non-blank line under it, holds
both (d28): T that names an option (its label once `*` and backticks at either end,
case, a trailing ` (Recommended)` and a period are dropped) refuses `--other` and a
`--pick` of another option; any other T refuses `--pick` and prints T, and under
`--other X` the label is `Other: X; the owner's line: T` (`Other: X` when X is T,
ignoring case). T never enters the ledger: `--text` stays the caller's. A line no
part of its block takes (d30: a part is a label's or the **Report.** bold line and
the lines under it to a blank, an option line under the third label, or the
**Your answer:** line and all under it) refuses `--pick`, after an unknown one, and
`--other X` takes it whatever T names, as `Other: X; the owner's line: W`, W those
lines then T. Under `.new.lock`, once block N is found, `answer` reads it from
git's HEAD (d35): a non-blank line above its **Your answer:** line that HEAD's copy
lacks, runs of spaces counted as one, is the owner's; it refuses `--pick` after the
stray lines, and W takes it after them, each line once. With no copy of question N
in HEAD (no commit there, HEAD lacks the file or the question, or git cannot read
it), `--pick` and `--other` exit 2 and write nothing: read the block first, since a
commit makes every line in it the block's own and `--other`'s text then carries the
owner's words, and commit the file. With `--area A` entry N is
written last under the `###` heading A names as `show --area` resolves it (an
exact name, else a unique prefix, a leading "The" left out of either; the headings
below the legacy marker do not count, and `Every session` matches only whole):
A is stripped of spaces and leading `#`s, a newline in it and two prefix matches
are refused,
a name no heading matches is a new `### A`, last under `## In force`, and the
success line names the heading. The title takes a period unless it ends in `?`
or `!`. At 25 entries in force `--area` is refused first, naming the ways out: a
line under `## Superseded`, `--amends M` or `--no-entry`. `--amends M` replaces
entry M's paragraph with `--text`, the whole paragraph in force after the answer,
adds to its tail an amendment and prints `replaced:` with the old paragraph; an
entry whose tail is missing or does not open with a date is refused, and a
`--text` that drops a sentence of it, one not held whole, is refused and listed
unless `--shorter`, which is valid only with `--amends`. `--add S` in place of
`--text`, under `--amends M` alone, appends S to the paragraph as it stands and
prints no `replaced:`. `--no-entry` writes no entry. One of the three is required: argparse refuses with exit 2.
`--text` is the body only, in both modes (D22): `answer` writes the bold title
and the `(DATE; source)` tail, and `--amends` keeps M's own, so a `--text` that
opens with a bold title or ends in a dated tail is refused, as is a `--text` or
`--add` holding a `(` that opens with a date and never closes. Every run removes
question N and its Proposed line and adds `- N. Title: LABEL (DATE; S)` under `## Answered`. The
run holds `.new.lock`, lints both texts (an open count over the cap, which the
answer lowers, is no refusal), and writes both files or neither;
then it rewrites the CLAUDE.md block, beside the ledger or at `--into`, when
that file holds the GENERATED markers; a target that is the ledger itself is
refused with exit 2 before anything is written. Once both files are written the answer
stands: a block that cannot be rewritten is a warning on stderr naming the
`agentik decisions render` command, with the `--ledger` and `--into` the answer used,
and the exit stays 0.

The block is loaded on every turn (d32), so the rewrite's line names its growth,
`answer: rewrote the block in PATH: X B to Y B, +D B; the block is loaded on every
turn`. An answer that touches `Every session`, by `--amends M` with M in force there
or an `--area` that resolves to it, and makes larger the block render would write at
the target, markers or none, is refused with exit 2 before anything is written, once
the lint has passed (a result that fails the lint is refused on the lint): the
refusal names the bytes, and the entry's tail note's share when the note grows. The
way out is an entry outside `Every session`, which the block lists by title only, or
`--every-turn`, valid only with `--area` or `--amends`. Same size or smaller passes.

d36: `Every session of the tree` answers `--area` only by its whole name, as `Every
session` does. `--move-to A`, valid only with `--amends M`, puts the amended entry last
under the heading A names, resolved as `--area` is. An answer that touches the tree's
section and makes the folder's file larger is refused as the block's growth is, and
`--every-turn` lets it through; the folder's file is never written here: a stderr line
names `render --scope tree` when the section changed.

d37: `--preview` makes every check and refusal above, under the same lock, then prints
the entry as it would be written, the Answered line, the unified diff `render` would
then make in the repo's file and, when the tree's section changes, in the folder's
file, and each file's loaded bytes now and after beside its ceiling; it writes nothing.
A file render would refuse, by the checks its own path makes (`render --scope tree`'s
for the folder's file), or cannot read gets render's reason and no diff, exit 0 (d37 r1).
"""

import collections
import difflib
import io
import os
import shlex
import subprocess
import types

from . import ask, questions
from .common import (GIT_TIMEOUT, Refusal, bounded, commit_texts, disk_text, held, keeps_crlf,
                     on_disk, read_text, write_text)
from .ledger import (DATE, EVERY_SESSION, IN_FORCE, IN_FORCE_CAP, LEGACY, PROPOSED, TITLED,
                     TREE_SESSION, bold_title, display, dropped, final_parenthetical, folded,
                     is_tree, load, parse, repeats, sentences, unclosed)
from .lookup import pick_area
from .render import (BEGIN, END, TARGET, apply, block, cmd_tree, growth, is_ledger, tail_note,
                     tree_file)
from .tree import ceiling_for, loaded_bytes

__all__ = ["cmd_answer", "insert_entry", "amend_entry", "drop_line", "move_entry"]

# d36: the two sections an answer reaches only by their whole names
WHOLE = (EVERY_SESSION.lower(), TREE_SESSION.lower())

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


def amend_entry(text, ledger, number, paragraph, amendment, shorter=False, add=None):
    """(`text` with entry `number`'s paragraph replaced, the old paragraph); its tail
    gains `amendment` after what it holds, so an earlier amendment is never dropped.
    An entry whose tail is missing or does not open with a date is refused, and a
    `paragraph` that does not hold each sentence of the old one whole is refused
    unless `shorter` (d30 ruling 1). With `add`, the paragraph is the old one, a
    space and `add`, and the old paragraph returned is None (d30 ruling 2)."""
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
    if add is not None:
        paragraph, replaced = ("%s %s" % (old, add)).strip(), None
    else:
        lost, replaced = dropped(ask.clean(old), paragraph), old
        if lost and not shorter:
            raise Refusal("answer: the new paragraph of entry %d drops %d of its %d sentences; "
                          "--text is the whole paragraph in force after the answer; pass --add "
                          "with the new sentences alone to keep the paragraph and append them, "
                          "or --shorter to let these go; nothing written:\n%s"
                          % (number, len(lost), len(sentences(ask.clean(old))), "\n".join(lost)))
    lines = text.splitlines(keepends=True)
    lines[entry.line - 1] = "%d. **%s** %s (%s)\n" % (
        number, titled.group(1), paragraph, folded(tail, amendment))
    return "".join(lines), replaced


def move_entry(text, number, area):
    """`text` with entry `number`'s line in force taken out and put last under `### area`
    (d36: `--amends M --move-to A`); `area` is a heading the ledger holds, or a new one."""
    ledger = parse(text)
    entry = next(e for e in ledger.entries if e.section == IN_FORCE and e.number == number)
    if (entry.area or "").lower() == area.lower():
        return text
    rest = drop_line(text, entry.line - 1)
    return insert_entry(rest, parse(rest), area, entry.text)


def drop_line(text, index):
    """`text` without line `index` and the blank line before it."""
    lines = text.splitlines(keepends=True)
    start = index - 1 if index > 0 and not lines[index - 1].strip() else index
    return "".join(lines[:start] + lines[index + 1:])


def normal(text):
    """`text` lowercased, with `*` and backticks at either end, a trailing ` (Recommended)`
    and a period before or after it dropped until none is left (d28 ruling)."""
    marker, last = questions.RECOMMENDED.strip().lower(), None
    text = text.lower()
    while text != last:
        last = text
        text = text.strip("*` ").rstrip(".").rstrip()
        text = text[:-len(marker)] if text.endswith(marker) else text
    return text


def named(block, typed):
    """The option labels `typed` names: the one it equals ignoring case, else each whose
    normal form is its normal form, so two labels one normal form apart are both named
    (d28 ruling; review r1 F1, F2)."""
    labels = [label for label, _marked, _effect in block.options]
    exact = [label for label in labels if label.lower() == typed.lower()]
    return exact or [label for label in labels if normal(label) == normal(typed)]


# a hook's GIT_DIR=.git or a caller's GIT_DIR naming another repository would make HEAD
# that repository's, so `head_block`'s git children run without them (d35 round 1)
REPO_VARIABLES = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
                  "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE")


def head_block(path_q, number):
    """Question `number`'s block as git's HEAD holds the questions file, read as
    `render.head_holds` reads one: in the real path's directory, each git child under
    GIT_TIMEOUT; a name HEAD lacks is read as the one HEAD tracks there equal to it under
    casefold, when there is one alone; git's repository variables are dropped from each
    child, so HEAD is the repository that holds the file. With no copy of it, a Refusal
    naming why, since `answer` then cannot tell what the owner typed into the block (d35
    ruling 5)."""
    real = os.path.realpath(path_q)
    where, name = os.path.dirname(real), os.path.basename(real)
    text, why = None, None
    env = {key: value for key, value in os.environ.items() if key not in REPO_VARIABLES}

    def blob_of(sha, tracked):
        return subprocess.run(["git", "cat-file", "blob", "%s:./%s" % (sha, tracked)],
                              cwd=where, env=env, capture_output=True, timeout=GIT_TIMEOUT)

    try:
        code, out = bounded(["git", "rev-parse", "--verify", "-q", "HEAD^{commit}"],
                            GIT_TIMEOUT, cwd=where, env=env)
        sha = out.strip()
        if code != 0 or not sha:
            why = "no commit to read there"
        else:
            blob = blob_of(sha, name)
            if blob.returncode != 0:
                # a case-blind disk opens the file git tracks as open-questions.md: the
                # one name HEAD holds there equal to `name` under casefold is the file's
                code, out = bounded(["git", "ls-tree", "--name-only", "-z", "%s:./" % sha],
                                    GIT_TIMEOUT, cwd=where, env=env)
                same = [tracked for tracked in out.split("\0") if code == 0 and tracked
                        and tracked.casefold() == name.casefold()]
                if len(same) == 1:
                    blob = blob_of(sha, same[0])
            if blob.returncode != 0:
                why = "HEAD does not hold %s" % name
            else:
                # the line ends `read_text` reads, so a CRLF blob parses as the file does
                text = blob.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError) as exc:
        why = "git cannot read it: %s" % exc
    if why is None:
        found = next((b for b in questions.parse(text).blocks if b.number == number), None)
        if found is not None:
            return found
        why = "HEAD's %s holds no question %d" % (name, number)
    raise Refusal("answer: git holds no copy of question %d (%s), so answer cannot tell what "
                  "was typed into its block; read the block first: a commit makes every line "
                  "in it the block's own, so words the owner typed there are carried in "
                  "--other's text; then commit %s and run this again; nothing written"
                  % (number, why, name))


def since(block, base):
    """The owner's lines (d35 ruling 2): each non-blank line of `block` above its
    **Your answer:** line that `base`, HEAD's copy of the block, lacks, in order, stripped.
    Runs of spaces count as one, and each line of `base` holds one line of `block`; a line
    deleted since the commit is none. The answer line and what is under it stay T (d28)."""
    held_lines = collections.Counter(" ".join(line.split()) for line in base.text.splitlines())
    lines = []
    for line in block.text.splitlines():
        if line.startswith(questions.ANSWER):
            break
        key = " ".join(line.split())
        if not key:
            continue
        if held_lines[key] > 0:
            held_lines[key] -= 1
        else:
            lines.append(line.strip())
    return lines


def pick(block, args, lacks=()):
    """The label of the answer, `--pick`'s option or `Other: X`, held to the owner's
    typed text T, `block.answer` (d28): T that names an option takes only `--pick` of
    it; any other T refuses `--pick` and stays in `--other`'s label. An unknown
    `--pick` keeps its own refusal. A block with stray lines, text no part of it takes,
    refuses `--pick` and puts them before T in `--other`'s label (d30 ruling 5). So do
    `lacks`, the block's lines HEAD's copy of it lacks, after the stray lines, each line
    once (d35 rulings 3 and 4)."""
    typed, stray = block.answer or "", list(block.stray)
    lacks = [line for line in lacks if line not in stray]
    options = named(block, typed) if typed and not stray and not lacks else []
    option = options[0] if len(options) == 1 else None
    names = ("answer: question %d's %s line names the option `%s`; pass --pick with it; "
             "nothing written" % (block.number, questions.ANSWER, option))
    twins = ("answer: question %d's %s line could name any of %s; ask the owner to type one "
             "label as it stands; nothing written"
             % (block.number, questions.ANSWER, ", ".join("`%s`" % o for o in options)))
    if args.other is None:
        label = pick_label(block, args.pick)
        if label is None:
            raise Refusal("answer: question %d has no option %r; its options are %s; nothing "
                          "written" % (block.number, args.pick,
                                       ", ".join(l for l, _m, _e in block.options)))
        if stray:
            raise Refusal("answer: question %d holds text no part of its block takes; pass "
                          "--other, which keeps it in the Answered line, or join it to its "
                          "part; nothing written:\n%s" % (block.number, "\n".join(stray)))
        if lacks:
            raise Refusal("answer: question %d's block holds lines that HEAD's copy of it "
                          "lacks; pass --other, which keeps them in the Answered line, or, "
                          "when they are the block's own words, commit %s and run this "
                          "again; nothing written:\n%s"
                          % (block.number, ask.QUESTIONS, "\n".join(lacks)))
        if len(options) > 1:
            raise Refusal(twins)
        if typed and option is None:
            raise Refusal("answer: question %d's %s line says more than a label; pass "
                          "--other, which keeps the line; nothing written:\n%s"
                          % (block.number, questions.ANSWER, typed))
        if option is not None and label != option:
            raise Refusal(names)
        return label
    other = ask.clean(args.other)
    if not other:
        raise Refusal("answer: empty --other; nothing written")
    if len(options) > 1:
        raise Refusal(twins)
    if option is not None:
        raise Refusal(names)
    typed = " ".join(stray + lacks + ([typed] if typed else []))
    if typed and other.lower() != typed.lower():
        return "Other: %s; the owner's line: %s" % (other, typed)
    return "Other: " + other


def pick_label(block, wanted):
    """The option whose label is `wanted`, ignoring case and ` (Recommended)`, or None."""
    wanted = ask.clean(wanted).lower()
    marker = questions.RECOMMENDED.lower()
    wanted = wanted[:-len(marker)] if wanted.endswith(marker) else wanted
    return next((label for label, _marked, _effect in block.options
                 if label.lower() == wanted), None)


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
    move = getattr(args, "move_to", None)
    if move is not None:
        if args.amends is None:
            raise Refusal("answer: --move-to is valid only with --amends; nothing written")
        move = ask.clean(move).lstrip("#").strip()
        if not move or "\n" in move or "\r" in move:
            raise Refusal("answer: --move-to names one heading; nothing written")
    if area is not None and os.path.exists(path):
        count = len([e for e in parse(read_text(path)).entries if e.section == IN_FORCE])
        if count >= IN_FORCE_CAP:
            # d30 ruling 4: the cap refuses before the --text test, and names the ways out.
            raise Refusal("answer: %d entries are in force, the cap, so entry %d cannot join "
                          "them; the ways out: retire one (move its line under `## Superseded` "
                          "with a date and `replaced by`, `merged into` or `lapsed with`), fold "
                          "the answer into one with --amends M, or pass --no-entry; nothing "
                          "written" % (count, number))
    add = ask.clean(args.add) if args.add is not None else None
    if add is not None and (args.amends is None or args.text is not None or args.shorter
                            or not add):
        raise Refusal("answer: --add takes the place of --text under --amends, never with "
                      "--shorter, and is never empty; nothing written")
    if not args.no_entry and not text and add is None:
        raise Refusal("answer: --text is required unless --no-entry; nothing written")
    if args.shorter and args.amends is None:
        raise Refusal("answer: --shorter is valid only with --amends; nothing written")
    if getattr(args, "every_turn", False) and args.no_entry:
        raise Refusal("answer: --every-turn is valid only with --area or --amends; nothing "
                      "written")
    flag, text = ("--add", add) if add is not None else ("--text", text)
    if unclosed(text):
        raise Refusal("answer: %s holds a `(` that opens with a date and never closes, a piece "
                      "of a (date; source) tail; pass the text without it; nothing written"
                      % flag)
    repeated = [] if args.no_entry else repeats(text)
    if repeated:
        raise Refusal("answer: %s %s; %s is the body only: answer writes the bold "
                      "title and the (date; source) tail, and --amends keeps the entry's own; "
                      "pass the text between them; nothing written"
                      % (flag, " and ".join(REFUSED[part] for part in repeated), flag))
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
        # d35: the lines the owner typed are those HEAD's copy of block N lacks
        label = pick(found, args, since(found, head_block(path_q, number)))
        title = found.title[:-1] if found.title.endswith(".") else found.title
        ledger = parse(ledger_text)
        proposed = next((e for e in ledger.entries
                         if e.section == PROPOSED and e.number == number), None)
        new_ledger = drop_line(ledger_text, proposed.line - 1) if proposed else ledger_text
        cause = "the owner's answer to decision %d, %s" % (number, source)
        replaced, cut = None, None
        if args.no_entry:
            done = "no entry"
        elif args.amends is not None:
            amendment, before = "%s, %s" % (date, cause), parse(new_ledger)
            new_ledger, replaced = amend_entry(new_ledger, before, args.amends, text,
                                               amendment, args.shorter, add)
            # d31: the tail before, when form T2 cuts any of it.
            was = final_parenthetical(next(e.body for e in before.entries
                                           if e.section == IN_FORCE
                                           and e.number == args.amends))
            cut = was if folded(was, amendment) != "%s; amended %s" % (was, amendment) \
                else None
            done = "entry %d amended" % args.amends
            if move is not None:
                # d36: the amended entry, moved last under the heading --move-to names
                try:
                    found_area = pick_area(parse(new_ledger), move, "answer", legacy=False,
                                           absent=True, whole=WHOLE)
                except Refusal as exc:
                    raise Refusal("%s; nothing written" % exc)
                heading = found_area.name if found_area else move
                new_ledger = move_entry(new_ledger, args.amends, heading)
                done = "entry %d amended, under `### %s`" % (args.amends, heading)
        else:
            line = "%d. %s %s (%s; %s)" % (number, bold_title(title), text, date, cause)
            current = parse(new_ledger)
            try:
                found_area = pick_area(current, area, "answer", legacy=False, absent=True,
                                       whole=WHOLE)
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
        # d32 fold (F2): the lint first, so a refusal's way out never meets the lint
        if not getattr(args, "every_turn", False):
            every_turn(ledger_text, new_ledger, path, target, args.amends,
                       None if args.no_entry or (args.amends is not None and move is None)
                       else heading)
        if getattr(args, "preview", False):
            # d37: every check above has run; show the result and write nothing
            written = None if args.no_entry else next(
                e.text for e in parse(new_ledger).entries if e.section == IN_FORCE
                and e.number == (args.amends if args.amends is not None else number))
            out.write("answer --preview: %d, %s; %s in %s; nothing written\n"
                      % (number, label, done, display(path)))
            out.write("%s\n" % (written.rstrip() if written else "no entry"))
            out.write("answered: - %d. %s: %s (%s; %s)\n" % (number, title, label, date, source))
            if replaced is not None:
                out.write("replaced: %s\n" % replaced)
            if cut is not None:
                out.write("tail was: (%s)\n" % cut)
            preview(ledger_text, new_ledger, path, target, out)
            return 0
        commit_texts([(path_q, new_q), (path, new_ledger)])
    out.write("answer: %d, %s; %s in %s\n" % (number, label, done, display(path)))
    if replaced is not None:
        out.write("replaced: %s\n" % replaced)
    if cut is not None:
        out.write("tail was: (%s)\n" % cut)
    if tree_lines(parse(ledger_text)) != tree_lines(parse(new_ledger)):
        # d36: the folder's file is above the repo; answer leaves it to its own command
        err.write("answer: the tree's section changed; `agentik decisions render --scope tree"
                  "%s` rewrites the folder's file\n" % (
                      " --ledger %s" % shlex.quote(args.ledger)
                      if getattr(args, "ledger", None) else ""))
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


def tree_lines(ledger):
    """The text of each entry of the tree's section, in ledger order."""
    return [e.text for e in ledger.entries if is_tree(e)]


def preview(ledger_text, new_ledger, path, target, out):
    """d37 `--preview`: the diff `render` would make in the repo's file at `target` once
    the ledger is `new_ledger`, and in the folder's file when the tree's section changes;
    each file's loaded bytes now and after beside its ceiling. It writes nothing."""
    old, new = parse(ledger_text), parse(new_ledger)
    files = []
    try:
        # d37 r1 F2: a file render cannot read is said, as answer's warning says it
        was = read_text(target) if os.path.exists(target) else ""
        files.append((target, was, apply(was, block(new, path, target), display(target)),
                      False))
    except Refusal as exc:
        out.write("answer --preview: %s; render would refuse it, so no diff\n" % exc)
    if tree_lines(old) != tree_lines(new):
        try:
            # d37 r1 F1: render's own tree path makes its target checks, its output unshown
            cmd_tree(types.SimpleNamespace(into=None, lint=False, check=True,
                                           fold_tails=False), new, path, io.StringIO(),
                     io.StringIO(), False)
            folder, text = tree_file(new, path)
            files.append((folder, read_text(folder) if os.path.exists(folder) else "", text,
                          True))
        except Refusal as exc:
            out.write("answer --preview: %s; render would refuse it, so no diff\n" % exc)
    for name, before, after, tree in files:
        shown = display(name)
        if before == after:
            out.write("answer --preview: %s: render would change nothing\n" % shown)
        else:
            out.writelines(difflib.unified_diff(before.splitlines(keepends=True),
                                                after.splitlines(keepends=True),
                                                shown, shown + " (after the answer)"))
        figure, kind = ceiling_for(name, new, tree)
        now = loaded_bytes(name, before) if before else 0
        then = loaded_bytes(name, after)
        out.write("answer --preview: %s loads %s B now and %s B after, %s B; the ceiling for "
                  "%s is %s B%s\n" % (shown, "{:,}".format(now), "{:,}".format(then),
                                      "{:+,}".format(then - now), kind, "{:,}".format(figure),
                                      "; over by {:,} B".format(then - figure)
                                      if then > figure else ""))


def every_turn(ledger_text, new_ledger, path, target, amends, heading):
    """d32 and d36: refuse an answer that makes the repo's block larger under `Every
    session`, or the tree's file larger under `Every session of the tree`."""
    repo_block(ledger_text, new_ledger, path, target, amends, heading)
    old, new = parse(ledger_text), parse(new_ledger)
    touched = any(is_tree(e) and e.number == amends for e in old.entries) or \
        (heading is not None and heading.lower() == TREE_SESSION.lower())
    if not touched:
        return
    was = len(tree_file(old, path)[1].encode()) if any(is_tree(e) for e in old.entries) else 0
    now = len(tree_file(new, path)[1].encode()) if any(is_tree(e) for e in new.entries) else 0
    if now > was:
        raise Refusal("answer: this answer adds %d B to the tree's file, %d B to %d B, which "
                      "every session of the tree loads on every turn; put it in another "
                      "entry, or pass --every-turn; nothing written" % (now - was, was, now))


def repo_block(ledger_text, new_ledger, path, target, amends, heading):
    """d32: refuse an answer that makes the block larger when it touches `Every session`,
    by `--amends M` with M in force there or an `--area` that resolves to it (`heading`).
    The block is the one `render` would write at `target`, markers or none: the relay puts
    the same block in each child's prompt. The growth is the whole block's, the entry's
    tail note included, and the refusal names the note's share when it grows."""
    every = EVERY_SESSION.lower()
    old = parse(ledger_text)
    entry = next((e for e in old.entries if amends is not None and e.number == amends
                  and e.section == IN_FORCE and (e.area or "").lower() == every), None)
    if entry is None and (heading is None or heading.lower() != every):
        return
    new, crlf = parse(new_ledger), keeps_crlf(target)
    was = on_disk(block(old, path, target), crlf)
    now = on_disk(block(new, path, target), crlf)
    if now <= was:
        return
    note = ""
    if entry is not None:
        after = next((e for e in new.entries if e.number == amends and e.section == IN_FORCE),
                     None)
        grown = (len(tail_note(after.text).encode()) - len(tail_note(entry.text).encode())
                 if after is not None else 0)
        note = "; %d B of it is the entry's tail note" % grown if grown > 0 else ""
    raise Refusal("answer: this answer adds %d B to the block, %d B to %d B, which is loaded "
                  "on every turn; put it in an entry outside `Every session`, which the block "
                  "lists by title only, or pass --every-turn%s; nothing written"
                  % (now - was, was, now, note))


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
        was, crlf = disk_text(target), keeps_crlf(target)
        write_text(target, new)
        out.write("answer: rewrote the block in %s: %s\n" % (display(target),
                                                             growth(was, new, crlf)))
