"""Surgical edits to MusicXML source text. The foundation of the approve/reject loop.

WHY NOT music21's writer: it re-serialises the whole document. Writing Briello 36 back with NO
edits at all produces an 11,071-line diff and grows the file 21%. You cannot approve a change you
cannot see, and Claude Code works because it shows you a diff. Editing the source text directly
means the diff is exactly the edit - typically 1-3 lines.

INDEXING TRAP (cost an hour): a MusicXML `<note>` element includes RESTS. music21's `.notes`
excludes them. Indexing raw `<note>` blocks as if they matched music21 note indices silently edits
the wrong note. Every locator here counts PITCHED notes only, matching music21.
"""
import re

NOTE_RE = re.compile(r'<note[\s\S]*?</note>')
STEP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


PART_RE = re.compile(r'<part id="([^"]+)">[\s\S]*?</part>')


def parts(raw):
    """[(index, part_id, name, start, end)] for every <part> in the score.

    EVERYTHING here used to assume a single-part (piano) score. `re.search` for a measure returns
    the FIRST match, so on a 30-part orchestral score every op silently operated on Flute 1 - ask
    to edit the cello and you edited the flute. Locators take a `part` index now.
    """
    names = dict(re.findall(r'<score-part id="([^"]+)"[^>]*>\s*<part-name[^>]*>([^<]*)', raw))
    out = []
    for i, m in enumerate(PART_RE.finditer(raw)):
        out.append((i, m.group(1), names.get(m.group(1), m.group(1)).strip(), m.start(), m.end()))
    return out


def part_index(raw, want):
    """Resolve an int index, a part id, or a (case-insensitive) part NAME to an index."""
    ps = parts(raw)
    if want is None:
        return 0
    if isinstance(want, int):
        if not 0 <= want < len(ps):
            raise ValueError(f'part {want} out of range; the score has {len(ps)} parts')
        return want
    w = str(want).strip().lower()
    for i, pid, name, _, _ in ps:
        if pid.lower() == w or name.lower() == w:
            return i
    matches = [i for i, pid, name, _, _ in ps if w in name.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f'part {want!r} is ambiguous: matches '
                         + ', '.join(parts(raw)[i][2] for i in matches))
    raise ValueError(f'no part named {want!r}; the score has: '
                     + ', '.join(f'{i}={n}' for i, _, n, _, _ in ps))


def measure_span(raw, number, part=0):
    """Byte span of `<measure number="N">` WITHIN one part. Returns (start, end) or None."""
    ps = parts(raw)
    if not ps:
        m = re.search(rf'<measure number="{number}"[\s\S]*?</measure>', raw)
        return (m.start(), m.end()) if m else None
    i = part_index(raw, part)
    lo, hi = ps[i][3], ps[i][4]
    m = re.search(rf'<measure number="{number}"[\s\S]*?</measure>', raw[lo:hi])
    return (lo + m.start(), lo + m.end()) if m else None


def find_note(raw, measure, index, staff=None, voice=None, part=0):
    """Byte span of the `index`-th PITCHED note (0-based) in a measure, matching music21's .notes.

    Rests are skipped, exactly as music21 does. Optionally filter by staff and voice.
    """
    sp = measure_span(raw, measure, part)
    if not sp:
        return None
    blk = raw[sp[0]:sp[1]]
    n = 0
    for m in NOTE_RE.finditer(blk):
        t = m.group(0)
        if '<rest' in t:
            continue
        if staff is not None and f'<staff>{staff}</staff>' not in t:
            continue
        if voice is not None and f'<voice>{voice}</voice>' not in t:
            continue
        if n == index:
            return (sp[0] + m.start(), sp[0] + m.end())
        n += 1
    return None


def read_pitch(block):
    s = re.search(r'<step>(\w)</step>', block)
    a = re.search(r'<alter>(-?\d+)</alter>', block)
    o = re.search(r'<octave>(-?\d+)</octave>', block)
    if not (s and o):
        return None
    alt = int(a.group(1)) if a else 0
    acc = {1: '#', 2: '##', -1: '-', -2: '--', 0: ''}.get(alt, '')
    return f'{s.group(1)}{acc}{o.group(1)}'


def tie_state(block):
    """'start', 'stop', 'both' or None for one <note> block."""
    t = set(re.findall(r'<tie type="(start|stop)"', block))
    return 'both' if len(t) == 2 else (t.pop() if t else None)


def set_pitch(raw, span, step, alter, octave, allow_tied=False):
    """Rewrite one note's <pitch> in place. Adds or removes <alter> as needed.

    REFUSES a tied note by default. A tie joins two <note> elements that must share a pitch;
    changing one end leaves the score tying D# to G, which is corrupt and renders as a stray
    slur. Caught by the model itself, which noticed bar 11's first note carries <tie type="stop"/>.
    Change both ends deliberately, or pick a different note.
    """
    b = raw[span[0]:span[1]]
    if not allow_tied:
        st = tie_state(b)
        if st:
            raise ValueError(f'that note is tied ({st}); changing one end of a tie would corrupt '
                             f'it. Pick an untied note, or change both ends explicitly.')
    nb = re.sub(r'<step>\w</step>', f'<step>{step}</step>', b)
    nb = re.sub(r'<octave>-?\d+</octave>', f'<octave>{octave}</octave>', nb)
    if re.search(r'<alter>-?\d+</alter>', nb):
        nb = (re.sub(r'\s*<alter>-?\d+</alter>', '', nb) if alter == 0
              else re.sub(r'<alter>-?\d+</alter>', f'<alter>{alter}</alter>', nb))
    elif alter != 0:
        nb = nb.replace(f'<step>{step}</step>', f'<step>{step}</step>\n     <alter>{alter}</alter>', 1)
    return raw[:span[0]] + nb + raw[span[1]:]


