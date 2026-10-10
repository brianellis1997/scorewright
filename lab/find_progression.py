"""Find a chord progression anywhere in his music, in any key, and show what he wrote over it.

A pattern is chord families with the root's distance from the previous chord in semitones:
    minor hdim@+2 major|dom@+5 minor@+5      i, ii half-diminished, V, i (Em F#m7b5 B Em)
Families: minor (m, m7, m9, madd9, m6, m(maj7)), major (maj, maj7, maj9, add9, 6), dom (7, 9,
7b9, 7sus4, 7#5), hdim (m7b5), dim (dim, dim7), sus (sus2, sus4, 7sus4), any.
Repeated windows of the same chord count once.

usage (whisperer env): python find_progression.py "<pattern>" [--max 30] [--melody]
reads ~/Documents/Score Exports/_logs/harmony_index/*.json (harmony_index.py)"""
import sys, json, glob, argparse

IDX = '/Users/bdogellis/Documents/Score Exports/_logs/harmony_index'
FAM = {'minor': {'min', 'm7', 'm9', 'madd9', 'm6', 'mmaj7'}, 'major': {'maj', 'maj7', 'maj9', 'add9', '6'},
       'dom': {'7', '9', '7b9', '7sus4', '7#5'}, 'hdim': {'m7b5'}, 'dim': {'dim', 'dim7'},
       'sus': {'sus2', 'sus4', '7sus4'}}
SHORT = {'maj': '', 'min': 'm', 'dim': 'dim', 'aug': '+', 'sus4': 'sus4', 'sus2': 'sus2', '7': '7', 'maj7': 'maj7',
         'm7': 'm7', 'm7b5': 'ø7', 'dim7': 'o7', 'mmaj7': 'm(maj7)', '7sus4': '7sus4', '6': '6', 'm6': 'm6',
         'add9': 'add9', 'madd9': 'm(add9)', '9': '9', 'maj9': 'maj9', 'm9': 'm9', '7b9': '7b9', '7#5': '7#5'}
N = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']


def parse(pattern):
    steps = []
    for tok in pattern.split():
        fam, _, iv = tok.partition('@')
        quals = set()
        for f in fam.split('|'):
            quals |= FAM.get(f, {f}) if f != 'any' else {None}
        steps.append((quals, int(iv) % 12 if iv else None))
    return steps


def chords(doc):
    seq = []
    for b in doc['bars']:
        for wi, (r, q, bass) in enumerate(b['w']):
            if r is None:
                continue
            if seq and seq[-1][2] == r and seq[-1][3] == q:
                continue
            seq.append((b['n'], wi, r, q, bass))
    return seq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pattern')
    ap.add_argument('--max', type=int, default=30)
    ap.add_argument('--melody', action='store_true')
    a = ap.parse_args()
    steps = parse(a.pattern)
    hits = 0
    files = sorted(glob.glob(f'{IDX}/*.json'))
    for f in files:
        doc = json.load(open(f))
        seq = chords(doc)
        bars = {b['n']: b for b in doc['bars']}
        for i in range(len(seq) - len(steps) + 1):
            ok = True
            for j, (quals, iv) in enumerate(steps):
                n, wi, r, q, bass = seq[i + j]
                if None not in quals and q not in quals:
                    ok = False
                    break
                if j and iv is not None and (r - seq[i + j - 1][2]) % 12 != iv:
                    ok = False
                    break
            if not ok:
                continue
            hits += 1
            span = seq[i:i + len(steps)]
            names = ' '.join(N[r] + SHORT.get(q, q) + ('' if bass is None or bass % 12 == r else '/' + N[bass % 12]) for _, _, r, q, bass in span)
            b0, b1 = span[0][0], span[-1][0]
            line = f'{doc["stem"][:44]:44} bars {b0}-{b1}  {names}'
            if a.melody:
                mel = ' '.join(f'{N[x % 12]}{x // 12 - 1}' for n in range(b0, b1 + 1) for _, _, x in bars.get(n, {}).get('m', []))
                line += f'  | {mel}'
            print(line)
            if hits >= a.max:
                print(f'... stopped at {a.max} (of {len(files)} scores indexed)')
                return
    print(f'{hits} matches in {len(files)} scores indexed')


if __name__ == '__main__':
    main()
