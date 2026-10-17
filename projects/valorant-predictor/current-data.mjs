import {causalTimeline} from './causal-player.mjs';
export function causalProjection(data,meta){
 const parts=data.cases||[data],timeline=causalTimeline(data);
 if(data.status==='ready'&&(parts.length!==2||parts.some(p=>p.state.stage!=='finished')||parts[1].teams[1]!==parts[0].state.winner))throw Error('Complete causal pair required');
 const cases=parts.map((part,index)=>{
  const players=new Map(),get=(id,lineup)=>{const a=lineup[id],team=part.teams[id[0]==='L'?0:1],key=team+':'+a.player;if(!players.has(key))players.set(key,{id:key,team,name:a.player,agents:[],maps:0,rounds:0,kills:0,deaths:0,plants:0,defuses:0});return players.get(key);};
  const maps=part.state.completed_maps.map(result=>{
   const frames=part.frames.filter(f=>f.map===result.map),lineup=frames.find(f=>f.kind==='lineup'),roundEnds=frames.filter(f=>f.kind==='round_end');
   for(const [id,a] of Object.entries(lineup.lineup)){const p=get(id,lineup.lineup);p.maps++;if(!p.agents.includes(a.agent))p.agents.push(a.agent);}
   const rounds=roundEnds.map(r=>{
    for(const id of Object.keys(r.lineup))get(id,r.lineup).rounds++;
    const events=frames.filter(f=>f.round_number===r.round_number&&f.event).map(f=>{
     const e=f.event,actor=get(e.actor,f.lineup);if(e.kind==='kill'){actor.kills++;get(e.target,f.lineup).deaths++;}if(e.kind==='plant')actor.plants++;if(e.kind==='defuse')actor.defuses++;
     return {...e,actor_name:f.lineup[e.actor].player,actor_team:actor.team,target_name:e.target?f.lineup[e.target]?.player:null};
    });
    return {number:r.round_number,winner:r.winner,score:r.round_score,attacking_team:r.attacking_team,resolution:r.resolution,copy:r.copy||'',events};
   });
   return {...result,start_time:timeline.find(f=>f.caseIndex===index&&f.kind==='lineup'&&f.map===result.map).start,start_side:part.bp.maps.find(m=>m.map===result.map).first_team_start_side,lineup:Object.entries(lineup.lineup).map(([id,a])=>({...a,team:part.teams[id[0]==='L'?0:1],actor_id:id})),plans:lineup.plan,rounds,round_count:rounds.length,attack_wins:rounds.filter(r=>r.winner===r.attacking_team).length};
  });
  return {id:index?'gf':'lf',match_id:meta.match_ids[index],label:index?'总决赛':'败者组决赛',teams:part.teams,score:part.state.series_score,winner:part.state.winner,bp:structuredClone(part.bp),maps,players:[...players.values()],round_count:maps.reduce((n,m)=>n+m.round_count,0),start_time:timeline.find(f=>f.kind==='bp'&&f.caseIndex===index).start,quality_flags:part.quality_flags||[]};
 });
 const order=[cases.at(-1)?.winner,cases.at(-1)?.teams.find(t=>t!==cases.at(-1)?.winner),cases[0]?.teams.find(t=>t!==cases[0]?.winner),...meta.finalists].filter((t,i,a)=>t&&a.indexOf(t)===i);
 const allPlayers=new Map();for(const part of cases)for(const p of part.players){if(!allPlayers.has(p.id))allPlayers.set(p.id,{...p,agents:[],maps:0,rounds:0,kills:0,deaths:0,plants:0,defuses:0,cases:[]});const merged=allPlayers.get(p.id);for(const key of ['maps','rounds','kills','deaths','plants','defuses'])merged[key]+=p[key];merged.cases.push(part.id);merged.agents=[...new Set([...merged.agents,...p.agents])];}
 return {channel:data.channel,status:data.status,model:meta.model,source_file:meta.source_file,source_sha256:meta.source_sha256,recorded_at:meta.recorded_at,recorded_at_basis:'Repository commit time of the unchanged model output; conservative publication cutoff, not provider completion time',calls:data.calls,round_count:cases.reduce((n,p)=>n+p.round_count,0),result_order:order,players:[...allPlayers.values()],cases};
}
export function factualEvent(event,official,now=Date.now()){
 const rows=new Map(event.history.filter(m=>m.state==='completed'&&m.winner&&Date.parse(m.start_utc)<=Math.min(now,Date.parse(event.fetched_at))).map(m=>[m.id,m]));
 if(Date.parse(official.fetched_at)<=now)for(const m of [...official.predecessors,...official.matches])if(verifiedCompleted(m,official,now))rows.set(m.id,m);
 return {...event,history:[...rows.values()].sort((a,b)=>Date.parse(a.start_utc)-Date.parse(b.start_utc))};
}
export function verifiedCompleted(match,official,now=Date.now()){
 const observed=Date.parse(official.fetched_at),start=Date.parse(match?.start_utc),needed=(match?.best_of+1)/2;
 return Boolean(match?.verified_current&&match.state==='completed'&&[3,5].includes(match.best_of)&&match.winner&&Array.isArray(match.teams)&&!match.teams.includes('TBD')&&Array.isArray(match.score)&&match.score.length===2&&match.score.every(n=>Number.isInteger(n)&&n>=0&&n<=needed)&&Math.max(...match.score)===needed&&match.score[0]!==match.score[1]&&match.teams[match.score[0]===needed?0:1]===match.winner&&Number.isFinite(start)&&Number.isFinite(observed)&&start<=observed&&observed<=now);
}
export function settleCausal(summary,official,now=Date.now()){
 return Object.values(summary.models).map(model=>{
  const recorded=Date.parse(model.recorded_at),results=[];
  for(const prediction of model.cases){
   const actual=official.matches.find(m=>m.id===prediction.match_id);
   if(model.status!=='ready'||!Number.isFinite(recorded)||actual?.best_of!==5||!verifiedCompleted(actual,official,now)||recorded>=Date.parse(actual.start_utc))continue;
   results.push({id:actual.id,label:prediction.label,predicted_winner:prediction.winner,actual_winner:actual.winner,hit:prediction.winner===actual.winner});
  }
  return {channel:model.channel,settled:results.length,hits:results.filter(r=>r.hit).length,results};
 });
}
export function currentFixture(event,official,now=Date.now()){
 const upper=(verifiedCompleted(official.predecessors[0],official,now)?official.predecessors[0].winner:null)||event.predecessors[0].winner,lower=(verifiedCompleted(official.predecessors[1],official,now)?official.predecessors[1].winner:null)||event.predecessors[1].winner;
 return {upperWinner:upper,upperLoser:upper?event.predecessors[0].teams.find(t=>t!==upper):null,lowerWinner:lower};
}