def add_dynamic(raw, measure, value, staff=1, voice=1, part=0):
    """Insert a <direction> dynamic at the start of a measure's content."""
    sp = measure_span(raw, measure, part)
    if not sp:
        return raw
    blk = raw[sp[0]:sp[1]]
    ins = blk.find('>') + 1                     # just after the <measure ...> tag
    d = (f'\n   <direction placement="below">\n    <direction-type>\n'
         f'     <dynamics><{value} /></dynamics>\n    </direction-type>\n'
         f'    <voice>{voice}</voice>\n    <staff>{staff}</staff>\n   </direction>')
    return raw[:sp[0]] + blk[:ins] + d + blk[ins:] + raw[sp[1]:]


def diff(a, b, context=1):
    import difflib
    return '\n'.join(difflib.unified_diff(a.splitlines(), b.splitlines(),
                                          'before', 'after', lineterm='', n=context))


MEASURE_RE = re.compile(r'<measure number="(\d+)"[\s\S]*?</measure>')


def excerpt(raw, first, last, only_parts=None):
    """A display-only MusicXML containing just measures [first, last], as TEXT.

    Not via music21: `score.measures(a, b)` + re-export silently DROPS DYNAMICS, which is fatal when
    the whole point is showing a dynamic that was added. Slicing the source text keeps dynamics,
    pedal, hairpins and slurs exactly as they are.

    Key/time/clef live in an <attributes> block in bar 1, so an excerpt starting at bar 10 would
    render with no key signature. The effective attributes from every earlier bar are carried
    forward into the first kept measure.
    """
    # `only_parts`: keep just these part indices. A 30-stave orchestral diff is unreadable; showing
    # only the instruments involved in the edit is the whole point of an excerpt.
    keep_ids = None
    if only_parts is not None:
        allp = parts(raw)
        want = {part_index(raw, p) for p in only_parts}
        keep_ids = {allp[i][1] for i in want if i < len(allp)}
    out = []
    for pm in re.finditer(r'<part id="([^"]*)">[\s\S]*?</part>', raw):
        if keep_ids is not None and pm.group(1) not in keep_ids:
            continue
        part = pm.group(0)
        kept, carried = [], {}
        for m in MEASURE_RE.finditer(part):
            n = int(m.group(1))
            # <transpose> MUST be carried too. Without it an excerpt of a transposing part is
            # written pitch with nothing saying so, and every consumer plays it raw: the page's
            # audio had clarinets and trumpets a whole tone sharp and horns a fifth sharp, while
            # the full-score render of the same music was in tune. Sounding pitch is not a property
            # of the notes, it is a property of the notes PLUS this element.
            for tag in ('key', 'time', 'clef', 'divisions', 'staves', 'transpose'):
                for a in re.finditer(rf'<{tag}[ >][\s\S]*?</{tag}>|<{tag}[^>]*/>', m.group(0)):
                    if n <= last:
                        # A piano part has TWO clefs (number="1" treble, number="2" bass). Keying
                        # only on the tag name kept one and dropped the other, and verovio then
                        # reported "Staff 2 cannot be found" and rendered the excerpt wrong.
                        num = re.search(r'number="(\d+)"', a.group(0))
                        carried[(tag, num.group(1) if num else '')] = a.group(0)
            if first <= n <= last:
                blk = m.group(0)
                if n == first and carried:
                    # MERGE, do not skip. A measure can already carry an <attributes> block holding
                    # only <staff-details> (a mid-score change). Treating that as "attributes are
                    # present" dropped the key signature and both clefs, and verovio rendered the
                    # excerpt with no key and no clefs at all.
                    have = re.search(r'<attributes>([\s\S]*?)</attributes>', blk)
                    body = have.group(1) if have else ''
                    # Check PER NUMBER, not per tag. Bar 53 of the Piano Sonata carries a clef
                    # change for staff 1, so "is there a <clef> already?" was true and BOTH carried
                    # clefs were skipped - staff 2 lost its bass clef, verovio defaulted it to
                    # treble, and the left hand rendered on ledger lines far below the staff.
                    # Same shape as every other bug here: a proxy instead of the object.
                    def present(tag, num):
                        for a in re.finditer(rf'<{tag}[ >][\s\S]*?</{tag}>|<{tag}[^>]*/>', body):
                            n = re.search(r'number="(\d+)"', a.group(0))
                            if (n.group(1) if n else '') == num:
                                return True
                        return False
                    missing = [v for t in ('divisions', 'key', 'time', 'staves', 'clef',
                                          'transpose')
                               for k, v in sorted(carried.items())
                               if k[0] == t and not present(t, k[1])]
                    if missing:
                        add = '\n    ' + '\n    '.join(missing)
                        if have:
                            blk = blk[:have.start(1)] + add + blk[have.start(1):]
                        else:
                            ins = blk.find('>') + 1
                            blk = (blk[:ins] + '\n   <attributes>' + add + '\n   </attributes>'
                                   + blk[ins:])
                kept.append(blk)
        if kept:
            head = part[:part.find('<measure')]
            out.append(head + '\n'.join(kept) + '\n  </part>')
    if not out:
        return None
    # Drop DANGLING spanners. A <slur type="start"> whose matching stop lies outside the excerpt
    # cannot be terminated, and verovio draws it as an enormous diagonal sweeping down through every
    # staff - the "horrible slur lines" that made the page unreadable. Same for ties, hairpins,
    # tuplets, pedal and octave lines.
    def _debalance(part_xml):
        for tag in ('slur', 'tied', 'wedge', 'tuplet', 'pedal', 'octave-shift', 'glissando'):
            opens = {}
            drop = []
            for m in re.finditer(rf'<{tag}\b[^>]*/?>', part_xml):
                t = m.group(0)
                ty = re.search(r'type="(\w+)"', t)
                if not ty:
                    continue
                num = (re.search(r'number="(\d+)"', t) or [None, '1'])[1] \
                    if re.search(r'number="(\d+)"', t) else '1'
                kind = ty.group(1)
                if kind in ('start', 'crescendo', 'diminuendo', 'up', 'down'):
                    opens.setdefault(num, []).append(m.span())
                elif kind in ('stop',):
                    if opens.get(num):
                        opens[num].pop()
                    else:
                        drop.append(m.span())      # a stop with no start in range
            for spans in opens.values():
                drop += spans                      # starts never closed in range
            for a, b in sorted(drop, reverse=True):
                part_xml = part_xml[:a] + part_xml[b:]
        # tidy notations wrappers left empty
        part_xml = re.sub(r'\s*<notations>\s*</notations>', '', part_xml)
        return part_xml

    out = [_debalance(p) for p in out]
    head = raw[:raw.find('<part id=')]
    if keep_ids is not None:
        # the <part-list> must not advertise parts we dropped, or verovio draws empty staves
        def _keep(m):
            return m.group(0) if m.group(1) in keep_ids else ''
        head = re.sub(r'<score-part id="([^"]+)">[\s\S]*?</score-part>', _keep, head)
    body = head + '\n'.join(out) + '\n</score-partwise>'
    return body


