// Loaded and executed only inside cua_repl. All UI actions use the native app.
export function installStudentRsiDriver(app, fs, bridgeDirectory) {
  async function fresh() {
    const ax = await app.getAXState({ emit: false, disableDiffing: true });
    if (!/standard window .*URL: tms03\.xiaogj\.com\//.test(ax))
      throw new Error("Source tab is not the selected native window");
    if (/heading 修改密码/.test(ax))
      throw new Error("Visible password warning blocks the source; dismiss it natively before continuing");
    return ax;
  }
  function element(ax, pattern) {
    const line = ax.split("\n").find((s) => pattern.test(s));
    if (!line) throw new Error("Required source control is absent: " + pattern);
    return Number(line.trim().match(/^\d+/)[0]);
  }
  function facts(ax) {
    const total = ax.match(/text 共\s*(\d+)\s*条/);
    const page = ax.match(/text 第\s*(\d+)\s*\/\s*(\d+)\s*页/);
    const size = ax.match(/text 每页\s*(\d+)/);
    if (!total || !page || !size) {
      if (/text 暂时还没有相关数据，试试别的查询条件吧。/.test(ax))
        return { total: null, page: null, pageSize: null, ids: [],
          emptyMessage: "暂时还没有相关数据，试试别的查询条件吧。" };
      return null;
    }
    return { total: Number(total[1]), page: Number(page[1]), pageSize: Number(size[1]),
      ids: [...ax.matchAll(/\d+ text (S\d+)\s*$/gm)].map(m => m[1]) };
  }
  async function stable() {
    let previous = null;
    for (let i = 0; i < 8; i++) {
      const ax = await fresh();
      const value = facts(ax);
      if (value && previous && JSON.stringify(value) === JSON.stringify(previous))
        return { ax, facts: value };
      previous = value;
    }
    throw new Error("Source list did not reach two matching complete native observations");
  }
  async function query(value, folder, name) {
    let ax = await fresh();
    await app.click(element(ax, /\d+ link 重置$/));
    ax = await fresh();
    const cleared = ax.split("\n").find(s => /\d+ text field .*学员姓名及首字母\/学号\/电话/.test(s));
    if (/Value: [^,\n]+/.test(cleared || ""))
      throw new Error("Reset did not clear the source query input");
    // Reset clears filters only; submitting the empty query restores actual results.
    await app.click(element(ax, /\d+ link 查询$/));
    const baseline = await stable();
    await fs.writeFile(folder + "/" + name + "-baseline.ax.txt", baseline.ax);
    ax = baseline.ax;
    await app.click(element(ax, /\d+ text field .*学员姓名及首字母\/学号\/电话/));
    await app.pressKey("super+a");
    await fresh();
    await app.paste(value);
    ax = await fresh();
    const input = ax.split("\n").find(s => /\d+ text field .*学员姓名及首字母\/学号\/电话/.test(s));
    const entered = input?.match(/Value: (.*?)(?:, Placeholder:|$)/)?.[1];
    if (entered !== value) throw new Error("Native query input differs from the requested probe; no query submitted");
    await app.click(element(ax, /\d+ link 查询$/));
    const result = await stable();
    await fs.writeFile(folder + "/" + name + "-result.ax.txt", result.ax);
    await fs.writeFile(folder + "/" + name + "-result.png", await app.getScreenshot({ emit: false }));
    return { baseline: baseline.facts, result: result.facts };
  }
  return async function serviceStudentRsiRequest() {
    const names = (await fs.readdir(bridgeDirectory)).filter(n => n.endsWith(".request.json")).sort();
    for (const name of names) {
      const request = JSON.parse(await fs.readFile(bridgeDirectory + "/" + name, "utf8"));
      const reply = bridgeDirectory + "/" + request.id + ".reply.json";
      try { await fs.access(reply); continue; } catch {}
      try {
        const folder = request.workspace + "/native-" + request.id;
        await fs.mkdir(folder, { recursive: true });
        const results = [];
        for (const item of request.cases)
          results.push(await query(item.query, folder, item.id));
        await fs.writeFile(reply, JSON.stringify({ results, evidence: folder }));
        return { id: request.id, role: request.role, cases: results.length };
      } catch (e) {
        await fs.writeFile(reply, JSON.stringify({ error: String(e) }));
        throw e;
      }
    }
    return { pending: false };
  };
};
