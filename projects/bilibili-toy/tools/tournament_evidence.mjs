// Structural comparison of actual UI traversals with independent random draws.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {tournamentFacts,sharedPredictionFacts} from './prediction_native.mjs';

const project=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),workspace=path.resolve(project,'../..');
const privateRoot=path.join(project,'private'),hash=x=>createHash('sha256').update(x).digest('hex');
const rel=x=>path.relative(workspace,x);
async function input(x){const f=await fs.realpath(path.resolve(workspace,x));if(!f.startsWith(privateRoot+path.sep))throw Error('Private evidence required');return f;}
function output(x){const f=path.resolve(workspace,x);if(!f.startsWith(privateRoot+path.sep))throw Error('Private output required');return f;}
const team=label=>label.match(/^([A-Z0-9]+) /)?.[1];
function choices(f){return f.toggles.map(t=>({team:team(t.label),checked:t.checked}));}
function signature(f){return JSON.stringify(choices(f));}
function matches(f){const a=choices(f),p=[];for(let i=0;i<a.length;i+=2)p.push(a.slice(i,i+2));return p;}
function result(f){const p=matches(f);return {quarterfinalists:p.slice(0,4).flat().map(x=>x.team),semifinalists:p.slice(4,6).flat().map(x=>x.team),champion:p.at(-1)?.find(x=>x.checked)?.team};}
function code(text){const raw=text.match(/https?:\/\/[^\s]+/)?.[0];if(!raw)throw Error('Actual copied URL unavailable');const url=new URL(raw),parts=url.searchParams.get('pick')?.split('_').map(x=>x.split('.'));if(url.searchParams.get('p')!=='pickem'||parts?.map(x=>x.length).join(',')!=='8,4,1')throw Error('Unexpected actual report encoding');return {url,quarterfinalists:parts[0],semifinalists:parts[1],champion:parts[2][0]};}
const equalSet=(a,b)=>a.length===b.length&&[...a].sort().join('|')===[...b].sort().join('|');
function reportMatches(a,b){return equalSet(a.quarterfinalists,b.quarterfinalists)&&equalSet(a.semifinalists,b.semifinalists)&&a.champion===b.champion;}
export {code as decodePredictionReport,result as predictionResult,reportMatches};
export function modelAffinityChecks(ax,runs){
  const facts=tournamentFacts(ax),own=result(facts);
  if(facts.toggles.length!==14||facts.toggles.filter(x=>x.checked).length!==7||!own.champion)throw Error('Completed actual knockout choices required');
  const rowPositions=new Map();
  const rows=runs.map(run=>{
    const escaped=run.name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    const shown=ax.match(new RegExp('link '+escaped+'\\s*八强(\\d+)·四强(\\d+) (\\d+), Value:'));
    if(!shown)throw Error('Actual model-affinity row unavailable: '+run.name);
    rowPositions.set(run.name,shown.index);
    const entries=Object.entries(run.summary.placement),qf=entries.filter(([,p])=>['QF','SF','RU','CHAMP'].includes(p)).map(([t])=>t),sf=entries.filter(([,p])=>['SF','RU','CHAMP'].includes(p)).map(([t])=>t);
    const q=own.quarterfinalists.filter(x=>qf.includes(x)).length,s=own.semifinalists.filter(x=>sf.includes(x)).length,total=q+2*s+5*Number(own.champion===run.summary.champion);
    return {name:run.name,expected:{qf:q,sf:s,total},actual:{qf:Number(shown[1]),sf:Number(shown[2]),total:Number(shown[3])},matches:q===Number(shown[1])&&s===Number(shown[2])&&total===Number(shown[3])};
  });
  const nearest=ax.match(/text 最像\s*\n(?:\s*\d+ container[^\n]*\n)?\s*\d+ text ([^\n]+)/)?.[1]?.trim();
  const best=ax.match(/text 按它的剧情结果对答案，这份能拿\s*\n\s*\d+ text (\d+)/)?.[1];
  const maximum=Math.max(...rows.map(x=>x.expected.total));
  const expectedOrder=[...rows].sort((a,b)=>b.expected.total-a.expected.total).map(x=>x.name);
  const actualOrder=[...rows].sort((a,b)=>rowPositions.get(a.name)-rowPositions.get(b.name)).map(x=>x.name);
  return {own,rows,nearest,best_score:Number(best),checks:{...Object.fromEntries(rows.map(x=>['affinity '+x.name,x.matches])),nearest_has_maximum_score:rows.some(x=>x.name===nearest&&x.expected.total===maximum),best_score_matches_actual_teams:Number(best)===maximum,affinity_order_matches_scores:JSON.stringify(actualOrder)===JSON.stringify(expectedOrder),nearest_matches_first_ranked_model:nearest===expectedOrder[0]}};
}
export function ownReportEndpoint(reportUrl,entryUrl){
  const report=new URL(reportUrl),entry=new URL(entryUrl);
  // The deployed static entry is served at both / and /index.html.
  const paths=entry.pathname==='/'?['/','/index.html']:[entry.pathname];
  return report.origin===entry.origin&&paths.includes(report.pathname);
}
export function friendReportChecks(importUrl,own,text){
  // The imported friend's URL can describe a different tournament from our report.
  const imported=code(importUrl),actual=text.match(/默契度 (\d+) \/ 21 分/);
  const expected=imported.quarterfinalists.filter(x=>own.quarterfinalists.includes(x)).length+2*imported.semifinalists.filter(x=>own.semifinalists.includes(x)).length+5*Number(imported.champion===own.champion);
  const shown=text.match(/冠军 ([A-Z0-9]+) · 四强 (.*?) · 八强 (.*?) （最像/);
  const shownReport=shown?{champion:shown[1],semifinalists:shown[2].split('/').map(x=>x.trim()),quarterfinalists:shown[3].split('/').map(x=>x.trim())}:null;
  return {score_matches:!!actual&&Number(actual[1])===expected,report_matches:!!shownReport&&reportMatches(imported,shownReport),champion:shown?.[1]||''};
}
function guard(ax,prep){
  if(!ax.includes('UUID='+prep.windowUuid))throw Error('Owned prediction window differs');
  const line=ax.split('\n').find(x=>x.includes('smart search field'))||'',value=line.match(/Value: (.*)$/)?.[1]?.split(/, (?:ID|Placeholder):/)[0]||'';
  const expected=new URL(prep.url),actual=new URL(value.includes('://')?value:expected.protocol+'//'+value);
  if(actual.origin!==expected.origin||actual.pathname!==expected.pathname||actual.search!==expected.search)throw Error('Actual prediction endpoint differs');
}
async function readMap(file,geometry){
  const raw=await fs.readFile(await input(file)),map=JSON.parse(raw),states={};
  for(const [id,state] of Object.entries(map.states)){
    const axFile=await input(state.ax),afterFile=await input(state.ax.replace(/\.ax\.txt$/,'.after.ax.txt'));
    const ax=await fs.readFile(axFile,'utf8'),after=await fs.readFile(afterFile,'utf8');guard(ax,map.preparation);guard(after,map.preparation);
    const facts=tournamentFacts(ax),afterFacts=tournamentFacts(after),image=await input(state.image);
    const elements=Object.fromEntries(Object.entries(facts.elements).filter(([k])=>k.startsWith('round ')||['round','reference','mode','nickname','visible_choices','selected_matches'].includes(k)));
    states[id]={facts,elements,interactions:{...facts.interactions},accessible_text:[],ax:rel(axFile),after_ax:rel(afterFile),image:rel(image),
      shared:sharedPredictionFacts(ax),capture:{...geometry,path:rel(image),state_consistent:JSON.stringify(facts)===JSON.stringify(afterFacts)},
      raw_sha256:{ax:hash(ax),after_ax:hash(after),image:hash(await fs.readFile(image))}};
  }
  return {states,preparation:map.preparation,raw_sha256:hash(raw)};
}
export function swissChecks(states){
  const checks={},draw=states['r1-draw'].facts,ids=choices(draw).map(x=>x.team),records=new Map(ids.map(x=>[x,{w:0,l:0}]));
  checks.initial_roster_unique=ids.length===16&&new Set(ids).size===16&&ids.every(Boolean);
  const pi=matches(states['pi-complete'].facts),qualifier=pi.at(-1).find(x=>x.checked)?.team;
  checks.playin_winner_enters_swiss=ids.includes(qualifier)&&choices(states['pi-draw'].facts).map(x=>x.team).filter(x=>x!==qualifier).every(x=>!ids.includes(x));
  const opponents=new Set();let grouped=true,active=true,notRepeated=true,validWinners=true;
  for(let r=1;r<=5;r++){
    const pairs=matches(states['r'+r+'-draw'].facts),done=matches(states['r'+r+'-complete'].facts),participants=pairs.flat().map(x=>x.team);
    active&&=equalSet(participants,[...records].filter(([,v])=>v.w<3&&v.l<3).map(([id])=>id));
    for(let i=0;i<pairs.length;i++){
      const pair=pairs[i],a=records.get(pair[0]?.team),b=records.get(pair[1]?.team);
      if(!a||!b){active=false;continue;}
      grouped&&=a.w===b.w&&a.l===b.l;
      const key=pair.map(x=>x.team).sort().join('|');notRepeated&&=!opponents.has(key);opponents.add(key);
      const selected=done[i]?.filter(x=>x.checked)||[];validWinners&&=selected.length===1&&pair.some(x=>x.team===selected[0]?.team);
      if(selected.length===1)for(const x of pair){const v=records.get(x.team);if(x.team===selected[0].team)v.w++;else v.l++;}
    }
  }
  checks.swiss_uses_active_teams_once=active;checks.swiss_pairs_same_record=grouped;
  checks.no_swiss_rematches_observed=notRepeated;checks.one_winner_per_match=validWinners;
  const qualified=[...records].filter(([,v])=>v.w===3).map(([id])=>id),ko=matches(states['ko-draw'].facts).slice(0,4);
  checks.eight_qualifiers_eight_eliminated=qualified.length===8&&[...records.values()].filter(v=>v.l===3).length===8;
  checks.knockout_uses_qualified_teams=equalSet(ko.flat().map(x=>x.team),qualified);
  const unbeaten=[...records].filter(([,v])=>v.w===3&&v.l===0).map(([id])=>id);
  const halves=unbeaten.map(id=>Math.floor(ko.findIndex(pair=>pair.some(x=>x.team===id))/2));
  checks.unbeaten_teams_in_opposite_halves=unbeaten.length===2&&halves[0]!==halves[1]&&halves.every(x=>x>=0);
  checks.unbeaten_teams_face_three_two=unbeaten.every(id=>{const pair=ko.find(p=>p.some(x=>x.team===id)),other=pair?.find(x=>x.team!==id);return other&&records.get(other.team)?.l===2;});
  const final=matches(states['ko-final-complete'].facts),winners=final.map(p=>p.find(x=>x.checked)?.team);
  checks.knockout_winners_feed_next_round=equalSet(final.slice(4,6).flat().map(x=>x.team),winners.slice(0,4))&&equalSet(final[6].map(x=>x.team),winners.slice(4,6))&&winners.every(Boolean);
  return checks;
}
async function observe(root,protocol){
  const directory=await input(root),geometry=protocol.capture;
  const main=await readMap(path.join(directory,'observed.json'),geometry),friend=await readMap(path.join(directory,'friend/observed.json'),geometry);
  const states=main.states,checks=swissChecks(states);
  let actionCount=0,policyValid=true,selectionApplied=true;
  for(const name of ['pi-complete',...Array.from({length:5},(_,i)=>'r'+(i+1)+'-complete'),'ko-qf-complete','ko-sf-complete','ko-final-complete']){
    const actions=JSON.parse(await fs.readFile(path.join(directory,name+'.actions.json'),'utf8'));
    for(const action of actions){
      const before=tournamentFacts(await fs.readFile(await input(action.before_ax),'utf8')),after=tournamentFacts(await fs.readFile(await input(action.after_ax),'utf8'));
      const chosen=team(action.chosen),pair=action.pair;
      policyValid&&=pair.length===2&&pair[0].label===action.chosen&&pair[0].probability>=pair[1].probability&&pair.every(p=>before.toggles.some(t=>t.label===p.label&&Number(t.label.match(/ (\d+(?:\.\d+)?)%/)?.[1])===p.probability));
      selectionApplied&&=choices(after).filter(x=>x.team===chosen&&x.checked).length===choices(before).filter(x=>x.team===chosen&&x.checked).length+1;
      actionCount++;
    }
  }
  states['ko-final-complete'].elements.recorded_ui_choices={value:String(actionCount)};
  states['ko-final-complete'].interactions={...states['ko-final-complete'].interactions,...checks,displayed_probability_policy_applied:policyValid,actual_ui_selection_applied:selectionApplied};
  const originals={pi:'pi-complete',r1:'r1-complete',r2:'r2-complete',r3:'r3-complete',r4:'r4-complete',r5:'r5-complete',ko:'ko-final-complete'};
  for(const [name,baseline] of Object.entries(originals))states['review-'+name].interactions.own_round_choices_retained=signature(states['review-'+name].facts)===signature(states[baseline].facts);
  for(const name of ['locked-reloaded','restored-preferred','restored-lock','locked-return','preferred-copied']){
    states[name].interactions.original_lock_time_retained=states[name].facts.lock_timestamp===states.locked.facts.lock_timestamp;
    states[name].interactions.original_final_choices_retained=signature(states[name].facts)===signature(states.locked.facts);
  }
  for(const [name,baseline] of [['locked-reset-attempt','locked-edit-attempt'],['edited-reloaded','after-restored-edit']])states[name].interactions.own_editor_choices_retained=signature(states[name].facts)===signature(states[baseline].facts);
  const preferred=code(await fs.readFile(path.join(directory,'preferred-report.txt'),'utf8')),copied=code(await fs.readFile(path.join(directory,'copied-report.txt'),'utf8'));
  for(const [name,report] of [['preferred-copied',preferred],['copied',copied]]){
    states[name].interactions.copied_report_matches_current_editor=reportMatches(report,result(states[name].facts));
    states[name].interactions.share_uses_own_endpoint=ownReportEndpoint(report.url,main.preparation.url);
  }
  for(const [name,state] of Object.entries(friend.states)){
    const own=result(state.facts),shared=state.shared,text=shared.accessible_text[0]||'';
    state.interactions={...state.interactions,...shared.interactions,own_editor_choices_retained:signature(state.facts)===signature(states['edited-reloaded'].facts)};
    if(shared.interactions.shared_prediction_visible){
      const checked=friendReportChecks(friend.preparation.url,own,text);
      state.interactions.friend_score_matches_observed_teams=checked.score_matches;
      state.accessible_text=[text.replace(/默契度 \d+ \/ 21 分/,'默契度 <actual own-team score> / 21 分')];
      state.interactions.friend_report_matches_copied_input=checked.report_matches;
      state.elements.friend_champion={value:checked.champion};
    }
    states['friend-'+name]=state;
  }
  return {states,preparation:main.preparation,source_observation_sha256:main.raw_sha256};
}
function freeze(source,protocol){
  if(new URL(source.preparation.url).origin!=='https://www.bilibili.com')throw Error('Actual original source required');
  const requirements=[];
  for(const [name,state] of Object.entries(source.states)){
    const evidence=[state.ax,state.after_ax];
    for(const [element,value] of Object.entries(state.elements))if('value' in value)requirements.push({id:name+'.'+element,state:name,kind:'element_value',element,value:value.value,evidence});else if('enabled' in value)requirements.push({id:name+'.'+element,state:name,kind:'element_boolean',element,field:'enabled',expected:value.enabled,evidence});
    for(const [field,value] of Object.entries(state.interactions))requirements.push({id:name+'.'+field,state:name,kind:'interaction_boolean',field,expected:value,evidence});
    state.accessible_text.forEach((text,i)=>requirements.push({id:name+'.text.'+i,state:name,kind:'accessible_text',text,evidence}));
    if(state.capture.state_consistent)requirements.push({id:name+'.pixels',state:name,kind:'image_pixels',reference_image:state.image,pixels:protocol.capture.content_rect_points.slice(2),reference_capture:state.capture,evidence:[state.image]});
    else requirements.push({id:name+'.pixels',state:name,kind:'pending',description:'Original state changed during capture; raw snapshot retained.',evidence});
  }
  return {schema_version:1,scope:protocol.scope,source_observation_sha256:source.source_observation_sha256,requirements};
}
async function main(){
const [mode,root,out]=process.argv.slice(2);if(!['freeze','observe'].includes(mode)||!root||!out)throw Error('Usage: tournament_evidence.mjs freeze|observe private-root private-output');
const protocol=JSON.parse(await fs.readFile(path.join(project,'prediction.json'),'utf8')).tournament,facts=await observe(root,protocol);
if(mode==='freeze'){const contract=freeze(facts,protocol),directory=output(out);await fs.mkdir(directory);await fs.writeFile(path.join(directory,'source.json'),JSON.stringify(facts));await fs.writeFile(path.join(directory,'contract.json'),JSON.stringify(contract));console.log(JSON.stringify({states:Object.keys(facts.states).length,requirements:contract.requirements.length}));}
else{await fs.writeFile(output(out),JSON.stringify(facts),{flag:'wx'});console.log(JSON.stringify({states:Object.keys(facts.states).length}));}
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await main();
