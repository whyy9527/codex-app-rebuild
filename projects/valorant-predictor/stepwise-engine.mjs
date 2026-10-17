// Free foundation for a causal, discrete board simulation. No provider calls.
// It is not a physical FPS engine and has no calibrated accuracy claim.
export const ACTORS=['L1','L2','L3','L4','L5','R1','R2','R3','R4','R5'];
const clone=v=>structuredClone(v);
const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).sort().join() === [...keys].sort().join();
const requireThat=(test,message)=>{if(!test)throw Error(message);};
const side=id=>id.startsWith('L')?0:1;
const canonical=v=>v&&typeof v==='object'?Array.isArray(v)?`[${v.map(canonical).join(',')}]`:`{${Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')}}`:JSON.stringify(v);
export async function stateHash(value){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical(value))))].map(v=>v.toString(16).padStart(2,'0')).join('');}
function operation(state){
 const roles=[['ban','A'],['ban',state.protocol==='grand_final'?'A':'B'],['pick','A'],['side','B'],['pick','B'],['side','A'],['pick','A'],['side','B'],['pick','B'],['side','A'],['decider',null],['side','B']];
 return roles[state.bp_step];
}
export async function initialState(context,channel,seed=1){
 requireThat(context.kind==='stepwise_board_context'&&/^[a-f0-9]{64}$/.test(context.evidence_sha256),'A frozen evidence digest is required');
 requireThat(context.teams.length===2&&new Set(context.teams).size===2&&context.pool.length===7&&new Set(context.pool).size===7,'Invalid teams or seven-map pool');
 requireThat(['codex','deepseek','doubao','mimo'].includes(channel),'Unknown model');
 requireThat(['bo5','grand_final'].includes(context.protocol),'Unsupported protocol');
 requireThat(context.agent_catalog.length>=5&&new Set(context.agent_catalog).size===context.agent_catalog.length,'Agent catalog required');
 requireThat(Number.isInteger(seed)&&seed>0,'Seed must be a positive integer');
 return {kind:'stepwise_board_state',context_sha256:await stateHash(context),channel,sequence:0,phase:'bp',protocol:context.protocol,teams:context.teams,bp_step:0,bans:[],maps:[],starts:[],map_index:0,map_score:[0,0],round_score:[0,0],round:1,round_phase:0,actors:{},resources:[3,3],plant:null,rng:seed>>>0,winner:null,halt_reason:null};
}
export function nextDecision(state){
 if(state.phase==='bp'){const [kind,role]=operation(state);return {kind,team:role==='A'?state.teams[0]:state.teams[1]};}
 if(state.phase==='lineup')return {kind:'lineup',map:state.maps[state.map_index]};
 if(state.phase==='round')return {kind:'orders',map:state.maps[state.map_index],round:state.round,phase:['setup','entry','resolve'][state.round_phase]};
 return null;
}
function graphFor(context,state){
 const name=state.maps[state.map_index],graph=context.maps[name];
 requireThat(graph&&graph.source&&graph.nodes&&graph.starts?.length===2&&graph.sites?.length>0&&Array.isArray(graph.edges),'Selected map lacks a frozen, sourced geometry');
 for(const point of graph.starts.flat().concat(graph.sites))requireThat(point in graph.nodes,'Unknown start or site');
 return graph;
}
function resetActors(state,graph){
 ACTORS.forEach((id,i)=>{state.actors[id]={...state.actors[id],alive:true,node:graph.starts[side(id)][i%5]};});
 state.plant=null;state.round_phase=0;
}
function finishRound(state,win,events,graph){
 state.round_score[win]++;events.push({kind:'round_end',winner:state.teams[win],score:clone(state.round_score)});
 state.resources=state.resources.map((value,i)=>Math.min(9,value+(i===win?1:2)));
 const [a,b]=state.round_score;
 if(Math.max(a,b)>=13&&Math.abs(a-b)>=2){
  state.map_score[win]++;events.push({kind:'map_end',map:state.maps[state.map_index],winner:state.teams[win],score:clone(state.round_score)});
  if(state.map_score[win]===3){state.phase='finished';state.winner=state.teams[win];events.push({kind:'series_end',winner:state.winner,score:clone(state.map_score)});}
  else {state.map_index++;state.round_score=[0,0];state.round=1;state.actors={};state.resources=[3,3];state.phase='lineup';}
 }else if(state.round>=50){state.phase='halted';state.halt_reason='Round safety cap reached; no winner inferred';}
 else {state.round++;resetActors(state,graph);}
}
export async function applyDecision(context,before,decision){
 requireThat(exact(decision,['channel','sequence','previous_state_sha256','action']),'Unexpected decision fields; final score/winner cannot be supplied');
 requireThat(before.context_sha256===await stateHash(context),'Context changed after freezing');
 requireThat(decision.channel===before.channel&&decision.sequence===before.sequence,'Model or sequence mismatch');
 const beforeHash=await stateHash(before);requireThat(decision.previous_state_sha256===beforeHash,'Decision does not bind the current state');
 requireThat(['bp','lineup','round'].includes(before.phase),'Terminal states cannot accept decisions');
 const state=clone(before),a=decision.action,events=[],next=nextDecision(state);
 if(state.phase==='bp'){
  if(next.kind==='side'){
   requireThat(exact(a,['side'])&&['ATK','DEF'].includes(a.side),'Expected a legal starting side');
   const index=state.maps.length-1;state.starts[index]=next.team===state.teams[0]?a.side:a.side==='ATK'?'DEF':'ATK';
   events.push({kind:'side',map:state.maps[index],team:next.team,side:a.side});
  }else{
   requireThat(exact(a,['map'])&&context.pool.includes(a.map)&&!state.bans.includes(a.map)&&!state.maps.includes(a.map),'Map missing, repeated or outside pool');
   state[next.kind==='ban'?'bans':'maps'].push(a.map);events.push({kind:next.kind,team:next.team,map:a.map});
  }
  state.bp_step++;
  if(operation(state)?.[0]==='decider'){
   const remaining=context.pool.filter(m=>!state.bans.includes(m)&&!state.maps.includes(m));requireThat(remaining.length===1,'Decider not unique');state.maps.push(remaining[0]);events.push({kind:'decider',map:remaining[0]});state.bp_step++;
  }
  if(state.bp_step===12){state.phase='lineup';}
 }else if(state.phase==='lineup'){
  const graph=graphFor(context,state);
  requireThat(exact(a,['agents'])&&exact(a.agents,ACTORS),'All ten agent choices required');
  for(const id of ACTORS)requireThat(context.agent_catalog.includes(a.agents[id]),'Unknown agent');
  for(const team of [0,1])requireThat(new Set(ACTORS.filter(id=>side(id)===team).map(id=>a.agents[id])).size===5,'Duplicate agent within a team');
  ACTORS.forEach(id=>{state.actors[id]={agent:a.agents[id]};});resetActors(state,graph);state.phase='round';events.push({kind:'lineup',map:state.maps[state.map_index],agents:clone(a.agents)});
 }else{
  const graph=graphFor(context,state),ids=ACTORS.filter(id=>state.actors[id].alive),startAttack=state.starts[state.map_index]==='ATK'?0:1,attack=state.round<=12?startAttack:state.round<=24?1-startAttack:(state.round%2===1?startAttack:1-startAttack);
  requireThat(exact(a,['orders','spend'])&&exact(a.orders,ids)&&Array.isArray(a.spend)&&a.spend.length===2,'Orders must cover exactly the survivors');
  a.spend.forEach((n,i)=>requireThat(Number.isInteger(n)&&n>=0&&n<=2&&n<=state.resources[i]&&(state.round_phase===0||n===0),'Illegal abstract resource spend'));
  for(const id of ids){const o=a.orders[id];requireThat(exact(o,['type','node','target'])&&['hold','move','fire','plant','defuse'].includes(o.type),'Invalid actor order');
   requireThat((o.type==='move'&&typeof o.node==='string'&&o.target===null)||(o.type==='fire'&&o.node===null&&typeof o.target==='string')||(['hold','plant','defuse'].includes(o.type)&&o.node===null&&o.target===null),'Order parameters do not match type');
   if(o.type==='move')requireThat(o.node in graph.nodes&&(o.node===state.actors[id].node||graph.edges.some(e=>e.includes(o.node)&&e.includes(state.actors[id].node))),'Movement crossed an unapproved edge');
   if(o.type==='fire')requireThat(ids.includes(o.target)&&side(o.target)!==side(id),'Target must be a live opponent');
   if(o.type==='plant')requireThat(side(id)===attack&&graph.sites.includes(state.actors[id].node)&&!state.plant,'Plant requires attacker at site');
   if(o.type==='defuse')requireThat(side(id)!==attack&&state.plant===state.actors[id].node,'Defuse requires defender at planted site');
  }
  requireThat(ids.filter(id=>a.orders[id].type==='plant').length<=1&&ids.filter(id=>a.orders[id].type==='defuse').length<=1,'Only one spike interaction per phase');
  state.resources=state.resources.map((n,i)=>n-a.spend[i]);
  for(const id of ids)if(a.orders[id].type==='move'){state.actors[id].node=a.orders[id].node;events.push({kind:'move',actor:id,node:a.orders[id].node});}
  const eliminated=new Set();
  for(const id of ids){const o=a.orders[id];if(o.type!=='fire')continue;
   // Deliberately abstract same-zone encounters, not game line-of-sight or aim.
   if(state.actors[id].node!==state.actors[o.target].node){events.push({kind:'no_contact',actor:id,target:o.target});continue;}
   state.rng=(Math.imul(state.rng,1664525)+1013904223)>>>0;const draw=state.rng/4294967296;
   events.push({kind:'shot',actor:id,target:o.target,draw});if(draw<.5)eliminated.add(o.target);
  }
  for(const id of eliminated){state.actors[id].alive=false;events.push({kind:'eliminated',actor:id});}
  let defused=false;
  for(const id of ids.filter(id=>state.actors[id].alive)){
   if(a.orders[id].type==='plant'){state.plant=state.actors[id].node;events.push({kind:'plant',actor:id,node:state.plant});}
   if(a.orders[id].type==='defuse'){defused=true;events.push({kind:'defuse',actor:id,node:state.plant});}
  }
  const count=team=>ACTORS.filter(id=>side(id)===team&&state.actors[id].alive).length;
  if(defused)finishRound(state,1-attack,events,graph);
  else if(!count(0)&&!count(1))finishRound(state,state.plant?attack:1-attack,events,graph);
  else if(!count(1-attack))finishRound(state,attack,events,graph);
  else if(!count(attack)&&!state.plant)finishRound(state,1-attack,events,graph);
  else if(state.round_phase===2)finishRound(state,state.plant?attack:1-attack,events,graph);
  else state.round_phase++;
 }
 state.sequence++;
 return {state,events,receipt:{before_sha256:beforeHash,after_sha256:await stateHash(state),channel:state.channel,sequence:before.sequence}};
}

