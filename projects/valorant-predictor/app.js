import {
  mapProbability,
  seriesDistribution,
  seriesProbability,
  finalsProbabilities,
  remainingSeriesProbability,
  teamStats,
  baselineProbability,
  validScore,
  validatePick,
  simulateSeries,
  validRanking,
  rankingProbability,
  moveRanking,
} from "./engine.mjs";
import { fictionFor, aggregateFictionPlayers } from "./fiction.mjs";
import { vetoMarkup, mountVeto } from "./veto.mjs";
import { tacticalMarkup, mountTactical, stopTactical } from "./tactical-replay.mjs";
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
  ["codex", "GPT-6.1 sol", "◎", "#c5b174"],
  ["deepseek", "DeepSeek V4.1 Flash", "≈", "#eeeae1"],
  ["doubao", "豆包", "●", "#a89758"],
  ["mimo", "MiMo V2.6 Pro", "M", "#9b9d94"],
].map(([id, name, icon, color]) => ({ id, name, icon, color }));
let event,
  officialCurrent,
  assets,
  forecast,
  forecasts = {},
  modelManifest = {},
  fiction = {},
  fictionManifest = {},
  fictionContext,
  selected = store.get("channel", "codex"),
  tab = "veto",
  current = 0,
  playing = false,
  speed = 1,
  muted = store.get("muted", false),
  scenario,
  simFrames = [],
  simSeries = [],
  simSeed = 20261017,
  playerTimer,
  toastTimer,
  audio;
let customRanking = store.get("ranking", null),
  personalReference = store.get("reference", "codex"),
  rankingDraft = null,
  rankingSelection = null;
let pick = store.get("pick", null),
  draft = { lfWinner: null, lfScore: null, champion: null, gfScore: null },
  pageRoute = "/";
let tickerOpen = true,
  tickerPaused = matchMedia("(prefers-reduced-motion: reduce)").matches;
