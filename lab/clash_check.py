"""Find hard clashes in a passage: two different parts sounding notes a minor second or a minor ninth
apart at the same moment, at concert pitch. Major sevenths are left out: the E over F of his Fmaj7
is a color he chose, and wider compound intervals do not rub.
Brian, Nov 14 2026: "be mindful of how the individual lines are interacting with the harmonies...
some passing tones are fine of course, but no obvious hard dissonances, notes within semitones."
Each clash is listed with its weight: 'strong' when both notes are held over the beat or one starts
on the beat, 'passing' when one is a short note (a sixteenth or an eighth) that starts off the beat.
It also lists each part that comes in after four bars of rest or more with no dynamic at its entry:
it plays at whatever dynamic it had last (S32, Nov 17: the tuba came in at bar 94, under ff brass,
with the mf it had in bar 53).
And each wind or brass note that ends a fade with no slur into it, and each hairpin that ends in the
bars with no dynamic where it ends: "a decrescendo to what?...
every crescendo and decrescendo, when ending a phrase, at least needs a dynamic marking where it's
headed" (Brian, Nov 23 2026: S34's trumpets faded to nothing in bar 105).
usage (whisperer env): python lab/clash_check.py <score.xml> <first bar> <last bar> [--all] [--leaps]
--leaps also lists each part leaping more than a fifth with no breath (an entry into a melody needs a way up)."""
import re
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


SECTIONS = [('Violin I', 'Violin II'), ('Violin II', 'Viola'), ('Viola', 'Violoncello')]


def pairs_of(names):
    """parts that must keep their order: the string sections, and 1 above 2 of the same instrument"""
    out = [p for p in SECTIONS if p[0] in names and p[1] in names]
    for n in names:
        if n.endswith(' 1') and n[:-1] + '2' in names:
            out.append((n, n[:-1] + '2'))
    return out


