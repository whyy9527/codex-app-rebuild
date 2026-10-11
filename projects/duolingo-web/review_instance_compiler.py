"""Compile one UI-confirmed result-review question; source instances own ordering."""
import re
import hashlib

def effect_resource(c, url):
    assert url.startswith(('https://d35aaqx5ub95lt.cloudfront.net/sounds/', 'https://simg-ssl.duolingo.com/videos/sound/')) and '?' not in url
    stem = 'en-effect-'+hashlib.sha256(url.encode()).hexdigest()[:20]
    c.resources[stem] = dict(url=url, kind='feedback', name=stem, source_file=stem+'.mp3')
    return stem+'.mp3'

def heading(snapshot, level):
    return re.search(r'heading "([^"\n]+)" \[level='+str(level)+r'\]', snapshot).group(1)

def compile_question(c, effect, raw, row, card, question_id):
    title, _, prompt = card['text'].partition('\n')
    assert row.get('feedback') and not row.get('rejected') and row['identity']['matches']
    q = dict(id=question_id, prompt=row['heading'], sourceType=raw['type'], explanation='',
             correctFeedback=heading(row['feedback'], 2))
    sounds = list(dict.fromkeys(m['src'] for m in row.get('media', []) if m['src'].startswith('https://d35aaqx5ub95lt.cloudfront.net/sounds/')))
    assert len(sounds) <= 1
    if sounds:
        q['correctFeedbackAudioResource'] = effect(sounds[0])
    for src, dst in [('tts', 'audioResource'), ('slowTts', 'slowAudioResource')]:
        if raw.get(src):
            q[dst] = c.resource(raw[src], 'speech')
    if raw.get('character'):
        q['characterResource'] = c.resource(raw['character']['image']['svg'], 'image')
    if raw['type'] == 'listenMatch':
        q.update(kind='matching', pairs=[dict(id=str(p['left_index']), left=str(p['left_index']+1), right=p['translation'],
                    audioResource=c.resource(p['played_audio'][0], 'speech')) for p in row['pair_audio_order']])
        q['rightOrder'] = [next(p['id'] for p in q['pairs'] if p['right'] == text) for text in row['right_text']]
        matched = list(dict.fromkeys(m['src'] for m in row.get('media', []) if m['src'].startswith('https://simg-ssl.duolingo.com/videos/sound/Match_Correct_')))
        if matched:
            assert len(matched) == 4
            q['matchedAudioResources'] = [effect(url) for url in matched]
        answer = ''
        audio = [p['audioResource'] for p in q['pairs']]
    elif raw['type'] == 'assist':
        q.update(kind='choice', hint=raw['prompt'], options=[dict(id=str(j), text=text) for j, text in enumerate(row['identity']['actual']['choices'])])
        q['answer'] = next(o['id'] for o in q['options'] if o['text'] == raw['choices'][raw['correctIndex']])
        answer = raw['choices'][raw['correctIndex']]
        audio = []
    elif raw['type'] in ['translate', 'listenTap']:
        if raw['type'] == 'translate':
            q.update(hint=raw['prompt'], sourceLanguage=raw['sourceLanguage'])
        if row.get('text_input'):
            q.update(kind='text_entry', answer=row['text_input']['value'])
            answer = q['answer']
        else:
            choices = [dict(text=v) if isinstance(v, str) else v for v in raw['choices']]
            chosen = [a['word'] for a in row['actions']]
            assert chosen == [choices[j]['text'] for j in raw['correctIndices']]
            words, ids = c.compile_word_bank(choices, [t.strip() for t in row['word_bank']], chosen)
            q.update(kind='word_tiles', words=words, answer_words=ids)
            # Exact canonical answer, including punctuation, comes from current public data.
            answer = raw.get('correctSolutions', [raw['prompt']])[0]
        audio = [q['audioResource']] if raw['type'] == 'listenTap' else []
    elif raw['type'] == 'listen':
        assert row['text_input']['value'] == raw['prompt']
        q.update(kind='text_entry', answer=raw['prompt'])
        answer = raw['prompt']
        audio = [q['audioResource']]
    elif raw['type'] == 'listenComplete':
        tokens = raw['displayTokens']; blanks = [j for j, t in enumerate(tokens) if t['isBlank']]
        assert len(blanks) == 1
        j = blanks[0]
        q.update(kind='text_entry', answer=row['text_input']['value'],
                 completionPrefix=''.join(t['text'] for t in tokens[:j]),
                 completionSuffix=''.join(t['text'] for t in tokens[j+1:]))
        assert q['answer'] == tokens[j]['text']
        answer = ''.join(t['text'] for t in tokens)
        audio = [q['audioResource']]
    else:
        raise ValueError(raw['type'])
    q['resultReview'] = dict(title=title, prompt=prompt, correctAnswer=answer, audioResources=audio)
    return q
