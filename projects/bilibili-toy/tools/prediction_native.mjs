// Shared Safari/native prediction actions. The comparator owns assertions.
export function predictionFacts(ax) {
  const lines = ax.split('\n');
  const start = lines.findIndex(s => /heading 我来预测, Value: 1/.test(s));
  const end = lines.findIndex((s, i) => i > start && /button 展开 AI 模拟速报/.test(s));
  if (start < 0 || end < 0) throw Error('Prediction content scope unavailable');
  const accessible_text = [], elements = {}, occurrences = {};
  for (const line of lines.slice(start, end)) {
    const text = line.match(/^\s*\d+ (?:heading|text|button(?: \(disabled\))?|toggle button) (.*?)(?:, Value:|, Help:|, Secondary Actions:|$)/);
    if (text) accessible_text.push(text[1].trim());
    const toggle = line.match(/toggle button (.*?), Value: (on|off|1|0)$/);
    if (toggle) {
      const count = occurrences[toggle[1]] = (occurrences[toggle[1]] || 0) + 1;
      elements[toggle[1] + ' [' + count + ']'] = {role: 'button', checked: /^(on|1)$/.test(toggle[2])};
    }
    const round = line.match(/button (\(disabled\) )?([1-7] .*)$/);
    if (round) elements[round[2]] = {role: 'button', enabled: !round[1]};
  }
  return {accessible_text, elements};
}

export function sharedPredictionFacts(ax) {
  const lines = ax.split('\n');
  const start = lines.findIndex(s => /container 好友预测战帖$/.test(s));
  const accessible_text = [];
  if (start >= 0) {
    const indent = lines[start].match(/^\s*/)[0].length;
    for (const line of lines.slice(start + 1)) {
      if (line.match(/^\s*/)[0].length <= indent) break;
      const text = line.match(/^\s*\d+ (?:text|button) (.*?)(?:, Value:|, Help:|$)/);
      if (text) accessible_text.push(text[1].trim());
    }
  }
  // Inline SVG loading can split one sentence into several AX text nodes.
  // Preserve every word in order while comparing the whole observed section.
  return {accessible_text: accessible_text.length ? [accessible_text.join(' ').replace(/\s+/g, ' ')] : [],
    elements: {}, interactions: {shared_prediction_visible: start >= 0}};
}

export function finalPredictionFacts(ax) {
  const lines = ax.split('\n');
  const championAt = lines.findIndex(s => /text 我的冠军$/.test(s));
  const champion = championAt < 0 ? null : lines.slice(championAt + 1, championAt + 6)
    .map(s => s.match(/text ([A-Z0-9]+)$/)?.[1]).find(Boolean);
  const lockedAt = lines.findIndex(s => /text 已锁定 ·/.test(s));
  const timestamp = lockedAt < 0 ? null : lines.slice(lockedAt + 1, lockedAt + 4)
    .map(s => s.match(/text (\d{4}\/\d+\/\d+ .*?)$/)?.[1]).find(Boolean);
  const choices = lines.flatMap(s => {
    const match = s.match(/toggle button (.*?), Value: (on|off|1|0)$/);
    return match ? [{label: match[1], checked: /^(on|1)$/.test(match[2])}] : [];
  });
  return {accessible_text: champion ? ['我的冠军 ' + champion] : [],
    elements: {champion: {role: 'text', value: champion || ''},
      selected_matches: {value: String(choices.filter(e => e.checked).length)},
      match_choices: {value: String(choices.length)}},
    interactions: {final_result_visible: !!champion, prediction_locked: lockedAt >= 0,
      copy_succeeded: ax.includes('text 已复制预测战报口令')},
    lock_signature: JSON.stringify({champion, timestamp, choices}), lock_timestamp: timestamp};
}

