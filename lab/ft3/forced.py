"""Forced-address decoding for the edit model.

The model kept writing plausible music into the wrong bar or the wrong voice. But the skeleton
of the answer is known before generation: which bars, which voices, in what order. So force it:
at each answer line start the characters `[b:N][V:k]` are dictated, after each closing barline
the next `[V:j]` (or the newline) is dictated, and the model writes only what is between. Same
character-mask machinery as the voice mask in t2s_constrained.py.

template = [(bar_index, [voice, voice, ...]), ...]   one entry per answer line
"""
import re, time
import numpy as np, torch
from samplings import top_p_sampling, top_k_sampling, temperature_sampling


STEP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
NOTE_TAIL = re.compile(r"(?:__|_|\^\^|\^|=)?([A-Ga-g])([,']*)$")


def register_block(text_so_far, lo, hi):
    """Chars that must NOT come next if a note is being spelled: ',' when another octave down
    would leave [lo, hi], "'" when another octave up would. Written pitch, so lo/hi are the
    instrument's sounding range shifted by its transposition."""
    m = NOTE_TAIL.search(text_so_far[-12:])
    if not m:
        return set()
    ltr, marks = m.group(1), m.group(2)
    midi = STEP[ltr.upper()] + (60 if ltr.isupper() else 72) + 12 * (marks.count("'") - marks.count(','))
    out = set()
    if midi - 12 < lo:
        out.add(',')
    if midi + 12 > hi:
        out.add("'")
    return out


class Forcer:
    def __init__(self, template, line_tags=None, voice_first=False):
        self.lines = [(b, list(vs)) for b, vs in template]
        self.line_tags = line_tags or [''] * len(self.lines)
        self.voice_first = voice_first
        self.li = 0          # current answer line
        self.vi = 0          # next voice index within the line
        self.pending = ''    # characters that MUST come next
        self.in_bar = False  # inside a voice's bar text (free generation)
        self.voice = None
        self._start_line()

    def _start_line(self):
        if self.li >= len(self.lines):
            self.pending = ''; return
        b, vs = self.lines[self.li]
        self.vi = 0
        self.pending = self.line_tags[self.li] + (f'[V:{vs[0]}][b:{b}]' if self.voice_first else f'[b:{b}][V:{vs[0]}]')
        self.voice = vs[0]
        self.in_bar = False

    def done(self):
        return self.li >= len(self.lines) and not self.pending

    def allowed(self):
        """set of allowed next chars, or None for free generation."""
        if self.pending:
            return {self.pending[0]}
        return None

    def consume(self, ch):
        if self.pending:
            if ch == self.pending[0]:
                self.pending = self.pending[1:]
                if not self.pending:
                    self.in_bar = True
            return
        if self.in_bar and ch == '|':
            self.in_bar = False
            b, vs = self.lines[self.li]
            self.vi += 1
            if self.vi < len(vs):
                self.pending = f'[V:{vs[self.vi]}]'
                self.voice = vs[self.vi]
            else:
                self.pending = '\n'
                self.li += 1
                self._after_newline = True
        elif not self.in_bar and ch == '\n':
            pass

    def consume_forced_newline(self):
        pass


def _consume(forcer, ch):
    """consume with the line-advance bookkeeping: the '\n' that ends a line is itself forced."""
    if forcer.pending == '\n' and ch == '\n':
        forcer.pending = ''
        forcer._start_line()
        return
    forcer.consume(ch)


