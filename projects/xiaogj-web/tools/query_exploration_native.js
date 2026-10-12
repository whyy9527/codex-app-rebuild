// Shared readonly actions; execute only in cua_repl. No expected results here.
export function queryFacts(ax) {
  const total=ax.match(/共\s*(\d+)\s*条/),page=ax.match(/第\s*(\d+)\s*\/\s*(\d+)\s*页/);
  const size=ax.match(/每页[ \t]*(\d+)/)||ax.match(/每页[ \t]*\n[ \t]*\d+ text (\d+)[ \t]*\n/);
  if(total&&page&&size)return {total:+total[1],page:+page[1],pageSize:+size[1],
    ids:[...ax.matchAll(/^\s*\d+ (?:text|cell(?: \([^)]*\))?) (S\d+)\s*$/gm)].map(m=>m[1])};
  if(ax.includes('暂时还没有相关数据，试试别的查询条件吧。'))return {
    total:null,page:null,pageSize:null,ids:[],emptyMessage:'暂时还没有相关数据，试试别的查询条件吧。'};
  return null;
}
export function installQueryExploration(app,fs,bridge) {
  const inputLine=ax=>ax.split('\n').find(s=>/\d+ text field .*学员姓名及首字母\/学号\/电话/.test(s));
  const inputValue=ax=>inputLine(ax)?.match(/Value: (.*?)(?:, Placeholder:|$)/)?.[1]||'';
  const index=(ax,re)=>{const line=ax.split('\n').find(s=>re.test(s));if(!line)throw Error('Missing control '+re);return +line.trim().match(/^\d+/)[0];};
  return async function service() {
    for(const name of (await fs.readdir(bridge)).filter(n=>n.endsWith('.request.json')).sort()) {
      const request=JSON.parse(await fs.readFile(bridge+'/'+name,'utf8')),reply=bridge+'/'+request.id+'.reply.json';
      try{await fs.access(reply);continue;}catch{}
      async function fresh(){
        const ax=await app.getAXState({emit:false,disableDiffing:true});
        const origin=request.side==='reference'?/URL: tms03\.xiaogj\.com\//:/URL: (?:127\.0\.0\.1|localhost):5183\//;
        if(!ax.split('\n').some(s=>/\d+ HTML content/.test(s)&&origin.test(s)))throw Error('Wrong selected query side');
        if(/heading 修改密码/.test(ax))throw Error('Password reminder blocks source');
        return ax;
      }
      async function click(label){const ax=await fresh();await app.click(index(ax,new RegExp('\\d+ (?:text|link|button) '+label+'(?:, Value:.*)?$')));return fresh();}
      async function stable(){let previous=null;for(let i=0;i<12;i++){const ax=await fresh(),value=queryFacts(ax);if(value&&previous&&JSON.stringify(value)===JSON.stringify(previous))return {ax,facts:value};previous=value;}throw Error('Query did not stabilize');}
      async function save(state,label){await fs.writeFile(request.out+'/'+label+'.ax.txt',state.ax);await fs.writeFile(request.out+'/'+label+'.png',await app.getScreenshot({emit:false}));}
      try {
        await fs.mkdir(request.out,{recursive:true});const rows=[];
        for(const item of request.cases){
          await click('重置');await click('查询');const baseline=await stable();await save(baseline,item.id+'-baseline');
          let ax=await fresh();await app.click(index(ax,/\d+ text field .*学员姓名及首字母\/学号\/电话/));await app.pressKey('super+a');await fresh();await app.paste(item.query);ax=await fresh();
          if(inputValue(ax)!==item.query)throw Error('Input differs; query not submitted');
          await click('查询');const result=await stable();await save(result,item.id+'-result');
          await click('重置');const reset=await stable();await save(reset,item.id+'-reset');
          rows.push({id:item.id,baseline:baseline.facts,result:result.facts,afterReset:reset.facts,inputCleared:inputValue(reset.ax)===''});
        }
        await click('查询');const restored=await stable();await save(restored,'restored');
        await fs.writeFile(reply,JSON.stringify({rows,restored:restored.facts}));return {id:request.id,side:request.side,cases:rows.length};
      }catch(error){await fs.writeFile(reply,JSON.stringify({error:String(error)}));throw error;}
    }
    return {pending:false};
  };
}
