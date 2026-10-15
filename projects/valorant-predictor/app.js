import {
  mapProbability,
  seriesDistribution,
  seriesProbability,
  teamStats,
  baselineProbability,
  validScore,
  validatePick,
  simulateSeries,
} from "./engine.mjs";
const $ = (s) => document.querySelector(s),
  main = $("#main-content");
const escape = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const pct = (p) => (p == null ? "待预测" : `${(p * 100).toFixed(1)}%`);
const store = {
  get(k, fallback) {
    try {
      return JSON.parse(localStorage.getItem("vct-finals-" + k)) ?? fallback;
    } catch {
      return fallback;
    }
  },
  set(k, v) {
    try {
      localStorage.setItem("vct-finals-" + k, JSON.stringify(v));
      return true;
    } catch {
      return false;
    }
  },
};
const channels = [
  ["opus", "Claude Opus 5.5", "✳", "#c2826a"],
  ["codex", "GPT-6.1 sol", "◎", "#d17d4d"],
  ["gemini", "Gemini 3.8", "✦", "#49bfb4"],
  ["deepseek", "DeepSeek V4.1 Flash", "≈", "#be9b48"],
  ["qwen", "Qwen3.8 Max", "✧", "#cc62a4"],
  ["glm", "GLM-5.3", "❋", "#75ad64"],
  ["doubao", "豆包", "●", "#9c7be8"],
  ["mimo", "MiMo V2.6 Pro", "M", "#eb6577"],
].map(([id, name, icon, color]) => ({ id, name, icon, color }));
let event,
  assets,
  forecast,
  forecasts = {},
  selected = store.get("channel", "codex"),
  tab = "live",
  current = 0,
  playing = false,
  speed = 1,
  muted = store.get("muted", true),
  scenario,
  simFrames = [],
  simSeed = 20261017,
  playerTimer,
  toastTimer,
  audio;
let pick = store.get("pick", null),
  draft = { lfWinner: null, lfScore: null, champion: null, gfScore: null },
  pageRoute = "/";
