"""Classical development techniques applied to a motif, mechanically and exactly.

The honest division of labour after a day of failing to compose: I cannot judge which development
a passage wants, but I can apply any of them perfectly across 30 transposing parts. So generate the
options and let Brian choose by ear - the thing he is good at and I am not.

His bar-1 motif: Eb6 - C6 - Gb6.  Down a minor 3rd (-3), up a tritone (+6). The tritone IS the
character; every transformation below preserves or deliberately alters that interval signature.
"""
from music21 import pitch

MOTIF = ['E-6', 'C6', 'G-6']
RHYTHM = [1.0, 0.5, 0.5]          # quarter, eighth, eighth (rests omitted here)


def _iv(names):
    ps = [pitch.Pitch(n).midi for n in names]
    return [ps[i + 1] - ps[i] for i in range(len(ps) - 1)]


def _from(start, ivs):
    out, cur = [start], pitch.Pitch(start).midi
    for v in ivs:
        cur += v
        p = pitch.Pitch(); p.midi = cur
        out.append(p.nameWithOctave)
    return out


IV = _iv(MOTIF)


def original():
    return MOTIF, RHYTHM, 'the motif as written: down a minor 3rd, up a tritone'


def inversion():
    return _from(MOTIF[0], [-v for v in IV]), RHYTHM, \
        'INVERSION - every interval flipped: up a minor 3rd, down a tritone. Same shape upside down'


def retrograde():
    return MOTIF[::-1], RHYTHM[::-1], 'RETROGRADE - the motif backwards'


def augmentation():
    return MOTIF, [r * 2 for r in RHYTHM], \
        'AUGMENTATION - same notes, twice as slow. Makes a theme feel monumental'


def diminution():
    return MOTIF, [r / 2 for r in RHYTHM], \
        'DIMINUTION - twice as fast. Turns a theme into figuration'


def fragmentation():
    return MOTIF[1:], RHYTHM[1:], \
        'FRAGMENTATION - only the tritone, the part that carries the tension. Beethoven does this ' \
        'constantly: keep breaking the theme down until only its most charged interval is left'


def sequence(step=-3, times=3):
    notes, rhy = [], []
    for k in range(times):
        notes += _from(pitch.Pitch(MOTIF[0]).transpose(step * k).nameWithOctave, IV)
        rhy += RHYTHM
    return notes, rhy, \
        f'SEQUENCE - the whole cell restated {times}x, each a minor 3rd lower. The engine of every ' \
        f'development section ever written'


def stretto_offsets():
    return [0.0, 1.0, 2.0], \
        'STRETTO - the same motif entering in three instruments a bar apart, overlapping. Turns a ' \
        'theme into texture without changing a note of it'


TECHNIQUES = [original, inversion, retrograde, augmentation, diminution, fragmentation, sequence]

if __name__ == '__main__':
    for fn in TECHNIQUES:
        notes, rhy, why = fn()
        pretty = ' '.join(f'{n}:{r:g}' for n, r in zip(notes, rhy))
        print(f'\n{fn.__name__.upper()}')
        print(f'  {pretty}')
        print(f'  {why}')
    off, why = stretto_offsets()
    print(f'\nSTRETTO\n  entries at beats {off}\n  {why}')
