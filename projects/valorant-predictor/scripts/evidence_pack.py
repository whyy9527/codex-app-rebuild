"""Compile public observed match facts. No inference, weighting, or model calls.

Collector requires beautifulsoup4; core validator and forecast contracts use stdlib.
Raw HTTP responses and timestamp receipts stay in the explicitly chosen cache.
"""
import argparse,hashlib,json,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
FOUR=['VIT','LOUD','100T','G2']
EVENT_URL='https://www.vlr.gg/event/matches/2766/valorant-champions-2026/?series_id=all'
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def text(n):return n.get_text(' ',strip=True) if n else ''
def number(n):
 s=text(n).rstrip('%');return None if not s or s=='—' or s=='-' else float(s) if '.' in s else int(s)
def parse_match(raw):
 from bs4 import BeautifulSoup
 s=BeautifulSoup(raw,'html.parser');date=s.select_one('.match-header-date [data-utc-ts]')
 if not date or not any(text(n).lower()=='final' for n in s.select('.match-header-vs-note')):raise ValueError('Not a completed dated match')
 codes=[text(n) for n in s.select_one('.vlr-rounds-row-col.mod-teams').select('.vlr-rounds-tag')]
 if len(codes)!=2 or len(set(codes))!=2:raise ValueError('Missing two team identities')
 patch=re.search(r'Patch\s+([\d.]+)',text(s.select_one('.match-header-date')))
 maps=[]
 for g in s.select('.vm-stats-game'):
  if g.get('data-game-id')=='all':continue
  h=g.select_one('.vm-stats-game-header')
  if h is None:continue
  name=h.select_one('.map-name');name=text(name).replace('PICK','').strip();teams=h.select('.team');score=[number(t.select_one('.score')) for t in teams]
  if len(score)!=2 or any(v is None for v in score):continue
  sides=[{'attack_wins':sum(number(x) or 0 for x in t.select('.mod-t')),'defense_wins':sum(number(x) or 0 for x in t.select('.mod-ct')),'overtime_wins':sum(number(x) or 0 for x in t.select('.mod-ot')),'side_scope':'regulation_only','start_side':'ATK' if t.select_one('span').get('class')==['mod-t'] else 'DEF'} for t in teams]
  if any(v['attack_wins']+v['defense_wins']+v['overtime_wins']!=score[i] for i,v in enumerate(sides)):raise ValueError('Side score mismatch')
  players=[]
  for r in g.select('.ovw-row:not(.mod-head)'):
   tag=text(r.select_one('.ovw-player-tag'));namep=text(r.select_one('.ovw-player-name'))
   if not namep:continue
   stats={k:number(r.select_one('[data-col="'+k+'"] .mod-both')) for k in ['acs','kills','deaths','assists','kast','adr','fb','fd']}
   players.append({'team':tag,'name':namep,'agents':[i.get('title') or i.get('alt') for i in r.select('.ovw-agents img')],**stats})
  if len(players)!=10 or any(sum(p['team']==c for p in players)!=5 for c in codes):raise ValueError('Need exact five observed players per team')
  maps.append({'game_id':g['data-game-id'],'map':name,'score':score,'sides':sides,'players':players})
 if not maps:raise ValueError('No observed maps')
 score=[sum(m['score'][i]>m['score'][1-i] for m in maps) for i in range(2)]
 return {'start_utc':date['data-utc-ts'].replace(' ','T')+'Z','teams':codes,'score':score,'patch':patch[1] if patch else None,'veto':text(s.select_one('.match-header-note')) or None,'maps':maps}
def collect(cache):
 from bs4 import BeautifulSoup
 cache.mkdir(parents=True,exist_ok=True)
 receipts=[]
 def fetch(url):
  sid=hashlib.sha256(url.encode()).hexdigest()[:20];stamp=datetime.now(timezone.utc).isoformat()
  raw=urlopen(Request(url,headers={'User-Agent':'VCT-Evidence/2.0'}),timeout=45).read();stamp=datetime.now(timezone.utc).isoformat();name=sid+('.pdf' if url.endswith('.pdf') else '.html');(cache/name).write_bytes(raw)
  receipts.append({'id':sid,'url':url,'observed_at':stamp,'sha256':hashlib.sha256(raw).hexdigest(),'file':name,'status':'observed'});return raw
 raw=fetch(EVENT_URL);s=BeautifulSoup(raw,'html.parser')
 urls=sorted({'https://www.vlr.gg'+a['href'] for a in s.select('a[href]') if 'Completed' in text(a) and any(n in text(a) for n in ['Team Vitality','LOUD','100 Thieves','G2 Esports']) and 'valorant-champions-2026' in a['href']})
 for u in urls:fetch(u)
 rules=json.loads((ROOT/'data/veto/context.json').read_text())['rules']
 for u in ['https://valorantesports.com/en-US/',rules['specific_url'],rules['competition_url']]:fetch(u)
 (cache/'receipts.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n')
