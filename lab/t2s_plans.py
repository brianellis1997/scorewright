"""Two plans for Orchestral Idea bars 17-32, in Text2Score's training format (5-10 measures).

P0 (control): plan describes only his bars 1-16 (measures 1, 5, 9, 13, 16); nothing said about 17-32.
P1 (steer):   same five, plus 17/21/25/29/32 written from his stated intent and the corpus seam
              stats: thin to strings, new material in a related key, winds enter, brass last,
              dominant of G by bar 32. Instrument names are his score's own part names.
"""
import os, pickle, sys
T2S = '/Users/bdogellis/Documents/Score Exports/_models/_text2score'
sys.path.insert(0, T2S)
from text2music.data.utils.xml2plan import convert_measures_to_text
HERE = os.path.dirname(os.path.abspath(__file__))
plan = pickle.load(open(f'{HERE}/oi_plan_full.pkl', 'rb'))
ALL = plan['all_instruments']
TOTAL = int(os.environ.get('T2S_TOTAL', 32))

STR = 'Violin I, Violin II, Viola, Violoncello, Contrabass'
NEW = {
    17: dict(inst=STR, rng='36–79', dens='Low', chords='[3, 7, 10]', dyn='pp'),
    21: dict(inst=STR + ', Bassoon 1, Clarinet in Bb 1', rng='36–84', dens='Moderate', chords='[7, 10, 2]', dyn='p'),
    25: dict(inst=STR + ', Bassoon 1, Bassoon 2, Clarinet in Bb 1, Flute 1, Oboe 1, Horn in F 1, Horn in F 2',
             rng='36–86', dens='Moderate', chords='[0, 3, 7]', dyn='mp, crescendo'),
    29: dict(inst=STR + ', Bassoon 1, Bassoon 2, Clarinet in Bb 1, Clarinet in Bb 2, Flute 1, Flute 2, Oboe 1, Oboe 2, '
             'Horn in F 1, Horn in F 2, Trombone 1, Trombone 2', rng='36–88', dens='Moderate', chords='[8, 0, 3]', dyn='mf'),
    32: dict(inst=STR + ', Bassoon 1, Bassoon 2, Bass Clarinet in Bb, Clarinet in Bb 1, Clarinet in Bb 2, Flute 1, Flute 2, '
             'Oboe 1, Oboe 2, Horn in F 1, Horn in F 2, Horn in F 3, Horn in F 4, Trumpet in Bb 1, Trumpet in Bb 2, '
             'Trombone 1, Trombone 2, Bass Trombone, Tuba', rng='31–91', dens='High', chords='[2, 6, 9, 0]', dyn='f'),
}


def measure_block(n, d):
    return (f"Measure: {n}\n  Instruments: {d['inst']}\n  Pitch Range: {d['rng']}\n  Note Density: {d['dens']}\n"
            f"  Tempo: None\n  Time Signature: 4/4\n  Key Signature: -2\n  Chords: {d['chords']}\n  Dynamics: {d['dyn']}\n")


base = {f'Measure: {n}': plan[f'Measure: {n}'] for n in (1, 5, 9, 13, 16)}
p0 = convert_measures_to_text(base, ALL, plan_length=TOTAL)
p1 = p0.rstrip('\n') + '\n\n' + '\n'.join(measure_block(n, NEW[n]) for n in sorted(NEW))
sfx = '' if TOTAL == 32 else f'_{TOTAL}'
open(f'{HERE}/t2s_plan_P0{sfx}.txt', 'w').write(p0)
open(f'{HERE}/t2s_plan_P1{sfx}.txt', 'w').write(p1)
print(p1)
print('P0 measures', p0.count('Measure:'), '| P1 measures', p1.count('Measure:'))
