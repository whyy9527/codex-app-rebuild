// Shared actual Safari UI preparation and timed playback, used only through CUA.
export function installAudioUI(app, fs) {
  const tree = () => app.getAXState({emit: false, disableDiffing: true});
  function guard(ax, url) {
    const field = ax.split('\n').find(s => /smart search field|Address and search bar/.test(s)) || '';
    const value = field.match(/Value: ([^,\n]*)/)?.[1] || '';
    const expected = new URL(url);
    const actual = new URL(value.includes('://') ? value : expected.protocol + '//' + value);
    if (actual.origin !== expected.origin || actual.pathname !== expected.pathname) throw Error('Audio endpoint changed');
  }
  async function click(pattern, url, optional = false) {
    let ax = await tree(); guard(ax, url);
    const line = ax.split('\n').find(s => pattern.test(s));
    if (!line) { if (optional) return ax; throw Error('Audio UI control absent: ' + pattern); }
    await app.click(Number(line.trim().match(/^\d+/)[0]));
    ax = await tree(); guard(ax, url); return ax;
  }
  async function prepare({url, dir, enabled, expectedBefore}) {
    await fs.mkdir(dir, {recursive: true});
    const recorded = await fs.access(dir + '/capture-request.json').then(() => true, e => {
      if (e.code === 'ENOENT') return false; throw e;
    });
    if (recorded) throw Error('Recorded evidence is immutable; choose a new directory');
    await app.pressKey('super+l'); await app.paste(url); await app.pressKey('Return');
    let ax;
    for (let i = 0; i < 12; i++) { ax = await tree(); if (ax.includes('heading S16 AI 大模型预测大赛, Value: 1')) break; }
    guard(ax, url);
    await click(/\d+ link Claude Opus 5\.5, Value:/, url);
    await click(/button\s+暂停, Help:/, url, true);
    await click(/checkbox 闲置 60 秒后自动换台, Value: (?:on|1)/, url, true);
    await click(/button 赛前$/, url);
    await click(/button 1x$/, url);
    // Paused skips one whole event: intro, then completed first game data.
    await click(/button 下一步, Help:/, url);
    await click(/button 下一步, Help:/, url);
    ax = await click(/toggle button BP, Value:/, url);
    const beforeEnabled = ax.includes('button 静音, Help:');
    if (typeof expectedBefore === 'boolean' && beforeEnabled !== expectedBefore) throw Error('Reload did not retain the observed prior sound setting');
    await fs.writeFile(dir + '/sound-before-toggle.ax.txt', ax);
    const change = enabled ? /button 开启音效, Help:/ : /button 静音, Help:/;
    ax = await click(change, url, true);
    if (!ax.includes(enabled ? 'button 静音, Help:' : 'button 开启音效, Help:')) throw Error('Requested sound state not observed');
    if (!/button\s+播放, Help:/.test(ax)) throw Error('Paused BP preparation unavailable');
    if (!/text AI 模拟 Claude Opus 5\.5\s+的世界/.test(ax)) throw Error('Requested model channel not observed');
    await fs.writeFile(dir + '/prepared.ax.txt', ax);
    const bytes = await app.getScreenshot({emit: false});
    await fs.writeFile(dir + (bytes[0] === 255 ? '/prepared.jpg' : '/prepared.png'), bytes);
    await fs.writeFile(dir + '/preparation.json', JSON.stringify({url, enabled,
      observed_sound_before_toggle: beforeEnabled, changed_sound_setting: beforeEnabled !== enabled,
      method: 'Pause, idle off, preseason, 1x, two event advances, BP; real sound button state',
      observed_at_unix_ms: Date.now()}));
    return {prepared: true, enabled};
  }
  async function play({url, dir}) {
    const ready = JSON.parse(await fs.readFile(dir + '/ready.json', 'utf8'));
    const before = Date.now();
    if (before <= ready.ready_unix_ms || before >= ready.ready_unix_ms + (ready.duration_seconds - 2) * 1000) throw Error('Capture is not in its trigger interval');
    const ax = await click(/button\s+播放, Help:/, url);
    if (!/button\s+暂停, Help:/.test(ax)) throw Error('Actual player did not start');
    await fs.writeFile(dir + '/playing.ax.txt', ax);
    await fs.writeFile(dir + '/actions.json', JSON.stringify([{action: 'play', before_unix_ms: before, after_unix_ms: Date.now()}]));
    return {playing: true, elapsed_after_ready_ms: Date.now() - ready.ready_unix_ms};
  }
  async function pause({url, dir}) {
    const before = Date.now();
    const ready = JSON.parse(await fs.readFile(dir + '/ready.json', 'utf8'));
    if (before >= ready.ready_unix_ms + ready.duration_seconds * 1000) throw Error('Pause is outside the capture interval');
    const ax = await click(/button\s+暂停, Help:/, url);
    if (!/button\s+播放, Help:/.test(ax)) throw Error('Actual player did not pause');
    const actions = JSON.parse(await fs.readFile(dir + '/actions.json', 'utf8'));
    actions.push({action: 'pause', before_unix_ms: before, after_unix_ms: Date.now()});
    await fs.writeFile(dir + '/actions.json', JSON.stringify(actions));
    await fs.writeFile(dir + '/paused.ax.txt', ax);
    return {paused: true, playback_ms: before - actions[0].after_unix_ms};
  }
  async function run({url, dir, seconds = 3}) {
    if (!(seconds >= 1 && seconds <= 5)) throw Error('Bounded playback sampling required');
    await play({url, dir});
    const actions = JSON.parse(await fs.readFile(dir + '/actions.json', 'utf8'));
    const deadline = actions[0].before_unix_ms + seconds * 1000;
    const samples = [];
    while (Date.now() < deadline) {
      const ax = await tree(); guard(ax, url);
      const bytes = await app.getScreenshot({emit: false});
      const stem = dir + '/playing-' + samples.length;
      await fs.writeFile(stem + '.ax.txt', ax);
      await fs.writeFile(stem + (bytes[0] === 255 ? '.jpg' : '.png'), bytes);
      samples.push({unix_ms: Date.now(), ax: stem + '.ax.txt'});
    }
    await fs.writeFile(dir + '/playback-samples.json', JSON.stringify(samples));
    return {...await pause({url, dir}), sampled_frames: samples.length};
  }
  return {prepare, play, pause, run};
}
