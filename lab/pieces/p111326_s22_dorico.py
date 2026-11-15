"""The Dorico steps for 111326 S22 (lab/pieces/p111326_s22.py), on his project after S21.
Each violin note of bars 41-42 moves down by scale steps (NoteEdit.PitchDown keeps its ID, slur and
portato); then the time signature in bar 1 becomes 2/4 with beam grouping 2+2 (eighths in pairs).
usage (whisperer env): python lab/pieces/p111326_s22_dorico.py <working.xml> <S22.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
import p111326_s22 as s22  # noqa: E402


def plan(x):
    p = Plan(x)
    for pid, bars in s22.CLIMB.items():
        for bar, names in bars.items():
            onsets = [it[0] for it in p.cur.items(pid, bar) if it[1] != 'Rest']
            for onset, old, new in zip(onsets, s22.old_names(x, pid, bar), names):
                n = s22.scale_steps(old, new)
                if n:
                    p.pitch(pid, bar, onset, n)
    p.step('time signature 2/4 with eighths in pairs', 'P31', 1, 0, edits=['NoteInput.CreateTimeSignature?Definition=2/4,2+2'])
    return p


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p = plan(x)
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
