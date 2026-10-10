"""Tests for the surgical MusicXML editor. Every test maps to a bug that shipped or a guard that
must not regress. Run: python test_xmledit.py
"""
import re
import xmledit as x

SRC = '/Users/bdogellis/Documents/Score Exports/MusicXML/Briello no 36 in D# minor.musicxml'
QRT = '/Users/bdogellis/Documents/Score Exports/MusicXML/9 16 String Quartet.musicxml'
RAW = open(SRC).read()
QRAW = open(QRT).read()


# --- the indexing trap ------------------------------------------------------

def test_find_note_skips_rests():
    """SHIPPED BUG: a MusicXML <note> includes RESTS; music21's .notes excludes them. Indexing raw
    <note> blocks as if they matched music21 indices edits the WRONG NOTE. Bar 5's first <note>
    element is an eighth rest; the E#4 is the second."""
    blk = RAW[x.measure_span(RAW, 5)[0]:x.measure_span(RAW, 5)[1]]
    first_raw = re.search(r'<note[\s\S]*?</note>', blk).group(0)
    assert '<rest' in first_raw, 'fixture changed: bar 5 should open with a rest'
    sp = x.find_note(RAW, 5, 0)
    assert '<rest' not in RAW[sp[0]:sp[1]], 'find_note returned a rest'
    assert x.read_pitch(RAW[sp[0]:sp[1]]) == 'E#4'


def test_chord_members_inherit_voice_and_staff():
    """SHIPPED BUG: chord members carry no <voice>/<staff> tag. Defaulting them to voice 1 invented
    a phantom 'staff 2 voice 1' that summed to zero, failing 38 of 40 bars of a CLEAN score."""
    pairs = set()
    last = (1, 1)
    for _, b in x.measure_notes(RAW, 11):
        last = x._staff_voice(b, last)
        pairs.add(last)
    assert (2, 1) not in pairs, 'phantom staff-2/voice-1 is back'
    assert x.voice_total(RAW, 11, 1, 1) == x.expected_duration(RAW, 11)


# --- duration arithmetic ----------------------------------------------------

def test_dur_to_type():
    d = x.divisions(RAW)
    assert d == 256
    assert x.dur_to_type(256, d) == ('quarter', 0)
    assert x.dur_to_type(384, d) == ('quarter', 1)      # dotted
    assert x.dur_to_type(64, d) == ('16th', 0)
    assert x.dur_to_type(1024, d) == ('whole', 0)
    assert x.dur_to_type(100, d) is None                # not a writable value


def test_validate_clean_on_unedited_score():
    """The absolute validator must not flag a score nobody has touched."""
    assert [c for m in range(1, 41) for c in x.validate(RAW, m)] == []


def test_split_is_duration_neutral():
    sp = x.find_note(RAW, 13, 3, staff=1)
    new, old = x.split_note(RAW, sp, [None, ('G', 1, 5)])
    assert old == 'E#5'
    assert x.validate_edit(RAW, new, 13) == []
    got = [x.read_pitch(b) for _, b in x.measure_notes(new, 13, staff=1) if '<rest' not in b]
    assert got[3:5] == ['E#5', 'G#5'], got


def test_merge_is_duration_neutral():
    # notes 2..4, not 1..3: note 1 is a tie STOP and merge correctly refuses it (see
    # test_tied_notes_are_protected). Picking a tied span here was a bug in this test, and the
    # guard catching it is the guard working.
    new = x.merge_notes(RAW, 13, 2, 3, staff=1)
    assert x.validate_edit(RAW, new, 13) == []
    before = [b for _, b in x.measure_notes(RAW, 13, staff=1) if '<rest' not in b]
    after = [b for _, b in x.measure_notes(new, 13, staff=1) if '<rest' not in b]
    assert len(after) == len(before) - 2, f'{len(before)} -> {len(after)}'
    assert x.note_duration(after[2]) == sum(x.note_duration(b) for b in before[2:5])


