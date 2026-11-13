"""`ask`: the open questions as AskUserQuestion calls (design d18 sections 1.1, 3).

    ask [N...]

Skips, with one warning each, a block whose **Your answer:** line is filled in
(`agentik decisions answer N` enters it first), a block the lint refuses, a block
with no base line or with more than one, whose lines cannot be told from the
owner's (d42), and a block that holds a line typed since `new` or `ask` wrote it
(d41: a line whose digest its base line lacks), so the owner's words are never
rendered over; it runs no git. Renders
the asked blocks once through respeak, outside the lock, then takes
`.new.lock`, reads both files again, and writes back each block whose text is
unchanged since the render and whose rendering kept its headings, numbers,
bold labels, option labels, the choice's `?`, a text in each prose part, and
no line outside a part; that block's Proposed line takes the new first
sentence of the recommendation. Under the same lock every asked block whose text
is unchanged since it was read leaves with its base line, computed from its text
as `ask` leaves it, with a render or without. Both files are written or neither. Then it
prints a JSON list of calls, at most four questions a call, built from the file
as it stands. With no respeak, a failed render, or a directory it cannot
write, the text stays, one warning goes to stderr and the exit is 0; so does a
base line that cannot be written when nothing was rendered. With no
N, every open question is asked.
"""

import json
import os
import re

from . import answer, ask, questions, speak
from .common import Refusal, commit_texts, held, read_text
from .ledger import PROPOSED, TITLED, display, final_parenthetical, parse

__all__ = ["cmd_ask", "payload", "question_of", "kept", "PER_CALL"]

PER_CALL = 4
BOLD = re.compile(r"^\*\*[^*]+\*\*")
NUMBER = re.compile(r"\d+")
WORD = re.compile(r"[a-z0-9]+(?:['.][a-z0-9]+)*")
# The parts a render may reword but never empty (d-n2 item 1).
PROSE = (questions.LABELS[0], questions.LABELS[1], questions.LABELS[3])


def first_sentence(text):
    found = ask.SENTENCE.match(text or "")
    return found.group(1) if found else (text or "")


def words(text):
    return " %s " % " ".join(WORD.findall(text.lower()))


def describe(effect, sentence):
    """An option's description: its effect, closed as a sentence, then the
    recommendation's first sentence when there is one; that sentence alone when
    it restates the effect, whole words compared (d-n2 item 10)."""
    effect = (effect or "").strip()
    sentence = (sentence or "").strip()
    if effect and sentence and words(effect).strip() and words(effect) in words(sentence):
        return sentence
    if effect and sentence and effect[-1] not in ".!?":
        effect += "."
    return " ".join(filter(None, [effect, sentence]))


def question_of(block):
    """One AskUserQuestion question from a block (design d18 section 1.1)."""
    parts = block.parts
    sentence = first_sentence(parts.get(questions.LABELS[3], ""))
    options = []
    for i, (label, _marked, effect) in enumerate(block.options):
        description = describe(effect, sentence if i == 0 else "")
        options.append({"label": label + (questions.RECOMMENDED if i == 0 else ""),
                        "description": description})
    return {"header": "Decision %d" % block.number,
            "question": " ".join(filter(None, [parts.get(questions.LABELS[0], ""),
                                               parts.get(questions.LABELS[1], "")])),
            "options": options, "multiSelect": False}


def payload(blocks):
    """The calls: each holds at most PER_CALL questions."""
    asked = [question_of(b) for b in blocks]
    return [{"questions": asked[i:i + PER_CALL]} for i in range(0, len(asked), PER_CALL)]


def loose(block):
    """The count of lines in `block` that no part takes: a line after a blank that
    opens no bold paragraph, option or answer line, and any line after the answer
    line (d-n2 item 1)."""
    count, current, third, answered = 0, False, False, False
    for line in block.text.splitlines()[1:]:
        if not line.strip():
            current = False
        elif answered:
            count += 1
        elif line.startswith(questions.ANSWER):
            answered = True
        elif BOLD.match(line):
            current, third = True, line.startswith("**%s**" % questions.LABELS[2])
        elif third and questions.OPTION.match(line):
            current = False
        elif not current:
            count += 1
    return count


def shape(block):
    """What a render must keep: the heading, the bold labels, the options and whether each
    has an effect, the answer line, the numbers, the choice's closing `?`, a text in each
    prose part, and the lines no part takes."""
    lines = block.text.splitlines()
    return (block.number, block.title, [BOLD.match(l).group(0) for l in lines if BOLD.match(l)],
            [(label, marked, bool(effect)) for label, marked, effect in block.options],
            block.answer,
            sorted(NUMBER.findall(block.text)),
            block.parts.get(questions.LABELS[1], "").endswith("?"),
            [bool(block.parts.get(label)) for label in PROSE], loose(block))


def kept(old, new):
    return new is not None and shape(old) == shape(new)


