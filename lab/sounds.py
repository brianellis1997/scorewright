"""Give every part of a MusicXML file its standard sound (<instrument-sound>, MusicXML sounds.xml IDs),
so MuseScore plays the right instrument. Dorico's export has no sound and no MIDI program, and
MuseScore 4 guesses from the part name: on Nov 13 2026 it made 15 of 111326's 32 parts a grand piano
(cor anglais, clarinets, horns, Wagner tuba, trumpets, harps, violins, double bass, and more).
Only parts without a sound get one; a part whose name is not in NAMES keeps what it has.
A "pizz." or "arco" text also gets a <sound pizzicato> switch, which MuseScore plays (as text alone
it stays arco).
usage: python sounds.py <in.musicxml> <out.musicxml>    from code: with_techniques(with_sounds(xml)) -> xml"""
import re, sys

NAMES = [  # (words in the part name, lower case, all must appear) -> sound ID
    (('piccolo',), 'wind.flutes.flute.piccolo'), (('alto', 'flute'), 'wind.flutes.flute.alto'), (('flute',), 'wind.flutes.flute'),
    (('cor', 'anglais'), 'wind.reed.english-horn'), (('english', 'horn'), 'wind.reed.english-horn'), (('oboe',), 'wind.reed.oboe'),
    (('clarinet', 'e flat'), 'wind.reed.clarinet.eflat'), (('clarinet', 'bass'), 'wind.reed.clarinet.bass'),
    (('clarinet', 'a)'), 'wind.reed.clarinet.a'), (('clarinet',), 'wind.reed.clarinet.bflat'),
    (('contrabassoon',), 'wind.reed.contrabassoon'), (('bassoon',), 'wind.reed.bassoon'),
    (('alto', 'sax'), 'wind.reed.saxophone.alto'), (('tenor', 'sax'), 'wind.reed.saxophone.tenor'),
    (('baritone', 'sax'), 'wind.reed.saxophone.baritone'), (('soprano', 'sax'), 'wind.reed.saxophone.soprano'),
    (('wagner', 'tuba'), 'brass.wagner-tuba'), (('horn',), 'brass.french-horn'), (('trumpet',), 'brass.trumpet.bflat'),
    (('bass', 'trombone'), 'brass.trombone.bass'), (('trombone',), 'brass.trombone'), (('tuba',), 'brass.tuba'),
    (('euphonium',), 'brass.euphonium'), (('timpani',), 'drum.timpani'), (('side', 'drum'), 'drum.snare-drum'),
    (('snare',), 'drum.snare-drum'), (('bass', 'drum'), 'drum.bass-drum'), (('cymbal',), 'metal.cymbal.crash'),
    (('tubular', 'bells'), 'metal.bells.tubular-bells'), (('glockenspiel',), 'pitched-percussion.glockenspiel'),
    (('xylophone',), 'pitched-percussion.xylophone'), (('vibraphone',), 'pitched-percussion.vibraphone'),
    (('marimba',), 'pitched-percussion.marimba'), (('celesta',), 'keyboard.celesta'), (('piano',), 'keyboard.piano'),
    (('harp',), 'pluck.harp'), (('violin',), 'strings.violin'), (('viola',), 'strings.viola'),
    (('violoncello',), 'strings.cello'), (('cello',), 'strings.cello'), (('double', 'bass'), 'strings.contrabass'),
    (('contrabass',), 'strings.contrabass'),
]


def sound_for(name):
    n = name.lower()
    return next((s for words, s in NAMES if all(w in n for w in words)), None)


def with_techniques(xml):
    """a pizz. or arco text becomes a pizzicato switch for MuseScore's playback (<sound pizzicato>)"""
    def one(m):
        d = m.group(0)
        if '<sound' in d:
            return d
        w = re.search(r'<words[^>]*>([^<]*)</words>', d)
        word = w.group(1).strip().lower() if w else ''
        flag = 'yes' if word.startswith('pizz') else 'no' if word.startswith('arco') else None
        return d.replace('</direction>', f'<sound pizzicato="{flag}"/></direction>') if flag else d
    return re.sub(r'<direction[ >].*?</direction>', one, xml, flags=re.S)


def with_sounds(xml):
    def one(m):
        pid, body = m.group(1), m.group(2)
        if '<instrument-sound>' in body:
            return m.group(0)
        name = re.search(r'<part-name>([^<]*)</part-name>', body)
        sound = sound_for(name.group(1)) if name else None
        if not sound:
            return m.group(0)
        if '<score-instrument' in body:
            body = re.sub(r'(<score-instrument [^>]*>.*?)(</score-instrument>)', rf'\1<instrument-sound>{sound}</instrument-sound>\2', body, count=1, flags=re.S)
        else:
            body = body + f'<score-instrument id="{pid}-I1"><instrument-name>{name.group(1)}</instrument-name><instrument-sound>{sound}</instrument-sound></score-instrument>'
        return f'<score-part id="{pid}">{body}</score-part>'
    return re.sub(r'<score-part id="([^"]+)">(.*?)</score-part>', one, xml, flags=re.S)


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(with_techniques(with_sounds(open(sys.argv[1], encoding='utf-8').read())))
