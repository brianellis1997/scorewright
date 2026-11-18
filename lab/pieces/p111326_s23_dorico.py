"""The Dorico steps for 111326 S23 (lab/pieces/p111326_s23.py), on his project as exported at 21:29.
Bar 60 first: each held note of the climax chord ends on beat 2 (EventEdit.DurationShortenByGrid twice,
the rhythmic grid being an eighth; the note keeps its ID, tie and slur), and the notes on beat 2 go
(Edit.Delete). Then the diminuendos, the cor anglais marks, the flute's echo with its marks, and the
chords: violas, bassoon (typed over his triads), cellos and basses, with their spellings and marks.
The violas' "unis." comes last, because a text box leaves no selection to go on from.
usage (whisperer env): python lab/pieces/p111326_s23_dorico.py <working.xml> <S23.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10_dorico import last_note, typed  # noqa: E402
from p111326_s15_dorico import sharp_groups  # noqa: E402
import p111326_s23 as s23  # noqa: E402


def plan(x):
    p = Plan(x)
    for pid in s23.HELD + [s23.CHORD]:
        p.shorten(pid, 60 if pid == s23.CHORD else 59, 0, 2)
    for pid in s23.REPEATED:
        late = [it[0] for it in p.cur.items(pid, 60) if it[1] != 'Rest' and it[0] >= 1]
        p.step(f'{p.who(pid)}: beat 2 of bar 60 out', pid, 60, late[0], to=(60, late[-1]) if len(late) > 1 else None,
               edits=['Edit.Delete'])
    state = [s23.stop(x)]
    p.use(state[0])
    for pid in s23.FADE:
        last = [it[0] for it in p.cur.items(pid, 60) if it[1] != 'Rest'][-1]
        p.hairpin(pid, (59, 0), (60, last), up=False)
    p.dynamic('P4', 60, 1.0, 'mp')
    for a, z in s23.CA_SLURS:
        p.slur('P4', a, z)
    for a, z in s23.CA_SLURS:
        p.articulation('P4', z[0], 0, 'kStaccatoTenuto')

    def line(l):
        pid, staff, bar, onset, bars = l
        p.notes(pid, bar, onset, typed(l), staff=staff)
        state[0] = s23.write_line(state[0], l)
        p.after_notes(state[0], pid, *last_note(l), staff=staff)
        for b, o, k in reversed(sharp_groups(l)):
            p.spell(pid, b, o, staff=staff, group=k)

    line(s23.echo_line())
    p.dynamic('P2', 61, 1.0, 'pp')
    for b in s23.ECHOES:
        p.slur('P2', (b, 1.0), (b + 1, 0))
        p.articulation('P2', b + 1, 0, 'kStaccatoTenuto')
    for pid in ('P30', 'P7', 'P31', 'P32'):
        line(s23.pad_line(pid))
        p.dynamic(pid, 61, 0, 'pp')
        for a, z in s23.slur_groups(s23.PADS[pid]):
            p.slur(pid, a, z)
    p.text('P30', 61, 0, 'unis.')
    return p


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p = plan(x)
    want = Score(s23.notes(x))
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S23: {bad[:5]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
