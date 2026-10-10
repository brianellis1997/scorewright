"""Instructed-infill training (PROJECT.md section 49) on the Text2Score decoder, Apple silicon.

Reads documents from edit_format.py (JSONL: text, answer_start, kind). Differences from ft2:
  - the instruction goes through the text encoder (where the plan used to go) AND stays in-text;
  - loss only on patches after the `%%answer` line: attention sees everything, the char decoder
    is trained only on the answer (their forward ties both to one mask, so this bypasses it);
  - proximity crop: the header, the bars nearest the target region, and the answer, within MAXP.
Env knobs: T2S_DOCS (train jsonl), T2S_DOCS_EVAL, T2S_INIT, T2S_OUT, T2S_EPOCHS, T2S_LR, T2S_MAXP,
T2S_FREEZE_BELOW, SMOKE.
"""
import os, re, sys, json, random, time, subprocess
from unidecode import unidecode
import numpy as np, torch
from torch.utils.data import Dataset, DataLoader
HERE = os.path.dirname(os.path.abspath(__file__))
T2S = os.path.join(os.environ['SW_ROOT'], '_text2score') if os.environ.get('SW_ROOT') else '/Users/bdogellis/Documents/Score Exports/_models/_text2score'
sys.path.insert(0, f'{T2S}/text2music/inference')
sys.path.insert(0, T2S)
sys.path.insert(0, os.path.join(HERE, '..', 'ft2'))      # ft2/config.py: PATCH_* etc.
from config import *
from utils import Patchilizer, CustomLMHeadModel
from transformers import GPT2Config, get_constant_schedule_with_warmup

DEV = torch.device(os.environ['T2S_DEVICE']) if os.environ.get('T2S_DEVICE') else (torch.device('cuda') if torch.cuda.is_available() else (torch.device('mps') if torch.backends.mps.is_available() else torch.device('cpu')))
ACCUM = int(os.environ.get('T2S_ACCUM', 1))
EVAL_EVERY = int(os.environ.get('T2S_EVAL_EVERY', 0))
EVAL_N = int(os.environ.get('T2S_EVAL_N', 200))
_SEED = int(os.environ.get('T2S_SEED', 0)); random.seed(_SEED); np.random.seed(_SEED); torch.manual_seed(_SEED)
SMOKE = bool(os.environ.get('SMOKE'))
DOCS = os.environ.get('T2S_DOCS')
DOCS_EVAL = os.environ.get('T2S_DOCS_EVAL')
OUT = os.environ.get('T2S_OUT', MODELS + 'weights_text2score_edit.pth')
pat = Patchilizer()


def crop(text, answer_start, budget_chars):
    """Keep header + answer + the body lines nearest the target region until budget_chars."""
    ctx, ans = text[:answer_start], text[answer_start:]
    lines = [l for l in ctx.split('\n') if l.strip()]
    bi = next((i for i, l in enumerate(lines) if l.startswith('[V:') or l.startswith('[b:') or l == '?'), len(lines))
    header, body = lines[:bi], [l for l in lines[bi:] if l != '%%answer']
    tgt = [i for i, l in enumerate(body) if l.endswith(']?') or l == '?' or '?|' in l]
    if not tgt:                                    # continuation: the target is the end
        tgt = [len(body) - 1]
    lo, hi = min(tgt), max(tgt)
    keep = set(range(lo, hi + 1))
    used = sum(len(l) + 1 for l in header) + sum(len(body[i]) + 1 for i in keep) + len(ans) + 16
    left, right = lo - 1, hi + 1
    while used < budget_chars and (left >= 0 or right < len(body)):
        cand = []
        if left >= 0: cand.append(left)
        if right < len(body): cand.append(right)
        i = cand[0] if len(cand) == 1 else (left if random.random() < 0.7 else right)
        if used + len(body[i]) + 1 > budget_chars:
            break
        keep.add(i); used += len(body[i]) + 1
        if i == left: left -= 1
        else: right += 1
    body2 = [body[i] for i in sorted(keep)]
    return '\n'.join(header + body2) + '\n%%answer\n' + ans


