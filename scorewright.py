#!/usr/bin/env python3
"""scorewright - talk to a score, get proposed edits, approve or reject them.

    python scorewright.py "Briello no 36 in D# minor"
    python scorewright.py "Fall Rose" --model google/gemini-2.5-flash --audio

The loop:
    stripped MusicXML (+ optional audio + computed facts)  ->  model
    model proposes edits as JSON  ->  verovio renders a red/green notation diff
    you approve / reject / push back  ->  xmledit applies a 1-3 line edit to the SOURCE

The .musicxml is the living file. Sibelius and Dorico are viewers you open when you want them;
nothing here goes through either. See PROJECT.md sections 15 and 16.
"""
import argparse, base64, json, os, re, subprocess, sys, textwrap, urllib.request

import analyze, compose, diffview, retrieve, strip_xml, xmledit

XML_DIR = '/Users/bdogellis/Documents/Score Exports/MusicXML/'
# Edits NEVER touch MusicXML/. That directory is the pristine export of the .sib archive and is the
# only copy of 1,607 scores that took a licence recovery and two days to produce. The first approved
# edit copies the score into working/ and everything after that edits the working copy.
WORK_DIR = '/Users/bdogellis/Documents/Score Exports/working/'
AUDIO_DIR = '/Users/bdogellis/Documents/Score Exports/_audio/'
SCRATCH = ('/private/tmp/claude-502/-Users-bdogellis-repos/'
           '4f969902-2eed-4359-8d3b-6b221b5d03bf/scratchpad/')
KEYFILE = '/tmp/.orkey'

# Only the Gemini family accepts audio input on OpenRouter. Passing --audio with any other model
# fails as an opaque HTTP 404 from the API, which reads like a broken key rather than an
# unsupported modality.
AUDIO_OK = ('google/gemini',)

PRICES = {'anthropic/claude-sonnet-4.5': (3.0, 15.0), 'google/gemini-2.5-pro': (1.25, 10.0),
          'google/gemini-2.5-flash': (0.30, 2.50), 'x-ai/grok-4.20': (1.25, 2.50),
          'openai/gpt-5-mini': (0.25, 2.00), 'deepseek/deepseek-chat-v3.1': (0.55, 1.65)}

