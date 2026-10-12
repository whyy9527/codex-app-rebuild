// Run only through cua_repl. Captures actual options; never chooses a value.
export function gradeFacts(ax) {
  return { options: [...ax.matchAll(/^\s*\d+ (?:menu item|option)(?: \([^)]*\))? (.*)$/gm)]
    .map(match => match[1].replace(/, (?:Value|ID|Secondary Actions):.*$/, '').trim()) };
}

export function installEnrollmentGrade(app, fs, bridge) {
  return async function service() {
    for (const name of (await fs.readdir(bridge)).filter(name => name.endsWith('.request.json')).sort()) {
      const request = JSON.parse(await fs.readFile(bridge + '/' + name, 'utf8'));
      const reply = bridge + '/' + request.id + '.reply.json';
      try { await fs.access(reply); continue; } catch {}
      const fresh = () => app.getAXState({ emit: false, disableDiffing: true });
      async function guarded() {
        const ax = await fresh();
        const origin = request.side === 'reference' ? /URL: tms03\.xiaogj\.com\// : /URL: 127\.0\.0\.1:5183\//;
        if (!ax.split('\n').some(line => /HTML content/.test(line) && origin.test(line)) || !/当前位置.*新学员报名/.test(ax)) throw Error('Wrong blank enrollment source');
        return ax;
      }
      async function save(ax, label) {
        await fs.writeFile(request.out + '/' + label + '.ax.txt', ax);
        await fs.writeFile(request.out + '/' + label + '.png', await app.getScreenshot({ emit: false }));
      }
      try {
        await fs.mkdir(request.out, { recursive: true });
        const rows = [];
        for (const item of request.cases) {
          const before = await guarded();
          await save(before, item.id + '-baseline');
          const line = before.split('\n').find(line => /\d+ pop up button/.test(line));
          if (!line) throw Error('Grade native popup control not observed');
          const index = +line.trim().match(/^\d+/)[0];
          if (item.method === 'click') await app.click(index);
          else if (item.method === 'keyboard') {
            // Focus only; Escape dismisses a possible click-opened menu first.
            await app.click(index); await fresh(); await app.pressKey('Escape'); await guarded();
            await app.pressKey('space');
          } else throw Error('Unknown opening method');
          const opened = await fresh(); await save(opened, item.id + '-opened');
          await app.pressKey('Escape'); const after = await guarded();
          await save(after, item.id + '-dismissed');
          rows.push({ id: item.id, baseline: gradeFacts(before), result: gradeFacts(opened), afterDismiss: gradeFacts(after) });
        }
        const restored = gradeFacts(await guarded());
        await fs.writeFile(reply, JSON.stringify({ rows, restored }));
        return { id: request.id, side: request.side, cases: rows.length };
      } catch (error) {
        await fs.writeFile(reply, JSON.stringify({ error: String(error) })); throw error;
      }
    }
    return { pending: false };
  };
}