export function installPredictionE2E(app, fs, bridge) {
  const tree = () => app.getAXState({emit: false, disableDiffing: true});
  function guard(ax, req) {
    const address = ax.split('\n').find(s => /smart search field|Address and search bar/.test(s)) || '';
    const value = address.match(/Value: ([^,\n]*)/)?.[1];
    const expected = new URL(req.url);
    let actual;
    try { actual = new URL(value.includes('://') ? value : expected.protocol + '//' + value); } catch {}
    if (actual?.origin !== expected.origin || actual?.pathname !== expected.pathname) {
      throw Error('Requested prediction endpoint is no longer selected');
    }
  }
  return async function servicePrediction() {
    for (const name of (await fs.readdir(bridge)).filter(n => n.endsWith('.request.json')).sort()) {
      const req = JSON.parse(await fs.readFile(bridge + '/' + name, 'utf8'));
      if (req.suite !== 'prediction') continue;
      const reply = bridge + '/' + req.id + '.reply.json';
      try { await fs.access(reply); continue; } catch {}
      const states = {}, actions = [];
      try {
        await app.pressKey('super+l'); await app.paste(req.url + '?p=pickem'); await app.pressKey('Return');
        let ax;
        for (let i = 0; i < 10; i++) {
          ax = await tree();
          if (ax.includes('heading 我来预测, Value: 1')) break;
        }
        guard(ax, req);
        if (req.cases.some(item => item.id === 'playin') && !/button 揭晓对阵/.test(ax)) {
          throw Error('Empty prediction prestate required; existing drafts are not reset by the driver');
        }
        for (const item of req.cases) {
          const collect = item.id === 'share' ? sharedPredictionFacts : item.id === 'locked' ? finalPredictionFacts : predictionFacts;
          if (item.query) {
            await app.pressKey('super+l'); await app.paste(req.url + item.query); await app.pressKey('Return');
            for (let i = 0; i < 10; i++) { ax = await tree(); if (ax.includes('heading 我来预测, Value: 1')) break; }
            guard(ax, req);
          }
          if (item.id === 'share') {
            const reveal = ax.split('\n').find(s => /button 揭晓对阵$/.test(s));
            if (reveal) { await app.click(Number(reveal.trim().match(/^\d+/)[0])); ax = await tree(); guard(ax, req); }
            const draft = predictionFacts(ax);
            if (Object.values(draft.elements).some(e => e.checked) || ax.includes('text 已锁定')) {
              throw Error('Shared-link comparison requires unselected PI draft; existing predictions are preserved');
            }
          }
          const lockedBaseline = item.id === 'locked' ? finalPredictionFacts(ax) : null;
          if (lockedBaseline && (!lockedBaseline.interactions.prediction_locked || !lockedBaseline.lock_timestamp)) {
            throw Error('Final lock verification requires an already locked test prediction');
          }
          for (const step of item.steps) {
            ax = await tree(); guard(ax, req);
            if (step.action === 'click') {
              const line = ax.split('\n').find(s => new RegExp(step.match).test(s));
              if (!line) throw Error('Prediction control absent: ' + step.match);
              await app.click(Number(line.trim().match(/^\d+/)[0]));
            } else if (step.action === 'reload') await app.pressKey('super+r');
            else if (step.action === 'scroll_top') {
              const frame = ax.split('\n').find(s => /HTML content .*#\/pickem(?:$|\?)/.test(s));
              if (!frame) throw Error('Prediction frame scroll target unavailable');
              await app.scroll(Number(frame.trim().match(/^\d+/)[0]), 'up', 20);
            } else if (step.action !== 'capture') throw Error('Unknown prediction action');
            ax = await tree(); guard(ax, req);
            if (step.action === 'reload') {
              for (let i = 0; i < 10 && !ax.includes('heading 我来预测, Value: 1'); i++) ax = await tree();
              guard(ax, req);
            }
            actions.push({case: item.id, ...step, attempted: true});
            if (step.capture) {
              const state = collect(ax);
              if (lockedBaseline) state.interactions.locked_prediction_retained = state.lock_signature === lockedBaseline.lock_signature;
              const bytes = await app.getScreenshot({emit: false});
              const extension = bytes[0] === 255 && bytes[1] === 216 ? 'jpg' : 'png';
              const image = req.workspace + '/' + step.capture + '.' + extension;
              const axPath = req.workspace + '/' + step.capture + '.ax.txt';
              await fs.writeFile(image, bytes); await fs.writeFile(axPath, ax);
              const after = await tree(); guard(after, req);
              const afterState = collect(after);
              if (lockedBaseline) afterState.interactions.locked_prediction_retained = afterState.lock_signature === lockedBaseline.lock_signature;
              states[step.capture] = {...state, image, ax: axPath,
                state_consistent: JSON.stringify(state) === JSON.stringify(afterState)};
            }
          }
        }
        await fs.writeFile(reply, JSON.stringify({states, actions, preparation: 'Play-in requires empty draft; shared link requires unselected official PI draw. Same clicks and reload on both endpoints. Existing drafts are never cleared.'}));
        return {endpoint: req.endpoint, states: Object.keys(states)};
      } catch (error) {
        await fs.writeFile(reply, JSON.stringify({states, actions, error: String(error)}));
        throw error;
      }
    }
    return {pending: false};
  };
}

// Full tournament traversal keeps random brackets as actual observed data.
// The shared policy reads displayed probabilities, without injecting a seed.
export function tournamentFacts(ax) {
  const base=predictionFacts(ax),lines=ax.split('\n');
  const start=lines.findIndex(x=>/heading 我来预测, Value: 1/.test(x));
  const end=lines.findIndex((x,i)=>i>start&&/button 展开 AI 模拟速报/.test(x));
  const scope=lines.slice(start,end).join('\n');
  if(/\(showing \d+-\d+ of \d+ items\)/.test(scope))throw Error('Prediction AX content is incomplete');
  const toggles=[...scope.matchAll(/^\s*(\d+) toggle button (\(disabled\) )?(.*?), Value: (on|off|1|0)$/gm)].map(m=>({index:+m[1],label:m[3],checked:/^(on|1)$/.test(m[4]),enabled:!m[2]}));
  const heading=scope.match(/heading (.*?), Value: 3/);
  const reference=scope.match(/pop up button 战队实力参考, Value: ([^\n]+)/);
  const tab=scope.match(/tab \(selected\) ([^\n]+)/);
  const nickname=scope.match(/text field (?:\([^)]*\) )?海报昵称, Value: ([^,\n]*)/);
  const roundControls={};
  for(const match of scope.matchAll(/^\s*\d+ button (\(disabled\) )?(?:[1-7] )?(入围赛|第 [1-5] 轮|淘汰赛)$/gm))roundControls['round '+match[2]]={role:'button',enabled:!match[1]};
  const finals=finalPredictionFacts(ax);
  return {...base,elements:{...base.elements,...roundControls,round:{value:heading?.[1]||''},reference:{value:reference?.[1]||''},nickname:{value:nickname?.[1]||''},
      mode:{value:tab?.[1]||''},visible_choices:{value:String(toggles.length)},selected_matches:{value:String(toggles.filter(x=>x.checked).length)}},
    interactions:{prediction_locked:finals.interactions.prediction_locked,copy_succeeded:finals.interactions.copy_succeeded},
    toggles,lock_timestamp:finals.lock_timestamp,champion:finals.elements.champion.value};
}

