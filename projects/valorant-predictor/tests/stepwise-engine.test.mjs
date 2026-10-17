import test from 'node:test';
import assert from 'node:assert/strict';
import {ACTORS,initialState,stateHash,nextDecision,applyDecision,decisionSchema} from '../stepwise-engine.mjs';
// Synthetic test board only. These coordinates are never published as a game map.
const graph={source:'synthetic_unit_test_only',nodes:Object.fromEntries([...ACTORS,'C'].map((id,i)=>[id,[i,0]])),starts:[ACTORS.slice(0,5),ACTORS.slice(5)],sites:['C'],edges:ACTORS.map(id=>[id,'C'])};
const context={kind:'stepwise_board_context',evidence_sha256:'a'.repeat(64),teams:['VIT','100T'],protocol:'bo5',pool:['Split','Summit','Sunset','Haven','Lotus','Ascent','Abyss'],agent_catalog:['Jett','Sova','Omen','Killjoy','KAY/O'],maps:Object.fromEntries(['Split','Summit','Sunset','Haven','Lotus','Ascent','Abyss'].map(m=>[m,graph]))};
const command=async(state,action)=>({channel:state.channel,sequence:state.sequence,previous_state_sha256:await stateHash(state),action});
const step=async(state,action,c=context)=>applyDecision(c,state,await command(state,action));
const orders=state=>({orders:Object.fromEntries(ACTORS.filter(id=>state.actors[id].alive).map(id=>[id,{type:'hold',node:null,target:null}])),spend:[0,0]});
async function ready(){let state=await initialState(context,'codex');while(state.phase==='bp'){const op=nextDecision(state);state=(await step(state,op.kind==='side'?{side:'DEF'}:{map:context.pool.find(m=>!state.bans.includes(m)&&!state.maps.includes(m))})).state;}const a={agents:Object.fromEntries(ACTORS.map((id,i)=>[id,context.agent_catalog[i%5]]))};return (await step(state,a)).state;}
test('legal BP consumes prior choices, automatic decider and opposite-side selection',async()=>{
 let state=await initialState(context,'codex');const ops=[];
 while(state.phase==='bp'){const op=nextDecision(state);ops.push(op);const result=await step(state,op.kind==='side'?{side:'DEF'}:{map:context.pool.find(m=>!state.bans.includes(m)&&!state.maps.includes(m))});assert.equal(result.receipt.before_sha256,await stateHash(state));state=result.state;}
 assert.equal(ops.length,11);assert.equal(state.bans.length,2);assert.equal(state.maps.length,5);assert.equal(new Set([...state.bans,...state.maps]).size,7);assert.equal(state.starts.length,5);assert.equal(state.phase,'lineup');
 const gf=await initialState({...context,teams:['LOUD','100T'],protocol:'grand_final'},'codex');const x=(await step(gf,{map:'Split'},{...context,teams:['LOUD','100T'],protocol:'grand_final'})).state;assert.equal(nextDecision(x).team,'LOUD');
});
test('prior state hash, sequence, exact model and no supplied winner are enforced',async()=>{
 const state=await initialState(context,'codex'),d=await command(state,{map:'Split'});
 await assert.rejects(applyDecision(context,state,{...d,winner:'VIT'}));await assert.rejects(applyDecision(context,state,{...d,channel:'deepseek'}));await assert.rejects(applyDecision(context,state,{...d,previous_state_sha256:'0'.repeat(64)}));
 const after=(await applyDecision(context,state,d)).state;await assert.rejects(applyDecision(context,after,d));assert.deepEqual(state.bans,[]);
});
test('same-map moves and resulting eliminations become the next exact live actor set',async()=>{
 let state=await ready(),a=orders(state);a.orders.L1={type:'move',node:'C',target:null};a.orders.R1={type:'move',node:'C',target:null};state=(await step(state,a)).state;assert.equal(state.round_phase,1);assert.equal(state.actors.R1.node,'C');
 a=orders(state);a.orders.L1={type:'fire',node:null,target:'R1'};const after=await step(state,a);assert.equal(after.state.actors.R1.alive,false);assert.equal(after.state.round_phase,2);assert.ok(after.events.some(e=>e.kind==='eliminated'&&e.actor==='R1'));
 const sch=await decisionSchema(context,after.state);assert.ok(!sch.properties.action.properties.orders.required.includes('R1'));
 const stale=orders(after.state);stale.orders.R1={type:'hold',node:null,target:null};await assert.rejects(step(after.state,stale));
});
test('state-dependent geometry, illegal transitions and unavailable maps fail without substitution',async()=>{
 const state=await ready(),a=orders(state);a.orders.L1={type:'move',node:'R2',target:null};await assert.rejects(step(state,a));a.orders.L1={type:'plant',node:null,target:null};await assert.rejects(step(state,a));
 const c={...context,maps:{}},init=await initialState(c,'codex');let s=init;while(s.phase==='bp'){const op=nextDecision(s);s=(await step(s,op.kind==='side'?{side:'DEF'}:{map:c.pool.find(m=>!s.bans.includes(m)&&!s.maps.includes(m))},c)).state;}
 await assert.rejects(step(s,{agents:Object.fromEntries(ACTORS.map((id,i)=>[id,c.agent_catalog[i%5]]))},c),/geometry/);
});
test('round events determine score; a terminal map derives series result without accepting one',async()=>{
 const state=await ready();state.round_phase=2;state.round_score=[12,0];state.map_score=[2,0];state.starts[state.map_index]='DEF';
 const result=await step(state,orders(state));assert.equal(result.state.phase,'finished');assert.equal(result.state.winner,'VIT');assert.deepEqual(result.state.map_score,[3,0]);assert.ok(result.events.some(e=>e.kind==='series_end'));
 await assert.rejects(step(result.state,{winner:'100T'}));
});
test('same state and seed replay exactly; a changed decision changes the next input',async()=>{
 const state=await ready(),hold=orders(state),move=orders(state);move.orders.L1={type:'move',node:'C',target:null};const a=await step(state,hold),b=await step(state,hold),c=await step(state,move);assert.deepEqual(a,b);assert.notEqual(a.receipt.after_sha256,c.receipt.after_sha256);
});
