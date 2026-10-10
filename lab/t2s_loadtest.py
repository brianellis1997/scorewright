"""Load Text2Score on MPS and generate a few patches from a toy plan. Smoke test only."""
import os, sys, time, warnings, torch
warnings.filterwarnings('ignore')
T2S = '/Users/bdogellis/Documents/Score Exports/_models/_text2score'
os.chdir(T2S)
sys.path.insert(0, f'{T2S}/text2music/inference'); sys.path.insert(0, T2S)
t0 = time.time()
from utils import *
from config import *
from transformers import GPT2Config
pc = GPT2Config(num_hidden_layers=PATCH_NUM_LAYERS, max_length=PATCH_LENGTH, max_position_embeddings=PATCH_LENGTH,
                n_embd=HIDDEN_SIZE, num_attention_heads=HIDDEN_SIZE // 64, vocab_size=1)
bc = GPT2Config(num_hidden_layers=CHAR_NUM_LAYERS, max_length=PATCH_SIZE + 1, max_position_embeddings=PATCH_SIZE + 1,
                hidden_size=HIDDEN_SIZE, num_attention_heads=HIDDEN_SIZE // 64, vocab_size=128)
m = CustomLMHeadModel(encoder_config=pc, decoder_config=bc)
print('built %.0fs' % (time.time() - t0), flush=True)
ck = torch.load(INFERENCE_WEIGHTS_PATH, map_location='cpu', weights_only=False)
missing, unexpected = m.load_state_dict(ck['model'], strict=False)
print('missing', len(missing), missing[:5]); print('unexpected', len(unexpected), unexpected[:5])
print('epoch', ck.get('epoch'), 'best', ck.get('best_epoch'), 'min_eval_loss', ck.get('min_eval_loss'), flush=True)
del ck
dev = torch.device('mps'); m.to(dev).eval()
print('on mps %.0fs' % (time.time() - t0), flush=True)
pat = Patchilizer()
plan = pat.encode_plan("Total Measures: 4\n\nInstruments: Piano\n\nMeasure: 1\n  Instruments: Piano\n  Pitch Range: 48–72\n  Note Density: Moderate\n  Tempo: 100 BPM\n  Time Signature: 4/4\n  Key Signature: 0\n  Chords: [0, 4, 7]\n").to(dev)
bos = [[pat.bos_token_id] * (PATCH_SIZE - 1) + [pat.eos_token_id]]
ip = torch.tensor(bos, device=dev).reshape(1, -1)
t1 = time.time(); out = ''
with torch.no_grad():
    for _ in range(12):
        p = m.generate(plan.unsqueeze(0), ip.unsqueeze(0), top_k=9, top_p=0.9, temperature=1.0)
        out += pat.decode([p])
        end = False
        for j in range(len(p)):
            if end:
                p[j] = 0
            if p[j] == 2:
                end = True
        ip = torch.cat([ip, torch.tensor([p], device=dev)], dim=1)
print('LOAD_OK total %.0fs, 12 patches in %.1fs' % (time.time() - t0, time.time() - t1))
print(repr(out[:300]))
