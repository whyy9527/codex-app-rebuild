import {mapSeriesDistribution,simulateMapSeries} from '../engine.mjs';
let input='';for await(const chunk of process.stdin)input+=chunk;
const proposal=JSON.parse(input);
const cases=Object.fromEntries(Object.entries(proposal.cases).map(([k,c])=>[k,{teams:c.teams,maps:c.maps,distribution:mapSeriesDistribution(c.maps)}]));
const lower=simulateMapSeries(cases.lf.teams,cases.lf.maps,20261017);
const gfKey=lower.winner==='VIT'?'gf_vit':'gf_100t';
const final=simulateMapSeries(cases[gfKey].teams,cases[gfKey].maps,20261018);
const pWin=c=>c.distribution.filter(r=>r.score[0]===3).reduce((s,r)=>s+r.probability,0),pLower=pWin(cases.lf);
console.log(JSON.stringify({kind:'conditional_independent_maps_arithmetic','cases':cases,champion_probabilities:{LOUD:pLower*pWin(cases.gf_vit)+(1-pLower)*pWin(cases.gf_100t),VIT:pLower*(1-pWin(cases.gf_vit)),'100T':(1-pLower)*(1-pWin(cases.gf_100t))},sample:{kind:'fictional_seeded_draw_not_prediction_mode',seeds:[20261017,20261018],series:[lower,final]},calibration:'subjective model probabilities, uncalibrated; independent-map simplification'}));
