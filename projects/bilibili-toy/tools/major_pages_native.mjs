// Shared actual responsive journeys; invoke through CUA only.
import {installMobileUI,appScope,appScrollbars} from './mobile_native.mjs';
import {installLosslessUI,guardOwnedPage} from './visual_png_native.mjs';
import {installRequestedRemovalReference} from './user_removal_native.mjs';
export function installMajorPagesUI(app,fs,{url,output,windowUuid,source=false}) {
  const tree=()=>app.getAXState({emit:false,disableDiffing:true});
  const index=line=>Number(line.trim().match(/^\d+/)[0]);
  const ui=installMobileUI(app,fs,{url,output:output+'/native-aux',windowUuid});
  async function ready(pattern){const end=Date.now()+20000;do{const ax=await tree();guardOwnedPage(ax,url,windowUuid);if(pattern.test(ax)&&ax.includes('button 展开 AI 模拟速报'))return ax;}while(Date.now()<end);throw Error('Actual requested page unavailable: '+pattern);}
  async function prepare(){await fs.mkdir(output,{recursive:true});await ui.prepare();if(source)await installRequestedRemovalReference(app,fs,{url,output,windowUuid}).prepare();return tree();}
  async function click(pattern){const ax=await tree();guardOwnedPage(ax,url,windowUuid);const line=ax.split('\n').find(x=>pattern.test(x));if(!line)throw Error('Actual page control missing: '+pattern);await app.click(index(line));return tree();}
  async function header(directory){await app.pressKey('super+alt+i');await tree();await app.pressKey('super+f');let ax=await tree();const field=ax.split('\n').find(x=>x.includes('search text field (settable)')&&!x.includes('Filter'));await app.setValue(index(field),'#main-content');await app.pressKey('Return');ax=await tree();await fs.writeFile(directory+'/header.inspector.ax.txt',ax,{flag:'wx'});const shell=ax.split('\n').find(x=>x.includes('--header-height:'));const height=Number(shell?.match(/--header-height:[^0-9]*([0-9.]+)px/)?.[1]);await app.pressKey('super+w');await tree();if(height!==191)throw Error('Actual mobile header differs: '+height);}
  async function page(spec){
    if(spec.model){await click(/link 首页, Value:/);await ready(/pop up button 选择 AI 频道/);await ui.selectModel(spec.model);}
    else if(spec.id==='team-gen'){await click(/link 战队, Value:/);await ready(/heading 参赛战队, Value: 1/);await click(/\d+ link.*GEN.*Gen\.G/);}
    else await click(new RegExp('\\d+ link '+spec.link+', Value:'));
    let ax=await ready(new RegExp(spec.heading_pattern));
    for(const bar of appScrollbars(ax)){await app.setValue(bar.index,'0');ax=await tree();}
    const heading=appScope(ax).split('\n').find(x=>/\d+ heading .*, Value: 1$/.test(x));
    if(!heading)throw Error('Actual scene heading unavailable');
    await app.click(index(heading));ax=await tree();guardOwnedPage(ax,url,windowUuid);
    const directory=output+'/'+spec.id;await fs.mkdir(directory);
    await fs.writeFile(directory+'/preparation.json',JSON.stringify({id:spec.id,scene_heading:heading.trim().replace(/^\d+ /,''),source,url,windowUuid}),{flag:'wx'});
    await header(directory);
    const png=installLosslessUI(app,fs,{url,output:directory,windowUuid});
    await png.capture('page-a');await png.capture('page-b');
    return {id:spec.id,heading:heading.trim().replace(/^\d+ /,'')};
  }
  return {prepare,page};
}
