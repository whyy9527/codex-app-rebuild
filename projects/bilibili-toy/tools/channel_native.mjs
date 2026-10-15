// Shared desktop channel actions. Native CUA only; facts are not pass flags.
import {appScope,appScrollbars} from './mobile_native.mjs';

const normalize=value=>value.replace(/\s+/g,'').trim();
export function channelFacts(ax) {
  const scope=appScope(ax),lines=scope.split('\n'),texts=[];
  const partial=[],tables=[];let table=-1;
  for(let i=0;i<lines.length;i++) {
    const line=lines[i];
    if(/^\s*\d+ table(?: |$)/.test(line)) {
      table++;const depth=line.match(/^\s*/)[0].length;let rows=0;
      for(const child of lines.slice(i+1)) {
        if(/^\s*\d+ /.test(child)&&child.match(/^\s*/)[0].length<=depth)break;
        if(/^\s*\d+ row(?: |$)/.test(child))rows++;
      }
      tables.push({ordinal:table,observed_rows:rows,truncated:line.includes('(showing ')});
    }
    const range=line.match(/\d+ (\w+) \(showing (\d+)-(\d+) of (\d+) items\)/);
    if(range)partial.push({role:range[1],table_ordinal:table,start:+range[2],end:+range[3],total:+range[4]});
    const m=line.match(/^\s*\d+ (?:heading|text|button|link|checkbox|toggle button|cell|row|slider|pop up button)(?: \([^)]*\))? (.*)$/);
    if(!m)continue;
    let value=m[1];
    while(i+1<lines.length&&!/^\s*\d+ /.test(lines[i+1]))value+=' '+lines[++i].trim();
    if(/^(?:距真实开赛|\d{2}:\d{2}:\d{2})/.test(value))continue;
    if(value.startsWith('Value: ')){const comma=value.indexOf(', ');if(comma<0)continue;value=value.slice(comma+2);}
    else value=value.split(/, (?:Value|Help|ID):/)[0];
    if(value)texts.push(normalize(value));
  }
  const elements={};
  const model=scope.match(/\d+ text 模型 · ([^\n]+)/);
  if(model)elements.world={value:model[1].trim()};
  else {
    const player=scope.indexOf('container AI 模拟回放播放器');
    const world=scope.slice(player).match(/\d+ text AI 模拟\s+(.+?)\s+的世界/);
    if(player>=0&&world)elements.world={value:world[1].trim()};
  }
  const day=scope.match(/slider \(settable, float\) 比赛日, Value: ([^\n]+)/);
  if(day)elements.match_day={value:day[1].trim()};
  const interactions={};
  if(scope.includes('container AI 模拟回放播放器'))interactions.player_paused=/button\s+播放, Help:/.test(scope);
  const idle=scope.match(/checkbox 闲置 60 秒后自动换台, Value: (\w+)/);
  if(idle)interactions.idle_enabled=['1','on'].includes(idle[1]);
  return {accessible_text:[...new Set(texts)],elements,interactions,partial_ranges:partial,tables};
}