function notify(text) {
  $("#toast").textContent = text;
  $("#toast").classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $("#toast").classList.remove("show"), 3000);
}
function sound(kind = "pick") {
  if (muted) return;
  try {
    audio ??= new AudioContext();
    audio.resume();
    const cues = {
      pick: [
        [660, 0.12, 0.08, 0],
        [990, 0.1, 0.05, 0.04],
      ],
      win: [523, 659, 784, 1046].map((hz, i) => [hz, 0.35, 0.09, i * 0.09]),
      advance: [392, 523, 659].map((hz, i) => [hz, 0.25, 0.08, i * 0.08]),
      champion: [523, 659, 784, 1046, 784, 1046, 1318].map((hz, i) => [
        hz,
        0.4,
        0.1,
        i * 0.13,
      ]),
      stamp: [[140, 0.12, 0.2, 0]],
    };
    const origin = audio.currentTime;
    for (const [hz, duration, volume, delay] of cues[kind] || cues.pick) {
      const oscillator = audio.createOscillator();
      const envelope = audio.createGain();
      const start = origin + delay;
      oscillator.type = kind === "stamp" ? "sine" : "triangle";
      oscillator.frequency.setValueAtTime(hz, start);
      if (kind === "stamp") oscillator.frequency.exponentialRampToValueAtTime(hz - 60, start + duration);
      envelope.gain.setValueAtTime(0, start);
      envelope.gain.linearRampToValueAtTime(volume, start + 0.01);
      envelope.gain.exponentialRampToValueAtTime(0.0001, start + duration);
      oscillator.connect(envelope);
      envelope.connect(audio.destination);
      oscillator.start(start);
      oscillator.stop(start + duration + 0.02);
    }
    const noise = (duration, volume, delay, cutoff) => {
      const buffer = audio.createBuffer(1, Math.floor(audio.sampleRate * duration), audio.sampleRate);
      const samples = buffer.getChannelData(0);
      for (let i = 0; i < samples.length; i++) samples[i] = (Math.random() * 2 - 1) * (1 - i / samples.length);
      const source = audio.createBufferSource(), filter = audio.createBiquadFilter(), envelope = audio.createGain();
      source.buffer = buffer; filter.type = "highpass"; filter.frequency.value = cutoff;
      const start = origin + delay;
      envelope.gain.value = volume;
      source.connect(filter); filter.connect(envelope); envelope.connect(audio.destination); source.start(start);
    };
    if (kind === "champion") for (let i = 0; i < 8; i++) noise(0.25, 0.04, 0.9 + i * 0.07, 1200);
    if (kind === "stamp") noise(0.06, 0.06, 0, 1500);
  } catch {}
}
function logo(code, size = "") {
  return event.teams[code]
    ? `<img class="logo ${size}" src="${escape(event.teams[code].logo)}" alt="${escape(event.teams[code].name)}" loading="lazy">`
    : '<span class="logo" aria-hidden="true">?</span>';
}
function channel() {
  return channels.find((c) => c.id === selected) || channels[0];
}
function avatar(c) {
  return `<span class="avatar" aria-hidden="true" style="--accent:${c.color}"><img src="${escape(assets.models[c.id].avatar)}" alt=""></span>`;
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
  if (id === "mine")
    return validRanking(customRanking, finalistsList())
      ? rankingProbability(customRanking, a, b)
      : null;
  return id === "baseline"
    ? baselineProbability(event, a, b)
    : forecasts[id]
      ? mapProbability(forecasts[id], a, b)
      : null;
}
function finalistsList() {
  return event.predecessors.flatMap((match) => match.teams);
}
function personalProbability(a, b) {
  return pmap(a, b, personalReference);
}
function matchup(id = selected) {
  const { upperWinner, upperLoser, lowerWinner } = opponentPairs();
  return {
    lf: [upperLoser, lowerWinner],
    upperWinner,
    lp: pmap(upperLoser, lowerWinner, id),
  };
}
function simulateFinals(id = selected) {
  const match = matchup(id);
  if (match.lp == null) return [];
  const lower = simulateSeries(...match.lf, match.lp, simSeed);
  return [
    lower,
    simulateSeries(
      match.upperWinner,
      lower.winner,
      pmap(match.upperWinner, lower.winner, id),
      simSeed + 1,
    ),
  ];
}
function fictionalReview(index, id = selected) {
  const { upperWinner, lowerWinner } = opponentPairs();
  return fictionFor(fiction[id], { upperWinner, lowerWinner }, index, simulateFinals(id)[index], event.source_sha256);
}
function fictionNotice() {
  return '<div class="notice fiction-notice"><strong>AI 虚构模拟</strong> · 以下 BP、回合比分、剧情、MVP 和评分均为模型创作，非真实比赛、非选手能力评估。</div>';
}
function fictionRatings(review) {
  return `<div class="table-wrap"><table class="fiction-ratings"><thead><tr><th>选手</th><th>战队</th><th>本场虚构评分 / 10</th><th>虚构表现评语</th></tr></thead><tbody>${Object.entries(review.players).sort((a, b) => b[1].rating - a[1].rating).map(([id, value]) => { const [team, name] = id.split(':'); return `<tr data-fiction-player="${escape(id)}"><th>${escape(name)}</th><td>${escape(team)}</td><td class="mono">${value.rating.toFixed(1)}</td><td>${escape(value.comment)}</td></tr>`; }).join("")}</tbody></table></div>`;
}
function fictionDetails(review, index) {
  if (!review) return '<section class="card section-heading"><h2>虚构剧情与评分待生成</h2><p class="muted">该频道尚无与当前情景匹配的真实模型创作，不代填内容。</p></section>';
  return `<section class="card section-heading fiction-details">${fictionNotice()}<h2>${escape(review.headline)}</h2><p>${escape(review.summary)}</p><h3>虚构地图 BP</h3><p class="muted">这是较早的虚构创作版图序，未按本轮官方 veto 步骤与选边重新生成；请从首页“地图 BP”查看新结构化预测，不能把两版串成同一次比赛。</p><div class="fiction-bp">${review.bp.bans.map(map => `<div class="bp-map banned"><small>模拟禁用</small><b>${escape(map)}</b></div>`).join("")}${review.bp.order.map((map, i) => `<div class="bp-map ${i >= review.input.series.maps.length ? "unplayed" : ""}"><small>第 ${i + 1} 图${i >= review.input.series.maps.length ? " · 未进行" : ""}</small><b>${escape(map)}</b></div>`).join("")}</div><p>${escape(review.bp.reason)}</p><h3>本场虚构选手评分</h3><p class="muted">0–10 分，仅描述这段虚构剧情中的系列赛表现；不是 ACS、KAST 或真实能力排名。</p>${fictionRatings(review)}<details class="fiction-sources"><summary>人物索引、地图和生成来源</summary><p>昵称索引不等于比赛当天官方首发。${review.input.series.teams.map(team => `<a class="source-link" href="${escape(fictionContext.teams[team].source_url)}" target="_blank" rel="noreferrer">${team} · ${fictionContext.teams[team].source_kind === "official_team" ? "俱乐部官网" : "赛事数据库补充"} ↗</a>`).join("　")}</p><p><a class="source-link" href="${escape(fictionContext.maps.source_url)}" target="_blank" rel="noreferrer">Riot 游戏地图目录 ↗</a> · <a class="source-link" href="data/${escape(fictionManifest[selected])}" target="_blank">${escape(channel().name)} 实际创作 JSON ↗</a></p></details></section>`;
}
function renderFictionPlayers(content) {
  const rows = aggregateFictionPlayers([fictionalReview(0), fictionalReview(1)]);
  content.innerHTML = fictionNotice() + scenarioForm() + `<section class="card fiction-player-board"><div class="section-head"><div><h2>虚构选手榜 · ${escape(channel().name)}</h2><p class="muted">取当前情景最后两场的系列赛评分均值；只统计实际写入剧情的出场。0–10 分，不代表真实能力。</p></div><span class="pill">${rows.length} 名剧情选手</span></div><div class="form-row"><label>搜索选手<input id="fiction-player-search" type="search" placeholder="输入昵称" /></label><label>战队<select id="fiction-player-team"><option value="">全部战队</option>${[...new Set(rows.map(r => r.team))].map(team => `<option>${escape(team)}</option>`).join("")}</select></label><label>排序<select id="fiction-player-sort"><option value="rating">虚构均分</option><option value="appearances">模拟出场数</option><option value="name">选手昵称</option></select></label><label><input type="checkbox" id="fiction-player-both" />只看两场均出场</label></div><div id="fiction-player-results"></div><p class="muted">名单依据俱乐部公开阵容索引；LOUD 使用赛事数据库补充。真实比赛数据与本榜分开。</p></section>`;
  const update = () => {
    const query = $("#fiction-player-search").value.trim().toLowerCase(), team = $("#fiction-player-team").value, sort = $("#fiction-player-sort").value;
    const filtered = rows.filter(row => row.name.toLowerCase().includes(query) && (!team || row.team === team) && (!$("#fiction-player-both").checked || row.appearances.length === 2));
    filtered.sort((a, b) => sort === "name" ? a.name.localeCompare(b.name) : sort === "appearances" ? b.appearances.length - a.appearances.length || b.rating - a.rating : b.rating - a.rating);
    $("#fiction-player-results").innerHTML = filtered.length ? `<div class="table-wrap"><table><thead><tr><th>排名</th><th>选手</th><th>战队</th><th>虚构均分 / 10</th><th>模拟出场</th><th>对应剧情</th></tr></thead><tbody>${filtered.map((row, i) => `<tr data-fiction-player="${escape(row.id)}"><td>${i + 1}</td><th>${escape(row.name)}</th><td>${row.team}</td><td class="mono">${row.rating.toFixed(1)}</td><td>${row.appearances.length}</td><td>${row.appearances.map(a => `<a class="source-link" href="${reviewLink(a.index)}">${a.index === 0 ? "败者组决赛" : "总决赛"} · ${a.rating.toFixed(1)}</a>`).join("<br>")}</td></tr>`).join("")}</tbody></table></div>` : '<div class="empty">没有匹配的虚构选手评分；该频道未生成时保持空榜。</div>';
  };
  for (const id of ["fiction-player-search", "fiction-player-team", "fiction-player-sort", "fiction-player-both"]) $("#" + id).addEventListener("input", update);
  update();bindScenario();
}
function pageHead(title, description) {
  const split = {"数据对比": ["数据", "对比"], "战队": ["参赛", "战队"], "我来预测": ["我来", "预测"], "谁最准": ["谁最", "准"], "AI 赛制介绍": ["VCT · ", "AI 赛制介绍"]}[title] || ["", title];
  return `<div class="wrap page-head"><div><h1>${escape(split[0])}<span class="page-title-cn">${escape(split[1])}</span></h1><p>${description}</p></div><div class="kicker">CHAMPIONS SHANGHAI · FINALS</div></div>`;
}
function officialBanner() {
  const upper = officialCurrent?.predecessors[0];
  if (!upper?.winner) return "";
  const loser = upper.teams.find(t => t !== upper.winner), alternate = scenario.upperWinner !== upper.winner;
  return `<div class="official-current ${alternate ? "counterfactual" : ""}"><span><b>官方已确认 · 10/16</b> ${upper.teams.join(" ")} ${upper.score.join(" : ")}；${upper.winner} 进入总决赛，${loser} 进入败者组决赛。另一支晋级队待核实。${alternate ? `<strong> 当前正在查看“${scenario.upperWinner} 晋级”的反事实情景。</strong>` : ""}</span><a href="${officialCurrent.source_url}" target="_blank" rel="noreferrer">官方记录 ↗</a></div>`;
}
function note() {
  return `<div class="notice">预测使用 ${escape(event.fetched_at.slice(0,10))} 冻结资料；最新官方状态另列。下方是晋级条件下的模型推演，情景选择不是官方赛果。${officialCurrent?.predecessors[0].winner && scenario.upperWinner !== officialCurrent.predecessors[0].winner ? " 当前为反事实情景。" : ""}</div>`;
}
function scenarioForm() {
  const upper = event.predecessors[0],
    lower = event.predecessors[1];
  return `<section class="card" aria-label="晋级情景"><h3>最后两场的晋级条件</h3><p class="muted">17 日：胜者组决赛败者 vs 败者组半决赛胜者。18 日：胜者组决赛胜者 vs 17 日胜者。</p><div class="form-row"><label>胜者组决赛胜者（16 日，不在预测范围）<select id="upper-winner" ${upper.winner ? "disabled" : ""}>${upper.teams.map((c) => `<option value="${c}" ${c === (upper.winner || scenario.upperWinner) ? "selected" : ""}>${c}${officialCurrent?.predecessors[0].winner ? c === officialCurrent.predecessors[0].winner ? " · 官方已确认" : " · 反事实分支" : ""}</option>`).join("")}</select></label><label>败者组半决赛胜者（16 日，不在预测范围）<select id="lower-winner" ${lower.winner ? "disabled" : ""}>${lower.teams.map((c) => `<option ${c === (lower.winner || scenario.lowerWinner) ? "selected" : ""}>${c}</option>`).join("")}</select></label></div><small class="muted">默认采用已确认的胜者；仍可回看历史反事实分支。未确认的另一场保持条件选择。官方最新状态见 <a class="source-link" href="https://valorantesports.com/en-US/" target="_blank" rel="noreferrer">赛事官网 ↗</a></small></section>`;
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
  return `<div id="home-model-selector" class="model-deck channels portraits" aria-label="选择模型，查看其沙盘与赛事预测">${channels.map(ch => {
    const champion = simulateFinals(ch.id)[1]?.winner;
    return `<a class="home-model channel portrait forecast-card ${selected === ch.id ? "on" : ""}" href="#/?ai=${ch.id}" role="button" aria-pressed="${selected === ch.id}" data-channel="${ch.id}" data-tactical-model="${ch.id}" style="--accent:${ch.color}"><img class="model-portrait" src="${escape(assets.models[ch.id].portrait)}" alt="" loading="eager"><div class="model-overview"><h2>${escape(ch.name)}</h2><small class="model-forecast-status">${available(ch.id) ? "赛事预测已生成" : "赛事预测待生成"}</small><div class="model-champion"><small>本次模拟冠军</small><b class="champ">${available(ch.id) ? logo(champion) + " " + champion : "待预测"}</b></div><small class="model-tactical-status" data-tactical-status>${tab === "sandbox" ? "沙盘方案读取中" : "沙盘方案 · 见战术页"}</small></div></a>`;
  }).join("")}</div>`;
}
function selectChannel(id) {
  const focused = Boolean(document.querySelector("#tactical-replay.tactical-focused"));
  if (!channels.some((c) => c.id === id)) return;
  selected = id;
  if (pageRoute === "/") history.replaceState(null, "", "#/?" + new URLSearchParams({ ai: selected, tab }));
  store.set("channel", selected);
  current = 0;
  buildSimulation();
  render();
  if (focused) {
    const root = document.querySelector("#tactical-replay");
    root?.classList.add("tactical-focused");
    const button = root?.querySelector("#tactical-focus");
    if (button) { button.textContent = "退出专注"; button.setAttribute("aria-pressed", "true"); }
  }
}
function bindModels() {
  document
    .querySelectorAll("[data-channel]")
    .forEach(
      (button) =>
        (button.onclick = event => {
          if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
          event.preventDefault();
          selectChannel(button.dataset.channel);
        }),
    );
  if ($("#mobile-model"))
    $("#mobile-model").onchange = (e) => selectChannel(e.target.value);
}
function replaySignature() {
  return JSON.stringify([
    event.matches.map((m) => m.id),
    opponentPairs(),
    simSeed,
  ]);
}
function saveReplay() {
  store.set("replay-" + selected, {
    signature: replaySignature(),
    index: current,
  });
}
function buildSimulation(restore = true) {
  simFrames = [];
  simSeries = [];
  simSeries = simulateFinals();
  if (!simSeries.length) return;
  for (const [index, series] of simSeries.entries()) {
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
  const saved = restore ? store.get("replay-" + selected, null) : null;
  current =
    saved?.signature === replaySignature() && Number.isInteger(saved.index)
      ? Math.max(0, Math.min(saved.index, simFrames.length - 1))
      : 0;
}
function home() {
  const c = channel();
  main.innerHTML = `<section class="hero home-intro"><div class="wrap"><div class="hero-top"><div><p class="eyebrow">CHAMPIONS SHANGHAI 2026 · 10/17–18</p><h1>四个模型，同场推演</h1><p>选一个模型，看它如何走位、如何判断最后两场比赛。</p></div><span class="home-label">AI 假设方案与模拟 · 非真实赛况</span></div>${officialBanner()}${modelGrid()}<p class="model-deck-note">冠军来自当前晋级情景的一次模拟；战术沙盘使用独立假设场景。<a href="#/compare">比较赛事概率 →</a></p></div></section><section class="wrap home-workspace"><div class="tabs home-tabs" role="tablist" aria-label="预测频道内容">${[
    ["veto", "01 地图 BP"], ["sandbox", "02 阵容与走位"], ["live", "03 比赛推演"], ["schedule", "赛程赛果"], ["bracket", "淘汰赛"], ["players", "选手榜"], ["news", "剧情与战报"], ["analysis", "赛前评估"], ["process", "预测过程"],
  ].map(([id,name]) => `<button role="tab" aria-selected="${tab === id}" aria-controls="channel-content" data-tab="${id}" class="${tab === id ? "on" : ""}">${name}</button>`).join("")}<span class="channel-meta">${escape(c.name)}</span></div><div class="studio-section"><div id="channel-content" role="tabpanel"></div></div></section>`;
  bindModels();
  document.querySelectorAll("[data-tab]").forEach(b => b.onclick = () => { tab = b.dataset.tab; history.replaceState(null, "", "#/?" + new URLSearchParams({ ai: selected, tab })); clearTimeout(playerTimer); render(); });
  renderChannel();
}

function officialSchedule() {
  return `<div class="table-wrap"><table><thead><tr><th>比赛</th><th>北京时间</th><th>官方对阵</th><th>赛制</th><th>状态</th></tr></thead><tbody>${(officialCurrent?.matches || event.matches).map((m) => `<tr><td>${m.label}</td><td>${formatDate(m.start_utc)}</td><td>${m.teams.join(" vs ")}</td><td>BO${m.best_of}</td><td>${m.winner ? m.score.join(" : ") : "待开赛"}</td></tr>`).join("")}</tbody></table></div>`;
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
function reviewLink(index, model = selected) {
  return `#/match/${index}?${new URLSearchParams({ ai: model, upper: opponentPairs().upperWinner, lower: opponentPairs().lowerWinner })}`;
}
function pairReason(teams) {
  return (
    forecasts[selected]?.pairs.find((p) =>
      teams.every((t) => p.teams.includes(t)),
    )?.reason || "该模型尚未输出分析"
  );
}
function simulationCards(withReport = false) {
  if (!simSeries.length)
    return '<div class="card empty">该模型尚未预测，暂无模拟战报。</div>';
  return `<div class="grid simulation-cards">${simSeries
    .map((series, index) => {
      const p = seriesProbability(pmap(...series.teams));
      return `<a class="card card-link simulation-card" href="${reviewLink(index)}"><div class="section-head"><span class="pill">AI 模拟</span><span class="muted">${formatDate(event.matches[index].start_utc)}</span></div><h3>${event.matches[index].label}</h3><div class="simulation-score">${logo(series.teams[0])}<b>${series.teams[0]}</b><strong>${series.score.join(" : ")}</strong><b>${series.teams[1]}</b>${logo(series.teams[1])}</div><p>${series.winner} ${index === 0 ? "晋级总决赛" : "赢得模拟冠军"} · ${series.maps.length} 图</p>${withReport ? `<p class="muted">${escape(pairReason(series.teams))}</p>` : ""}<small class="muted">${series.teams[0]} 赛前 BO5 概率 ${pct(p)} · 查看逐图回看 →</small></a>`;
    })
    .join("")}</div>`;
}
function reviewPage(index) {
  const series = simSeries[index];
  main.innerHTML =
    pageHead(
      `${event.matches[index].label} · 模拟回看`,
      `${channel().name} 的世界 · ${formatDate(event.matches[index].start_utc)}`,
    ) +
    `<div class="wrap section"><a class="source-link" href="#/?ai=${selected}&tab=schedule">← 返回该频道赛程</a>${note()}<div id="review-content"></div></div>`;
  if (!series) {
    $("#review-content").innerHTML =
      '<section class="card empty"><h2>该模型等待预测</h2><p class="muted">暂无实际模型输出，不生成回看比分。</p></section>';
    return;
  }
  const p = pmap(...series.teams);
  const scores = [[0, 0], ...series.maps.map((m) => m.score)];
  const chances = scores.map((score) => remainingSeriesProbability(score, p));
  const points = chances.map((chance, i) => [
    55 + (i * 790) / series.maps.length,
    210 - chance * 160,
  ]);
  const scoreTable = series.maps
    .map(
      (map, i) =>
        `<tr><th>第 ${i + 1} 图</th><td>${map.winner}</td><td class="mono">${map.score.join(" : ")}</td><td>${pct(chances[i + 1])}</td></tr>`,
    )
    .join("");
  $("#review-content").innerHTML =
    `<section class="card review-head"><span class="pill">AI 模拟 · 非真实赛果</span><div class="versus"><div class="vs-team">${logo(series.teams[0])}<b>${series.teams[0]}</b></div><div class="score">${series.score.join(" : ")}<small>BO5 · ${series.maps.length} 图</small></div><div class="vs-team">${logo(series.teams[1])}<b>${series.teams[1]}</b></div></div><h2>${series.winner} ${index === 0 ? "晋级总决赛" : "夺得模拟冠军"}</h2><p class="muted">当前晋级情景与固定随机种子下的一次推演。它与直播播放器使用同一组逐图结果。</p><div class="odds-bar" aria-label="赛前系列赛概率"><span style="width:${100 * seriesProbability(p)}%">${series.teams[0]} ${pct(seriesProbability(p))}</span><span>${series.teams[1]} ${pct(1 - seriesProbability(p))}</span></div></section><section class="card section-heading"><h2>赛前判断 · ${escape(channel().name)}</h2><p>${escape(pairReason(series.teams))}</p><p class="muted">单图概率 ${pct(p)}；按各图独立且同概率换算，${series.teams[0]} 赢得 BO5 的概率为 ${pct(seriesProbability(p))}。</p></section><section class="card section-heading"><h2>逐图回看</h2><div class="map-tabs" role="group" aria-label="选择模拟地图">${series.maps.map((map, i) => `<button data-review-map="${i}" aria-pressed="${i === 0}" class="${i === 0 ? "on" : ""}">第 ${i + 1} 图 · ${map.winner} 胜</button>`).join("")}</div><div id="review-map" aria-live="polite"></div><div class="table-wrap"><table><thead><tr><th>地图</th><th>模拟胜者</th><th>累计比分</th><th>${series.teams[0]} 此时系列赛概率</th></tr></thead><tbody>${scoreTable}</tbody></table></div></section><section class="card section-heading"><h2>系列赛胜率走势</h2><p class="muted">每图结束后按剩余图数计算的条件概率，沿用模型的固定单图概率。不是实测局内走势。</p><div class="chart-scroll"><svg viewBox="0 0 900 255" class="series-chart" role="img" aria-label="${series.teams[0]} 系列赛条件胜率走势">${[0, 0.25, 0.5, 0.75, 1].map((v) => `<line x1="55" x2="845" y1="${210 - v * 160}" y2="${210 - v * 160}" class="chart-grid"/><text x="42" y="${215 - v * 160}" text-anchor="end">${v * 100}%</text>`).join("")}<polyline points="${points.map((p) => p.join(",")).join(" ")}"/>${points.map(([x, y], i) => `<circle cx="${x}" cy="${y}" r="5"/><text x="${x}" y="240" text-anchor="middle">${i === 0 ? "赛前" : `第 ${i} 图`}</text><text x="${x}" y="${y - 12}" text-anchor="middle" class="chart-value">${pct(chances[i])}</text>`).join("")}</svg></div></section>${fictionDetails(fictionalReview(index), index)}<div class="form-row section-heading"><a class="btn" href="${reviewLink(1 - index)}">${index === 0 ? "下一场 · 总决赛" : "上一场 · 败者组决赛"} →</a><a class="btn" href="#/?ai=${selected}">返回直播</a><button id="share-review">复制回看链接</button></div>`;
  const showMap = (i) => {
    const map = series.maps[i], review = fictionalReview(index), story = review?.maps[String(i)];
    $("#review-map").innerHTML =
      `<h3>第 ${i + 1} 图 · ${map.winner} 获胜</h3><p class="muted">累计比分 ${map.score.join(" : ")}。${Math.max(...map.score) === 3 ? `${map.winner} 已赢下系列赛。` : `进入下一图，${series.teams[0]} 赢得系列赛的条件概率为 ${pct(chances[i + 1])}。`}</p>${story ? `${fictionNotice()}<div class="fiction-map-story"><h3>${escape(review.bp.order[i])} · 虚构回合比分 ${map.winner === series.teams[0] ? `13 : ${story.losing_rounds}` : `${story.losing_rounds} : 13`}</h3><p>${escape(story.story)}</p><p class="muted">本图虚构 MVP · ${escape(story.mvp.split(":")[1])}（${escape(map.winner)}）</p></div>` : ""}<a class="source-link" href="#/?ai=${selected}">在直播中回放 →</a>`;
    document.querySelectorAll("[data-review-map]").forEach((b) => {
      const on = Number(b.dataset.reviewMap) === i;
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", String(on));
    });
  };
  document
    .querySelectorAll("[data-review-map]")
    .forEach((b) => (b.onclick = () => showMap(Number(b.dataset.reviewMap))));
  showMap(0);
  $("#share-review").onclick = async () => {
    try {
      await navigator.clipboard.writeText(location.href);
      notify("已复制当前模型的回看链接");
    } catch {
      notify("自动复制不可用，请复制浏览器地址栏中的回看链接");
    }
  };
}
function renderChannel() {
  const content = $("#channel-content");
  if (!content) return;
  const m = matchup();
  if (tab === "veto") {
    content.innerHTML = scenarioForm() + vetoMarkup();
    bindScenario();
    mountVeto({ model: selected, scenario, onSandbox: () => document.querySelector('[data-tab="sandbox"]').click() });
    return;
  }
  if (tab === "sandbox") {
    content.innerHTML = tacticalMarkup();
    mountTactical({ model: selected, onModelChange: selectChannel });
    return;
  }
  if (tab === "schedule") {
    content.innerHTML =
      note() +
      officialSchedule() +
      `<h2 class="section-heading">${escape(channel().name)} 的模拟赛程</h2>` +
      simulationCards() +
      `<div class="notice blue">以上两场模拟与官方赛程分别展示。点击模拟比赛查看逐图回看。</div>`;
    return;
  }
  if (tab === "bracket") {
    content.innerHTML =
      note() +
      scenarioForm() +
      `<div class="bracket"><div class="pick-match"><h3>17 日 · 败者组决赛</h3>${m.lf.map((t) => `<div class="pick-team">${logo(t)}<b>${t}</b></div>`).join("")}</div><div class="bracket-arrow">→</div><div class="pick-match"><h3>18 日 · 总决赛 · 模型推演</h3>${(simSeries[1]?.teams || [m.upperWinner, null]).map((t) => `<div class="pick-team">${logo(t)}<b>${t || "待预测"}</b></div>`).join("")}</div><div class="bracket-arrow">→</div><div class="result-card card"><small>该频道模拟冠军</small><h2>${simSeries[1]?.winner || "待预测"}</h2></div></div>`;
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
  if (tab === "players") {
    renderFictionPlayers(content);
    return;
  }
  if (tab === "news") {
    content.innerHTML =
      `<h2>最后两场 · 模拟战报</h2><p class="muted">来自当前频道逐图推演的结果摘要，非真实新闻。赛前理由来自该模型实际输出。</p>` +
      simulationCards(true) + fictionNotice() + `<div class="grid two fiction-news">${[0, 1].map(index => { const review = fictionalReview(index); return review ? `<article class="card"><span class="pill">AI 虚构剧情 · ${event.matches[index].label}</span><h3>${escape(review.headline)}</h3><p>${escape(review.summary)}</p><a class="btn" href="${reviewLink(index)}">阅读逐图虚构剧情 →</a></article>` : '<article class="card empty">该频道虚构剧情待生成</article>'; }).join("")}</div>`;
    return;
  }
  if (tab === "process") {
    content.innerHTML = `<div class="card article"><h2>预测过程</h2><ol><li>从 Riot 官网赛事页提取本届 ${event.history.length} 场已完成系列赛。</li><li>只根据 17、18 日两场的晋级关系建立条件对阵。</li><li>${available(selected) ? escape(channel().name) + " 独立读取官方战绩后，给出六组可能对阵的单图主观概率。" : "该频道尚未运行，不展示代填预测。"}</li><li>把每张地图的独立获胜概率换算为先赢三图的 BO5 系列赛分布。</li><li>播放器按固定随机种子实际推演比赛；一次模拟不代表最可能赛果。</li></ol><p class="muted">${escape(forecasts[selected]?.calibration || "该模型尚未运行")}</p>${available(selected) ? `<a class="btn" href="data/${escape(modelManifest[selected])}" target="_blank">查看 ${escape(channel().name)} 原始预测 JSON</a>` : ""}</div>`;
    return;
  }
  content.innerHTML =
    note() +
    `<div class="studio" style="--mc:${channel().color}" tabindex="0" role="region" aria-label="AI 模拟回放播放器"><div><div class="stage-box"><div class="stage-top"><span class="pill">● AI 模拟</span>${avatar(channel())}<span>${escape(channel().name)} 的世界</span><span class="stage-date" id="stage-date"></span></div><div id="stage"></div></div><div class="progress"><i id="progress" style="width:0"></i></div><div class="controls"><button id="prev" aria-label="上一步">◀</button><button id="play" class="play" title="${playing ? "暂停" : "播放"} (空格)">${playing ? "Ⅱ 暂停" : "▶ 播放"}</button><button id="next" aria-label="下一步">▶|</button><button id="next-match">下一场</button><button id="next-day">下一天</button><button id="mute">${muted ? "取消静音" : "静音"}</button><span class="spacer"></span>${[1, 2, 4, 8].map((n) => `<button data-speed="${n}" class="${speed === n ? "on" : ""}">${n}x</button>`).join("")}</div><p class="keyboard-tip">播放器获得焦点后：空格播放/暂停，左右跳步，上下调速，M 静音。</p><div class="date-buttons"><button data-day="0">10/17</button><button data-day="1">10/18</button><button id="replay-start">从头播放</button><a id="review-current" class="btn" href="${reviewLink(0)}">查看本场回看 →</a></div></div><aside class="studio-side"><div class="schedule"><h3>最后两场 · 模拟赛程</h3>${event.matches.map((match, i) => `<button class="schedule-row" data-row="${i}" aria-label="跳到${match.label}"><b>${match.label}<small class="muted" style="display:block;margin-top:8px">${formatDate(match.start_utc)}</small></b><span>BO5</span></button>`).join("")}<div style="padding:12px"><span class="pill official">官方对阵待定</span><p class="muted" style="font-size:12px;margin:12px 0">胜者组败者 → 败者组决赛<br>败者组胜者 → 总决赛</p></div></div><section class="feed"><h3>赛事动态</h3><div class="feed-model">${avatar(channel())}<span>${escape(channel().name)} 的世界</span></div><div id="feed-events" aria-live="polite"></div></section></aside></div>`;
  bindPlayer();
  updatePlayer();
}
function updatePlayer() {
  if (!$("#stage")) return;
  if (!simFrames.length) {
    $("#stage").innerHTML =
      `<div class="empty"><div class="symbol">◌</div><h2>该模型等待预测</h2><p class="muted">没有真实模型输出，暂不生成模拟比分。</p></div>`;
    $("#stage-date").textContent = "10 月 17 / 18 日";
    $("#feed-events").textContent = "该模型等待预测";
    for (const id of ["play", "prev", "next", "next-match", "next-day"])
      $("#" + id).disabled = true;
    return;
  }
  const frame = simFrames[current];
  saveReplay();
  $("#feed-events").innerHTML = simFrames
    .slice(Math.max(0, current - 4), current + 1)
    .reverse()
    .map(
      (item, i) =>
        `<a class="feed-event ${i === 0 ? "active" : ""}" href="${reviewLink(item.index)}"><span>${item.kind === "pre" ? "◇" : item.kind === "final" ? "★" : "↗"}</span><span>${escape(item.caption)}</span></a>`,
    )
    .join("");
  $("#review-current").href = reviewLink(frame.index);
  $("#stage-date").textContent =
    frame.index === 0 ? "10 月 17 日" : "10 月 18 日";
  $("#stage").innerHTML =
    `<div class="stage-scene"><div class="versus"><div class="vs-team">${logo(frame.teams[0])}<b>${frame.teams[0]}</b></div><div class="score">${frame.score.join(" : ")}<small>BO5 · ${frame.kind === "pre" ? "赛前" : frame.kind === "final" ? "模拟赛果" : "模拟地图"}</small></div><div class="vs-team">${logo(frame.teams[1])}<b>${frame.teams[1]}</b></div></div><p class="stage-caption">${frame.caption}</p></div>`;
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
  sound(
    simFrames[current]?.kind === "final"
      ? simFrames[current].index === 1
        ? "champion"
        : "advance"
      : simFrames[current]?.kind === "map"
        ? "win"
        : "pick",
  );
  setPlayerTimer();
}
function setPlayerTimer() {
  clearTimeout(playerTimer);
  if (
    playing &&
    !document.hidden &&
    pageRoute === "/" &&
    tab === "live" &&
    simFrames.length
  )
    playerTimer = setTimeout(
      () => step(1),
      (simFrames[current]?.kind === "pre"
        ? 4000
        : simFrames[current]?.kind === "final"
          ? 6000
          : 7500) / speed,
    );
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
  document
    .querySelectorAll("[data-row]")
    .forEach((b) => (b.onclick = () => jump(Number(b.dataset.row))));
  $("#replay-start").onclick = () => {
    current = 0;
    playing = true;
    updatePlayer();
    setPlayerTimer();
  };
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
  const columns = [...channels, { id: "baseline", name: "统计基线", color: "#c9c8bd" }],
    running = columns.filter((c) => c.id === "baseline" || available(c.id)),
    teams = finalistsList(),
    { upperWinner, upperLoser, lowerWinner } = opponentPairs();
  const champion = (id) => {
    const values = finalsProbabilities(
      pmap(upperLoser, lowerWinner, id),
      pmap(upperWinner, upperLoser, id),
      pmap(upperWinner, lowerWinner, id),
    );
    return Object.fromEntries([[upperWinner, values[0]], [upperLoser, values[1]], [lowerWinner, values[2]]]);
  };
  const championships = Object.fromEntries(running.map((c) => [c.id, champion(c.id)])),
    ranks = Object.fromEntries(running.map((c) => [c.id, referenceRanking(c.id)])),
    headings = columns.map((c) => `<th><i style="background:${c.color}"></i>${escape(c.name)}</th>`).join("");
  const teamLabel = (team) => `<th scope="row"><a href="#/team/${team}">${logo(team)}${team}</a><small>${escape(event.teams[team].region?.toUpperCase())}</small></th>`;
  const cell = (value, text) => `<td class="compare-heat" style="--heat:${value}" data-value="${value}">${text}</td>`;
  const probabilities = teams.map((team) => `<tr>${teamLabel(team)}${columns.map((c) => championships[c.id] ? cell(championships[c.id][team] || 0, pct(championships[c.id][team] || 0)) : '<td class="muted">待预测</td>').join("")}</tr>`).join("");
  const rankings = teams.map((team) => {
    const actual = channels.filter((c) => available(c.id)).map((c) => ranks[c.id].indexOf(team) + 1);
    return `<tr>${teamLabel(team)}${columns.map((c) => ranks[c.id] ? cell(1 - ranks[c.id].indexOf(team) / teams.length, ranks[c.id].indexOf(team) + 1) : '<td class="muted">待预测</td>').join("")}<td>${actual.length ? (actual.reduce((a, b) => a + b, 0) / actual.length).toFixed(1) : "—"}</td><td>${actual.length > 1 ? Math.max(...actual) - Math.min(...actual) : "—"}</td></tr>`;
  }).join("");
  const disagreements = forecast.pairs.map((pair) => {
    const values = channels.filter((c) => available(c.id)).map((c) => ({ ...c, p: pmap(...pair.teams, c.id) }));
    return { teams: pair.teams, values, spread: values.length > 1 ? Math.max(...values.map((v) => v.p)) - Math.min(...values.map((v) => v.p)) : null };
  }).sort((a, b) => (b.spread || 0) - (a.spread || 0));
  const dots = disagreements.map((row, i) => {
    const y = 60 + i * 60;
    return `<text x="10" y="${y + 5}">${row.teams.join(" 对 ")}</text><text x="140" y="${y + 5}" class="chart-value">差 ${row.spread == null ? "—" : (row.spread * 100).toFixed(1)} 点</text>${row.values.map((v) => `<circle cx="${240 + v.p * 600}" cy="${y}" r="6" fill="${v.color}"><title>${escape(v.name)} · ${row.teams[0]} ${pct(v.p)}</title></circle>`).join("")}<circle cx="${240 + pmap(...row.teams, "baseline") * 600}" cy="${y}" r="8" fill="none" stroke="#c9c8bd" stroke-width="2"><title>统计基线 ${pct(pmap(...row.teams, "baseline"))}</title></circle>`;
  }).join("");
  main.innerHTML = pageHead("数据对比", "已完成的 AI 预测放在一起看：谁看好谁，谁和谁意见最不一样") +
    `<div class="wrap section compare-page">${note()}${scenarioForm()}<section class="section"><h2>夺冠概率对比</h2><p class="muted">在所选 16 日晋级情景下，枚举最后两场 BO5 的全部胜负路径，计算各队夺冠概率。颜色越亮，概率越高。不是额外预测 16 日赛果；未晋级队在该情景下为 0%。</p><div class="table-wrap"><table id="champion-comparison" class="compare-matrix"><thead><tr><th>战队</th>${headings}</tr></thead><tbody>${probabilities}</tbody></table></div><p class="muted compare-caption">仅消费已运行模型的单图概率。每图独立且同概率，精确计算而非声称运行十万次模拟。</p></section><section class="section"><h2>实力排序对比</h2><p class="muted">四队相互对阵的平均单图胜率由高到低排序，是概率推导的参考排名。平均与名次差仅统计已运行 AI；统计基线单独列出。</p><div class="table-wrap"><table id="ranking-comparison" class="compare-matrix"><thead><tr><th>战队</th>${headings}<th>AI 平均</th><th>名次差</th></tr></thead><tbody>${rankings}</tbody></table></div></section><section class="section"><h2>分歧榜 · 模型意见最不一致的对阵</h2><p class="muted">点表示左队在中立场地的单图胜率，按已运行 AI 的最高与最低概率之差排序。空心圈为统计基线。仅比较这四个已完成预测的模型。</p><div class="model-legend">${running.map((c) => `<span><i style="background:${c.color}"></i>${escape(c.name)}</span>`).join("")}</div><div class="chart-scroll"><svg id="disagreement-chart" viewBox="0 0 900 430" role="img" aria-label="六组可能对阵的模型单图胜率分歧">${[0, .2, .4, .5, .6, .8, 1].map((p) => `<line class="chart-grid" x1="${240 + p * 600}" x2="${240 + p * 600}" y1="38" y2="390"/><text x="${240 + p * 600}" y="24" text-anchor="middle">${p * 100}%</text>`).join("")}${dots}</svg></div></section><section class="section"><h2>BO5 预测概率对比</h2><p class="muted">左侧队伍赢得系列赛的概率。统计基线由本届官方地图战绩的公开公式计算。</p><div class="table-wrap"><table><thead><tr><th>可能对阵</th>${headings}</tr></thead><tbody>${forecast.pairs.map((pair) => `<tr><th>${pair.teams.join(" vs ")}</th>${columns.map((c) => running.includes(c) ? cell(seriesProbability(pmap(...pair.teams, c.id)), pct(seriesProbability(pmap(...pair.teams, c.id)))) : '<td class="muted">待预测</td>').join("")}</tr>`).join("")}</tbody></table></div></section><section class="section"><div class="section-head"><h2>当前情景 · 比分分布</h2><label>实力参考 <select id="compare-model">${running.map((c) => `<option value="${c.id}">${escape(c.name)}</option>`).join("")}</select></label></div><p class="muted">败者组决赛六个可能比分之和为 100%；来自单图独立、同概率假设。</p><div class="grid" id="distributions"></div><div id="compare-reasons"></div></section></div>`;
  bindScenario();
  const update = (id) => {
    const m = matchup(id);
    $("#distributions").innerHTML = seriesDistribution(m.lp).sort((a, b) => b.probability - a.probability).map((r) => `<div class="card"><h3>${m.lf[0]} ${r.score.join(" : ")} ${m.lf[1]}</h3><b class="gold">${pct(r.probability)}</b></div>`).join("");
    $("#compare-reasons").innerHTML = forecasts[id] ? analysisTable(forecasts[id]) : '<p class="muted">统计基线：每队实力 =（本届地图胜场 + 1）/（地图负场 + 1）；两队实力之比换算单图概率。</p>';
  };
  $("#compare-model").value = available(selected) ? selected : "codex";
  $("#compare-model").onchange = (e) => update(e.target.value);
  update($("#compare-model").value);
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
function referenceRanking(id) {
  const teams = finalistsList();
  return [...teams].sort((a, b) => {
    const strength = (team) =>
      teams
        .filter((other) => other !== team)
        .reduce((sum, other) => sum + (pmap(team, other, id) ?? 0), 0);
    return strength(b) - strength(a);
  });
}
function renderRankingEditor() {
  const editor = $("#ranking-editor");
  if (!editor || !rankingDraft) return;
  editor.innerHTML = `<section class="card rank-editor" aria-label="自定义实力排名"><div class="section-head"><div><h3>我的实力排名</h3><p class="muted">越靠前越强。拖动抓手、先选队再选位置，或使用上移/下移按钮。</p></div><div class="rank-import"><select id="ranking-import" aria-label="导入排名来源"><option value="baseline">统计基线</option>${channels
    .filter((c) => available(c.id))
    .map((c) => `<option value="${c.id}">${c.name}</option>`)
    .join(
      "",
    )}</select><button id="ranking-import-button">导入它的排名</button></div></div><p id="ranking-tip" class="muted" role="status">${rankingSelection === null ? "键盘聚焦一行后，可按上下方向键移动该战队。" : `已选中 ${rankingDraft[rankingSelection]}，点击要放到的位置。`}</p><ol class="ranking-list">${rankingDraft.map((team, i) => `<li data-ranking-row="${i}" tabindex="0" class="${rankingSelection === i ? "selected" : ""}" aria-label="第 ${i + 1} 名 ${team}"><span class="ranking-number">${i + 1}</span><span class="ranking-grip" data-ranking-grip="${i}" aria-hidden="true">⠿</span>${logo(team)}<b>${team}</b><span class="ranking-buttons"><button data-ranking-move="up" data-ranking-index="${i}" aria-label="上移 ${team}" ${i === 0 ? "disabled" : ""}>↑</button><button data-ranking-move="down" data-ranking-index="${i}" aria-label="下移 ${team}" ${i === rankingDraft.length - 1 ? "disabled" : ""}>↓</button></span></li>`).join("")}</ol><div class="actions"><button class="btn primary" id="ranking-use">使用这份排名</button><button class="btn" id="ranking-cancel">取消</button></div><small class="muted">名次差换算沿用参考站的单图公式：1 / (1 + exp(−名次差 × 0.122))。它是个人实力假设，不是 AI 输出。导入模型时，按对其余三队的平均单图概率排序。</small></section>`;
  const move = (from, to, focus = false) => {
    if (to < 0 || to >= rankingDraft.length || from === to) return;
    rankingDraft = moveRanking(rankingDraft, from, to);
    rankingSelection = null;
    renderRankingEditor();
    if (focus) editor.querySelector(`[data-ranking-row="${to}"]`).focus();
  };
  editor.querySelectorAll("[data-ranking-move]").forEach(
    (button) =>
      (button.onclick = (e) => {
        e.stopPropagation();
        const i = Number(button.dataset.rankingIndex);
        move(i, i + (button.dataset.rankingMove === "up" ? -1 : 1), true);
      }),
  );
  editor.querySelectorAll("[data-ranking-row]").forEach((row) => {
    row.onclick = (e) => {
      if (e.target.closest("button,.ranking-grip")) return;
      const i = Number(row.dataset.rankingRow);
      if (rankingSelection === null) {
        rankingSelection = i;
        renderRankingEditor();
      } else if (rankingSelection === i) {
        rankingSelection = null;
        renderRankingEditor();
      } else move(rankingSelection, i);
    };
    row.onkeydown = (e) => {
      if (e.target !== row || !["ArrowUp", "ArrowDown"].includes(e.key)) return;
      e.preventDefault();
      const i = Number(row.dataset.rankingRow);
      move(i, i + (e.key === "ArrowUp" ? -1 : 1), true);
    };
  });
  editor.querySelectorAll("[data-ranking-grip]").forEach((handle) => {
    let from = null,
      destination = null;
    handle.onpointerdown = (e) => {
      e.preventDefault();
      from = Number(handle.dataset.rankingGrip);
      destination = from;
      handle.setPointerCapture(e.pointerId);
    };
    handle.onpointermove = (e) => {
      if (from === null) return;
      const row = document
        .elementFromPoint(e.clientX, e.clientY)
        ?.closest("[data-ranking-row]");
      if (row) destination = Number(row.dataset.rankingRow);
    };
    handle.onpointerup = (e) => {
      const start = from,
        end = destination;
      from = null;
      destination = null;
      if (handle.hasPointerCapture(e.pointerId))
        handle.releasePointerCapture(e.pointerId);
      if (start !== null && end !== null) move(start, end, true);
    };
    handle.onpointercancel = () => {
      from = null;
      destination = null;
    };
  });
  $("#ranking-import-button").onclick = () => {
    rankingDraft = referenceRanking($("#ranking-import").value);
    rankingSelection = null;
    renderRankingEditor();
  };
  $("#ranking-cancel").onclick = () => {
    rankingDraft = null;
    rankingSelection = null;
    editor.replaceChildren();
  };
  $("#ranking-use").onclick = () => {
    if (!validRanking(rankingDraft, finalistsList())) return;
    customRanking = [...rankingDraft];
    personalReference = "mine";
    rankingDraft = null;
    rankingSelection = null;
    const saved =
      store.set("ranking", customRanking) &&
      store.set("reference", personalReference);
    pickemPage();
    notify(
      saved
        ? "已保存四强实力排名，胜率参考已更新"
        : "排名本次可用，但浏览器未能保存",
    );
  };
}
function pickemPage() {
  const { upperWinner, upperLoser, lowerWinner } = opponentPairs(),
    teams = [upperLoser, lowerWinner],
    finalists = [upperWinner, draft.lfWinner];
  main.innerHTML =
    pageHead("我来预测", "只预测两场：选出败者组决赛胜者，再选出上海全球冠军") +
    `<div class="wrap section"><div class="tabs" role="tablist"><button class="on" role="tab" aria-selected="true" id="my-tab">我的预测</button><button role="tab" aria-selected="false" id="sim-tab">模拟两场</button></div>${note()}${scenarioForm()}<div class="stepper"><span class="on">1 · 败者组决赛</span><span class="${draft.lfWinner ? "on" : ""}">2 · 总决赛</span><span class="${draft.champion ? "on" : ""}">3 · 预测战报</span></div><div class="form-row"><label>战队实力参考<select id="reference-model">${channels
      .filter((c) => available(c.id))
      .map(
        (c) =>
          `<option value="${c.id}" ${personalReference === c.id ? "selected" : ""}>${c.name}</option>`,
      )
      .join(
        "",
      )}<option value="baseline" ${personalReference === "baseline" ? "selected" : ""}>统计基线</option>${validRanking(customRanking, finalistsList()) ? `<option value="mine" ${personalReference === "mine" ? "selected" : ""}>我的实力排名</option>` : ""}</select></label><button id="autofill" class="btn gold">按实力参考一键填完</button><button id="custom-ranking" class="btn">自定义实力排名</button><button id="reset" class="btn">重新预测</button></div><div id="ranking-editor"></div><div class="bracket"><div class="pick-match" id="lower-final"><h3>10 / 17 · 败者组决赛 <span>BO5</span></h3>${teams.map((t) => pickTeam(t, draft.lfWinner, "lf", personalProbability(...teams), teams[0])).join("")}${draft.lfWinner ? scoreSelect("lf", draft.lfWinner, teams, draft.lfScore) : ""}</div><div class="bracket-arrow">→</div><div class="pick-match" id="grand-final"><h3>10 / 18 · 总决赛 <span>BO5</span></h3>${finalists.map((t) => (t ? pickTeam(t, draft.champion, "gf", draft.lfWinner ? personalProbability(...finalists) : null, finalists[0]) : '<button class="pick-team" disabled>等待败者组决赛胜者</button>')).join("")}${draft.champion ? scoreSelect("gf", draft.champion, finalists, draft.gfScore) : ""}</div><div class="bracket-arrow">→</div><div class="card result-card" id="pick-result"><small>你预测的上海全球冠军</small>${draft.champion ? logo(draft.champion) + "<h2>" + draft.champion + "</h2>" : '<h2>?</h2><p class="muted">完成两场选择后生成战报</p>'}</div></div><div class="actions"><button class="btn primary" id="save-pick" ${draft.champion ? "" : "disabled"}>保存预测战报</button><button class="btn" id="poster-button" ${draft.champion ? "" : "disabled"}>生成预测海报</button><button class="btn" id="share-pick" ${draft.champion ? "" : "disabled"}>复制分享链接</button></div><p class="muted" style="font-size:12px;margin-top:14px" id="save-state">${pick ? "上次预测：" + escape(pick.champion) + " 冠军 · " + escape(formatDate(pick.created_at)) : "预测保存在当前浏览器，可随时重新选择。"}</p><section class="card" id="personal-simulation" hidden style="margin-top:20px"></section></div>`;
  bindScenario();
  $("#reference-model").onchange = (e) => {
    personalReference = e.target.value;
    store.set("reference", personalReference);
    pickemPage();
  };
  $("#custom-ranking").onclick = () => {
    rankingDraft = customRanking
      ? [...customRanking]
      : referenceRanking(
          personalReference === "mine" ? "baseline" : personalReference,
        );
    rankingSelection = null;
    renderRankingEditor();
  };
  if (rankingDraft) renderRankingEditor();
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
    const p = personalProbability(...teams);
    draft.lfWinner = p >= 0.5 ? teams[0] : teams[1];
    draft.lfScore = seriesDistribution(p)
      .filter(
        (r) => (r.score[0] === 3 ? teams[0] : teams[1]) === draft.lfWinner,
      )
      .sort((a, b) => b.probability - a.probability)[0].score;
    const fs = [upperWinner, draft.lfWinner],
      gp = personalProbability(...fs);
    draft.champion = gp >= 0.5 ? fs[0] : fs[1];
    draft.gfScore = seriesDistribution(gp)
      .filter((r) => (r.score[0] === 3 ? fs[0] : fs[1]) === draft.champion)
      .sort((a, b) => b.probability - a.probability)[0].score;
    pickemPage();
    sound("champion");
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
    const lp = personalProbability(...teams),
      lf = simulateSeries(...teams, lp, Date.now() % 4294967296),
      gf = simulateSeries(
        upperWinner,
        lf.winner,
        personalProbability(upperWinner, lf.winner),
        (Date.now() % 4294967296) + 1,
      );
    $("#personal-simulation").hidden = false;
    $("#personal-simulation").innerHTML =
      `<span class="pill">模拟赛果</span><h2 style="margin-top:15px">${gf.winner} 夺冠</h2><p>17 日 · ${lf.teams.join(" vs ")} · ${lf.score.join(" : ")}<br>18 日 · ${gf.teams.join(" vs ")} · ${gf.score.join(" : ")}</p><p class="muted">按所选实力参考的单图概率实际随机推演。本次结果尚未写入你的预测。</p>`;
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
    sound("stamp");
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
    `<div class="wrap section article"><section class="card"><h2>赛事数据</h2><p>最近获取：${escape(new Date(event.fetched_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" }))}（北京时间）。官方页面结构化数据中共提取 ${event.history.length} 场已完成系列赛，本应用只预测两场 BO5。</p><ul>${event.sources.map((s) => `<li><a href="${escape(s.url)}" target="_blank" rel="noreferrer">${escape(s.publisher)} · ${s.role === "official_schedule_results" ? "官方赛程与真实结果" : "上海冠军赛赛制说明"} ↗</a></li>`).join("")}</ul><p class="muted">${event.limitations.map(escape).join("<br>")}</p><details><summary>快照与原始数据</summary><p style="overflow-wrap:anywhere">官方响应 SHA-256：${event.source_sha256}</p><a href="data/event.json" target="_blank" class="source-link">查看赛事快照 JSON</a></details></section><section class="card" style="margin-top:20px"><h2>预测来源</h2><p>已完成频道：${channels.filter(c => forecasts[c.id]).map(c => escape(c.name)).join("、")}。各频道只使用已核实身份的独立实际输出。所有模型使用同一份冻结赛事资料。展示中所有主观概率、模拟比分都标识为预测或模拟。</p>${channels.filter(c => forecasts[c.id]).map(c => `<a class="source-link" href="data/${escape(modelManifest[c.id])}" target="_blank">查看 ${escape(c.name)} 原始预测与理由 ↗</a>`).join("　")}</section><section class="card" style="margin-top:20px"><h2>AI 虚构比赛创作</h2>${fictionNotice()}<p>${channels.filter(c => fiction[c.id]).map(c => escape(c.name)).join("、")} 分别为四种晋级情景创作最后两场的地图 BP、逐图故事与系列赛选手评分。胜者与大比分由同一个模拟引擎固定，创作不能改写它们。</p><p>选手昵称优先参考俱乐部官网；LOUD 当前名单使用赛事数据库补充。真实首发以比赛当天官方公布为准。七张地图仅组成虚构创作池，不宣称是本届官方地图池。</p><a class="source-link" href="data/fiction-context.json" target="_blank">查看人物与地图索引来源 ↗</a><p class="muted">虚构榜按当前情景两场系列赛评分的均值排序，不是 ACS、KAST、真实能力排名，也不参与预测准确率结算。</p></section><section class="card" style="margin-top:20px"><h2>视觉参考与素材</h2><p>交互与页面结构参考用户指定的 <a href="https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html" target="_blank" rel="noreferrer">S16 AI 预测大赛</a>。赛事内容改为 VALORANT，范围限定为最后两场。前端代码独立编写。</p><p>模型人像按用户要求引用自 <a href="https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html" target="_blank" rel="noreferrer">我叫张大喵的 S16 AI 预测大赛</a>，保留 GPT、DeepSeek、豆包、MiMo 的原有对应关系。战队标志来自 Riot 赛事官网。图像权利归相应权利人，模型形象不代表提供商背书或合作。</p></section><section class="card" style="margin-top:20px"><h2>字体授权</h2><p>正文与中文标题使用设备系统字体，英文标题与数字按需使用 Anton、JetBrains Mono。历史 OPPO Sans、MiSans 素材和许可保留，但页面不加载这两份大字体；所有字体原文件未修改。</p><ul><li><a class="source-link" href="assets/fonts/OPPO-Sans-LICENSE.txt" target="_blank">OPPO Sans 许可</a></li><li><a class="source-link" href="assets/fonts/MiSans-LICENSE.pdf" target="_blank">MiSans 许可 · Xiaomi Inc.</a></li><li><a class="source-link" href="assets/fonts/anton-OFL.txt" target="_blank">Anton · SIL OFL 1.1</a></li><li><a class="source-link" href="assets/fonts/jetbrainsmono-OFL.txt" target="_blank">JetBrains Mono · SIL OFL 1.1</a></li></ul></section><section class="card" style="margin-top:20px"><h2>本地保存与分享</h2><p>个人预测、自定义实力排名、频道、各频道回放进度、静音和晋级情景保存在当前浏览器。分享链接只包含你选择的晋级情景、两场比分和生成时间。数据不会上传。</p></section></div>`;
}
function route() {
  clearTimeout(playerTimer);
  playing = false;
  const [path, query = ""] = (location.hash.slice(1) || "/").split("?");
  pageRoute = path;
  if (path === "/") playing = true;
  const params = new URLSearchParams(query);
  if (
    params.has("tab") &&
    [
      "veto",
      "sandbox",
      "live",
      "schedule",
      "bracket",
      "players",
      "news",
      "analysis",
      "process",
    ].includes(params.get("tab"))
  )
    tab = params.get("tab");
  else if (path === "/") tab = "veto";
  if (params.get("ai") && channels.some((c) => c.id === params.get("ai")))
    selected = params.get("ai");
  if (
    path.startsWith("/match/") &&
    params.has("upper") &&
    params.has("lower")
  ) {
    if (
      event.predecessors[0].teams.includes(params.get("upper")) &&
      event.predecessors[1].teams.includes(params.get("lower"))
    )
      scenario = {
        upperWinner: params.get("upper"),
        lowerWinner: params.get("lower"),
      };
    else notify("回看链接中的晋级情景无效，使用当前情景");
  }
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
  stopTactical();
  document.querySelectorAll(".mainnav a").forEach((a) => {
    const on =
      a.getAttribute("href") ===
      "#" +
        (pageRoute.startsWith("/team/")
          ? "/teams"
          : pageRoute.startsWith("/match/")
            ? "/"
            : pageRoute);
    a.classList.toggle("on", on);
    if (on) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  if (pageRoute === "/") home();
  else if (/^\/match\/[01]$/.test(pageRoute))
    reviewPage(Number(pageRoute.split("/")[2]));
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
  renderTicker();
}
function renderTicker() {
  const ticker = $("#simulation-ticker");
  ticker.className = `ticker${tickerOpen ? tickerPaused ? " paused" : "" : " ticker-closed"}`;
  if (!tickerOpen) {
    ticker.innerHTML = '<button class="ticker-label">展开 AI 模拟速报（含后续剧情）</button>';
    ticker.querySelector("button").onclick = () => { tickerOpen = true; renderTicker(); };
    return;
  }
  const reports = channels.filter((c) => available(c.id)).flatMap((c) => simulateFinals(c.id).map((series, index) => {
    const winnerIndex = series.teams.indexOf(series.winner), loser = series.teams[1 - winnerIndex],
      chance = seriesProbability(pmap(series.winner, loser, c.id));
    return { c, series, index, loser, chance, winnerIndex };
  }));
  const row = (duplicate) => `<div class="ticker-row"${duplicate ? ' aria-hidden="true"' : ""}>${reports.map(({ c, series, index, loser, chance, winnerIndex }) => `<a class="tick" href="${reviewLink(index, c.id)}"${duplicate ? ' tabindex="-1"' : ""}><span class="pill">AI 模拟</span><span class="muted">${escape(c.name)} 的世界</span>${logo(series.winner)}<b>${series.winner}</b><span>${series.score[winnerIndex]}–${series.score[1 - winnerIndex]}</span><span>${loser}</span><span class="muted">赛前 ${pct(chance)}</span></a>`).join("")}</div>`;
  ticker.innerHTML = `<button class="ticker-label" aria-pressed="${tickerPaused}">${tickerPaused ? "滚动速报" : "暂停速报"}</button><div class="ticker-track"><div class="ticker-move">${row(false)}${tickerPaused ? "" : row(true)}</div></div><button class="ticker-close" aria-label="收起模拟速报">×</button>`;
  ticker.querySelector(".ticker-label").onclick = () => { tickerPaused = !tickerPaused; renderTicker(); };
  ticker.querySelector(".ticker-close").onclick = () => { tickerOpen = false; renderTicker(); };
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
  ctx.fillStyle = "#0b0d0b";
  ctx.fillRect(0, 0, 800, 1000);
  ctx.fillStyle = "#c5b174";
  ctx.textAlign = "center";
  ctx.font = "bold 28px sans-serif";
  ctx.fillText("CHAMPIONS SHANGHAI 2026", 400, 120);
  ctx.fillStyle = "#f2f2f2";
  ctx.font = "bold 48px sans-serif";
  ctx.fillText("我的决赛预测", 400, 230);
  ctx.fillStyle = "#c5b174";
  ctx.font = "bold 120px sans-serif";
  ctx.fillText(draft.champion, 400, 450);
  ctx.fillStyle = "#eeeae1";
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
  ctx.fillStyle = "#a9aaa3";
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
    [event, assets, manifest, fictionManifest, fictionContext, officialCurrent] = await Promise.all(
      ["data/event.json", "data/assets.json", "data/model-forecasts.json", "data/model-fiction.json", "data/fiction-context.json", "data/official-current.json"].map(
        fetchJSON,
      ),
    );
    [forecasts, fiction] = await Promise.all([manifest, fictionManifest].map(async entries => Object.fromEntries(await Promise.all(Object.entries(entries).map(async ([id, path]) => [id, await fetchJSON("data/" + path)])))));
    modelManifest = manifest;
    forecast = forecasts.codex;
    if (!forecast) throw Error("GPT-6.1 sol 预测数据缺失");
    if (
      event.matches.length !== 2 ||
      event.matches.some((m) => m.best_of !== 5)
    )
      throw Error("赛事数据不符合两场 BO5 范围");
    scenario = store.get("scenario", {
      upperWinner: officialCurrent.predecessors[0].winner || event.predecessors[0].teams[1],
      lowerWinner: officialCurrent.predecessors[1].winner || event.predecessors[1].teams[1],
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
    if (!validRanking(customRanking, finalistsList())) customRanking = null;
    if (
      !(
        personalReference === "baseline" ||
        (personalReference === "mine" && customRanking) ||
        available(personalReference)
      )
    )
      personalReference = "codex";
    if (!channels.some(c => c.id === selected)) {
      selected = "codex";
      store.set("channel", selected);
    }
    window.addEventListener("hashchange", route);
    document.addEventListener("visibilitychange", setPlayerTimer);
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