def test_to_rest_is_duration_neutral():
    sp = x.find_note(RAW, 13, 5, staff=1)
    d = x.note_duration(RAW[sp[0]:sp[1]])
    new = x.to_rest(RAW, sp)
    assert x.validate_edit(RAW, new, 13) == []
    rests_before = [b for _, b in x.measure_notes(RAW, 13, staff=1) if '<rest' in b]
    rests_after = [b for _, b in x.measure_notes(new, 13, staff=1) if '<rest' in b]
    assert len(rests_after) == len(rests_before) + 1
    assert d in [x.note_duration(b) for b in rests_after], 'the rest kept the wrong duration'
    assert len([b for _, b in x.measure_notes(new, 13, staff=1) if '<rest' not in b]) == \
           len([b for _, b in x.measure_notes(RAW, 13, staff=1) if '<rest' not in b]) - 1


def test_validate_edit_catches_a_non_neutral_change():
    """Guard against validate_edit being a no-op."""
    sp = x.find_note(RAW, 13, 3, staff=1)
    blk = RAW[sp[0]:sp[1]]
    broken = RAW[:sp[0]] + blk.replace('<duration>64</duration>',
                                       '<duration>128</duration>') + RAW[sp[1]:]
    assert x.validate_edit(RAW, broken, 13), 'a lengthened note must be rejected'


# --- tie guards -------------------------------------------------------------

def test_tied_notes_are_protected():
    """A tie joins two notes that must share a pitch. Editing one end corrupts it. The MODEL spotted
    this before the code did."""
    sp = x.find_note(RAW, 13, 0, staff=1)
    assert x.tie_state(RAW[sp[0]:sp[1]]) == 'start', 'fixture changed'
    for fn, args in ((x.set_pitch, (RAW, sp, 'G', 0, 4)),
                     (x.split_note, (RAW, sp, [None, ('G', 1, 5)]))):
        try:
            fn(*args)
            raise AssertionError(f'{fn.__name__} did not refuse a tied note')
        except ValueError as e:
            assert 'tied' in str(e)
    try:
        x.merge_notes(RAW, 13, 0, 2, staff=1)
        raise AssertionError('merge_notes did not refuse a tied note')
    except ValueError as e:
        assert 'tied' in str(e)


def test_untied_notes_still_editable():
    """Guard against the tie check turning the ops into a no-op."""
    sp = x.find_note(RAW, 13, 3, staff=1)
    assert x.tie_state(RAW[sp[0]:sp[1]]) is None
    assert x.set_pitch(RAW, sp, 'G', 0, 5) != RAW


# --- notations --------------------------------------------------------------

def test_adding_a_notation_preserves_existing_children():
    """_ensure_notations REBUILDS the children list; it must not drop <tied>, slurs or tuplets that
    were already there."""
    tgt = None
    for mn in range(1, 40):
        for i in range(12):
            sp = x.find_note(QRAW, mn, i)
            if sp and '<tied' in QRAW[sp[0]:sp[1]]:
                tgt = (mn, i)
                break
        if tgt:
            break
    assert tgt, 'fixture: no tied note found'
    new = x.add_articulation(QRAW, x.find_note(QRAW, *tgt), 'staccato')
    blk = new[x.find_note(new, *tgt)[0]:x.find_note(new, *tgt)[1]]
    assert '<tied' in blk, 'the existing <tied> was destroyed'
    assert '<staccato />' in blk


def test_ensure_notations_preserves_children_when_no_articulations_block():
    """MUTATION-DRIVEN. The first version of this test picked a note that ALREADY had an
    <articulations> block, so add_articulation took its own branch and _ensure_notations was never
    exercised - a mutation that made _ensure_notations discard every existing child survived.
    The path that matters is a note with <notations> holding a slur or tie but NO articulations."""
    tgt = None
    for mn in range(1, 40):
        for i in range(12):
            sp = x.find_note(QRAW, mn, i)
            if not sp:
                continue
            blk = QRAW[sp[0]:sp[1]]
            if '<notations>' in blk and '<articulations>' not in blk and (
                    '<slur' in blk or '<tied' in blk):
                tgt = (mn, i)
                break
        if tgt:
            break
    assert tgt, 'fixture: no note with notations-but-no-articulations found'
    before = QRAW[x.find_note(QRAW, *tgt)[0]:x.find_note(QRAW, *tgt)[1]]
    kept = re.findall(r'<(slur|tied|tuplet)\b', before)
    new = x.add_articulation(QRAW, x.find_note(QRAW, *tgt), 'staccato')
    after = new[x.find_note(new, *tgt)[0]:x.find_note(new, *tgt)[1]]
    for tag in kept:
        assert f'<{tag}' in after, f'_ensure_notations destroyed the existing <{tag}>'
    assert '<staccato />' in after