def compile_pack(cache,cutoff):
 cutoff_dt=datetime.fromisoformat(cutoff.replace('Z','+00:00'));receipts=json.loads((cache/'receipts.json').read_text());sources=[];facts=[];series=[]
 for r in receipts:
  if r['status']!='observed':continue
  raw=(cache/r['file']).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=r['sha256']:raise ValueError('Source digest mismatch')
  if datetime.fromisoformat(r['observed_at'])>cutoff_dt:raise ValueError('Evidence observed after freeze')
  source={'id':r['id'],'url':r['url'],'observed_at':r['observed_at'],'sha256':r['sha256'],'kind':'official' if 'vlr.gg' not in r['url'] else 'secondary_esports_database'};sources.append(source)
  if re.search(r'vlr.gg/\d+/',r['url']):
   row=parse_match(raw);mid=r['url'].split('/')[3];fid='series:'+mid
   if datetime.fromisoformat(row['start_utc'].replace('Z','+00:00'))>=cutoff_dt:raise ValueError('Future match in input')
   if not set(row['teams'])&set(FOUR):raise ValueError('Unrelated match')
   base={'source_id':r['id'],'as_of':None,'event_start_utc':row['start_utc'],'available_at':r['observed_at'],'availability_basis':'first_observed_completed_page; historical_publication_time_unknown','coverage':'one completed Champions 2026 series','sample_count':len(row['maps'])}
   facts.append({'id':fid,'type':'completed_series',**base,'value':{k:v for k,v in row.items() if k!='maps'}})
   for i,m in enumerate(row['maps'],1):facts.append({'id':f'map:{mid}:{i}','type':'map_result',**base,'coverage':'one completed map; per-player published statistics','sample_count':1,'value':{'series_ref':fid,'teams':row['teams'],**m}})
   series.append((row,fid))
 # Current official schedule is new input, never overwrite event.json or old forecasts.
 from sync_data import extract
 official=next((r for r in receipts if r.get('status')=='observed' and r['url']=='https://valorantesports.com/en-US/'),None)
 official_event=extract((cache/official['file']).read_text()) if official else None
 if official_event:
  facts.append({'id':'official:schedule','type':'official_schedule','source_id':official['id'],'as_of':None,'available_at':official['observed_at'],'coverage':'official page at observation; not live','sample_count':len(official_event['history']),'value':{'matches':official_event['matches'],'predecessors':official_event['predecessors']}})
 context=json.loads((ROOT/'data/veto/context.json').read_text());rule_source=next(r for r in receipts if r['url']==context['rules']['specific_url'])
 if rule_source['sha256']!=context['rules']['specific_sha256']:raise ValueError('Official specific rules changed; re-review before compiling')
 rule_text=subprocess.check_output(['pdftotext',str(cache/rule_source['file']),'-'],text=True)
 patch_line=next(line.strip() for line in rule_text.splitlines() if 'All matches will be played on patch version' in line)
 facts.append({'id':'official:rules','type':'competition_rules','source_id':rule_source['id'],'as_of':None,'available_at':rule_source['observed_at'],'coverage':context['rules']['sections'],'sample_count':1,'value':{'pool':context['pool'],'competitive_patch_statement':patch_line,'rules':context['rules']}})
 summaries={};rosters={}
 for team in FOUR:
  rows=sorted([(r,f) for r,f in series if team in r['teams']],key=lambda rf:rf[0]['start_utc']);by_map={}
  if not rows:raise ValueError('No observed matches for '+team)
  latest,fid=rows[-1];rosters[team]={'status':'last_observed_match_lineup','players':[p['name'] for p in latest['maps'][-1]['players'] if p['team']==team],'event_start_utc':latest['start_utc'],'evidence_refs':[f'map:{fid.split(":")[1]}:{len(latest["maps"])}'],'upcoming_starting_lineup':'unconfirmed'}
  for row,ref in rows:
   i=row['teams'].index(team)
   for j,m in enumerate(row['maps'],1):
    b=by_map.setdefault(m['map'],{'played':0,'wins':0,'rounds_won':0,'rounds_lost':0,'attack_wins':0,'attack_rounds':0,'defense_wins':0,'defense_rounds':0,'evidence_refs':[]});side=m['sides'][i];opp=m['sides'][1-i]
    b['played']+=1;b['wins']+=m['score'][i]>m['score'][1-i];b['rounds_won']+=m['score'][i];b['rounds_lost']+=m['score'][1-i];b['attack_wins']+=side['attack_wins'];b['attack_rounds']+=side['attack_wins']+opp['defense_wins'];b['defense_wins']+=side['defense_wins'];b['defense_rounds']+=side['defense_wins']+opp['attack_wins'];b['evidence_refs'].append(f'map:{ref.split(":")[1]}:{j}')
  summaries[team]={'side_summary_scope':'regulation_only; overtime excluded from side denominators','series_played':len(rows),'series_won':sum(r['score'][r['teams'].index(team)]>r['score'][1-r['teams'].index(team)] for r,_ in rows),'by_map':by_map}
 gaps=[{'type':k,'status':'unavailable','reason':reason} for k,reason in [('confirmed_upcoming_lineup','Past match participation does not confirm the next starting lineup.'),('injury_and_scrim','No verified primary evidence collected; do not infer health or scrim form.'),('long_term_history','Only this tournament; opponent strength and small samples remain confounders.'),('official_player_telemetry','Player/map statistics are VLR secondary records, not Riot telemetry.'),('historical_available_at','Original publication timestamps not supplied; conservatively use first collection time.'),('probability_calibration','No fitted or validated probability calibration; historical model predictions stay frozen.')]]
 pack={'schema_version':'valorant_evidence.v2','frozen_at':cutoff,'prediction_status':'not_run_requires_new_authorization','scope':['2026-10-17','2026-10-18'],'teams':FOUR,'sources':sources,'facts':facts,'team_summaries':summaries,'rosters':rosters,'gaps':gaps,'legacy_input':{'file':'data/event.json','sha256':hashlib.sha256((ROOT/'data/event.json').read_bytes()).hexdigest(),'used_by_existing_forecasts':True,'v2_used_by_existing_forecasts':False},'notes':['Summary counts are arithmetic over cited map facts, not additional independent evidence.','No odds, composite strengths, invented weights, financial data, or inferred injuries.','Per-player stats retain published per-map ACS/KAST; no unweighted cross-map average.','Roster names preserve provider spelling; no alias guessing.']}
 pack['content_sha256']=digest(pack);validate_pack(pack);return pack
