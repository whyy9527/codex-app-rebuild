// Shared native CUA observation for the new real-results match breakdown.
import {guardOwnedPage} from './visual_png_native.mjs';
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
