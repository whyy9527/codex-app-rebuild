"""Compile the actually accepted current walk and its observed 17-card review.

An explicit instance fixture, never an adaptive selection algorithm or a change
to the default main/practice courses. All answers are tied to source feedback.
"""
import importlib.util
import hashlib
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
OLD = BASE / 'evidence/english-isolation-presentation-v1/source-probe'
EV = BASE / 'evidence/english-current-walk-v1/source'
spec = importlib.util.spec_from_file_location('english', BASE / 'compile-english-course.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def read(path):
    return json.loads(path.read_text())


def heading(snapshot, level):
    return re.search(r'heading "([^"\n]+)" \[level='+str(level)+r'\]', snapshot).group(1)


def effect(url):
    assert url.startswith(('https://d35aaqx5ub95lt.cloudfront.net/sounds/', 'https://simg-ssl.duolingo.com/videos/sound/')) and '?' not in url
    stem = 'en-effect-'+hashlib.sha256(url.encode()).hexdigest()[:20]
    c.resources[stem] = dict(url=url, kind='feedback', name=stem, source_file=stem+'.mp3')
    return stem+'.mp3'


records = []
for i in range(14):
    data = read(OLD/f'replay-{i}.json')
    records.append((data['session']['challenges'][0]['content'], data['observed'][0]))
tail = read(EV/'challenges.json')
records += [(record['content'], row) for record, row in zip(tail['session']['challenges'], tail['observed'])]
cards = [r for r in read(EV/'review-open-roles.json')['visible'] if r['tag'] == 'DIV' and r['role'] == 'button']
assert len(records) == len(cards) == 17
questions, speeches = [], []
for i, ((raw, row), card) in enumerate(zip(records, cards)):
    title, _, prompt = card['text'].partition('\n')
    if raw['type'] in ('translate', 'speak'):
        assert prompt == raw['prompt']
    elif raw['type'] == 'assist':
        assert raw['prompt'] in title
    elif raw['type'] in ('listenMatch', 'listenTap'):
        assert title == '选择你听到的内容：'
    elif raw['type'] == 'listenComplete':
        assert title == '输入所缺单词'
    if raw['type'] == 'speak':
        assert raw['prompt'] == 'Hot, please.' and not row.get('feedback')
        speeches.append(dict(id='current-review-speech', beforeQuestionID=f'current-review-q{i+1}',
            title=row['heading'], phrase=raw['prompt'], audioResource=c.resource(raw['tts'], 'speech'),
            declineLabel='现在不做口语题', closedTitle='麦克风已关闭', closedBody='将在 15 分钟后恢复',
            resultReview=dict(title=title, prompt=prompt, correctAnswer=raw['prompt'],
                              declinedAnswer=raw['prompt'], audioResources=[])))
        continue
    assert row.get('feedback') and not row.get('rejected') and row['identity']['matches']
    q = dict(id=f'current-review-q{i}', prompt=row['heading'], sourceType=raw['type'], explanation='',
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
    questions.append(q)
assert len(questions) == 16 and len(speeches) == 1
lesson = dict(id='current-review-practice', title='英语练习', questions=questions, deferredSpeech=speeches,
              interludes=[dict(id='current-review-intro', afterQuestionID='current-review-q13', text='哎哟不错哦！要不要玩点刺激的？')],
              settlement=[dict(id='current-review-result', kind='result', title='完美！', body='你练习全对，无错完成本单元',
                               continueLabel='继续', secondaryLabel='回顾本单元', retryLabel='重新练习')])
fixture = dict(provenance=dict(source='Actually accepted current-instance walk and observed 17-card review',
               evidence=[str(OLD.relative_to(BASE.parents[1])), str(EV.relative_to(BASE.parents[1]))],
               unknown='Wrong-answer review deduplication, adaptive retry selection, reward/XP and normal speech grading'),
               data=dict(candidate_course=dict(id='duolingo-current-review-instance', title='英语练习', speechLanguage='en',
                         interfaceLanguage='zh', mistakeHeartCost=0, lessons=[lesson])))
# Actual public source identities read from the review DOM, not replacements.
for name, asset in [('check', 'bed2a542bc7eddc78e75fbe85260b89e'), ('close', 'ed25a8cf69261b0c1e25b147f369f74a')]:
    stem = 'en-result-review-'+name
    c.resources[stem] = dict(name=stem, source_file=stem+'.svg', kind='home',
                            url='https://d35aaqx5ub95lt.cloudfront.net/images/'+asset+'.svg')
for path, value in [(BASE/'fixture-reference-en-zh-current-review-v1.json', fixture),
                    (BASE/'reference-assets-en-zh-current-review-v1.json', list(c.resources.values()))]:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(dict(graded_questions=len(questions), review_cards=len(cards), resources=len(c.resources))))
