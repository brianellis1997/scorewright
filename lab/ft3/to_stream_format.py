"""docs2 -> docs3: put the voice tag first on every body line ([V:k][b:i]... instead of [b:i][V:k]...)
so the patchilizer treats the lines as tunebody: bar-level patches and, in training, its own
[r:idx/remaining] countdown on every line, exactly as in pretraining. Tags swap in place, so
answer_start does not move.
usage: python ft3/to_stream_format.py <in.jsonl> <out.jsonl> [max_docs]"""
import re, sys, json
SWAP = re.compile(r'^\[b:(\d+)\](\[V:\d+\])')
def convert(text):
    return '\n'.join(SWAP.sub(r'\2[b:\1]', l) for l in text.split('\n'))
if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    lim = int(sys.argv[3]) if len(sys.argv) > 3 else None
    n = 0
    with open(dst, 'w') as w:
        for l in open(src):
            d = json.loads(l)
            t = convert(d['text'])
            assert len(t) == len(d['text'])
            d['text'] = t
            w.write(json.dumps(d) + '\n'); n += 1
            if lim and n >= lim: break
    print('STREAM_FORMAT_DONE', n, dst)