def refresh_proposed(ledger_text, block):
    """`ledger_text` with block N's Proposed line taking its recommendation's first sentence."""
    entry = next((e for e in parse(ledger_text).entries
                  if e.section == PROPOSED and e.number == block.number), None)
    titled = TITLED.match(entry.body) if entry else None
    if not titled:
        return ledger_text
    sentence = first_sentence(block.parts.get(questions.LABELS[3], ""))
    lines = ledger_text.splitlines(keepends=True)
    lines[entry.line - 1] = "%d. **%s** %s (%s)\n" % (
        block.number, titled.group(1), sentence, final_parenthetical(entry.body))
    return "".join(lines)


def write_back(path, path_q, asked, rendered, err):
    """The questions text after the write-back of every block the render kept, `rendered`
    None when nothing was rendered, and of the base line of each asked block whose text
    is unchanged since it was read (d41 ruling 6; d42 ruling 5: each asked block has
    one)."""
    fresh = {b.number: b for b in questions.parse(rendered).blocks} if rendered else {}
    with held(os.path.join(os.path.dirname(path), ask.LOCK), ask.NEW_WAIT, err):
        q_text, l_text = read_text(path_q), read_text(path)
        changed = rewrote = False
        for old in asked:
            new = fresh.get(old.number)
            if rendered is not None and not kept(old, new):
                err.write("ask: the render lost part of question %d; its text stays\n"
                          % old.number)
                new = None
            now = next((b for b in questions.parse(q_text).blocks if b.number == old.number),
                       None)
            if now is None or now.text != old.text:
                continue
            new = new if new is not None and new.text != old.text else None
            written = now.text if new is None else new.text
            if new is None and now.base == questions.digests(now.text):
                continue
            written = questions.stamped(written)
            if new is not None:
                l_text, rewrote = refresh_proposed(l_text, new), True
            q_text = questions.replace_block(q_text, now, written)
            changed = True
        if changed:
            try:
                commit_texts([(path_q, q_text), (path, l_text)])
            except Refusal as exc:
                if rewrote:
                    raise
                err.write("ask: %s; the questions stay as written\n" % exc)
                return read_text(path_q)
    return q_text


def skipped(block, problems):
    """Why `block` is not asked, or None: its answer line is filled in, the lint
    refuses it (d-n2 items 3 and 4), it has no base line or more than one (d42 ruling
    5), or it holds lines typed since it was written (d41 ruling 5)."""
    if block.answer:
        return ("is answered on its %s line; run `agentik decisions answer %d` for it first"
                % (questions.ANSWER, block.number))
    head = "question %d: " % block.number
    refused = [m[len(head):] for n, m in problems if n == block.start + 1 and m.startswith(head)]
    if refused:
        return "fails the lint: %s" % "; ".join(refused)
    if block.base is None:
        return ("has no base line, or more than one, so its lines cannot be told from typed "
                "ones; run agentik decisions answer %d --other for it first" % block.number)
    if answer.since(block):
        return ("holds lines typed since it was written; run agentik decisions answer %d "
                "--other for it first" % block.number)
    return None


def askable(parsed, wanted, err, warned):
    """The blocks of `parsed` numbered in `wanted` that can be asked, each with its one
    base line; each other one is warned of once, its number kept in `warned`."""
    asked = []
    for block in parsed.blocks:
        if block.number not in wanted:
            continue
        why = skipped(block, parsed.problems)
        if why is None:
            asked.append(block)
        elif block.number not in warned:
            warned.add(block.number)
            err.write("ask: question %d %s; not asked\n" % (block.number, why))
    return asked


def render(asked, path_q):
    """(the rendered text, None), or (None, why it was not rendered)."""
    where = os.path.dirname(path_q)
    cache = os.path.join(os.path.expanduser("~"), ".claude", "plugins", "cache")
    root = speak.respeak_root(os.environ, cache)
    if root is None:
        return None, "no respeak (RESPEAK_ROOT or an installed plugin)"
    if not os.access(where or os.curdir, os.W_OK):
        return None, "%s is not writable" % display(where or os.curdir)
    return speak.render_text("\n\n".join(b.text for b in asked) + "\n", where, root,
                             os.environ)


def cmd_ask(args, path, out, err):
    path_q = os.path.join(os.path.dirname(path), ask.QUESTIONS)
    text = read_text(path_q) if os.path.exists(path_q) else ""
    parsed = questions.parse(text)
    unknown = sorted(set(args.numbers) - {b.number for b in parsed.blocks})
    if unknown:
        raise Refusal("ask: no open question %s in %s" % (
            ", ".join(map(str, unknown)), display(path_q)))
    warned = set()
    asked = askable(parsed, set(args.numbers) or {b.number for b in parsed.blocks}, err,
                    warned)
    if asked:
        rendered, why = render(asked, path_q)
        if rendered is None:
            err.write("ask: %s; the questions stay as written\n" % why)
        # d41 ruling 6: the base lines are written with a render or without, unless the
        # directory refused the render already; d42: only an asked block's, each based
        if rendered is not None or os.access(os.path.dirname(path_q) or os.curdir, os.W_OK):
            text = write_back(path, path_q, asked, rendered, err)
    asked = askable(questions.parse(text), {b.number for b in asked}, err, warned)
    out.write(json.dumps(payload(asked), indent=2, ensure_ascii=False) + "\n")
    return 0
