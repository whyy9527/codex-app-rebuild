import assert from 'node:assert/strict';
import {appScope,appScrollbars,mobileFacts} from './mobile_native.mjs';

// Native Safari uses tabs, and routes expose one or two outer scrollbars.
const ax=`0 standard window Example
\t1 text field Description: Width, Value: 375
\t2 text field Description: Height, Value: 667
\t3 text Description: Zoom Level, Value: ( 99% )
\t4 pop up button Description: Pixel Ratio, Value: 2x
\t5 scroll area
\t\t6 HTML content
\t\t\t7 link 跳到主要内容, Value: example.test
\t\t\t8 container Example · AI 区新人 UP · 资深 LOL 观众
\t\t\t\t9 button + 关注
\t\t\t10 heading 数据 对比, Value: 1
\t\t\t11 container
\t\t\t\t12 scroll bar (settable, float) 0.5
\t\t13 scroll bar (settable, float) 0
\t14 container Toy 详情
\t\t15 button 分享`;
assert.equal(appScrollbars(ax).length,1);
assert.equal(appScrollbars(ax)[0].index,13);
assert(!appScope(ax).includes('关注'));
assert(!appScope(ax).includes('Toy 详情'));
assert.deepEqual(mobileFacts(ax).headings,['数据对比']);
assert.equal(mobileFacts(ax).interactions.at_scroll_origin,true);
const two=ax.replace('\t\t13 scroll bar','\t\t16 scroll bar (settable, float) 0.3\n\t\t13 scroll bar');
assert.equal(appScrollbars(two).length,2);
assert.equal(mobileFacts(two).interactions.at_scroll_origin,false);
assert.throws(()=>appScrollbars(ax.replace('7 link 跳到主要内容','7 link Wrong')),/boundary unavailable/);
assert.throws(()=>appScrollbars(two.replace('\t\t13 scroll bar','\t\t17 scroll bar (settable, float) 0\n\t\t13 scroll bar')),/ambiguous/);
console.log('Mobile scope, native indentation and scroll-origin checks passed');