class DS(Dataset):
    def __init__(self, path, n=None):
        self.d = [json.loads(l) for l in open(path)]
        if n: self.d = self.d[:n]

    def __len__(self):
        return len(self.d)

    def __getitem__(self, i):
        d = self.d[i]
        budget = MAXP * PATCH_SIZE * 0.8
        for _ in range(12):                      # budget in patches, not chars: lines pad to whole patches
            text = crop(d['text'], d['answer_start'], budget_chars=budget)
            text = ''.join(c if ord(c) < 128 else unidecode(c) for c in text.replace('\u266d', 'b').replace('\u266f', '#'))
            if len(pat.encode_generate(text)) <= PATCH_LENGTH:
                break
            budget *= 0.8
        instr = text.split('\n', 1)[0].replace('%%instruction: ', '')
        ids = pat.encode_train(text, patch_length=PATCH_LENGTH, patch_size=PATCH_SIZE)
        acc = ''; loss_from = None
        for k, p in enumerate(ids):
            acc += pat.patch2chars(p)
            if '%%answer' in acc:
                loss_from = k + 1; break
        if loss_from is None or loss_from >= len(ids) - 1:
            return None
        return (torch.tensor(ids, dtype=torch.long), loss_from, pat.encode_plan(instr), d['kind'])


def collate(b):
    b = [x for x in b if x is not None]
    if not b:
        return None
    ids, lf, pids, kind = b[0]
    return ids.unsqueeze(0).to(DEV), lf, pids.unsqueeze(0).to(DEV), kind


def answer_loss(model, ids, loss_from, pids):
    patches = ids.reshape(1, -1, PATCH_SIZE)
    enc = model.patch_level_model(pids, patches)['last_hidden_state']       # attention over all
    encoded = enc[0, loss_from - 1:-1]
    targets = patches[0, loss_from:]
    return model.char_level_decoder(encoded, targets).loss


def health():
    try:
        t = subprocess.run(['memory_pressure'], capture_output=True, text=True).stdout
        return int((re.search(r'free percentage: (\d+)', t) or [0, 50])[1])
    except FileNotFoundError:
        return 50