function notify(text) {
  $("#toast").textContent = text;
  $("#toast").classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $("#toast").classList.remove("show"), 3000);
}
function sound() {
  if (muted) return;
  try {
    audio ??= new AudioContext();
    audio.resume();
    const oscillator = audio.createOscillator(),
      gain = audio.createGain();
    oscillator.connect(gain);
    gain.connect(audio.destination);
    oscillator.frequency.value = 660;
    gain.gain.setValueAtTime(0.05, audio.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audio.currentTime + 0.12);
    oscillator.start();
    oscillator.stop(audio.currentTime + 0.13);
  } catch {}
}
function logo(code, size = "") {
  return event.teams[code]
    ? `<img class="logo ${size}" src="${escape(event.teams[code].logo)}" alt="${escape(event.teams[code].name)}" loading="lazy">`
    : '<span class="logo" aria-hidden="true">?</span>';
}
function channel() {
  return channels.find((c) => c.id === selected) || channels[1];
}
function avatar(c) {
  return `<span class="avatar" aria-hidden="true" style="--accent:${c.color}">${c.icon}</span>`;
}
function available(id) {
  return Boolean(forecasts[id]);
}
function opponentPairs() {
  const u = event.predecessors[0].teams;
  const upperWinner = event.predecessors[0].winner || scenario.upperWinner,
    lowerWinner = event.predecessors[1].winner || scenario.lowerWinner;
  return {
    upperWinner,
    upperLoser: u.find((c) => c !== upperWinner),
    lowerWinner,
  };
}
function pmap(a, b, id = selected) {
  return id === "baseline"
    ? baselineProbability(event, a, b)
    : forecasts[id]
      ? mapProbability(forecasts[id], a, b)
      : null;
}
function matchup(id = selected) {
  const { upperWinner, upperLoser, lowerWinner } = opponentPairs();
  const lp = pmap(upperLoser, lowerWinner, id);
  const lfWinner = lp == null ? null : lp >= 0.5 ? upperLoser : lowerWinner;
  return {
    lf: [upperLoser, lowerWinner],
    gf: [upperWinner, lfWinner],
    lp,
    gp: lfWinner ? pmap(upperWinner, lfWinner, id) : null,
  };
}
function pageHead(title, description) {
  return `<div class="wrap page-head"><div><h1>${title}</h1><p>${description}</p></div><div class="kicker">CHAMPIONS SHANGHAI · FINALS</div></div>`;
}
function note() {
  return `<div class="notice">官方对阵${event.matches.every((m) => m.teams.includes("TBD")) ? "尚未确定" : "已更新"}。下方晋级情景用于分析 17、18 日的两场比赛；情景选择不是官方赛果。</div>`;
}
function scenarioForm() {
  const upper = event.predecessors[0],
    lower = event.predecessors[1];
  return `<section class="card" aria-label="晋级情景"><h3>先选定决赛周末的晋级情景</h3><p class="muted">17 日：胜者组决赛败者 vs 败者组半决赛胜者。18 日：胜者组决赛胜者 vs 17 日胜者。</p><div class="form-row"><label>胜者组决赛胜者（16 日，不在预测范围）<select id="upper-winner" ${upper.winner ? "disabled" : ""}>${upper.teams.map((c) => `<option ${c === (upper.winner || scenario.upperWinner) ? "selected" : ""}>${c}</option>`).join("")}</select></label><label>败者组半决赛胜者（16 日，不在预测范围）<select id="lower-winner" ${lower.winner ? "disabled" : ""}>${lower.teams.map((c) => `<option ${c === (lower.winner || scenario.lowerWinner) ? "selected" : ""}>${c}</option>`).join("")}</select></label></div><small class="muted">已确定的官方晋级结果会自动接入。官方最新状态见 <a class="source-link" href="https://valorantesports.com/en-US/" target="_blank" rel="noreferrer">赛事官网 ↗</a></small></section>`;
}
function bindScenario() {
  for (const [id, key] of [
    ["upper-winner", "upperWinner"],
    ["lower-winner", "lowerWinner"],
  ]) {
    const element = $("#" + id);
    if (element)
      element.onchange = () => {
        scenario[key] = element.value;
        store.set("scenario", scenario);
        draft = {
          lfWinner: null,
          lfScore: null,
          champion: null,
          gfScore: null,
        };
        current = 0;
        buildSimulation();
        render();
        notify("晋级情景已更新，后续预测已重新计算");
      };
  }
}
function modelGrid() {
  return `<div class="channels">${channels.map((c) => `<button class="channel ${selected === c.id ? "on" : ""}" data-channel="${c.id}" aria-pressed="${selected === c.id}" style="--accent:${c.color}">${avatar(c)}<span>${c.name}</span><small>${available(c.id) ? "已预测" : "待预测"}</small></button>`).join("")}</div>`;
}
function bindModels() {
  document.querySelectorAll("[data-channel]").forEach(
    (button) =>
      (button.onclick = () => {
        selected = button.dataset.channel;
        store.set("channel", selected);
        current = 0;
        buildSimulation();
        render();
      }),
  );
}
function buildSimulation() {
  simFrames = [];
  const m = matchup();
  if (m.lp == null) return;
  const first = simulateSeries(...m.lf, m.lp, simSeed),
    second = simulateSeries(
      m.gf[0],
      first.winner,
      pmap(m.gf[0], first.winner),
      simSeed + 1,
    );
  for (const [index, series] of [first, second].entries()) {
    simFrames.push({
      index,
      teams: series.teams,
      score: [0, 0],
      caption: `赛前分析 · ${event.matches[index].label}`,
      kind: "pre",
    });
    series.maps.forEach((map, i) =>
      simFrames.push({
        index,
        teams: series.teams,
        score: map.score,
        caption: `模拟第 ${i + 1} 图 · ${map.winner} 获胜`,
        kind: "map",
      }),
    );
    simFrames.push({
      index,
      teams: series.teams,
      score: series.score,
      caption: `模拟赛果 · ${series.winner} 晋级${index === 1 ? "并夺冠" : ""}`,
      kind: "final",
    });
  }
  current = Math.min(current, simFrames.length - 1);
}
function home() {
  const c = channel(),
    m = matchup("codex");
  main.innerHTML = `<section class="hero"><div class="wrap"><div class="hero-top"><div><p class="eyebrow">AI 模拟内容 · 仅供参考</p><h1>VALORANT AI 大模型预测大赛</h1><p>上海全球冠军赛最后两场，同一份官方资料、同一套 BO5 规则，各自给出判断</p></div><div class="hero-actions"><div class="countdown"><small>仅预测 10 月 17 / 18 日</small><strong>决赛周末</strong></div><a class="btn" href="#/pickem">我也来预测</a><a class="btn primary" href="#/leaderboard">看谁最准</a></div></div><div class="portraits" aria-label="选择模型形象">${channels.map((ch, i) => `<button class="portrait ${selected === ch.id ? "on" : ""}" data-channel="${ch.id}" aria-label="进入 ${ch.name} 的频道"><img src="${escape(assets.agents[i].url)}&w=280" alt="" loading="${i < 4 ? "eager" : "lazy"}"><span>${ch.name.split(" · ")[0]}</span></button>`).join("")}</div></div></section><div class="channel-panel"><div class="wrap">${modelGrid()}</div></div><div class="wrap section"><div class="tabs" role="tablist" aria-label="预测频道内容">${[
    ["live", "直播"],
    ["schedule", "赛程赛果"],
    ["bracket", "淘汰赛"],
    ["analysis", "赛前评估"],
    ["process", "预测过程"],
  ]
    .map(
      ([id, name]) =>
        `<button role="tab" aria-selected="${tab === id}" data-tab="${id}" class="${tab === id ? "on" : ""}">${name}</button>`,
    )
    .join(
      "",
    )}</div><p class="muted" style="font-size:12px;margin:12px 0">${escape(c.name)} · ${available(c.id) ? escape(c.name) + " 的独立条件预测；系列赛按模型单图概率推演" : "尚无该模型实际输出"} · <a class="source-link" href="#/about">统计与来源说明</a></p><div id="channel-content"></div></div><section class="wrap section"><div class="section-head"><h2>各 AI 预测的冠军</h2><a class="muted" href="#/compare">完整对比 →</a></div><p class="muted">每个频道保留独立预测。未实际运行的模型显示待预测。</p><div class="grid">${channels
    .map((ch) => {
      const cm = matchup(ch.id);
      return `<a class="card forecast-card card-link" style="--accent:${ch.color}" href="#/?ai=${ch.id}"><h3>${ch.name}</h3><small class="muted">${available(ch.id) ? "当前晋级情景下的预测" : "等待独立模型输出"}</small><div class="champ">${available(ch.id) ? logo(cm.gp >= 0.5 ? cm.gf[0] : cm.gf[1]) + " " + (cm.gp >= 0.5 ? cm.gf[0] : cm.gf[1]) : "待预测"}</div><span class="muted">进入频道 →</span></a>`;
    })
    .join(
      "",
    )}</div></section><section class="wrap section"><div class="section-head"><h2>最后两场 · 官方赛程</h2><a class="muted" href="#/pickem">写下你的判断 →</a></div>${officialSchedule()}</section><section class="wrap section"><div class="card"><h2>谁才是真正的预言家？</h2><p class="muted">两场比赛结束后，用真实赛果检验预测。没有赛果时，排行榜保持等待结算。</p><a class="btn" href="#/leaderboard">查看排行榜</a></div></section>`;
  bindModels();
  document.querySelectorAll("[data-tab]").forEach(
    (b) =>
      (b.onclick = () => {
        tab = b.dataset.tab;
        render();
      }),
  );
  renderChannel();
}
function officialSchedule() {
  return `<div class="table-wrap"><table><thead><tr><th>比赛</th><th>北京时间</th><th>官方对阵</th><th>赛制</th><th>状态</th></tr></thead><tbody>${event.matches.map((m) => `<tr><td>${m.label}</td><td>${formatDate(m.start_utc)}</td><td>${m.teams.join(" vs ")}</td><td>BO${m.best_of}</td><td>${m.winner ? m.score.join(" : ") : "待开赛"}</td></tr>`).join("")}</tbody></table></div>`;
}
function formatDate(value) {
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}
function renderChannel() {
  const content = $("#channel-content");
  if (!content) return;
  const m = matchup();
  if (tab === "schedule") {
    content.innerHTML =
      note() +
      officialSchedule() +
      `<div class="notice blue">以上为官方赛程。模拟比分只出现在直播与淘汰赛视图。</div>`;
    return;
  }
  if (tab === "bracket") {
    content.innerHTML =
      note() +
      scenarioForm() +
      `<div class="bracket"><div class="pick-match"><h3>17 日 · 败者组决赛</h3>${m.lf.map((t) => `<div class="pick-team">${logo(t)}<b>${t}</b></div>`).join("")}</div><div class="bracket-arrow">→</div><div class="pick-match"><h3>18 日 · 总决赛 · 模型推演</h3>${m.gf.map((t) => `<div class="pick-team">${logo(t)}<b>${t || "待预测"}</b></div>`).join("")}</div><div class="bracket-arrow">→</div><div class="result-card card"><small>该频道预测冠军</small><h2>${m.gp == null ? "待预测" : m.gp >= 0.5 ? m.gf[0] : m.gf[1]}</h2></div></div>`;
    bindScenario();
    return;
  }
  if (tab === "analysis") {
    content.innerHTML =
      note() +
      scenarioForm() +
      (available(selected)
        ? analysisTable(forecasts[selected])
        : '<div class="card empty">该模型尚未输出赛前评估</div>');
    bindScenario();
    return;
  }
  if (tab === "process") {
    content.innerHTML = `<div class="card article"><h2>预测过程</h2><ol><li>从 Riot 官网赛事页提取本届 ${event.history.length} 场已完成系列赛。</li><li>只根据 17、18 日两场的晋级关系建立条件对阵。</li><li>${available(selected) ? escape(channel().name) + " 独立读取官方战绩后，给出六组可能对阵的单图主观概率。" : "该频道尚未运行，不展示代填预测。"}</li><li>把每张地图的独立获胜概率换算为先赢三图的 BO5 系列赛分布。</li><li>播放器按固定随机种子实际推演比赛；一次模拟不代表最可能赛果。</li></ol><p class="muted">${escape(forecast.calibration)}</p><a class="btn" href="data/gpt-6.1-sol-forecast.json" target="_blank">查看原始预测 JSON</a></div>`;
    return;
  }
  content.innerHTML =
    note() +
    `<div class="studio" tabindex="0" role="region" aria-label="AI 模拟回放播放器"><div><div class="stage-box"><div class="stage-top"><span class="pill">● AI 模拟</span><span>${escape(channel().name)} 的世界</span><span class="stage-date" id="stage-date"></span></div><div id="stage"></div></div><div class="progress"><i id="progress" style="width:0"></i></div><div class="controls"><button id="prev" aria-label="上一步">◀</button><button id="play" class="play" title="${playing ? "暂停" : "播放"} (空格)">${playing ? "Ⅱ 暂停" : "▶ 播放"}</button><button id="next" aria-label="下一步">▶|</button><button id="next-match">下一场</button><button id="next-day">下一天</button><button id="mute">${muted ? "取消静音" : "静音"}</button><span class="spacer"></span>${[1, 2, 4, 8].map((n) => `<button data-speed="${n}" class="${speed === n ? "on" : ""}">${n}x</button>`).join("")}</div><p class="keyboard-tip">播放器获得焦点后：空格播放/暂停，左右跳步，上下调速，M 静音。</p><div class="date-buttons"><button data-day="0">10/17</button><button data-day="1">10/18</button></div></div><aside class="schedule"><h3>今日赛程 · 最后两场</h3>${event.matches.map((match, i) => `<div class="schedule-row" data-row="${i}"><b>${match.label}<small class="muted" style="display:block;margin-top:8px">${formatDate(match.start_utc)}</small></b><span>BO5</span></div>`).join("")}<div style="padding:12px"><span class="pill official">官方对阵待定</span><p class="muted" style="font-size:12px;margin:12px 0">胜者组败者 → 败者组决赛<br>败者组胜者 → 总决赛</p><a class="btn" href="#/pickem">我也来预测</a></div></aside></div>`;
  bindPlayer();
  updatePlayer();
}
function updatePlayer() {
  if (!$("#stage")) return;
  if (!simFrames.length) {
    $("#stage").innerHTML =
      `<div class="empty"><div class="symbol">◌</div><h2>该模型等待预测</h2><p class="muted">没有真实模型输出，暂不生成模拟比分。</p></div>`;
    $("#stage-date").textContent = "10 月 17 / 18 日";
    for (const id of ["play", "prev", "next", "next-match", "next-day"])
      $("#" + id).disabled = true;
    return;
  }
  const frame = simFrames[current];
  $("#stage-date").textContent =
    frame.index === 0 ? "10 月 17 日" : "10 月 18 日";
  $("#stage").innerHTML =
    `<div class="versus"><div class="vs-team">${logo(frame.teams[0])}<b>${frame.teams[0]}</b></div><div class="score">${frame.score.join(" : ")}<small>BO5 · ${frame.kind === "pre" ? "赛前" : frame.kind === "final" ? "模拟赛果" : "模拟地图"}</small></div><div class="vs-team">${logo(frame.teams[1])}<b>${frame.teams[1]}</b></div></div><p class="stage-caption">${frame.caption}</p>`;
  $("#progress").style.width = `${(100 * (current + 1)) / simFrames.length}%`;
  $("#prev").disabled = current === 0;
  $("#next").disabled = current === simFrames.length - 1;
  $("#play").textContent = playing ? "Ⅱ 暂停" : "▶ 播放";
  $("#play").title = playing ? "暂停 (空格)" : "播放 (空格)";
  document
    .querySelectorAll("[data-day]")
    .forEach((b) =>
      b.classList.toggle("on", Number(b.dataset.day) === frame.index),
    );
  document
    .querySelectorAll("[data-row]")
    .forEach((b) =>
      b.classList.toggle("active", Number(b.dataset.row) === frame.index),
    );
}
function step(n) {
  current = Math.max(0, Math.min(current + n, simFrames.length - 1));
  if (current === simFrames.length - 1) playing = false;
  updatePlayer();
  sound();
  setPlayerTimer();
}
function setPlayerTimer() {
  clearTimeout(playerTimer);
  if (playing && pageRoute === "/" && tab === "live" && simFrames.length)
    playerTimer = setTimeout(() => step(1), 1800 / speed);
}
function togglePlay() {
  if (!simFrames.length) return;
  if (!playing && current === simFrames.length - 1) current = 0;
  playing = !playing;
  updatePlayer();
  setPlayerTimer();
}
function jump(index) {
  const target = simFrames.findIndex((f) => f.index === index);
  if (target >= 0) {
    current = target;
    updatePlayer();
    setPlayerTimer();
  }
}
function bindPlayer() {
  $("#play").onclick = togglePlay;
  $("#prev").onclick = () => step(-1);
  $("#next").onclick = () => step(1);
  $("#next-match").onclick = () => jump(1);
  $("#next-day").onclick = () => jump(1);
  $("#mute").onclick = () => {
    muted = !muted;
    store.set("muted", muted);
    $("#mute").textContent = muted ? "取消静音" : "静音";
    sound();
  };
  document.querySelectorAll("[data-speed]").forEach(
    (b) =>
      (b.onclick = () => {
        speed = Number(b.dataset.speed);
        document
          .querySelectorAll("[data-speed]")
          .forEach((n) => n.classList.toggle("on", n === b));
        setPlayerTimer();
      }),
  );
  document
    .querySelectorAll("[data-day]")
    .forEach((b) => (b.onclick = () => jump(Number(b.dataset.day))));
  $(".studio").onkeydown = (e) => {
    if (/^(BUTTON|A|SELECT|INPUT|TEXTAREA)$/.test(e.target.tagName)) return;
    if (
      [
        " ",
        "ArrowLeft",
        "ArrowRight",
        "ArrowUp",
        "ArrowDown",
        "m",
        "M",
      ].includes(e.key)
    ) {
      e.preventDefault();
      if (e.key === " ") togglePlay();
      else if (e.key === "ArrowLeft") step(-1);
      else if (e.key === "ArrowRight") step(1);
      else if (e.key.toLowerCase() === "m") $("#mute").click();
      else {
        speed = Math.min(
          8,
          Math.max(1, e.key === "ArrowUp" ? speed * 2 : speed / 2),
        );
        renderChannel();
        setPlayerTimer();
      }
    }
  };
  setPlayerTimer();
}
function analysisTable(model = forecast) {
  return `<div class="table-wrap" style="margin-top:20px"><table><thead><tr><th>可能对阵</th><th>左队单图概率</th><th>左队 BO5 概率</th><th>依据（${escape(model.model_id)}）</th></tr></thead><tbody>${model.pairs.map((p) => `<tr><td>${p.teams.join(" vs ")}</td><td class="heat">${pct(p.p_first)}</td><td class="heat">${pct(seriesProbability(p.p_first))}</td><td style="white-space:normal;min-width:300px">${escape(p.reason)}</td></tr>`).join("")}</tbody></table></div>`;
}
function comparePage() {
  main.innerHTML =
    pageHead("数据对比", "同一份官方战绩，比较每个模型的两场条件预测") +
    `<div class="wrap section">${note()}${scenarioForm()}<div class="section"><h2>BO5 预测概率对比</h2><p class="muted">左侧队伍获胜的概率。未运行的模型保持待预测；统计基线由公开公式计算。</p><div class="table-wrap"><table><thead><tr><th>可能对阵</th>${channels.map((c) => `<th>${c.name}</th>`).join("")}<th>统计基线</th></tr></thead><tbody>${forecast.pairs.map((p) => `<tr><td>${p.teams.join(" vs ")}</td>${channels.map((c) => `<td class="${available(c.id) ? "heat" : "muted"}">${available(c.id) ? pct(seriesProbability(pmap(...p.teams, c.id))) : "待预测"}</td>`).join("")}<td class="heat">${pct(seriesProbability(baselineProbability(event, ...p.teams)))}</td></tr>`).join("")}</tbody></table></div></div><h2>当前情景 · 比分分布</h2><p class="muted">六个可能的 BO5 最终比分概率之和为 100%；来自单图独立、同概率假设。</p><div class="grid" id="distributions"></div>${analysisTable()}</div>`;
  bindScenario();
  const m = matchup();
  $("#distributions").innerHTML = seriesDistribution(
    mapProbability(forecast, ...m.lf),
  )
    .sort((a, b) => b.probability - a.probability)
    .map(
      (r) =>
        `<div class="card"><h3>${m.lf[0]} ${r.score.join(" : ")} ${m.lf[1]}</h3><b class="gold">${pct(r.probability)}</b></div>`,
    )
    .join("");
}
function teamsPage(code) {
  if (code && event.teams[code]) {
    const t = event.teams[code],
      s = teamStats(event, code),
      history = event.history.filter((m) => m.teams.includes(code));
    main.innerHTML =
      pageHead(t.name, "官方本届系列赛记录 · 历史事实不计入两场预测") +
      `<div class="wrap section"><div class="card"><div class="team-head">${logo(code)}<div><h2>${code}</h2><span class="muted">${escape(t.region?.toUpperCase())}</span></div></div><div class="stats"><div class="stat"><strong>${s.wins} / ${s.played}</strong><span>系列赛获胜 / 已赛</span></div><div class="stat"><strong>${s.mapsWon}–${s.mapsLost}</strong><span>地图胜负</span></div><div class="stat"><strong>${pct(s.mapsWon / (s.mapsWon + s.mapsLost))}</strong><span>地图胜率</span></div></div>${history.map((m) => `<div class="history-line"><small class="muted">${formatDate(m.start_utc)}</small><b>${m.teams.join(" vs ")}</b><span>${m.score.join(" : ")}</span><span class="tag">真实赛果</span></div>`).join("")}</div><div class="actions"><a class="btn" href="#/teams">返回战队</a><a class="btn" href="https://valorantesports.com/en-US/" target="_blank" rel="noreferrer">官方来源 ↗</a></div></div>`;
    return;
  }
  main.innerHTML =
    pageHead("战队", "决赛周末四强，及本届全球冠军赛的官方战绩") +
    `<div class="wrap section"><input class="team-search" id="team-search" type="search" placeholder="搜索战队名称或简称" aria-label="搜索战队"><div class="grid" id="team-grid"></div></div>`;
  const renderTeams = (query) => {
    const finalists = event.predecessors.flatMap((p) => p.teams),
      all = Object.values(event.teams).sort(
        (a, b) =>
          (finalists.includes(b.code) ? 1 : 0) -
          (finalists.includes(a.code) ? 1 : 0),
      );
    const list = all.filter((t) =>
      (t.code + " " + t.name).toLowerCase().includes(query.toLowerCase()),
    );
    $("#team-grid").innerHTML = list.length
      ? list
          .map((t) => {
            const s = teamStats(event, t.code);
            return `<a class="card card-link" href="#/team/${t.code}"><div class="team-head">${logo(t.code)}<div><h3>${t.code}</h3><small class="muted">${escape(t.name)}</small></div></div><div class="stats"><div class="stat"><strong>${s.wins}–${s.played - s.wins}</strong><span>系列赛</span></div><div class="stat"><strong>${s.mapsWon}–${s.mapsLost}</strong><span>地图</span></div></div><span class="tag">${finalists.includes(t.code) ? "决赛周末四强" : "本届参赛队"}</span></a>`;
          })
          .join("")
      : '<div class="card empty">没有找到匹配战队</div>';
  };
  renderTeams("");
  $("#team-search").oninput = (e) => renderTeams(e.target.value);
}
function pickemPage() {
  const { upperWinner, upperLoser, lowerWinner } = opponentPairs(),
    teams = [upperLoser, lowerWinner],
    finalists = [upperWinner, draft.lfWinner];
  main.innerHTML =
    pageHead("我来预测", "只预测两场：选出败者组决赛胜者，再选出上海全球冠军") +
    `<div class="wrap section"><div class="tabs" role="tablist"><button class="on" role="tab" aria-selected="true" id="my-tab">我的预测</button><button role="tab" aria-selected="false" id="sim-tab">模拟两场</button></div>${note()}${scenarioForm()}<div class="stepper"><span class="on">1 · 败者组决赛</span><span class="${draft.lfWinner ? "on" : ""}">2 · 总决赛</span><span class="${draft.champion ? "on" : ""}">3 · 预测战报</span></div><div class="form-row"><label>战队实力参考<select id="reference-model">${channels
      .filter((c) => available(c.id))
      .map((c) => `<option value="${c.id}">${c.name}</option>`)
      .join(
        "",
      )}<option value="baseline">统计基线</option></select></label><button id="autofill" class="btn gold">按实力参考一键填完</button><button id="reset" class="btn">重新预测</button></div><div class="bracket"><div class="pick-match" id="lower-final"><h3>10 / 17 · 败者组决赛 <span>BO5</span></h3>${teams.map((t) => pickTeam(t, draft.lfWinner, "lf", mapProbability(forecast, ...teams), teams[0])).join("")}${draft.lfWinner ? scoreSelect("lf", draft.lfWinner, teams, draft.lfScore) : ""}</div><div class="bracket-arrow">→</div><div class="pick-match" id="grand-final"><h3>10 / 18 · 总决赛 <span>BO5</span></h3>${finalists.map((t) => (t ? pickTeam(t, draft.champion, "gf", draft.lfWinner ? mapProbability(forecast, ...finalists) : null, finalists[0]) : '<button class="pick-team" disabled>等待败者组决赛胜者</button>')).join("")}${draft.champion ? scoreSelect("gf", draft.champion, finalists, draft.gfScore) : ""}</div><div class="bracket-arrow">→</div><div class="card result-card" id="pick-result"><small>你预测的上海全球冠军</small>${draft.champion ? logo(draft.champion) + "<h2>" + draft.champion + "</h2>" : '<h2>?</h2><p class="muted">完成两场选择后生成战报</p>'}</div></div><div class="actions"><button class="btn primary" id="save-pick" ${draft.champion ? "" : "disabled"}>保存预测战报</button><button class="btn" id="poster-button" ${draft.champion ? "" : "disabled"}>生成预测海报</button><button class="btn" id="share-pick" ${draft.champion ? "" : "disabled"}>复制分享链接</button></div><p class="muted" style="font-size:12px;margin-top:14px" id="save-state">${pick ? "上次预测：" + escape(pick.champion) + " 冠军 · " + escape(formatDate(pick.created_at)) : "预测保存在当前浏览器，可随时重新选择。"}</p><section class="card" id="personal-simulation" hidden style="margin-top:20px"></section></div>`;
  bindScenario();
  document.querySelectorAll("[data-pick]").forEach(
    (b) =>
      (b.onclick = () => {
        const t = b.dataset.team;
        if (b.dataset.pick === "lf") {
          draft.lfWinner = t;
          draft.lfScore = t === teams[0] ? [3, 1] : [1, 3];
          draft.champion = null;
          draft.gfScore = null;
        } else if (draft.lfWinner) {
          draft.champion = t;
          draft.gfScore = t === finalists[0] ? [3, 1] : [1, 3];
        }
        sound();
        pickemPage();
      }),
  );
  for (const phase of ["lf", "gf"]) {
    const field = $("#" + phase + "-score");
    if (field)
      field.onchange = () => {
        const pair = phase === "lf" ? teams : finalists,
          winner = phase === "lf" ? draft.lfWinner : draft.champion;
        const n = Number(field.value);
        draft[phase + "Score"] = winner === pair[0] ? [3, n] : [n, 3];
      };
  }
  $("#autofill").onclick = () => {
    const ref = $("#reference-model").value,
      p = pmap(...teams, ref);
    draft.lfWinner = p >= 0.5 ? teams[0] : teams[1];
    draft.lfScore = seriesDistribution(p)
      .filter(
        (r) => (r.score[0] === 3 ? teams[0] : teams[1]) === draft.lfWinner,
      )
      .sort((a, b) => b.probability - a.probability)[0].score;
    const fs = [upperWinner, draft.lfWinner],
      gp = pmap(...fs, ref);
    draft.champion = gp >= 0.5 ? fs[0] : fs[1];
    draft.gfScore = seriesDistribution(gp)
      .filter((r) => (r.score[0] === 3 ? fs[0] : fs[1]) === draft.champion)
      .sort((a, b) => b.probability - a.probability)[0].score;
    pickemPage();
    notify("已按所选实力参考填入两场预测");
  };
  $("#reset").onclick = () => {
    draft = { lfWinner: null, lfScore: null, champion: null, gfScore: null };
    pickemPage();
    notify("当前草稿已重置，已保存的战报仍可恢复");
  };
  $("#save-pick").onclick = savePick;
  $("#poster-button").onclick = showPoster;
  $("#share-pick").onclick = sharePick;
  $("#sim-tab").onclick = () => {
    const lp = pmap(...teams),
      lf = simulateSeries(...teams, lp, Date.now() % 4294967296),
      gf = simulateSeries(
        upperWinner,
        lf.winner,
        pmap(upperWinner, lf.winner),
        (Date.now() % 4294967296) + 1,
      );
    $("#personal-simulation").hidden = false;
    $("#personal-simulation").innerHTML =
      `<span class="pill">模拟赛果</span><h2 style="margin-top:15px">${gf.winner} 夺冠</h2><p>17 日 · ${lf.teams.join(" vs ")} · ${lf.score.join(" : ")}<br>18 日 · ${gf.teams.join(" vs ")} · ${gf.score.join(" : ")}</p><p class="muted">按GPT-6.1 sol 的单图概率实际随机推演。本次结果尚未写入你的预测。</p>`;
    $("#my-tab").classList.remove("on");
    $("#sim-tab").classList.add("on");
    $("#my-tab").setAttribute("aria-selected", "false");
    $("#sim-tab").setAttribute("aria-selected", "true");
  };
  $("#my-tab").onclick = () => {
    $("#personal-simulation").hidden = true;
    $("#my-tab").classList.add("on");
    $("#sim-tab").classList.remove("on");
    $("#my-tab").setAttribute("aria-selected", "true");
    $("#sim-tab").setAttribute("aria-selected", "false");
  };
}
function pickTeam(t, winner, phase, p, first) {
  return `<button class="pick-team ${winner === t ? "win" : winner ? "lose" : ""}" data-pick="${phase}" data-team="${t}" aria-pressed="${winner === t}">${logo(t)}<b>${t}</b><small>${p == null ? "待预测" : pct(seriesProbability(t === first ? p : 1 - p))}</small></button>`;
}
function scoreSelect(phase, winner, teams, score) {
  const loser = winner === teams[0] ? teams[1] : teams[0],
    losses = score ? Math.min(...score) : 1;
  return `<label class="score-select">${winner} 3 : <select id="${phase}-score" aria-label="${phase === "lf" ? "败者组决赛" : "总决赛"}负方地图数">${[0, 1, 2].map((n) => `<option value="${n}" ${n === losses ? "selected" : ""}>${n}</option>`).join("")}</select> ${loser}</label>`;
}
function makePick() {
  const pair = opponentPairs();
  return {
    version: 1,
    source_sha256: event.source_sha256,
    match_ids: event.matches.map((m) => m.id),
    upperWinner: pair.upperWinner,
    lowerWinner: pair.lowerWinner,
    ...draft,
    created_at: new Date().toISOString(),
  };
}
function savePick() {
  const value = makePick();
  if (!validatePick(value, event)) {
    notify("请先完成两场合法比分与胜者选择");
    return;
  }
  pick = value;
  if (store.set("pick", pick)) {
    notify("两场预测已保存");
    $("#save-state").textContent =
      "已保存 · " +
      formatDate(pick.created_at) +
      " · " +
      pick.champion +
      " 冠军";
  } else notify("浏览器存储不可用，可复制分享链接保存");
}
function showPoster() {
  if (!draft.champion) return;
  $("#poster-content").innerHTML =
    `<p class="kicker">CHAMPIONS SHANGHAI 2026</p><h2>我的决赛预测</h2>${logo(draft.champion)}<h1 class="gold" style="margin:18px 0">${draft.champion}</h1><p>10 / 17 · ${opponentPairs().upperLoser} ${draft.lfScore.join(" : ")} ${opponentPairs().lowerWinner}<br>10 / 18 · ${opponentPairs().upperWinner} ${draft.gfScore.join(" : ")} ${draft.lfWinner}</p><p class="muted">个人情景预测 · 非官方赛果</p>`;
  $("#poster").showModal();
}
async function sharePick() {
  const value = makePick();
  if (!validatePick(value, event)) return;
  const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(value))))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
  const url = location.href.split("#")[0] + "#/pickem?share=" + encoded;
  try {
    await navigator.clipboard.writeText(url);
    notify("已复制分享链接");
  } catch {
    const field = document.createElement("textarea");
    field.value = url;
    field.setAttribute("aria-label", "手动复制预测链接");
    $("#save-state").replaceChildren(field);
    field.focus();
    field.select();
    notify("可从文本框手动复制链接");
  }
}
function leaderboardPage() {
  const rows = event.matches.filter((m) => m.winner);
  main.innerHTML =
    pageHead("谁最准", "只用 17、18 日两场官方真实赛果结算") +
    `<div class="wrap section"><div class="card"><div class="section-head"><h2>真实赛果 · ${rows.length} / 2 场已结算</h2><span class="pill official">官方赛果</span></div>${officialSchedule()}${rows.length ? "" : '<div class="empty"><p class="symbol">◷</p><h2>等待真实赛果</h2><p class="muted">两场比赛尚未结束。准确率与 Brier 分数暂不计算。</p></div>'}</div><section class="section"><h2>预测排行榜</h2><div class="table-wrap"><table><thead><tr><th>模型 / 参与者</th><th>已结算场数</th><th>预测命中</th><th>Brier 分数</th><th>状态</th></tr></thead><tbody>${channels
      .map((c) => {
        const scored = available(c.id)
          ? rows
              .map((r) => {
                const p = mapProbability(forecasts[c.id], ...r.teams);
                return p == null
                  ? null
                  : {
                      p: seriesProbability(p),
                      winner: r.winner === r.teams[0] ? 1 : 0,
                    };
              })
              .filter(Boolean)
          : [];
        return `<tr><td>${c.name}</td><td>${scored.length}</td><td>${scored.length ? scored.filter((r) => (r.p >= 0.5 ? 1 : 0) === r.winner).length + " / " + scored.length : "—"}</td><td>${scored.length ? (scored.reduce((s, r) => s + (r.p - r.winner) ** 2, 0) / scored.length).toFixed(4) : "—"}</td><td class="muted">${available(c.id) ? (scored.length ? "已结算" : "等待赛果") : "待预测"}</td></tr>`;
      })
      .join(
        "",
      )}<tr><td>我的预测${pick ? " · " + pick.champion : ""}</td><td>${pick ? rows.length : 0}</td><td>${pick && rows.length ? rows.filter((r) => r.winner === (r.id === event.matches[0].id ? pick.lfWinner : pick.champion)).length + " / " + rows.length : "—"}</td><td>—</td><td class="muted">${pick ? "已保存，等待完整赛果" : "尚未填写"}</td></tr></tbody></table></div><div class="notice blue">Brier 分数是预测概率与真实胜负之差的平方，越低越好。模型未输出或比赛未结束时不占位计分。个人胜者选择单独显示命中数。</div></section><a class="btn primary" href="#/pickem">${pick ? "查看我的预测" : "我也来预测"}</a></div>`;
}
function methodPage() {
  main.innerHTML =
    pageHead("AI 赛制介绍", "同一份数据、独立输出，区分预测、推演和真实赛果") +
    `<div class="wrap section article"><div class="method-grid"><section class="card"><span class="kicker">01 · DATA</span><h2>官方资料</h2><p>Riot 赛事官网的赛程、对阵、赛制和 ${event.history.length} 场已完成系列赛记录。资料截止 ${escape(formatDate(forecast.data_cutoff))}。</p></section><section class="card"><span class="kicker">02 · FORECAST</span><h2>独立预测</h2><p>各频道只展示实际生成的输出。已接入的独立预测可以横向比较；其他频道保持待预测。</p></section><section class="card"><span class="kicker">03 · SCORE</span><h2>赛后检验</h2><p>只结算 17 日败者组决赛与 18 日总决赛。真实赛果出现后计算命中与 Brier 分数。</p></section></div><section class="card section" style="margin-top:20px"><h2>BO5 如何计算？</h2><p>一场比赛先赢三张地图即获胜。设某队单图胜率为 p，在地图独立且同概率的简化假设下，3:k 的概率为 C(2+k,k) × p³ × (1−p)ᵏ，k 为 0、1、2。</p><p>把 3:0、3:1、3:2 相加，得到该队赢下 BO5 的概率。播放器用相同单图概率和固定随机种子逐图推演，完整生成两场比赛。</p></section><section class="card"><h2>统计基线</h2><p>只用本届地图胜负，强度 =（地图胜场 + 1）/（地图负场 + 1），对阵单图概率 = 左队强度 / 两队强度之和。这是透明的样本平滑基线，没有训练或回测，不是官方胜率。</p><p class="muted">${escape(forecast.calibration)}</p></section><section class="card" style="margin-top:20px"><h2>只保留最后两场</h2><p>16 日两场只作为晋级条件。不会重新预测小组赛和已经结束的淘汰赛；个人预测和 AI 预测都聚焦 17、18 日。</p><a class="btn" href="#/pickem">开始我的预测</a></section></div>`;
}
function aboutPage() {
  main.innerHTML =
    pageHead("内容、数据与素材说明", "来源可追溯，未知信息保持未知") +
    `<div class="wrap section article"><section class="card"><h2>赛事数据</h2><p>最近获取：${escape(new Date(event.fetched_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" }))}（北京时间）。官方页面结构化数据中共提取 ${event.history.length} 场已完成系列赛，本应用只预测两场 BO5。</p><ul>${event.sources.map((s) => `<li><a href="${escape(s.url)}" target="_blank" rel="noreferrer">${escape(s.publisher)} · ${s.role === "official_schedule_results" ? "官方赛程与真实结果" : "上海冠军赛赛制说明"} ↗</a></li>`).join("")}</ul><p class="muted">${event.limitations.map(escape).join("<br>")}</p><details><summary>快照与原始数据</summary><p style="overflow-wrap:anywhere">官方响应 SHA-256：${event.source_sha256}</p><a href="data/event.json" target="_blank" class="source-link">查看赛事快照 JSON</a></details></section><section class="card" style="margin-top:20px"><h2>预测来源</h2><p>GPT-6.1 sol 频道由已核实的 gpt-6.1-sol / high 独立运行根据官方记录生成，不代表其他模型。DeepSeek V4.1 Flash 来自经核实的官方 API 实际响应；其他模型等待真实输出。展示中所有主观概率、模拟比分都标识为预测或模拟。</p><a class="source-link" href="data/gpt-6.1-sol-forecast.json" target="_blank">查看GPT-6.1 sol 原始预测与理由</a></section><section class="card" style="margin-top:20px"><h2>视觉参考与素材</h2><p>交互与页面结构参考用户指定的 <a href="https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html" target="_blank" rel="noreferrer">S16 AI 预测大赛</a>。赛事内容改为 VALORANT，范围限定为最后两场。前端代码独立编写。</p><p>英雄立绘来自 <a href="https://playvalorant.com/en-us/agents/" target="_blank" rel="noreferrer">VALORANT 英雄官网</a>，战队标志来自 Riot 赛事官网页面引用的公开 CDN。仅引用公开 URL，权利归 Riot Games 与各战队；模型频道的装饰英雄不代表任何合作关系。</p></section><section class="card" style="margin-top:20px"><h2>本地保存与分享</h2><p>个人预测、频道、静音和晋级情景保存在当前浏览器。分享链接只包含你选择的晋级情景、两场比分和生成时间。数据不会上传。</p></section></div>`;
}
function route() {
  clearTimeout(playerTimer);
  playing = false;
  const [path, query = ""] = (location.hash.slice(1) || "/").split("?");
  pageRoute = path;
  const params = new URLSearchParams(query);
  if (params.get("ai") && channels.some((c) => c.id === params.get("ai")))
    selected = params.get("ai");
  if (path === "/pickem" && params.has("share")) {
    try {
      const value = JSON.parse(
        decodeURIComponent(
          escapeUnicode(
            atob(params.get("share").replace(/-/g, "+").replace(/_/g, "/")),
          ),
        ),
      );
      if (!validatePick(value, event)) throw Error();
      scenario = {
        upperWinner: value.upperWinner,
        lowerWinner: value.lowerWinner,
      };
      draft = {
        lfWinner: value.lfWinner,
        lfScore: value.lfScore,
        champion: value.champion,
        gfScore: value.gfScore,
      };
      notify("已打开分享的预测；保存后留在当前浏览器");
    } catch {
      notify("分享链接无效或不适用于当前赛事数据");
    }
  }
  buildSimulation();
  render();
  window.scrollTo(0, 0);
}
function escapeUnicode(s) {
  return s
    .split("")
    .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
    .join("");
}
function render() {
  document.querySelectorAll(".mainnav a").forEach((a) => {
    const on =
      a.getAttribute("href") ===
      "#" + (pageRoute.startsWith("/team/") ? "/teams" : pageRoute);
    a.classList.toggle("on", on);
    if (on) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  if (pageRoute === "/") home();
  else if (pageRoute === "/compare") comparePage();
  else if (pageRoute === "/teams") teamsPage();
  else if (pageRoute.startsWith("/team/"))
    teamsPage(decodeURIComponent(pageRoute.split("/")[2]));
  else if (pageRoute === "/pickem") pickemPage();
  else if (pageRoute === "/leaderboard") leaderboardPage();
  else if (pageRoute === "/method") methodPage();
  else if (pageRoute === "/about") aboutPage();
  else
    main.innerHTML =
      pageHead("页面不存在", "可以返回首页继续查看两场决赛预测") +
      '<div class="wrap section"><a class="btn" href="#/">返回首页</a></div>';
  document.title =
    (pageRoute === "/pickem" ? "我来预测 · " : "") + "VALORANT AI 决赛预测大赛";
}
$(".skip-link").onclick = (e) => {
  e.preventDefault();
  main.focus();
  main.scrollIntoView({ behavior: "instant", block: "start" });
};
$("#close-poster").onclick = () => $("#poster").close();
$("#poster").onclick = (e) => {
  if (e.target === $("#poster")) $("#poster").close();
};
$("#download-poster").onclick = () => {
  const canvas = document.createElement("canvas");
  canvas.width = 800;
  canvas.height = 1000;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#101632";
  ctx.fillRect(0, 0, 800, 1000);
  ctx.fillStyle = "#c8aa6e";
  ctx.textAlign = "center";
  ctx.font = "bold 28px sans-serif";
  ctx.fillText("CHAMPIONS SHANGHAI 2026", 400, 120);
  ctx.fillStyle = "#e6e1e5";
  ctx.font = "bold 48px sans-serif";
  ctx.fillText("我的决赛预测", 400, 230);
  ctx.fillStyle = "#c8aa6e";
  ctx.font = "bold 120px sans-serif";
  ctx.fillText(draft.champion, 400, 450);
  ctx.fillStyle = "#c1e5ff";
  ctx.font = "26px sans-serif";
  ctx.fillText(
    `10/17  ${opponentPairs().upperLoser} ${draft.lfScore.join(":")} ${opponentPairs().lowerWinner}`,
    400,
    620,
  );
  ctx.fillText(
    `10/18  ${opponentPairs().upperWinner} ${draft.gfScore.join(":")} ${draft.lfWinner}`,
    400,
    690,
  );
  ctx.fillStyle = "#8a90bd";
  ctx.font = "22px sans-serif";
  ctx.fillText("个人情景预测 · 非官方赛果", 400, 880);
  const a = document.createElement("a");
  a.download = "VALORANT-我的决赛预测.png";
  a.href = canvas.toDataURL("image/png");
  a.click();
};
async function start() {
  try {
    const fetchJSON = async (url) => {
      const response = await fetch(url, { cache: "no-cache" });
      if (!response.ok) throw Error("HTTP " + response.status);
      return response.json();
    };
    let manifest;
    [event, assets, manifest] = await Promise.all(
      ["data/event.json", "data/assets.json", "data/model-forecasts.json"].map(
        fetchJSON,
      ),
    );
    forecasts = Object.fromEntries(
      await Promise.all(
        Object.entries(manifest).map(async ([channel, path]) => [
          channel,
          await fetchJSON("data/" + path),
        ]),
      ),
    );
    forecast = forecasts.codex;
    if (!forecast) throw Error("GPT-6.1 sol 预测数据缺失");
    if (
      event.matches.length !== 2 ||
      event.matches.some((m) => m.best_of !== 5)
    )
      throw Error("赛事数据不符合两场 BO5 范围");
    scenario = store.get("scenario", {
      upperWinner: event.predecessors[0].teams[1],
      lowerWinner: event.predecessors[1].teams[1],
    });
    for (const [key, index] of [
      ["upperWinner", 0],
      ["lowerWinner", 1],
    ])
      if (!event.predecessors[index].teams.includes(scenario[key]))
        scenario[key] = event.predecessors[index].teams[0];
    if (pick && validatePick(pick, event)) {
      scenario = {
        upperWinner: pick.upperWinner,
        lowerWinner: pick.lowerWinner,
      };
      draft = {
        lfWinner: pick.lfWinner,
        lfScore: pick.lfScore,
        champion: pick.champion,
        gfScore: pick.gfScore,
      };
    } else if (pick) {
      notify("已保存的旧预测与当前资料不一致，原始记录仍保留");
      pick = null;
    }
    window.addEventListener("hashchange", route);
    route();
    const updateCountdown = () => {
      const remaining = new Date(event.matches[0].start_utc) - Date.now();
      const hours = Math.floor(remaining / 3600000),
        minutes = Math.floor((remaining % 3600000) / 60000);
      $("#countdown").textContent =
        remaining > 0
          ? `距败者组决赛 ${hours} 时 ${minutes} 分`
          : "决赛周末 · 官方快照";
    };
    updateCountdown();
    setInterval(updateCountdown, 60000);
  } catch (error) {
    main.innerHTML =
      pageHead(
        "赛事数据暂不可用",
        "请重试；数据加载失败不代表比赛尚未开始或没有记录",
      ) +
      `<div class="wrap section"><div class="notice">${escape(error.message)}</div><button class="btn" id="retry">重试</button></div>`;
    $("#retry").onclick = start;
  }
}
start();
