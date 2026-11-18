"""The Dorico steps for 111326 S26 (lab/pieces/p111326_s26.py): six hairpins and two dynamics on his
cor anglais notes, each selected by its ID.
usage (whisperer env): python lab/pieces/p111326_s26_dorico.py <working.xml> <S26.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan  # noqa: E402
import p111326_s26 as s26  # noqa: E402


def plan(x):
    p = Plan(x)
    for a, z, up in s26.HAIRPINS:
        p.hairpin('P4', a, z, up=up)
    for bar, onset, mark in s26.DYNAMICS:
        p.dynamic('P4', bar, onset, mark)
    return p


if __name__ == '__main__':
    p = plan(open(sys.argv[1], encoding='utf-8').read())
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
