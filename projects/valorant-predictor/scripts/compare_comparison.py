"""Independently enumerate BO5 paths; compare actual rendered table probabilities."""
import argparse
import itertools
import json
from pathlib import Path


def compare(observed, project):
    rows = []
    def check(name, actual, expected):
        rows.append({'id': name, 'status': 'pass' if actual == expected else 'fail', 'actual': actual, 'expected': expected})
    source, candidate = observed.get('reference', {}), observed.get('candidate', {})
    for heading in ['夺冠概率对比', '实力排序对比', '分歧榜 · 模型意见最不一致的对阵']:
        check('source-' + heading, heading in source.get('headings', []), True)
        check('candidate-' + heading, heading in candidate.get('headings', []), True)
    def bo5(p):
        total = 0
        # Every five-map binary outcome has exactly one stopped-series winner.
        for maps in itertools.product([0, 1], repeat=5):
            if sum(maps) < 3:
                total += p ** (5 - sum(maps)) * (1 - p) ** sum(maps)
        return total
    event = json.loads((project / 'data/event.json').read_text())
    models = {'codex': json.loads((project / 'data/gpt-6.1-sol-forecast.json').read_text()), 'deepseek': json.loads((project / 'data/deepseek-forecast.json').read_text())}
    def probability(a, b, model):
        if model == 'baseline':
            def strength(team):
                scores = [m['score'][::1 if m['teams'][0] == team else -1] for m in event['history'] if team in m['teams']]
                return (1 + sum(s[0] for s in scores)) / (1 + sum(s[1] for s in scores))
            return strength(a) / (strength(a) + strength(b))
        pair = next(p for p in models[model]['pairs'] if set(p['teams']) == {a, b})
        return pair['p_first'] if pair['teams'][0] == a else 1 - pair['p_first']
    check('four-qualifier-scenarios', len(candidate.get('cases', [])), 4)
    for case in candidate.get('cases', []):
        upper, lower = case['upper'], case['lower']
        loser = next(t for t in event['predecessors'][0]['teams'] if t != upper)
        for row in case['rows']:
            check(f'{upper}-{lower}-{row["team"]}-six-pending-models', [row['values'][c] for c in [0, 2, 4, 5, 6, 7]], [{'text': '待预测', 'value': None}] * 6)
        for model, column in [('codex', 1), ('deepseek', 3), ('baseline', 8)]:
            q = bo5(probability(loser, lower, model))
            ua, ub = bo5(probability(upper, loser, model)), bo5(probability(upper, lower, model))
            expected = {upper: q * ua + (1-q) * ub, loser: q * (1-ua), lower: (1-q) * (1-ub)}
            total = 0
            for row in case['rows']:
                actual = float(row['values'][column]['value']);total += actual
                check(f'{upper}-{lower}-{model}-{row["team"]}', abs(actual - expected.get(row['team'], 0)) < 1e-12, True)
            check(f'{upper}-{lower}-{model}-sum', abs(total - 1) < 1e-12, True)
    check('two-models-and-baseline-six-pair-dots', len(candidate.get('dots', [])), 18)
    for model, payload in models.items():
        check(model + '-real-reason', payload['pairs'][0]['reason'] in candidate.get(model, {}).get('reasons', ''), True)
    check('independent-model-distributions', candidate.get('codex', {}).get('distribution') != candidate.get('deepseek', {}).get('distribution'), True)
    for name, facts in [('source', source), ('candidate', candidate)]:
        motion = facts.get('motion', {});samples = motion.get('samples', [])
        check(name + '-animation-duration', motion.get('timing', {}).get('duration'), '0.45s')
        check(name + '-animation-easing', motion.get('timing', {}).get('easing'), 'ease-out')
        check(name + '-actual-fade', bool(samples and min(s['opacity'] for s in samples) < 1 and samples[-1]['opacity'] == 1), True)
        check(name + '-actual-translation', bool(samples and any(s['transform'] != 'none' for s in samples) and samples[-1]['transform'] == 'none'), True)
    width = candidate.get('mobile_width', {})
    check('mobile-no-page-overflow', width.get('scroll') == width.get('viewport') == 320, True)
    check('driver-errors', [observed.get('error'), *observed.get('errors', [])], [None])
    return {'status': 'pass' if all(r['status'] == 'pass' for r in rows) else 'fail', 'rows': rows, 'scope': 'Original comparison concepts and real sampled fade; four conditional VALORANT scenarios. Missing models remain pending.'}


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--observed',required=True);p.add_argument('--out',required=True);a=p.parse_args();root=Path(__file__).resolve().parents[3]
    result=compare(json.loads((root/a.observed).read_text()),Path(__file__).resolve().parents[1]);out=root/a.out;out.mkdir(parents=True,exist_ok=False);(out/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'passed':sum(r['status']=='pass'for r in result['rows']),'total':len(result['rows'])}));raise SystemExit(0 if result['status']=='pass'else 1)