def test_notation_whitelists():
    sp = x.find_note(RAW, 13, 5, staff=1)
    for fn, bad in ((x.add_articulation, 'sforzando'), (x.add_ornament, 'squiggle')):
        try:
            fn(RAW, sp, bad)
            raise AssertionError(f'{fn.__name__} accepted {bad!r}')
        except ValueError as e:
            assert 'unknown' in str(e)
    assert x.add_articulation(RAW, sp, 'marcato') != RAW      # alias for strong-accent


def test_duplicate_articulation_refused():
    sp = x.find_note(RAW, 13, 5, staff=1)
    once = x.add_articulation(RAW, sp, 'staccato')
    try:
        x.add_articulation(once, x.find_note(once, 13, 5, staff=1), 'staccato')
        raise AssertionError('a duplicate staccato was accepted')
    except ValueError as e:
        assert 'already' in str(e)


def test_remove_notation_tidies_empty_wrappers():
    sp = x.find_note(RAW, 13, 5, staff=1)
    added = x.add_articulation(RAW, sp, 'staccato')
    back = x.remove_notation(added, x.find_note(added, 13, 5, staff=1), 'staccato')
    blk = back[x.find_note(back, 13, 5, staff=1)[0]:x.find_note(back, 13, 5, staff=1)[1]]
    assert '<articulations>' not in blk and '<notations>' not in blk


def test_slur_applies_end_first_and_numbers_uniquely():
    """Inserting at the START first would shift every offset after it, so the stop would land in the
    wrong place."""
    new = x.add_slur(RAW, 13, 5, 8, staff=1)
    a = new[x.find_note(new, 13, 5, staff=1)[0]:x.find_note(new, 13, 5, staff=1)[1]]
    b = new[x.find_note(new, 13, 8, staff=1)[0]:x.find_note(new, 13, 8, staff=1)[1]]
    assert 'type="start"' in a and 'type="stop"' in b
    n1 = re.search(r'<slur type="start" number="(\d+)"', a).group(1)
    n2 = re.search(r'<slur type="stop" number="(\d+)"', b).group(1)
    assert n1 == n2
    two = x.add_slur(new, 13, 6, 7, staff=1)
    nums = set(re.findall(r'<slur[^>]*number="(\d+)"', two[x.measure_span(two, 13)[0]:
                                                          x.measure_span(two, 13)[1]]))
    assert len(nums) == 2, f'overlapping slurs must differ, got {nums}'


def test_slur_rejects_backwards_span():
    try:
        x.add_slur(RAW, 13, 8, 5, staff=1)
        raise AssertionError('a backwards slur was accepted')
    except ValueError as e:
        assert 'after it starts' in str(e)


# --- excerpting -------------------------------------------------------------

def test_excerpt_keeps_dynamics_clefs_and_key():
    """music21's score.measures() DROPS DYNAMICS, which is fatal when the edit under review IS a
    dynamic. And a piano has TWO clefs - keeping one produced 'Staff 2 cannot be found'."""
    ex = x.excerpt(QRAW, 10, 14)
    assert ex and ex.count('<measure') == QRAW[:0].count('x') + len(
        [m for m in x.MEASURE_RE.finditer(ex)])
    attrs = re.search(r'<attributes>[\s\S]*?</attributes>', ex)
    assert attrs, 'the excerpt carries no attributes block'
    assert '<key' in attrs.group(0) or '<key' in ex, 'key signature lost'
    assert len(re.findall(r'<clef', ex)) >= 1


def test_excerpt_merges_into_an_existing_attributes_block():
    """SHIPPED BUG: a bar can already hold an <attributes> containing only <staff-details>. Treating
    that as 'attributes present' skipped the injection and the excerpt rendered with no key and no
    clefs at all."""
    ex = x.excerpt(RAW, 9, 13)
    a = re.search(r'<attributes>[\s\S]*?</attributes>', ex).group(0)
    assert '<key' in a, f'key not merged in: {" ".join(a.split())[:120]}'
    assert a.count('<clef') >= 2, 'both piano clefs must be carried forward'


# --- writing new material ---------------------------------------------------

