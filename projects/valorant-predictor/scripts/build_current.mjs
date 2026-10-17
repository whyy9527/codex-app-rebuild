import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {causalProjection} from '../current-data.mjs';
const project=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),input=path.resolve(process.argv[2]||project),read=async p=>JSON.parse(await readFile(path.join(input,p),'utf8'));
const manifest=await read('data/causal/models.json'),evidence=await read('data/evidence-v2.json'),event=await read('data/event.json'),out={kind:'validated_causal_projection',prepared_at:new Date().toISOString(),evidence_frozen_at:evidence.frozen_at,evidence_sha256:evidence.content_sha256,models:{}};
for(const [channel,row] of Object.entries(manifest.models)){
 if(!row.file){out.models[channel]={channel,status:row.status,cases:[],round_count:0};continue;}
 const bytes=await readFile(path.join(input,row.file)),sha=createHash('sha256').update(bytes).digest('hex');if(sha!==row.sha256)throw Error('Projection source digest differs');const data=JSON.parse(bytes);let recorded=null;
 try{recorded=execFileSync('git',['log','-1','--format=%cI','--',row.file],{cwd:project,encoding:'utf8'}).trim()||null;}catch{}
 out.models[channel]=causalProjection(data,{source_file:row.file,source_sha256:sha,recorded_at:recorded,model:data.cases[0].records[0].runtime_attestation.model,match_ids:event.matches.map(m=>m.id),finalists:event.predecessors.flatMap(m=>m.teams)});
}
out.round_count=Object.values(out.models).reduce((n,m)=>n+m.round_count,0);await writeFile(path.join(input,'data/current-results.json'),JSON.stringify(out,null,2)+'\n');console.log('Current pages project actual causal rounds:',out.round_count);

const finals=await read('data/gf-postmatch/models.json'),finalOut={kind:'isolated_postmatch_final_projection',version:finals.version,evidence_sha256:finals.evidence_sha256,information_cutoff:finals.information_cutoff,models:{}};
for(const [channel,row] of Object.entries(finals.models)){
 if(row.status!=='ready')continue;
 const bytes=await readFile(path.join(input,row.file)),sha=createHash('sha256').update(bytes).digest('hex');if(sha!==row.sha256)throw Error('Final projection source digest differs');const data=JSON.parse(bytes);
 finalOut.models[channel]=causalProjection(data,{source_file:row.file,source_sha256:sha,recorded_at:row.recorded_at,model:data.records[0].runtime_attestation.model,match_ids:event.matches.map(m=>m.id),finalists:finals.teams});
}
await writeFile(path.join(input,'data/gf-postmatch/results.json'),JSON.stringify(finalOut,null,2)+'\n');console.log('New final projections:',Object.keys(finalOut.models).join(',')||'none complete');
