"""111326 S37 (Nov 23 2026): S36 (lab/pieces/p111326_s36.py) with three more slurs. Horn 1, horn 2 and the
bassoon also fade over bar 105 and go on, p, into the soft harmony of bar 106; the new check in
lab/clash_check.py ("unslurred last note of a fade") found them unslurred there. Each is slurred from
its note of bar 105 into its note of bar 106, where its phrase slur of bars 106-109 starts.
usage (whisperer env): python lab/pieces/p111326_s37.py <export.xml> <out.xml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s36 as s36  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

INTO_106 = ('P9', 'P10', 'P7')


def build(x):
    sc0 = Score(x)
    y = s36.build(x)
    m = Marks(y)
    for pid in INTO_106:
        m.slur(pid, (105, s36.last_of_105(sc0, pid)), (106, 0), number=2)
    out = m.text()
    assert len(re.findall(r'<slur type="start" number="2"/>', out)) == len(re.findall(r'<slur type="stop" number="2"/>', out))
    return out


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