NOC = '/Users/bdogellis/Documents/Score Exports/MusicXML/Nocturne no 6 in B.musicxml'
NRAW = open(NOC).read()


def test_write_notes_fills_an_empty_bar():
    """The op that makes 'finish this piece' possible. 209 corpus scores stop early."""
    before = [b for _, b in x.measure_notes(NRAW, 95, 1, 1)]
    assert all('<rest' in b for b in before), 'fixture: bar 95 should be empty'
    new = x.write_notes(NRAW, 95, 1, 1, ['B4:1', 'C#5:0.5', 'D#5:0.5', 'E5:1', 'F#5:1'])
    got = [x.read_pitch(b) for _, b in x.measure_notes(new, 95, 1, 1)]
    assert got == ['B4', 'C#5', 'D#5', 'E5', 'F#5'], got
    assert x.validate(new, 95) == []
    assert sum(x.note_duration(b) for _, b in x.measure_notes(new, 95, 1, 1)) == 1024


def test_write_notes_refuses_a_bar_that_does_not_add_up():
    """Without this the bar is silently broken and Sibelius renders nonsense."""
    try:
        x.write_notes(NRAW, 95, 1, 1, ['B4:1', 'C#5:1'])
        raise AssertionError('a short bar was accepted')
    except ValueError as e:
        assert 'needs 4' in str(e) and 'B4:1=1' in str(e), f'error not itemised: {e}'


def test_write_notes_accepts_the_same_duration_words_the_listing_prints():
    """SHIPPED BUG: bar_listing() prints 'q'/'8'/'16' but write_notes required decimals, so the
    model wrote 'B3:q' and was refused. Reading one syntax and requiring another was MY
    inconsistency, not the model's error."""
    assert x.parse_event('B3:q') == ([('B', 0, 3)], 1.0)
    assert x.parse_event('E5:8') == ([('E', 0, 5)], 0.5)
    assert x.parse_event('A4:h.') == ([('A', 0, 4)], 3.0)
    new = x.write_notes(NRAW, 95, 1, 1, ['B4:q', 'C#5:8', 'D#5:8', 'E5:q', 'F#5:q'])
    assert x.validate(new, 95) == []


def test_chords_are_written_with_chord_tags():
    new = x.write_notes(NRAW, 95, 1, 1, ['[B3 D#4 F#4]:4'])
    blocks = [b for _, b in x.measure_notes(new, 95, 1, 1)]
    assert len(blocks) == 3
    assert '<chord' not in blocks[0] and all('<chord' in b for b in blocks[1:])
    assert sum(x.note_duration(b) for b in blocks if '<chord' not in b) == 1024


def test_tuplets_sound_right_and_ARE_tuplets():
    """SHIPPED BUG: MusicXML fixes the order of a <note>'s children. Emitting <voice>/<instrument>
    after <type> made music21 silently ignore <time-modification>, so the triplets SOUNDED correct
    and were not tuplets at all. Sounding right is not enough - assert the tuplet is recognised."""
    from music21 import converter
    import warnings
    new = x.write_notes(NRAW, 95, 1, 1,
                        ['{3:2 E5:0.5 D5:0.5 B4:0.5}', 'A4:1', '{3:2 F#4:8 E4:8 C#4:8}', 'B3:q'])
    durs = [x.note_duration(b) for _, b in x.measure_notes(new, 95, 1, 1)]
    assert durs == [85, 85, 86, 256, 85, 85, 86, 256], durs   # rounding lands on the group, as
    assert sum(durs) == 1024                                   # Sibelius writes it: 85/85/86
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        m = converter.parse(new).parts[0].measure(95)
    tup = [n for n in m.recurse().notes if n.duration.tuplets]
    assert len(tup) == 6, f'music21 sees {len(tup)} tuplet notes, want 6'
    assert tup[0].duration.type == 'eighth'
    t = tup[0].duration.tuplets[0]
    assert (t.numberNotesActual, t.numberNotesNormal) == (3, 2)