SYSTEM_HEAD = """You are a composer's assistant working on Brian Ellis's own scores. You are direct
and concrete. You do not flatter and you do not hedge everything.

WHERE YOUR INFORMATION COMES FROM — this matters and you must be explicit about it.
{sources}
Tag every substantive claim with its source, e.g. "the ostinato never breaks [NOTATION]".
Never present an impression as a fact.

Things you must not do:
- Do not guess the key from the notes. The notated key signature and mode are in the file. Read them.
- Do not describe a single note or a two-note dyad as a chord.
- Do not invent range, interval or count claims. Those are in [COMPUTED] or you do not know them.
- Do not propose changing the pitch of a TIED note. A tie joins two notes that must share a pitch;
  changing one end corrupts it. Check for <tie> before proposing set_pitch.

PROPOSING EDITS. When Brian asks for a change, propose it as a fenced block:

```scorewright
[{"op": "set_pitch",    "measure": 5,  "index": 0, "step": "G", "alter": 0, "octave": 4,
  "why": "one sentence"},
 {"op": "add_dynamic",  "measure": 12, "value": "mf", "why": "one sentence"}]
```

  set_pitch    measure, index, step A-G, alter (-2..2, 0 = natural), octave. Optional staff/voice.
  add_dynamic  measure, value (pppp pp p mp mf f ff fff). Optional staff/voice.
  split_note   measure, index, pitches: a list. ADDS notes by subdividing one note's time.
               Each entry is null (keep the original pitch) or [step, alter, octave].
               e.g. splitting a quarter into two eighths, the second a new G#4:
                 {"op":"split_note","measure":13,"index":3,"pitches":[null,["G",1,4]]}
  merge_notes  measure, index, count. DELETES notes by absorbing them into the first one,
               which lengthens to their combined duration.
  to_rest      measure, index. Silences a note, keeping its duration.
  add_articulation   measure, index, kind: staccato accent tenuto marcato staccatissimo
                     detached-legato spiccato breath-mark caesura stress unstress
  add_ornament       measure, index, kind: trill-mark mordent inverted-mordent turn
                     inverted-turn delayed-turn shake schleifer tremolo
  remove_notation    measure, index, kind - takes any articulation or ornament off a note
  add_hairpin        measure, kind (crescendo|diminuendo), optional stop_measure. Brian's bars
                     carry 32 hairpins; a passage without them is dynamically flat.
  add_slur           measure, from_index, to_index, optional to_measure for a slur across a
                     barline. Phrasing: use it, it is what makes a line sing.
  write_notes        measure, staff, voice, events - WRITES NEW MATERIAL into a bar, replacing
                     whatever is there (usually a whole-bar rest). This is the op for FINISHING
                     an unfinished piece. `events` uses the SAME compact notation you are reading
                     in [COMPUTED] and [CORPUS]:
                       {"op":"write_notes","measure":95,"staff":1,"voice":1,
                        "events":["B4:1","C#5:0.5","D#5:0.5","E5:1","F#5:1"],"why":"..."}
                     "F#4:0.5" a note, "[B3 D#4 F#4]:2" a chord, "r:1" a rest; the number is the
                     duration IN QUARTER NOTES (0.5 = eighth, 1 = quarter, 1.5 = dotted quarter).
                     TUPLETS: "{3:2 E5:0.5 D5:0.5 B4:0.5}" = three eighths in the time of two.
                     Brian writes triplets constantly - use them where the surrounding music does.
                     The events MUST sum to the bar length or the edit is refused with the actual
                     numbers. Write one bar per op.
                     `from_beat` CONTINUES A PHRASE MID-BAR: it keeps everything before that point
                     and writes from there on. Beats are quarter notes from the start of the bar,
                     so from_beat 0.5 keeps the first eighth. USE THIS when the last written bar is
                     partly full - continuing from the middle of a gesture is usually more musical
                     than restarting at the next barline. The events must then sum to the REMAINDER
                     of the bar, not the whole bar.
  ALL OPS take an optional `part` - an index or a part NAME ("Violoncello", "Timpani"). It
  defaults to 0. ON A MULTI-PART SCORE YOU MUST PASS IT, or you will edit the first instrument
  instead of the one you meant. The [COMPUTED] listing names every part with its index.
  append_measures    count - adds empty bars at the END of the piece, past the final barline, so
                     it can be extended. Use when the piece ends AT its last written bar. The final
                     double barline moves to the new end automatically.

`index` is 0-based among PITCHED notes in that bar; RESTS ARE NOT COUNTED. This matches how the
[COMPUTED] bar listings are numbered. Use those listings - do not count notes out of the XML
yourself, you are not reliable at that.

EVERY OP IS DURATION-NEUTRAL: the bar's total is preserved, so notes are added by splitting time
and deleted by merging it. There is no "insert a note and push everything along" - that is not how
a bar works. An edit that changes a voice's total duration is rejected before you ever see a diff.

WHEN ASKED TO FINISH OR CONTINUE A PIECE:
- **MATCH THE TEXTURE, not just the melody.** Look at what the preceding bars actually do. If the
  music is in chords, WRITE CHORDS - "[B3 D#4 F#4]:2", not a bare single line. If both hands are
  playing, WRITE BOTH: one write_notes op per staff per bar. A thin single line under a chordal
  passage is wrong even when every pitch is defensible, and it is the most common way to get this
  visibly wrong.
- Read the bar immediately before the gap in [COMPUTED] and count: how many notes per bar, how many
  simultaneous pitches, which staves are active. Continue THAT.
- Write in the notated key and metre. Use tuplets where the surrounding music does.
- A few bars at a time, then let Brian react. Do not dump thirty bars he has to untangle.
- If the piece ends AT its last written bar with no empty bars to fill, `append_measures` first.
- **Look at the LAST PARTLY-WRITTEN bar before restarting at a barline.** If it holds a gesture that
  stops mid-bar, continue it there with `from_beat` rather than beginning fresh in the next bar.
- The [COMPUTED] RHYTHM section tells you, for any bar that stops part-way, exactly which durations
  completing the previous bar's pattern requires. USE IT VERBATIM. Do not invent a shorter note
  value to make the arithmetic work - a rhythm that sums correctly but does not match the pattern
  is wrong, and it is obvious to Brian at a glance.
- The [COMPUTED] FORM MAP shows which passages of this piece restate which. Read it before adding
  material: it tells you what has already been said, and where. A continuation should know whether
  it is restating, developing or departing.
- Say what the phrase is doing musically, not just which notes it contains.
- **CONTINUING IS NOT CONCLUDING.** "Continue this piece" means the music goes ON: develop the
  material, move the harmony somewhere new, set up what comes next. It does NOT mean write a final
  cadence and stop. A single tutti chord is an ENDING, and Brian did not ask for an ending. Write
  music that clearly wants a next bar - leave the phrase open, land somewhere that implies more.
  Only write a conclusion if he explicitly asks you to end the piece.
- **ON AN ORCHESTRAL SCORE, ORCHESTRATE.** Do not write one line and leave 29 staves resting.
  Decide who carries the melody, who supports, who doubles, who is silent - and say why. Silence is
  a real choice; an instrument left out because you forgot it is not. Respect each instrument's
  range ([COMPUTED] lists violations). **[COMPUTED] PITCH tells you whether this score is at
  concert pitch or transposed, and for every transposing part exactly what to write to sound a
  given note. READ IT. Roughly half of Brian's scores are transposed and half are not - never
  assume, and never guess a transposition yourself.**
  Build it up over turns: melody and bass first, then inner voices, then colour.
- **WHEN BRIAN ASKS YOU TO WRITE BARS, WRITE THEM.** He can reject a proposal in one keystroke and
  see it rendered and hear it first; he cannot react to a question. If you are genuinely unsure
  between two readings, pick the one better supported by the score, WRITE IT, and say in one line
  what the alternative would have been. Refusing to write because his intent is ambiguous is not
  caution, it is a non-answer - the diff is the conversation.

Still NOT supported: editing a note that is TIED, changing a time signature or key, and
removing bars, and creating a staff or voice that does not exist in a bar (so a completely silent
part in an otherwise-written score cannot be filled yet). Say so plainly. Propose few, specific edits.
Explain the musical reason. Never emit the block unless a change was actually asked for."""

SRC_WITH_AUDIO = """You have been given all three of these, and THEY OFTEN DISAGREE:
  [NOTATION]  the score as MusicXML. Exact for pitch, rhythm, dynamics, articulation, pedalling.
  [AUDIO]     a synthesised rendering. Carries character and affect the notation does not.
  [COMPUTED]  facts calculated deterministically. These are EXACT; never contradict them.
If notation and audio disagree, SAY SO and say which you trust and why."""

CORPUS_NOTE = """
  [CORPUS]    passages from Brian's OWN other scores whose melodic shape matches the bars under
              discussion, retrieved by transposition-invariant interval matching. Use these when
              suggesting how HE would solve something - name the piece and bar so he can check it.
              A retrieved passage is evidence of his habits, NOT an instruction to copy."""

