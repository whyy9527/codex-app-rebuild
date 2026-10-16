// Same actual UI traversal for source and candidate; no expected content input.
import {installChannelUI} from './channel_native.mjs';

export function seriesControls(ax) {
  const lines=ax.split('\n');
  const first=lines.find((line,i)=>/^\s*\d+ button .+/.test(line)&&/· Bo[135](?:\s|$)/.test(lines[i+1]||''));
  const games=lines.flatMap(line=>{
    const match=line.match(/^\s*\d+ link 第\s+(\d+)\s+局\s+([^,]+)\s+胜(?: [^,]+)?, Value:/);
    return match?[{number:Number(match[1]),label:match[0].trim().replace(/^\d+ /,'')}]:[];
  });
  return {first_series:first?.trim().replace(/^\d+ /,''),games};
}
export function installDetailsUI(app,fs,options) {
  const ui=installChannelUI(app,fs,options);
  const tree=()=>app.getAXState({emit:false,disableDiffing:true});
  async function model(model) {
    if(!/^[a-z]+$/.test(model.id))throw Error('Invalid model case ID');
    await ui.click(/link 首页, Value:/);
    await ui.selectModel(model.label);
    await ui.navigate('赛程赛果');
    const schedule=await tree(),first=seriesControls(schedule).first_series;
    if(!first)throw Error('No actual series button');
    await fs.mkdir(options.output,{recursive:true});
    await fs.writeFile(options.output+'/'+model.id+'-schedule-entry.ax.txt',schedule,{flag:'wx'});
    const escaped=first.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    await ui.click(new RegExp('^\\s*\\d+ '+escaped+'$'));
    await ui.waitFor(/link 第\s+1\s+局/);
    const series=await tree(),games=seriesControls(series).games;
    if(!games.length||games.some((game,i)=>game.number!==i+1))throw Error('Actual game navigation incomplete');
    await ui.collect(model.id+'-series-collapsed');
    await ui.click(/button 展开全文 ↓$/);
    await ui.collect(model.id+'-series-expanded');
    for(const game of games) {
      await ui.click(new RegExp('link 第\\s+'+game.number+'\\s+局'));
      await ui.waitFor(new RegExp('text 第\\s+'+game.number+'\\s+局'));
      await ui.collect(model.id+'-game-'+game.number);
    }
    const actions={model,first_series:first,games,selection:'First actual series in complete schedule; game list read from actual series links.'};
    await fs.writeFile(options.output+'/'+model.id+'-actions.json',JSON.stringify(actions),{flag:'wx'});
    return {model:model.id,first_series:first,games:games.length,states:games.length+2};
  }
  return {prepare:ui.prepare,model};
}