def test_note_children_are_in_musicxml_order():
    """SHIPPED BUG: MusicXML fixes the order of a <note>'s children. Emitting <voice>/<instrument>
    after <type> made music21 silently ignore <time-modification> - the triplets sounded right and
    were not tuplets. Assert the order directly, not just the audible result."""
    new = x.write_notes(NRAW, 95, 1, 1, ['{3:2 E5:8 D5:8 B4:8}', 'A4:1', 'B3:h'])
    blk = x.measure_notes(new, 95, 1, 1)[0][1]
    order = [t for t in re.findall(
        r'<(pitch|rest|duration|instrument|voice|type|dot|time-modification|staff|notations)\b', blk)]
    want = ['pitch', 'duration', 'instrument', 'voice', 'type', 'time-modification', 'staff',
            'notations']
    seen = [t for t in order if t in want]
    idx = [want.index(t) for t in seen]
    assert idx == sorted(idx), f'children out of MusicXML order: {seen}'
    assert 'voice' in seen and seen.index('voice') < seen.index('type'), seen
    assert seen.index('type') < seen.index('time-modification'), seen


def test_write_notes_leaves_the_rest_of_the_score_alone():
    new = x.write_notes(NRAW, 95, 1, 1, ['B4:4'])
    for tag in ('wedge', 'pedal', 'slur', 'tied'):
        assert len(re.findall(f'<{tag}', new)) == len(re.findall(f'<{tag}', NRAW)), tag
    assert [x.read_pitch(b) for _, b in x.measure_notes(new, 90, staff=1)] == \
           [x.read_pitch(b) for _, b in x.measure_notes(NRAW, 90, staff=1)]


SON = '/Users/bdogellis/Documents/Score Exports/MusicXML/Piano Sonata in Gm BEM 001.musicxml'
SRAW = open(SON).read()


def test_append_measures_moves_the_final_barline():
    """Without moving it the piece keeps its ending in the middle. An interior repeat barline
    (bar 34 here) must NOT be disturbed."""
    n0 = max(int(m.group(1)) for m in x.MEASURE_RE.finditer(SRAW))
    new = x.append_measures(SRAW, 4)
    n1 = max(int(m.group(1)) for m in x.MEASURE_RE.finditer(new))
    assert n1 == n0 + 4
    def bl(raw, n):
        sp = x.measure_span(raw, n)
        m = re.search(r'<barline[\s\S]*?</barline>', raw[sp[0]:sp[1]])
        return m.group(0) if m else None
    assert bl(SRAW, n0) is not None, 'fixture: last bar should carry the final barline'
    assert bl(new, n0) is None, 'the old last bar kept its final barline'
    assert bl(new, n1) is not None, 'the new last bar has no final barline'
    assert bl(new, 34) is not None and 'repeat' in bl(new, 34), 'the interior repeat was disturbed'
    assert len(re.findall(r'<barline', new)) == len(re.findall(r'<barline', SRAW))


def test_appended_bars_are_writable_and_valid():
    new = x.append_measures(SRAW, 2)
    n = max(int(m.group(1)) for m in x.MEASURE_RE.finditer(new))
    assert x.validate(new, n) == []
    w = x.write_notes(new, n, 1, 1, ['[G3 B-3 D4]:2', '[F#3 A3 D4]:2'])
    got = [x.read_pitch(b) for _, b in x.measure_notes(w, n, 1, 1)]
    assert got == ['G3', 'B-3', 'D4', 'F#3', 'A3', 'D4'], got
    assert x.validate(w, n) == []


def test_from_beat_continues_mid_bar_and_keeps_whole_chords():
    """SHIPPED BUG: bar 54 beat 1 is a FOUR-NOTE chord. Splitting on duration alone kept its first
    notehead and replaced the other three, gutting the chord. A <chord> member is the same event as
    the note before it and must share its fate."""
    before = [x.read_pitch(b) for _, b in x.measure_notes(SRAW, 54, staff=1)][:4]
    assert before == ['F#3', 'B3', 'E4', 'F#4'], f'fixture changed: {before}'
    new = x.write_notes(SRAW, 54, 1, 1,
                        ['[E3 A3 C#4 E4]:1.5', '[E3 A3 C#4 E4]:0.5', '[D3 G3 B-3 D4]:1.5'],
                        from_beat=0.5)
    assert [x.read_pitch(b) for _, b in x.measure_notes(new, 54, staff=1)][:4] == before, \
        'the kept chord was gutted'
    assert x.validate(new, 54) == [] and x.validate_edit(SRAW, new, 54) == []