SRC_NO_AUDIO = """You have been given exactly TWO sources:
  [NOTATION]  the score as MusicXML. Exact for pitch, rhythm, dynamics, articulation, pedalling.
  [COMPUTED]  facts calculated deterministically. These are EXACT; never contradict them.
YOU HAVE NOT HEARD THIS PIECE. There is no audio in this session. Never write [AUDIO], and never
claim anything about how it sounds as though you had heard it — you are reading, not listening.
If asked about character or mood, answer from the notation and say that is what you are doing."""


def system_prompt(with_audio, with_corpus=False):
    # .replace, not .format: the prompt contains a JSON example whose braces .format() would try
    # to interpolate ("KeyError: '\"op\"'").
    src = SRC_WITH_AUDIO if with_audio else SRC_NO_AUDIO
    if with_corpus:
        src += CORPUS_NOTE
    return SYSTEM_HEAD.replace('{sources}', src)


def load_key():
    if os.path.exists(KEYFILE):
        k = open(KEYFILE).read().strip()
        if k:
            return k
    for p in ('/Users/bdogellis/repos/Prolific/.env', '/Users/bdogellis/repos/MrMercado/.env'):
        try:
            for line in open(p):
                if line.startswith('OPENROUTER_API_KEY'):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")
        except FileNotFoundError:
            pass
    sys.exit('No OPENROUTER_API_KEY found.')


DURNAME = {4: 'w', 2: 'h', 1: 'q', .5: '8', .25: '16', .125: '32', .0625: '64',
           3: 'h.', 1.5: 'q.', .75: '8.', .375: '16.'}


def bar_listing(raw, max_bars=220, max_events=14):
    """Per-part, per-bar note listing. See _bar_listing_impl."""
    return _bar_listing_impl(raw, max_bars, max_events)


