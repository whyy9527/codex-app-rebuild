// Shared E2E actions; execute in cua_repl against the selected native app.
// Expectations are intentionally absent. The comparator owns assertions.
export function installStudentQueryE2E(app, fs, bridgeDirectory) {
  function index(ax, pattern) {
    const line = ax.split("\n").find(s => pattern.test(s));
    if (!line) throw new Error("Required query control absent: " + pattern);
    return Number(line.trim().match(/^\d+/)[0]);
  }
  function facts(ax) {
    const total = ax.match(/共\s*(\d+)\s*条/);
    const page = ax.match(/第\s*(\d+)\s*\/\s*(\d+)\s*页/);
    const size = ax.match(/每页\s*(\d+)/);
    if (total && page && size) return {
      total: Number(total[1]), page: Number(page[1]), pageSize: Number(size[1]),
      ids: [...ax.matchAll(/\d+ text (S\d+)\s*$/gm)].map(m => m[1]),
    };
    if (/text 暂时还没有相关数据，试试别的查询条件吧。/.test(ax))
      return { total: null, page: null, pageSize: null, ids: [],
        emptyMessage: "暂时还没有相关数据，试试别的查询条件吧。" };
    const error = ax.match(/text (该查询的学员数据尚未准备好|学员数据尚未准备好|学员数据读取失败)/);
    return error ? { error: error[1] } : null;
  }
  return async function serviceStudentQueryE2E() {
    for (const filename of (await fs.readdir(bridgeDirectory)).filter(n => n.endsWith('.request.json')).sort()) {
      const request = JSON.parse(await fs.readFile(bridgeDirectory + '/' + filename, 'utf8'));
      const reply = bridgeDirectory + '/' + request.id + '.reply.json';
      try { await fs.access(reply); continue; } catch {}
      async function fresh() {
        const ax = await app.getAXState({emit:false, disableDiffing:true});
        const origin = request.side === 'reference' ? /URL: tms03\.xiaogj\.com\// : /URL: (?:127\.0\.0\.1|localhost):5183\//;
        if (!origin.test(ax.split('\n').find(s => /standard window/.test(s)) || ''))
          throw new Error('Selected native tab does not match requested side');
        if (/heading 修改密码/.test(ax))
          throw new Error('Password warning blocks source UI; dismiss natively before replay');
        return ax;
      }
      async function stable() {
        let previous = null;
        for (let i=0; i<8; i++) {
          const ax = await fresh(), value = facts(ax);
          if (value && previous && JSON.stringify(value) === JSON.stringify(previous))
            return {ax, facts:value};
          previous = value;
        }
        throw new Error('Query state did not stabilize; preserve unavailable result');
      }
      async function click(name) {
        const ax = await fresh();
        await app.click(index(ax, new RegExp('\\d+ (?:link|button) '+name+'(?:, Value:.*)?$')));
        return fresh();
      }
      async function save(state, label) {
        await fs.writeFile(request.out+'/'+label+'.ax.txt',state.ax);
        await fs.writeFile(request.out+'/'+label+'.png',await app.getScreenshot({emit:false}));
      }
      try {
        const rows=[];
        for (const item of request.cases) {
          await click('重置'); await click('查询');
          const baseline=await stable(); await save(baseline,item.id+'-baseline');
          let ax=await fresh();
          await app.click(index(ax,/\d+ text field .*学员姓名及首字母\/学号\/电话/));
          await app.pressKey('super+a'); await fresh(); await app.paste(item.query);
          ax=await fresh();
          const input=ax.split('\n').find(s=>/\d+ text field .*学员姓名及首字母\/学号\/电话/.test(s));
          if (input?.match(/Value: (.*?)(?:, Placeholder:|$)/)?.[1] !== item.query)
            throw new Error('Actual query input differs; query not submitted');
          await click('查询');
          const result=await stable(); await save(result,item.id+'-result');
          await click('重置');
          const reset=await stable(); await save(reset,item.id+'-reset');
          const cleared=reset.ax.split('\n').find(s=>/\d+ text field .*学员姓名及首字母\/学号\/电话/.test(s));
          rows.push({id:item.id, baseline:baseline.facts, result:result.facts,
            afterReset:reset.facts, inputCleared:!(/Value: [^,\n]+/.test(cleared||''))});
        }
        await click('查询'); // Restore default results after the final reset.
        const restored=await stable(); await save(restored,'restored');
        await fs.writeFile(reply,JSON.stringify({rows,restored:restored.facts}));
        return {id:request.id,side:request.side,cases:rows.length};
      } catch(error) {
        await fs.writeFile(reply,JSON.stringify({error:String(error)}));
        throw error;
      }
    }
    return {pending:false};
  };
}
