"""111326 S1, applied live in Brian's open Dorico project through the remote-control link
(app/dorico_rc.py), on Nov 13 2026, after he asked: "this needs to be seamless, like a Claude Code
session: you have the actual file, and Claude edits it." The 30 marks of p111326_s1.py, each one
undo step: every start note is reached from a fixed start point and checked against the status bar
(bar and concert pitch) before the mark is made; the script stops at the first mismatch. A fresh
export afterwards matched the plan mark for mark, with every note unchanged.

The start point, X=234 Y=201, is the oboe's quarter rest in bar 7 in his page layout that day (the
position of his own click in Dorico's log). Running this again would add the marks a second time.
usage (whisperer env): python lab/pieces/p111326_s1_dorico.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))
from dorico_rc import Dorico  # noqa: E402
A = 'Edit.SelectAtPoint?X=234&Y=201&AddToSelection=0&BlockSelection=0&NextSelectionAtPoint=0&SelectionTriggerAction=0'
OB = {7: 'R E5 D5', 8: 'E5 E5 D5', 9: 'E5 E5 D5', 10: 'E5 F5 G5 F5', 11: 'E5 D5 D5 C5', 12: 'D5 D5 C5', 13: 'D5 D5 C5',
      14: 'D5 E5 F5 E5', 15: 'D5 C5 B4', 16: 'A4', 17: 'G4'}
FL = {15: 'R E5 D5', 16: 'E5 E5 D5', 17: 'E5 E5 D5', 18: 'E5 F5 G5 F5', 19: 'E5 D5 C5 B4', 20: 'C5 C5 E5', 21: 'C5 C5 B4',
      22: 'A4 C5 D5 E5', 23: 'D5 C5 G5', 24: 'F5'}
HN = {8: 'C4', 15: 'G#4', 16: 'A4'}
DYN = 'NoteInput.CreateDynamic?Definition={}&UseLocalOverride=0'
PORT = 'NoteInput.SetArticulation?Value=kStaccatoTenuto'
SLUR = 'NoteInput.SlurStart'
UP = 'NoteInput.HairpinStart?Type=kGradualDynamicUp&GradualDynamicType=kCrescOrDim'
DOWN = 'NoteInput.HairpinStart?Type=kGradualDynamicDown&GradualDynamicType=kCrescOrDim'
done = []


def expect(bar, pitch):
    b, item, _ = d.sb()
    want = 'Rest' if pitch == 'R' else f'Note: {pitch} '
    if b != bar or not item.startswith(want):
        raise SystemExit(f'STOP after {len(done)} marks: expected bar {bar} {want!r}, Dorico shows bar {b} {item!r}')


def anchor():
    d.cmd(A, 1, 0.3)
    expect(7, 'R')
    d.cmd('EventEdit.NavigateRight', 1)
    expect(7, 'E5')
    d.cmd('EventEdit.NavigateLeft', 1)
    expect(7, 'R')


def at(staff, bar, k):
    anchor()
    if bar > 7:
        d.cmd('EventEdit.NavigateRightBar', bar - 7, 0.12)
    expect(bar, OB[bar].split()[0] if bar in OB else 'R')
    if staff == 'fl':
        d.cmd('EventEdit.NavigateUp', 1)
        expect(bar, FL[bar].split()[0])
        if k:
            d.cmd('EventEdit.NavigateRight', k)
        expect(bar, FL[bar].split()[k])
    elif staff == 'ob':
        if k:
            d.cmd('EventEdit.NavigateRight', k)
        expect(bar, OB[bar].split()[k])
    elif staff == 'hn':
        d.cmd('EventEdit.NavigateDown', 6, 0.15)
        expect(bar, HN[bar])
    elif staff == 'vn':
        seen = []
        for _ in range(60):
            d.cmd('EventEdit.NavigateDown', 1, 0.12)
            b, item, _ = d.sb()
            seen.append(item.startswith('Note'))
            if item.startswith('Note') and len(seen) > 9 and not any(seen[-2:-1]):
                break
        expect(bar, 'A4')


def mark(staff, bar, k, command, ext=0, label=''):
    at(staff, bar, k)
    if ext:
        d.cmd('EventEdit.NavigateRightExtend', ext, 0.12)
    errs = d.cmd(command, 1, 0.4)
    if errs:
        raise SystemExit(f'STOP after {len(done)} marks: {label} gave {errs}')
    done.append(label)
    print('ok', label, flush=True)



if __name__ == '__main__':
    d = Dorico()
    try:
        mark('ob', 7, 1, DYN.format('mp'), 0, 'oboe mp bar 7')
        for bar in (8, 9, 12, 13):
            mark('ob', bar, 0, PORT, 0, f'oboe portato bar {bar}')
        mark('ob', 9, 1, UP, 3, 'oboe cresc 9-10')
        mark('ob', 10, 2, DOWN, 5, 'oboe dim 10-11')
        mark('ob', 13, 1, UP, 3, 'oboe cresc 13-14')
        mark('ob', 14, 2, DOWN, 5, 'oboe dim 14-16')
        mark('ob', 17, 0, DYN.format('p'), 0, 'oboe p bar 17')
        mark('hn', 8, 0, DYN.format('p'), 0, 'horn p bar 8')
        mark('hn', 15, 0, DOWN, 0, 'horn dim bar 15')
        mark('hn', 16, 0, DYN.format('pp'), 0, 'horn pp bar 16')
        mark('vn', 16, 0, DYN.format('pp'), 0, 'violin I pp bar 16')
        for (bar, k, ext) in ((15, 1, 2), (16, 1, 2), (17, 1, 7), (19, 2, 2), (20, 1, 2), (21, 1, 7), (23, 2, 1)):
            mark('fl', bar, k, SLUR, ext, f'flute slur from bar {bar}')
        for bar in (16, 17, 20, 21):
            mark('fl', bar, 0, PORT, 0, f'flute portato bar {bar}')
        mark('fl', 17, 1, UP, 3, 'flute cresc 17-18')
        mark('fl', 18, 2, DOWN, 5, 'flute dim 18-19')
        mark('fl', 21, 1, UP, 7, 'flute cresc 21-23')
        mark('fl', 23, 2, DOWN, 1, 'flute dim 23-24')
        mark('fl', 15, 1, DYN.format('mp'), 0, 'flute mp bar 15')
    finally:
        print('marks done:', len(done))
        d.cmd('Edit.SelectNone', 1, 0.2)
