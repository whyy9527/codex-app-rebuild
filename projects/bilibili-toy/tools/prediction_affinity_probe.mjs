// Read-only verification of each origin's existing draft against frozen model results.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {modelAffinityChecks,predictionResult} from './tournament_evidence.mjs';
import {tournamentFacts} from './prediction_native.mjs';
import {guardOwnedPage} from './visual_png_native.mjs';
const project=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),workspace=path.resolve(project,'../..');
const [side,stemArg,outArg,windowUuid]=process.argv.slice(2);
if(!['source','public'].includes(side)||!stemArg||!outArg||!windowUuid)throw Error('Usage: prediction_affinity_probe.mjs source|public capture-stem output-json window-uuid');
const stem=path.resolve(workspace,stemArg),out=path.resolve(workspace,outArg),privateRoot=project+'/private/';
if(!stem.startsWith(privateRoot)||!out.startsWith(privateRoot))throw Error('Evidence must stay private');
const original=(await fs.readFile(project+'/private/original-share-entry-url.txt','utf8')).trim(),url=side==='source'?original:'https://s16.xinxiayiyan.com/?'+new URL(original).search.slice(1);
const raw=await fs.readFile(stem+'.ax.txt','utf8'),after=await fs.readFile(stem+'.after.ax.txt','utf8');
guardOwnedPage(raw,url,windowUuid);guardOwnedPage(after,url,windowUuid);
const index=JSON.parse(await fs.readFile(project+'/private/site/data/index.json','utf8'));
const datasets={},runs=await Promise.all(index.runs.map(async r=>{const bytes=await fs.readFile(project+'/private/site/data/'+r.id+'/run.json');datasets[r.id]=createHash('sha256').update(bytes).digest('hex');return {...r,summary:JSON.parse(bytes).summary};}));
const observed=modelAffinityChecks(raw,runs),afterObserved=modelAffinityChecks(after,runs);
const interactions={...observed.checks,capture_choices_stable:JSON.stringify(predictionResult(tournamentFacts(raw)))===JSON.stringify(predictionResult(tournamentFacts(after))),capture_scores_stable:JSON.stringify(observed)===JSON.stringify(afterObserved)};
const facts={states:{prediction_affinity:{interactions}},observed,datasets,scope:'Each actual own draft scored independently; no storage/seed/draft copied or reset, no equality assertion between different draft values.'};
await fs.writeFile(out,JSON.stringify(facts,null,2),{flag:'wx'});
if(side==='source'){
 if(!Object.values(interactions).every(Boolean))throw Error('Source observations not ready for contract freeze');
 const evidence=[path.relative(workspace,stem+'.ax.txt'),path.relative(workspace,stem+'.after.ax.txt')];
 const requirements=Object.entries(interactions).map(([field,expected])=>({id:'prediction_affinity.'+field,state:'prediction_affinity',kind:'interaction_boolean',field,expected,evidence}));
 await fs.writeFile(out.replace(/\.json$/,'-contract.json'),JSON.stringify({schema_version:1,scope:facts.scope,requirements},null,2),{flag:'wx'});
}
console.log(JSON.stringify({side,checks:interactions,best:observed.nearest,best_score:observed.best_score}));
