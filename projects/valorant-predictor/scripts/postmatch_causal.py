"""One isolated, explicitly authorized grand-final worker; original predictions remain immutable."""
import argparse,fcntl,json,os,traceback
from pathlib import Path
import causal_series as c
import paid_causal as paid
from evidence_pack import validate_pack

def run(root,channel):
 root=root.resolve();approval=json.loads((root/'approval.json').read_text());paid.approved_cap(root)
 if channel not in ['codex','deepseek','mimo','doubao'] or channel not in approval['worker_channels']:raise ValueError('Unapproved worker')
 pack=json.loads((root/'evidence.json').read_text());validate_pack(pack)
 if pack['content_sha256']!=approval['evidence_sha256'] or pack['scope']!=['2026-10-18']:raise ValueError('Frozen batch input differs')
 if approval['teams']!=['LOUD','VIT'] or approval['purpose']!='grand_final_postmatch_20261018':raise ValueError('Wrong actual final')
 out=root/channel;out.mkdir(exist_ok=True);started=paid.now()
 with (out/'worker.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  c.write(out/'worker-status.json',{'status':'running','run_id':root.name,'channel':channel,'pid':os.getpid(),'started_at':started,'evidence_sha256':pack['content_sha256']})
  try:
   if channel=='codex':
    c.write(out/'approval.json',{'approved':True,'model':c.MODEL,'api_budget_cny':0,'no_artificial_call_limit':True,'authorization_source':'User explicitly authorized this post-match GPT quota run; no paid API fallback'})
   c.call=paid.GPT_CALL if channel=='codex' else paid.make_call(channel,root)
   def publish(dest,evidence):
    paid.publish_provider(dest,evidence,channel,publish_pair=False)
    path=dest/'public.json';value=json.loads(path.read_text());value.update(case_id='gf',match_id='115576361461208331',prediction_version=root.name,information_cutoff=pack['frozen_at'],version_kind='postmatch_rerun',exclude_from_original_prematch_accuracy=True);c.write(path,value)
   c.publish=publish;state=out/'state.json';s=json.loads(state.read_text()) if state.exists() else c.initial(pack,['LOUD','VIT'])
   if s['teams']!=['LOUD','VIT'] or s['evidence_sha256']!=pack['content_sha256']:raise ValueError('Checkpoint belongs to another fixture/input')
   if not state.exists():c.write(state,s)
   if s['stage']=='bp':
    task={'task':'已核实10月17日败决VIT 3:1 100T。现在只预测10月18日14:00北京时间总决赛LOUD vs VIT；VIT不是你自己推出来的败决赢家。LOUD为胜者组冠军，连续禁用两图并优先选A/B身份；A/B/A/B选四图，剩余第五图，选边B/A/B/A/B。first_team_start_side始终指teams[0]=LOUD。输出BP和真实证据引用，不得预选赢家或比分。'}
    paid.complete_bp(channel,root,out,s,pack,True,task_override=task)
   c.run_remaining(out,pack,max_rounds=6 if channel=='codex' else 1 if channel=='deepseek' else 3)
   s=json.loads(state.read_text());publish(out,pack)
   if s['stage']!='finished' or max(s['series_score'])!=3:raise ValueError('Final not complete')
   c.write(out/'worker-status.json',{'status':'finished','run_id':root.name,'channel':channel,'pid':os.getpid(),'started_at':started,'finished_at':paid.now(),'winner':s['winner'],'score':s['series_score'],'evidence_sha256':pack['content_sha256']})
   print(channel+' FINAL COMPLETE '+str(s['series_score'])+' '+s['winner'],flush=True)
  except Exception as e:
   c.write(out/'worker-status.json',{'status':'blocked','run_id':root.name,'channel':channel,'pid':os.getpid(),'started_at':started,'stopped_at':paid.now(),'error':str(e)});traceback.print_exc();raise

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--channel',choices=['codex','deepseek','mimo','doubao'],required=True);a=p.parse_args();run(a.root,a.channel)