def _bar_listing_impl(raw, max_bars=220, max_events=14):
    """Exact per-bar note listing: index, pitch, duration, tie.

    THIS EXISTS BECAUSE THE MODEL CANNOT READ THESE OUT OF THE XML. Measured three separate times:
    it called bar 11's F#4 an "E#4", invented an invalid tie there, and then claimed bar 13 index 3
    was tied when it is not. Structural claims from a model hold up; note-level ones do not (§19c).
    Indices here are the SAME indices the edit ops take, so it never has to count anything.
    """
    div = xmledit.divisions(raw)
    ps = xmledit.parts(raw)
    nums = sorted({int(m.group(1)) for m in xmledit.MEASURE_RE.finditer(
        raw[ps[0][3]:ps[0][4]] if ps else raw)})
    budget = max_bars * max(1, 3 - len(ps) // 12)      # a 30-part score needs a tighter cap
    if len(nums) * max(len(ps), 1) > budget * 4:
        return (f'(score has {len(nums)} bars x {len(ps)} parts; per-bar listing omitted. '
                f'Ask about specific bars and they will be provided.)')
    out = []
    for pi, _pid, pname, _a, _b in (ps or [(0, '', '', 0, len(raw))]):
        for n in nums:
            for st in (1, 2, 3):
                items, i = [], 0
                for sp, b in xmledit.measure_notes(raw, n, staff=st, part=pi):
                    if '<chord' in b:
                        continue
                    if '<rest' in b:
                        continue
                    d = xmledit.note_duration(b) / div
                    nm = DURNAME.get(d, f'{d:g}q')
                    t = xmledit.tie_state(b)
                    mark = {'start': '~>', 'stop': '<~', 'both': '<~>'}.get(t, '')
                    if i < max_events:
                        items.append(f'{i}:{xmledit.read_pitch(b)}:{nm}{mark}')
                    i += 1
                if items:
                    more = f' ...+{i - max_events}' if i > max_events else ''
                    tag = f'p{pi}' + (f' s{st}' if st > 1 or len(ps) == 1 else '')
                    out.append(f'  m{n} {tag} {pname[:18]}: ' + ' '.join(items) + more)
    head = ('BAR NOTES - part:staff then index:pitch:duration, ~> tie start, <~ tie stop.\n'
            'THESE INDICES ARE THE ONES THE EDIT OPS TAKE (pass part=N). Rests are not counted.\n'
            'Do not count notes in the XML yourself.\n')
    if len(ps) > 1:
        # Include the (staff, voice) pairs each part uses. The model guessed voice 1 for the harp's
        # staff 2 - which is voice 2 - and the edit was refused. It should not have to guess.
        rows = []
        for i, _pid, n, _a, _b in ps:
            pairs, last = [], (1, 1)
            for m in nums[:4]:
                for _sp, blk in xmledit.measure_notes(raw, m, part=i):
                    last = xmledit._staff_voice(blk, last)
                    if last not in pairs:
                        pairs.append(last)
                if pairs:
                    break
            sv = ' '.join(f's{a}v{b}' for a, b in pairs) or 's1v1'
            rows.append(f'{i}={n} [{sv}]')
        head += 'PARTS (index=name [staff/voice pairs to pass]): ' + ', '.join(rows) + '\n'
    return head + '\n'.join(out)


def _durseq(raw, measure, staff, voice=None):
    """Duration sequence of one bar in quarter notes, chords counted once."""
    div = xmledit.divisions(raw)
    out = []
    for _, b in xmledit.measure_notes(raw, measure, staff, voice):
        if '<chord' in b:
            continue
        out.append((xmledit.note_duration(b) / div, '<rest' in b))
    return out


def rhythm_hint(raw, max_bars=3):
    """For each PARTIALLY-written bar, state what completing the previous bar's rhythm requires.

    Brian caught the model continuing an "eighth + dotted-quarter" pattern as
    "dotted-quarter + SIXTEENTH + dotted-quarter + sixteenth" - same total, wrong rhythm, extra
    event. The pattern was plainly visible in the bar listing and it still got it wrong. So compute
    it: this is the same principle as bar_listing(), applied to rhythm.
    """
    nums = sorted({int(m.group(1)) for m in xmledit.MEASURE_RE.finditer(raw)})
    fmt = lambda q: DURNAME.get(q, f'{q:g}q')
    out = []
    for n in nums:
        for st in (1, 2):
            seq = _durseq(raw, n, st)
            if not seq or all(r for _, r in seq) or not any(r for _, r in seq):
                continue                       # fully empty or fully written - nothing to complete
            sounded = sum(d for d, r in seq if not r)
            total = sum(d for d, _ in seq)
            if sounded <= 0 or sounded >= total:
                continue
            prev = None
            for p in range(n - 1, max(0, n - 4), -1):
                ps = _durseq(raw, p, st)
                if ps and not any(r for _, r in ps):
                    prev = ps
                    break
            line = (f'  bar {n} staff {st}: written through beat {sounded:g}, '
                    f'{total - sounded:g} quarter notes remain')
            if prev:
                pat = ' '.join(fmt(d) for d, _ in prev)
                acc, rest = 0.0, []
                for d, _ in prev:
                    if acc >= sounded:
                        rest.append(d)
                    acc += d
                if rest and abs(sum(rest) - (total - sounded)) < 1e-6:
                    line += (f'. Bar {p} runs [{pat}]; continuing that pattern from beat '
                             f'{sounded:g} gives exactly [{" ".join(fmt(d) for d in rest)}]')
                else:
                    line += f'. Bar {p} runs [{pat}]'
            out.append(line)
            if len(out) >= max_bars * 2:
                break
    if not out:
        return ''
    return ('RHYTHM - bars that stop part-way, and what continuing the previous bar\'s pattern\n'
            'would require. Match the pattern; do not invent a new note value to make the sum work.\n'
            + '\n'.join(out))


def transposition_facts(raw):
    """Which parts are transposing, and by how much.

    MEASURED: 55% of Brian's multi-part scores carry <transpose>, 45% are at concert pitch. He
    believed most were concert - for `Orchestral Idea` that is wrong, its Bb clarinet's written B4
    sounds A4. Neither he nor the model can assume, and a concert-pitch line written into a
    transposing part validates, renders and sounds a whole tone wrong. So state it.
    """
    ps = xmledit.parts(raw)
    if not ps:
        return ''
    rows = []
    for i, _pid, name, lo, hi in ps:
        m = re.search(r'<transpose>[\s\S]*?</transpose>', raw[lo:hi])
        if not m:
            continue
        ch = re.search(r'<chromatic>(-?\d+)</chromatic>', m.group(0))
        oc = re.search(r'<octave-change>(-?\d+)</octave-change>', m.group(0))
        semis = (int(ch.group(1)) if ch else 0) + 12 * (int(oc.group(1)) if oc else 0)
        rows.append((i, name, semis))
    if not rows:
        return ('PITCH: this score is written at CONCERT PITCH - no part transposes. Write the '
                'pitch you want to HEAR.')
    out = ['PITCH: this score is TRANSPOSED. For the parts below, the pitch you write is NOT the',
           'pitch that sounds. WRITE THE WRITTEN PITCH. To sound a concert C, write the note in',
           'the "write" column.']
    for i, name, semis in rows:
        direction = 'lower' if semis < 0 else 'higher'
        # to sound X, write X shifted by -semis
        ex = 'C4'
        try:
            from music21 import pitch as _p
            ex = _p.Pitch('C4').transpose(-semis).nameWithOctave
        except Exception:
            pass
        out.append(f'  part {i} {name[:22]:<24} sounds {abs(semis)} semitones {direction} than '
                   f'written; to sound concert C4, write {ex}')
    return '\n'.join(out)


def texture_target(raw):
    """The texture of the last bars of real music, as a target to match when writing new ones.

    Telling the model AFTERWARDS that its texture is flat costs a whole call. Telling it the numbers
    to hit costs nothing. Same principle as bar_listing/rhythm_hint: compute what it gets wrong.
    """
    ps = xmledit.parts(raw)
    if len(ps) < 2:
        return ''
    nums = sorted({int(m.group(1)) for m in xmledit.MEASURE_RE.finditer(raw[ps[0][3]:ps[0][4]])})
    live = [n for n in nums
            if any('<rest' not in b for i, _, _, _, _ in ps
                   for _, b in xmledit.measure_notes(raw, n, part=i))]
    if not live:
        return ''
    ref = live[-1]
    p = analyze.texture_profile(raw, ref, xmledit.parts, xmledit.measure_notes)
    return ('TEXTURE TARGET - bar %d is the last bar of real music. Anything you write must behave\n'
            'like it, or the edit is REFUSED:\n'
            '  %d parts sounding, %d DISTINCT rhythmic layers, largest unison group %d parts,\n'
            '  %.2f note-events per sounding part.\n'
            'So: give the inner parts their own rhythm rather than a static whole-note pad, keep any\n'
            'running motor going, and do not put more than ~%d parts on the same rhythm.'
            % (ref, p['sounding_parts'], p['distinct_rhythms'], p['largest_unison_group'],
               p['events_per_part'], max(p['largest_unison_group'], 4)))


def computed_facts(path, raw=None, stem=None):
    """The arithmetic layer. Exact things a model is unreliable at over thousands of notes.

    Includes a FORM MAP. Brian: "how do these edits relate to the rest of the piece? ... it's like
    writing a novel, you need to take into account what has come before." The model gets the whole
    score, but as raw text with no outline - so it is told where material recurs.
    """
    parts = []
    try:
        # Cover the WHOLE piece, not the first 40 bars: a 106-bar sonata had no harmonic summary
        # at all for bars 41-106, which is exactly where a continuation gets written.
        n = max((len(p.getElementsByClass('Measure'))
                 for p in __import__('music21').converter.parse(path).parts), default=40) \
            if False else None
        nbars = len({int(m.group(1)) for m in xmledit.MEASURE_RE.finditer(raw or open(path).read())})
        parts.append(analyze.brief(path, max_measures=min(max(nbars, 40), 240)))
    except Exception as e:
        parts.append(f'(analysis unavailable: {type(e).__name__})')
    try:
        tt = texture_target(raw if raw is not None else open(path).read())
        if tt:
            parts.append(tt)
    except Exception:
        pass
    try:
        tf = transposition_facts(raw if raw is not None else open(path).read())
        if tf:
            parts.append(tf)
    except Exception as e:
        parts.append(f'(transposition facts unavailable: {type(e).__name__})')
    try:
        rh = rhythm_hint(raw if raw is not None else open(path).read())
        if rh:
            parts.append(rh)
    except Exception as e:
        parts.append(f'(rhythm hint unavailable: {type(e).__name__})')
    if stem:
        try:
            parts.append(retrieve.form_text(stem))
        except Exception as e:
            parts.append(f'(form map unavailable: {type(e).__name__})')
    try:
        parts.append(bar_listing(raw if raw is not None else open(path).read()))
    except Exception as e:
        parts.append(f'(bar listing unavailable: {type(e).__name__}: {e})')
    return '\n\n'.join(parts)


def source_path(stem):
    """Prefer an existing working copy; fall back to the pristine export."""
    w = WORK_DIR + stem + '.musicxml'
    return w if os.path.exists(w) else XML_DIR + stem + '.musicxml'


def build_context(stem, want_audio, xml_budget=45000):
    """Assemble the prompt.

    COST: sending the whole stripped MusicXML every turn is what makes this expensive - 147,410
    tokens for a 30-part score, ~$0.30 a call before the model says anything, and `:continue` is
    three calls. The bar listing already carries every note, pitch, duration and tie; the XML adds
    notations, dynamics and slurs. Above the budget we send the LISTING plus a stripped excerpt of
    the recent bars instead of the whole document.
    """
    path = source_path(stem)
    if not os.path.exists(path):
        sys.exit(f'No such score: {path}')
    raw = open(path).read()
    import tiktoken
    enc = tiktoken.get_encoding('cl100k_base')
    full = strip_xml.strip(raw)
    n = len(enc.encode(full))
    if n > xml_budget:
        nums = sorted({int(m.group(1)) for m in xmledit.MEASURE_RE.finditer(
            raw[xmledit.parts(raw)[0][3]:xmledit.parts(raw)[0][4]] if xmledit.parts(raw) else raw)})
        last = nums[-1] if nums else 1
        lo = max(1, last - 3)
        ex = xmledit.excerpt(raw, lo, last) or full
        exn = len(enc.encode(strip_xml.strip(ex)))
        notation = (f'[NOTATION] The full score is {n:,} tokens, too expensive to send every turn. '
                    f'You are given the LAST {last - lo + 1} BARS as MusicXML ({exn:,} tokens); '
                    f'[COMPUTED] below carries every note of every bar of the whole piece, plus the '
                    f'harmony, form map and rhythm. Ask for other bars and they will be provided.'
                    f'\n\n' + strip_xml.strip(ex))
    else:
        notation = '[NOTATION] The score as MusicXML:\n\n' + full
    parts = [{'type': 'text', 'text': notation},
             {'type': 'text', 'text': '[COMPUTED] Deterministic facts. These are exact; never '
                                      'contradict them.\n\n'
                                      + computed_facts(path, raw, stem)}]
    if want_audio:
        wav = AUDIO_DIR + stem + '_16k.wav'
        if not os.path.exists(wav):
            print('  rendering audio (first time for this score)...', flush=True)
            import render_audio
            render_audio.render(stem)
        parts.append({'type': 'text', 'text': '[AUDIO] A synthesised rendering of the same score:'})
        parts.append({'type': 'input_audio',
                      'input_audio': {'data': base64.b64encode(open(wav, 'rb').read()).decode(),
                                      'format': 'wav'}})
    return raw, path, parts


BARS_RE = re.compile(r'\b(?:bars?|mm?\.|measures?)\s*(\d+)\s*(?:[-\u2013to]+\s*(\d+))?', re.I)


def corpus_context(stem, user_text, top=5):
    """[CORPUS]: passages from Brian's OTHER scores that share melodic shape with the bars he just
    mentioned. Retrieval is triggered by bar numbers in his message - the cheap, obvious heuristic,
    and it means the corpus costs nothing on turns that are not about a specific passage."""
    m = BARS_RE.search(user_text or '')
    if not m:
        return None
    lo = int(m.group(1))
    hi = int(m.group(2)) if m.group(2) else lo + 3
    # If the named bars are EMPTY - which is exactly the case when finishing a piece - there is
    # nothing to match on. Walk back to the last bars that actually have notes and retrieve on
    # THOSE: what we want is "how does he continue writing like this", not "what matches silence".
    note = ''
    try:
        raw = open(source_path(stem)).read()
        def density(a, b):
            """fraction of bars in [a,b] that have ANY sounding note in ANY part"""
            ps = xmledit.parts(raw) or [(0, '', '', 0, len(raw))]
            live = 0
            for n in range(a, b + 1):
                if any('<rest' not in blk for i, _, _, _, _ in ps
                       for _, blk in xmledit.measure_notes(raw, n, part=i)):
                    live += 1
            return live / max(1, b - a + 1)
        # "any bar has a note" was too weak: after one bar of a range was written, the walk-back
        # stopped firing and retrieval matched against three-quarters silence. Require the range
        # to be mostly written, and look across ALL parts, not just part 0.
        if density(lo, hi) < 0.6:
            end = lo - 1
            while end > 0 and density(end, end) < 1.0:
                end -= 1
            if end > 0:
                lo, hi = max(1, end - 3), end
                note = (f' (bars {m.group(1)}+ are empty, so this matches the last WRITTEN bars '
                        f'{lo}-{hi} instead - the material to continue from)')
    except Exception:
        pass
    try:
        res, nq = retrieve.query(stem, lo, hi, top=top)
    except Exception as e:
        return f'[CORPUS] retrieval unavailable: {type(e).__name__}: {e}'
    if not res:
        return (f'[CORPUS] Nothing in the other 1,606 scores matches the melodic shape of '
                f'bars {lo}-{hi}. That is itself information: this gesture is not one of his habits.')
    out = [f'[CORPUS] Passages from Brian\'s OWN other scores sharing the melodic shape of '
           f'bars {lo}-{hi}{note} ({nq} n-grams queried). Cite the piece and bar if you use one.']
    for r in res:
        try:
            m0 = int(str(r['measures']).split('-')[0])
        except Exception:
            continue
        txt = retrieve.excerpt_text(r['score'], m0, m0 + 3, part=r['part'], max_chars=260)
        out.append(f"\n--- {r['score']}  (part {r['part']}, bars {r['measures']}, "
                   f"similarity {r['weight']})\n{txt}")
    return '\n'.join(out)


def call(model, messages, key, max_tokens=12000):
    # 1600 truncated a 30-part analysis mid-sentence and 5000 truncated a 30-part ORCHESTRATION:
    # reasoning models spend the budget thinking before emitting, and an orchestral edit block is
    # one JSON op per part per bar. Output tokens are cheap next to a 200k prompt.
    body = json.dumps({'model': model, 'max_tokens': max_tokens, 'messages': messages}).encode()
    req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=body,
                                 headers={'Authorization': f'Bearer {key}',
                                          'Content-Type': 'application/json'})
    d = json.load(urllib.request.urlopen(req, timeout=600))
    u = d.get('usage', {})
    pi, po = PRICES.get(model, (1.0, 5.0))
    cost = u.get('prompt_tokens', 0) * pi / 1e6 + u.get('completion_tokens', 0) * po / 1e6
    msg = d['choices'][0]['message']
    txt = msg.get('content') or ''
    if not txt.strip():
        # A reasoning model can spend the whole budget thinking and return EMPTY content. Returning
        # '' silently made a staged phase produce nothing and the next phase build on nothing.
        fin = d['choices'][0].get('finish_reason')
        txt = (msg.get('reasoning') or '').strip()
        if not txt:
            raise RuntimeError(f'{model} returned no content (finish_reason={fin}, '
                               f'{u.get("completion_tokens", 0)} completion tokens). '
                               f'Raise --max-tokens.')
    return (txt, cost, u.get('prompt_tokens', 0))


