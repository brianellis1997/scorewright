"""111326 S7 (Nov 13 2026): everything moves one bar later, so the piece can open with an 8-bar
introduction: "move all this stuff up to bar 9 so we can have an eight bar introduction... the two
eighth notes that the oboe starts on in bar 7 would start in bar 8, and the phrase starts in bar 9".
Bars 1-6 are empty, so one empty bar goes in before bar 3 in every part; nothing else changes. In
Dorico that is one NoteInput.CreateBarLine with the time in quarters (Plan.insert_bars).
usage (whisperer env): python lab/pieces/p111326_s7.py <S6 or the working score> <out.xml> [plan.json]"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan  # noqa: E402

AT = 3


def build(x):
    def part(m):
        pid, body = m.group(1), m.group(2)
        bar = re.search(rf'<measure number="{AT}"[^>]*>.*?</measure>', body, re.S)
        assert bar and '<pitch>' not in bar.group(0) and '<direction' not in bar.group(0), f'{pid} bar {AT} is not empty'
        body = re.sub(r'<measure number="(\d+)"', lambda n: f'<measure number="{int(n.group(1)) + 1}"' if int(n.group(1)) >= AT else n.group(0), body)
        return f'<part id="{pid}">' + body.replace(bar.group(0).replace(f'number="{AT}"', f'number="{AT + 1}"', 1), bar.group(0) + '\n' + bar.group(0).replace(f'number="{AT}"', f'number="{AT + 1}"', 1), 1) + '</part>'
    return re.sub(r'<part id="([^"]+)">(.*?)</part>', part, x, flags=re.S)


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    out = build(x)
    open(sys.argv[2], 'w', encoding='utf-8').write(out)
    if len(sys.argv) > 3:
        p = Plan(x)
        p.insert_bars(AT, 1, ('P3', 7, 1.0))
        p.save(sys.argv[3])
    print('wrote', sys.argv[2])