def validate_pack(pack):
 if pack.get('schema_version')!='valorant_evidence.v2':raise ValueError('Evidence schema mismatch')
 cutoff=datetime.fromisoformat(pack['frozen_at'].replace('Z','+00:00'));sources={s['id']:s for s in pack['sources']};ids=set()
 if len(sources)!=len(pack['sources']) or any(datetime.fromisoformat(s['observed_at'].replace('Z','+00:00'))>cutoff for s in sources.values()):raise ValueError('Duplicate source or source observed after freeze')
 for f in pack['facts']:
  if f['id'] in ids or f['source_id'] not in sources:raise ValueError('Duplicate or unknown evidence source')
  ids.add(f['id']);available=datetime.fromisoformat(f['available_at'].replace('Z','+00:00'))
  if available!=datetime.fromisoformat(sources[f['source_id']]['observed_at'].replace('Z','+00:00')):raise ValueError('Availability must preserve first source observation')
  if available>cutoff:raise ValueError('Future evidence')
 for f in pack['facts']:
  if f['type']=='map_result' and f['value']['series_ref'] not in ids:raise ValueError('Unknown series ref')
 copy={k:v for k,v in pack.items() if k!='content_sha256'}
 if pack.get('content_sha256')!=digest(copy):raise ValueError('Evidence content hash mismatch')
 return True
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);p.add_argument('--collect',action='store_true');p.add_argument('--freeze');p.add_argument('--out',type=Path,default=ROOT/'data/evidence-v2.json');a=p.parse_args()
 if a.collect:collect(a.cache)
 pack=compile_pack(a.cache,a.freeze or datetime.now(timezone.utc).isoformat());a.out.parent.mkdir(parents=True,exist_ok=True);tmp=a.out.with_suffix('.tmp');tmp.write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n');tmp.replace(a.out);print(json.dumps({'facts':len(pack['facts']),'sources':len(pack['sources']),'maps':sum(f['type']=='map_result' for f in pack['facts']),'sha256':pack['content_sha256']}))
