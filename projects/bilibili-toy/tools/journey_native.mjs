// Shared native E2E: actual actions and facts, with no expected answers in the driver.
export function installJourneyE2E(app, fs, bridge) {
  const tree=()=>app.getAXState({emit:false,disableDiffing:true});
  function guard(ax, req) {
    const address=ax.split('\n').find(s=>s.includes('Address and search bar'))||'';
    if(!address.includes(req.guard))throw new Error('Requested endpoint is no longer selected');
  }
  function facts(ax) {
    const text=ax.split('\n').flatMap(line=>{
      const m=line.match(/^\s*\d+ (?:heading|text|button|link) (.*?)(?:, Value:|, Help:|$)/);
      return m?[m[1]]:[];
    });
    const elements={};
    for(const label of ['BP','比赛','结果','数据']){
      const line=ax.split('\n').find(s=>s.includes('toggle button '+label+', Value:'));
      if(line)elements[label]={role:'button',checked:line.includes('Value: 1')};
    }
    const idle=ax.split('\n').find(s=>s.includes('checkbox 闲置 60 秒后自动换台, Value:'));
    if(idle)elements.idle={role:'checkbox',checked:idle.includes('Value: 1')};
    const playback=ax.split('\n').find(s=>/button  (播放|暂停), Help:/.test(s));
    if(playback)elements.playback={role:'button',value:playback.includes(' 暂停,')?'暂停':'播放'};
    return {accessible_text:text,elements};
  }
  return async function serviceJourney(){
    for(const name of (await fs.readdir(bridge)).filter(n=>n.endsWith('.request.json')).sort()){
      const req=JSON.parse(await fs.readFile(bridge+'/'+name,'utf8'));
      const reply=bridge+'/'+req.id+'.reply.json';
      try{await fs.access(reply);continue;}catch{}
      if(req.suite!=='journeys')continue;
      const states={},actions=[];
      try{
        let ax=await tree();guard(ax,req);
        // Close source-owned expanded host before preparation when present.
        const close=ax.split('\n').find(s=>/\d+ button 收起$/.test(s));
        if(close){await app.click(Number(close.trim().match(/^\d+/)[0]));ax=await tree();guard(ax,req);}
        await app.pressKey('super+l');await app.paste(req.url);await app.pressKey('Return');
        for(let i=0;i<8;i++){
          ax=await tree();guard(ax,req);
          if(ax.includes('heading S16 AI 大模型预测大赛, Value: 1'))break;
        }
        if(!ax.includes('heading S16 AI 大模型预测大赛, Value: 1'))throw new Error('Homepage preparation unavailable');
        for(const item of req.cases)for(const step of item.steps){
          ax=await tree();guard(ax,req);
          if(step.action==='goto_query'){
            if(!step.query.startsWith('?'))throw new Error('Expected an explicit query on the selected endpoint');
            await app.pressKey('super+l');await app.paste(req.url+step.query);await app.pressKey('Return');
            for(let i=0;i<8;i++){
              ax=await tree();guard(ax,req);
              if(ax.includes(step.ready))break;
            }
            if(!ax.includes(step.ready))throw new Error('Query entry did not reach its observed ready state');
            actions.push({case:item.id,query:step.query,performed:true});
          }else{
            const pattern=new RegExp(step.match);
            const line=ax.split('\n').find(s=>pattern.test(s));
            if(!line&&step.action!=='click_if_present')throw new Error('Control absent: '+step.match);
            if(line){await app.click(Number(line.trim().match(/^\d+/)[0]));ax=await tree();guard(ax,req);}
            actions.push({case:item.id,match:step.match,performed:!!line});
          }
          if(step.capture){
            const state=facts(ax);
            const bytes=await app.getScreenshot({emit:false});
            const extension=bytes[0]===255&&bytes[1]===216?'jpg':'png';
            const image=req.workspace+'/'+step.capture+'.'+extension;
            await fs.writeFile(image,bytes);
            await fs.writeFile(req.workspace+'/'+step.capture+'.ax.txt',ax);
            const after=await tree();guard(after,req);
            states[step.capture]={...state,image,ax:req.workspace+'/'+step.capture+'.ax.txt',
              state_consistent:JSON.stringify(state.elements)===JSON.stringify(facts(after).elements)};
          }
        }
        await fs.writeFile(reply,JSON.stringify({states,actions,preparation:'same native route/actions; pause, idle off, preseason, 1x before event/phase traversal'}));
        return {endpoint:req.endpoint,states:Object.keys(states),actions:actions.length};
      }catch(e){await fs.writeFile(reply,JSON.stringify({error:String(e),states,actions}));throw e;}
    }
    return {pending:false};
  };
}
