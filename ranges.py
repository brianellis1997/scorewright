"""Instrument ranges, SOUNDING pitch, MIDI numbers. Textbook (Adler / Blatter) with modern
extensions: contrabass C extension, low-C bass clarinet, contrabassoon to A0, string harmonics
at the top. Loose on purpose at the top of strings and winds; the point is to catch a bassoon
at Eb6, not to police a virtuoso.

This is the only kind of rule the copilot enforces: physical. Nothing here is about key,
harmony, or style.
"""
import re

RANGES = [
    (r'piccolo', 74, 108),
    (r'alto flute', 54, 91),
    (r'bass flute', 48, 84),
    (r'flute', 59, 101),
    (r'english horn|cor anglais', 51, 84),
    (r'oboe d.amore', 55, 86),
    (r'bass oboe|heckelphone', 45, 79),
    (r'oboe', 58, 93),
    (r'contrabass clarinet', 22, 62),
    (r'bass clarinet', 34, 79),
    (r'e.?b clarinet|clarinet in e', 55, 98),
    (r'clarinet', 49, 94),
    (r'contrabassoon|contra.?bassoon', 21, 60),
    (r'bassoon', 33, 77),
    (r'soprano sax', 56, 88),
    (r'alto sax', 49, 81),
    (r'tenor sax', 44, 76),
    (r'baritone sax', 36, 69),
    (r'bass sax', 32, 64),
    (r'horn', 33, 84),
    (r'piccolo trumpet', 64, 96),
    (r'trumpet|cornet|flugelhorn', 52, 87),
    (r'bass trombone', 24, 72),
    (r'trombone', 34, 79),
    (r'euphonium|baritone', 34, 72),
    (r'wagner tuba', 40, 79),
    (r'tuba', 24, 70),
    (r'timpani', 36, 62),
    (r'glockenspiel', 79, 108),
    (r'xylophone', 65, 108),
    (r'vibraphone', 53, 89),
    (r'marimba', 36, 96),
    (r'crotales', 84, 108),
    (r'chimes|tubular', 60, 77),
    (r'harp', 23, 104),
    (r'celesta', 60, 108),
    (r'piano|keyboard|synth', 21, 108),
    (r'organ', 24, 108),
    (r'harpsichord', 29, 89),
    (r'guitar', 40, 88),
    (r'contrabass|double bass|string bass|bass$', 24, 79),
    (r'violoncello|cello', 36, 96),
    (r'viola', 48, 98),
    (r'violin', 55, 108),
    (r'mezzo', 55, 84),
    (r'soprano', 58, 90),
    (r'alto|contralto', 53, 79),
    (r'tenor', 43, 76),
    (r'baritone', 43, 69),
    (r'bass', 36, 65),
    (r'harmonica', 48, 84),
    (r'banjo|mandolin|ukulele', 48, 88),
    (r'cimbalom|dulcimer', 36, 88),
    (r'voice|vocal|whistl', 43, 88),
]
UNPITCHED = re.compile(r'cymbal|gong|tam|snare|drum|triangle|tambourine|castanet|wood ?block|percussion|shaker|maraca|claves|whip|ratchet', re.I)


def range_of(part_name):
    """(lo, hi) sounding MIDI for a part name, or None when unpitched / unknown."""
    n = (part_name or '').lower()
    if UNPITCHED.search(n):
        return None
    for pat, lo, hi in RANGES:
        if re.search(pat, n):
            return lo, hi
    return None


def check(score):
    """music21 score AT SOUNDING PITCH -> list of (part, bar, midi, lo, hi) violations."""
    out = []
    for p in score.parts:
        r = range_of(p.partName)
        if not r:
            continue
        lo, hi = r
        for m in p.getElementsByClass('Measure'):
            for n in m.notes:
                for q in n.pitches:
                    if q.midi < lo or q.midi > hi:
                        out.append((p.partName, m.number, q.midi, lo, hi))
    return out
