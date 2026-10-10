"""BLIND TEST: give a model only the notes and see if it beats the hand-written analysis.

The thesis under test is Brian's: a transformer reading the score directly will understand it
better than a Python script computing statistics about it. Krumhansl-Schmuckler is literally
bag-of-words for music - throw away order, count pitch classes, correlate against a reference
distribution - so this is the music equivalent of asking whether an LLM beats tf-idf.

RULES: the model gets the compact encoding and NOTHING else. No filename (the titles state the
key), no detected key, no roman numerals, no hints. Ground truth comes from Brian, not from me.
"""
import os, sys, json, time, urllib.request

KEY = open('/tmp/.orkey').read().strip()
CD = '/Users/bdogellis/Documents/Score Exports/compact/'

MODELS = [
    ('openai/gpt-5-mini',            0.25,  2.00),
    ('deepseek/deepseek-chat-v3.1',  0.55,  1.65),
    ('x-ai/grok-4.20',               1.25,  2.50),
    ('anthropic/claude-sonnet-4.5',  3.00, 15.00),
]

PROMPT = """Below is a complete musical score in a compact notation.

Format: one line per instrumental part, `PartName: <bar> | <bar> | ...`. Within a bar, events are
space separated. `C#4:0.5` is a note (pitch, then duration in quarter notes). `[D#4 F#4 A#4]:2` is
a chord. `r:1` is a rest. `~` means tied into the next note. `//` separates simultaneous voices in
one part. `<p>` `<f>` are dynamics.

{score}

Answer concisely:
1. KEY. Give one answer, spelled the way the composer most likely notated it.
2. HARMONIC PROGRESSION. Give the repeating chord progression as roman numerals AND as chord names.
3. FORM. Where are the sections and what happens?
4. Anything else musically notable.

Be direct. If you are unsure, say so rather than hedging everything."""


def ask(model, prompt, max_tokens=2500):
    body = json.dumps({'model': model, 'max_tokens': max_tokens,
                       'messages': [{'role': 'user', 'content': prompt}]}).encode()
    r = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=body,
                               headers={'Authorization': f'Bearer {KEY}',
                                        'Content-Type': 'application/json'})
    t0 = time.time()
    d = json.load(urllib.request.urlopen(r, timeout=300))
    u = d.get('usage', {})
    msg = d['choices'][0]['message']
    # reasoning models can spend the whole budget thinking and return empty content
    c = msg.get('content') or msg.get('reasoning') or '[EMPTY - budget spent on reasoning]'
    return (c, u.get('prompt_tokens', 0),
            u.get('completion_tokens', 0), time.time() - t0)


def main():
    stem = sys.argv[1]
    score = open(CD + stem + '.txt').read()
    prompt = PROMPT.format(score=score)
    total = 0.0
    for m, pin, pout in MODELS:
        try:
            txt, ti, to, secs = ask(m, prompt)
        except Exception as e:
            print(f'\n### {m}\n  ERROR: {str(e)[:160]}')
            continue
        cost = ti * pin / 1e6 + to * pout / 1e6
        total += cost
        print(f'\n{"="*74}\n### {m}   {ti:,} in / {to:,} out   ${cost:.4f}   {secs:.0f}s\n{"="*74}')
        print(txt.strip())
    print(f'\n\nTOTAL SPEND THIS RUN: ${total:.4f}')


if __name__ == '__main__':
    main()
