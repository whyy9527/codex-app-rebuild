import assert from 'node:assert/strict';
import {guardOwnedPage} from './visual_png_native.mjs';
const ax=`0 standard window Task, UUID=ABC-123
1 text field Description: smart search field in a private window, Value: 127.0.0.1:4619/?plat_id=620, ID: Address`;
const url='http://127.0.0.1:4619/?plat_id=620';
guardOwnedPage(ax,url,'ABC-123');
for(const changed of [ax.replace('4619','4618'),ax.replace('plat_id=620','plat_id=1')])assert.throws(()=>guardOwnedPage(changed,url,'ABC-123'),/endpoint changed/);
assert.throws(()=>guardOwnedPage(ax,url,'OTHER'),/page changed/);
guardOwnedPage(ax.replace('127.0.0.1:4619/','https://s16.xinxiayiyan.com/'),'https://s16.xinxiayiyan.com/?plat_id=620','ABC-123');
console.log('Owned PNG page identity, elided HTTP scheme, query and port checks passed');