# ---------------------------------------------------------------------------
# Duration arithmetic. Adding, deleting or re-rhythmicising a note shifts the timing of everything
# after it in the bar, so every op below is DURATION-NEUTRAL by construction: the bar's total is
# unchanged, which makes a broken bar unrepresentable rather than merely detectable.
# ---------------------------------------------------------------------------

TYPES = [('maxima', 32), ('long', 16), ('breve', 8), ('whole', 4), ('half', 2), ('quarter', 1),
         ('eighth', .5), ('16th', .25), ('32nd', .125), ('64th', .0625), ('128th', .03125)]


def divisions(raw):
    """Divisions per QUARTER note, from the first <divisions> in the file."""
    m = re.search(r'<divisions>(\d+)</divisions>', raw)
    return int(m.group(1)) if m else 1


def dur_to_type(dur, div):
    """(type_name, n_dots) for a duration, or None if it is not a plain or dotted note value."""
    q = dur / div
    for name, beats in TYPES:
        if abs(q - beats) < 1e-9:
            return name, 0
        if abs(q - beats * 1.5) < 1e-9:
            return name, 1
        if abs(q - beats * 1.75) < 1e-9:
            return name, 2
    return None


def note_duration(block):
    m = re.search(r'<duration>(\d+)</duration>', block)
    return int(m.group(1)) if m else 0


def _set_block_duration(block, dur, div):
    """Rewrite one <note> block's duration, <type> and dots to match."""
    out = re.sub(r'<duration>\d+</duration>', f'<duration>{dur}</duration>', block)
    tt = dur_to_type(dur, div)
    out = re.sub(r'\s*<dot\s*/>', '', out)
    if tt:
        name, dots = tt
        if re.search(r'<type>[^<]*</type>', out):
            out = re.sub(r'<type>[^<]*</type>', f'<type>{name}</type>', out)
        else:
            out = out.replace('</duration>', f'</duration>\n    <type>{name}</type>', 1)
        if dots:
            out = re.sub(r'(</type>)', r'\1' + '\n    <dot />' * dots, out, count=1)
    return out


def _staff_voice(block, last):
    """(staff, voice) for a note block. A CHORD MEMBER carries no <voice>/<staff> tag and inherits
    from the preceding note. Defaulting those to voice 1 invented a phantom "staff 2 voice 1" that
    summed to zero, and the validator then failed 38 of 40 bars of an UNEDITED score."""
    s = re.search(r'<staff>(\d+)</staff>', block)
    v = re.search(r'<voice>(\d+)</voice>', block)
    return (int(s.group(1)) if s else last[0], int(v.group(1)) if v else last[1])


def measure_notes(raw, measure, staff=None, voice=None, part=0):
    """[(span, block)] for every <note> element (INCLUDING RESTS) in a measure, in document order.

    Rests are included here on purpose: duration arithmetic has to account for them. `find_note`
    counts pitched notes only, matching music21. Do not mix the two indexings up - that trap has
    already cost this project an hour (see the module docstring).
    """
    sp = measure_span(raw, measure, part)
    if not sp:
        return []
    blk = raw[sp[0]:sp[1]]
    out, last = [], (1, 1)
    for m in NOTE_RE.finditer(blk):
        t = m.group(0)
        last = _staff_voice(t, last)
        if staff is not None and last[0] != staff:
            continue
        if voice is not None and last[1] != voice:
            continue
        out.append(((sp[0] + m.start(), sp[0] + m.end()), t))
    return out


def voice_total(raw, measure, staff=1, voice=1, part=0):
    """Sum of durations in one voice of a measure. <chord> notes do not advance time."""
    tot = 0
    for _, b in measure_notes(raw, measure, staff, voice, part):
        if '<chord' in b:
            continue
        tot += note_duration(b)
    return tot


def expected_duration(raw, measure, part=0):
    """What one voice of this measure SHOULD sum to, from the governing time signature."""
    div = divisions(raw)
    beats = beat_type = None
    ps = parts(raw)
    scope = raw[ps[part_index(raw, part)][3]:ps[part_index(raw, part)][4]] if ps else raw
    for m in MEASURE_RE.finditer(scope):
        if int(m.group(1)) > measure:
            break
        b = re.search(r'<beats>(\d+)</beats>', m.group(0))
        t = re.search(r'<beat-type>(\d+)</beat-type>', m.group(0))
        if b and t:
            beats, beat_type = int(b.group(1)), int(t.group(1))
    if not beats:
        return None
    return int(div * 4 * beats / beat_type)


def validate_edit(before, after, measure, part=0):
    """THE REAL GATE: [] if the edit left every voice's total duration unchanged.

    Absolute validation is the wrong test. A SECONDARY voice legitimately need not fill the bar -
    Sibelius often omits explicit rests for the remainder - so "voice 3 sums to 768, expected 1024"
    is normal notation, not damage. Checking absolute correctness flagged clean scores; checking
    that the edit is duration-NEUTRAL flags exactly what we care about and nothing else.
    """
    def totals(raw):
        out, last = {}, (1, 1)
        for _, b in measure_notes(raw, measure, part=part):
            last = _staff_voice(b, last)
            if '<chord' not in b:
                out[last] = out.get(last, 0) + note_duration(b)
        return out
    a, b = totals(before), totals(after)
    bad = []
    for k in sorted(set(a) | set(b)):
        if a.get(k, 0) != b.get(k, 0):
            bad.append(f'bar {measure} staff {k[0]} voice {k[1]}: duration changed '
                       f'{a.get(k, 0)} -> {b.get(k, 0)}; the edit must be duration-neutral')
    return bad