def test_from_beat_splits_a_rest_and_re_emits_the_remainder():
    """A rest CAN be divided, and refusing made from_beat unusable on a resting staff - exactly
    when you want to continue mid-bar (left hand under a right-hand gesture).
    SHIPPED BUG: the shortened rest was computed and then DROPPED, so the bar summed to 896 of
    1024. The remainder must be re-emitted ahead of the new material."""
    before = [b for _, b in x.measure_notes(SRAW, 54, 2, 2)]
    assert len(before) == 1 and '<rest' in before[0], 'fixture: staff 2 should be one whole rest'
    new = x.write_notes(SRAW, 54, 2, 2, ['B1:1.5', 'B1:0.5', 'E2:1.5'], from_beat=0.5)
    got = [(x.read_pitch(b) or 'rest', x.note_duration(b))
           for _, b in x.measure_notes(new, 54, 2, 2)]
    assert got[0] == ('rest', 128), f'the split rest remainder was dropped: {got}'
    assert x.validate_edit(SRAW, new, 54) == [], x.validate_edit(SRAW, new, 54)


def test_from_beat_refuses_to_split_a_NOTE():
    """A rest divides; a note does not - splitting one would change what sounds."""
    try:
        x.write_notes(SRAW, 53, 1, 1, ['E4:1'], from_beat=0.75)
        raise AssertionError('from_beat inside a note was accepted')
    except ValueError as e:
        assert 'inside a note' in str(e) and 'boundaries are at' in str(e), e


def test_from_beat_past_the_end_of_the_bar_is_refused():
    """Superseded the old 'must land on a boundary' test, whose message improved: an off-boundary
    from_beat inside a NOTE is now caught by test_from_beat_refuses_to_split_a_NOTE, and inside a
    REST it legitimately splits. What remains genuinely invalid is a beat past the bar."""
    try:
        x.write_notes(SRAW, 54, 1, 1, ['E4:1'], from_beat=4.0)
        raise AssertionError('from_beat at/past the end of the bar was accepted')
    except ValueError as e:
        assert 'nothing to replace' in str(e) or 'past the end' in str(e), e


def test_from_beat_zero_still_replaces_the_whole_bar():
    """Guard against from_beat plumbing changing the default behaviour."""
    a = x.write_notes(SRAW, 55, 1, 1, ['[G3 B-3 D4]:4'])
    b = x.write_notes(SRAW, 55, 1, 1, ['[G3 B-3 D4]:4'], from_beat=0)
    assert a == b


def test_excerpt_carries_BOTH_clefs_when_a_clef_CHANGE_is_present():
    """SHIPPED BUG: bar 53 of the sonata carries a clef change for staff 1, so 'is a <clef> already
    present?' was true and BOTH carried clefs were skipped. Staff 2 lost its bass clef, verovio
    defaulted it to treble, and the left hand rendered on ledger lines far below the staff.
    Check PER NUMBER, not per tag."""
    ex = x.excerpt(SRAW, 53, 58)
    clefs = dict(re.findall(r'<clef number="(\d+)"[\s\S]*?<sign>(\w)</sign>', ex))
    assert clefs.get('1') and clefs.get('2'), f'both staves need a clef, got {clefs}'
    assert clefs['2'] == 'F', f'staff 2 must keep its bass clef, got {clefs}'
    # and where staff 1 legitimately IS in bass clef, that must survive too
    ex2 = x.excerpt(SRAW, 22, 26)
    c2 = dict(re.findall(r'<clef number="(\d+)"[\s\S]*?<sign>(\w)</sign>', ex2))
    assert c2.get('1') == 'F' and c2.get('2') == 'F', c2


def test_rhythm_hint_gives_the_pattern_completion():
    """Brian caught the model continuing [8 q. 8 q.] as [q. 16 q. 16] - same total, wrong rhythm.
    The hint computes the answer so it does not have to."""
    import scorewright as sw
    h = sw.rhythm_hint(SRAW)
    assert 'bar 54 staff 1' in h, h
    line = [l for l in h.split('\n') if 'bar 54 staff 1' in l][0]
    assert '3.5 quarter notes remain' in line, line
    assert 'Bar 53 runs [8 q. 8 q.]' in line, line
    assert 'gives exactly [q. 8 q.]' in line, line


