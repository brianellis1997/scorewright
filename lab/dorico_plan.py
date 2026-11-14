"""Map a change for Brian's open Dorico project to remote-control steps at the moment the suggestion
is made, so that his Accept runs them at once (app/dorico_apply.py) with no thinking in between.
The playbook with every recipe, timing and fact behind this: app/DORICO.md.

The plan is built from the score Dorico has now (a fresh export when he edited since the last one;
app/dorico_rc.py edits_since tells). Every step starts from the project's anchor, an item whose page
position is known from his own clicks in Dorico's log (the oboe's rest in bar 7 of 111326), walks to
its target with arrow commands counted from that score, and names what Dorico's status bar must show
there ("Note: G5", concert pitch). Vertical walks happen in the anchor's bar, then the walk moves
along the bars. When a step changes what a later step walks over (an explode fills staves), call
use() with the score as it is after that step.

usage:
    p = Plan(open('dorico_export.xml').read(), anchor=('P3', 7, 234, 201))
    p.explode('P9', 8, 16, staves=3)              # horn 1's chords onto horn 1, horn 2, Wagner tuba
    p.use(open('S5.musicxml').read())
    p.slur('P28', (16, 0), (19, None), staves=3)  # None: the last item of the bar
    p.dynamic('P2', 15, 1.5, 'mp'); p.hairpin('P2', (16, 0), (18, 1.0), up=True)
    p.articulation('P2', 16, 0); p.tie('P29', 17, 0); p.split_beam('P3', 10, 1.0)
    p.save('S5.dorico.json')                      # sw_suggest.py --plan does this beside the suggestion"""
import json, re

STEPS = 'CDEFGAB'
PC = dict(C=0, D=2, E=4, F=5, G=7, A=9, B=11)
KEEPS = ('NoteInput.SetArticulation', 'Edit.SplitBeam')
PITCH = r'<step>(\w)</step>(?:\s*<alter>(-?\d+)</alter>)?\s*<octave>(\d+)</octave>'


def shift(p, d, c):
    step, alter, octave = p
    di = octave * 7 + STEPS.index(step) + d
    mi = 12 * (octave + 1) + PC[step] + alter + c
    s, o = STEPS[di % 7], di // 7
    return s, mi - (12 * (o + 1) + PC[s]), o


def count(specs):
    return sum(int(c.partition('*')[2] or 1) for c in specs)


def name(p):
    step, alter, octave = p
    return step + ('#' * alter if alter > 0 else 'b' * -alter) + str(octave)