def validate(raw, measure, part=0):
    """Absolute check. Only OVERFULL voices are unambiguously broken - see validate_edit."""
    exp = expected_duration(raw, measure, part)
    if exp is None:
        return []
    bad = []
    seen, last = set(), (1, 1)
    for _, b in measure_notes(raw, measure, part=part):
        last = _staff_voice(b, last)
        seen.add(last)
    for st, vo in sorted(seen):
        got = voice_total(raw, measure, st, vo, part)
        if got > exp:
            bad.append(f'bar {measure} staff {st} voice {vo}: sums to {got}, OVERFULL '
                       f'(expected at most {exp})')
    return bad


def _blank_note(template, step, alter, octave, dur, div):
    """A new <note> cloned from a neighbour, so it inherits voice, staff and formatting."""
    b = re.sub(r'<rest\s*/>',
               f'<pitch>\n     <step>{step}</step>'
               + (f'\n     <alter>{alter}</alter>' if alter else '')
               + f'\n     <octave>{octave}</octave>\n    </pitch>', template)
    if '<pitch>' not in b:
        b = re.sub(r'<pitch>[\s\S]*?</pitch>',
                   f'<pitch>\n     <step>{step}</step>'
                   + (f'\n     <alter>{alter}</alter>' if alter else '')
                   + f'\n     <octave>{octave}</octave>\n    </pitch>', b)
    else:
        b = re.sub(r'<step>\w</step>', f'<step>{step}</step>', b)
        b = re.sub(r'<octave>-?\d+</octave>', f'<octave>{octave}</octave>', b)
        if re.search(r'<alter>-?\d+</alter>', b):
            b = (re.sub(r'\s*<alter>-?\d+</alter>', '', b) if alter == 0
                 else re.sub(r'<alter>-?\d+</alter>', f'<alter>{alter}</alter>', b))
        elif alter:
            b = b.replace(f'<step>{step}</step>', f'<step>{step}</step>\n     <alter>{alter}</alter>', 1)
    # a clone must never inherit the neighbour's ties, beams or notations
    b = re.sub(r'\s*<tie[^>]*/>', '', b)
    b = re.sub(r'\s*<notations>[\s\S]*?</notations>', '', b)
    b = re.sub(r'\s*<beam[^>]*>[^<]*</beam>', '', b)
    return _set_block_duration(b, dur, div)


def split_note(raw, span, pitches):
    """Replace one note with several summing to the SAME duration - duration-neutral by design.

    `pitches` is a list of (step, alter, octave) or None to keep the original pitch. The parent
    duration is divided as evenly as the division count allows, remainder onto the first note.
    This is how a new note gets added without shifting anything after it in the bar.
    """
    div = divisions(raw)
    blk = raw[span[0]:span[1]]
    # Splitting strips ties from the fragments, which would silently orphan a tie coming from the
    # previous bar. The model spotted this before the code did.
    st = tie_state(blk)
    if st:
        raise ValueError(f'that note is tied ({st}); splitting it would orphan the tie. '
                         f'Pick an untied note.')
    total = note_duration(blk)
    n = len(pitches)
    if n < 2:
        raise ValueError('split needs at least two parts')
    if total % n:
        # keep it representable: only split into pieces that are real note values
        share = total // n
        if dur_to_type(share, div) is None:
            raise ValueError(f'cannot split a duration of {total} into {n} writable note values')
    share = total // n
    durs = [share] * n
    durs[0] += total - share * n
    if any(dur_to_type(d, div) is None for d in durs):
        raise ValueError(f'splitting into {n} gives durations that are not writable note values')
    cur = read_pitch(blk)
    out = []
    for p, d in zip(pitches, durs):
        if p is None:
            out.append(_set_block_duration(re.sub(r'\s*<tie[^>]*/>', '',
                       re.sub(r'\s*<notations>[\s\S]*?</notations>', '', blk)), d, div))
        else:
            out.append(_blank_note(blk, p[0], p[1], p[2], d, div))
    return raw[:span[0]] + '\n   '.join(out) + raw[span[1]:], cur


def merge_notes(raw, measure, index, count, staff=None, voice=None, part=0):
    """Replace `count` consecutive pitched notes with the FIRST one, lengthened to their total.

    Duration-neutral. This is how a note is deleted without shifting the bar: its time is absorbed
    by its neighbour rather than removed.
    """
    div = divisions(raw)
    spans = []
    for i in range(index, index + count):
        sp = find_note(raw, measure, i, staff, voice, part)
        if not sp:
            raise ValueError(f'no pitched note {i} in bar {measure}')
        spans.append(sp)
    if any('<chord' in raw[s[0]:s[1]] for s in spans):
        raise ValueError('merging chord members is not supported')
    if any(tie_state(raw[s[0]:s[1]]) for s in spans):
        raise ValueError('one of those notes is tied; merging would orphan the tie')
    total = sum(note_duration(raw[s[0]:s[1]]) for s in spans)
    if dur_to_type(total, div) is None:
        raise ValueError(f'merged duration {total} is not a writable note value')
    keep = re.sub(r'\s*<tie[^>]*/>', '', raw[spans[0][0]:spans[0][1]])
    return raw[:spans[0][0]] + _set_block_duration(keep, total, div) + raw[spans[-1][1]:]


def to_rest(raw, span):
    """Turn a note into a rest of the same duration. Duration-neutral."""
    b = raw[span[0]:span[1]]
    if '<rest' in b:
        return raw
    b = re.sub(r'<pitch>[\s\S]*?</pitch>', '<rest />', b)
    b = re.sub(r'\s*<tie[^>]*/>', '', b)
    b = re.sub(r'\s*<notations>[\s\S]*?</notations>', '', b)
    return raw[:span[0]] + b + raw[span[1]:]


# ---------------------------------------------------------------------------
# Notations: articulations, ornaments, slurs. All duration-neutral - they attach to notes and never
# change timing - so none of them can break a bar.
#
# NOTE the two different tie elements. <tie> is the SOUNDING tie and is a direct child of <note>;
# <tied> is the VISUAL slur-shape and lives inside <notations>. tie_state() reads <tie>. Do not
# conflate them.
# ---------------------------------------------------------------------------

