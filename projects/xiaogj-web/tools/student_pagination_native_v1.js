// Shared native pagination actions. No expected rows or page outcomes enter this driver.
export function installStudentPagination(app, fs, bridge) {
  function index(ax, re) {
    const line = ax.split('\n').find(s => re.test(s));
    if (!line) throw new Error('Missing pagination control: '+re);
    return Number(line.trim().match(/^\d+/)[0]);
  }
  function facts(ax) {
    const total=ax.match(/共\s*(\d+)\s*条/), page=ax.match(/第\s*(\d+)\s*\/\s*(\d+)\s*页/), size=ax.match(/每页\s*(\d+)/);
    return total && page && size ? {total:+total[1],page:+page[1],pages:+page[2],pageSize:+size[1],
      ids:[...ax.matchAll(/\d+ text (S\d+)\s*$/gm)].map(m=>m[1])} : null;
  }
  return async function servicePagination() {
    for (const name of (await fs.readdir(bridge)).filter(n=>n.endsWith('.request.json')).sort()) {
      const request=JSON.parse(await fs.readFile(bridge+'/'+name,'utf8'));
      const reply=bridge+'/'+request.id+'.reply.json';
      try {await fs.access(reply);continue;} catch {}
      async function fresh() {
        const ax=await app.getAXState({emit:false,disableDiffing:true});
        const origin=request.side==='candidate' ? /URL: (?:127\.0\.0\.1|localhost):5183\// : /URL: tms03\.xiaogj\.com\//;
        if (!origin.test(ax.split('\n').find(s=>/standard window/.test(s))||'')) throw new Error('Wrong selected pagination side');
        if (/heading 修改密码/.test(ax)) throw new Error('Source password warning occludes pagination');
        return ax;
      }
      async function stable(label) {
        let before=null;
        for(let i=0;i<8;i++) {
          const ax=await fresh(),value=facts(ax);
          if(value && before && JSON.stringify(value)===JSON.stringify(before)) {
            await fs.writeFile(request.out+'/'+label+'.ax.txt',ax);
            await fs.writeFile(request.out+'/'+label+'.png',await app.getScreenshot({emit:false}));
            return value;
          }
          before=value;
        }
        throw new Error('Pagination facts did not stabilize');
      }
      async function action(step) {
        let ax=await fresh();
        if(step.type==='jump') {
          await app.click(index(ax,/\d+ text field .*按回车键跳转。/));
          await app.pressKey('super+a'); await fresh(); await app.paste(step.value);
          ax=await fresh();
          const line=ax.split('\n').find(s=>/\d+ text field .*按回车键跳转。/.test(s));
          if(line?.match(/Value: (.*?)(?:, Placeholder:|$)/)?.[1]!==step.value) throw new Error('Page input mismatch; not submitted');
          await app.pressKey('Return'); await fresh();
        } else if(step.type==='next'||step.type==='previous') {
          let target;
          if(request.side==='candidate') target=index(ax,new RegExp('\\d+ button(?: \\([^)]*\\))? '+(step.type==='next'?'下一页':'上一页')+'$'));
          else {
            const start=ax.indexOf('text 第 '),end=ax.indexOf('table',start);
            const links=ax.slice(start,end<0?undefined:end).split('\n').filter(s=>/^\s*\d+ link\s*$/.test(s));
            if(links.length!==2) throw new Error('Original pagination pair is ambiguous');
            target=Number(links[step.type==='next'?1:0].trim().match(/^\d+/)[0]);
          }
          await app.click(target); await fresh();
        } else throw new Error('Unknown pagination action');
      }
      async function baseline() {
        for(const name of ['重置','查询']) {
          const ax=await fresh();
          await app.click(index(ax,new RegExp('\\d+ (?:link|button) '+name+'(?:, Value:.*)?$')));await fresh();
        }
        await action({type:'jump',value:'1'});
      }
      try {
        await fs.mkdir(request.out,{recursive:true});
        const rows=[];
        for(const item of request.cases) {
          await baseline();const initial=await stable(item.id+'-baseline'),states=[];
          for(let i=0;i<item.actions.length;i++) {
            await action(item.actions[i]);states.push(await stable(item.id+'-step-'+i));
          }
          rows.push({id:item.id,baseline:initial,states});
        }
        await baseline();const restored=await stable('restored');
        await fs.writeFile(reply,JSON.stringify({rows,restored}));
        return {id:request.id,role:request.role,side:request.side,cases:rows.length};
      } catch(error) {await fs.writeFile(reply,JSON.stringify({error:String(error)}));throw error;}
    }
    return {pending:false};
  };
}
