// Shared real UI actions for both source and candidate; loaded in cua_repl.
export function installNavigationE2E(app, fs, bridge) {
  const fresh=()=>app.getAXState({emit:false,disableDiffing:true});
  const signatures=ax=>[...ax.matchAll(/\d+ heading (.+?), Value: (\d+)/g)].map(m=>m[1]);
  const text=ax=>ax.split('\n').flatMap(line=>{
    const m=line.match(/^\s*\d+ (?:heading|text|button|link) (.*?)(?:, Value:|, Help:|$)/);
    return m?[m[1]]:[];
  });
  return async function serviceNavigation() {
    for(const name of (await fs.readdir(bridge)).filter(n=>n.endsWith('.request.json')).sort()) {
      const req=JSON.parse(await fs.readFile(bridge+'/'+name,'utf8'));
      const reply=bridge+'/'+req.id+'.reply.json';
      try {await fs.access(reply);continue;} catch {}
      const states={};
      try {
        for(const item of req.cases) {
          let ax=await fresh();
          const address=ax.split('\n').find(s=>s.includes('Address and search bar'))||'';
          if(!address.includes(req.guard)) throw new Error('Bound tab changed; current origin is not the requested endpoint');
          await app.pressKey('super+l');await app.paste(req.url);await app.pressKey('Return');
          for(let i=0;i<8;i++) {
            ax=await fresh();
            if(ax.includes('heading S16 AI 大模型预测大赛, Value: 1')&&ax.includes('link 数据对比,'))break;
          }
          if(!ax.includes('heading S16 AI 大模型预测大赛, Value: 1'))throw new Error('Home preparation unavailable');
          const label=item.label;
          const line=ax.split('\n').find(s=>s.includes(' link '+label+', Value:'));
          if(!line)throw new Error('Missing navigation '+label);
          await app.click(Number(line.trim().match(/^\d+/)[0]));
          let previous=null, stable=false;
          for(let i=0;i<8;i++){
            ax=await fresh();const heads=signatures(ax);
            if(heads.length&&!heads.includes('S16 AI 大模型预测大赛')&&JSON.stringify(heads)===previous){stable=true;break;}
            previous=JSON.stringify(heads);
          }
          if(!stable)throw new Error('Page did not reach repeated complete headings: '+item.id);
          await fs.writeFile(req.workspace+'/'+item.id+'.ax.txt',ax);
          const bytes=await app.getScreenshot({emit:false});
          const extension=bytes[0]===255&&bytes[1]===216?'jpg':'png';
          await fs.writeFile(req.workspace+'/'+item.id+'.'+extension,bytes);
          const after=await fresh();
          states[item.id]={accessible_text:text(ax),headings:signatures(ax),
            state_consistent:JSON.stringify(signatures(ax))===JSON.stringify(signatures(after)),
            image:req.workspace+'/'+item.id+'.'+extension,ax:req.workspace+'/'+item.id+'.ax.txt'};
        }
        await fs.writeFile(reply,JSON.stringify({states,preparation:'navigate home before each primary nav action; browser storage retained'}));
        return {endpoint:req.endpoint,states:Object.fromEntries(Object.entries(states).map(([k,v])=>[k,v.headings]))};
      }catch(e){await fs.writeFile(reply,JSON.stringify({error:String(e),states}));throw e;}
    }
    return {pending:false};
  };
}
