"""The Dorico steps for 111326 S44 (lab/pieces/p111326_s44.py), on his export of Nov 25, 08:55: his viola chords
of bars 128-134 and his Violin II run of bars 131-134 deleted; the oboe's tied E lengthened by one grid step
(EventEdit.DurationLengthenByGrid; leave it out with hold_oboe=False); then every line typed, sharps and flats
checked, the staccatos, the slurs (with the low brass slurred in from bar 127) and the dynamics.
usage (whisperer env): python lab/pieces/p111326_s44_dorico.py <export.xml> <S44.dorico.json> [--no-hold]"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10 import put  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
from p111326_s28_dorico import accidentals, events  # noqa: E402
import p111326_s44 as s44  # noqa: E402

H = Fraction(1, 2)
ORDER = ['P2', 'P1', 'P6', 'P29', 'P30', 'P14', 'P11', 'P15', 'P7', 'P31', 'P32', 'P8']


def plan(x, hold_oboe=True):
    p = Plan(x)
    final = s44.notes(x)
    if not hold_oboe:
        final = copy_bars(final, x, 'P3', [128])
    want = Score(final)
    ls = s44.lines(x)
    last = [it[0] for it in p.cur.nav('P30', 134)][-1]
    p.step('Viola: his chords of bars 128-134 out', 'P30', 128, 0, to=(134, last), edits=['Edit.Delete'])
    state = x
    for b in s44.BARS:
        state = put(state, 'P30', b, [(None, 8, None)])
    p.use(state)
    # the run starts on beat 2.25 of bar 131, off the eighth-note caret grid: the caret comes there from his
    # Violin II note on that beat, before his run is deleted
    run = events({b: ls['P6'][b] for b in range(131, 135)}, s44.RUN_FROM)
    p.notes('P6', *s44.RUN_FROM, run, start=('P29', 1, 131, s44.RUN_FROM[1]))
    run_state = copy_bars(state, final, 'P6', range(132, 135))
    run_state = put(run_state, 'P6', 131, [(None, 4, None), (None, 1, None)] + ls['P6'][131][3:])
    state = run_state
    p.after_notes(state, 'P6', 134, Fraction(7, 4))
    run_end = [it[0] for it in p.cur.nav('P29', 134)][-1]
    p.step('Violin II: his run of bars 131-134 out (it goes to the clarinet)', 'P29', 131, Fraction(5, 4), to=(134, run_end), edits=['Edit.Delete'])
    for b in range(131, 135):
        state = put(state, 'P29', b, [(None, 8, None)])
    p.use(state)
    if hold_oboe:
        p.step('Oboe: its tied E an eighth longer, into the violins', 'P3', 127, 1, edits=['EventEdit.DurationLengthenByGrid'])
        state = copy_bars(state, final, 'P3', [128])
        p.use(state)
    for pid in ORDER:
        bars = ls[pid] if pid != 'P6' else {b: evs for b, evs in ls['P6'].items() if b <= 131}
        if pid == 'P6':
            bars = dict(bars)
            bars[131] = bars[131][:2]
        evs = events(bars, (min(bars), 0))
        k = next(i for i, e in enumerate(evs) if e[0] is not None)
        start = (min(bars), sum((Fraction(e[1]) for e in evs[:k]), Fraction(0)))
        p.notes(pid, *start, evs[k:])
        state = copy_bars(state, final, pid, sorted(bars))
        typed = [(b, it[0]) for b in sorted(bars) for it in want.items(pid, b) if it[1] != 'Rest' and not it[2]
                 and (pid != 'P6' or (b, it[0]) <= (131, H))]
        p.after_notes(state, pid, *typed[-1])
        for b, o, n in reversed(accidentals(want, pid, bars, start)):
            p.spell(pid, b, o, group=n)
    for staff in (1, 2):
        evs = []
        for b in sorted(s44.HARP):
            evs += [(n, Fraction(d, 4)) for n, d in s44.harp_events(b, staff)]
        p.notes('P26', 128, H, evs[1:], staff=staff)
    state = copy_bars(state, final, 'P26', sorted(s44.HARP))
    p.use(state)
    p.articulate('P7', (128, H), (134, 3 * H), 'kStaccato')
    p.articulate('P6', (128, H), (131, H), 'kStaccato')
    for pid, sl in s44.SLURS.items():
        for a, z in sl:
            p.slur(pid, a, z)
    for pid in s44.INTO_128:
        p.slur(pid, want.chain_start(pid, 127, 0), (128, 0))
    for pid in ('P28', 'P2'):
        p.dynamic(pid, 128, 1, 'mp')
        p.dynamic(pid, 133, 0, 'mf')
    p.dynamic('P1', 133, 0, 'mf')
    p.dynamic('P6', *s44.RUN_FROM, 'mp')
    p.dynamic('P31', 129, 1, 'p')
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x, hold_oboe='--no-hold' not in sys.argv)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S44: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
