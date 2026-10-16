// Shared native CUA observation for the new real-results match breakdown.
import {guardOwnedPage,openElementInspector,installLosslessUI} from './visual_png_native.mjs';
export async function captureLiveMatch(app,fs,{url,windowUuid,stem}) {
  const tree=()=>app.getAXState({emit:false,disableDiffing:true});
  const index=line=>Number(line.trim().match(/^\d+/)[0]);
  async function ready(pattern){const until=Date.now()+20000;do{const ax=await tree();guardOwnedPage(ax,url,windowUuid);if(pattern.test(ax))return ax;}while(Date.now()<until);throw Error('Actual live-results page did not become ready');}
  await app.pressKey('super+l');await app.paste(url);await app.pressKey('Return');
  let ax=await ready(/link 谁最准, Value:/);
  await app.click(index(ax.split('\n').find(x=>/link 谁最准, Value:/.test(x))));
  ax=await ready(/summary KC 3 : 2 C9 .*Value: (on|off)/);
  const summary=ax.split('\n').find(x=>/summary KC 3 : 2 C9 /.test(x));
  if(summary.endsWith('Value: off')){await app.click(index(summary));ax=await ready(/summary KC 3 : 2 C9 .*Value: on/);}
  await fs.writeFile(stem+'.ax.txt',ax,{flag:'wx'});
  const bytes=await app.getScreenshot({emit:false});
  await fs.writeFile(stem+(bytes[0]===255?'.jpg':'.png'),bytes,{flag:'wx'});
  const after=await tree();guardOwnedPage(after,url,windowUuid);
  await fs.writeFile(stem+'.after.ax.txt',after,{flag:'wx'});
  return {stem,bytes:bytes.length};
}

export async function capturePredictionResult(app,fs,{url,windowUuid,stem}) {
  const tree=()=>app.getAXState({emit:false,disableDiffing:true});
  const index=line=>Number(line.trim().match(/^\d+/)[0]);
  async function ready(pattern){const until=Date.now()+20000;do{const ax=await tree();guardOwnedPage(ax,url,windowUuid);if(pattern.test(ax)&&ax.includes('button 展开 AI 模拟速报'))return ax;}while(Date.now()<until);throw Error('Actual prediction page did not become ready');}
  await app.pressKey('super+l');await app.paste(url);await app.pressKey('Return');
  let ax=await ready(/link 我来预测, Value:/);
  await app.click(index(ax.split('\n').find(x=>/link 我来预测, Value:/.test(x))));
  ax=await ready(/heading 我来预测, Value: 1/);
  const knockout=ax.split('\n').find(x=>/\d+ button 淘汰赛$/.test(x));
  if(!knockout)throw Error('Completed knockout view unavailable; existing drafts must be preserved');
  await app.click(index(knockout));ax=await ready(/text 我的冠军/);
  await fs.writeFile(stem+'.ax.txt',ax,{flag:'wx'});
  const bytes=await app.getScreenshot({emit:false});await fs.writeFile(stem+(bytes[0]===255?'.jpg':'.png'),bytes,{flag:'wx'});
  const after=await tree();guardOwnedPage(after,url,windowUuid);await fs.writeFile(stem+'.after.ax.txt',after,{flag:'wx'});
  return {stem,bytes:bytes.length};
}

export function installSeriesTableUI(app,fs,{url,windowUuid,output}) {
  const tree=()=>app.getAXState({emit:false,disableDiffing:true});
  const index=line=>Number(line.trim().match(/^\d+/)[0]);
  const guard=ax=>guardOwnedPage(ax,url,windowUuid);
  async function ready(){const until=Date.now()+20000;do{const ax=await tree();guard(ax);if(ax.includes('summary KC 3 : 2 C9')&&ax.includes('button 展开 AI 模拟速报')&&!ax.includes('button (disabled) 检查中'))return ax;}while(Date.now()<until);throw Error('Completed original series unavailable');}
  async function prepare(){let ax=await tree();guard(ax);const link=ax.split('\n').find(x=>/link 谁最准, Value:/.test(x));await app.click(index(link));ax=await ready();const closed=ax.split('\n').find(x=>/summary KC 3 : 2 C9 .*Value: off/.test(x));if(closed){await app.click(index(closed));ax=await ready();}await fs.mkdir(output,{recursive:true});return ax;}
  async function capture(spec){
    let ax=await ready();
    const scrollModule=await import('./mobile_native.mjs');
    for(const bar of scrollModule.appScrollbars(ax)){await app.setValue(bar.index,'0');ax=await tree();guard(ax);}
    if(scrollModule.appScrollbars(ax).some(x=>x.value!=='0'))throw Error('Actual series scroll did not reset');
    const directory=output+'/'+spec.id;await fs.mkdir(directory);
    await openElementInspector(app,url);await app.pressKey('super+f');ax=await tree();
    const find=ax.split('\n').find(x=>x.includes('search text field (settable)')&&!x.includes('Filter'));
    await app.setValue(index(find),spec.selector);await app.pressKey('Return');ax=await tree();
    const selected=ax.split('\n').find(x=>/row \(selected/.test(x)&&new RegExp(spec.node_pattern).test(x));
    if(!selected||!ax.includes('Value: '+spec.selector))throw Error('Actual requested table anchor unavailable');
    await fs.writeFile(directory+'/anchor.before.ax.txt',ax,{flag:'wx'});
    await app.click(index(selected),{mouseButton:'right'});ax=await tree();
    const scroll=ax.split('\n').find(x=>/^\s*\d+ Scroll into View,/.test(x));
    if(!scroll)throw Error('Native Scroll into View unavailable');
    await fs.writeFile(directory+'/anchor.menu.ax.txt',ax,{flag:'wx'});
    await app.click(index(scroll));ax=await tree();await fs.writeFile(directory+'/anchor.after.ax.txt',ax,{flag:'wx'});
    await app.pressKey('super+w');ax=await tree();guard(ax);
    await app.pressKey('Down');const started=Date.now(),trace=[];let previous,stable=false;
    do{ax=await tree();guard(ax);const values=scrollModule.appScrollbars(ax).map(x=>x.value);trace.push({unix_ms:Date.now(),values});if(Date.now()-started>=400&&JSON.stringify(values)===previous){stable=true;break;}previous=JSON.stringify(values);}while(Date.now()-started<5000);
    if(!stable||trace.at(-1).values.every(x=>x==='0'))throw Error('Actual anchored scroll unavailable');
    const tables=ax.split('\n').filter(x=>/^\s*\d+ table$/.test(x));
    if(tables.length!==6||!tables[spec.table_index])throw Error('Actual completed-series table identity unavailable');
    await app.click(index(tables[spec.table_index]));ax=await tree();guard(ax);
    await fs.writeFile(directory+'/preparation.json',JSON.stringify({id:spec.id,url,windowUuid,selector:spec.selector,action:'Native Scroll into View then one Arrow Down to clear the fixed ticker',scroll_trace:trace}),{flag:'wx'});
    const png=installLosslessUI(app,fs,{url,output:directory,windowUuid});
    await png.capture('page-a');await png.capture('page-b');return {id:spec.id,scroll_values:trace.at(-1).values};
  }
  return {prepare,capture};
}