export function installTournamentUI(app,fs,{url,output,windowUuid}) {
  const tree=()=>app.getAXState({emit:false,disableDiffing:true});
  function guard(ax) {
    if(!ax.includes('UUID='+windowUuid))throw Error('Owned prediction window changed');
    const field=ax.split('\n').find(x=>x.includes('smart search field'))||'';
    const value=field.match(/Value: (.*)$/)?.[1]?.split(/, (?:ID|Placeholder):/)[0]||'';
    const expected=new URL(url),actual=new URL(value.includes('://')?value:expected.protocol+'//'+value);
    if(actual.origin!==expected.origin||actual.pathname!==expected.pathname||actual.search!==expected.search)throw Error('Prediction endpoint/share query changed');
  }
  async function ready() {
    const deadline=Date.now()+20000;
    do{const ax=await tree();guard(ax);if(ax.includes('heading 我来预测, Value: 1')&&ax.includes('button 展开 AI 模拟速报'))return ax;}while(Date.now()<deadline);
    throw Error('Prediction did not become ready');
  }
  async function click(pattern) {
    const ax=await tree();guard(ax);const line=ax.split('\n').find(x=>pattern.test(x));
    if(!line)throw Error('Prediction control missing: '+pattern);
    await app.click(Number(line.trim().match(/^\d+/)[0]));const after=await tree();guard(after);return after;
  }
  async function capture(id) {
    if(!/^[a-z0-9-]+$/.test(id))throw Error('Invalid prediction capture identifier');
    await fs.mkdir(output,{recursive:true});
    const stem=output+'/'+id;
    try{await fs.access(stem+'.ax.txt');throw Error('Prediction capture already exists');}catch(e){if(e.code!=='ENOENT')throw e;}
    const ax=await ready(),facts=tournamentFacts(ax),bytes=await app.getScreenshot({emit:false}),after=await ready();
    await fs.writeFile(stem+'.ax.txt',ax);await fs.writeFile(stem+'.after.ax.txt',after);
    const image=stem+(bytes[0]===255?'.jpg':'.png');await fs.writeFile(image,bytes);
    let map={states:{},preparation:{url,windowUuid,policy:'Choose the higher displayed win probability within each unselected match; lexical team-label tie-break. Existing drafts never reset.'}};
    try{map=JSON.parse(await fs.readFile(output+'/observed.json','utf8'));}catch(e){if(e.code!=='ENOENT')throw e;}
    if(map.preparation.url!==url||map.preparation.windowUuid!==windowUuid)throw Error('Existing prediction preparation differs');
    map.states[id]={...facts,ax:stem+'.ax.txt',image,state_consistent:JSON.stringify(facts)===JSON.stringify(tournamentFacts(after))};
    await fs.writeFile(output+'/observed.json',JSON.stringify(map));
    return {id,round:facts.elements.round.value,selected:facts.elements.selected_matches.value,choices:facts.toggles.length,locked:facts.interactions.prediction_locked};
  }
  async function begin() {
    const ax=await tree();if(!ax.includes('UUID='+windowUuid))throw Error('Owned window changed');
    await app.pressKey('super+l');await app.paste(url);await app.pressKey('Return');
    const deadline=Date.now()+20000;
    do{const home=await tree();guard(home);if(home.includes('link 我来预测, Value:'))break;}while(Date.now()<deadline);
    await click(/\d+ link 我来预测, Value:/);const initial=await ready();
    if(!/button 揭晓对阵$/.test(initial.split('\n').find(x=>/button 揭晓对阵/.test(x))||'')||tournamentFacts(initial).toggles.some(x=>x.checked)||initial.includes('text 已锁定'))throw Error('Empty prediction required; existing draft preserved');
    return capture('empty');
  }
  async function fill(id,{limit=16}={}) {
    if(!Number.isInteger(limit)||limit<1||limit>16)throw Error('Invalid bounded choice count');
    await fs.mkdir(output,{recursive:true});const actions=[];
    for(let step=0;step<limit;step++) {
      const ax=await ready(),facts=tournamentFacts(ax);let pair;
      if(facts.interactions.prediction_locked)throw Error('Locked prediction cannot be filled');
      for(let i=0;i<facts.toggles.length;i+=2) {
        const candidates=facts.toggles.slice(i,i+2);
        if(candidates.length===2&&candidates.every(x=>!x.checked&&x.enabled)){pair=candidates;break;}
      }
      if(!pair)break;
      const ranked=pair.map(x=>({...x,probability:Number(x.label.match(/ (\d+(?:\.\d+)?)%/)?.[1])}));
      if(ranked.some(x=>!Number.isFinite(x.probability)))throw Error('Actual displayed match probabilities unavailable');
      ranked.sort((a,b)=>b.probability-a.probability||a.label.localeCompare(b.label));
      const stamp=Date.now();await app.click(ranked[0].index);const after=await ready();
      const stem=output+'/'+id+'-action-'+String(step).padStart(2,'0');
      await fs.writeFile(stem+'.before.ax.txt',ax,{flag:'wx'});await fs.writeFile(stem+'.after.ax.txt',after,{flag:'wx'});
      actions.push({pair:ranked.map(({label,probability})=>({label,probability})),chosen:ranked[0].label,before_unix_ms:stamp,after_unix_ms:Date.now(),before_ax:stem+'.before.ax.txt',after_ax:stem+'.after.ax.txt'});
    }
    await fs.writeFile(output+'/'+id+'.actions.json',JSON.stringify(actions),{flag:'wx'});
    return capture(id);
  }
  async function reload(id) {
    await app.pressKey('super+r');const deadline=Date.now()+20000;let entry,ax;
    do {
      ax=await tree();guard(ax);
      if(ax.includes('heading 我来预测, Value: 1')){entry='prediction';break;}
      if(ax.includes('heading S16 AI 大模型预测大赛, Value: 1')){entry='home';break;}
    }while(Date.now()<deadline);
    if(!entry)throw Error('Reload entry did not become ready');
    await fs.writeFile(output+'/'+id+'.reload-entry.ax.txt',ax,{flag:'wx'});
    await fs.writeFile(output+'/'+id+'.reload.json',JSON.stringify({entry}),{flag:'wx'});
    if(entry==='home')await click(/\d+ link 我来预测, Value:/);
    await ready();return capture(id);
  }
  async function nickname(value) {
    const ax=await ready(),line=ax.split('\n').find(x=>/text field \(settable\) 海报昵称, Value:/.test(x));
    if(!line)throw Error('Editable poster nickname unavailable');
    await app.click(Number(line.trim().match(/^\d+/)[0]));await app.pressKey('super+a');await app.paste(value);
    const after=await ready();if(tournamentFacts(after).elements.nickname.value!==value)throw Error('Nickname input did not apply');
    return after;
  }
  async function toggleFinal(id) {
    const ax=await ready(),facts=tournamentFacts(ax),pair=facts.toggles.slice(-2);
    if(facts.elements.round.value!=='淘汰赛'||pair.length!==2||pair.filter(x=>x.checked).length!==1)throw Error('Completed final pair required');
    const other=pair.find(x=>!x.checked&&x.enabled);if(!other)throw Error('Other finalist is not interactive');
    await app.click(other.index);await ready();return capture(id);
  }
  return {begin,click,capture,fill,reload,nickname,toggleFinal};
}
