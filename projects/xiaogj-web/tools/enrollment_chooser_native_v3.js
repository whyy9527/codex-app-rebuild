// E2E guard revision: aria-modal hides breadcrumb; retain actual origin and route.
function imageSize(bytes) {
  const data = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (data.getUint32(0) === 0x89504e47) return [data.getUint32(16), data.getUint32(20)];
  if (data.getUint16(0) !== 0xffd8) throw Error('Unknown capture image encoding');
  let offset = 2;
  while (offset < bytes.length) {
    if (bytes[offset++] !== 0xff) continue;
    while (bytes[offset] === 0xff) offset++;
    const marker = bytes[offset++];
    if ([0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf].includes(marker)) return [data.getUint16(offset+5),data.getUint16(offset+3)];
    if (marker === 0xd9 || marker === 0xda) break;
    offset += data.getUint16(offset);
  }
  throw Error('Capture dimensions unavailable');
}
// CUA-only readonly selector probes. Captions are actual facts, never verdicts.
function captions(ax) {
  return ax.split('\n').map(line => line.match(/^\s*\d+ (?:text|button|link|heading|cell(?: \([^)]*\))?|container) (.*)$/)?.[1])
    .filter(Boolean).map(text => text.replace(/, (?:Value|ID|Secondary Actions):.*$/, '').replace(/[\ue000-\uf8ff]/g, '').trim()).filter(Boolean);
}
export function installEnrollmentChooser(app, fs, bridge) {
  return async function service() {
    for (const name of (await fs.readdir(bridge)).filter(name => name.endsWith('.request.json')).sort()) {
      const request = JSON.parse(await fs.readFile(bridge + '/' + name, 'utf8'));
      const reply = bridge + '/' + request.id + '.reply.json';
      try { await fs.access(reply); continue; } catch {}
      async function fresh() {
        const ax = await app.getAXState({ emit: false, disableDiffing: true });
        const origin = request.side === 'reference' ? /URL: tms03\.xiaogj\.com\// : /URL: 127\.0\.0\.1:5183\//;
        const page = ax.split('\n').find(line => /HTML content/.test(line) && origin.test(line));
        const enrollment = /当前位置.*新学员报名/.test(ax) || Boolean(page && /workspace\/(?:新学员报名|%E6%96%B0%E5%AD%A6%E5%91%98%E6%8A%A5%E5%90%8D)/i.test(page) && /(?:container|heading) 选择(?:课程|物品)/.test(ax));
        if (!page || !enrollment) throw Error('Wrong enrollment chooser side');
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
          const before = await fresh(); await save(before, item.id + '-baseline');
          const baseline = new Set(captions(before));
          const facts = ax => ({ added: [...new Set(captions(ax).filter(text => !baseline.has(text)))].sort() });
          const label = item.method === 'courses' ? '选课' : item.method === 'items' ? '选物品' : null;
          if (!label) throw Error('Unknown chooser');
          const line = before.split('\n').find(line => new RegExp('\\d+ (?:button|link|text) ' + label + '(?:, Value:.*)?$').test(line));
          if (line) await app.click(+line.trim().match(/^\d+/)[0]);
          else {
            // Observed 1324x833 Safari blank enrollment toolbar. No hidden selector guessing.
            const pixels = imageSize(await app.getScreenshot({ emit: false }));
            if (![[2648,1666],[1324,833]].some(size => size[0] === pixels[0] && size[1] === pixels[1])) throw Error('Unreviewed native capture geometry');
            const scale = pixels[0] / 1324;
            await app.click((item.method === 'courses' ? [927, 374] : [1089, 374]).map(point => point * scale));
          }
          let opened = await fresh(), previous = null;
          for (let i = 0; i < 10; i++) {
            const value = facts(opened);
            if (value.added.length && JSON.stringify(value) === previous) break;
            previous = JSON.stringify(value); opened = await fresh();
          }
          await save(opened, item.id + '-opened');
          await app.pressKey('Escape'); let after = await fresh();
          if (facts(after).added.length) {
            const oldLines = new Set(before.split('\n').map(line => line.trim().replace(/^\d+ /, '')));
            const close = after.split('\n').filter(line => /\d+ (?:button|link|text) ×(?:,.*)?$/.test(line) && !oldLines.has(line.trim().replace(/^\d+ /, '')));
            if (close.length !== 1) throw Error('Chooser did not dismiss; no unique observed close control');
            await app.click(+close[0].trim().match(/^\d+/)[0]); after = await fresh();
          }
          await save(after, item.id + '-dismissed');
          rows.push({ id: item.id, baseline: facts(before), result: facts(opened), afterDismiss: facts(after) });
        }
        await fs.writeFile(reply, JSON.stringify({ rows, restored: rows.at(-1).afterDismiss }));
        return { id: request.id, side: request.side, cases: rows.length };
      } catch (error) {
        await fs.writeFile(reply, JSON.stringify({ error: String(error) })); throw error;
      }
    }
    return { pending: false };
  };
}
