// The same readonly period actions on both sides; returns facts, no expectations.
export async function captureHomePeriods(app, fs, { side, out }) {
  if (!['reference', 'candidate'].includes(side)) throw new Error('Unknown side');
  async function fresh() {
    const ax = await app.getAXState({ emit: false, disableDiffing: true });
    const window = ax.split('\n').find(line => /standard window/.test(line)) || '';
    const target = side === 'candidate' ? /URL: (?:127\.0\.0\.1|localhost):5183\// : /URL: tms03\.xiaogj\.com\//;
    if (!target.test(window)) throw new Error('Wrong homepage period side');
    return ax;
  }
  await fs.mkdir(out, { recursive: true });
  const captures = [];
  const scenarios = JSON.parse(await fs.readFile(new URL('../home-periods-scenarios.json', import.meta.url), 'utf8'));
  for (const { id: name, section, label, end } of scenarios.cases) {
    const lines = (await fresh()).split('\n');
    const start = lines.findIndex(line => new RegExp('\\d+ text ' + section + '$').test(line));
    const stop = lines.findIndex((line, i) => i > start && new RegExp('\\d+ text ' + end + '$').test(line));
    if (start < 0 || stop < 0) throw new Error('Homepage section absent: ' + section);
    const control = lines.slice(start, stop).find(line => new RegExp('\\d+ (?:toggle button|button) ' + label + '(?:, Value: [01])?$').test(line));
    if (!control) throw new Error('Period control absent: ' + label);
    await app.click(Number(control.trim().match(/^\d+/)[0]));
    const ax = await fresh();
    await fs.writeFile(out + '/' + name + '.ax.txt', ax);
    captures.push({ name, section, action: 'click', label });
  }
  await fs.writeFile(out + '/actions.json', JSON.stringify({ side, captures }, null, 2) + '\n');
  return captures;
}
