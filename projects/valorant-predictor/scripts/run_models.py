"""Run available exact model channels against one frozen official input.

No fallback model is accepted. Runtime identity comes from the provider/CLI
response, never from the model-authored forecast. Credentials stay with CLIs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = {'type':'object','properties':{'pairs':{'type':'array','items':{'type':'object','properties':{
    'team1':{'type':'string'},'team2':{'type':'string'},'p_first':{'type':'number'},'reason':{'type':'string'}},
    'required':['team1','team2','p_first','reason'],'additionalProperties':False}},'limitations':{'type':'string'}},
    'required':['pairs','limitations'],'additionalProperties':False}


def normalize(value, event, model, channel, attestation):
    teams = set(t for p in event['predecessors'] for t in p['teams'])
    required = {frozenset(p) for p in itertools.combinations(teams,2)}
    seen, pairs = set(), []
    for row in value['pairs']:
        pair = frozenset([row['team1'],row['team2']])
        p = row['p_first']
        if pair not in required or pair in seen or type(p) not in (int,float) or not 0 < p < 1 or not row['reason'].strip():
            raise ValueError('Duplicate, missing, invalid or unknown model pair')
        seen.add(pair)
        pairs.append({'teams':[row['team1'],row['team2']],'p_first':p,'reason':row['reason']})
    if seen != required: raise ValueError('Exactly six distinct finalists pairs required')
    limitations=value['limitations']
    if isinstance(limitations,list) and limitations and all(isinstance(item,str) and item.strip() for item in limitations):
        limitations='；'.join(limitations)
    if not isinstance(limitations,str) or not limitations.strip():raise ValueError('Model limitations must contain nonempty text')
    return {'schema_version':1,'channel':channel,'model_id':model,'kind':'llm_analysis','created_at':datetime.now(timezone.utc).isoformat(),
            'source_sha256':event['source_sha256'],'data_cutoff':max(r['start_utc'] for r in event['history']),
            'scope':[m['id'] for m in event['matches']],'probability_unit':'single_map',
            'calibration':'独立模型的主观赛前判断，未校准。'+limitations,'pairs':pairs,'runtime_attestation':attestation}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--provider',choices=['codex'],required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    event=json.loads((ROOT/'data/event.json').read_text())
    prompt='''你是电竞赛前分析模型。只根据下面这份冻结的 Riot 官网赛事资料，用中文输出严格 JSON。不要调用工具、联网、写文件或查询任何个人资料。仅预测 2026-10-17 败者组决赛和 10-18 总决赛，不预测16日比赛。对阵尚未确定，因此为四强之间全部六组可能对阵各给一个单张地图胜率 p_first（0到1）与具体理由；team1 和 team2 使用官方简称。概率为你的主观判断，不要伪称统计校准或已运行十万次。不得编造地图BP、选手能力、历史荣誉、阵容和伤病。本页未提供这些事实。每组一次，不得遗漏或重复。字段只含 pairs:[{team1,team2,p_first,reason}] 与 limitations。两场都为BO5，系列赛转换由独立程序负责，切勿把系列赛概率填成单图概率。\n官方资料：\n'''+json.dumps(event,ensure_ascii=False)
    (args.out/'prompt.txt').write_text(prompt)
    (args.out/'schema.json').write_text(json.dumps(SCHEMA))
    with tempfile.TemporaryDirectory(prefix='valorant-forecast-') as temp:
        model='gpt-6.1-sol';channel='codex';result=args.out/'last-message.json'
        command=['codex','exec','--skip-git-repo-check','--ephemeral','--sandbox','read-only','--color','never',
                 '--model',model,'-c','model_reasoning_effort="high"','--output-schema',str((args.out/'schema.json').resolve()),
                 '--output-last-message',str(result.resolve()),'-']
        completed=subprocess.run(command,input=prompt,cwd=temp,capture_output=True,text=True,timeout=240)
    (args.out/'stdout.log').write_text(completed.stdout);(args.out/'stderr.log').write_text(completed.stderr)
    if completed.returncode: raise RuntimeError('Model channel unavailable; see private run logs (no fallback used)')
    header=completed.stderr.split('user\n',1)[0]
    actual=re.search(r'^model:\s*(\S+)',header,re.M);effort=re.search(r'^reasoning effort:\s*(\S+)',header,re.M)
    if not actual or actual[1]!=model or not effort or effort[1]!='high':raise ValueError('Codex runtime identity/effort unavailable or mismatched')
    value=json.loads(result.read_text());attestation={'provider':'openai','model':actual[1],'reasoning_effort':effort[1],
        'startup_header_sha256':hashlib.sha256(header.encode()).hexdigest()}
    normalized=normalize(value,event,model,channel,attestation)
    (args.out/'validated-forecast.json').write_text(json.dumps(normalized,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'provider':args.provider,'model':model,'pairs':len(normalized['pairs']),'result':str(args.out/'validated-forecast.json')},ensure_ascii=False))


if __name__=='__main__':main()