// The schema is generated from exactly the state passed to the next model call.
// Providers must not choose different IDs, a final winner, or a future state.
export async function decisionSchema(context,state){
 const strict=properties=>({type:'object',additionalProperties:false,required:Object.keys(properties),properties});
 const next=nextDecision(state);requireThat(next,'No next decision for terminal state');let action;
 if(['ban','pick'].includes(next.kind))action=strict({map:{type:'string',enum:context.pool.filter(m=>!state.bans.includes(m)&&!state.maps.includes(m))}});
 else if(next.kind==='side')action=strict({side:{type:'string',enum:['ATK','DEF']}});
 else if(next.kind==='lineup')action=strict({agents:strict(Object.fromEntries(ACTORS.map(id=>[id,{type:'string',enum:context.agent_catalog}])))});
 else action=strict({orders:strict(Object.fromEntries(ACTORS.filter(id=>state.actors[id].alive).map(id=>[id,strict({type:{type:'string',enum:['hold','move','fire','plant','defuse']},node:{type:['string','null']},target:{type:['string','null']}})]))),spend:{type:'array',minItems:2,maxItems:2,items:{type:'integer',minimum:0,maximum:2}}});
 return strict({channel:{const:state.channel},sequence:{const:state.sequence},previous_state_sha256:{const:await stateHash(state)},action});
}