EDIT_RE = re.compile(r'```scorewright\s*(\[[\s\S]*?\])\s*```')


def parse_edits(text):
    m = EDIT_RE.search(text)
    if not m:
        return None, text
    try:
        edits = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        return None, text + f'\n\n(could not parse the edit block: {e})'
    return edits, EDIT_RE.sub('', text).strip()


def apply_edits(raw, edits, texture_change=None):
    """Returns (new_xml, [human-readable descriptions]). Raises ValueError on a bad locator.

    Every op is duration-neutral, and `validate_edit` re-checks that per measure afterwards. A bar
    that no longer adds up never reaches the diff.
    """
    out, notes = raw, []
    # Baseline for duration-neutrality. append_measures CREATES bars, so a bar written after an
    # append has no counterpart in `raw` and validate_edit sees "duration changed 0 -> 1024" and
    # refuses every single write. The baseline moves forward past structural ops.
    base = raw
    for e in edits:
        op = e.get('op')
        P = xmledit.part_index(out, e.get('part', 0))
        pn = xmledit.parts(out)
        _before_n = len(notes)
        if op == 'set_pitch':
            sp = xmledit.find_note(out, e['measure'], e['index'],
                                   e.get('staff'), e.get('voice'))
            if not sp:
                raise ValueError(f"no pitched note {e['index']} in bar {e['measure']}")
            old = xmledit.read_pitch(out[sp[0]:sp[1]])
            out = xmledit.set_pitch(out, sp, e['step'], int(e.get('alter', 0)), e['octave'])
            sp2 = xmledit.find_note(out, e['measure'], e['index'], e.get('staff'), e.get('voice'), P)
            notes.append((e['measure'], f"note {e['index']}: {old} -> "
                                        f"{xmledit.read_pitch(out[sp2[0]:sp2[1]])}",
                          e.get('why', '')))
        elif op == 'add_dynamic':
            out = xmledit.add_dynamic(out, e['measure'], e['value'],
                                      e.get('staff', 1), e.get('voice', 1), part=P)
            notes.append((e['measure'], f"add {e['value']}", e.get('why', '')))
        elif op == 'split_note':
            sp = xmledit.find_note(out, e['measure'], e['index'], e.get('staff'), e.get('voice'), P)
            if not sp:
                raise ValueError(f"no pitched note {e['index']} in bar {e['measure']}")
            ps = [None if p is None else (p[0], int(p[1]), int(p[2])) for p in e['pitches']]
            out, old = xmledit.split_note(out, sp, ps)
            shown = ', '.join('(kept)' if p is None else f'{p[0]}{"#" * max(0, p[1])}{p[2]}'
                              for p in ps)
            notes.append((e['measure'], f"note {e['index']}: {old} split into {len(ps)} -> {shown}",
                          e.get('why', '')))
        elif op == 'merge_notes':
            n = int(e['count'])
            before = [xmledit.read_pitch(out[s[0]:s[1]]) for s in
                      (xmledit.find_note(out, e['measure'], e['index'] + i,
                                         e.get('staff'), e.get('voice')) for i in range(n)) if s]
            out = xmledit.merge_notes(out, e['measure'], e['index'], n,
                                      e.get('staff'), e.get('voice'), part=P)
            notes.append((e['measure'], f"notes {e['index']}..{e['index'] + n - 1} "
                                        f"({' '.join(before)}) merged into one",
                          e.get('why', '')))
        elif op == 'to_rest':
            sp = xmledit.find_note(out, e['measure'], e['index'], e.get('staff'), e.get('voice'), P)
            if not sp:
                raise ValueError(f"no pitched note {e['index']} in bar {e['measure']}")
            old = xmledit.read_pitch(out[sp[0]:sp[1]])
            out = xmledit.to_rest(out, sp)
            notes.append((e['measure'], f"note {e['index']} ({old}) -> rest", e.get('why', '')))
        elif op in ('add_articulation', 'add_ornament', 'remove_notation'):
            sp = xmledit.find_note(out, e['measure'], e['index'], e.get('staff'), e.get('voice'), P)
            if not sp:
                raise ValueError(f"no pitched note {e['index']} in bar {e['measure']}")
            pitch = xmledit.read_pitch(out[sp[0]:sp[1]])
            fn = {'add_articulation': xmledit.add_articulation,
                  'add_ornament': xmledit.add_ornament,
                  'remove_notation': xmledit.remove_notation}[op]
            out = fn(out, sp, e['kind'])
            verb = 'remove' if op == 'remove_notation' else 'add'
            notes.append((e['measure'], f"note {e['index']} ({pitch}): {verb} {e['kind']}",
                          e.get('why', '')))
        elif op == 'write_notes':
            st, vo = int(e.get('staff', 1)), int(e.get('voice', 1))
            before = [xmledit.read_pitch(b) or 'r'
                      for _, b in xmledit.measure_notes(out, e['measure'], st, vo, P)]
            fb = float(e.get('from_beat', 0) or 0)
            out = xmledit.write_notes(out, e['measure'], st, vo, e['events'], from_beat=fb, part=P)
            was = 'empty' if all(p == 'r' for p in before) else ' '.join(before[:6])
            at = f' from beat {fb:g}' if fb else ''
            notes.append((e['measure'],
                          f"staff {st}{at}: write {' '.join(e['events'])}  (was {was})",
                          e.get('why', '')))
        elif op == 'append_measures':
            n = int(e['count'])
            before = max(int(m.group(1)) for m in xmledit.MEASURE_RE.finditer(out))
            out = xmledit.append_measures(out, n)
            base = out                      # newly created bars have no "before" to compare with
            notes.append((before, f'append {n} empty bar(s): the piece now runs to bar {before + n}',
                          e.get('why', '')))
        elif op == 'add_hairpin':
            out = xmledit.add_hairpin(out, e['measure'], e.get('kind', 'crescendo'),
                                      e.get('staff', 1), e.get('voice', 1), P,
                                      e.get('stop_measure'))
            notes.append((e['measure'], f"{e.get('kind','crescendo')} to bar "
                                        f"{e.get('stop_measure', e['measure'])}", e.get('why', '')))
        elif op == 'add_slur':
            out = xmledit.add_slur(out, e['measure'], e['from_index'], e['to_index'],
                                   e.get('staff'), e.get('voice'), e.get('to_measure'), part=P)
            tgt = ('' if e.get('to_measure') in (None, e['measure'])
                   else f" (to bar {e['to_measure']})")
            notes.append((e['measure'], f"slur notes {e['from_index']}..{e['to_index']}{tgt}",
                          e.get('why', '')))
        else:
            raise ValueError(f'unsupported op: {op}')
        # Name the instrument on every line. On a 30-part score "staff 1: write B-5:4" is useless -
        # you cannot tell the tuba from the piccolo. append_measures affects all parts, so it is
        # left unlabelled.
        if len(pn) > 1 and op != 'append_measures':
            for k in range(_before_n, len(notes)):
                m_, d_, w_ = notes[k]
                notes[k] = (m_, f'{pn[P][2][:20]} - {d_}', w_)
    problems = []
    for m in sorted({n[0] for n in notes}):
        if xmledit.measure_span(base, m, part=P) is None:
            continue                        # a bar that did not exist in the baseline
        problems += xmledit.validate_edit(base, out, m, part=P)
    if problems:
        raise ValueError('; '.join(problems))
    # TEXTURE GATE. Arithmetic validity is not musical validity: a bar can sum correctly, use only
    # chord tones and correct transpositions, and still be inert. This compares each WRITTEN bar
    # against the last bar of real music and refuses if the texture went flat.
    written = sorted({m for m, d, _ in notes if 'write ' in d})
    # A NEW SECTION is supposed to differ from what came before. The gate exists to catch a texture
    # that went flat by accident, not to forbid contrast - so a deliberate change can declare itself
    # and say why. Brian: "it's kinda just repeating... I think we need a new texture."
    if texture_change:
        notes.insert(0, (written[0] if written else 1,
                         'TEXTURE CHANGE (deliberate)', texture_change))
    # CLASH GATE: a simultaneous semitone between two parts. Applies even to a deliberate texture
    # change - a new section is allowed to sound different, not to sound wrong.
    if written:
        try:
            cl = analyze.check_clashes(out, written, xmledit.parts, xmledit.measure_notes,
                                       xmledit.divisions)
        except Exception:
            cl = []
        if cl:
            raise ValueError('semitone clashes between parts: ' + '; '.join(
                f"bar {c['measure']} beat {c['beat']}: {c['low']} vs {c['high']} "
                f"({c['interval']})" for c in cl[:6])
                + '. Two parts sounding a semitone apart at the same moment reads as a mistake.')
    if written and not texture_change and len(xmledit.parts(out)) > 1:
        try:
            ref = min(written) - 1
            while ref > 0 and not any(
                    '<rest' not in b for i, _, _, _, _ in xmledit.parts(out)
                    for _, b in xmledit.measure_notes(out, ref, part=i)):
                ref -= 1
            if ref > 0:
                flags = analyze.texture_report(out, written, ref,
                                               xmledit.parts, xmledit.measure_notes)
                if flags:
                    raise ValueError('the notes are legal but the TEXTURE is wrong: '
                                     + '; '.join(flags)
                                     + '. Give the inner parts their own rhythm instead of a static '
                                       'pad, keep any motor rhythm running, and stop doubling one '
                                       'line across the whole orchestra.')
        except ValueError:
            raise
        except Exception:
            pass
    return out, notes


