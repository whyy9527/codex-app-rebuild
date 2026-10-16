// Re-derive keyboard facts from actual AX exports; no browser or synthetic UI.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {playerFacts} from './mobile_native.mjs';

const project=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const workspace=path.resolve(project,'../..'),privateRoot=path.join(project,'private');
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
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
function endpoint(ax,prep) {
  if(!ax.includes('UUID='+prep.windowUuid))throw Error('Actual owned window differs');
  const field=ax.split('\n').find(x=>x.includes('smart search field'))||'';
  const value=field.match(/Value: (.*)$/)?.[1]?.split(/, (?:ID|Placeholder):/)[0]||'';
  const expected=new URL(prep.url),actual=new URL(value.includes('://')?value:expected.protocol+'//'+value);
  if(actual.origin!==expected.origin||actual.pathname!==expected.pathname||actual.search!==expected.search)throw Error('Actual endpoint or share query differs');
}
async function observe(value,geometry) {
  const raw=await fs.readFile(await input(value));
  const source=JSON.parse(raw),states={};
  const directory=path.dirname(await input(value));
  let visual={states:{}};
  try {visual=JSON.parse(await fs.readFile(path.join(directory,'visual-speed-observations.json'),'utf8'));}
  catch(error){if(error.code!=='ENOENT')throw error;}
  for(const [name,row] of Object.entries(source.states)) {
    const axFile=await input(row.ax),afterFile=await input(row.ax.replace(/\.ax\.txt$/,'.after.ax.txt'));
    const ax=await fs.readFile(axFile,'utf8'),after=await fs.readFile(afterFile,'utf8');
    endpoint(ax,source.preparation);endpoint(after,source.preparation);
    const beforeFacts=playerFacts(ax),afterFacts=playerFacts(after);
    const image=await input(row.image),imageBytes=await fs.readFile(image);
    if(visual.states[name]) {
      if(visual.states[name].image_sha256!==hash(imageBytes))throw Error('Visual label belongs to another image');
      beforeFacts.elements.visual_speed={value:visual.states[name].label};
      afterFacts.elements.visual_speed={value:visual.states[name].label};
    }
    const stateConsistent=JSON.stringify(beforeFacts)===JSON.stringify(afterFacts);
    const state={...beforeFacts,after_facts:afterFacts,ax:relative(axFile),image:relative(image),
      capture:{...geometry,path:relative(image),state_consistent:stateConsistent},
      raw_sha256:{ax:hash(ax),after_ax:hash(after),image:hash(imageBytes)}};
    try {
      const action=JSON.parse(await fs.readFile(path.join(directory,name+'.action.json'),'utf8'));
      if(!(action.before_unix_ms<=action.after_unix_ms))throw Error('Invalid actual action interval');
      state.elements.actual_key={value:action.key};state.action=action;
    }catch(error){if(error.code!=='ENOENT')throw error;}
    states[name]=state;
  }
  return {states,preparation:source.preparation,raw_observation_sha256:hash(raw)};
}
function freeze(source,protocol) {
  const url=new URL(source.preparation.url);
  if(url.origin!=='https://www.bilibili.com'||url.pathname!=='/toy/LkvCZhw12wgT2Pqx/index.html')throw Error('Original source endpoint required');
  for(const step of protocol.steps) {
    if(source.states[step.id]?.action?.key!==step.key)throw Error('Original key action missing: '+step.id);
  }
  const requirements=[];
  for(const [name,state] of Object.entries(source.states)) {
    const evidence=[state.ax,state.ax.replace(/\.ax\.txt$/,'.after.ax.txt')];
    const pending=(field,description)=>requirements.push({id:name+'.'+field,state:name,kind:'pending',description,evidence});
    for(const [element,value] of Object.entries(state.elements)) {
      if(element!=='actual_key'&&JSON.stringify(value)!==JSON.stringify(state.after_facts.elements[element])) {
        pending('value.'+element,'Original element changed during screenshot capture: '+element);continue;
      }
      requirements.push({id:name+'.value.'+element,state:name,kind:'element_value',element,value:value.value,evidence});
    }
    for(const [field,value] of Object.entries(state.interactions)) {
      if(value!==state.after_facts.interactions[field]) {pending(field,'Original control changed during screenshot capture: '+field);continue;}
      requirements.push({id:name+'.'+field,state:name,kind:'interaction_boolean',field,expected:value,evidence});
    }
    if(JSON.stringify(state.accessible_text)===JSON.stringify(state.after_facts.accessible_text)) {
      state.accessible_text.forEach((text,i)=>requirements.push({id:name+'.text.'+i,state:name,kind:'accessible_text',text,evidence}));
    }else pending('timeline-text','Original playback timeline text changed during screenshot acquisition; raw snapshots retained.');
    if(state.capture.state_consistent)requirements.push({id:name+'.pixels',state:name,kind:'image_pixels',
      reference_image:state.image,pixels:protocol.capture.content_rect_points.slice(2),reference_capture:state.capture,evidence:[state.image]});
    else pending('pixels','Original capture changed during acquisition; no comparable frozen image.');
  }
  return {schema_version:1,scope:protocol.scope,source_observation_sha256:source.raw_observation_sha256,requirements};
}
const [mode,observed,out]=process.argv.slice(2);
if(!['freeze','observe'].includes(mode)||!observed||!out)throw Error('Usage: keyboard_evidence.mjs freeze|observe observed.json private-output');
const protocol=JSON.parse(await fs.readFile(path.join(project,'journeys.json'),'utf8')).keyboard;
const geometry=Object.fromEntries(['content_rect_points','backing_scale','window_points'].map(k=>[k,protocol.capture[k]]));
const facts=await observe(observed,geometry);
if(mode==='freeze') {
  const contract=freeze(facts,protocol),directory=output(out);
  await fs.mkdir(directory,{recursive:false});
  await fs.writeFile(path.join(directory,'source.json'),JSON.stringify(facts,null,2));
  await fs.writeFile(path.join(directory,'contract.json'),JSON.stringify(contract,null,2));
  console.log(JSON.stringify({states:Object.keys(facts.states).length,requirements:contract.requirements.length}));
}else {
  await fs.writeFile(output(out),JSON.stringify(facts,null,2),{flag:'wx'});
  console.log(JSON.stringify({states:Object.keys(facts.states).length}));
}