def crossings(score, lo, hi):
    """[(bar, beat, upper part, its note, lower part, its note)]: the lower part sounds above the upper
    one. Brian, Nov 15 2026: "violin two is playing higher than violin one... and then they cross
    again... that just doesn't make sense from a school writing perspective" """
    ns = notes(score, lo, hi)
    tops = {}
    for n in ns:
        tops.setdefault(n[0], []).append(n)
    out = []
    for up, low in pairs_of(set(tops)):
        for a in tops[up]:
            for c in tops[low]:
                if c[1] < a[2] and a[1] < c[2] and c[3] > a[3]:
                    t = max(a[1], c[1])
                    out.append((lo + int(t // 2), t % 2, up, a[4], low, c[4]))
    return sorted(set(out))


def entries(score, lo, hi, gap=4):
    """[(bar, part, bars of rest, last dynamic)]: entries in [lo, hi] after gap or more bars of rest
    with no dynamic in the entry bar at or before the first note (any staff of the part)"""
    out = []
    for pid in score.parts:
        bars = score.parts[pid][0]
        staves = [st for p, st in score.staves if p == pid]
        dyns = set().union(*(score.dyns.get((pid, st), set()) for st in staves))
        quiet, last = 0, None
        for b in sorted(bars):
            if b > hi:
                break
            starts = [it[0] for st in staves for it in score.items(pid, b, st) if it[1] != 'Rest']
            if starts and b >= lo and quiet >= gap and not any(d[0] == b and d[1] <= min(starts) for d in dyns):
                out.append((b, score.names[pid], quiet, last))
            found = re.findall(r'<dynamics>\s*<(\w+)/>', bars[b])
            last = f'{found[-1]} in bar {b}' if found else last
            quiet = 0 if starts else quiet + 1
    return sorted(out)


def targets(score, lo, hi):
    """[(part, start, end)]: hairpins that end in [lo, hi] with no dynamic at their end (any staff)"""
    out = []
    for pid in score.parts:
        staves = [st for p, st in score.staves if p == pid]
        dyns = set().union(*(score.dyns.get((pid, st), set()) for st in staves))
        for st in staves:
            for a, e in score.wedges.get((pid, st), []):
                if not lo <= e[0] <= hi or e in dyns:
                    continue
                starts = sorted(it[0] for s2 in staves if e[0] in score.parts[pid][0]
                                for it in score.items(pid, e[0], s2) if it[1] != 'Rest' and not it[2] and it[0] >= e[1])
                if starts and (e[0], starts[0]) in dyns:
                    continue
                out.append((score.names[pid], a, e))
    return sorted(out, key=lambda t: (t[2], t[0]))


BREATH = ('piccolo', 'flute', 'oboe', 'anglais', 'clarinet', 'bassoon', 'horn', 'trumpet', 'trombone', 'tuba')


def fades(score, lo, hi):
    """[(part, bar, onset, starts a phrase)]: a wind or brass note where a decrescendo ends, right after a note, with no slur or
    tie into it: the player tongues it (Brian, Nov 23 2026: "there should be a slur to that final
    note... when we're fading out or doing these transitions or dovetails, slurring is vital")"""
    out = []
    for pid in score.parts:
        if not any(w in score.names[pid].lower() for w in BREATH):
            continue
        bars, _, divs = score.parts[pid]
        for (a, e), kind in zip(score.wedges.get((pid, 1), []), score.wedge_kinds.get((pid, 1), [])):
            if kind != 'diminuendo' or not lo <= e[0] <= hi or e[0] not in bars:
                continue
            its = score.items(pid, e[0])
            k = next((i for i, it in enumerate(its) if it[0] == e[1] and it[1] != 'Rest'), None)
            if k is None:
                continue
            before = its[k - 1][1] != 'Rest' if k else any(it[1] != 'Rest' for it in score.items(pid, e[0] - 1)[-1:])
            t, found = 0, None
            for m in re.finditer(r'<note[ >].*?</note>|<backup>.*?</backup>|<forward>.*?</forward>', bars[e[0]], re.S):
                x = m.group(0)
                d = int((re.search(r'<duration>(\d+)</duration>', x) or [0, 0])[1])
                if x.startswith('<backup'):
                    t -= d
                    continue
                if '<chord/>' in x:
                    continue
                if t == e[1] * divs[e[0]] and '<rest' not in x:
                    found = x
                    break
                t += d
            if found and '<tie type="start"' in found and '<slur type="stop"' not in found:
                nb = e[0] + 1
                nxt = re.search(r'<note[ >].*?</note>', bars.get(nb, ''), re.S)
                if nxt and '<slur type="stop"' in nxt.group(0):
                    continue
            if before and found and '<slur type="stop"' not in found and '<tie type="stop"' not in found:
                out.append((score.names[pid], e[0], e[1], '<slur type="start"' in found))
    return sorted(out, key=lambda r: (r[1], r[2], r[0]))


if __name__ == '__main__':
    xml = open(sys.argv[1], encoding='utf-8').read()
    lo, hi = int(sys.argv[2]), int(sys.argv[3])
    found = clashes(Score(xml), lo, hi)
    shown = [f for f in found if f[0] == 'strong' or '--all' in sys.argv]
    for kind, bar, beat, a, c in shown:
        print(f'bar {bar} beat {float(beat) + 1:g}: {kind:7} {a[0]} {a[4]} / {c[0]} {c[4]}')
    print(f'{sum(f[0] == "strong" for f in found)} strong, {sum(f[0] == "passing" for f in found)} passing')
    for bar, beat, up, x, low, y in crossings(Score(xml), lo, hi):
        print(f'crossing: bar {bar} beat {float(beat) + 1:g}: {low} {y} above {up} {x}')
    for bar, part, quiet, last in entries(Score(xml), lo, hi):
        print(f'entry with no dynamic: bar {bar}: {part} after {quiet} bars of rest; it plays at {last or "no dynamic yet"}')
    for part, a, e in targets(Score(xml), lo, hi):
        print(f'hairpin with no target dynamic: {part}, from bar {a[0]} beat {float(a[1]) + 1:g} to bar {e[0]} beat {float(e[1]) + 1:g}')
    for part, bar, onset, phrase in fades(Score(xml), lo, hi):
        why = ('it starts a new phrase slur: a breath between phrases is fine, a fade or a dovetail into it is not'
               if phrase else 'a wind player tongues it')
        print(f'unslurred last note of a fade: bar {bar} beat {float(onset) + 1:g}: {part} ({why})')
    if '--leaps' in sys.argv:
        for bar, beat, part, x, y, d in leaps(Score(xml), lo, hi):
            print(f'leap: bar {bar} beat {float(beat) + 1:g}: {part} {x} to {y} ({d:+d})')
