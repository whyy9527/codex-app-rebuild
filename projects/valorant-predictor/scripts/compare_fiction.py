"""Compare recorded UI facts to the frozen model artifacts and user C8 scope."""
import argparse
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def compare(observed):
    rows = []
    def check(name, actual, expected):rows.append({'id':name, 'knowledge_source':'decision:user-C8-and-validated-model-output', 'actual':actual, 'expected':expected, 'status':'pass' if actual == expected else 'fail'})
    check('no-runtime-errors', observed.get('errors'), [])
    check('driver-completed', observed.get('error'), None)
    manifest = json.loads((ROOT / 'data/model-fiction.json').read_text())
    check('all-conditional-reviews', len(observed['cases']), 8 * len(manifest))
    for channel, filename in manifest.items():
        dataset = json.loads((ROOT / 'data' / filename).read_text())
        for key, row in dataset['cases'].items():
            actual = observed['cases'].get(channel + ':' + key, {})
            prefix = channel + ':' + key + ':'
            check(prefix + 'headline', actual.get('headline'), row['headline'])
            check(prefix + 'clear-fiction-label', '非真实比赛、非选手能力评估' in actual.get('notice', ''), True)
            check(prefix + 'seven-distinct-bp-maps', actual.get('bp'), row['bp']['bans'] + row['bp']['order'])
            check(prefix + 'unplayed-maps', actual.get('unplayed'), 5 - len(row['maps']))
            ratings = {r['id']:{'rating':r['rating'], 'comment':r['comment']} for r in actual.get('ratings', [])}
            expected = {key:{'rating':f"{item['rating']:.1f}", 'comment':item['comment']} for key, item in row['players'].items()}
            check(prefix + 'all-ten-series-ratings', ratings, expected)
            check(prefix + 'played-map-coverage', len(actual.get('maps', [])), len(row['maps']))
            for i, story in row['maps'].items():
                fact = actual.get('maps', [])[int(i)]
                winner = row['input']['series']['maps'][int(i)]['winner'];teams = row['input']['series']['teams']
                score = f"13 : {story['losing_rounds']}" if winner == teams[0] else f"{story['losing_rounds']} : 13"
                check(prefix + i + ':model-story', fact['story'], story['story'])
                check(prefix + i + ':oriented-round-score', fact['title'], row['bp']['order'][int(i)] + ' · 虚构回合比分 ' + score)
                check(prefix + i + ':winning-team-mvp', fact['mvp'], f"本图虚构 MVP · {story['mvp'].split(':')[1]}（{winner}）")
                check(prefix + i + ':fiction-label', '非真实比赛' in fact['notice'], True)
        board = observed['boards'][channel]
        sums, counts = {}, {}
        for index in [0, 1]:
            for player, value in dataset['cases'][f'VIT_100T_{index}']['players'].items():
                sums[player] = sums.get(player, 0) + value['rating'];counts[player] = counts.get(player, 0) + 1
        check(channel + ':board-coverage', sorted(r['id'] for r in board['all']), sorted(sums))
        check(channel + ':board-means', all(abs(float(r['rating']) - sums[r['id']] / counts[r['id']]) <= .050000001 and int(r['count']) == counts[r['id']] for r in board['all']), True)
        check(channel + ':board-descending', [float(r['rating']) for r in board['all']], sorted((float(r['rating']) for r in board['all']), reverse=True))
        check(channel + ':empty-search-feedback', '没有匹配' in board['empty'], True)
        check(channel + ':team-filter', sorted(board['team']), sorted(k for k in sums if k.startswith('VIT:')))
        check(channel + ':two-series-filter', sorted(board['both']), sorted(k for k in sums if counts[k] == 2))
        check(channel + ':name-sort', board['names'], sorted((k.split(':')[1] for k in sums), key=str.casefold))
        check(channel + ':review-link-label', '非真实比赛' in board['opened_review_notice'], True)
        path, query = urlsplit(board['shared_url']).fragment.split('?', 1);args = parse_qs(query)
        key = f"{args['upper'][0]}_{args['lower'][0]}_{path.split('/')[-1]}"
        check(channel + ':fresh-context-shared-review', board['shared_headline'], dataset['cases'][key]['headline'])
        check(channel + ':news-uses-same-two-reviews', board['news'], [dataset['cases'][f'VIT_100T_{i}']['headline'] for i in [0, 1]])
        check(channel + ':news-label', '非真实比赛' in board['news_notice'], True)
    for width in ['320', '390']:
        item = observed['mobile'][width]
        for view in ['review', 'board']:check(width + ':' + view + ':no-horizontal-document-overflow', item[view]['scroll'] <= item[view]['viewport'], True)
        check(width + ':touch-selected-map', item['story'], json.loads((ROOT / 'data/codex-fiction.json').read_text())['cases']['VIT_100T_1']['maps']['4']['story'])
        check(width + ':mobile-search', item['searched'], ['Chronicle'])
    counts = {state:sum(r['status'] == state for r in rows) for state in ['pass', 'fail']}
    return {'status':'pass' if not counts['fail'] else 'fail', 'counts':counts, 'rows':rows}


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--observed',required=True);parser.add_argument('--out',required=True);args=parser.parse_args();result=compare(json.loads((REPO/args.observed).read_text()));out=REPO/args.out;out.mkdir(parents=True,exist_ok=False);(out/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':result['status'],'counts':result['counts']}));raise SystemExit(0 if result['status']=='pass' else 1)