if __name__ == '__main__':
    pc_ = GPT2Config(num_hidden_layers=PATCH_NUM_LAYERS, max_length=PATCH_LENGTH, max_position_embeddings=PATCH_LENGTH,
                     n_embd=HIDDEN_SIZE, num_attention_heads=HIDDEN_SIZE // 64, vocab_size=1)
    cc_ = GPT2Config(num_hidden_layers=CHAR_NUM_LAYERS, max_length=PATCH_SIZE + 1, max_position_embeddings=PATCH_SIZE + 1,
                     hidden_size=HIDDEN_SIZE, num_attention_heads=HIDDEN_SIZE // 64, vocab_size=128)
    model = CustomLMHeadModel(encoder_config=pc_, decoder_config=cc_)
    ck = torch.load(INIT_PATH, map_location='cpu', weights_only=False)
    model.load_state_dict(ck['model'], strict=False); del ck
    print('init from', INIT_PATH, flush=True)
    trainable = []
    for name, p in model.named_parameters():
        ok = name.startswith('char_level_decoder') or name.startswith('patch_level_model.base.ln_f') \
            or name.startswith('patch_level_model.context_layernorm') \
            or any(name.startswith(f'patch_level_model.base.h.{k}.') for k in range(FREEZE_BELOW, PATCH_NUM_LAYERS))
        p.requires_grad = ok
        if ok: trainable.append(p)
    model = model.to(DEV)
    print(f'trainable {sum(p.numel() for p in trainable)/1e6:.0f}M on {DEV}', flush=True)
    opt = torch.optim.AdamW(trainable, lr=LEARNING_RATE)
    sched = get_constant_schedule_with_warmup(opt, num_warmup_steps=50)
    tl = DataLoader(DS(DOCS, 12 if SMOKE else None), batch_size=1, shuffle=True, collate_fn=collate)
    el = DataLoader(DS(DOCS_EVAL, 6 if SMOKE else None), batch_size=1, shuffle=False, collate_fn=collate) if DOCS_EVAL else None
    print(f'train docs {len(tl)} eval docs {len(el) if el else 0}', flush=True)
    best = 1e9
    for epoch in range(1, NUM_EPOCHS + 1):
        model.train(); tot = 0; n = 0; t0 = time.time(); by = {}
        for batch in tl:
            if batch is None: continue
            ids, lf, pids, kind = batch
            try:
                loss = answer_loss(model, ids, lf, pids)
                (loss / ACCUM).backward()
                if (n + 1) % ACCUM == 0:
                    opt.step(); sched.step(); model.zero_grad(set_to_none=True)
            except RuntimeError as e:
                if 'out of memory' in str(e).lower():
                    model.zero_grad(set_to_none=True)
                    (torch.cuda.empty_cache() if DEV.type == 'cuda' else torch.mps.empty_cache()); print(f'  oom-skip {ids.shape[1]//PATCH_SIZE} patches', flush=True); continue
                raise
            tot += loss.item(); n += 1; by.setdefault(kind, []).append(loss.item())
            if n % 50 == 0:
                print(f'  e{epoch} {n}/{len(tl)} loss {tot/n:.4f} {(time.time()-t0)/n:.1f}s/it | ' +
                      ' '.join(f'{k}:{np.mean(v):.3f}' for k, v in by.items()), flush=True)
            if n % 200 == 0:
                fp = health(); print(f'  health: mem free {fp}%', flush=True)
                if fp < 8:
                    torch.save({'model': model.state_dict(), 'epoch': epoch, 'partial': n}, OUT); print('ABORT low memory', flush=True); sys.exit(1)
            if EVAL_EVERY and el and n % EVAL_EVERY == 0:
                model.eval(); s_ = 0; m_ = 0
                with torch.no_grad():
                    for k_, batch_ in enumerate(el):
                        if k_ >= EVAL_N: break
                        if batch_ is None: continue
                        try: s_ += answer_loss(model, batch_[0], batch_[1], batch_[2]).item(); m_ += 1
                        except RuntimeError: continue
                print(f'  EVAL@{n}: {s_/max(m_,1):.4f} on {m_} held-out docs', flush=True); model.train()
            if not SMOKE and n % int(os.environ.get('T2S_SAVE_EVERY', 3000)) == 0:
                torch.save({'model': model.state_dict(), 'epoch': epoch, 'partial': n}, OUT); print(f'  checkpoint at step {n} -> {OUT}', flush=True)
            if SMOKE and n == 1:
                pp = ids[0].reshape(-1, PATCH_SIZE)
                print('SMOKE loss_from', lf, 'of', pp.shape[0], 'patches; target starts:', repr(''.join(pat.patch2chars(list(map(int, p_))) for p_ in pp[lf:lf + 6].tolist()))[:240], flush=True)
            if SMOKE and n >= 8: break
            if int(os.environ.get('T2S_MAX_STEPS', 0)) and n >= int(os.environ.get('T2S_MAX_STEPS', 0)):
                torch.save({'model': model.state_dict(), 'epoch': epoch, 'partial': n}, OUT); print(f'  stopped at step {n} (T2S_MAX_STEPS) -> {OUT}', flush=True); break
        ev = None
        if el:
            model.eval(); s = 0; m = 0
            with torch.no_grad():
                for batch in el:
                    if batch is None: continue
                    ids, lf, pids, kind = batch
                    try:
                        s += answer_loss(model, ids, lf, pids).item(); m += 1
                    except RuntimeError as e:
                        if 'out of memory' in str(e).lower(): torch.mps.empty_cache(); continue
                        raise
            ev = s / max(m, 1)
        print(f'EPOCH {epoch}: train {tot/max(n,1):.4f} eval {ev} ({(time.time()-t0)/60:.1f} min) | ' +
              ' '.join(f'{k}:{np.mean(v):.3f}' for k, v in by.items()), flush=True)
        if not SMOKE and (ev is None or ev < best):
            best = ev if ev is not None else best
            torch.save({'model': model.state_dict(), 'epoch': epoch, 'eval': ev}, OUT); print(f'  saved -> {OUT}', flush=True)
    print('TRAINING DONE', flush=True)
