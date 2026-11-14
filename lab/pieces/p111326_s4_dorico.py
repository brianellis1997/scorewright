"""111326 S4 put into Brian's open Dorico project after he pressed Accept in the panel (Nov 13 2026),
through the remote-control link (app/dorico_rc.py). This is the pattern for every Dorico change:
the suggestion first, Dorico only after Accept, then a fresh export compared with the suggestion.
That export matched S4 note for note and mark for mark.

Steps, each start note checked against the status bar before the command:
1. Horn 1 bars 8-16: select the bar-8 chord, extend bar by bar until the status bar shows
   "Bars 8-16", Edit.Copy; select the bar-8 chord again, NavigateDownExtend twice (one staff a
   press: Horn 1, Horn 2, Wagner tuba), Edit.PasteExplode. Explode carried the slurs, dynamics and
   hairpin to each staff.
2. Violin I bars 16-24 the same way onto Violin I, Violin II and the viola.
3. String slurs over 16-19 and 20-24 (NoteInput.SlurStart over the range).
4. The held notes: NoteInput.Tie on the first of two equal quarters; Dorico shows them as a half note.
5. Beams in pairs: Edit.SplitBeam on the third eighth of each four-eighth bar.
To reach the strings: from the oboe, NavigateDownNextStave goes to the bottom staff, then
NavigateUp one staff a press.
usage (whisperer env): python lab/pieces/p111326_s4_dorico.py   (it was run once; a second run would explode again)"""
import re, subprocess, sys

sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))), 'app'))
from dorico_rc import Dorico  # noqa: E402

A = 'Edit.SelectAtPoint?X=234&Y=201&AddToSelection=0&BlockSelection=0&NextSelectionAtPoint=0&SelectionTriggerAction=0'
d = None


def expect(bar, want):
    b, item, _ = d.sb()
    if b != bar or not item.startswith(want):
        raise SystemExit(f'STOP: expected bar {bar} {want!r}, Dorico shows bar {b} {item!r}')


def anchor():
    d.cmd(A, 1, 0.3); expect(7, 'Rest')
    d.cmd('EventEdit.NavigateRight'); expect(7, 'Note: E5 ')
    d.cmd('EventEdit.NavigateLeft'); expect(7, 'Rest')


def oboe(bar):
    anchor()
    if bar > 7:
        d.cmd('EventEdit.NavigateRightBar', bar - 7, 0.12)


def bars_shown():
    m = next((re.findall(r'\d+', p) for p in d.sb()[2] if p.startswith('Bars ')), None)
    return tuple(int(v) for v in m) if m else None


def extend_to(last):
    for _ in range(20):
        r = bars_shown()
        if r and r[-1] >= last:
            break
        d.cmd('EventEdit.NavigateRightExtendBar', 1, 0.2)
    if bars_shown()[-1] != last:
        raise SystemExit(f'STOP: the range shows {bars_shown()}')


if __name__ == '__main__':
    raise SystemExit('S4 is already in the project (Nov 13 2026). These steps are the pattern for the next change.')
