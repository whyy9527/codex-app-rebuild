"""Read public Riot SSR match records, retaining exact event identity and provenance."""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

SOURCE = 'https://valorantesports.com/en-US/'
ARTICLE = 'https://valorantesports.com/en-US/news/champions-shanghai-everything-you-need-to-know'
EVENT = 'Champions Shanghai'
TARGETS = {'2026-10-17': '败者组决赛', '2026-10-18': '总决赛'}


def extract(html):
    events = {}
    for m in re.finditer(r'\{"__typename":"EventMatch"', html):
        try:
            event, _ = json.JSONDecoder().raw_decode(html[m.start():])
        except ValueError:
            continue
        if event.get('tournament', {}).get('name') == EVENT:
            events[event['id']] = event
    if not events:
        raise ValueError('Official SSR contains no Champions Shanghai matches; preserve previous snapshot')
    rows, teams = [], {}
    for e in sorted(events.values(), key=lambda e: (e['startTime'], e['id'])):
        participants = []
        for t in e['matchTeams']:
            code = t['code']
            participants.append(code)
            if code != 'TBD':
                teams[code] = {'id': t['teamId'], 'code': code, 'name': t['name'],
                               'logo': t['image'].replace('http://', 'https://'),
                               'region': (t.get('homeLeague') or {}).get('regionSlug')}
        result = [t.get('result') for t in e['matchTeams']]
        completed = e['state'] == 'completed'
        winner = next((t['code'] for t in e['matchTeams'] if (t.get('result') or {}).get('outcome') == 'win'), None)
        strategy = e['match']['strategy']
        best_of = strategy['count']
        if completed and (winner is None or any(r is None for r in result)):
            raise ValueError('Completed official match lacks a consistent result: ' + e['id'])
        rows.append({'id': e['id'], 'start_utc': e['startTime'], 'stage': e['blockName'], 'state': e['state'],
                     'teams': participants, 'best_of': best_of,
                     'score': [r['gameWins'] for r in result] if completed else None, 'winner': winner,
                     'source_url': SOURCE})
    matches = []
    for date, label in TARGETS.items():
        exact = [r for r in rows if r['start_utc'][:10] == date]
        if len(exact) != 1 or exact[0]['best_of'] != 5:
            raise ValueError('Expected exactly one official BO5 on ' + date)
        matches.append({**exact[0], 'label': label})
    upcoming = [r for r in rows if r['start_utc'][:10] == '2026-10-16']
    if len(upcoming) != 2:
        raise ValueError('Cannot resolve official finals-weekend predecessor matches')
    return {'event': '2026 VALORANT 上海全球冠军赛', 'timezone': 'Asia/Shanghai',
            'matches': matches, 'teams': teams, 'history': [r for r in rows if r['score'] is not None],
            'predecessors': upcoming, 'scope': list(TARGETS),
            'sources': [{'url': SOURCE, 'role': 'official_schedule_results', 'publisher': 'Riot Games'},
                        {'url': ARTICLE, 'role': 'official_stage_dates', 'publisher': 'Riot Games'}]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', type=Path, help='Reparse an exact saved public HTML response')
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parents[1] / 'data/event.json')
    args = parser.parse_args()
    if args.html:
        raw = args.html.read_bytes()
    else:
        with urlopen(Request(SOURCE, headers={'User-Agent': 'VCT-Finals-Replica/1.0', 'Accept-Encoding': 'gzip'}), timeout=30) as response:
            raw = response.read()
    if raw[:2] == b'\x1f\x8b': raw = gzip.decompress(raw)
    data = extract(raw.decode('utf-8'))
    data.update(fetched_at=datetime.now(timezone.utc).isoformat(), source_sha256=hashlib.sha256(raw).hexdigest(),
                limitations=['官方对阵为 TBD 时保留待定；不把情景选择当作已确定对阵。',
                             '官方本页提供系列赛与地图胜场，未提供选手 ACS/KAST 或地图名称；这些数据不补造。'])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temp = args.out.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temp.replace(args.out)
    print(json.dumps({'matches': len(data['matches']), 'history': len(data['history']), 'fetched_at': data['fetched_at']}))


if __name__ == '__main__': main()
