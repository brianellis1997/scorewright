"""Regression tests for the analysis layer. Every test here corresponds to a bug that shipped.

The rule this codebase keeps relearning: VERIFY THE OBJECT, NOT A PROXY. Each failure below was a
signal harvested from something that merely resembled the thing we meant.
"""
from music21 import stream, note, chord, instrument, meter
import analyze


def test_range_key_is_longest_match_not_substring():
    """SHIPPED BUG: 'Tenor Saxophone' substring-matched the VOICE entry 'Tenor' (C3-A4) and reported
    418 violations in Gettysburg Day 3 that do not exist."""
    for name, want in [('Tenor Saxophone', 'Tenor Saxophone'),
                       ('Alto Saxophone', 'Alto Saxophone'),
                       ('Soprano Saxophone', 'Soprano Saxophone'),
                       ('Bass Clarinet', 'Bass Clarinet'),
                       ('Alto Flute', 'Alto Flute'),
                       ('Bass Trombone', 'Bass Trombone'),
                       ('Contrabassoon', 'Contrabassoon')]:
        assert analyze._match_range(name)[0] == want, f'{name} matched the wrong instrument'
    assert analyze._match_range('Tenor')[0] == 'Tenor'          # the voice still resolves
    assert analyze._match_range('Kazoo')[0] is None             # unknown -> no check, not a guess


def _part(inst, pitches, ql=1.0):
    p = stream.Part()
    # Real MusicXML from Sibelius sets atSoundingPitch=False. A synthetic Part defaults to
    # 'unknown', and music21 then refuses to transpose - so a fixture without this line tests a
    # code path that never runs in production.
    p.atSoundingPitch = False
    p.insert(0, inst)
    m = stream.Measure(number=1)
    for x in pitches:
        m.append(note.Note(x, quarterLength=ql))
    p.append(m)
    return p


def test_range_check_uses_sounding_not_written_pitch():
    """A Bb clarinet WRITTEN C7 sounds Bb6, which is inside its range. Checking written pitch
    against a sounding table flags it as too high."""
    s = stream.Score()
    s.insert(0, _part(instrument.Clarinet(), ['C7']))
    assert analyze.check_ranges(s) == [], 'written C7 on Bb clarinet is not a violation'


def test_range_check_still_catches_a_real_violation():
    """Guard against the fix above turning the check into a no-op."""
    s = stream.Score()
    s.insert(0, _part(instrument.Contrabass(), ['E-1']))
    v = analyze.check_ranges(s)
    assert len(v) == 1 and v[0]['count'] == 1 and v[0]['examples'][0]['direction'] == 'below'


def test_unpitched_percussion_does_not_crash():
    """SHIPPED BUG: Unpitched has no .pitch and no .notes. Only orchestral scores have percussion,
    so 900+ solo/chamber parses passed before this surfaced."""
    from music21 import note as n2
    p = stream.Part(); p.atSoundingPitch = False; p.insert(0, instrument.SnareDrum())
    m = stream.Measure(number=1); m.append(n2.Unpitched()); p.append(m)
    s = stream.Score(); s.insert(0, p)
    analyze.check_ranges(s)


def _two_voices(top, bottom):
    s = stream.Score()
    for i, seq in enumerate((top, bottom)):
        p = stream.Part(); p.partName = f'V{i}'
        m = stream.Measure(number=1)
        for x in seq:
            m.append(note.Note(x, quarterLength=1.0))
        p.append(m); s.insert(0, p)
    return s


def test_parallel_fifths_detected():
    assert len(analyze.check_parallels(_two_voices(['G5', 'A5'], ['C4', 'D4']))) >= 1


def test_oblique_motion_is_not_a_parallel():
    """SHIPPED BUG: holding one voice while the other moves is oblique motion, not parallel motion.
    The first version reported it because it only compared the interval names."""
    # C4 held under G5->G5 is a repeated fifth, not parallel motion
    assert analyze.check_parallels(_two_voices(['G5', 'G5'], ['C4', 'C4'])) == []


