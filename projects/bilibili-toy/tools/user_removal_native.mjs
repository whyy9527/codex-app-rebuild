// Local original-page reference variant for the user's two explicit deletions.
// Invoke only from CUA with an actual native App binding. Reload restores it.
import {guardOwnedPage} from './visual_png_native.mjs';
export function installRequestedRemovalReference(app,fs,{url,output,windowUuid}) {
  if(new URL(url).origin!=='https://www.bilibili.com')throw Error('Actual original origin required');
  const tree=()=>app.getAXState({emit:false,disableDiffing:true});
  const index=line=>Number(line.trim().match(/^\d+/)[0]);
  async function remove(selector,pattern,stem) {
    await app.pressKey('super+f');let ax=await tree();
    const field=ax.split('\n').find(x=>x.includes('search text field (settable)')&&!x.includes('Filter'));
    if(!field)throw Error('Actual inspector search unavailable');
    await app.setValue(index(field),selector);await app.pressKey('Return');ax=await tree();
    const node=ax.split('\n').find(x=>pattern.test(x));
    if(!node)throw Error('Actual requested original node unavailable');
    await fs.writeFile(output+'/'+stem+'.before.ax.txt',ax,{flag:'wx'});
    await app.click(index(node),{mouseButton:'right'});ax=await tree();
    const group=ax.split('\n').find(x=>/^\s*\d+ (?:\(selected\) )?Delete$/.test(x));
    if(!group)throw Error('Actual DOM Delete group unavailable');
    await app.click(index(group));ax=await tree();
    const action=ax.split('\n').find(x=>/^\s*\d+ (?:\(selected\) )?Node, ID: forwardContextMenuAction:$/.test(x));
    if(!action)throw Error('Actual DOM Delete Node action unavailable');
    await fs.writeFile(output+'/'+stem+'.menu.ax.txt',ax,{flag:'wx'});
    await app.click(index(action));ax=await tree();
    await fs.writeFile(output+'/'+stem+'.after.ax.txt',ax,{flag:'wx'});
    if(ax.split('\n').some(x=>pattern.test(x)))throw Error('Requested original node still present');
  }
  async function prepare() {
    const before=await tree();guardOwnedPage(before,url,windowUuid);
    await fs.mkdir(output,{recursive:true});
    await fs.writeFile(output+'/before-requested-removals.ax.txt',before,{flag:'wx'});
    await app.pressKey('super+alt+i');let ax=await tree();
    if(!ax.includes('standard window Web Inspector — www.bilibili.com'))throw Error('Original inspector unavailable');
    await remove('.author-bar',/row .*<div.*author-bar/,'author-node-delete');
    await remove('.toy-shell-sidebar',/row .*<aside.*toy-shell-sidebar/,'sidebar-node-delete');
    await app.pressKey('super+w');ax=await tree();guardOwnedPage(ax,url,windowUuid);
    await fs.writeFile(output+'/after-requested-removals.ax.txt',ax,{flag:'wx'});
    if(/container .*AI 区新人 UP/.test(ax))throw Error('Original author subtree reappeared');
    return {removed:['.author-bar','aside#toy-shell-sidebar'],original_url:url};
  }
  return {prepare};
}
