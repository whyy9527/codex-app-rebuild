export const FINAL_FIXTURE = Object.freeze({id:'115576361461208331',teams:Object.freeze(['LOUD','VIT']),start_utc:'2026-10-18T06:00:00Z',best_of:5});
export function validateFinalPick(value){
 if(value?.version!==2||value.scope!=='grand_final_20261018'||value.match_id!==FINAL_FIXTURE.id||JSON.stringify(value.teams)!==JSON.stringify(FINAL_FIXTURE.teams)||!FINAL_FIXTURE.teams.includes(value.champion)||!Array.isArray(value.score)||value.score.length!==2)return false;
 const index=FINAL_FIXTURE.teams.indexOf(value.champion);
 return value.score.every(Number.isInteger)&&value.score[index]===3&&value.score[1-index]>=0&&value.score[1-index]<=2&&Number.isFinite(Date.parse(value.created_at));
}
export function makeFinalPick(draft,source,now=new Date().toISOString()){
 return {version:2,scope:'grand_final_20261018',match_id:FINAL_FIXTURE.id,teams:[...FINAL_FIXTURE.teams],champion:draft.champion,score:draft.score?[...draft.score]:null,source_sha256:source,created_at:now};
}
