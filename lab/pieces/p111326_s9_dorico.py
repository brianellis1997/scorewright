"""The Dorico steps for 111326 S9 (lab/pieces/p111326_s9.py): S8's steps, then Violin I's G5 pickup
in bar 24 (typed over the end of the pad's B3, then slurred into the E5) and the B flat clarinet's
A on beat 2 of bar 28 (typed over the second half of its G sharp, then tied into bar 29).
usage (whisperer env): python lab/pieces/p111326_s9_dorico.py <S7.xml> <S9.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s8_dorico  # noqa: E402
import p111326_s9  # noqa: E402


def plan(x7):
    p = p111326_s8_dorico.plan(x7)
    x9 = p111326_s9.notes(x7)
    p.notes('P28', 24, 1.0, [('G5', 1)])
    p.after_notes(x9, 'P28', 24, 1.0)
    p.slur('P28', (24, 1.0), (25, 0))
    p.notes('P6', 28, 1.0, [('A4', 1)])
    p.after_notes(x9, 'P6', 28, 1.0)
    p.tie('P6', 28, 1.0)
    return p


if __name__ == '__main__':
    p = plan(open(sys.argv[1], encoding='utf-8').read())
    p.save(sys.argv[2], requires=['S7'])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