# Whitelists, because the model supplies these strings and they end up in the file verbatim.
ARTICULATIONS = {'accent', 'strong-accent', 'staccato', 'tenuto', 'detached-legato',
                 'staccatissimo', 'spiccato', 'scoop', 'plop', 'doit', 'falloff',
                 'breath-mark', 'caesura', 'stress', 'unstress'}
ORNAMENTS = {'trill-mark', 'turn', 'delayed-turn', 'inverted-turn', 'shake', 'mordent',
             'inverted-mordent', 'schleifer', 'tremolo'}


def _indent_of(block):
    """The indentation Sibelius used for this note's children, so insertions match the file."""
    m = re.search(r'\n(\s+)<duration>', block)
    return m.group(1) if m else '    '


def _ensure_notations(block, inner):
    """Insert `inner` into the note's <notations>, creating the element if absent.

    Rebuilds the block with consistent indentation rather than splicing a string in beside whatever
    whitespace happened to be there - naive splicing left stray blank lines and closing tags jammed
    onto the end of the previous element.
    """
    ind = _indent_of(block)
    m = re.search(r'<notations>([\s\S]*?)</notations>', block)
    if m:
        kids = [x.strip() for x in re.findall(r'<[a-z-]+(?:\s[^>]*)?/>|<[a-z-]+>[\s\S]*?</[a-z-]+>',
                                              m.group(1))]
        kids.append(inner.strip())
        body = ''.join(f'\n{ind} {k}' for k in kids)
        return block[:m.start()] + f'<notations>{body}\n{ind}</notations>' + block[m.end():]
    return re.sub(r'\n\s*</note>',
                  f'\n{ind}<notations>\n{ind} {inner.strip()}\n{ind}</notations>'
                  f'\n{ind[:-1] if len(ind) > 1 else ""}</note>', block, count=1)


def add_articulation(raw, span, kind):
    """staccato / accent / tenuto / marcato etc. on one note. Duration-neutral."""
    kind = {'marcato': 'strong-accent'}.get(kind, kind)
    if kind not in ARTICULATIONS:
        raise ValueError(f'unknown articulation {kind!r}; known: {", ".join(sorted(ARTICULATIONS))}')
    b = raw[span[0]:span[1]]
    if re.search(rf'<{kind}\s*/>', b):
        raise ValueError(f'that note already has a {kind}')
    ind = _indent_of(b)
    m = re.search(r'<articulations>([\s\S]*?)</articulations>', b)
    if m:
        kids = [x.strip() for x in re.findall(r'<[a-z-]+(?:\s[^>]*)?/>', m.group(1))] + [f'<{kind} />']
        body = ''.join(f'\n{ind}  {k}' for k in kids)
        nb = b[:m.start()] + f'<articulations>{body}\n{ind} </articulations>' + b[m.end():]
    else:
        nb = _ensure_notations(b, f'<articulations>\n{ind}  <{kind} />\n{ind} </articulations>')
    return raw[:span[0]] + nb + raw[span[1]:]


def add_ornament(raw, span, kind):
    """trill-mark / mordent / turn etc. on one note. Duration-neutral."""
    if kind not in ORNAMENTS:
        raise ValueError(f'unknown ornament {kind!r}; known: {", ".join(sorted(ORNAMENTS))}')
    b = raw[span[0]:span[1]]
    if re.search(rf'<{kind}\s*/>', b):
        raise ValueError(f'that note already has a {kind}')
    ind = _indent_of(b)
    m = re.search(r'<ornaments>([\s\S]*?)</ornaments>', b)
    if m:
        kids = [x.strip() for x in re.findall(r'<[a-z-]+(?:\s[^>]*)?/>', m.group(1))] + [f'<{kind} />']
        body = ''.join(f'\n{ind}  {k}' for k in kids)
        nb = b[:m.start()] + f'<ornaments>{body}\n{ind} </ornaments>' + b[m.end():]
    else:
        nb = _ensure_notations(b, f'<ornaments>\n{ind}  <{kind} />\n{ind} </ornaments>')
    return raw[:span[0]] + nb + raw[span[1]:]


def remove_notation(raw, span, kind):
    """Remove one articulation or ornament, tidying now-empty wrappers."""
    b = raw[span[0]:span[1]]
    if not re.search(rf'<{re.escape(kind)}\s*/>', b):
        raise ValueError(f'that note has no {kind}')
    nb = re.sub(rf'\s*<{re.escape(kind)}\s*/>', '', b, count=1)
    for w in ('articulations', 'ornaments', 'notations'):
        nb = re.sub(rf'\s*<{w}>\s*</{w}>', '', nb)
    return raw[:span[0]] + nb + raw[span[1]:]


def _free_slur_number(raw, measure, span_lo, span_hi):
    """A slur number not already open across this range. Overlapping slurs must differ."""
    used = set()
    for m in MEASURE_RE.finditer(raw):
        if span_lo <= int(m.group(1)) <= span_hi:
            used |= {int(x) for x in re.findall(r'<slur[^>]*number="(\d+)"', m.group(0))}
    n = 1
    while n in used:
        n += 1
    return n


def add_slur(raw, measure, from_index, to_index, staff=None, voice=None, to_measure=None,
             part=0):
    """Slur from one note to another. Duration-neutral.

    Applied END FIRST: inserting at the start would shift every byte offset after it, so the second
    span would point at the wrong place. Same reason edits elsewhere are applied back-to-front.
    """
    m2 = measure if to_measure is None else to_measure
    a = find_note(raw, measure, from_index, staff, voice, part)
    b = find_note(raw, m2, to_index, staff, voice, part)
    if not a:
        raise ValueError(f'no pitched note {from_index} in bar {measure}')
    if not b:
        raise ValueError(f'no pitched note {to_index} in bar {m2}')
    if b[0] <= a[0]:
        raise ValueError('the slur must end after it starts')
    n = _free_slur_number(raw, measure, min(measure, m2), max(measure, m2))
    out = raw[:b[0]] + _ensure_notations(raw[b[0]:b[1]],
                                         f'<slur type="stop" number="{n}" />') + raw[b[1]:]
    out = out[:a[0]] + _ensure_notations(out[a[0]:a[1]],
                                         f'<slur type="start" number="{n}" />') + out[a[1]:]
    return out


