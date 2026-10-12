// Shared readonly detail journey. Expectations stay with the independent comparator.
export function installStudentDetail(app, fs, bridge) {
  function index(ax, re) {
    const line=ax.split('\n').find(s=>re.test(s));
    if(!line)throw new Error('Detail control absent: '+re);
    return Number(line.trim().match(/^\d+/)[0]);
  }
  function list(ax) {
    const total=ax.match(/共\s*(\d+)\s*条/), page=ax.match(/第\s*(\d+)\s*\/\s*(\d+)\s*页/), size=ax.match(/每页\s*(\d+)/);
    return total&&page&&size ? {total:+total[1],page:+page[1],pageSize:+size[1],
      ids:[...ax.matchAll(/\d+ text (S\d+)\s*$/gm)].map(m=>m[1])} : null;
  }
  function text(ax) {
    const content=ax.split('\n').filter(s=>/^\s*\d+ text /.test(s)).map(s=>s.replace(/^\s*\d+ text /,''));
    return content.join(' ').replace(/\s+/g,' ').trim();
  }
  return async function serviceDetail() {
    for(const name of (await fs.readdir(bridge)).filter(n=>n.endsWith('.request.json')).sort()) {
      const request=JSON.parse(await fs.readFile(bridge+'/'+name,'utf8')),reply=bridge+'/'+request.id+'.reply.json';
      try {await fs.access(reply);continue;} catch {}
      async function fresh() {
        const ax=await app.getAXState({emit:false,disableDiffing:true});
        const re=request.side==='candidate'?/URL: (?:127\.0\.0\.1|localhost):5183\//:/URL: tms03\.xiaogj\.com\//;
        if(!re.test(ax.split('\n').find(s=>/standard window/.test(s))||''))throw new Error('Wrong selected detail side');
        if(/heading 修改密码/.test(ax))throw new Error('Password notice occludes source');
        return ax;
      }
      async function capture(stage,label) {
        let before=null;
        for(let i=0;i<10;i++) {
          const ax=await fresh(),value=stage==='list'?list(ax):{text:text(ax)};
          const ready=value&&(stage==='list'||(value.text.includes('账户余额：')&&value.text.includes(stage==='expanded'?'联系信息':'只显示当前就读班级')));
          if(ready&&before&&JSON.stringify(value)===JSON.stringify(before)) {
            await fs.writeFile(request.out+'/'+label+'.ax.txt',ax);
            await fs.writeFile(request.out+'/'+label+'.png',await app.getScreenshot({emit:false}));
            return value;
          }
          before=ready?value:null;
        }
        throw new Error('Detail '+stage+' did not stabilize');
      }
      async function click(pattern) {const ax=await fresh();await app.click(index(ax,pattern));return fresh();}
      async function collapseIfExpanded() {
        let ax=await fresh();
        if(/\d+ (?:link|button) 展开$/m.test(ax))return;
        if(!text(ax).includes('基本信息')||!text(ax).includes('联系信息'))return;
        if(request.side==='candidate') {
          await click(/\d+ (?:link|button) 收起$/);
        } else {
          const png=await app.getScreenshot({emit:false});
          const dimensions=new DataView(png.buffer,png.byteOffset,png.byteLength);
          if(dimensions.getUint32(16)!==2940||dimensions.getUint32(20)!==1666)
            throw new Error('Source collapse coordinates require observed 2940x1666 screenshot');
          await app.click([2790,662]);await fresh();
        }
        ax=await fresh();
        if(!/\d+ (?:link|button) 展开$/m.test(ax))throw new Error('Collapse preparation not observed');
      }
      async function backIfOpen() {
        const ax=await fresh();
        if(/\d+ (?:link|button) .*返回\s*$/m.test(ax))await click(/\d+ (?:link|button) .*返回\s*$/);
      }
      try {
        await fs.mkdir(request.out,{recursive:true});const rows=[];
        for(const item of request.cases) {
          await backIfOpen();
          for(const label of ['重置','查询'])await click(new RegExp('\\d+ (?:link|button) '+label+'(?:, Value:.*)?$'));
          const baseline=await capture('list',item.id+'-baseline');
          const ax=await fresh();const line=ax.split('\n').find(s=>new RegExp('\\d+ (?:link|button) ').test(s)&&s.trim().endsWith(' '+item.entry));
          if(!line)throw new Error('Observed student entry absent');
          await app.click(Number(line.trim().match(/^\d+/)[0]));await fresh();
          await collapseIfExpanded();
          const overview=await capture('overview',item.id+'-overview');const states=[overview];
          for(const action of item.actions) {
            if(action.type!=='expand')throw new Error('Unsupported readonly detail action');
            await click(/\d+ (?:link|button) 展开$/);
            states.push(await capture('expanded',item.id+'-expanded'));
          }
          await collapseIfExpanded();await backIfOpen();
          const restored=await capture('list',item.id+'-restored');rows.push({id:item.id,baseline,states,restored});
        }
        const restored=await capture('list','restored');
        await fs.writeFile(reply,JSON.stringify({rows,restored}));return {id:request.id,role:request.role,side:request.side,cases:rows.length};
      } catch(error) {await fs.writeFile(reply,JSON.stringify({error:String(error)}));throw error;}
    }
    return {pending:false};
  };
}
