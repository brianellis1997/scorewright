"""Text2Score fine-tune on Brian's multi-instrument scores, on Apple silicon, with plans extracted
from his own MusicXML so the model learns HIS texture given a plan.

Deliberate departures from their finetune/train-gen.py, each for a reason found tonight:
  - crops are BAR-aligned and the plan is renumbered relative to the crop (Measure 1 = first bar
    of the window). Their random head/tail/middle crops restart the [r:] index at 0 while plan
    measure numbers stay absolute, which is one reason the plan pulled so weakly at his seam.
  - only the top PATCH layers + char decoder train (bottom FREEZE_BELOW frozen, encoder frozen):
    the plan-to-notes cross-attention is what has to change, and half the backward is skipped.
  - scores with fewer than MIN_INSTRUMENTS parts are excluded: piano pieces teach nothing about
    thinning an orchestra.
  - fp32 on MPS, batch 1, OOM-skip, memory_pressure guard, thermal log every 100 steps.
"""
import os, re, sys, json, random, time, pickle, subprocess
import numpy as np, torch
from torch.utils.data import Dataset, DataLoader
HERE = os.path.dirname(os.path.abspath(__file__))
T2S = '/Users/bdogellis/Documents/Score Exports/_models/_text2score'
sys.path.insert(0, f'{T2S}/text2music/inference')
sys.path.insert(0, T2S)
sys.path.insert(0, HERE)                      # ft2/ FIRST so `from config import *` reads ours
from config import *
from utils import Patchilizer, CustomLMHeadModel
from text2music.data.utils.xml2plan import get_priority_order, get_measures, convert_measures_to_text
from transformers import GPT2Config, get_constant_schedule_with_warmup

DEV = torch.device('mps') if torch.backends.mps.is_available() else torch.device('cpu')
random.seed(0); np.random.seed(0); torch.manual_seed(0)
SMOKE = bool(os.environ.get('SMOKE'))
pat = Patchilizer()

PC = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'Fb': 4, 'E#': 5, 'F': 5, 'F#': 6, 'Gb': 6,
      'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11, 'Cb': 11, 'B#': 0}
NAME = {0: 'C', 1: 'Db', 2: 'D', 3: 'Eb', 4: 'E', 5: 'F', 6: 'F#', 7: 'G', 8: 'Ab', 9: 'A', 10: 'Bb', 11: 'B'}
ALT = {1: 'C#', 6: 'Gb', 11: 'Cb'}


def major_pc(key):
    """'Bmin' -> relative major pitch class; 'Gb' -> 6. Unknown -> 0."""
    m = re.match(r'^([A-G][#b]?)(min|dor|phr|lyd|mix|loc|maj|m)?$', key or '')
    if not m:
        return 0
    pc = PC.get(m.group(1), 0)
    mode = m.group(2) or ''
    shift = {'min': 3, 'm': 3, 'dor': 10, 'phr': 8, 'lyd': 5, 'mix': 7, 'loc': 1}.get(mode, 0)
    return (pc + shift) % 12


def plan_for_crop(plan, s, L, pitch_shift):
    sub = {}
    for j in range(L):
        k = f'Measure: {s + 1 + j}'
        if k in plan:
            sub[f'Measure: {j + 1}'] = plan[k]
    if not sub:
        return ''
    work = dict(sub); work['all_instruments'] = plan['all_instruments']
    top, _ = get_priority_order(work, top_pct=10, top_n=random.randint(5, 10))
    meas = get_measures(work, top)
    if 'Measure: 1' in sub:
        meas['Measure: 1'] = sub['Measure: 1']
    return convert_measures_to_text(meas, plan['all_instruments'], pitch_shift=pitch_shift, plan_length=L)