@torch.no_grad()
def write_forced(model, pat, plan_ids, prefix, template, temperature=0.7, top_k=9, top_p=0.9, max_secs=600, dev=None, voice_ranges=None, line_tags=None, voice_first=False):
    from utils import safe_normalize_probs
    PATCH_SIZE = 16
    dev = dev or next(model.parameters()).device
    ip = pat.encode_generate(prefix)
    ip = torch.tensor([[x for sub in ip for x in sub]], device=dev).reshape(1, -1)
    forcer = Forcer(template, line_tags=line_tags, voice_first=voice_first)
    gen, t0 = '', time.time()
    while not forcer.done():
        # one patch: char loop with the mask
        patches = ip
        if patches.shape[-1] % PATCH_SIZE != 0:
            tokens = patches[:, -(patches.shape[-1] % PATCH_SIZE):].squeeze(0)
            tokens = torch.cat((torch.tensor([model.bos_token_id], device=dev), tokens), dim=-1)
            patches = patches[:, :-(patches.shape[-1] % PATCH_SIZE)]
        else:
            tokens = torch.tensor([model.bos_token_id], device=dev)
        patches = patches.reshape(1, -1, PATCH_SIZE)
        enc = model.patch_level_model(plan_ids.unsqueeze(0), patches)['last_hidden_state']
        out = []
        while True:
            prob = model.char_level_decoder.generate(enc[0][-1], tokens).cpu().detach().numpy()
            prob = safe_normalize_probs(prob)
            ok = forcer.allowed()
            if ok is not None:
                mask = np.zeros_like(prob)
                for c in ok:
                    mask[ord(c)] = 1
                prob = safe_normalize_probs(mask)            # dictated: no sampling at all
            else:
                prob[0:3] = 0                                # never end mid-answer
                if forcer.in_bar and re.search(r'\[V:\d+\]$', gen):
                    prob[ord('[')] = 0                       # no second voice tag right after a dictated one
                if forcer.in_bar and voice_ranges and forcer.voice in voice_ranges:
                    lo, hi = voice_ranges[forcer.voice]
                    for c in register_block(gen, lo, hi):
                        prob[ord(c)] = 0                     # cannot leave the instrument's range
                prob[ord('\n')] = 0 if forcer.in_bar else prob[ord('\n')]
                prob = safe_normalize_probs(top_k_sampling(safe_normalize_probs(prob), top_k=top_k, return_probs=True))
                prob = safe_normalize_probs(top_p_sampling(prob, top_p=top_p, return_probs=True))
            tok = int(temperature_sampling(prob, temperature=temperature)) if ok is None else int(np.argmax(prob))
            out.append(tok)
            if tok >= 3:
                gen += chr(tok); _consume(forcer, chr(tok))
            if len(tokens) >= PATCH_SIZE or forcer.done():
                break
            tokens = torch.cat((tokens, torch.tensor([tok], device=dev)), dim=0)
        # pad the patch like the reference loop and append
        end = False
        for j in range(len(out)):
            if end: out[j] = pat.special_token_id
            if out[j] == pat.eos_token_id: end = True
        ip = torch.cat([ip, torch.tensor([out], device=dev)], dim=1)
        if time.time() - t0 > max_secs or len(gen) > 30000 or ip.shape[1] >= 2048 * PATCH_SIZE:
            break
    return gen


def template_from_truth(truth_lines):
    """[(bar, [voices])] from ground-truth answer lines (benchmark use)."""
    out = []
    for l in truth_lines:
        mb = re.search(r'\[b:(\d+)\]', l)
        vs = [int(v) for v in re.findall(r'\[V:(\d+)\]', l)]
        if mb and vs:
            out.append((int(mb.group(1)), vs))
    return out


def voice_ranges_from_header(header_lines):
    """{voice: (lo, hi)} in WRITTEN pitch from the V: lines (nm=... transpose=...), via ranges.py."""
    import sys, os
    sys.path.insert(0, '/Users/bdogellis/repos/scorewright')
    import ranges
    out = {}
    for l in header_lines:
        m = re.match(r'^V:(\d+)\b(.*)$', l)
        if not m:
            continue
        v, rest = int(m.group(1)), m.group(2)
        nm = re.search(r'nm="([^"]*)"', rest)
        tr = re.search(r'transpose=(-?\d+)', rest)
        r = ranges.range_of(nm.group(1)) if nm else None
        if r is None and not nm:
            prev = out.get(v - 1)
            r = prev
        if r:
            t = int(tr.group(1)) if tr else 0
            out[v] = (r[0] - t, r[1] - t)
    return out