# ---------------------------------------------------------------------------
# WRITING NEW MATERIAL. Everything above edits notes that already exist; this creates them, which
# is what "help me finish this piece" actually requires. 209 scores in the corpus stop early and
# leave 8+ empty bars, and 452 are more than 40% empty.
#
# The event syntax is deliberately the SAME compact notation the model already reads everywhere in
# [COMPUTED] and [CORPUS]:  "F#4:0.5"  "[C4 E4 G4]:2"  "r:1"  - pitch(es) then duration in quarters.
# ---------------------------------------------------------------------------

EVENT_RE = re.compile(r'^(?:\[([^\]]+)\]|([A-G][#\-b]*-?\d+)|(r))\s*:\s*'
                      r'(\d+(?:\.\d+)?|w|h\.?|q\.?|8\.?|16\.?|32|64)$')
# A tuplet group: "{3:2 E5:0.5 D5:0.5 B4:0.5}" = three eighths in the time of two.
TUPLET_RE = re.compile(r'^\{\s*(\d+)\s*:\s*(\d+)\s+(.+?)\s*\}$')


# The SAME duration names bar_listing() prints, so the model writes in the notation it reads.
# It emitted "B3:q" because the listing shows "0:F#5:q" - reading one syntax and requiring another
# was an inconsistency of mine, not a mistake of the model's.
DURWORD = {'w': 4.0, 'h': 2.0, 'q': 1.0, '8': 0.5, '16': 0.25, '32': 0.125, '64': 0.0625,
           'h.': 3.0, 'q.': 1.5, '8.': 0.75, '16.': 0.375}


def parse_event(tok):
    """'F#4:0.5' | 'F#4:q' | '[C4 E4 G4]:2' | 'r:1'  ->  ([pitches] or None, quarters)."""
    m = EVENT_RE.match(tok.strip())
    if not m:
        raise ValueError(f'cannot parse event {tok!r}; expected e.g. "F#4:0.5", "F#4:q", '
                         f'"[C4 E4]:2", "r:1"')
    d = m.group(4)
    q = DURWORD[d] if d in DURWORD else float(d)
    if q <= 0:
        raise ValueError(f'{tok!r} has a non-positive duration')
    if m.group(3):
        return None, q
    names = [m.group(2)] if m.group(2) else m.group(1).split()
    out = []
    for nm in names:
        p = re.match(r'^([A-G])([#\-b]*)(-?\d+)$', nm.strip())
        if not p:
            raise ValueError(f'cannot parse pitch {nm!r} in {tok!r}')
        alt = p.group(2).count('#') - p.group(2).count('-') - p.group(2).count('b')
        out.append((p.group(1), alt, int(p.group(3))))
    return out, q


def _new_note(template, pitches, dur, div, is_chord=False, tup=None, written=None,
              tup_pos=None):
    """As below, plus tuplet support.

    A tuplet note carries THREE things Sibelius writes and all three are required or the bar reads
    wrong: <duration> is the SOUNDING length (256/3 for a triplet eighth, rounded), <type> is the
    WRITTEN value (eighth), and <time-modification> says 3-in-the-space-of-2. The first and last
    note of the group also carry <tuplet type="start"/stop">.
    """
    return _new_note_impl(template, pitches, dur, div, is_chord, tup, written, tup_pos)


ADDED_COLOR = '#0B8A3E'      # green, like an added line in a diff


def _new_note_impl(template, pitches, dur, div, is_chord=False, tup=None, written=None,
                   tup_pos=None, colour_new=False):
    """Build a <note> from scratch, cloning voice/staff/instrument from a neighbour in the same
    voice. Engraving positions are dropped - they belong to the note being replaced, not this one."""
    def grab(tag):
        m = re.search(rf'<{tag}[^>]*/>|<{tag}>[^<]*</{tag}>', template)
        return [m.group(0)] if m else []
    keep_pre = grab('instrument') + grab('voice')      # before <type>
    keep_post = grab('staff')                          # after <time-modification>
    ind = _indent_of(template)
    body = []
    if is_chord:
        body.append('<chord />')
    if pitches is None:
        body.append('<rest />')
    else:
        st, al, oc = pitches
        body.append('<pitch>')
        body.append(f' <step>{st}</step>')
        if al:
            body.append(f' <alter>{al}</alter>')
        body.append(f' <octave>{oc}</octave>')
        body.append('</pitch>')
    body.append(f'<duration>{dur}</duration>')
    # MusicXML fixes the order of a <note>'s children:
    #   pitch, duration, tie, instrument, voice, type, dot, accidental, time-modification,
    #   stem, staff, beam, notations
    # Emitting <voice>/<instrument> AFTER <type> made music21 silently ignore
    # <time-modification>: the triplets SOUNDED right but were not tuplets. Order is not cosmetic.
    body += keep_pre
    tt = dur_to_type(written if written is not None else dur, div)
    if tt:
        body.append(f'<type>{tt[0]}</type>')
        body += ['<dot />'] * tt[1]
    if tup:
        body.append('<time-modification>')
        body.append(f' <actual-notes>{tup[0]}</actual-notes>')
        body.append(f' <normal-notes>{tup[1]}</normal-notes>')
        if tt:
            body.append(f' <normal-type>{tt[0]}</normal-type>')
        body.append('</time-modification>')
    body += keep_post
    if tup and tup_pos in ('start', 'stop'):
        body.append('<notations>')
        body.append(f' <tuplet type="{tup_pos}" bracket="no" number="1" />')
        body.append('</notations>')
    # Colour every note we WRITE. MusicXML carries a `color` attribute and Sibelius,
    # Dorico and MuseScore all honour it - Brian's own file already colours every note
    # "#000000". So additions show up GREEN in his actual score, in context, instead of in
    # a detached HTML tab. This is the Claude Code diff, inside the notation program.
    tag = f'<note color="{ADDED_COLOR}">' if colour_new else '<note>'
    return f'{tag}\n{ind}' + f'\n{ind}'.join(body) + f'\n{ind[:-1] or ""}</note>'


