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

export function sharedPredictionFacts(ax) {
  const lines = ax.split('\n');
  const start = lines.findIndex(s => /container 好友预测战帖$/.test(s));
  const accessible_text = [];
  if (start >= 0) {
    const indent = lines[start].match(/^\s*/)[0].length;
    for (const line of lines.slice(start + 1)) {
      if (line.match(/^\s*/)[0].length <= indent) break;
      const text = line.match(/^\s*\d+ (?:text|button) (.*?)(?:, Value:|, Help:|$)/);
      if (text) accessible_text.push(text[1].trim());
    }
  }
  // Inline SVG loading can split one sentence into several AX text nodes.
  // Preserve every word in order while comparing the whole observed section.
  return {accessible_text: accessible_text.length ? [accessible_text.join(' ').replace(/\s+/g, ' ')] : [],
    elements: {}, interactions: {shared_prediction_visible: start >= 0}};
}

export function finalPredictionFacts(ax) {
  const lines = ax.split('\n');
  const championAt = lines.findIndex(s => /text 我的冠军$/.test(s));
  const champion = championAt < 0 ? null : lines.slice(championAt + 1, championAt + 6)
    .map(s => s.match(/text ([A-Z0-9]+)$/)?.[1]).find(Boolean);
  const lockedAt = lines.findIndex(s => /text 已锁定 ·/.test(s));
  const timestamp = lockedAt < 0 ? null : lines.slice(lockedAt + 1, lockedAt + 4)
    .map(s => s.match(/text (\d{4}\/\d+\/\d+ .*?)$/)?.[1]).find(Boolean);
  const choices = lines.flatMap(s => {
    const match = s.match(/toggle button (.*?), Value: (on|off|1|0)$/);
    return match ? [{label: match[1], checked: /^(on|1)$/.test(match[2])}] : [];
  });
  return {accessible_text: champion ? ['我的冠军 ' + champion] : [],
    elements: {champion: {role: 'text', value: champion || ''},
      selected_matches: {value: String(choices.filter(e => e.checked).length)},
      match_choices: {value: String(choices.length)}},
    interactions: {final_result_visible: !!champion, prediction_locked: lockedAt >= 0,
      copy_succeeded: ax.includes('text 已复制预测战报口令')},
    lock_signature: JSON.stringify({champion, timestamp, choices}), lock_timestamp: timestamp};
}

export function installPredictionE2E(app, fs, bridge) {
  const tree = () => app.getAXState({emit: false, disableDiffing: true});
  function guard(ax, req) {
    const address = ax.split('\n').find(s => /smart search field|Address and search bar/.test(s)) || '';
    const value = address.match(/Value: ([^,\n]*)/)?.[1];
    const expected = new URL(req.url);
    let actual;
    try { actual = new URL(value.includes('://') ? value : expected.protocol + '//' + value); } catch {}
    if (actual?.origin !== expected.origin || actual?.pathname !== expected.pathname) {
      throw Error('Requested prediction endpoint is no longer selected');
    }
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
        if (req.cases.some(item => item.id === 'playin') && !/button 揭晓对阵/.test(ax)) {
          throw Error('Empty prediction prestate required; existing drafts are not reset by the driver');
        }
        for (const item of req.cases) {
          const collect = item.id === 'share' ? sharedPredictionFacts : item.id === 'locked' ? finalPredictionFacts : predictionFacts;
          if (item.query) {
            await app.pressKey('super+l'); await app.paste(req.url + item.query); await app.pressKey('Return');
            for (let i = 0; i < 10; i++) { ax = await tree(); if (ax.includes('heading 我来预测, Value: 1')) break; }
            guard(ax, req);
          }
          if (item.id === 'share') {
            const reveal = ax.split('\n').find(s => /button 揭晓对阵$/.test(s));
            if (reveal) { await app.click(Number(reveal.trim().match(/^\d+/)[0])); ax = await tree(); guard(ax, req); }
            const draft = predictionFacts(ax);
            if (Object.values(draft.elements).some(e => e.checked) || ax.includes('text 已锁定')) {
              throw Error('Shared-link comparison requires unselected PI draft; existing predictions are preserved');
            }
          }
          const lockedBaseline = item.id === 'locked' ? finalPredictionFacts(ax) : null;
          if (lockedBaseline && (!lockedBaseline.interactions.prediction_locked || !lockedBaseline.lock_timestamp)) {
            throw Error('Final lock verification requires an already locked test prediction');
          }
          for (const step of item.steps) {
            ax = await tree(); guard(ax, req);
            if (step.action === 'click') {
              const line = ax.split('\n').find(s => new RegExp(step.match).test(s));
              if (!line) throw Error('Prediction control absent: ' + step.match);
              await app.click(Number(line.trim().match(/^\d+/)[0]));
            } else if (step.action === 'reload') await app.pressKey('super+r');
            else if (step.action === 'scroll_top') {
              const frame = ax.split('\n').find(s => /HTML content .*#\/pickem(?:$|\?)/.test(s));
              if (!frame) throw Error('Prediction frame scroll target unavailable');
              await app.scroll(Number(frame.trim().match(/^\d+/)[0]), 'up', 20);
            } else if (step.action !== 'capture') throw Error('Unknown prediction action');
            ax = await tree(); guard(ax, req);
            if (step.action === 'reload') {
              for (let i = 0; i < 10 && !ax.includes('heading 我来预测, Value: 1'); i++) ax = await tree();
              guard(ax, req);
            }
            actions.push({case: item.id, ...step, attempted: true});
            if (step.capture) {
              const state = collect(ax);
              if (lockedBaseline) state.interactions.locked_prediction_retained = state.lock_signature === lockedBaseline.lock_signature;
              const bytes = await app.getScreenshot({emit: false});
              const extension = bytes[0] === 255 && bytes[1] === 216 ? 'jpg' : 'png';
              const image = req.workspace + '/' + step.capture + '.' + extension;
              const axPath = req.workspace + '/' + step.capture + '.ax.txt';
              await fs.writeFile(image, bytes); await fs.writeFile(axPath, ax);
              const after = await tree(); guard(after, req);
              const afterState = collect(after);
              if (lockedBaseline) afterState.interactions.locked_prediction_retained = afterState.lock_signature === lockedBaseline.lock_signature;
              states[step.capture] = {...state, image, ax: axPath,
                state_consistent: JSON.stringify(state) === JSON.stringify(afterState)};
            }
          }
        }
        await fs.writeFile(reply, JSON.stringify({states, actions, preparation: 'Play-in requires empty draft; shared link requires unselected official PI draw. Same clicks and reload on both endpoints. Existing drafts are never cleared.'}));
        return {endpoint: req.endpoint, states: Object.keys(states)};
      } catch (error) {
        await fs.writeFile(reply, JSON.stringify({states, actions, error: String(error)}));
        throw error;
      }
    }
    return {pending: false};
  };
}
