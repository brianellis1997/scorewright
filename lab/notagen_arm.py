"""NotaGen as a continuation engine, on Apple silicon.

The shipped inference.py is cuda-or-cpu and generates whole pieces from a metadata prompt. What
this project needs instead is: given the ABC of bars 1..K of one of Brian's scores, what comes
next? That is a prefix continuation, which the model supports natively - it is a decoder LM - it
just is not what the reference script exposes.
"""
import os, sys, re, torch
NG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NotaGen', 'inference')
sys.path.insert(0, NG)

PATCH_SIZE, PATCH_LENGTH = 16, 1024
MODELS = '/Users/bdogellis/Documents/Score Exports/_models/'
BIG = MODELS + 'weights_notagenx_p_size_16_p_length_1024_p_layers_20_h_size_1280.pth'

DEV = torch.device('mps') if torch.backends.mps.is_available() else torch.device('cpu')


def load(path=BIG, layers=20, hidden=1280, char_layers=6, patch_length=None):
    # patch_length must match the CHECKPOINT's position table (NotaGen-X: 1024; the small
    # pretrain and Brian's fine-tune: 2048), and it must be set module-wide BEFORE the sliding
    # window math ever runs.
    global PATCH_LENGTH
    if patch_length:
        PATCH_LENGTH = patch_length
    from transformers import GPT2Config
    import utils as U
    pc = GPT2Config(num_hidden_layers=layers, max_length=PATCH_LENGTH,
                    max_position_embeddings=PATCH_LENGTH, n_embd=hidden,
                    num_attention_heads=hidden // 64, vocab_size=1)
    bc = GPT2Config(num_hidden_layers=char_layers, max_length=PATCH_SIZE + 1,
                    max_position_embeddings=PATCH_SIZE + 1, hidden_size=hidden,
                    num_attention_heads=hidden // 64, vocab_size=128)
    m = U.NotaGenLMHeadModel(encoder_config=pc, decoder_config=bc)
    ck = torch.load(path, map_location='cpu')
    m.load_state_dict(ck['model'])
    m.to(DEV).eval()
    return m, U.Patchilizer()


@torch.no_grad()
def continue_abc(model, pat, prefix, max_chars=900, n_bars=None, top_k=9, top_p=0.9,
                 temperature=1.0, keep_frac=3, verbose=False):
    """Feed an ABC prefix, return the characters the model writes next.

    THE SLIDING WINDOW MUST CUT ON A BAR BOUNDARY. A 24-staff score fills the 1024-patch context in
    about 16 bars, so without re-encoding the model writes two bars and stops. But re-encoding in
    the middle of a bar orphans it: the first version produced bar 19 with 2.0 quarters and zero
    notes across all 24 parts, then a damaged bar 20, and the whole continuation had to be truncated
    back to bar 18. Interleaved ABC puts exactly one bar per line, so a bar boundary IS a newline -
    drop any trailing partial line from BOTH the output and the re-encode context and let the model
    write that bar again from clean state.
    """
    ip = pat.encode_generate(prefix)
    ip = torch.tensor([[x for sub in ip for x in sub]], device=DEV).reshape(1, -1)
    gen = ''
    while True:
        if n_bars is not None and gen.count('\n') >= n_bars:
            break
        if n_bars is None and len(gen) >= max_chars:
            break
        if len(gen) > 200_000:
            break
        p = model.generate(ip.unsqueeze(0), top_k=top_k, top_p=top_p, temperature=temperature)
        if p[0] == pat.bos_token_id and p[1] == pat.eos_token_id:
            break
        gen += pat.decode([p])
        end = False
        for j in range(len(p)):
            if end:
                p[j] = pat.special_token_id
            if p[j] == pat.eos_token_id:
                end = True
        ip = torch.cat([ip, torch.tensor([p], device=DEV)], dim=1)
        if ip.shape[1] >= PATCH_LENGTH * PATCH_SIZE:
            full = prefix + gen
            cut = full.rfind('\n')
            if cut < len(prefix):
                break                      # not even one complete new bar; nothing safe to keep
            full = full[:cut + 1]
            gen = full[len(prefix):]       # every bar in `gen` is now complete
            body = full.split('\n')
            k = next((i for i, l in enumerate(body)
                      if l.startswith('[V:') or l.startswith('[r:')), None)
            if k is None:
                break
            meta, bars = body[:k], [l for l in body[k:] if l.strip()]
            ip = pat.encode_generate('\n'.join(meta + bars[-max(2, len(bars) // keep_frac):]) + '\n')
            ip = torch.tensor([[x for sub in ip for x in sub]], device=DEV).reshape(1, -1)
            if verbose:
                print(f'    [window slid, {gen.count(chr(10))} complete bars so far]', flush=True)
    # never hand back a partial bar
    cut = gen.rfind('\n')
    return gen[:cut + 1] if cut >= 0 else gen


# ---- ABC note parsing, for scoring against ground truth -------------------------------------
STEP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
NOTE_RE = re.compile(r"(__|_|\^\^|\^|=)?([A-Ga-g])([,']*)")


def abc_pitches(text):
    """Every note in a chunk of ABC as a midi number, in order. Strips !markings! and \"text\"
    first: `!open!` contains a lowercase e that otherwise reads as a note, and `\"^accel.\"`
    contains three."""
    t = re.sub(r'![^!\n]*!', '', text)
    t = re.sub(r'"[^"\n]*"', '', t)
    t = re.sub(r'\[[A-Zr]:[^\]\n]*\]', '', t)          # [V:1], [r:0/1], [Q:1/4=120]
    out = []
    for m in NOTE_RE.finditer(t):
        acc, ltr, oct_ = m.group(1), m.group(2), m.group(3)
        v = STEP[ltr.upper()] + (60 if ltr.isupper() else 72)
        v += {'__': -2, '_': -1, '^': 1, '^^': 2, '=': 0, None: 0}[acc]
        v += 12 * (oct_.count("'") - oct_.count(','))
        out.append(v)
    return out


if __name__ == '__main__':
    m, p = load()
    print('loaded on', DEV, sum(x.numel() for x in m.parameters()) / 1e6, 'M params')
