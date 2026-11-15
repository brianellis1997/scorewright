"""Find hard clashes in a passage: two different parts sounding notes a minor second or a minor ninth
apart at the same moment, at concert pitch. Major sevenths are left out: the E over F of his Fmaj7
is a color he chose, and wider compound intervals do not rub.
Brian, Nov 14 2026: "be mindful of how the individual lines are interacting with the harmonies...
some passing tones are fine of course, but no obvious hard dissonances, notes within semitones."
Each clash is listed with its weight: 'strong' when both notes are held over the beat or one starts
on the beat, 'passing' when one is a short note (a sixteenth or an eighth) that starts off the beat.
usage (whisperer env): python lab/clash_check.py <score.xml> <first bar> <last bar> [--all] [--leaps]
--leaps also lists each part leaping more than a fifth with no breath (an entry into a melody needs a way up)."""
import sys
from fractions import Fraction

from dorico_plan import Score, midi


def notes(score, lo, hi):
    """[(part name, start, end, midi, name)] with times in quarters from the start of bar lo"""
    out = []
    for pid, staff in score.staves:
        bars = score.parts[pid][0]
        per_bar = None
        for b in range(lo, hi + 1):
            if b not in bars:
                continue
            its = score.items(pid, b, staff)
            if per_bar is None:
                per_bar = Fraction(2)
            for k, it in enumerate(its):
                end = its[k + 1][0] if k + 1 < len(its) and its[k + 1][0] > it[0] else per_bar
                if it[1] == 'Rest':
                    continue
                for n in it[1]:
                    t0 = (b - lo) * per_bar + it[0]
                    out.append((f'{score.names[pid]}{"" if staff == 1 else " " + str(staff)}', t0, (b - lo) * per_bar + end, midi(n), n, b, it[0]))
    return out


def clashes(score, lo, hi):
    ns = notes(score, lo, hi)
    found = []
    for i, a in enumerate(ns):
        for c in ns[i + 1:]:
            if a[0] == c[0]:
                continue
            if c[1] >= a[2] or a[1] >= c[2]:
                continue
            if abs(a[3] - c[3]) not in (1, 13):
                continue
            start = max(a[1], c[1])
            short = [x for x in (a, c) if x[2] - x[1] <= Fraction(1, 2) and x[1] % 1 != 0]
            found.append(('passing' if short else 'strong', lo + int(start // 2), start % 2, a, c))
    return sorted(found, key=lambda f: (f[1], f[2]))


def leaps(score, lo, hi, limit=7):
    """[(bar, beat, part, from, to, semitones)]: each part's top line jumping more than a fifth with no
    breath (a quarter or less) between the notes. Brian, Nov 14 2026, on Violin I leaping an octave
    into the melody it took over: "it needs to be a fluid transition, maybe a sextuplet run"."""
    by_part = {}
    for n in notes(score, lo, hi):
        by_part.setdefault(n[0], {})
        top = by_part[n[0]].get(n[1])
        if top is None or n[3] > top[3]:
            by_part[n[0]][n[1]] = n
    out = []
    for part, ns in by_part.items():
        seq = [ns[t] for t in sorted(ns)]
        for a, c in zip(seq, seq[1:]):
            if c[1] - a[2] <= 1 and abs(c[3] - a[3]) > limit:
                out.append((lo + int(c[1] // 2), c[1] % 2, part, a[4], c[4], c[3] - a[3]))
    return sorted(out)


if __name__ == '__main__':
    xml = open(sys.argv[1], encoding='utf-8').read()
    lo, hi = int(sys.argv[2]), int(sys.argv[3])
    found = clashes(Score(xml), lo, hi)
    shown = [f for f in found if f[0] == 'strong' or '--all' in sys.argv]
    for kind, bar, beat, a, c in shown:
        print(f'bar {bar} beat {float(beat) + 1:g}: {kind:7} {a[0]} {a[4]} / {c[0]} {c[4]}')
    print(f'{sum(f[0] == "strong" for f in found)} strong, {sum(f[0] == "passing" for f in found)} passing')
    if '--leaps' in sys.argv:
        for bar, beat, part, x, y, d in leaps(Score(xml), lo, hi):
            print(f'leap: bar {bar} beat {float(beat) + 1:g}: {part} {x} to {y} ({d:+d})')