class DS(Dataset):
    def __init__(self, files, train=True):
        self.f, self.train = files, train

    def __len__(self):
        return len(self.f)

    def __getitem__(self, i):
        fp = self.f[i]['path']
        folder, stem = os.path.dirname(fp), os.path.basename(fp)
        opc = major_pc(self.f[i].get('key'))
        if self.train:
            prob = [1, 2, 3, 4, 3, 2, 1]
            o = random.choices(range(-3, 4), weights=prob)[0]
        else:
            o = 0
        pc = (opc + o) % 12
        cands = [NAME[pc]] + ([ALT[pc]] if pc in ALT else [])
        if pc in ALT and random.random() < 0.2:
            cands.reverse()
        path = next((os.path.join(folder, k, f'{stem}_{k}.abc') for k in cands
                     if os.path.exists(os.path.join(folder, k, f'{stem}_{k}.abc'))), None)
        if path is None:
            k = NAME[opc]; path = os.path.join(folder, k, f'{stem}_{k}.abc'); o = 0
            if not os.path.exists(path):
                return None
        pk = os.path.join(PLANS_DIR, stem + '.pkl')
        if not os.path.exists(pk):
            return None
        plan = pickle.load(open(pk, 'rb'))
        lines = [l for l in open(path, encoding='utf-8').read().split('\n') if l.strip()
                 and not l.startswith('T:') and not l.startswith('C:')]
        bi = next((i for i, l in enumerate(lines) if l.startswith('[V:')), None)
        if bi is None:
            return None
        header, body = lines[:bi], lines[bi:]
        n = len(body)
        hp = len(pat.patchilize_metadata([l + '\n' for l in header]))
        per = [len(pat.patchilize_tunebody([f'[r:{i}/{n - 1 - i}]' + l + '\n'])) for i, l in enumerate(body)]
        budget = MAXP - hp - 2
        if sum(per) <= budget or not self.train:
            s, e = 0, n
            if sum(per) > budget:
                e, acc = 0, 0
                while e < n and acc + per[e] <= budget:
                    acc += per[e]; e += 1
        else:
            s = random.randint(0, n - 1)
            e, acc = s, 0
            while e < n and acc + per[e] <= budget:
                acc += per[e]; e += 1
            if e - s < 2:
                s = 0; e, acc = 0, 0
                while e < n and acc + per[e] <= budget:
                    acc += per[e]; e += 1
        L = e - s
        if L < 1:
            return None
        text = '\n'.join(header + body[s:e]) + '\n'
        ids = pat.encode_train(text, patch_length=PATCH_LENGTH, patch_size=PATCH_SIZE)
        ptxt = plan_for_crop(plan, s, L, o)
        pids = pat.encode_plan(ptxt)
        return (torch.tensor(ids, dtype=torch.long), torch.tensor([1] * len(ids), dtype=torch.long), pids)


def collate(batch):
    b = [x for x in batch if x is not None]
    if not b:
        return None
    ids, ms, pids = b[0]
    return ids.unsqueeze(0).to(DEV), ms.unsqueeze(0).to(DEV), pids.unsqueeze(0).to(DEV)


def keep(rec):
    pk = os.path.join(PLANS_DIR, os.path.basename(rec['path']) + '.pkl')
    if not os.path.exists(pk):
        return False
    try:
        return len(pickle.load(open(pk, 'rb')).get('all_instruments', [])) >= MIN_INSTRUMENTS
    except Exception:
        return False


def health():
    t = subprocess.run(['memory_pressure'], capture_output=True, text=True).stdout
    fp = int((re.search(r'free percentage: (\d+)', t) or [0, 50])[1])
    th = subprocess.run(['pmset', '-g', 'therm'], capture_output=True, text=True).stdout
    lim = (re.search(r'CPU_Speed_Limit\s*=\s*(\d+)', th) or [0, 'n/a'])[1]
    if 'No thermal warning' in th: lim = 'no thermal warning'
    elif 'thermal warning level' in th.lower(): lim = th.strip().split('\n')[-1][:40]
    bt = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True).stdout
    bat = (re.search(r'(\d+%); ([a-z ]+)', bt) or [0, '?', '?'])
    return fp, lim, f'{bat[1]} {bat[2]}' if bat != 0 else '?'


