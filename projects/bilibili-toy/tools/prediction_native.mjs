// Shared Safari/native prediction actions. The comparator owns assertions.
export function predictionFacts(ax) {
  const lines = ax.split('\n');
  const start = lines.findIndex(s => /heading 我来预测, Value: 1/.test(s));
  const end = lines.findIndex((s, i) => i > start && /button 展开 AI 模拟速报/.test(s));
  if (start < 0 || end < 0) throw Error('Prediction content scope unavailable');
  const accessible_text = [], elements = {}, occurrences = {};
  for (const line of lines.slice(start, end)) {
    const text = line.match(/^\s*\d+ (?:heading|text|button(?: \(disabled\))?|toggle button) (.*?)(?:, Value:|, Help:|, Secondary Actions:|$)/);
    if (text) accessible_text.push(text[1].trim());
    const toggle = line.match(/toggle button (.*?), Value: (on|off|1|0)$/);
    if (toggle) {
      const count = occurrences[toggle[1]] = (occurrences[toggle[1]] || 0) + 1;
      elements[toggle[1] + ' [' + count + ']'] = {role: 'button', checked: /^(on|1)$/.test(toggle[2])};
    }
    const round = line.match(/button (\(disabled\) )?([1-7] .*)$/);
    if (round) elements[round[2]] = {role: 'button', enabled: !round[1]};
  }
  return {accessible_text, elements};
}

export function installPredictionE2E(app, fs, bridge) {
  const tree = () => app.getAXState({emit: false, disableDiffing: true});
  function guard(ax, req) {
    const address = ax.split('\n').find(s => /smart search field|Address and search bar/.test(s)) || '';
    if (!address.includes(req.guard)) throw Error('Requested prediction endpoint is no longer selected');
  }
  return async function servicePrediction() {
    for (const name of (await fs.readdir(bridge)).filter(n => n.endsWith('.request.json')).sort()) {
      const req = JSON.parse(await fs.readFile(bridge + '/' + name, 'utf8'));
      if (req.suite !== 'prediction') continue;
      const reply = bridge + '/' + req.id + '.reply.json';
      try { await fs.access(reply); continue; } catch {}
      const states = {}, actions = [];
      try {
        await app.pressKey('super+l'); await app.paste(req.url + '?p=pickem'); await app.pressKey('Return');
        let ax;
        for (let i = 0; i < 10; i++) {
          ax = await tree();
          if (ax.includes('heading 我来预测, Value: 1')) break;
        }
        guard(ax, req);
        if (!/button 揭晓对阵/.test(ax)) throw Error('Empty prediction prestate required; existing drafts are not reset by the driver');
        for (const item of req.cases) for (const step of item.steps) {
          ax = await tree(); guard(ax, req);
          if (step.action === 'click') {
            const line = ax.split('\n').find(s => new RegExp(step.match).test(s));
            if (!line) throw Error('Prediction control absent: ' + step.match);
            await app.click(Number(line.trim().match(/^\d+/)[0]));
          } else if (step.action === 'reload') await app.pressKey('super+r');
          else if (step.action !== 'capture') throw Error('Unknown prediction action');
          ax = await tree(); guard(ax, req);
          if (step.action === 'reload') {
            for (let i = 0; i < 10 && !ax.includes('heading 我来预测, Value: 1'); i++) ax = await tree();
            guard(ax, req);
          }
          actions.push({case: item.id, ...step, attempted: true});
          if (step.capture) {
            const state = predictionFacts(ax);
            const bytes = await app.getScreenshot({emit: false});
            const extension = bytes[0] === 255 && bytes[1] === 216 ? 'jpg' : 'png';
            const image = req.workspace + '/' + step.capture + '.' + extension;
            const axPath = req.workspace + '/' + step.capture + '.ax.txt';
            await fs.writeFile(image, bytes); await fs.writeFile(axPath, ax);
            const after = await tree(); guard(after, req);
            states[step.capture] = {...state, image, ax: axPath,
              state_consistent: JSON.stringify(state) === JSON.stringify(predictionFacts(after))};
          }
        }
        await fs.writeFile(reply, JSON.stringify({states, actions, preparation: 'Empty draft required; official PI draw; same clicks and reload on both endpoints. Random Swiss draws excluded from this deterministic slice.'}));
        return {endpoint: req.endpoint, states: Object.keys(states)};
      } catch (error) {
        await fs.writeFile(reply, JSON.stringify({states, actions, error: String(error)}));
        throw error;
      }
    }
    return {pending: false};
  };
}
