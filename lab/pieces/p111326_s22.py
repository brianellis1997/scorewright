"""111326 S22 (Nov 15 2026), after Brian's reason on S21: "bar 40 going to bar 41 for the two
violins... they're on these low C's and they're now going up... more than an octave, a 10th, to a
high E doubling the flutes. It just doesn't work... we could have bar 41 and 42 be a transition for
the violins to start to reach up to that register and then be fully doubling the flutes starting in
bar 43... in 2/4 time... eighth notes connected in groups of two."
- Violins, bars 41-42: they climb from their C in the theme's rhythm and with its slurs and
  portato, C, G, A, then B, and join the flutes on beat 2 of bar 42 (E, D), doubling them from
  there (Violin II an octave lower). F and C on those beats would rub a semitone against the oboe's
  E and the held B (clash_check), so G and the theme's own E take their place.
- Eighths are beamed in pairs, one pair per beat, in the whole piece. In Dorico the time signature
  in bar 1 becomes 2/4 with the beam grouping 2+2 (the same meter).
usage (whisperer env): python lab/pieces/p111326_s22.py <working.xml> <out.xml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import measure_span, rebeam  # noqa: E402

CLIMB = {'P28': {41: ['C5', 'G5', 'A5'], 42: ['B5', 'E6', 'D6']}, 'P29': {41: ['C4', 'G4', 'A4'], 42: ['B4', 'E5', 'D5']}}
STEPS = 'CDEFGAB'


def scale_steps(a, b):
    """diatonic steps from note a to note b (both without accidentals), negative is down"""
    return (int(b[-1]) * 7 + STEPS.index(b[0])) - (int(a[-1]) * 7 + STEPS.index(a[0]))


def climb(x):
    for pid, bars in CLIMB.items():
        for bar, names in bars.items():
            s0, s1 = measure_span(x, pid, bar)
            body = x[s0:s1]
            notes = [m for m in re.finditer(r'<note[ >].*?</note>', body, re.S) if '<rest' not in m.group(0)]
            assert len(notes) == len(names), (pid, bar, len(notes))
            for m, name in reversed(list(zip(notes, names))):
                new = re.sub(r'<pitch>.*?</pitch>', f'<pitch><step>{name[0]}</step><octave>{name[-1]}</octave></pitch>', m.group(0), count=1, flags=re.S)
                new = re.sub(r'\s*<accidental>[^<]*</accidental>', '', new)
                body = body[:m.start()] + new + body[m.end():]
            x = x[:s0] + body + x[s1:]
    return x


def old_names(x, pid, bar):
    s0, s1 = measure_span(x, pid, bar)
    out = []
    for m in re.finditer(r'<note[ >].*?</note>', x[s0:s1], re.S):
        p = re.search(r'<step>(\w)</step>(?:\s*<alter>(-?\d+)</alter>)?\s*<octave>(\d+)</octave>', m.group(0))
        if p:
            assert not p.group(2), 'an altered note'
            out.append(p.group(1) + p.group(3))
    return out


def notes(x):
    return climb(x)


def build(x):
    return rebeam(climb(x))


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
