// Import in cua_repl only. The bridge is an explicit tool-call boundary, not a runner.
export function installToyDriver(app, fs, bridge) {
  const source = 'https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html';
  const index = (ax, pattern) => {
    const line = ax.split('\n').find(s => pattern.test(s));
    if (!line) throw new Error('Required visible control absent: ' + pattern);
    return Number(line.trim().match(/^\d+/)[0]);
  };
  const fresh = () => app.getAXState({emit:false, disableDiffing:true});
  function identity(ax) {
    const address = ax.split('\n').find(s => s.includes('Address and search bar')) || '';
    if (!address.includes(source)) throw new Error('Source tab changed; refusing to operate other page');
  }
  const headings = ax => [...ax.matchAll(/\d+ heading (.+?), Value: (\d+)/g)]
    .map(m => ({text:m[1], level:Number(m[2])}));
  async function navigate(item, folder) {
    let ax = await fresh(); identity(ax);
    await app.pressKey('super+l'); await app.paste(source); await app.pressKey('Return');
    // URL reload restores the route, not server state, user storage or live clock.
    for(let i=0;i<8;i++) {
      ax = await fresh(); identity(ax);
      if(ax.includes('heading S16 AI 大模型预测大赛, Value: 1') && ax.includes('link 数据对比,')) break;
    }
    if(!ax.includes('heading S16 AI 大模型预测大赛, Value: 1')) throw new Error('Source home not loaded');
    await fs.writeFile(folder+'/'+item.id+'-before.ax.txt',ax);
    const pattern = new RegExp('\\d+ link '+item.label+', Value:');
    await app.click(index(ax,pattern));
    let previous=null, facts=null;
    for(let i=0;i<8;i++) {
      ax=await fresh(); identity(ax); facts=headings(ax);
      if(facts.length && JSON.stringify(facts)===JSON.stringify(previous) &&
         !facts.some(x=>x.text==='S16 AI 大模型预测大赛')) break;
      previous=facts;
    }
    if(!facts?.length || facts.some(x=>x.text==='S16 AI 大模型预测大赛'))
      throw new Error('Navigation did not reach a distinct loaded page');
    await fs.writeFile(folder+'/'+item.id+'.ax.txt',ax);
    await fs.writeFile(folder+'/'+item.id+'.png',await app.getScreenshot({emit:false}));
    return {id:item.id,headings:facts,source,reset:'navigate source home; existing browser storage retained',
      ax:item.id+'.ax.txt',screenshot:item.id+'.png'};
  }
  return async function service() {
    const names=(await fs.readdir(bridge)).filter(n=>n.endsWith('.request.json')).sort();
    for(const name of names) {
      const request=JSON.parse(await fs.readFile(bridge+'/'+name,'utf8'));
      const reply=bridge+'/'+request.id+'.reply.json';
      try {await fs.access(reply);continue;} catch {}
      const folder=request.workspace+'/native-'+request.id;
      await fs.mkdir(folder,{recursive:true});
      try {
        const results=[];
        for(const item of request.cases) results.push(await navigate(item,folder));
        await fs.writeFile(reply,JSON.stringify({results,evidence:folder}));
        return {id:request.id,role:request.role,results};
      } catch(e) {await fs.writeFile(reply,JSON.stringify({error:String(e)}));throw e;}
    }
    return {pending:false};
  };
}
