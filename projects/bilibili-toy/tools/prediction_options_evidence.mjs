import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {tournamentFacts} from './prediction_native.mjs';
import {swissChecks,ownReportEndpoint,decodePredictionReport,predictionResult,reportMatches} from './tournament_evidence.mjs';

const project=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),workspace=path.resolve(project,'../..');
const privateRoot=path.join(project,'private'),rel=x=>path.relative(workspace,x),hash=x=>createHash('sha256').update(x).digest('hex');
async function input(x){const f=await fs.realpath(path.resolve(workspace,x));if(!f.startsWith(privateRoot+path.sep))throw Error('Private input required');return f;}
function output(x){const f=path.resolve(workspace,x);if(!f.startsWith(privateRoot+path.sep))throw Error('Private output required');return f;}
const labels=['自定义实力排名','调整我的实力排名','取消','使用这份排名','导入它的排名','1x','2x','4x','开始模拟','暂停','继续','再模拟一届','直接看结果','显示全部轮次 →'];
const models=['隐藏分','Claude Opus 5.5','GPT-6.1 sol','Gemini 3.8','DeepSeek V4.1 Flash','Qwen3.8 Max','GLM-5.3','豆包','MiMo V2.6 Pro'];
export function predictionOptionsFacts(ax){
  const facts=tournamentFacts(ax),lines=ax.split('\n'),start=lines.findIndex(x=>/heading 我来预测, Value: 1/.test(x)),end=lines.findIndex((x,i)=>i>start&&/button 展开 AI 模拟速报/.test(x));
  if(start<0||end<0)throw Error('Complete prediction scope required');
  const scope=lines.slice(start,end).join('\n'),elements={mode:facts.elements.mode};
  for(const match of scope.matchAll(/^\s*\d+ pop up button (\(disabled\) )?(战队实力参考|导入来源), Value: (.*)$/gm)){
    elements[match[2]]={value:match[3]};elements[match[2]+' enabled']={enabled:!match[1]};
  }
  for(const match of scope.matchAll(/^\s*\d+ button (\([^)]*\) )?([^,\n]+)(?:, Secondary Actions:.*)?$/gm)){
    if(labels.includes(match[2])){elements['control '+match[2]]={enabled:match[1]!=='(disabled) '};if(match[1]&&/expanded|collapsed/.test(match[1]))elements['panel state']={value:match[1].trim()};}
  }
  const ranks=[...scope.matchAll(/^\s*\d+ text (\d+) ([A-Z0-9]+) ([A-Z]+)$/gm)].map(m=>({rank:+m[1],team:m[2],region:m[3]}));
  if(ranks.length&&ranks.length!==19)throw Error('Incomplete custom ranking');
  if(ranks.length){elements.ranking={value:ranks.map(x=>`${x.rank} ${x.team} ${x.region}`).join(' | ')};for(const m of scope.matchAll(/^\s*\d+ button (\(disabled\) )?([A-Z0-9]+ (?:上移|下移))$/gm))elements[m[2]]={enabled:!m[1]};}
  const menu=lines.slice(end).filter(x=>/^\s*\d+ (?:\(selected\) )?/.test(x)).map(x=>x.trim().replace(/^\d+ (?:\(selected\) )?/,'' )).filter(x=>models.includes(x));
  if(menu.length)elements.menu={value:menu.join(' | ')};
  const finalPair=facts.toggles.slice(-2);
  return {elements,ranks,facts,final_pair:finalPair.map(x=>({team:x.label.match(/^([A-Z0-9]+) /)?.[1],probability:Number(x.label.match(/ (\d+(?:\.\d+)?)%/)?.[1])})),interactions:{custom_editor_visible:ranks.length>0}};
}
function guard(ax,prep){
  if(!ax.includes('UUID='+prep.windowUuid))throw Error('Owned window differs');
  const value=ax.split('\n').find(x=>/smart search field/.test(x))?.match(/Value: (.*)$/)?.[1]?.split(/, (?:ID|Placeholder):/)[0];
  const expected=new URL(prep.url),actual=new URL(value?.includes('://')?value:expected.protocol+'//'+value);
  if(actual.origin!==expected.origin||actual.pathname!==expected.pathname||actual.search!==expected.search)throw Error('Actual endpoint differs');
}
const selection=f=>JSON.stringify(f.toggles.map(x=>({team:x.label.match(/^([A-Z0-9]+) /)?.[1],checked:x.checked})));
async function observe(root,protocol){
  const directory=await input(root),raw=await fs.readFile(path.join(directory,'observed.json')),map=JSON.parse(raw),states={};
  for(const [name,state] of Object.entries(map.states)){
    const axPath=await input(state.ax),afterPath=await input(state.ax.replace(/\.ax\.txt$/,'.after.ax.txt')),image=await input(state.image);
    const ax=await fs.readFile(axPath,'utf8'),after=await fs.readFile(afterPath,'utf8');guard(ax,map.preparation);guard(after,map.preparation);
    const parsed=predictionOptionsFacts(ax),later=predictionOptionsFacts(after);
    states[name]={...parsed,accessible_text:[],ax:rel(axPath),after_ax:rel(afterPath),image:rel(image),capture:{...protocol.capture,path:rel(image),state_consistent:JSON.stringify(parsed)===JSON.stringify(later)},raw_sha256:{ax:hash(ax),after_ax:hash(after),image:hash(await fs.readFile(image))}};
  }
  const initial=states['my-default'].facts;
  for(const [name,state] of Object.entries(states))if(state.elements.mode.value==='我的预测')state.interactions.own_prediction_choices_retained=selection(state.facts)===selection(initial);
  for(const [name,state] of Object.entries(states))if(name.startsWith('reference-')&&name!=='reference-menu'){
    const baseline=states['my-default'].final_pair;
    if(state.final_pair.length===2)for(const side of state.final_pair)state.elements['final probability '+side.team]={value:String(side.probability)};
    state.interactions.actual_probabilities_valid=state.facts.toggles.every(x=>Number.isFinite(Number(x.label.match(/ (\d+(?:\.\d+)?)%/)?.[1])));
    state.interactions.same_final_pair_retained=state.final_pair.map(x=>x.team).join('|')===baseline.map(x=>x.team).join('|');
  }
  const simulated={};
  for(const round of ['pi','r1','r2','r3','r4','r5','ko']){
    const state=states['simulation-result-'+round];simulated[round+'-draw']=simulated[round+'-complete']=state;
    state.elements.completed_matches={value:String(state.facts.toggles.length/2)};
    state.interactions.completed_readonly_results=state.facts.toggles.length>0&&state.facts.toggles.every(x=>!x.enabled)&&state.facts.toggles.filter(x=>x.checked).length===state.facts.toggles.length/2;
  }
  simulated['ko-final-complete']=states['simulation-result-ko'];
  states['simulation-result-ko'].interactions={...states['simulation-result-ko'].interactions,...swissChecks(simulated)};
  const report=decodePredictionReport(await fs.readFile(path.join(directory,'simulation-report.txt'),'utf8'));
  states['simulation-copied'].interactions.copied_simulation_matches_result=reportMatches(report,predictionResult(states['simulation-copied'].facts));
  states['simulation-copied'].interactions.share_uses_own_endpoint=ownReportEndpoint(report.url,map.preparation.url);
  return {states,preparation:map.preparation,raw_sha256:hash(raw),selection:map.selection??null};
}
function freeze(source,protocol){
  if(new URL(source.preparation.url).origin!=='https://www.bilibili.com')throw Error('Actual original required');
  const requirements=[];
  for(const [name,state] of Object.entries(source.states)){
    const evidence=[state.ax,state.after_ax];
    for(const [element,value] of Object.entries(state.elements))requirements.push('value' in value?{id:name+'.'+element,state:name,kind:'element_value',element,value:value.value,evidence}:{id:name+'.'+element,state:name,kind:'element_boolean',element,field:'enabled',expected:value.enabled,evidence});
    for(const [field,value] of Object.entries(state.interactions))requirements.push({id:name+'.'+field,state:name,kind:'interaction_boolean',field,expected:value,evidence});
    requirements.push(state.capture.state_consistent?{id:name+'.pixels',state:name,kind:'image_pixels',reference_image:state.image,pixels:protocol.capture.content_rect_points.slice(2),reference_capture:state.capture,evidence:[state.image]}:{id:name+'.pixels',state:name,kind:'pending',description:'Actual original state changed during capture; raw evidence retained.',evidence});
  }
  requirements.push({id:'simulation-speed-selection',state:'simulation-speed-4',kind:'pending',description:'Speed selection is visually indicated; AX does not expose selection. Timing and selected-style comparison remain separate acceptance.',evidence:[source.states['simulation-speed-2'].image,source.states['simulation-speed-4'].image]});
  return {schema_version:1,scope:protocol.scope,source_observation_sha256:source.raw_sha256,requirements};
}
async function main(){
  const [mode,root,out]=process.argv.slice(2);if(!['freeze','observe'].includes(mode)||!root||!out)throw Error('Usage: prediction_options_evidence.mjs freeze|observe private-root private-output');
  const protocol=JSON.parse(await fs.readFile(path.join(project,'prediction.json'),'utf8')).options,facts=await observe(root,protocol);
  if(mode==='freeze'){const contract=freeze(facts,protocol),directory=output(out);await fs.mkdir(directory);await fs.writeFile(path.join(directory,'source.json'),JSON.stringify(facts));await fs.writeFile(path.join(directory,'contract.json'),JSON.stringify(contract));console.log(JSON.stringify({states:Object.keys(facts.states).length,requirements:contract.requirements.length}));}
  else{await fs.writeFile(output(out),JSON.stringify(facts),{flag:'wx'});console.log(JSON.stringify({states:Object.keys(facts.states).length}));}
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await main();