def show_diff(raw, new, notes, stem, context=2, with_audio=True, side_by_side=True):
    """Excerpt of the edited bars +/- context, red/green highlights, and playable before/after."""
    out = SCRATCH + 'sw_diff.html'
    open(out, 'w').write(diffview.build(raw, new, notes, stem, context, with_audio, side_by_side))
    subprocess.run(['open', out], check=False)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('score')
    ap.add_argument('--model', default='anthropic/claude-sonnet-4.5')
    ap.add_argument('--audio', action='store_true', help='also let the model HEAR the score')
    ap.add_argument('--context', type=int, default=2, help='bars of context around an edit')
    ap.add_argument('--no-audio', action='store_true', help='skip before/after playback in the diff')
    ap.add_argument('--no-corpus', action='store_true',
                    help='do not retrieve matching passages from his other 1,606 scores')
    ap.add_argument('--stacked', action='store_true',
                    help='before/after stacked instead of side by side (wide orchestral scores)')
    a = ap.parse_args()

    if a.audio and not a.model.startswith(AUDIO_OK):
        sys.exit(f'--audio needs an audio-capable model; {a.model} is not one.\n'
                 f'  try: --model google/gemini-2.5-pro   (or gemini-2.5-flash, 10x cheaper)')
    key = load_key()
    print(f'loading {a.score} ...', flush=True)
    raw, path, ctx = build_context(a.score, a.audio)
    live = raw
    msgs = [{'role': 'system', 'content': system_prompt(a.audio, not a.no_corpus)},
            {'role': 'user', 'content': ctx}]
    spent = 0.0
    where = 'working copy' if path.startswith(WORK_DIR) else 'pristine export (read-only)'
    print(f'  {os.path.getsize(path):,} bytes from the {where}  |  model {a.model}'
          f'  |  audio {"on" if a.audio else "off"}')
    print(f'  edits are written to {WORK_DIR}')
    print('  type a question or a request. ctrl-c to quit.')
    print('  :continue <first> <last>   staged PLAN -> COMPOSE -> ORCHESTRATE\n')

    while True:
        try:
            q = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        # :continue <lo> <hi>  runs the staged PLAN -> COMPOSE -> ORCHESTRATE flow
        staged = re.match(r'^:continue\s+(\d+)\s+(\d+)\s*$', q.strip())
        turn = q
        if not a.no_corpus:
            cc = corpus_context(a.score, q)
            if cc:
                print(f'  [corpus: {cc.count("---")} matching passages from his other scores]')
                turn = q + '\n\n' + cc
        if staged:
            lo_, hi_ = int(staged.group(1)), int(staged.group(2))
            cc = corpus_context(a.score, f'bars {lo_} {hi_}')
            base = list(msgs) + ([{'role': 'user', 'content': cc}] if cc else [])
            try:
                txt, cost = compose.run(lambda m: call(a.model, m, key), base, lo_, hi_,
                                        hi_ - lo_ + 1)
            except Exception as e:
                print(f'  [error: {str(e)[:200]}]\n')
                continue
            spent += cost
            ptok = 0
            msgs.append({'role': 'user', 'content': turn})
            msgs.append({'role': 'assistant', 'content': txt})
        else:
            msgs.append({'role': 'user', 'content': turn})
            try:
                txt, cost, ptok = call(a.model, msgs, key)
            except Exception as e:
                print(f'  [error: {str(e)[:200]}]\n')
                msgs.pop()
                continue
            spent += cost
            msgs.append({'role': 'assistant', 'content': txt})
        edits, prose = parse_edits(txt)
        print()
        print(textwrap.fill(prose, 96, replace_whitespace=False) if prose else '(no comment)')
        print(f'\n  [{ptok:,} tok, ${cost:.4f}, session ${spent:.4f}]')

        if edits:
            try:
                new, notes = apply_edits(live, edits)
            except (ValueError, KeyError) as e:
                print(f'  [edit rejected before rendering: {e}]\n')
                msgs.append({'role': 'user',
                             'content': f'That edit could not be applied: {e}. Try again.'})
                continue
            print('\n  proposed:')
            for m, d, w in notes:
                print(f'    bar {m}  {d}')
                if w:
                    print(textwrap.fill(w, 88, initial_indent='            ',
                                        subsequent_indent='            '))
            print('  rendering diff' + ('' if a.no_audio else ' and audio') + '...', flush=True)
            show_diff(live, new, notes, a.score, a.context, not a.no_audio, not a.stacked)
            ans = input('\n  [a]pprove / [r]eject / [enter] to keep talking: ').strip().lower()
            if ans == 'a':
                os.makedirs(WORK_DIR, exist_ok=True)
                dst = WORK_DIR + a.score + '.musicxml'
                open(dst, 'w').write(new)
                live = new
                print(f'  written to {dst}\n')
                msgs.append({'role': 'user', 'content': 'Approved and applied.'})
            elif ans == 'r':
                print('  discarded\n')
                msgs.append({'role': 'user', 'content': 'Rejected. Leave the score as it was.'})
            else:
                print('  left pending\n')
        print()
    print(f'session total ${spent:.4f}')


if __name__ == '__main__':
    main()