export function installChannelUI(app,fs,{url,output,windowUuid}) {
  const tree=()=>app.getAXState({emit:false,disableDiffing:true});
  function guard(ax) {
    if(!ax.includes('UUID='+windowUuid))throw Error('Owned desktop window changed');
    if(ax.includes('Description: Viewport Size,'))throw Error('Expected ordinary desktop viewport');
    const field=ax.split('\n').find(x=>x.includes('smart search field'))||'';
    const value=field.match(/Value: (.*)$/)?.[1]?.split(/, (?:ID|Placeholder):/)[0]||'';
    const expected=new URL(url),actual=new URL(value.includes('://')?value:expected.protocol+'//'+value);
    if(actual.origin!==expected.origin||actual.pathname!==expected.pathname||actual.search!==expected.search)throw Error('Desktop endpoint/share query changed');
  }
  async function ready(predicate) {
    const deadline=Date.now()+20000;
    do {const ax=await tree();if(ax.includes('link 跳到主要内容,')){guard(ax);if(predicate(ax)&&!/^\s*\d+ text (?:正在加载|加载中)/m.test(appScope(ax)))return ax;}}while(Date.now()<deadline);
    throw Error('Requested channel content did not become ready');
  }
  async function click(pattern,optional=false) {
    const ax=await tree();guard(ax);
    const line=ax.split('\n').find(x=>pattern.test(x));
    if(!line){if(optional)return;throw Error('Channel control missing: '+pattern);}
    await app.click(Number(line.trim().match(/^\d+/)[0]));const after=await tree();guard(after);return after;
  }
  async function top() {
    let ax=await tree();guard(ax);const count=appScrollbars(ax).length;
    for(let i=0;i<count;i++){await app.setValue(appScrollbars(ax)[i].index,'0');ax=await tree();guard(ax);}
    if(appScrollbars(ax).some(x=>x.value!=='0'))throw Error('Actual desktop scroll did not reset');
  }
  async function selectModel(label) {
    await click(/\d+ link 直播, Value:/);
    const escaped=label.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    await click(new RegExp('\\d+ link '+escaped+', Value:'));
    await ready(ax=>ax.includes('container AI 模拟回放播放器')&&channelFacts(ax).elements.world?.value===label);
    await click(/button\s+暂停, Help:/,true);
    await click(/checkbox 闲置 60 秒后自动换台, Value: (?:on|1)/,true);
    await click(/button 赛前$/);await click(/button 1x$/);await top();
  }
  async function prepare() {
    const ax=await tree();if(!ax.includes('UUID='+windowUuid))throw Error('Owned window changed');
    await app.pressKey('super+l');await app.paste(url);await app.pressKey('Return');
    await ready(ax=>/link Claude Opus 5\.5, Value:/.test(ax));
    await selectModel('Claude Opus 5.5');
  }
  async function navigate(label) {
    const before=await tree();guard(before);const signature=JSON.stringify(channelFacts(before).accessible_text);
    await click(new RegExp('\\d+ link '+label+', Value:'));
    await ready(ax=>JSON.stringify(channelFacts(ax).accessible_text)!==signature);
    await top();
  }
  async function collect(id) {
    if(!/^[a-z0-9-]+$/.test(id))throw Error('Invalid channel case identifier');
    await fs.mkdir(output,{recursive:true});
    const directory=output+'/'+id;await fs.mkdir(directory);
    const observations=[],union=new Set();let initial;
    for(let n=0;n<30;n++) {
      const ax=await tree();guard(ax);const facts=channelFacts(ax);
      if(facts.partial_ranges.some(x=>x.role!=='table'))throw Error('Non-table AX content omitted; capture unavailable');
      initial??=facts;
      if(JSON.stringify(facts.elements)!==JSON.stringify(initial.elements)||JSON.stringify(facts.interactions)!==JSON.stringify(initial.interactions))throw Error('Channel state changed while scrolling');
      const image=await app.getScreenshot({emit:false}),after=await tree();guard(after);
      const afterFacts=channelFacts(after);
      const stem=directory+'/'+String(n).padStart(2,'0');
      await fs.writeFile(stem+'.ax.txt',ax);await fs.writeFile(stem+'.after.ax.txt',after);
      const imagePath=stem+(image[0]===255?'.jpg':'.png');await fs.writeFile(imagePath,image);
      facts.accessible_text.forEach(x=>union.add(x));afterFacts.accessible_text.forEach(x=>union.add(x));
      const row={ax:stem+'.ax.txt',image:imagePath,facts,after_facts:afterFacts,
        scroll_values:appScrollbars(ax).map(x=>x.value),state_consistent:JSON.stringify(facts)===JSON.stringify(afterFacts)};
      observations.push(row);
      const tables=observations.flatMap(o=>[...o.facts.partial_ranges,...o.after_facts.partial_ranges]);
      const unfinished=tables.some(t=>!observations.some(o=>[o.facts,o.after_facts].some(f=>
        f.tables.some(x=>x.ordinal===t.table_ordinal&&!x.truncated&&x.observed_rows>0)||
        f.partial_ranges.some(x=>x.table_ordinal===t.table_ordinal&&x.start===0&&x.end===x.total&&x.total===t.total))));
      if(!unfinished)break;
      const bars=appScrollbars(after);
      if(bars.at(-1).value==='1')break;
      const area=after.split('\n').filter(x=>/^\s*\d+ scroll area$/.test(x)).at(-1);
      if(!area)throw Error('Application scroll area unavailable');
      await app.scroll(Number(area.trim().match(/^\d+/)[0]),'down',1);await tree();
    }
    const state={accessible_text:[...union],elements:initial.elements,interactions:initial.interactions,observations};
    await fs.writeFile(directory+'/observed.json',JSON.stringify(state));
    let existing={states:{},preparation:{url,windowUuid,viewport:'ordinary desktop; same native window'}};
    try{existing=JSON.parse(await fs.readFile(output+'/observed.json','utf8'));}catch(error){if(error.code!=='ENOENT')throw error;}
    if(existing.preparation.url!==url||existing.preparation.windowUuid!==windowUuid)throw Error('Existing channel preparation differs');
    existing.states[id]=state;await fs.writeFile(output+'/observed.json',JSON.stringify(existing));
    await top();return {id,texts:union.size,frames:observations.length,partial:observations.flatMap(x=>x.facts.partial_ranges)};
  }
  return {prepare,selectModel,navigate,collect,top,click};
}