class Plan:
    def __init__(self, xml, anchor):
        self.use(xml)
        self.anchor = dict(part=anchor[0], bar=anchor[1],
                           command=f'Edit.SelectAtPoint?X={anchor[2]}&Y={anchor[3]}&AddToSelection=0&BlockSelection=0&NextSelectionAtPoint=0&SelectionTriggerAction=0')
        self.steps = []

    def use(self, xml):
        """the score the next steps walk over: Dorico's score as it will be when they run"""
        self.parts, self.staves, self.tied = {}, [], set()
        self.names = dict(re.findall(r'<score-part id="([^"]+)">\s*<part-name>([^<]*)</part-name>', xml))
        for pid in re.findall(r'<score-part id="([^"]+)"', xml):
            body = re.search(rf'<part id="{pid}">(.*?)</part>', xml, re.S).group(1)
            t = re.search(r'<transpose\b.*?</transpose>', body, re.S)
            tx = t.group(0) if t else ''
            g = lambda tag: int(m.group(1)) if (m := re.search(rf'<{tag}>(-?\d+)</{tag}>', tx)) else 0
            tr = (g('diatonic') + 7 * g('octave-change'), g('chromatic') + 12 * g('octave-change'))
            n = int((re.search(r'<staves>(\d+)</staves>', body) or [0, 1])[1])
            self.parts[pid] = (body, tr)
            self.staves += [(pid, s) for s in range(1, n + 1)]

    def items(self, pid, bar, staff=1):
        """[(onset in quarters, 'Rest' or [concert names, top first], tie continuation)] for voice 1 of a staff in a bar"""
        body, tr = self.parts[pid]
        m = re.search(rf'<measure number="{bar}"[^>]*>(.*?)</measure>', body, re.S)
        div = int(re.findall(r'<divisions>(\d+)</divisions>', body[:m.end()])[-1])
        t, out = 0, []
        for ev in re.finditer(r'<note[ >].*?</note>|<backup>.*?</backup>|<forward>.*?</forward>', m.group(1), re.S):
            s = ev.group(0)
            d = int((re.search(r'<duration>(\d+)</duration>', s) or [0, 0])[1])
            if s.startswith('<backup'):
                t -= d
                continue
            if s.startswith('<forward'):
                t += d
                continue
            if int((re.search(r'<staff>(\d+)</staff>', s) or [0, 1])[1]) != staff or '<grace' in s:
                continue
            if '<chord/>' in s:
                if out and out[-1][1] != 'Rest':
                    p = re.search(PITCH, s)
                    out[-1][1].append(shift((p.group(1), int(p.group(2) or 0), int(p.group(3))), *tr))
                continue
            if '<rest' in s:
                out.append([t / div, 'Rest', False])
            else:
                p = re.search(PITCH, s)
                out.append([t / div, [shift((p.group(1), int(p.group(2) or 0), int(p.group(3))), *tr)],
                            '<tie type="stop"/>' in s and '<tie type="start"/>' not in s])
            t += d
        for it in out:
            if it[1] != 'Rest':
                it[1] = [name(p) for p in sorted(it[1], key=lambda p: -(12 * (p[2] + 1) + PC[p[0]] + p[1]))]
        return out

    def index(self, pid, bar, onset=None, staff=1):
        its = self.items(pid, bar, staff)
        return len(its) - 1 if onset is None else next(i for i, it in enumerate(its) if abs(it[0] - onset) < 1e-6)

    def height(self, index, bar):
        """arrow presses a staff takes at the bar line: one per note of its chord, or one for a rest"""
        pid, staff = self.staves[index]
        first = self.items(pid, bar, staff)[0][1]
        return 1 if first == 'Rest' else len(first)

    def at(self, pid, bar, onset, staff=1):
        a = next(i for i, s in enumerate(self.staves) if s == (self.anchor['part'], 1))
        z = next(i for i, s in enumerate(self.staves) if s == (pid, staff))
        ab = self.anchor['bar']
        moves = []
        if z > a:
            down = self.height(a, ab) + sum(self.height(i, ab) for i in range(a + 1, z))
            up = sum(self.height(i, ab) for i in range(z + 1, len(self.staves) - 1)) + 1
            moves = [f'EventEdit.NavigateDown*{down}'] if down <= up + 1 else ['EventEdit.NavigateDownNextStave', f'EventEdit.NavigateUp*{up}']
        elif z < a:
            moves = [f'EventEdit.NavigateUp*{sum(self.height(i, ab) for i in range(z, a))}']
        if bar > ab:
            moves.append(f'EventEdit.NavigateRightBar*{bar - ab}')
        elif bar < ab:
            moves.append(f'EventEdit.NavigateLeftBar*{ab - bar}')
        its = self.items(pid, bar, staff)
        k = self.index(pid, bar, onset, staff)
        if any(it[2] for it in its[:k + 1]):
            raise ValueError(f'{self.who(pid)} bar {bar}: the walk crosses a note tied from the bar before; test how Dorico steps over it first (DORICO.md)')
        if any(t[:3] == (pid, staff, bar) and t[3] < its[k][0] for t in self.tied):
            raise ValueError(f'{self.who(pid)} bar {bar}: an earlier tie in this bar merges two items; put ties last on the staff, or call use() with the tied score')
        if k:
            moves.append(f'EventEdit.NavigateRight*{k}')
        target = its[k][1]
        expect = ['Rest'] if target == 'Rest' else [f'Note: {n} ' for n in target] + ([f'Chord: {", ".join(reversed(target))} '] if len(target) > 1 else [])
        return dict(part=pid, staff=staff, bar=bar, item=k, moves=moves, expect=[bar, expect],
                    unique=sum(1 for it in its if it[1] == target) == 1)

    def span(self, pid, b0, k0, b1, o1=None, staff=1):
        """NavigateRightExtend presses from item k0 of bar b0 to the item at onset o1 of bar b1 (its last if None)"""
        k1 = self.index(pid, b1, o1, staff)
        if any(it[2] for b in range(b0, b1 + 1) for it in self.items(pid, b, staff)[k0 + 1 if b == b0 else 0:]):
            raise ValueError(f'{self.who(pid)} bars {b0}-{b1}: the range crosses a note tied from the bar before; test how Dorico counts it first (DORICO.md)')
        if any(t[:2] == (pid, staff) and b0 <= t[2] <= b1 for t in self.tied):
            raise ValueError(f'{self.who(pid)} bars {b0}-{b1}: a tie in the range merges two items; put ties last on the staff, or call use() with the tied score')
        if b1 == b0:
            return k1 - k0
        return len(self.items(pid, b0, staff)) - k0 + sum(len(self.items(pid, b, staff)) for b in range(b0 + 1, b1)) + k1

    def step(self, label, at, to=None, down=0, edits=(), plain=()):
        """walk to `at` and check it, select on to `to` = (bar, onset or None) and `down` more staves,
        then run `plain` (nothing to undo) and `edits` (one undo step each). When the step before ended
        on one note of the same staff, `rel` is the short walk from there: after edits that leave that
        note selected (KEEPS), or else when this target is the only one of its pitch in its bar, so a
        walk that starts from the new mark cannot pass the check by luck. The runner tries `rel`
        first and walks from the anchor on a miss."""
        prev = self.steps[-1] if self.steps else None
        s = dict(label=label, moves=at['moves'], expect=at['expect'], extend=[], at=[at['part'], at['staff'], at['bar'], at['item']])
        keeps = all(e.split('?')[0] in KEEPS for e in prev['edits']) if prev else False
        if prev and prev['at'][:2] == s['at'][:2] and not prev['extend'] and (at['unique'] or keeps):
            b1, k1, b, k = prev['at'][2], prev['at'][3], at['bar'], at['item']
            rel = ([] if (b, k) == (b1, k1) else [f'EventEdit.NavigateRight*{k - k1}'] if b == b1 and k > k1 else
                   [f'EventEdit.NavigateRightBar*{b - b1}'] + ([f'EventEdit.NavigateRight*{k}'] if k else []) if b > b1 else None)
            if rel is not None and count(rel) < 1 + count(at['moves']):
                s['rel'] = rel
        if to:
            n = self.span(at['part'], at['bar'], at['item'], to[0], to[1], at['staff'])
            if n:
                s['extend'].append(f'EventEdit.NavigateRightExtend*{n}')
                s['range'] = [at['bar'], to[0]]
        if down:
            s['extend'].append(f'EventEdit.NavigateDownExtend*{down}')
        s['plain'], s['edits'] = list(plain), list(edits)
        self.steps.append(s)
        return s

    def who(self, pid):
        return self.names.get(pid, pid)

    def probe(self, label, pid, bar, onset, staff=1):
        return self.step(label, self.at(pid, bar, onset, staff))

    def dynamic(self, pid, bar, onset, mark, staff=1):
        return self.step(f'{mark} for {self.who(pid)} in bar {bar}', self.at(pid, bar, onset, staff),
                         edits=[f'NoteInput.CreateDynamic?Definition={mark}&UseLocalOverride=0'])

    def articulation(self, pid, bar, onset, value='kStaccatoTenuto', staff=1):
        return self.step(f'{value[1:]} for {self.who(pid)} in bar {bar}', self.at(pid, bar, onset, staff),
                         edits=[f'NoteInput.SetArticulation?Value={value}'])

    def slur(self, pid, start, end, staves=1, staff=1):
        return self.step(f'slur for {self.who(pid)} bars {start[0]}-{end[0]}', self.at(pid, *start, staff), to=end,
                         down=staves - 1, edits=['NoteInput.SlurStart'])

    def hairpin(self, pid, start, end, up=True, staves=1, staff=1):
        kind = 'Up' if up else 'Down'
        return self.step(f'{"cresc" if up else "dim"} for {self.who(pid)} bars {start[0]}-{end[0]}', self.at(pid, *start, staff), to=end,
                         down=staves - 1, edits=[f'NoteInput.HairpinStart?Type=kGradualDynamic{kind}&GradualDynamicType=kCrescOrDim'])

    def tie(self, pid, bar, onset, staff=1):
        s = self.step(f'tie for {self.who(pid)} in bar {bar}', self.at(pid, bar, onset, staff), edits=['NoteInput.Tie'])
        self.tied.add((pid, staff, bar, onset))
        return s

    def split_beam(self, pid, bar, onset, staff=1):
        return self.step(f'beam split for {self.who(pid)} in bar {bar}', self.at(pid, bar, onset, staff), edits=['Edit.SplitBeam'])

    def explode(self, pid, b0, b1, staves, staff=1):
        """copy the chords of bars b0-b1 and paste-explode them onto this staff and the staves-1 below it"""
        self.step(f'copy {self.who(pid)} bars {b0}-{b1}', self.at(pid, b0, 0, staff), to=(b1, None), plain=['Edit.Copy'])
        return self.step(f'spread over {staves} staves', self.at(pid, b0, 0, staff), down=staves - 1, edits=['Edit.PasteExplode'])

    def commands(self):
        return sum(count(s['rel'] if 'rel' in s else [self.anchor['command']] + s['moves']) + count(s['extend'] + s['plain'] + s['edits']) for s in self.steps)

    def save(self, path):
        json.dump(dict(anchor=self.anchor, steps=self.steps, commands=self.commands()), open(path, 'w'), indent=1)
