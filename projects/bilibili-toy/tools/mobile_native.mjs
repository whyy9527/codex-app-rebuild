// Shared responsive-web observation actions, executed only through CUA.
export function appScope(ax) {
  const lines=ax.split('\n'), start=lines.findIndex(x=>/^\s*\d+ link 跳到主要内容,/.test(x));
  if(start<0)throw Error('Application content boundary unavailable');
  const indent=lines[start].match(/^\s*/)[0].length, output=[];
  let excludedDepth=null;
  for(const line of lines.slice(start)) {
    const numbered=/^\s*\d+ /.test(line), depth=line.match(/^\s*/)[0].length;
    if(numbered&&depth<indent)break;
    if(excludedDepth!==null&&numbered&&depth<=excludedDepth)excludedDepth=null;
    if(/container .* · AI 区新人 UP · 资深 LOL 观众/.test(line)){excludedDepth=depth;continue;}
    if(excludedDepth===null)output.push(line);
  }
  return output.join('\n');
}
export function appScrollbars(ax) {
  const lines=ax.split('\n'), start=lines.findIndex(x=>/^\s*\d+ link 跳到主要内容,/.test(x));
  if(start<0)throw Error('Application scroll boundary unavailable');
  const parent=lines.slice(0,start).findLastIndex(x=>/^\s*\d+ scroll area$/.test(x));
  if(parent<0)throw Error('Application scroll area unavailable');
  const depth=lines[parent].match(/^\s*/)[0].length, bars=[];
  for(const line of lines.slice(parent+1)) {
    const indent=line.match(/^\s*/)[0].length;
    if(/^\s*\d+ /.test(line)&&indent<=depth)break;
    const m=line.match(/^\s*(\d+) scroll bar \(settable, float\) ([0-9.]+)$/);
    if(m)bars.push({index:Number(m[1]),value:m[2],depth:indent});
  }
  const outer=bars.filter(bar=>bar.depth===Math.min(...bars.map(x=>x.depth)));
  if(outer.length<1||outer.length>2)throw Error('Application scrollbars unavailable or ambiguous');
  return outer;
}
export function mobileFacts(ax) {
  const scope=appScope(ax), lines=scope.split('\n');
  const normalized=value=>value.replace(/\s+/g,'').trim();
  const heads=[...scope.matchAll(/\d+ heading (.*?), Value: (\d+)/g)].map(m=>normalized(m[1]));
  const elements={};
  for(const label of ['Width','Height','Zoom Level','Pixel Ratio']) {
    const line=ax.split('\n').find(x=>x.includes('Description: '+label+','));
    const value=line?.match(/Value: (.*)$/)?.[1];
    if(value===undefined)throw Error('Responsive viewport measurement unavailable: '+label);
    elements[label]={value:value.trim()};
  }
  const selector=scope.match(/pop up button 选择 AI 频道, Value: ([^\n]*)/);
  if(selector)elements.model={value:selector[1]};
  const scrollValues=appScrollbars(ax).map(x=>x.value);
  const interactions={at_scroll_origin:scrollValues.every(x=>x==='0')};
  if(scope.includes('container AI 模拟回放播放器'))interactions.player_paused=/button 播放, Help:/.test(scope);
  const idle=scope.match(/checkbox 闲置 60 秒后自动换台, Value: (\w+)/);
  if(idle)interactions.idle_enabled=['1','on'].includes(idle[1]);
  const text=lines.flatMap(line=>{
    const m=line.match(/^\s*\d+ (?:heading|text|button|link|checkbox|pop up button) (.*)$/);
    if(!m||/^(?:距真实开赛|\d{2}:\d{2}:\d{2})/.test(m[1]))return [];
    let value=m[1];
    if(value.startsWith('Value: ')){const comma=value.indexOf(', ');return comma<0?[]:[normalized(value.slice(comma+2))];}
    value=value.split(/, (?:Value|Help|ID):/)[0];
    return [normalized(value)];
  });
  return {accessible_text:[...new Set([...heads,...text])].filter(Boolean),elements,interactions,headings:heads,scroll_values:scrollValues};
}
export function playerFacts(ax) {
  const lines=ax.split('\n'),start=lines.findIndex(x=>/\d+ container AI 模拟回放播放器$/.test(x));
  if(start<0)throw Error('Player boundary unavailable');
  const depth=lines[start].match(/^\s*/)[0].length,scope=[];
  for(const line of lines.slice(start+1)) {
    if(/^\s*\d+ /.test(line)&&line.match(/^\s*/)[0].length<=depth)break;
    scope.push(line);
  }
  const text=scope.flatMap(line=>{
    const match=line.match(/^\s*\d+ (?:text|button|checkbox|toggle button) (.*?)(?:, (?:Value|Help|ID):|$)/);
    return match?[match[1].trim()]:[];
  });
  const focusDetail=ax.match(/The focused UI element is \d+ ([^\n]+)/)?.[1]||'unavailable';
  const focus=focusDetail.startsWith('HTML content')?'HTML content':focusDetail.split(/, (?:Value|Help|ID):/)[0];
  const mobile=mobileFacts(ax);
  return {accessible_text:[...new Set(text)],elements:{...mobile.elements,focus:{value:focus}},
    interactions:{player_paused:scope.some(x=>/button 播放, Help:/.test(x)),
      sound_enabled:scope.some(x=>/button 静音, Help:/.test(x)),
      idle_enabled:mobile.interactions.idle_enabled},focus_detail:focusDetail};
}
export function installMobileUI(app,fs,{url,output,windowUuid,width=375,height=667}) {
  const states={};
  const tree=()=>app.getAXState({emit:false,disableDiffing:true});
  async function readyPlayer(label) {
    const deadline=Date.now()+20000;
    do {
      const ax=await tree();
      if(ax.includes('container AI 模拟回放播放器')&&ax.includes('button 赛前')&&
         ax.includes('pop up button 选择 AI 频道, Value: '+label)){guard(ax);return ax;}
    } while(Date.now()<deadline);
    throw Error('Responsive player did not become ready: '+label);
  }
  function guard(ax) {
    if(!ax.includes('UUID='+windowUuid))throw Error('Owned responsive window changed');
    const field=ax.split('\n').find(x=>x.includes('smart search field'))||'';
    const value=field.match(/Value: (.*)$/)?.[1]?.split(/, (?:ID|Placeholder):/)[0]||'';
    const expected=new URL(url),actual=new URL(value.includes('://')?value:expected.protocol+'//'+value);
    if(actual.origin!==expected.origin||actual.pathname!==expected.pathname||actual.search!==expected.search)throw Error('Responsive endpoint or share query changed');
    const facts=mobileFacts(ax);
    if(facts.elements.Width.value!==String(width)||facts.elements.Height.value!==String(height))throw Error('Responsive viewport changed');
  }
  async function click(pattern,optional=false) {
    let ax=await tree();guard(ax);const line=ax.split('\n').find(x=>pattern.test(x));
    if(!line){if(optional)return ax;throw Error('Mobile control missing: '+pattern);}
    await app.click(Number(line.trim().match(/^\d+/)[0]));ax=await tree();guard(ax);return ax;
  }
  async function capture(id,{player=false}={}) {
    if(!/^[a-z0-9-]+$/.test(id))throw Error('Invalid capture identifier');
    try {
      const existing=JSON.parse(await fs.readFile(output+'/observed.json','utf8'));
      if(existing.preparation.url!==url||existing.preparation.windowUuid!==windowUuid||existing.preparation.width!==width||existing.preparation.height!==height)throw Error('Existing capture preparation differs');
      Object.assign(states,existing.states);
    } catch(error) {if(error.code!=='ENOENT')throw error;}
    try{await fs.access(output+'/'+id+'.ax.txt');throw Error('Capture already exists: '+id);}catch(error){if(error.code!=='ENOENT')throw error;}
    const ax=await tree();guard(ax);
    const bytes=await app.getScreenshot({emit:false});
    const after=await tree();guard(after);
    const extract=player?playerFacts:mobileFacts;
    const facts=extract(ax),afterFacts=extract(after);
    const stateConsistent=JSON.stringify(facts)===JSON.stringify(afterFacts);
    if(!stateConsistent&&!player)throw Error('Mobile state changed during capture');
    await fs.mkdir(output,{recursive:true});
    const stem=output+'/'+id;await fs.writeFile(stem+'.ax.txt',ax);await fs.writeFile(stem+'.after.ax.txt',after);
    const image=stem+(bytes[0]===255?'.jpg':'.png');await fs.writeFile(image,bytes);
    states[id]={...facts,ax:stem+'.ax.txt',image,observed_at_unix_ms:Date.now(),state_consistent:stateConsistent};
    await fs.writeFile(output+'/observed.json',JSON.stringify({states,preparation:{url,windowUuid,width,height,user_agent:'Safari default; Android UA triggers original platform App gate, observed separately'}},null,2));
    return {id,headings:facts.headings,model:facts.elements.model?.value,bytes};
  }
  async function pausedIntro() {
    await click(/button 暂停, Help:/,true);
    await click(/checkbox 闲置 60 秒后自动换台, Value: (?:on|1)/,true);
    await click(/button 赛前$/);
    await click(/button 1x$/);
    return top();
  }
  async function top() {
    const initial=await tree();guard(initial);
    for(let i=0;i<appScrollbars(initial).length;i++) {
      const ax=await tree();guard(ax);
      await app.setValue(appScrollbars(ax)[i].index,'0');
      const after=await tree();guard(after);
      if(appScrollbars(after)[i].value!=='0')throw Error('Application scroll did not reset');
    }
    return tree();
  }
  async function selectModel(label,{prepare=true}={}) {
    const before=await tree();guard(before);
    const selector=before.split('\n').find(x=>/pop up button 选择 AI 频道, Value:/.test(x));
    if(!selector)throw Error('Mobile native AI selector unavailable');
    await app.click(Number(selector.trim().match(/^\d+/)[0]));
    const menu=await tree();
    const options=menu.split('\n').filter(x=>/^\s*\d+ (?:\(selected\) )?[^,\n]+$/.test(x));
    const selected=options.find(x=>x.replace(/^\s*\d+ (?:\(selected\) )?/,'')===label);
    if(!selected)throw Error('Observed model option unavailable: '+label);
    await app.click(Number(selected.trim().match(/^\d+/)[0]));
    await readyPlayer(label);
    return prepare?pausedIntro():tree();
  }
  async function navigate(label,id) {
    const pattern=new RegExp('\\d+ link '+label+', Value:');
    await click(pattern);await top();return capture(id);
  }
  async function prepare() {
    const before=await tree();if(!before.includes('UUID='+windowUuid))throw Error('Owned window changed before preparation');
    await app.pressKey('super+l');await app.paste(url);await app.pressKey('Return');
    const deadline=Date.now()+20000;
    do {const ax=await tree();if(ax.includes('选择 AI 频道')){guard(ax);return selectModel('Claude Opus 5.5');}} while(Date.now()<deadline);
    throw Error('Responsive application did not become ready');
  }
  async function focusPlayer() {
    const ax=await click(/text 播放器区域获得焦点后：/);
    if(!/The focused UI element is \d+ container AI 模拟回放播放器/.test(ax))throw Error('Actual player keyboard focus unavailable');
    return ax;
  }
  async function key(key,id) {
    if(!/^[a-z0-9-]+$/.test(id))throw Error('Invalid capture identifier');
    try{await fs.access(output+'/'+id+'.action.json');throw Error('Key action already exists: '+id);}catch(error){if(error.code!=='ENOENT')throw error;}
    const before=await tree();guard(before);
    const beforeUnixMs=Date.now();await app.pressKey(key);
    const after=await tree();guard(after);
    await fs.mkdir(output,{recursive:true});
    await fs.writeFile(output+'/'+id+'.action.json',JSON.stringify({key,before_unix_ms:beforeUnixMs,after_unix_ms:Date.now(),
      before_focus:playerFacts(before).elements.focus.value,after_focus:playerFacts(after).elements.focus.value}),{flag:'wx'});
    return capture(id,{player:true});
  }
  return {prepare,capture,selectModel,navigate,click,top,focusPlayer,key};
}
