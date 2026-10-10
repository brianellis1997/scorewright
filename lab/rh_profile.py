"""What the accompaniment's right hand does against the melody, measured from his scores.

For every melody attack: is it doubled in the right hand (same pitch class, unison or octave), or
harmonised a third or sixth below (attacked together), or neither? For every melody rest of a beat
or more: does the right hand fill it with a line (three or more attacks), sustain, or rest? Grace
notes and ornaments are counted. With --examples, prints the fills note by note.

Brian, S5 of "Where I Left It": "the right hand, I would be filling in: doubling the melody at
times, or in thirds, some ornamentation, or filling lines when the melody stops."

usage (whisperer env): python rh_profile.py <score.musicxml> [...] [--examples N]"""
import sys, argparse
from music21 import converter

KEYBOARD = ('piano', 'pno', 'guitar', 'gtr', 'harp')
N = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']


def notes(part):
    out = []
    for n in part.flatten().notes:
        if n.duration.quarterLength <= 0:
            continue
        s = float(n.offset); e = s + float(n.duration.quarterLength)
        for p in n.pitches:
            out.append((s, e, int(round(p.ps))))
    return sorted(out)


def melody_events(part):
    ev = []
    for n in part.flatten().notesAndRests:
        if n.duration.quarterLength <= 0:
            continue
        s = float(n.offset); e = s + float(n.duration.quarterLength)
        if n.isRest:
            ev.append((s, e, None))
        else:
            tie = n.tie.type if n.tie is not None else None
            m = int(round(max(p.ps for p in n.pitches)))
            if tie in ('stop', 'continue') and ev and ev[-1][2] == m:
                ev[-1] = (ev[-1][0], e, m)
            else:
                ev.append((s, e, m))
    rests = []
    for s, e, m in ev:
        if m is None and rests and rests[-1][1] >= s - 1e-6:
            rests[-1] = (rests[-1][0], e)
        elif m is None:
            rests.append((s, e))
    return [x for x in ev if x[2] is not None], rests


def profile(path, examples):
    sc = converter.parse(path)
    try:
        sc = sc.toSoundingPitch()
    except Exception:
        pass
    parts = list(sc.parts)
    names = [(p.partName or '').lower() for p in parts]
    mi = next((i for i, n in enumerate(names) if not any(k in n for k in KEYBOARD)), None)
    kb = [i for i, n in enumerate(names) if any(k in n for k in KEYBOARD)]
    if mi is None or not kb:
        return None
    rh = notes(parts[kb[0]])
    mel, rests = melody_events(parts[mi])
    gr = sum(1 for p in parts for n in p.flatten().notes if n.duration.isGrace)
    orn = sum(len(n.expressions) for p in parts for n in p.flatten().notes)
    dbl = harm = other = 0
    for s, e, m in mel:
        at = [x for x in rh if x[0] <= s + 1e-6 < x[1]]
        att = [x for x in at if abs(x[0] - s) < 1e-6]
        if any(x[2] % 12 == m % 12 for x in at):
            dbl += 1
        elif any(((m - x[2]) % 12) in (3, 4, 8, 9) and x[2] < m for x in att):
            harm += 1
        else:
            other += 1
    filled = sustained = silent = 0
    ex = []
    measures = list(parts[mi].getElementsByClass('Measure'))
    starts = [float(m.offset) for m in measures]
    for s, e in rests:
        if e - s < 1.0 - 1e-6:
            continue
        inside = [x for x in rh if s - 1e-6 <= x[0] < e - 1e-6]
        onsets = sorted({x[0] for x in inside})
        if len(onsets) >= 3:
            filled += 1
            if len(ex) < examples:
                import bisect
                b = bisect.bisect_right(starts, s + 1e-6)
                top = []
                for o in onsets:
                    top.append(max(x[2] for x in inside if x[0] == o))
                ex.append(f'bar {b}: ' + ' '.join(f'{N[t % 12]}{t // 12 - 1}' for t in top))
        elif any(x[0] < s - 1e-6 < x[1] or x[0] <= s < x[1] for x in rh):
            sustained += 1
        else:
            silent += 1
    tot = max(1, dbl + harm + other)
    gaps = max(1, filled + sustained + silent)
    return dict(piece=path.rsplit('/', 1)[-1].rsplit('.', 1)[0], melody=parts[mi].partName,
                doubled=round(dbl / tot, 2), thirds_sixths=round(harm / tot, 2),
                gaps=filled + sustained + silent, gaps_filled=round(filled / gaps, 2),
                gaps_sustained=round(sustained / gaps, 2), gaps_silent=round(silent / gaps, 2),
                grace=gr, ornaments=orn, examples=ex)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scores', nargs='+')
    ap.add_argument('--examples', type=int, default=0)
    a = ap.parse_args()
    print(f"{'piece':28} {'melody':18} {'doubled':>7} {'3rds/6ths':>9} {'rests':>5} {'filled':>6} {'held':>5} {'silent':>6} {'grace':>5} {'orn':>4}")
    for f in a.scores:
        p = profile(f, a.examples)
        if not p:
            continue
        print(f"{p['piece'][:28]:28} {p['melody'][:18]:18} {p['doubled']:7} {p['thirds_sixths']:9} {p['gaps']:5} "
              f"{p['gaps_filled']:6} {p['gaps_sustained']:5} {p['gaps_silent']:6} {p['grace']:5} {p['ornaments']:4}")
        for x in p['examples']:
            print('     fill', x)


if __name__ == '__main__':
    main()