def test_edits_are_independent_across_staves_and_bars():
    """No hard-coded requirement that treble and bass edits align."""
    import scorewright as sw
    new, notes = sw.apply_edits(SRAW, [
        {'op': 'write_notes', 'measure': 60, 'staff': 2, 'voice': 2, 'events': ['G2:2', 'D3:2']},
        {'op': 'write_notes', 'measure': 75, 'staff': 1, 'voice': 1, 'events': ['[B-4 D5]:4']},
        {'op': 'add_dynamic', 'measure': 12, 'value': 'mp'},
    ])
    assert [x.read_pitch(b) for _, b in x.measure_notes(new, 60, staff=2)] == ['G2', 'D3']
    assert all('<rest' in b for _, b in x.measure_notes(new, 60, staff=1)), \
        'staff 1 of bar 60 should be untouched'
    assert [x.read_pitch(b) for _, b in x.measure_notes(new, 75, staff=1)] == ['B-4', 'D5']
    for m in (12, 60, 75):
        assert x.validate(new, m) == []


ORC = '/Users/bdogellis/Documents/Score Exports/MusicXML/Orchestral Idea.musicxml'
ORAW = open(ORC).read()


def test_locators_are_confined_to_the_named_part():
    """SHIPPED BUG, and the real orchestral blocker: measure_span used re.search, which returns the
    FIRST match. On a 30-part score every op silently operated on Flute 1 - ask to edit the cello
    and you edited the flute."""
    ps = x.parts(ORAW)
    assert len(ps) == 30, f'fixture: expected 30 parts, got {len(ps)}'
    fl = [x.read_pitch(b) for _, b in x.measure_notes(ORAW, 16, part=0)]
    vc = [x.read_pitch(b) for _, b in x.measure_notes(ORAW, 16, part='Violoncello')]
    assert fl != vc, 'flute and cello returned the same notes - part is being ignored'
    assert 'D6' in fl and 'D4' in vc, (fl[:4], vc[:4])
    assert x.part_index(ORAW, 'Timpani') == 20
    assert x.part_index(ORAW, 0) == 0


def test_part_can_be_addressed_by_name_and_bad_names_are_refused():
    try:
        x.part_index(ORAW, 'Kazoo')
        raise AssertionError('an unknown part name was accepted')
    except ValueError as e:
        assert 'no part named' in str(e)
    try:
        x.part_index(ORAW, 'Flute')            # ambiguous: Flute 1 and Flute 2
        raise AssertionError('an ambiguous part name was accepted')
    except ValueError as e:
        assert 'ambiguous' in str(e)


def test_orchestral_write_and_append_reach_every_part():
    new = x.append_measures(ORAW, 2)
    n = max(int(m.group(1)) for m in x.MEASURE_RE.finditer(new[x.parts(new)[0][3]:x.parts(new)[0][4]]))
    assert all(x.measure_span(new, n, part=i) for i, _, _, _, _ in x.parts(new)), \
        'append_measures did not reach every part'
    vc, ti = x.part_index(new, 'Violoncello'), x.part_index(new, 'Timpani')
    new = x.write_notes(new, n, 1, 1, ['[F3 A3 C4]:4'], part=vc)
    new = x.write_notes(new, n, 1, 1, ['F2:2', 'C3:2'], part=ti)
    assert [x.read_pitch(b) for _, b in x.measure_notes(new, n, part=vc)] == ['F3', 'A3', 'C4']
    assert [x.read_pitch(b) for _, b in x.measure_notes(new, n, part=ti)] == ['F2', 'C3']
    assert all('<rest' in b for _, b in x.measure_notes(new, n, part=0)), \
        'writing to the cello disturbed the flute'
    assert x.validate(new, n, part=vc) == [] and x.validate(new, n, part=ti) == []


if __name__ == '__main__':
    import sys, traceback
    fails = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith('test_') or not callable(fn):
            continue
        try:
            fn()
            print(f'  PASS {name}')
        except Exception:
            fails += 1
            print(f'  FAIL {name}')
            traceback.print_exc(limit=3)
    print(f'\n{"ALL PASS" if not fails else str(fails) + " FAILED"} ({len([n for n in globals() if n.startswith("test_")])} tests)')
    sys.exit(1 if fails else 0)
