"""Generate explicitly fictional reviews with verified, matching model channels.

The engine owns winners, scores and case IDs. Models own only fictional map
vetoes, narratives and ratings. Outputs cannot change the frozen simulation.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

from run_models import ROOT
from run_api_models import request, PROVIDERS


def digest(value):return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def strict_json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:raise ValueError('Duplicate JSON key: ' + key)
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique)


def cases_for(channel):
    script = '''import fs from 'node:fs';
import {mapProbability,simulateSeries} from './engine.mjs';
const event=JSON.parse(fs.readFileSync('data/event.json'));
const manifest=JSON.parse(fs.readFileSync('data/model-forecasts.json'));
const forecast=JSON.parse(fs.readFileSync('data/'+manifest[process.argv[1]]));
const result={};
for(const upperWinner of event.predecessors[0].teams)for(const lowerWinner of event.predecessors[1].teams){
 const upperLoser=event.predecessors[0].teams.find(t=>t!==upperWinner);
 const lower=simulateSeries(upperLoser,lowerWinner,mapProbability(forecast,upperLoser,lowerWinner),20261017);
 const grand=simulateSeries(upperWinner,lower.winner,mapProbability(forecast,upperWinner,lower.winner),20261018);
 [lower,grand].forEach((series,index)=>{result[`${upperWinner}_${lowerWinner}_${index}`]={scenario:{upperWinner,lowerWinner},match_index:index,match_id:event.matches[index].id,series};});
}
console.log(JSON.stringify(result));'''
    return json.loads(subprocess.check_output(['node', '--input-type=module', '-e', script, channel], cwd=ROOT, text=True))


def object_schema(properties):return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}


def schema_for(cases, context):
    text = {'type': 'string'}
    properties = {}
    for key, case in cases.items():
        players = [team + ':' + player for team in case['series']['teams'] for player in context['teams'][team]['players']]
        rating = object_schema({'rating': {'type': 'number'}, 'comment': text})
        map_story = object_schema({'story': text, 'losing_rounds': {'type': 'integer'}, 'mvp': {'type': 'string', 'enum': players}})
        properties[key] = object_schema({
            'headline': text, 'summary': text,
            'bp': object_schema({'bans': {'type': 'array', 'items': {'type': 'string', 'enum': context['maps']['pool']}}, 'order': {'type': 'array', 'items': {'type': 'string', 'enum': context['maps']['pool']}}, 'reason': text}),
            'maps': object_schema({str(i): map_story for i in range(len(case['series']['maps']))}),
            'players': object_schema({player: rating for player in players}),
        })
    return object_schema(properties)


def validate(value, cases, context):
    def keys(actual, expected):
        if not isinstance(actual, dict) or set(actual) != set(expected):raise ValueError('Missing, extra or duplicate case/field coverage')
    def text(v, minimum, maximum):
        if not isinstance(v, str) or not minimum <= len(v.strip()) <= maximum or '<' in v or '>' in v:raise ValueError('Invalid fiction text')
    keys(value, cases)
    for key, case in cases.items():
        row = value[key];keys(row, ['headline', 'summary', 'bp', 'maps', 'players'])
        text(row['headline'], 5, 65);text(row['summary'], 30, 280)
        keys(row['bp'], ['bans', 'order', 'reason']);text(row['bp']['reason'], 20, 180)
        bans, order = row['bp']['bans'], row['bp']['order']
        if not isinstance(bans, list) or not isinstance(order, list) or len(bans) != 2 or len(order) != 5 or len(set(bans + order)) != 7 or set(bans + order) != set(context['maps']['pool']):raise ValueError('Fictional seven-map veto must partition two bans and five ordered maps')
        players = {team + ':' + player for team in case['series']['teams'] for player in context['teams'][team]['players']}
        keys(row['players'], players);keys(row['maps'], [str(i) for i in range(len(case['series']['maps']))])
        for i, item in row['maps'].items():
            keys(item, ['story', 'losing_rounds', 'mvp']);text(item['story'], 25, 220)
            if type(item['losing_rounds']) is not int or not 0 <= item['losing_rounds'] <= 11:raise ValueError('Invalid fictional regulation map score')
            if re.search(r'[ABC]\s*点|半场|手枪局后连追', item['story'], re.I):raise ValueError('Do not invent unverified map-site layout or partial round arithmetic')
            for first, second in re.findall(r'(\d+)\s*[-:：比]\s*(\d+)', item['story']):
                numbers = [int(first), int(second)]
                terminal_series = int(i) == len(case['series']['maps']) - 1 and numbers == sorted(case['series']['score'], reverse=True)
                if numbers != [13, item['losing_rounds']] and not terminal_series:raise ValueError('Narrative score conflicts with its structured fictional round/terminal series score')
            winner = case['series']['maps'][int(i)]['winner']
            if item['mvp'] not in players or not item['mvp'].startswith(winner + ':'):raise ValueError('Map MVP must belong to supplied simulated winning team')
        for item in row['players'].values():
            keys(item, ['rating', 'comment']);text(item['comment'], 8, 90)
            if type(item['rating']) not in (int, float) or not math.isfinite(item['rating']) or not 0 <= item['rating'] <= 10:raise ValueError('Fiction rating must be finite and within 0..10')
    return value


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--provider', choices=['codex', *PROVIDERS], required=True);parser.add_argument('--out', type=Path, required=True);parser.add_argument('--repair-from', type=Path);parser.add_argument('--case-ids', nargs='+');args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    context = json.loads((ROOT / 'data/fiction-context.json').read_text())
    event = json.loads((ROOT / 'data/event.json').read_text())
    cases = cases_for(args.provider)
    if args.case_ids:
        if len(set(args.case_ids)) != len(args.case_ids) or not set(args.case_ids) <= set(cases):raise ValueError('Unknown or duplicate selected cases')
        cases = {key: cases[key] for key in args.case_ids}
    schema = schema_for(cases, context)
    if args.repair_from and (args.provider == 'codex' or json.loads((args.repair_from / 'cases.json').read_text()) != cases):raise ValueError('Repair must retain the exact frozen case inputs')
    prompt = '''用中文创作 VALORANT 赛前虚构比赛回看。所有剧情、BP、回合比分、MVP 和 0..10 选手评分都将明确标注为虚构，绝不是真实战报或能力评估。只写指定17、18日两场，不预测16日。禁止联网、调用工具、写文件。禁止虚构选手引语、心理、私生活、伤病、争议或背书。根对象只含八个case键，不能添加type、properties等schema元字段。
引擎已经固定每个情景的对阵、逐图胜者和最终比分，你不能改动它们。按下面 JSON Schema 精确输出所有8个 case，每个 case 独立写作。BP 使用提供的七张虚构地图池：bans 恰好两张，order 恰好五张，二者合起来七张无重复；order 后几图可能未进行。不是官方赛事 BP 规则。
maps 只包含实际模拟打出的图，以0起的字符串序号为键；story 每图25到220字符，必须服从该图胜者，描写合理的局内攻防；losing_rounds 是0到11整数，胜方固定13回合；mvp 使用该图胜队的 team:player ID。不得在文字中发明与输入矛盾的系列赛比分。story不写A点/B点/C点等未提供地图结构，不写半场分数、中途比分或连续赢几回合的算术。可以写包点、入口、中路、侧翼和转点等通用战术。若story写回合比分，只允许13比losing_rounds这一种最终比分，与结构字段完全一致。
players 必须覆盖本场两队全部十人，键为输入的 team:player，每人 rating 为0..10数值，comment 为8到90字符的本场虚构表现评语，不评价真实能力。headline 5到65字符、summary 30到280字符、bp.reason 20到180字符。所有字段严格遵守 schema，不添加免责声明字段，页面会统一醒目标识。
人物与地图索引（名单来源不能延伸成真实首发或表现）：
''' + json.dumps(context, ensure_ascii=False) + '\n不可更改的模拟比赛：\n' + json.dumps(cases, ensure_ascii=False) + '\nJSON Schema：\n' + json.dumps(schema, ensure_ascii=False)
    prompt = prompt.replace('八个case', f'{len(cases)}个case').replace('所有8个 case', f'所有{len(cases)}个 case')
    (args.out / 'prompt.txt').write_text(prompt);(args.out / 'schema.json').write_text(json.dumps(schema));(args.out / 'cases.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2))
    if args.provider == 'codex':
        result = (args.out / 'last-message.json').resolve()
        command = ['codex', 'exec', '--skip-git-repo-check', '--ephemeral', '--sandbox', 'read-only', '--color', 'never', '--model', 'gpt-6.1-sol', '-c', 'model_reasoning_effort="high"', '--output-schema', str((args.out / 'schema.json').resolve()), '--output-last-message', str(result), '-']
        with tempfile.TemporaryDirectory(prefix='valorant-fiction-') as temp:
            run = subprocess.run(command, input=prompt, capture_output=True, text=True, cwd=temp, timeout=600)
        (args.out / 'stdout.log').write_text(run.stdout);(args.out / 'stderr.log').write_text(run.stderr)
        if run.returncode:raise RuntimeError('Model fiction run failed; no fallback used')
        header = run.stderr.split('user\n', 1)[0]
        model = re.search(r'^model:\s*(\S+)', header, re.M);effort = re.search(r'^reasoning effort:\s*(\S+)', header, re.M)
        if not model or model[1] != 'gpt-6.1-sol' or not effort or effort[1] != 'high':raise ValueError('Model identity mismatch')
        attestation = {'provider': 'openai', 'model': model[1], 'reasoning_effort': effort[1], 'startup_header_sha256': hashlib.sha256(header.encode()).hexdigest()}
        value = strict_json(result.read_text())
    else:
        config = PROVIDERS[args.provider];key = os.environ.get(config['key'])
        if not key:raise RuntimeError(args.provider + ' credential unavailable')
        catalog = request(config['base'] + '/models', key)
        entry = next((r for r in catalog['data'] if r['id'] == config['model'] and (config['display'] is None or r.get('name') == config['display'])), None)
        if not entry:raise ValueError('Exact provider model unavailable')
        body = {'model': config['model'], 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 16384, 'thinking': {'type': 'enabled'}}
        if args.provider != 'mimo':body.update(response_format={'type': 'json_object'}, reasoning_effort='high')
        if args.repair_from:
            prior = json.loads((args.repair_from / 'response.json').read_text())
            if prior.get('model') != config['model']:raise ValueError('Repair provider identity differs')
            previous = prior['choices'][0]['message']['content']
            try:
                validate(strict_json(previous), cases, context)
            except (ValueError, KeyError, TypeError) as error:
                failure = str(error)
            else:raise ValueError('Previous output is already valid; no repair needed')
            body['messages'] += [{'role': 'assistant', 'content': previous}, {'role': 'user', 'content': '上次结果未通过校验：' + failure + '。保留指定case和比赛输入，只修复契约问题，完整输出所有指定case。根对象与各case不能添加type、properties等schema元字段。story不写中途系列赛比分，只可写与losing_rounds一致的13比N图比分。严格JSON，不用代码围栏。'}]
            (args.out / 'repair.json').write_text(json.dumps({'prior_response_sha256': hashlib.sha256(previous.encode()).hexdigest(), 'validation_error': failure, 'attempt': 1}))
        response = request(config['base'] + '/chat/completions', key, body, timeout=600)
        (args.out / 'response.json').write_text(json.dumps(response, ensure_ascii=False, indent=2))
        if response.get('model') != config['model'] or response['choices'][0].get('finish_reason') != 'stop':raise ValueError('Incomplete or mismatched model output')
        value = strict_json(response['choices'][0]['message']['content'])
        attestation = {'provider': args.provider, 'model': response['model'], 'catalog_name': entry.get('name'), 'thinking': 'enabled'}
    validate(value, cases, context)
    manifest = json.loads((ROOT / 'data/model-forecasts.json').read_text())
    output = {'schema_version': 1, 'kind': 'fiction', 'channel': args.provider, 'created_at': datetime.now(timezone.utc).isoformat(), 'label': 'AI 虚构模拟 · 非真实比赛、非选手能力评估', 'event_source_sha256': event['source_sha256'], 'forecast_sha256': hashlib.sha256((ROOT / 'data' / manifest[args.provider]).read_bytes()).hexdigest(), 'context_sha256': digest(context), 'runtime_attestation': attestation, 'cases': {key: {'input': case, **value[key]} for key, case in cases.items()}}
    (args.out / 'validated-fiction.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'channel': args.provider, 'cases': len(cases), 'model': attestation['model'], 'validated': True}))


if __name__ == '__main__':main()
