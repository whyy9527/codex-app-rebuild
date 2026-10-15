import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';

const script=await fs.readFile(new URL('../app/frame-entry.js',import.meta.url),'utf8');
function entry(search,hash=''){
  const frame={dataset:{entryHash:hash}};
  vm.runInNewContext(script,{document:{querySelector:()=>frame},window:{location:{search}}});
  return frame.src;
}
const query='?plat_id=620&share_origin=top_right&p=pickem&pick=original-code';
assert.equal(entry(query),'/content/index.html'+query);
assert.equal(entry('?p=pickem','#/ai/opus-5.5__S16-MAIN/match/PI-UB1?g=4'),
  '/content/index.html#/ai/opus-5.5__S16-MAIN/match/PI-UB1?g=4');
assert.equal(entry('','#/ai/opus-5.5__S16-MAIN'),'/content/index.html#/ai/opus-5.5__S16-MAIN');
console.log('Root query forwarding and fixed world/game share routes passed');
