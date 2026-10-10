"""RAW MUSICXML vs OUR COMPACTION - same models, same questions, one variable.

Brian's objection, and it is the right one: the compaction is a lossy regex of the score. Asking a
model about the music from the compaction is like asking about a novel from a regex of the novel.
The only way to know what the compaction costs us is to hand the same model the raw material.
"""
import sys, json, time, urllib.request, os
import tiktoken

KEY = open('/tmp/.orkey').read().strip()
X = '/Users/bdogellis/Documents/Score Exports/MusicXML/'
C = '/Users/bdogellis/Documents/Score Exports/compact/'
enc = tiktoken.get_encoding('cl100k_base')

Q = """Answer these about the score above. Be specific and concrete; do not hedge.

1. CORE PROGRESSION - the repeating harmonic progression, as roman numerals AND chord names.
2. KEY.
3. WHAT INSTRUMENTS, and the actual pitch range each one plays (lowest and highest note).
4. STRUCTURE - the sections, with bar numbers.
5. THE MELODY - describe it. What does it do?
6. MOOD / TONE - if you had to describe the character of this piece, what is it?
7. WHAT IS IT ABOUT - what do you think the composer is going for?"""

FMT = """Format: one line per part, `PartName: <bar> | <bar> | ...`. Within a bar: `C#4:0.5` is a
note (pitch, then duration in quarter notes), `[D#4 F#4 A#4]:2` a chord, `r:1` a rest, `~` tied
into the next note, `//` separates simultaneous voices, `<p>` `<f>` dynamics."""

MODELS = [('google/gemini-2.5-flash', .30, 2.50, 1048576),
          ('openai/gpt-5-mini', .25, 2.00, 400000),
          ('deepseek/deepseek-chat-v3.1', .55, 1.65, 163840),
          ('x-ai/grok-4.20', 1.25, 2.50, 2000000),
          ('anthropic/claude-sonnet-4.5', 3.00, 15.00, 1000000)]


def ask(model, prompt, mx=1100):
    b = json.dumps({'model': model, 'max_tokens': mx,
                    'messages': [{'role': 'user', 'content': prompt}]}).encode()
    r = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=b,
                               headers={'Authorization': f'Bearer {KEY}',
                                        'Content-Type': 'application/json'})
    d = json.load(urllib.request.urlopen(r, timeout=600))
    u = d.get('usage', {})
    m = d['choices'][0]['message']
    return (m.get('content') or '[EMPTY]', u.get('prompt_tokens', 0), u.get('completion_tokens', 0))


def main():
    stem = sys.argv[1]
    raw = open(X + stem + '.musicxml').read()
    comp = open(C + stem + '.txt').read()
    variants = [('RAW MUSICXML', f'Below is a complete musical score as MusicXML.\n\n{raw}\n\n{Q}'),
                ('OUR COMPACTION', f'Below is a complete musical score in a compact notation.\n{FMT}\n\n{comp}\n\n{Q}')]
    out, total = {}, 0.0
    for vname, prompt in variants:
        n = len(enc.encode(prompt))
        for model, pi, po, ctx in MODELS:
            if n + 1500 > ctx:
                print(f'  SKIP {model} / {vname}: {n:,} tok exceeds ctx'); continue
            try:
                txt, ti, to = ask(model, prompt)
            except Exception as e:
                print(f'  ERR  {model} / {vname}: {str(e)[:110]}'); continue
            cost = ti * pi / 1e6 + to * po / 1e6
            total += cost
            out[(model, vname)] = {'text': txt, 'in': ti, 'out': to, 'cost': round(cost, 4)}
            print(f'  ok   {model:<30} {vname:<15} {ti:>8,} in  ${cost:.4f}')
    json.dump({f'{k[0]}||{k[1]}': v for k, v in out.items()},
              open(f'h2h_{stem[:24].replace(" ","_")}.json', 'w'), indent=1)
    print(f'\nTOTAL SPEND: ${total:.4f}   -> h2h_{stem[:24].replace(" ","_")}.json')


if __name__ == '__main__':
    main()