def _expand(events):
    """-> [(pitches, written_quarters, tuplet_or_None, position_in_group)] in order."""
    out = []
    for tok in events:
        t = tok.strip() if isinstance(tok, str) else tok
        m = TUPLET_RE.match(t) if isinstance(t, str) else None
        if m:
            act, norm = int(m.group(1)), int(m.group(2))
            inner = m.group(3).split()
            if len(inner) < 2:
                raise ValueError(f'tuplet {tok!r} needs at least two notes')
            for k, e in enumerate(inner):
                p, q = parse_event(e)
                pos = 'start' if k == 0 else ('stop' if k == len(inner) - 1 else None)
                out.append((p, q, (act, norm), pos))
        else:
            p, q = parse_event(t)
            out.append((p, q, None, None))
    return out


def _offsets(spans, div):
    """Beat offsets (in divisions) at which events start, for a helpful error message."""
    out, acc = [], 0
    for _, blk in spans:
        if '<chord' in blk:
            continue
        out.append(acc)
        acc += note_duration(blk)
    return out


def write_notes(raw, measure, staff, voice, events, allow_partial=False, from_beat=0.0,
                part=0):
    """Replace (measure, staff, voice) with `events`. THE op for finishing a piece.

    `from_beat` KEEPS everything before that point in the bar and writes from there on, so a phrase
    can be continued MID-BAR. Brian: "measure 54, there's clearly a pattern going on - why wasn't
    something inserted on the second eighth note and continuing the phrase, why does it have to
    start in a completely new bar?" Beats are counted in QUARTER NOTES from the start of the bar,
    so from_beat=0.5 means "keep the first eighth, write the rest".

    `events` is a list of compact tokens: ["E4:1", "F#4:0.5", "r:0.5", "[B3 D#4 F#4]:2"].
    Durations are in quarter notes and MUST sum to the bar, or the bar is silently broken - so this
    is checked before anything is written, and refused with the actual numbers if it does not.
    """
    div = divisions(raw)
    spans = measure_notes(raw, measure, staff, voice, part)
    if not spans:
        raise ValueError(f'bar {measure} has no staff {staff} voice {voice} to write into')
    # Split point. Everything sounding before `from_beat` stays exactly where it is; the write
    # replaces from there to the end of the bar.
    prefix, tail_spans, acc, split_at = [], [], 0, None
    if from_beat:
        want = int(round(from_beat * div))
        for i, (sp, blk) in enumerate(spans):
            if '<chord' in blk:
                continue        # a chord member is the same event as the note before it
            if acc == want:
                split_at = i
                break
            nd = note_duration(blk)
            if acc + nd > want:
                # the split lands INSIDE this event. A rest can be divided; a note cannot.
                if '<rest' not in blk:
                    raise ValueError(
                        f'from_beat={from_beat:g} falls inside a note in bar {measure} staff '
                        f'{staff} voice {voice}; note boundaries are at '
                        f'{", ".join(str(o / div) for o in _offsets(spans, div))}')
                head = want - acc
                if dur_to_type(head, div) is None:
                    raise ValueError(f'splitting that rest needs a {head / div:g}-quarter rest, '
                                     f'which is not a writable note value')
                prefix.append(_set_block_duration(blk, head, div))
                split_at = i
                break
            acc += nd
        if split_at is None:
            if acc == want:
                split_at = len(spans)
            else:
                raise ValueError(f'from_beat={from_beat:g} is past the end of bar {measure} '
                                 f'staff {staff} voice {voice}')
        tail_spans = spans[split_at:]
        if not tail_spans:
            raise ValueError(f'nothing to replace after beat {from_beat:g} in bar {measure}')
    parsed = _expand(events)
    # sounding length: a tuplet note lasts written * normal/actual
    def sound(q, tup):
        return q * div * (tup[1] / tup[0] if tup else 1)
    total = int(round(sum(sound(q, t) for _, q, t, _ in parsed)))
    exp = expected_duration(raw, measure, part)
    have = sum(note_duration(b) for _, b in spans if '<chord' not in b)
    target = have if allow_partial else (exp if exp is not None else have)
    if from_beat:
        target -= int(round(from_beat * div))
    if total != target:
        # Itemise. "totals 3.66797 but needs 4" leaves the model guessing which event is wrong;
        # the per-event breakdown shows it, and tuplet arithmetic is where it goes wrong.
        parts = []
        for ev, (_, q, tup, _) in zip(
                [e for e in events for _ in range(1)], parsed[:len(events)]):
            parts.append(f'{ev}={sound(q, tup) / div:g}')
        run = ', '.join(f'{tok}={sum(sound(q, t) for _, q, t, _ in _expand([tok])) / div:g}'
                        for tok in events)
        raise ValueError(
            f'those events total {total / div:g} quarter notes but bar {measure} staff {staff} '
            f'voice {voice} needs {target / div:g}. Sounding lengths: {run}. '
            f'(A tuplet "{{3:2 a:0.5 b:0.5 c:0.5}}" sounds as 1 quarter, not 1.5.) '
            f'Adjust so they sum to {target / div:g}.')
    for pitches, q, tup, _ in parsed:
        if dur_to_type(int(round(q * div)), div) is None:
            raise ValueError(f'{q:g} quarter notes is not a writable note value; use plain or '
                             f'dotted values, or a tuplet like "{{3:2 E5:0.5 D5:0.5 B4:0.5}}"')
    template = (tail_spans[0][1] if from_beat else spans[0][1])
    blocks = []
    # Distribute the rounding inside each tuplet so the GROUP sums exactly - Sibelius writes
    # 85/85/86 for a triplet at 256 divisions, not 85/85/85, which would lose a division.
    i = 0
    while i < len(parsed):
        tup = parsed[i][2]
        if tup is None:
            pitches, q, _, _ = parsed[i]
            d = int(round(q * div))
            if pitches is None:
                blocks.append(_new_note(template, None, d, div))
            else:
                for k, p in enumerate(pitches):
                    blocks.append(_new_note(template, p, d, div, is_chord=(k > 0)))
            i += 1
            continue
        j = i
        while j < len(parsed) and parsed[j][2] == tup and not (j > i and parsed[j][3] == 'start'):
            j += 1
            if j - 1 > i and parsed[j - 1][3] == 'stop':
                break
        grp = parsed[i:j]
        want = int(round(sum(q * div * tup[1] / tup[0] for _, q, _, _ in grp)))
        durs = [int(q * div * tup[1] / tup[0]) for _, q, _, _ in grp]
        for k in range(want - sum(durs)):
            durs[-(k + 1)] += 1
        for (pitches, q, _, pos), d in zip(grp, durs):
            w = int(round(q * div))
            if pitches is None:
                blocks.append(_new_note(template, None, d, div, tup=tup, written=w, tup_pos=pos))
            else:
                for k, p in enumerate(pitches):
                    blocks.append(_new_note(template, p, d, div, is_chord=(k > 0), tup=tup,
                                            written=w, tup_pos=pos if k == 0 else None))
        i = j
    ind = _indent_of(template)[:-1] or ''
    if from_beat:
        lo, hi = tail_spans[0][0][0], tail_spans[-1][0][1]
        blocks = prefix + blocks       # a split rest's remainder must be RE-EMITTED, not dropped
    else:
        lo, hi = spans[0][0][0], spans[-1][0][1]
    return raw[:lo] + f'\n{ind}'.join(blocks) + raw[hi:]


