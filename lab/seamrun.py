"""Generate the B section with gates calibrated from HIS 173 measured seams - zero Claude taste.

Model: HIS fine-tuned checkpoint (last night's blind winner).
Seed: bar 17 built from his transition playbook mechanically - the sextuplet motor thinned to one
      choir (clarinets+viola, his motor carriers) at p, everyone else resting. No pitch invention:
      the motor bar reuses bar 16's own motor pitches. Then the model writes 6 bars.

Gates, each from measurement, none from opinion:
  KEY   0.45 <= keycorr(A section, new bars) <= 0.92   (his median 0.71; excludes both static
        repetition and out-of-distribution jumps like Gb major)
  RIFF  riff level < 0.30                              (his median 0.07, 3 of 4 seams write new
        melody; hard-caps motif restatement, the E#0 failure)
  TEX   4 <= mean nonstring parts in first 4 bars <= 15  (his seams keep the band but halve
        activity - excludes both collapse and the going-nowhere tutti he flagged in the A/B)
  FADE  no ppp/pppp in first 4 bars
Rank survivors by nothing - present up to 3 to his ears. His verdicts are the ranking.
"""
import json, os, re, statistics as st, subprocess, sys, time, warnings
warnings.simplefilter('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, '/Users/bdogellis/repos/scorewright')
import notagen_arm as NA, retrieve
import deepdive as DD

BRIAN = '/Users/bdogellis/Documents/Score Exports/_models/weights_notagen_brian_small.pth'
SRC = '/Users/bdogellis/Documents/Score Exports/abc_augmented/Bb/Orchestral Idea_Bb.abc'
STEP = {'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}

lines = [l for l in open(SRC).read().split('\n') if l.strip()]
bi = [i for i, l in enumerate(lines) if l.startswith('[V:')]
head, body = lines[:bi[0]], [lines[j] for j in bi]

# seed bar 17: motor thinned to clarinets+viola at p; his bar 16 motor content, nothing invented
m16 = DD.voices_of(body[15])
keep = {5, 6, 22}
seed = ''.join(f'[V:{v}]!p! ' + re.sub(r'![^!]*!', '', m16[v]).strip()
               + ('|' if not m16[v].rstrip().endswith('|') else '')
               for v in sorted(keep) if v in m16)
prefix = '\n'.join(head + body[-9:] + [seed]) + '\n'


def pcs_and_seqs(text_bars):
    pcs = [0.0]*12; seqs = []
    for bl in text_bars:
        for v, t in DD.voices_of(bl).items():
            ps = NA.abc_pitches(t)
            for p in ps: pcs[p % 12] += 1
            if len(ps) >= 5: seqs.append([(p, 1.0, 0) for p in ps])
    return pcs, seqs


def corr(a, b):
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    d = (sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))**.5
    return num/d if d else 0


A_pcs, A_seqs = pcs_and_seqs(body[8:16])
A_g0 = set(h for s in A_seqs for k, h, _ in retrieve.grams(s) if k == 0)


def gate(gen):
    bars = [l for l in gen.split('\n') if l.strip()]
    if len(bars) < 4: return None
    B_pcs, B_seqs = pcs_and_seqs(bars)
    kc = corr(A_pcs, B_pcs)
    B_g0 = set(h for s in B_seqs for k, h, _ in retrieve.grams(s) if k == 0)
    riff = len(B_g0 & A_g0)/len(B_g0) if B_g0 else 0
    per = []
    for bl in bars[:4]:
        vs = DD.voices_of(bl)
        per.append(len([v for v in vs if NA.abc_pitches(vs[v]) and v not in DD.STRINGS]))
    tex = st.mean(per) if per else 0
    fade = bool(re.search(r'!p{3,4}!', '\n'.join(bars[:4])))
    ok = (0.45 <= kc <= 0.92) and (riff < 0.30) and (4 <= tex <= 15) and not fade
    return {'keycorr': round(kc,2), 'riff': round(riff,2), 'tex': round(tex,1),
            'fade': fade, 'passes': ok, 'bars': len(bars)}


if __name__ == '__main__':
    m, p = NA.load(BRIAN, layers=12, hidden=768, char_layers=3, patch_length=2048)
    print('his model up', flush=True)
    winners = 0
    for i in range(10):
        t = subprocess.run(['memory_pressure'], capture_output=True, text=True).stdout
        if int((re.search(r'free percentage: (\d+)', t) or [0,50])[1]) < 10:
            print('ABORT memory', flush=True); break
        t0 = time.time()
        gen = NA.continue_abc(m, p, prefix, n_bars=6, temperature=0.9)
        g = gate(gen)
        rec = {'i': i, 'secs': round(time.time()-t0,1), **(g or {'passes': False, 'bars': 0})}
        print(json.dumps(rec), flush=True)
        open(f'{HERE}/seam_{i}.abc', 'w').write(gen)
        open(f'{HERE}/seamrun.jsonl', 'a').write(json.dumps(rec)+'\n')
        if g and g['passes']:
            winners += 1
            if winners >= 3: break
    print(f'DONE SEAMRUN {winners} passing', flush=True)
