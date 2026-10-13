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
export function installEnrollmentAmounts(app, fs, bridge) {
  return async function service() {
    for (const name of (await fs.readdir(bridge)).filter(name => name.endsWith('.request.json')).sort()) {
      const request = JSON.parse(await fs.readFile(bridge + '/' + name, 'utf8'));
      const reply = bridge + '/' + request.id + '.reply.json';
      try { await fs.access(reply); continue; } catch {}
      async function fresh(preparing = false) {
        let ax = await app.getAXState({ emit: false, disableDiffing: true });
        const origin = request.side === 'reference' ? /URL: tms03\.xiaogj\.com\// : /URL: 127\.0\.0\.1:5183\//;
        let page = ax.split('\n').find(line => /HTML content/.test(line) && origin.test(line));
        if (preparing && !page) {
          for (let i = 0; i < 30 && !page; i++) {
            if (/HTML content.*URL:/.test(ax)) throw Error('Different live page during preparation');
            await app.getScreenshot({ emit: false });
            ax = await app.getAXState({ emit: false, disableDiffing: true });
            page = ax.split('\n').find(line => /HTML content/.test(line) && origin.test(line));
          }
        }
        const enrollment = /当前位置.*新学员报名/.test(ax) || Boolean(page && /workspace\/(?:新学员报名|%E6%96%B0%E5%AD%A6%E5%91%98%E6%8A%A5%E5%90%8D)/i.test(page) && /(?:container|heading) 选择(?:课程|物品)/.test(ax));
        if (!page || (!preparing && !enrollment)) throw Error('Wrong enrollment chooser side');
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
          for (let i = 0; i < 30; i++) {
            const value = facts(opened);
            if (/heading 选择(?:课程|物品),/.test(opened) && (opened.slice(opened.search(/heading 选择(?:课程|物品),/)).match(/\d+ checkbox/g) ?? []).length >= 2 && JSON.stringify(value) === previous) break;
            previous = JSON.stringify(value); await app.getScreenshot({ emit: false }); opened = await fresh();
          }
          await save(opened, item.id + '-opened');
          function selection(ax) {
            const match = ax.match(/\d+ heading 选择(?:课程|物品),/);
            if (!match) throw Error('Actual chooser heading missing');
            const dialog = ax.slice(match.index);
            const count = dialog.match(/已选择[：:]\s*(\d+)/);
            const checked = dialog.split('\n').filter(line => /\d+ checkbox/.test(line) && /(?:Value: 1|checkbox 1)(?:,|$)/.test(line)).length;
            return { count: count ? Number(count[1]) : null, checked };
          }
          const heading = opened.match(/\d+ heading 选择(?:课程|物品),/);
          if (!heading) throw Error('Actual chooser heading missing');
          const dialog = opened.slice(heading.index);
          const table = dialog.match(/\d+ table\n/);
          if (!table) throw Error('Observed catalog table missing');
          const boxes = dialog.slice(table.index).split('\n').filter(line => /\d+ checkbox/.test(line));
          if (boxes.length < 2) throw Error('No actual catalog row checkbox');
          await app.click(Number(boxes[1].trim().match(/^\d+/)[0]));
          const selected = await fresh(); await save(selected, item.id + '-selected');
          const selectedHeading = selected.match(/\d+ heading 选择(?:课程|物品),/);
          const confirm = selected.slice(selectedHeading.index).split('\n').find(line => /\d+ (?:button|text|link) 确定(?:,.*)?$/.test(line));
          if (!confirm) throw Error('Observed chooser confirm control missing');
          await app.click(Number(confirm.trim().match(/^\d+/)[0]));
          let confirmed = await fresh(), confirmedPrevious = null;
          for (let i = 0; i < 15; i++) {
            const value = JSON.stringify(captions(confirmed));
            if (!/heading 选择(?:课程|物品),/.test(confirmed) && !confirmed.includes('请选择要收费的课程或物品') && value === confirmedPrevious) break;
            confirmedPrevious = value; confirmed = await fresh();
          }
          await save(confirmed, item.id + '-confirmed');
          function billingFacts(ax) {
            const table = ax.match(/\d+ table\n/);
            if (!table) throw Error('Actual billing table missing');
            const billing = ax.slice(table.index).split(/\n\s*\d+ (?:button 报名|image WindowControlShadowView)/)[0];
            const rowStarts = [...billing.matchAll(/\d+ row \(selectable\)/g)];
            if (rowStarts.length !== 2) throw Error('Expected one actual billing entry');
            const entry = billing.slice(rowStarts[1].index);
            const cells = entry.split(/\n\s*\d+ cell \(selectable\)/).slice(1);
            if (cells.length < 13) throw Error('Incomplete billing cells');
            const value = index => {
              const field = cells[index].split('\n').find(line => /\d+ text field \(settable\)/.test(line)) ?? '';
              const explicit = field.match(/Value: ([^,\n]*)/);
              if (explicit) return explicit[1];
              return field.match(/text field \(settable\) (-?\d+(?:\.\d+)?)$/)?.[1] ?? '';
            };
            const plain = index => cells[index].split('\n')[0].trim().replace(/^Value: /, '');
            return { price: plain(3), quantity: value(4), discount: value(8), amount: plain(9),
              inputs: (entry.match(/\d+ text field/g) ?? []).length };
          }
          async function editField(position, value) {
            const ax = await fresh();
            const table = ax.match(/\d+ table\n/);
            const fields = ax.slice(table.index).split('\n').filter(line => /\d+ text field \(settable\)/.test(line));
            if (!fields[position]) throw Error('Observed billing input missing');
            await app.click(Number(fields[position].trim().match(/^\d+/)[0]));
            await app.pressKey('super+a'); await app.typeText(value); await app.pressKey('Tab');
            return await fresh();
          }
          confirmed = await editField(0, item.quantity);
          if (item.discount !== null) confirmed = await editField(1, item.discount);
          let amountPrevious = null;
          for (let i = 0; i < 10; i++) {
            const value = JSON.stringify(billingFacts(confirmed));
            if (value === amountPrevious) break;
            amountPrevious = value; confirmed = await fresh();
          }
          await save(confirmed, item.id + '-edited');
          const result = billingFacts(confirmed);
          // Refresh only discards the unsaved local enrollment form; no server reset is claimed.
          await app.pressKey('super+r'); let recovery = await fresh(true);
          if (request.side === 'reference') {
            for (let i = 0; i < 30 && !/heading 修改密码/.test(recovery); i++) {
              await app.getScreenshot({ emit: false }); recovery = await fresh(true);
            }
            if (!/heading 修改密码/.test(recovery)) throw Error('Observed refresh password reminder did not appear');
          }
          await save(recovery, item.id + '-refreshed');
          const reminder = recovery.match(/\d+ heading 修改密码/);
          if (reminder) {
            const cancel = recovery.slice(reminder.index).split('\n').find(line => /\d+ (?:text|button) 取消(?:,.*)?$/.test(line));
            if (!cancel) throw Error('Password reminder cancel missing');
            await app.click(Number(cancel.trim().match(/^\d+/)[0])); recovery = await fresh(true);
          }
          for (let i = 0; i < 30 && !/当前位置.*新学员报名/.test(recovery) && !/\d+ button 新学员报名(?:,.*)?$/m.test(recovery); i++) {
            await app.getScreenshot({ emit: false }); recovery = await fresh(true);
          }
          if (!/当前位置.*新学员报名/.test(recovery)) {
            const enrollment = recovery.split('\n').find(line => /\d+ button 新学员报名(?:,.*)?$/.test(line));
            if (!enrollment) throw Error('Observed new enrollment preparation missing');
            await app.click(Number(enrollment.trim().match(/^\d+/)[0]));
          }
          let after = await fresh(true);
          for (let i = 0; i < 30 && !/当前位置.*新学员报名/.test(after); i++) {
            await app.getScreenshot({ emit: false }); after = await fresh(true);
          }
          after = await fresh();
          let recoveryPrevious = null;
          for (let i = 0; i < 15; i++) {
            const value = JSON.stringify(captions(after));
            if (after.includes('请选择要收费的课程或物品') && value === recoveryPrevious) break;
            recoveryPrevious = value; after = await fresh();
          }
          await save(after, item.id + '-dismissed');
          rows.push({ id: item.id, baseline: facts(before), result, afterDismiss: facts(after) });
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
