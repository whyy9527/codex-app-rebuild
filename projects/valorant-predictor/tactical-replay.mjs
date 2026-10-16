// Hand-authored demonstration only. No model forecast is interpreted as telemetry.
export const DURATION = 30;
export const MAPS = {
  ascent: {
    name: '亚海悬城', english: 'ASCENT', image: 'assets/tactical/ascent.png',
    sites: [['A', 310, 155], ['B', 285, 800]],
    zones: [['中路', 520, 530], ['进攻方向 ←', 800, 740]],
    attack: [
      [[480,195],[480,230],[480,255],[480,280]],
      [[610,265],[565,265],[525,265],[490,265],[480,245]],
      [[560,500],[520,500],[455,500],[455,450],[455,405],[455,370]],
      [[410,715],[400,715],[400,740],[385,740]],
      [[670,655],[620,655],[570,655],[540,655],[540,675]],
    ],
    defend: [
      [[305,135],[325,135],[325,170]],
      [[400,295],[400,325],[410,345]],
      [[280,795],[300,795],[310,765]],
      [[300,495],[340,495],[375,495]],
      [[300,295],[300,280],[325,280]],
    ],
  },
  haven: {
    name: '隐世修所', english: 'HAVEN', image: 'assets/tactical/haven.png',
    sites: [['A', 385, 150], ['B', 390, 490], ['C', 370, 835]],
    zones: [['中路', 575, 560], ['进攻方向 ←', 835, 715]],
    attack: [
      [[570,180],[580,200],[590,220],[600,240],[610,260]],
      [[630,390],[620,370],[620,340],[610,310],[600,290],[600,260]],
      [[600,520],[560,520],[530,520],[500,520]],
      [[650,855],[600,855],[550,855],[505,855],[465,855]],
      [[505,635],[475,635],[445,635],[430,615]],
    ],
    defend: [
      [[395,130],[420,130],[435,150]],
      [[395,490],[420,490],[435,520]],
      [[360,840],[350,810],[375,800]],
      [[285,320],[315,320],[350,320]],
      [[285,660],[285,700],[310,735]],
    ],
  },
};
export const LINEUPS = {
  attack: [
    ['wushu', '捷风', '决斗'], ['hunter', '猎枭', '先锋'],
    ['wraith', '幽影', '控场'], ['killjoy', '奇乐', '哨卫'], ['grenadier', 'K/O', '先锋'],
  ],
  defend: [
    ['clay', '雷兹', '决斗'], ['breach', '铁臂', '先锋'],
    ['gumshoe', '零', '哨卫'], ['pandemic', '蝰蛇', '控场'], ['guide', '斯凯', '先锋'],
  ],
};
export function pointAt(points, progress) {
  const p = Math.max(0, Math.min(1, progress));
  const lengths = points.slice(1).map((point, i) => Math.hypot(point[0] - points[i][0], point[1] - points[i][1]));
  let remaining = lengths.reduce((a, b) => a + b, 0) * p;
  for (let i = 0; i < lengths.length; i++) {
    if (remaining <= lengths[i]) {
      const f = lengths[i] ? remaining / lengths[i] : 0;
      return [points[i][0] + (points[i + 1][0] - points[i][0]) * f, points[i][1] + (points[i + 1][1] - points[i][1]) * f];
    }
    remaining -= lengths[i];
  }
  return points.at(-1);
}
export function phaseAt(time) {
  return time < 8 ? 0 : time < 20 ? 1 : time < DURATION ? 2 : 3;
}
const phases = [
  ['初始站位', '两侧分线落位，先看双方的特工配置。'],
  ['多线推进', '红方沿入口移动，蓝方在包点与中路调整站位。'],
  ['控图收束', '观察两翼与中路的距离；此演示不计算交火或胜负。'],
  ['演示结束', '可以拖动时间轴回看，或换一张地图重新播放。'],
];
const state = { map: 'ascent', time: 0, playing: false, speed: 1, routes: true, selected: 'attack-0' };
let frameId, activeRoot, teardown;
const clock = time => `00:${String(Math.floor(time)).padStart(2, '0')}`;
export function tacticalMarkup() {
  return `<section id="tactical-replay" class="tactical" aria-label="战术沙盘演示"><header class="tactical-heading"><div><p class="tactical-eyebrow">TACTICAL SANDBOX · 5 VS 5</p><h2>战术沙盘 · 阵容与走位</h2></div><span class="tactical-demo">演示回放 · 非模型预测</span></header><p class="tactical-disclosure">当前模型未输出特工选用与逐秒坐标。以下阵容与路线为各频道共用的手工示例，不代表真实赛况。</p><div class="tactical-toolbar"><div class="tactical-maps" role="group" aria-label="选择演示地图">${Object.entries(MAPS).map(([id, m]) => `<button data-tactical-map="${id}" aria-pressed="${state.map === id}">${m.name}<small>${m.english}</small></button>`).join('')}</div><div class="tactical-toolbar-end"><label><input type="checkbox" id="tactical-routes" ${state.routes ? 'checked' : ''}>显示路线</label><button id="tactical-focus" aria-pressed="false">专注地图</button></div></div><div id="tactical-arena"></div><div class="tactical-transport"><button id="tactical-play" class="tactical-play">▶ 播放演示</button><button id="tactical-reset" aria-label="回到初始站位">↺ 重置</button><label class="tactical-scrub"><span class="sr-only">演示进度</span><input id="tactical-progress" type="range" min="0" max="30" step="0.1" value="${state.time}" aria-label="演示进度"><span class="tactical-time"><output id="tactical-time">${clock(state.time)}</output> / 00:30</span></label><label class="tactical-speed">速度<select id="tactical-speed" aria-label="演示速度"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></label></div><div class="tactical-phase"><b id="tactical-phase-title"></b><span id="tactical-phase-copy"></span></div><details class="tactical-sources"><summary>演示边界与素材来源</summary><p>底图与特工图标为 Riot 游戏素材，经 <a href="https://valorant-api.com/" target="_blank" rel="noreferrer">Valorant-API</a> 公开目录取得。路线是用于讲解的手工折线，未接入碰撞、技能、枪械、经济与逐回合胜负；地图选择不代表本届官方地图池。</p><p>本非官方社区展示使用 Riot Games 素材，依据其 <a href="https://www.riotgames.com/en/legal" target="_blank" rel="noreferrer">Legal Jibber Jabber</a> 政策创作；Riot Games 未认可或赞助本项目。<a href="data/tactical-assets.json" target="_blank">素材来源与摘要 ↗</a></p></details></section>`;
}
export function stopTactical() {
  cancelAnimationFrame(frameId);
  state.playing = false;
  teardown?.();
  teardown = null;
  activeRoot = null;
}
export function mountTactical() {
  const root = document.querySelector('#tactical-replay');
  if (!root) return;
  activeRoot = root;
  const find = selector => root.querySelector(selector);
  const stop = () => { state.playing = false; cancelAnimationFrame(frameId); update(); };
  const actors = () => Object.entries(LINEUPS).flatMap(([side, lineup]) => lineup.map(([id, name, role], index) => ({ id: `${side}-${index}`, icon: id, name, role, side, index, path: MAPS[state.map][side][index] })));
  function roster(side) {
    return `<aside class="tactical-roster ${side}"><div class="tactical-team"><span>${side === 'attack' ? 'ATK' : 'DEF'}</span><h3>${side === 'attack' ? '红方 · 进攻' : '蓝方 · 防守'}</h3><small>示例阵容 / 5 人</small></div>${actors().filter(a => a.side === side).map(a => `<button class="tactical-agent" data-tactical-agent="${a.id}" aria-pressed="${state.selected === a.id}"><span class="tactical-agent-number">${a.index + 1}</span><img src="assets/tactical/${a.icon}.png" alt=""><span><b>${a.name}</b><small>${a.role}</small></span><span class="tactical-agent-arrow" aria-hidden="true">↗</span></button>`).join('')}</aside>`;
  }
  function draw() {
    const map = MAPS[state.map];
    find('#tactical-arena').innerHTML = `<div class="tactical-layout">${roster('attack')}<div class="tactical-map"><div class="tactical-map-caption"><b>${map.english}</b><span>全图视角 · 示例</span></div><div class="tactical-map-canvas"><img class="tactical-map-image" src="${map.image}" alt="${map.name}真实游戏小地图"><svg class="tactical-overlay" viewBox="0 0 1000 1000" aria-hidden="true"><g class="tactical-site-labels">${map.sites.map(([name,x,y]) => `<g transform="translate(${x} ${y})"><circle r="34"/><text y="10">${name}</text></g>`).join('')}${map.zones.map(([name,x,y]) => `<text class="tactical-zone" x="${x}" y="${y}">${name}</text>`).join('')}</g><g class="tactical-paths">${actors().map(a => `<polyline class="tactical-path ${a.side}" data-path="${a.id}" points="${a.path.map(p => p.join(',')).join(' ')}"/>`).join('')}</g></svg>${actors().map(a => `<button class="tactical-marker ${a.side}" data-marker="${a.id}" aria-label="${a.side === 'attack' ? '进攻' : '防守'}方 ${a.index + 1}号 ${a.name}" title="${a.name} · ${a.role}"><img src="assets/tactical/${a.icon}.png" alt=""><span>${a.index + 1}</span></button>`).join('')}<div class="tactical-map-error" hidden>地图素材加载失败，请刷新重试。</div></div><div class="tactical-map-legend"><span class="attack">▲ 进攻方</span><span class="defend">◆ 防守方</span><span>折线为演示移动路线</span></div></div>${roster('defend')}</div>`;
    find('.tactical-map-image').onerror = () => { stop(); find('.tactical-map-error').hidden = false; find('#tactical-play').disabled = true; };
    root.querySelectorAll('[data-tactical-agent], [data-marker]').forEach(button => button.onclick = () => {state.selected = button.dataset.tacticalAgent || button.dataset.marker;update();});
    update();
  }
  function update() {
    if (activeRoot !== root || !root.isConnected) return;
    root.dataset.time = state.time.toFixed(2);
    root.dataset.playing = String(state.playing);
    root.dataset.map = state.map;
    find('#tactical-play').textContent = state.playing ? 'Ⅱ 暂停演示' : state.time >= DURATION ? '↺ 重播演示' : '▶ 播放演示';
    find('#tactical-play').setAttribute('aria-pressed', String(state.playing));
    find('#tactical-progress').value = state.time;
    find('#tactical-progress').setAttribute('aria-valuetext', `${clock(state.time)}，${phases[phaseAt(state.time)][0]}`);
    find('#tactical-time').textContent = clock(state.time);
    const phase = phases[phaseAt(state.time)];
    find('#tactical-phase-title').textContent = phase[0];
    find('#tactical-phase-copy').textContent = phase[1];
    actors().forEach(a => {
      // First 3 seconds expose initial positions; end at 25s and hold for narration.
      const [x,y] = pointAt(a.path, (state.time - 3) / 22);
      const marker = find(`[data-marker="${a.id}"]`);
      marker.style.left = `${x / 10}%`; marker.style.top = `${y / 10}%`;
      marker.classList.toggle('selected', state.selected === a.id);
      marker.setAttribute('aria-pressed', String(state.selected === a.id));
      const row = find(`[data-tactical-agent="${a.id}"]`);
      row.setAttribute('aria-pressed', String(state.selected === a.id));
      const path = find(`[data-path="${a.id}"]`);
      path.style.display = state.routes ? '' : 'none';
      path.classList.toggle('selected', state.selected === a.id);
    });
  }
  function start() {
    if (state.time >= DURATION) state.time = 0;
    state.playing = true;
    let previous;
    function tick(now) {
      if (!state.playing || activeRoot !== root || !root.isConnected) return;
      if (previous !== undefined) state.time = Math.min(DURATION, state.time + Math.min((now - previous) / 1000, 0.1) * state.speed);
      previous = now;
      if (state.time >= DURATION) state.playing = false;
      update();
      if (state.playing) frameId = requestAnimationFrame(tick);
    }
    frameId = requestAnimationFrame(tick);
    update();
  }
  root.querySelectorAll('[data-tactical-map]').forEach(button => button.onclick = () => {
    stop(); state.map = button.dataset.tacticalMap; state.time = 0;
    root.querySelectorAll('[data-tactical-map]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    draw(); find('#tactical-play').disabled = false;
  });
  find('#tactical-play').onclick = () => state.playing ? stop() : start();
  find('#tactical-reset').onclick = () => { stop(); state.time = 0; update(); };
  find('#tactical-progress').oninput = event => { const time = Number(event.target.value); stop(); state.time = time; update(); };
  find('#tactical-speed').value = state.speed;
  find('#tactical-speed').onchange = event => { state.speed = Number(event.target.value); };
  find('#tactical-routes').onchange = event => { state.routes = event.target.checked; update(); };
  find('#tactical-focus').onclick = event => {
    const focused = root.classList.toggle('tactical-focused');
    event.target.setAttribute('aria-pressed', String(focused));
    event.target.textContent = focused ? '退出专注' : '专注地图';
    if (focused) root.scrollIntoView({block: 'start'});
  };
  const onKey = event => { if (event.key === 'Escape' && root.classList.contains('tactical-focused')) find('#tactical-focus').click(); };
  document.addEventListener('keydown', onKey);
  const onVisibility = () => { if (document.hidden) stop(); };
  document.addEventListener('visibilitychange', onVisibility);
  teardown = () => { document.removeEventListener('visibilitychange', onVisibility); document.removeEventListener('keydown', onKey); };
  draw();
}
