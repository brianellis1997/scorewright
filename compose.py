"""Staged continuation: PLAN -> COMPOSE -> ORCHESTRATE, instead of one overloaded call.

Brian: "is it doing retrieval? does it have multiple steps? like, okay this is the material, this
is a possibility of how it could continue, let me see what Brian has done in the past... then let
me orchestrate that."

A single call has to analyse, invent and instrument simultaneously, and it shows: it wrote one
tutti chord as an ENDING when asked to continue. Splitting the work means each stage sees the
previous stage's conclusion and can be judged on its own.

  1 PLAN        analyse the material and say where it should go. NO notes. Retrieval is in scope.
  2 COMPOSE     the musical line only - melody and bass, in concert terms. Still no orchestration.
  3 ORCHESTRATE turn that line into parts, respecting transposition and who is playing.
"""
import json, re

PLAN = """You are planning how to CONTINUE this piece. Do not write any notes yet and do not emit
an edit block.

Answer, in this order and briefly:
1. MATERIAL - the motifs and gestures the piece is built from, with bar numbers.
2. WHERE IT STANDS - what the last written bar leaves unresolved: harmonically, rhythmically, in
   register and in energy.
3. WHAT BRIAN DOES - read [CORPUS]. What do his other pieces do at a comparable moment? Do not
   copy them; say what they tell you about his habits, and say so plainly if they tell you nothing.
4. THE PLAN - where the next {n} bars should go and why. Name the harmonic destination, what
   happens to the motif, and the shape of the energy. THE MUSIC MUST CONTINUE, not conclude.
5. ORCHESTRATION SKETCH - who carries the line, who supports, who is deliberately silent.

Be concrete and short. This plan is what the next stage composes from."""

COMPOSE = """Now compose ONLY the musical line for bars {lo}-{hi}, following your plan.

Give the MELODY and the BASS as concert pitches, bar by bar, in the compact notation
("F#4:0.5", "[B3 D#4]:2", "r:1", "{{3:2 a b c}}"). Nothing else - no inner voices, no instrument
assignments, no edit block yet. Check each bar sums to the bar length and say the total.

Then state the harmony of each bar as a chord name. This is the skeleton the orchestration hangs
on, so it has to be right before anything is assigned to an instrument."""

ORCH = """Now orchestrate what you just composed, for bars {lo}-{hi}, and emit the edit block.

Rules you must follow:
- Assign the melody, the bass and the inner voices to actual instruments, and say who is silent.
- [COMPUTED] PITCH tells you whether this score is transposed. If it is, WRITE THE WRITTEN PITCH so
  the SOUNDING pitch matches the skeleton you just composed. Check every transposing part.
- [COMPUTED] PARTS gives each part's index and its [staff/voice] pairs. Pass `part` on every op and
  use the staff/voice it lists. Do not guess.
- Keep each bar summing correctly; the edit is refused otherwise.
- `append_measures` first if the bars you need do not exist.

Emit one ```scorewright block with all the ops."""


def run(session_call, base_msgs, lo, hi, n, echo=print, cheap_call=None, apply_fn=None,
        retries=3):
    """session_call/cheap_call(messages) -> (text, cost, prompt_tokens).

    PLAN and COMPOSE are reasoning about material and go to the CHEAP model; only ORCHESTRATE needs
    the expensive one. If `apply_fn` is given, the orchestration is applied immediately and any
    failure - a bad locator, a bar that does not add up, or the TEXTURE GATE - is fed straight back
    for another attempt. Without that loop the model never learns its output was inert.
    """
    msgs = list(base_msgs)
    total = 0.0
    cheap = cheap_call or session_call
    for name, prompt, fn in (('PLAN', PLAN.format(n=n), cheap),
                             ('COMPOSE', COMPOSE.format(lo=lo, hi=hi), cheap)):
        msgs.append({'role': 'user', 'content': prompt})
        txt, cost, ptok = fn(msgs)
        msgs.append({'role': 'assistant', 'content': txt})
        total += cost
        echo(f'\n--- {name} ---  [{ptok:,} tok, ${cost:.4f}]')
        echo(txt.strip()[:1400])

    prompt = ORCH.format(lo=lo, hi=hi)
    last = ''
    for attempt in range(1, retries + 1):
        msgs.append({'role': 'user', 'content': prompt})
        txt, cost, ptok = session_call(msgs)
        msgs.append({'role': 'assistant', 'content': txt})
        total += cost
        last = txt
        echo(f'\n--- ORCHESTRATE (attempt {attempt}) ---  [{ptok:,} tok, ${cost:.4f}]')
        echo(txt.strip()[:900])
        if apply_fn is None:
            break
        ok, err = apply_fn(txt)
        if ok:
            echo(f'  -> accepted on attempt {attempt}')
            break
        echo(f'  -> REJECTED: {err[:220]}')
        prompt = ('That was refused:\n\n' + err + '\n\nFix it and emit the whole edit block '
                  'again. Do not explain, just correct the music and re-emit.')
    return last, total
