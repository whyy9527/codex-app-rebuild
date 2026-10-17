import {vetoSteps} from './veto.mjs';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const expectedModels={codex:'gpt-6.1-sol',deepseek:'deepseek-flash',doubao:'doubao-seed-2-1-pro-260915',mimo:'mimo-v2.6-pro'};
const labels={codex:'GPT-6.1 sol',deepseek:'DeepSeek V4.1 Flash',doubao:'豆包',mimo:'MiMo V2.6 Pro'};
const clock=t=>`${Math.floor(t/60).toString().padStart(2,'0')}:${Math.floor(t%60).toString().padStart(2,'0')}`;
const playbackRates=[1,2,4,8,16];
let active,raf,playbackRate=4,autoplayPending=true;
export function stopCausalPlayer(){cancelAnimationFrame(raf);active?.cleanup?.();active=null;}
export function causalMarkup(models){return `<section class="prediction-player" id="prediction-player" aria-label="逐步比赛推演"><div class="player-models">${models}</div><div class="player-now"><span id="causal-stage">读取推演</span><select id="causal-map-select" aria-label="选择比赛地图" disabled><option>等待地图</option></select><span id="causal-identity">实际模型输出 · AI 模拟</span></div><div class="player-controls"><button id="causal-prev" aria-label="上一段" disabled>←</button><button id="causal-play" class="player-play" disabled>读取推演</button><button id="causal-next" aria-label="下一段" disabled>→</button><label class="player-scrub"><span class="sr-only">推演进度</span><input id="causal-progress" type="range" value="0" min="0" step="0.01" aria-label="推演进度" disabled><output id="causal-clock">00:00</output></label><div class="causal-speed" role="group" aria-label="推演倍速"><span>倍速</span>${playbackRates.map(rate=>`<button type="button" data-causal-speed="${rate}" aria-pressed="${rate===playbackRate}" disabled>${rate}×</button>`).join('')}</div></div><div id="causal-screen" class="causal-screen"></div><p id="causal-caption" class="causal-caption"></p><details class="player-notes"><summary>推演依据与边界</summary><div id="causal-notes"></div></details></section>`;}
export function causalTimeline(data,onlyCase=null){
 let time=0;const result=[];
 for(const [physicalIndex,part] of (data.cases||[data]).entries()){
  const caseIndex=!data.cases&&data.case_id==='gf'?1:physicalIndex;
  if(onlyCase!==null&&caseIndex!==onlyCase)continue;
  const bp=part.bp;if(!bp)continue;
  const c={priority_role:bp.priority_role,bans:bp.bans,maps:bp.maps.map(m=>m.map),a_start_sides:bp.maps.map(m=>bp.priority_role==='A'?m.first_team_start_side:m.first_team_start_side==='ATK'?'DEF':'ATK')};
  const steps=vetoSteps({teams:part.teams,priority_team:part.teams[0],protocol:caseIndex?'grand_final':'bo5'},c).steps;
  const add=(value,duration,chapter=false)=>{result.push({...value,teams:part.teams,caseIndex,caseState:{completed_maps:part.state.completed_maps||[]},caseWarnings:part.quality_flags||[],start:time,end:time+duration,chapter});time+=duration;};
  steps.forEach((step,i)=>add({kind:'bp',step,index:i,bp,steps:steps.slice(0,i+1)},1.3,i===0));
  let roundLength=1,lastRoundEnd=null;
  for(const [i,frame] of part.frames.entries()){
   if(frame.kind==='lineup')lastRoundEnd=null;
   if(frame.kind==='round_end')lastRoundEnd=frame;
   const view=['map_end','series_end'].includes(frame.kind)&&lastRoundEnd?.map===frame.map?{...frame,positions:frame.positions??lastRoundEnd.positions,alive:frame.alive??lastRoundEnd.alive}:frame;
   if(frame.kind==='round_start')roundLength=Math.max(1,part.frames.slice(i).findIndex(f=>f.kind==='round_end')+1);
   if(frame.kind==='lineup')add(view,4,true);
   else if(frame.kind==='map_end')add(view,4,true);
   else if(frame.kind==='series_end')add(view,8,true);
   else add(view,6/roundLength,frame.kind==='round_start');
  }
 }
 return result;
}
export function routeRegion(frame,time){
 const route=frame.event?.kind==='move'?frame.event.route:[];
 if(!route.length)return null;
 const fraction=Math.max(0,Math.min(.999999,(time-frame.start)/(frame.end-frame.start)));
 return route[Math.floor(fraction*route.length)];
}
// Advance through every event and model-emitted movement region, including at 16×.
export function playbackTimes(frames,from,to){
 if(to<=from)return [];
 const points=[];
 for(const frame of frames){
  if(frame.end<=from)continue;if(frame.start>to)break;
  if(frame.start>from)points.push(frame.start);
  if(frame.event?.kind==='move')for(let i=1;i<frame.event.route.length;i++){
   const point=frame.start+(frame.end-frame.start)*(i+.5)/frame.event.route.length;
   if(point>from&&point<=to)points.push(point);
  }
 }
 if(points.at(-1)!==to)points.push(to);
 return points;
}
export async function mountCausalPlayer(model,{caseIndex=null,manifestPath='data/causal/models.json',evidencePath='data/evidence-v2.json'}={}){
 stopCausalPlayer();const root=document.querySelector('#prediction-player');if(!root)return;
 const token={root};active=token;const alive=()=>active===token&&root.isConnected,find=s=>root.querySelector(s);
 root.dataset.model=model;
 const fetchJSON=async path=>{const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw Error(`读取失败 ${r.status}`);return r.json();};
 try{
  const manifest=await fetchJSON(manifestPath),record=manifest.models[model];if(!alive())return;
  if(!record?.file){root.dataset.status='not_run';find('#causal-stage').textContent=labels[model];find('#causal-identity').textContent=record?.status==='running'?'首份输出生成中':record?.status==='blocked'?'本轮推演已暂停':'本轮逐步推演尚未运行';find('#causal-play').textContent='等待模型推演';find('#causal-screen').innerHTML='<div class="player-pending"><span>BP → 阵容 → 地图内事件 → 结果</span><h2>逐步推演待生成</h2><p>模型的首份有效输出就绪后即可播放。</p></div>';find('#causal-notes').textContent='不以其他模型、旧抽样或独立Ascent方案补齐。';return;}
  const fetchVerified=async()=>{const response=await fetch(record.file,{cache:'no-store'});if(!response.ok)throw Error('推演文件读取失败');const body=await response.arrayBuffer(),hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',body))].map(v=>v.toString(16).padStart(2,'0')).join('');if(hash!==record.sha256)throw Error('推演文件摘要不匹配');return JSON.parse(new TextDecoder().decode(body));};
  const [data,context,agentData,mapArt]=await Promise.all([fetchVerified(),fetchJSON('data/causal/map-context.json'),fetchJSON('data/causal/agents.json'),fetchJSON('data/causal/map-art.json')]);if(!alive())return;
  if(!['actual_gpt_batched_causal_series','actual_model_batched_causal_series'].includes(data.kind)||data.channel!==model||(data.cases||[data]).some(p=>p.records.some(r=>r.runtime_attestation?.model!==expectedModels[model])))throw Error('模型身份不匹配');
  const frames=causalTimeline(data,caseIndex),total=frames.at(-1).end;let time=0,playing=false,previous,index=-1,map='',selected='L1';const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
  root.querySelectorAll('[data-causal-speed]').forEach(b=>b.disabled=false);root.dataset.status=data.status;const mapSelect=find('#causal-map-select');mapSelect.innerHTML=frames.filter(f=>f.kind==='lineup'||f.kind==='bp'&&f.index===0).map(f=>`<option value="${f.start}" data-case="${f.caseIndex}" data-map="${esc(f.kind==='bp'?'bp':f.map)}">${f.caseIndex?'总决赛':'败者决赛'} · ${esc(f.kind==='bp'?'地图 BP':f.map)}</option>`).join('');mapSelect.disabled=false;find('#causal-progress').max=total;find('#causal-play').disabled=false;find('#causal-next').disabled=false;find('#causal-progress').disabled=false;
  find('#causal-notes').innerHTML=`<p>模型逐批预测双方决策与有序回合事件，程序从事件核算比分；下一批读取已验算状态。批内为一次响应中的顺序推演，没有逐回合外部反馈。</p><p>地图区域来自游戏资源目录；区域路径是模型假设，未验证FPS碰撞、视线、枪械或技能。经济只显示模型判断的档位，首发沿用最近出场名单作模拟假设。加时从第一队R25先攻、逐轮换边，是预先声明的简化约定。</p><p>${(data.cases||[data]).some(p=>p.records.some(r=>r.validation?.status==='partial'))?'已排除无效回合后缀，后续从最后有效比分继续。 ':''}${(data.cases||[data]).flatMap(p=>p.quality_flags||[]).map(n=>`<span class="causal-quality-note">${esc(n.message)}</span>`).join('')}${data.calls} 个阶段请求 · ${data.status==='ready'?'本场已推演结束':'系列赛尚未结束，当前只播放已验算内容'}</p><p><a href="${esc(evidencePath)}" target="_blank">本版本冻结资料 ↗</a> · <a href="data/causal/map-context.json" target="_blank">地图区域来源 ↗</a></p>`;
  const buy={pistol:'手枪局',eco:'经济局',force:'强起',half:'半起',full:'全装'};
  function controls(){find('#causal-play').textContent=playing?'Ⅱ 暂停':time>=total-.01?'↺ 重播推演':'▶ 播放推演';find('#causal-play').setAttribute('aria-pressed',String(playing));find('#causal-progress').value=time;find('#causal-clock').textContent=`${clock(time)} / ${clock(total)}`;find('#causal-prev').disabled=time===0;root.dataset.time=time.toFixed(2);root.dataset.playing=String(playing);root.dataset.speed=String(playbackRate);root.querySelectorAll('[data-causal-speed]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.causalSpeed)===playbackRate)));}
  function bpHTML(f){
   const step=f.step,past=f.steps,all=frames.filter(x=>x.kind==='bp'&&x.caseIndex===f.caseIndex),label={ban:'禁用',pick:'选图',side:'选边',decider:'决胜图'},image=name=>mapArt.maps[name]?.image||context.maps[name].image;
   const status=name=>{const decision=past.find(x=>x.map===name&&['ban','pick','decider'].includes(x.kind));return decision?`${decision.team||'剩余'} · ${label[decision.kind]}`:'待选择';};
   return `<div class="player-bp causal-bp"><div class="player-match"><span>${f.caseIndex?'10/18 · 总决赛':'10/17 · 败者组决赛'} · BO5 · AI 模拟 BP</span><h2>${esc(f.teams[0])}<i>VS</i>${esc(f.teams[1])}</h2></div><figure class="bp-feature ${step.kind}"><img src="${esc(image(step.map))}" alt="${esc(step.map)} 地图场景" width="1280" height="720"><figcaption><span class="bp-turn">第 ${f.index+1} / ${all.length} 步 · ${esc(step.team||'自动确定')}</span><div><h3>${esc(step.map)}</h3><p><i class="bp-action-symbol" aria-hidden="true">${{ban:'×',pick:'✓',side:'⇄',decider:'◇'}[step.kind]}</i>${label[step.kind]}${step.side?' · '+(step.side==='ATK'?'进攻':'防守')+'开局':''}</p></div></figcaption><span class="bp-feature-corner" aria-hidden="true"></span></figure>
   <div class="bp-pool" aria-label="七图池，点击查看该图的禁选步骤">${Object.keys(context.maps).map(name=>{const decision=past.find(x=>x.map===name&&['ban','pick','decider'].includes(x.kind)),state=decision?.kind==='ban'?'banned':decision?'picked':'pending',target=all.find(x=>x.step.map===name);return `<button class="bp-map-card ${state} ${step.map===name?'current':''}" data-bp-time="${target.start}" data-map="${esc(name)}" aria-label="查看 ${esc(name)} 禁选步骤：${esc(status(name))}" ${step.map===name?'aria-current="step"':''}><img src="${esc(image(name))}" alt="" width="1280" height="720"><span class="bp-map-shade"></span><span class="bp-map-name">${esc(name)}</span><span class="bp-map-state">${state==='banned'?'×':state==='picked'?'✓':'◇'} ${esc(status(name))}</span>${step.map===name?'<span class="bp-current-label">当前</span>':''}</button>`;}).join('')}</div>
   <ol class="bp-sequence" aria-label="双方禁选顺序">${all.map((x,i)=>`<li><button data-bp-time="${x.start}" ${i===f.index?'aria-current="step"':''} class="${i<f.index?'done':''}"><small>${String(i+1).padStart(2,'0')}</small><b>${esc(x.step.team||'剩余')}</b><span>${label[x.step.kind]}</span></button></li>`).join('')}</ol>
   <ol class="player-map-order">${f.bp.maps.map((m,i)=>{const pick=all.find(x=>x.step.map===m.map&&['pick','decider'].includes(x.step.kind));return `<li class="${step.map===m.map?'current':''}"><small>MAP ${i+1}</small><b>${esc(m.map)}</b><span>${esc(pick.step.team||'剩余')} ${label[pick.step.kind]}</span><span>${esc(f.teams[0])} ${m.first_team_start_side==='ATK'?'进攻':'防守'}</span></li>`;}).join('')}</ol></div>`;
  }
  function arenaHTML(f){const lineup=f.lineup,ctx=context.maps[f.map];return `<div class="causal-scoreboard"><b>${esc(f.teams[0])} <strong id="causal-left-score">0</strong></b><div><span>${esc(f.map)}</span><small id="causal-round-label"></small></div><b><strong id="causal-right-score">0</strong> ${esc(f.teams[1])}</b></div><div class="causal-arena">${['L','R'].map((s,side)=>`<aside class="causal-roster ${s}"><header><b>${f.teams[side]}</b><small id="causal-side-${s}"></small></header>${Object.entries(lineup).filter(([id])=>id[0]===s).map(([id,a])=>`<button data-causal-actor="${id}"><img src="${esc(agentData.agents[a.agent].image)}" alt=""><span><b>${esc(a.player)}</b><small>${esc(a.agent)}</small></span><i>${id.slice(1)}</i></button>`).join('')}</aside>`).join('')}<div class="causal-map"><img src="${esc(ctx.image)}" alt="${esc(f.map)}真实游戏小地图"><div class="causal-area-labels">${ctx.site_areas.map(id=>`<span style="left:${ctx.areas[id].xy[0]*100}%;top:${ctx.areas[id].xy[1]*100}%">${esc(id[0])}</span>`).join('')}</div><div class="causal-route" aria-hidden="true"></div>${Object.entries(lineup).map(([id,a])=>`<button class="causal-marker" data-causal-marker="${id}" aria-label="${esc(a.player+' '+a.agent)}"><img src="${esc(agentData.agents[a.agent].image)}" alt=""><span>${id.slice(1)}</span></button>`).join('')}</div></div><div class="causal-event"><b id="causal-event-title"></b><span id="causal-event-copy"></span></div>`;}
  function animateRegionMove(f){
   if(!playing||reducedMotion||f.event?.kind!=='move')return;
   const region=routeRegion(f,time),xy=context.maps[f.map].areas[region]?.xy,marker=find(`[data-causal-marker="${f.event.actor}"]`);
   if(marker&&xy){marker.style.left=xy[0]*100+'%';marker.style.top=xy[1]*100+'%';}
   root.querySelectorAll('.causal-route-point').forEach(p=>p.classList.toggle('current',p.dataset.region===region));
  }
  function draw(){if(!alive())return;const i=Math.max(0,frames.findIndex(f=>time<f.end)),f=frames[i]||frames.at(-1);root.dataset.stage=f.kind;root.dataset.frame=i;if(i===index){animateRegionMove(f);controls();return;}index=i;const currentMapOption=[...mapSelect.options].find(o=>Number(o.dataset.case)===f.caseIndex&&o.dataset.map===(f.kind==='bp'?'bp':f.map));if(currentMapOption)mapSelect.value=currentMapOption.value;
   if(f.kind==='bp'){find('#causal-stage').textContent='01 · 地图 BP';find('#causal-screen').innerHTML=bpHTML(f);root.querySelectorAll('[data-bp-time]').forEach(b=>b.onclick=()=>seek(Number(b.dataset.bpTime)+.03));find('#causal-caption').textContent='双方按合法顺序禁选地图与起始边。';map='';}
   else if(f.kind==='series_end'){find('#causal-stage').textContent='本场结果';find('#causal-screen').innerHTML=`<div class="player-finish"><span>${esc(labels[model])} 逐步推演结果</span><h2>${esc(f.winner)}</h2><p>${esc(f.teams[0])} ${f.series_score.join(' : ')} ${esc(f.teams[1])}</p><div class="player-series-results">${f.caseState.completed_maps.map(m=>`<div><small>${esc(m.map)}</small><b>${esc(f.teams[0])} <strong>${m.score.join(':')}</strong> ${esc(f.teams[1])}</b>${(f.caseWarnings||[]).filter(n=>n.map===m.map).map(n=>`<p class="causal-quality-note">${esc(n.message)}</p>`).join('')}</div>`).join('')}</div></div>`;find('#causal-caption').textContent='比分由本次逐步模拟事件累计得出。';map='';}
   else {
    if(map!==f.caseIndex+':'+f.map||!find('.causal-arena')){find('#causal-screen').innerHTML=arenaHTML(f);map=f.caseIndex+':'+f.map;root.querySelectorAll('[data-causal-actor],[data-causal-marker]').forEach(b=>b.onclick=()=>{selected=b.dataset.causalActor||b.dataset.causalMarker;index=-1;draw();});}
    const ctx=context.maps[f.map],sample=f.positions?f:frames.find(x=>x.caseIndex===f.caseIndex&&x.map===f.map&&x.kind==='round_start'),positions=sample?.positions||{},live=new Set(f.alive||Object.keys(f.lineup)),atk=f.attacking_team||sample?.attacking_team;
    find('#causal-stage').textContent=f.kind==='lineup'?'02 · 双方阵容':f.kind==='map_end'?'本图结果':'03 · 地图内推演';find('#causal-left-score').textContent=f.round_score?.[0]??0;find('#causal-right-score').textContent=f.round_score?.[1]??0;find('#causal-round-label').textContent=`大比分 ${f.series_score.join(':')}${f.round_number?' · R'+f.round_number:''}`;
    for(const [side,s] of ['L','R'].entries()){const attacking=atk===f.teams[side];find('.causal-roster.'+s).classList.toggle('attacking',attacking);find('#causal-side-'+s).textContent=(attacking?'ATK · 进攻':'DEF · 防守')+' · '+(buy[f.buy?.[side]]||'模拟阵容');root.querySelectorAll('.causal-roster.'+s+' button').forEach(b=>{const id=b.dataset.causalActor;b.classList.toggle('selected',id===selected);b.classList.toggle('dead',!live.has(id));});}
    for(const [id,area] of Object.entries(positions)){const p=ctx.areas[area]?.xy,b=find(`[data-causal-marker="${id}"]`);if(!p||!b)continue;b.style.left=p[0]*100+'%';b.style.top=p[1]*100+'%';b.classList.toggle('dead',!live.has(id));b.classList.toggle('selected',id===selected);b.classList.toggle('attacking',(id[0]==='L'?f.teams[0]:f.teams[1])===atk);b.title=f.lineup[id].player+' · '+ctx.areas[area].label;}
    const e=f.event;find('.causal-route').innerHTML=e?.kind==='move'?e.route.map((id,i)=>{const a=ctx.areas[id];return `<span class="causal-route-point" data-region="${esc(id)}" style="left:${a.xy[0]*100}%;top:${a.xy[1]*100}%" title="${esc(a.label)}">${i+1}</span>`;}).join(''):'';const names=id=>f.lineup[id]?.player||id,kindLabel={move:'区域转移',kill:'击杀',plant:'下包',defuse:'拆包'};
    find('#causal-event-title').textContent=e?`${names(e.actor)} · ${kindLabel[e.kind]}`:f.kind==='map_end'?`${f.winner} 赢下 ${f.map}`:f.kind==='round_end'?`${f.winner} 赢下 R${f.round_number}`:f.kind==='lineup'?'双方同时选特工':`R${f.round_number} · 开局控图`;
    find('#causal-event-copy').textContent=e?e.kind==='move'?e.route.map(id=>ctx.areas[id].label).join(' → '):e.kind==='kill'?`${names(e.target)} 被击杀 · ${ctx.areas[e.area].label}`:ctx.areas[e.area].label:f.kind==='lineup'?`${f.teams[0]} ${atk===f.teams[0]?'进攻':'防守'}开局 · ${f.teams[1]} ${atk===f.teams[1]?'进攻':'防守'}开局`:f.kind==='round_start'?'双方进入本回合控图区域。':f.kind==='map_end'?(f.caseWarnings||[]).filter(n=>n.map===f.map).map(n=>n.message).join(' '):f.copy||'';
    find('#causal-caption').textContent='AI 区域级比赛模拟 · 路径、交锋与经济档位为模型推演';
   }
   animateRegionMove(f);find('#causal-identity').textContent=labels[model]+' · '+(f.caseIndex?'总决赛':'败者组决赛')+' · '+(data.status==='ready'?'已完成':'已验算部分');controls();
  }
  const pause=()=>{playing=false;previous=undefined;cancelAnimationFrame(raf);controls();};
  const seek=t=>{pause();time=Math.max(0,Math.min(total-.001,t));index=-1;draw();};
  function advanceTo(now){
   if(previous!==undefined){const target=Math.min(total-.001,time+Math.min(Math.max(0,(now-previous)/1000),.1)*playbackRate);for(const point of playbackTimes(frames,time,target)){time=point;draw();}}
   previous=now;
  }
  function tick(now){if(!alive()||!playing)return;advanceTo(now);if(time>=total-.001)pause();else raf=requestAnimationFrame(tick);}
  root.querySelectorAll('[data-causal-speed]').forEach(b=>b.onclick=()=>{if(playing)advanceTo(performance.now());playbackRate=Number(b.dataset.causalSpeed);controls();});
  mapSelect.onchange=()=>seek(Number(mapSelect.value)+.03);
  const play=()=>{if(playing||!alive())return;if(time>=total-.01){time=0;index=-1;}playing=true;previous=undefined;controls();raf=requestAnimationFrame(tick);};
  find('#causal-play').onclick=()=>playing?pause():play();find('#causal-progress').oninput=e=>seek(Number(e.target.value));find('#causal-next').onclick=()=>seek(frames.find(f=>f.chapter&&f.start>time+.1)?.start??total-.001);find('#causal-prev').onclick=()=>seek([...frames].reverse().find(f=>f.chapter&&f.start<time-.5)?.start??0);
  const onVisibility=()=>{if(document.hidden)pause();};document.addEventListener('visibilitychange',onVisibility);token.cleanup=()=>document.removeEventListener('visibilitychange',onVisibility);const bookmark=new URLSearchParams(location.hash.split('?')[1]||'').get('at');if(bookmark!==null&&Number.isFinite(Number(bookmark)))seek(Number(bookmark));else draw();
  const shouldAutoplay=autoplayPending;autoplayPending=false;if(shouldAutoplay)play();
 }catch(e){if(alive()){root.dataset.status='failed';find('#causal-screen').innerHTML=`<div class="player-pending"><h2>推演暂不可用</h2><p>${esc(e.message)}</p></div>`;find('#causal-play').textContent='暂不可播放';}}
}
