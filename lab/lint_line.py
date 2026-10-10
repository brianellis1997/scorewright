"""Check a melody line for the conventions a player or listener hears as mistakes.

Rules (each report names the bar and beat):
- a chromatically raised note (sharper than the key, the raised 6th and 7th of minor included)
  must move up by step or repeat; a lowered note must move down by step or repeat.
  Brian, S4 of "Where I Left It": "if you include an accidental, Mozart or Chopin would have it
  lean up; you just go down from the D sharp. It sounds like a wrong note."
- no augmented or diminished melodic intervals (augmented 2nd, tritone, diminished 4th...)
- a leap bigger than a fourth is followed by a step back the other way, and two leaps in one
  direction never add up to more than an octave ("the jumps come out of nowhere")
- breath: a wind player or singer needs a rest at least every N seconds (default 8) at the
  marked tempo ("no wind instrument or human voice could hold that melody that long")
- range, in sounding pitch, for the instruments listed below

usage (whisperer env): python lint_line.py <score.musicxml> [--part N] [--breath 8] [--tempo Q]
exit 1 when anything is reported"""
import sys, argparse
from music21 import converter, interval, pitch as m21pitch

RANGES = {'english horn': ('E3', 'A5'), 'oboe': ('Bb3', 'G6'), 'flute': ('C4', 'C7'), 'clarinet': ('D3', 'Bb6'),
          'bassoon': ('Bb1', 'E5'), 'voice': ('A3', 'A5'), 'soprano': ('C4', 'C6'), 'mezzo': ('A3', 'A5'),
          'violin': ('G3', 'E7'), 'viola': ('C3', 'E6'), 'cello': ('C2', 'A5')}


def scale_pcs(ks):
    """the key's diatonic pitch classes; in minor also the natural 6th and 7th"""
    k = ks.asKey()
    return {p.pitchClass for p in k.getPitches()}, k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('score')
    ap.add_argument('--part', type=int, default=0)
    ap.add_argument('--breath', type=float, default=8.0)
    ap.add_argument('--tempo', type=float)
    a = ap.parse_args()
    sc = converter.parse(a.score)
    try:
        sc = sc.toSoundingPitch()
    except Exception:
        pass
    part = sc.parts[a.part]
    name = (part.partName or '').lower()
    mm = sc.recurse().getElementsByClass('MetronomeMark')
    q = a.tempo or (mm[0].getQuarterBPM() if mm else 60)
    issues = []
    items = [n for n in part.flatten().notesAndRests]
    notes = []
    for el in items:
        if el.isRest:
            notes.append(('rest', el))
        elif el.isNote:
            if el.tie is not None and el.tie.type in ('stop', 'continue') and notes and notes[-1][0] == 'note':
                continue
            notes.append(('note', el))

    def where(n):
        m = n.getContextByClass('Measure')
        return f'bar {m.number if m else "?"} beat {round(n.beat, 2):g}'

    seq = [n for k, n in notes if k == 'note']
    for i, n in enumerate(seq):
        ks = n.getContextByClass('KeySignature')
        if ks is None:
            continue
        dia, key = scale_pcs(ks)
        pc = n.pitch.pitchClass
        nxt = seq[i + 1] if i + 1 < len(seq) else None
        tonic = key.tonic.pitchClass
        raised, lowered = False, False
        if pc not in dia:
            ref = [d for d in dia if (pc - d) % 12 == 1]
            low = [d for d in dia if (d - pc) % 12 == 1]
            letter_dia = {p.step: p for p in key.getPitches()}
            kp = letter_dia.get(n.pitch.step)
            if kp is not None:
                diff = (n.pitch.ps - kp.ps) % 12
                raised, lowered = diff == 1, diff == 11
            else:
                raised, lowered = bool(ref), bool(low) and not ref
        if key.mode == 'minor' and pc in ((tonic - 1) % 12, (tonic + 9) % 12):
            raised = True
        if nxt is not None and (raised or lowered):
            d = nxt.pitch.ps - n.pitch.ps
            ok = d == 0 or (raised and 0 < d <= 2) or (lowered and -2 <= d < 0)
            if not ok:
                issues.append(f'{where(n)}: {n.pitch.nameWithOctave} is {"raised" if raised else "lowered"} '
                              f'but moves {"down" if d < 0 else "up"} to {nxt.pitch.nameWithOctave}; it should '
                              f'{"rise" if raised else "fall"} by step')
        if nxt is not None:
            iv = interval.Interval(n.pitch, nxt.pitch)
            if iv.simpleName not in ('A1', 'd1') and (iv.specifier in (interval.Specifier.AUGMENTED, interval.Specifier.DIMINISHED) or iv.simpleName in ('A2', 'A4', 'd5', 'd4', 'd7', 'A5')):
                issues.append(f'{where(nxt)}: {iv.niceName} from {n.pitch.nameWithOctave} to {nxt.pitch.nameWithOctave}')
            semis = nxt.pitch.ps - n.pitch.ps
            if abs(semis) > 5 and i + 2 < len(seq):
                after = seq[i + 2].pitch.ps - nxt.pitch.ps
                if not (after != 0 and abs(after) <= 2 and (after > 0) != (semis > 0)):
                    issues.append(f'{where(nxt)}: leap of {iv.niceName.lower()} ({n.pitch.nameWithOctave} to '
                                  f'{nxt.pitch.nameWithOctave}) is not followed by a step back')
            if i + 2 < len(seq):
                s2 = seq[i + 2].pitch.ps - nxt.pitch.ps
                if abs(semis) > 2 and abs(s2) > 2 and (semis > 0) == (s2 > 0) and abs(semis + s2) > 12:
                    issues.append(f'{where(nxt)}: two leaps the same way span more than an octave')
    run, start = 0.0, None
    for k, n in notes:
        if k == 'rest':
            if run > a.breath:
                issues.append(f'{where(start)}: {run:.1f} s without a rest (breath at least every {a.breath:g} s)')
            run, start = 0.0, None
            continue
        if start is None:
            start = n
        run += n.duration.quarterLength * 60.0 / q
        t = n
        while t.tie is not None and t.tie.type in ('start', 'continue'):
            t = t.next('Note')
            if t is None:
                break
            run += t.duration.quarterLength * 60.0 / q
    if run > a.breath and start is not None:
        issues.append(f'{where(start)}: {run:.1f} s without a rest at the end')
    rng = next((v for k, v in RANGES.items() if k in name), None)
    if rng and seq:
        lo, hi = m21pitch.Pitch(rng[0]), m21pitch.Pitch(rng[1])
        for n in seq:
            if not lo.ps <= n.pitch.ps <= hi.ps:
                issues.append(f'{where(n)}: {n.pitch.nameWithOctave} outside the {name} range {rng[0]}-{rng[1]}')
    print(f'{part.partName}: {len(seq)} notes, tempo {q:g}, {len(issues)} issue(s)')
    for s in issues:
        print('  ' + s)
    sys.exit(1 if issues else 0)


if __name__ == '__main__':
    main()
