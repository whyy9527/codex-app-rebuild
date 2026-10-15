// Re-derive desktop-channel evidence from actual native AX captures.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {channelFacts} from './channel_native.mjs';

const project=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const workspace=path.resolve(project,'../..'),privateRoot=path.join(project,'private');
const hash=value=>createHash('sha256').update(value).digest('hex');
const relative=file=>path.relative(workspace,file);
async function input(value) {
  const file=await fs.realpath(path.resolve(workspace,value));
  if(!file.startsWith(privateRoot+path.sep))throw Error('Evidence must stay in project private');
  return file;
}
function output(value) {
  const file=path.resolve(workspace,value);
  if(!file.startsWith(privateRoot+path.sep))throw Error('Output must stay in project private');
  return file;
}
function guard(ax,prep) {
  if(!ax.includes('UUID='+prep.windowUuid)||ax.includes('Description: Viewport Size,'))throw Error('Desktop preparation changed');
  const field=ax.split('\n').find(x=>x.includes('smart search field'))||'';
  const value=field.match(/Value: (.*)$/)?.[1]?.split(/, (?:ID|Placeholder):/)[0]||'';
  const expected=new URL(prep.url),actual=new URL(value.includes('://')?value:expected.protocol+'//'+value);
  if(actual.origin!==expected.origin||actual.pathname!==expected.pathname||actual.search!==expected.search)throw Error('Actual endpoint or share query differs');
}
async function observe(value,protocol) {
  const raw=await fs.readFile(await input(value)),capture=JSON.parse(raw),states={};
  const expected=protocol.models.flatMap(m=>protocol.views.map(v=>m.id+'-'+v.id));
  if(expected.length!==Object.keys(capture.states).length||expected.some(id=>!capture.states[id]))throw Error('Every channel/view pair required');
  for(const [name,state] of Object.entries(capture.states)) {
    const texts=new Map(),snapshots=[];let initial;
    for(const observation of state.observations) {
      const axPath=await input(observation.ax),afterPath=await input(observation.ax.replace(/\.ax\.txt$/,'.after.ax.txt'));
      const before=await fs.readFile(axPath,'utf8'),after=await fs.readFile(afterPath,'utf8');
      guard(before,capture.preparation);guard(after,capture.preparation);
      const facts=channelFacts(before),afterFacts=channelFacts(after);
      for(const [data,file] of [[facts,axPath],[afterFacts,afterPath]]) {
        if(data.partial_ranges.some(x=>x.role!=='table'))throw Error('Non-table AX omission in '+name);
        initial??=data;
        if(JSON.stringify(initial.elements)!==JSON.stringify(data.elements)||JSON.stringify(initial.interactions)!==JSON.stringify(data.interactions))throw Error('World/day/control changed while scrolling '+name);
        for(const text of data.accessible_text)if(!texts.has(text))texts.set(text,relative(file));
      }
      const image=await input(observation.image),imageBytes=await fs.readFile(image);
      snapshots.push({facts,after_facts:afterFacts,ax:relative(axPath),after_ax:relative(afterPath),image:relative(image),
        capture:{...protocol.capture,path:relative(image),state_consistent:JSON.stringify(facts)===JSON.stringify(afterFacts)},
        raw_sha256:{ax:hash(before),after_ax:hash(after),image:hash(imageBytes)}});
    }
    if(!initial?.elements.world)throw Error('Actual selected world unavailable: '+name);
    const all=snapshots.flatMap(s=>[s.facts,s.after_facts]);
    const ordinals=[...new Set(all.flatMap(f=>f.tables.map(t=>t.ordinal)))];
    const elements={...initial.elements},tableEvidence={};
    for(const ordinal of ordinals) {
      const full=all.flatMap(f=>f.tables).filter(t=>t.ordinal===ordinal&&!t.truncated&&t.observed_rows>0);
      if(!full.length)throw Error('Complete native table structure not observed: '+name+'/'+ordinal);
      const counts=[...new Set(full.map(t=>t.observed_rows))];
      if(counts.length!==1)throw Error('Full table row count changed: '+name+'/'+ordinal);
      const key='table_'+ordinal+'_rows';elements[key]={value:String(counts[0])};
      tableEvidence[key]=snapshots.filter(s=>[s.facts,s.after_facts].some(f=>f.tables.some(t=>t.ordinal===ordinal&&!t.truncated&&t.observed_rows===counts[0]))).map(s=>s.ax);
    }
    states[name]={accessible_text:[...texts.keys()],text_evidence:Object.fromEntries(texts),elements,interactions:initial.interactions,
      snapshots,table_evidence:tableEvidence,capture:snapshots[0].capture};
  }
  return {states,preparation:capture.preparation,raw_observation_sha256:hash(raw)};
}
function freeze(source,protocol) {
  const url=new URL(source.preparation.url);
  if(url.origin!=='https://www.bilibili.com'||url.pathname!=='/toy/LkvCZhw12wgT2Pqx/index.html')throw Error('Original endpoint required');
  const requirements=[];
  for(const [name,state] of Object.entries(source.states)) {
    const evidence=[state.snapshots[0].ax];
    state.accessible_text.forEach((text,i)=>requirements.push({id:name+'.text.'+i,state:name,kind:'accessible_text',text,evidence:[state.text_evidence[text]]}));
    for(const [element,value] of Object.entries(state.elements))requirements.push({id:name+'.value.'+element,state:name,kind:'element_value',element,value:value.value,evidence:state.table_evidence[element]||evidence});
    for(const [field,value] of Object.entries(state.interactions))requirements.push({id:name+'.'+field,state:name,kind:'interaction_boolean',field,expected:value,evidence});
    if(state.capture.state_consistent)requirements.push({id:name+'.pixels',state:name,kind:'image_pixels',reference_image:state.snapshots[0].image,
      pixels:protocol.capture.content_rect_points.slice(2),reference_capture:state.capture,evidence:[state.snapshots[0].image]});
    else requirements.push({id:name+'.pixels',state:name,kind:'pending',description:'Original AX structure changed during screenshot acquisition; raw frame retained.',evidence});
  }
  return {schema_version:1,scope:protocol.scope,source_observation_sha256:source.raw_observation_sha256,requirements};
}
const [mode,observed,out]=process.argv.slice(2);
if(!['freeze','observe'].includes(mode)||!observed||!out)throw Error('Usage: channel_evidence.mjs freeze|observe observed.json private-output');
const protocol=JSON.parse(await fs.readFile(path.join(project,'journeys.json'),'utf8')).channels;
const facts=await observe(observed,protocol);
if(mode==='freeze') {
  const contract=freeze(facts,protocol),directory=output(out);await fs.mkdir(directory);
  await fs.writeFile(path.join(directory,'source.json'),JSON.stringify(facts));
  await fs.writeFile(path.join(directory,'contract.json'),JSON.stringify(contract));
  console.log(JSON.stringify({states:Object.keys(facts.states).length,requirements:contract.requirements.length}));
}else {
  await fs.writeFile(output(out),JSON.stringify(facts),{flag:'wx'});
  console.log(JSON.stringify({states:Object.keys(facts.states).length}));
}