if __name__ == '__main__':
    pc_ = GPT2Config(num_hidden_layers=PATCH_NUM_LAYERS, max_length=PATCH_LENGTH, max_position_embeddings=PATCH_LENGTH,
                     n_embd=HIDDEN_SIZE, num_attention_heads=HIDDEN_SIZE // 64, vocab_size=1)
    cc_ = GPT2Config(num_hidden_layers=CHAR_NUM_LAYERS, max_length=PATCH_SIZE + 1, max_position_embeddings=PATCH_SIZE + 1,
                     hidden_size=HIDDEN_SIZE, num_attention_heads=HIDDEN_SIZE // 64, vocab_size=128)
    model = CustomLMHeadModel(encoder_config=pc_, decoder_config=cc_)
    ck = torch.load(INIT_PATH, map_location='cpu', weights_only=False)
    print('init from', INIT_PATH, flush=True)
    model.load_state_dict(ck['model'], strict=False); del ck
    trainable = []
    for name, p in model.named_parameters():
        ok = name.startswith('char_level_decoder') or name.startswith('patch_level_model.base.ln_f') \
            or name.startswith('patch_level_model.context_layernorm') \
            or any(name.startswith(f'patch_level_model.base.h.{k}.') for k in range(FREEZE_BELOW, PATCH_NUM_LAYERS))
        p.requires_grad = ok
        if ok:
            trainable.append(p)
    model = model.to(DEV)
    print(f'params total {sum(p.numel() for p in model.parameters())/1e6:.0f}M, trainable '
          f'{sum(p.numel() for p in trainable)/1e6:.0f}M, device {DEV}', flush=True)
    opt = torch.optim.AdamW(trainable, lr=LEARNING_RATE)
    sched = get_constant_schedule_with_warmup(opt, num_warmup_steps=50)

    train_files = [r for r in (json.loads(l) for l in open(DATA_TRAIN_INDEX_PATH)) if keep(r)]
    eval_files = [r for r in (json.loads(l) for l in open(DATA_EVAL_INDEX_PATH)) if keep(r)]
    if SMOKE:
        train_files, eval_files = train_files[:6], eval_files[:3]
    print(f'train {len(train_files)} scores (>= {MIN_INSTRUMENTS} instruments), eval {len(eval_files)}', flush=True)
    tl = DataLoader(DS(train_files, True), batch_size=1, shuffle=True, collate_fn=collate)
    el = DataLoader(DS(eval_files, False), batch_size=1, shuffle=False, collate_fn=collate)

    best = 1e9
    for epoch in range(1, NUM_EPOCHS + 1):
        model.train(); tot = 0; n = 0; t0 = time.time()
        for batch in tl:
            if batch is None:
                continue
            xs, ms, ps = batch
            try:
                loss = model(ps, xs, ms).loss
                loss.backward()
                opt.step(); sched.step(); model.zero_grad(set_to_none=True)
            except RuntimeError as e:
                if 'out of memory' in str(e).lower():
                    model.zero_grad(set_to_none=True); torch.mps.empty_cache()
                    print(f'  oom-skip step {n} ({xs.shape[1]} patches)', flush=True); continue
                raise
            tot += loss.item(); n += 1
            if n % 25 == 0:
                print(f'  e{epoch} {n}/{len(tl)} loss {tot/n:.4f} {(time.time()-t0)/n:.1f}s/it', flush=True)
            if n % 100 == 0 or (SMOKE and n % 2 == 0):
                fp, lim, bat = health()
                print(f'  health: mem free {fp}%  thermal {lim}  battery {bat}', flush=True)
                if fp < 8:
                    torch.save({'model': model.state_dict(), 'epoch': epoch, 'partial': n}, WEIGHTS_OUT)
                    print(f'ABORT: memory free {fp}%, checkpoint saved at step {n}', flush=True); sys.exit(1)
            if SMOKE and n >= 6:
                break
        model.eval(); ev = 0; m2 = 0
        with torch.no_grad():
            for batch in el:
                if batch is None:
                    continue
                xs, ms, ps = batch
                try:
                    ev += model(ps, xs, ms).loss.item(); m2 += 1
                except RuntimeError as e:
                    if 'out of memory' in str(e).lower():
                        torch.mps.empty_cache(); continue
                    raise
        ev /= max(m2, 1)
        print(f'EPOCH {epoch}: train {tot/max(n,1):.4f}  eval {ev:.4f}  ({(time.time()-t0)/60:.1f} min)', flush=True)
        if ev < best and not SMOKE:
            best = ev
            torch.save({'model': model.state_dict(), 'epoch': epoch, 'eval': ev}, WEIGHTS_OUT)
            print(f'  saved -> {WEIGHTS_OUT}', flush=True)
    print('TRAINING DONE', flush=True)