def append_measures(raw, count, after=None):
    """Add `count` empty bars to the end of every part. Extends a piece past its final barline.

    209 corpus scores stop early with empty bars already present, but many others end AT their last
    written bar and simply cannot be continued without this.

    The final double barline (`light-heavy`) must MOVE to the new last measure, or the piece keeps
    its ending in the middle. Each new bar is whole rests, one per (staff, voice) that the previous
    last bar used, with <backup> between them - the structure Sibelius itself writes.
    """
    if count < 1:
        raise ValueError('count must be at least 1')
    div = divisions(raw)
    out = raw
    for pm in list(re.finditer(r'<part id="[^"]*">[\s\S]*?</part>', out))[::-1]:
        part = pm.group(0)
        ms = list(MEASURE_RE.finditer(part))
        if not ms:
            continue
        last = ms[-1]
        lastno = int(last.group(1))
        blk = last.group(0)
        dur = expected_duration(raw, lastno) or div * 4
        # which (staff, voice) pairs does this part actually use?
        pairs, seen = [], (1, 1)
        for nm in NOTE_RE.finditer(blk):
            seen = _staff_voice(nm.group(0), seen)
            if seen not in pairs:
                pairs.append(seen)
        if not pairs:
            pairs = [(1, 1)]
        inst = re.search(r'<instrument[^>]*/>', blk)
        inst = inst.group(0) if inst else ''
        # the final barline moves from the old last bar to the new one
        barline = re.search(r'<barline[\s\S]*?</barline>', blk)
        bl = barline.group(0) if barline else ''
        newpart = part
        if bl:
            newpart = newpart[:last.start()] + blk.replace(bl, '').replace('\n   \n', '\n') \
                      + newpart[last.end():]
        added = []
        for i in range(1, count + 1):
            body = []
            for k, (st, vo) in enumerate(pairs):
                if k:
                    body.append(f'   <backup>\n    <duration>{dur}</duration>\n   </backup>')
                tt = dur_to_type(dur, div)
                body.append(
                    '   <note>\n    <rest />\n'
                    f'    <duration>{dur}</duration>\n'
                    + (f'    {inst}\n' if inst else '')
                    + f'    <voice>{vo}</voice>\n'
                    + (f'    <type>{tt[0]}</type>\n' if tt else '')
                    + f'    <staff>{st}</staff>\n   </note>')
            tail = f'\n   {bl}' if (bl and i == count) else ''
            added.append(f'  <measure number="{lastno + i}">\n' + '\n'.join(body)
                         + tail + '\n  </measure>')
        newpart = newpart.replace('\n </part>', '\n' + '\n'.join(added) + '\n </part>')
        out = out[:pm.start()] + newpart + out[pm.end():]
    return out


def add_hairpin(raw, measure, kind='crescendo', staff=1, voice=1, part=0, stop_measure=None):
    """A crescendo or diminuendo wedge. Brian's bars 9-16 carry 32 of them and my drafts had none -
    the hairpins are how he shapes a phrase, and a passage without them is dynamically flat."""
    if kind not in ('crescendo', 'diminuendo'):
        raise ValueError("kind must be 'crescendo' or 'diminuendo'")
    end = measure if stop_measure is None else stop_measure
    n = _free_slur_number(raw, measure, min(measure, end), max(measure, end))

    def wedge(m, ty):
        sp = measure_span(raw2[0], m, part)
        if not sp:
            return
        blk = raw2[0][sp[0]:sp[1]]
        ins = blk.find('>') + 1 if ty == 'crescendo' or m == measure else len(blk) - len('</measure>')
        d = (f'\n   <direction placement="below">\n    <direction-type>\n'
             f'     <wedge type="{ty}" number="{n}" />\n    </direction-type>\n'
             f'    <voice>{voice}</voice>\n    <staff>{staff}</staff>\n   </direction>')
        raw2[0] = raw2[0][:sp[0]] + blk[:ins] + d + blk[ins:] + raw2[0][sp[1]:]

    raw2 = [raw]
    # stop first: inserting at the start would move the later offsets
    sp = measure_span(raw2[0], end, part)
    if sp:
        blk = raw2[0][sp[0]:sp[1]]
        ins = blk.rfind('</measure>')
        d = (f'   <direction placement="below">\n    <direction-type>\n'
             f'     <wedge type="stop" number="{n}" />\n    </direction-type>\n'
             f'    <voice>{voice}</voice>\n    <staff>{staff}</staff>\n   </direction>\n  ')
        raw2[0] = raw2[0][:sp[0]] + blk[:ins] + d + blk[ins:] + raw2[0][sp[1]:]
    wedge(measure, kind)
    return raw2[0]