def test_harmonic_reduction_drops_passing_tones():
    """SHIPPED BUG: raw chordify labelled every vertical slice, turning 14 bars of the G-minor
    quartet into figures like 'vi#5#4'. Short sonorities must not survive the reduction."""
    s = stream.Score()
    p = stream.Part(); m = stream.Measure(number=1)
    m.insert(0, meter.TimeSignature('4/4'))
    m.insert(0, chord.Chord(['C4', 'E4', 'G4'], quarterLength=3.5))
    m.insert(3.5, chord.Chord(['D4', 'F#4'], quarterLength=0.5))   # eighth-note passing sonority
    p.append(m); s.insert(0, p)
    prog = analyze.harmonic_sketch(s).get('progression', [])
    assert prog and len(prog[0]['rn']) == 1, 'the eighth-note passing chord should be dropped'


def test_single_note_is_not_labelled_a_chord():
    """SHIPPED BUG: Fall Rose m1-4 is ONE cello pedal on D - one pitch class - and the reduction
    reported "i" for all four bars. Invented harmony reads as fact, which is worse than a gap."""
    from music21 import key as k21
    c = chord.Chord(['D2'])
    lab = analyze._label(c, k21.Key('D', 'major'))
    assert lab is not None and 'alone' in lab, f'a single note must not become a roman numeral: {lab}'
    d = analyze._label(chord.Chord(['B4', 'E5']), k21.Key('D', 'major'))
    assert 'dyad' in d, f'a two-note dyad must not become a roman numeral: {d}'
    tri = analyze._label(chord.Chord(['D4', 'F#4', 'A4']), k21.Key('D', 'major'))
    assert tri == 'I', f'a real triad must still get a roman numeral, got {tri}'


def test_roman_numerals_use_notated_spelling():
    """SHIPPED BUG: Briello no 36 is notated in 6 sharps (D# minor); Krumhansl returns the
    enharmonic FLAT spelling (Eb minor). Roman numerals compare spellings, so the tonic D# minor
    triad came out as '#vii' and Brian's i-VI-III-VII read as '#vii #V #II #VI'."""
    from music21 import key as k21
    dsharp = k21.KeySignature(6).asKey('minor')
    assert dsharp.tonic.name == 'D#'
    got = [analyze._label(chord.Chord(c), dsharp) for c in
           (['D#4', 'F#4', 'A#4'], ['B3', 'D#4', 'F#4'], ['F#3', 'A#3', 'C#4'], ['C#4', 'E#4', 'G#4'])]
    assert got[0] == 'i', f'tonic should be i, got {got[0]}'
    assert got[2] == 'III', f'F# major should be III, got {got[2]}'


def test_reduction_never_drops_a_bar():
    """SHIPPED BUG: min_beats dropped 34 of Briello 36's 40 bars, because fast piano writing has no
    chord lasting a full beat. That is exactly the Debussy/Ravel case."""
    from music21 import meter as m21m
    s = stream.Score(); p = stream.Part(); m = stream.Measure(number=1)
    m.insert(0, m21m.TimeSignature('4/4'))
    for i in range(8):                       # nothing longer than an eighth
        m.insert(i * 0.5, chord.Chord(['C4', 'E4', 'G4'], quarterLength=0.5))
    p.append(m); s.insert(0, p)
    prog = analyze.harmonic_sketch(s).get('progression', [])
    assert prog and prog[0]['rn'], 'a bar of fast chords must still produce a label'


if __name__ == '__main__':
    import sys, traceback
    fails = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith('test_') or not callable(fn):
            continue
        try:
            fn(); print(f'  PASS {name}')
        except Exception:
            fails += 1
            print(f'  FAIL {name}'); traceback.print_exc(limit=2)
    print(f'\n{"ALL PASS" if not fails else str(fails) + " FAILED"}')
    sys.exit(1 if fails else 0)
