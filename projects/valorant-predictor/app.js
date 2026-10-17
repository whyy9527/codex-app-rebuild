import {factualEvent,settleCausal,currentFixture,verifiedCompleted,fixturePrediction} from './current-data.mjs';
import {causalMarkup, mountCausalPlayer, stopCausalPlayer} from "./causal-player.mjs";
import { v2Markup } from "./forecast-v2.mjs";
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
  ["mimo", "MiMo V2.6 Pro", "M", "#9b9d94"],
  ["doubao", "豆包", "●", "#a89758"],
].map(([id, name, icon, color]) => ({ id, name, icon, color }));
let event,
  officialCurrent,
  evidencePack,
  v2Predictions = {},
  causalAvailability = {},
  currentData,currentAgents,currentMapArt,archiveData,currentCase=0,draftScenario=null,savedPickIncompatible=false,
  v2Case = "lf",
  assets,
  forecast,
  forecasts = {},
  modelManifest = {},
  fiction = {},
  fictionManifest = {},
  fictionContext,
  selected = store.get("channel", "codex"),
  tab = "player",
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
  return currentData?.models[id]?.status==="ready";
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
    ? baselineProbability(factualEvent(event,officialCurrent), a, b)
    : forecasts[id]
      ? mapProbability(forecasts[id], a, b)
      : null;
}
function finalistsList() {
  return event.predecessors.flatMap((match) => match.teams);
}
function personalProbability(a,b){return personalReference==='mine'?rankingProbability(customRanking,a,b):personalReference==='baseline'?baselineProbability(factualEvent(event,officialCurrent),a,b):null;}
function personalFixture(){
 const live=currentFixture(event,officialCurrent);if(!draftScenario)return live;
 return {...draftScenario,upperLoser:event.predecessors[0].teams.find(t=>t!==draftScenario.upperWinner)};
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
  return `<section class="card section-heading fiction-details">${fictionNotice()}<h2>${escape(review.headline)}</h2><p>${escape(review.summary)}</p><h3>虚构地图 BP</h3><p class="muted">这是较早的虚构创作版图序，未按本轮官方 veto 步骤与选边重新生成；请从首页“地图 BP”查看新结构化预测，不能把两版串成同一次比赛。</p><div class="fiction-bp">${review.bp.bans.map(map => `<div class="bp-map banned"><small>模拟禁用</small><b>${escape(map)}</b></div>`).join("")}${review.bp.order.map((map, i) => `<div class="bp-map ${i >= review.input.series.maps.length ? "unplayed" : ""}"><small>第 ${i + 1} 图${i >= review.input.series.maps.length ? " · 未进行" : ""}</small><b>${escape(map)}</b></div>`).join("")}</div><p>${escape(review.bp.reason)}</p><h3>本场虚构选手评分</h3><p class="muted">0–10 分，仅描述这段虚构剧情中的系列赛表现；不是 ACS、KAST 或真实能力排名。</p>${fictionRatings(review)}<details class="fiction-sources"><summary>人物索引、地图和生成来源</summary><p>昵称索引不等于比赛当天官方首发。${review.input.series.teams.map(team => `<a class="source-link" href="${escape(fictionContext.teams[team].source_url)}" target="_blank" rel="noreferrer">${team} · ${fictionContext.teams[team].source_kind === "official_team" ? "俱乐部官网" : "赛事数据库补充"} ↗</a>`).join("　")}</p><p><a class="source-link" href="${escape(fictionContext.maps.source_url)}" target="_blank" rel="noreferrer">Riot 游戏地图目录 ↗</a></p></details></section>`;
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
function counterfactualScenario() {
  return officialCurrent.predecessors.some((m,i) => m.winner && m.winner !== scenario[i === 0 ? "upperWinner" : "lowerWinner"]);
}
function officialBanner() {
  const upper = officialCurrent?.predecessors[0], lower = officialCurrent?.predecessors[1];
  if (!upper?.winner) return "";
  const loser = upper.teams.find(t => t !== upper.winner), alternate = counterfactualScenario();
  return `<div class="official-current ${alternate ? "counterfactual" : ""}"><span><b>赛前已确认 · 10/16</b> ${upper.teams.join(" ")} ${upper.score.join(" : ")}；${upper.winner} 进入总决赛，${loser} 进入败者组决赛。${lower?.winner ? `${lower.teams.join(" ")} ${lower.score.join(" : ")}；${lower.winner} 进入败者组决赛。` : "另一支晋级队待核实。"}${alternate ? "<strong> 当前为与已知赛果不同的历史反事实情景。</strong>" : ""}</span><a href="${officialCurrent.source_url}" target="_blank" rel="noreferrer">赛事记录 ↗</a></div>`;
}
function note() {
  return `<div class="notice">旧输入版预测 · 尚未使用新证据包 v2。预测使用 ${escape(event.fetched_at.slice(0,10))} 冻结资料；最新官方状态另列。下方是晋级条件下的模型推演，情景选择不是官方赛果。${counterfactualScenario() ? " 当前为反事实情景。" : ""}</div>`;
}
function scenarioForm() {
  const upper = event.predecessors[0],
    lower = event.predecessors[1];
  return `<section class="card" aria-label="晋级情景"><h3>最后两场的晋级条件</h3><p class="muted">17 日：胜者组决赛败者 vs 败者组半决赛胜者。18 日：胜者组决赛胜者 vs 17 日胜者。</p><div class="form-row"><label>胜者组决赛胜者（16 日，不在预测范围）<select id="upper-winner" ${upper.winner ? "disabled" : ""}>${upper.teams.map((c) => `<option value="${c}" ${c === (upper.winner || scenario.upperWinner) ? "selected" : ""}>${c}${officialCurrent?.predecessors[0].winner ? c === officialCurrent.predecessors[0].winner ? " · 官方已确认" : " · 反事实分支" : ""}</option>`).join("")}</select></label><label>败者组半决赛胜者（16 日，不在预测范围）<select id="lower-winner" ${lower.winner ? "disabled" : ""}>${lower.teams.map((c) => `<option ${c === (lower.winner || scenario.lowerWinner) ? "selected" : ""}>${c}</option>`).join("")}</select></label></div><small class="muted">默认采用已确认的胜者；仍可回看历史反事实分支。已知结果与旧版情景推演分开显示。官方最新状态见 <a class="source-link" href="https://valorantesports.com/en-US/" target="_blank" rel="noreferrer">赛事官网 ↗</a></small></section>`;
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
function finalPrediction(id){return fixturePrediction(currentData.models[id],officialCurrent.matches[1]);}
function modelGrid() {
  return `<div id="home-model-selector" class="model-deck channels portraits" aria-label="选择模型">${channels.map(ch=>{const p=finalPrediction(ch.id),home=pageRoute==='/';return `<a class="home-model channel portrait ${selected===ch.id?'on':''}" href="#/?ai=${ch.id}" role="button" aria-pressed="${selected===ch.id}" data-channel="${ch.id}" data-tactical-model="${ch.id}"><img class="model-portrait" src="${escape(assets.models[ch.id].portrait)}" alt=""><div class="model-overview"><small>${home?'预测冠军':'原赛前情景冠军'}</small><strong class="model-champion-pick">${home?(p?escape(p.winner):'待更新'):escape(causalAvailability[ch.id]?.champion||'待更新')}</strong><h2>${escape(ch.name)}</h2><span data-tactical-status hidden></span></div></a>`;}).join('')}</div>`;
}
function selectChannel(id) {
  const focused = Boolean(document.querySelector("#tactical-replay.tactical-focused"));
  if (!channels.some((c) => c.id === id)) return;
  selected = id;
  if (["/", "/channel"].includes(pageRoute)) history.replaceState(null, "", "#" + pageRoute + "?" + new URLSearchParams({ ai: selected, tab, ...(pageRoute==="/channel"?{case:currentCase?"gf":"lf"}:{}) }));
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
function selectedCharacter(){
 const model=channel(),source=assets.models[selected],prediction=finalPrediction(selected);
 return `<figure class="selected-character" data-selected-model="${selected}" aria-label="当前模型人物 · ${escape(model.name)}"><div class="selected-character-window"><img class="selected-character-portrait" src="${escape(source.portrait)}" alt="${escape(model.name)} 人物" width="${selected==='codex'?937:600}" height="${selected==='codex'?1678:800}"></div><figcaption><strong>${escape(model.name)}</strong><span>预测冠军</span><b class="selected-champion">${prediction?escape(prediction.winner):'待更新'}</b></figcaption></figure>`;
}
function actualSources(){
 const labels=url=>url===officialCurrent.source_url?'Riot · 官方赛程':url.includes('everything-you-need-to-know')?'Riot · 冠军赛赛制说明':url.endsWith('.pdf')?'Riot · 冻结资料中的赛事规则 PDF':'VLR · '+new URL(url).pathname.split('/').at(-1).replace('valorant-champions-2026-','').replaceAll('-',' ');
 return `<details class="card actual-sources"><summary>AI 实际使用的赛前资料 · ${evidencePack.sources.length} 个来源</summary><p>四家读取同一份冻结资料，截止 ${formatDate(evidencePack.frozen_at)}（北京时间）。以下为输入资料实际引用的来源，不代表模型另行实时浏览；赛后赛果不在这份输入中。</p><ul>${evidencePack.sources.map(source=>`<li><a href="${escape(source.url)}" target="_blank" rel="noopener noreferrer">${escape(labels(source.url))} ↗</a></li>`).join('')}</ul><p><a href="https://valorant-api.com/v1/maps?language=en-US" target="_blank" rel="noopener noreferrer">模型地图区域上下文 · Valorant-API 地图目录 ↗</a></p></details>`;
}
function home() {
 if(tab!=="player"){channelPage();return;}
 const final=officialCurrent.matches[1],prediction=finalPrediction(selected),selector=modelGrid()+selectedCharacter();
 const pending=`<section class="prediction-player final-pending" id="final-pending" data-model="${selected}"><div class="player-models">${selector}</div><div class="player-pending"><span>LOUD vs VIT · 总决赛</span><h2>${escape(channel().name)} · 待更新</h2><p>尚无这个对阵的推演。原赛前结果按 100T 晋级情景生成，已归档，不替换队名冒充新预测。</p><a class="btn" href="#/archive?ai=${selected}">查看原赛前推演 →</a></div></section>`;
 main.innerHTML=`<section class="wrap player-home"><header class="player-intro event-intro final-intro"><div><p>CHAMPIONS SHANGHAI 2026 · GRAND FINAL</p><h1>LOUD <i>VS</i> VIT</h1><span class="event-scope">10 月 18 日 14:00 · 北京时间 · BO5 总决赛</span></div><a class="event-pick-link" href="#/pickem">我也来预测 <span aria-hidden="true">↗</span></a></header><p class="final-status">${prediction?'DeepSeek 赛前已生成 · 资料与推演冻结于败决开赛前 · AI 模拟，非真实赛况':'三家新对阵推演待更新 · 本轮未新增模型调用'}</p>${prediction?causalMarkup(selector):pending}<div class="final-reference"><a href="${escape(final.source_url)}" target="_blank" rel="noopener noreferrer">Riot 决赛赛程 ↗</a><a href="${escape(final.additional_source_url)}" target="_blank" rel="noopener noreferrer">VLR 决赛详情 ↗</a><a href="#/archive">Archive · 10/17 赛前预测与赛果</a></div>${actualSources()}</section>`;
 bindModels();if(prediction)mountCausalPlayer(selected,{caseIndex:1});
}
function archivePage(){
 const actual=archiveData.actual_result;
 main.innerHTML=pageHead('Archive','10 月 17 日 · 冻结预测与已核实赛果')+`<div class="wrap section archive-page"><section class="card"><p class="pill">败者组决赛 · 已结束</p><h2>${actual.teams[0]} ${actual.score.join(' : ')} ${actual.teams[1]}</h2><div class="current-map-scores">${actual.maps.map(m=>`<span>${m.map} <b>${m.score.join(':')}</b></span>`).join('')}</div><p class="muted">地图比分按 VIT : 100T 顺序。</p><p><a href="${escape(actual.source_url)}" target="_blank" rel="noopener noreferrer">VLR 终局赛果 ↗</a> · <a href="#/leaderboard">查看胜者与比分命中 →</a></p><p>赛前四家两场推演全部保留，共 597 回合。每家的总决赛对手沿用其原败决预测；与真实对阵不同的情景不作为新决赛预测。</p><p class="muted">冻结证据对应版本 ${archiveData.baseline_git_revision.slice(0,7)}，原模型文件保留 SHA-256 绑定。没有赛后回填，也没有重跑模型。</p></section><section class="card section-heading"><label>查看模型 <select id="archive-model">${channels.map(c=>`<option value="${c.id}" ${selected===c.id?'selected':''}>${escape(c.name)}</option>`).join('')}</select></label><div id="archive-results"></div></section>${new URLSearchParams(location.hash.split('?')[1]||'').get('replay')==='1'?causalMarkup(''):''}${actualSources()}</div>`;
 const show=()=>{$('#archive-results').innerHTML=`<p class="muted">${selected==='deepseek'?'原总决赛情景 LOUD vs VIT，与实际对阵一致；赛前已生成。':'原总决赛情景 LOUD vs 100T，与实际对阵不同，仅供历史回看。'}</p>`+currentCards(currentData.models[selected]);};show();$('#archive-model').onchange=e=>{location.hash='#/archive?ai='+e.target.value;};if($('#prediction-player'))mountCausalPlayer(selected);
}

function currentMeta(){return `<p class="current-meta"><span class="pill">赛前冻结推演</span> 四家共 ${currentData.round_count} 回合 · 资料截止 ${formatDate(currentData.evidence_frozen_at)} · 页面整理 ${formatDate(currentData.prepared_at)}（北京时间）</p>`;}
function currentPlay(model,part,map){return `#/archive?replay=1&ai=${model.channel}&at=${(map||part).start_time+.03}`;}
function currentCards(model){return `<div class="grid current-series-grid">${model.cases.map(p=>`<article class="card current-series-card ${p.id===(currentCase?'gf':'lf')?'active':''}" data-channel="${model.channel}" data-match="${p.id}" data-source="${model.source_sha256}"><small>${p.label} · 原赛前 AI 推演</small><h3>${p.teams[0]} <strong>${p.score.join(' : ')}</strong> ${p.teams[1]}</h3><p>${p.winner}${p.id==='lf'?' 晋级总决赛':' 夺冠'} · ${p.round_count} 回合</p><div class="current-map-scores">${p.maps.map(m=>`<span>${m.map} <b>${m.score.join(':')}</b></span>`).join('')}</div><a class="btn" href="${currentPlay(model,p)}">回放这场推演 →</a> ${p.quality_flags.map(n=>`<p class="causal-quality-note">${escape(n.message)}</p>`).join('')}</article>`).join('')}</div>`;}
function currentMatchControl(model){return `<label class="current-match-control">查看比赛 <select id="current-match-select">${model.cases.map((p,i)=>`<option value="${i}" ${i===currentCase?'selected':''}>${p.label} · ${p.teams.join(' vs ')}</option>`).join('')}</select></label>`;}
function renderCurrentPlayers(model){
 const rows=model.players;const wrap=$('#channel-content');wrap.innerHTML=currentMeta()+`<section class="card"><h2>模型阵容与事件统计 · ${escape(channel().name)}</h2><p class="muted">按本轮实际选人和击杀事件累计，属于 AI 推演。</p><div class="form-row"><label>找选手<input id="fiction-player-search" type="search" placeholder="输入昵称"></label><label>战队<select id="fiction-player-team"><option value="">全部战队</option>${[...new Set(rows.map(p=>p.team))].map(t=>`<option>${t}</option>`).join('')}</select></label><label>排序<select id="fiction-player-sort"><option value="kills">模型击杀</option><option value="name">昵称</option><option value="maps">出场地图</option></select></label><label><input id="fiction-player-both" type="checkbox">两场都出场</label></div><div id="fiction-player-results"></div></section>`;
 const show=()=>{const query=$('#fiction-player-search').value.toLowerCase(),team=$('#fiction-player-team').value,both=$('#fiction-player-both').checked,sort=$('#fiction-player-sort').value;const list=rows.filter(p=>(!team||p.team===team)&&p.name.toLowerCase().includes(query)&&(!both||p.cases.length===2)).sort((a,b)=>sort==='name'?a.name.localeCompare(b.name):b[sort]-a[sort]);$('#fiction-player-results').innerHTML=`<div class="table-wrap"><table><thead><tr><th>选手</th><th>战队</th><th>选用特工</th><th>模型击杀 / 阵亡</th><th>地图 / 回合</th></tr></thead><tbody>${list.map(p=>`<tr data-fiction-player="${escape(p.id)}"><th>${escape(p.name)}</th><td>${p.team}</td><td>${p.agents.map(a=>`<span class="current-agent"><img src="${currentAgents.agents[a].image}" alt="">${escape(a)}</span>`).join('')}</td><td>${p.kills} / ${p.deaths}</td><td>${p.maps} / ${p.rounds}</td></tr>`).join('')}</tbody></table>${list.length?'':'<p class="empty">没找到这位选手。</p>'}</div>`;};['fiction-player-search','fiction-player-team','fiction-player-sort','fiction-player-both'].forEach(id=>$('#'+id).oninput=show);show();
}
function renderCurrentReport(model,part){
 $('#channel-content').innerHTML=currentMeta()+currentMatchControl(model)+`<section class="card"><h2>回合战报 · ${part.teams.join(' vs ')}</h2><p class="muted">下面按本轮推演的回合经过展开。</p><label>查看地图 <select id="current-report-map">${part.maps.map((m,i)=>`<option value="${i}">${m.map} · ${m.score.join(':')}</option>`).join('')}</select></label><div id="current-round-report"></div></section>`;
 const show=()=>{const m=part.maps[Number($('#current-report-map').value)];$('#current-round-report').innerHTML=`<div class="current-report-head"><img src="${currentMapArt.maps[m.map].image}" alt="${m.map}"><h3>${m.map} · ${m.score.join(' : ')}</h3></div>${part.quality_flags.filter(n=>n.map===m.map).map(n=>`<p class="causal-quality-note">${escape(n.message)}</p>`).join('')}${m.rounds.map(r=>`<details class="current-round" data-round="${r.number}"><summary>R${r.number} · ${r.winner} 获胜 · ${r.score.join(':')}</summary><p>${escape(r.copy)}</p><ol>${r.events.map(e=>`<li>${escape(e.actor_name)} · ${e.kind==='kill'?'击杀 '+escape(e.target_name):e.kind==='move'?escape(e.route.join(' → ')):e.kind==='plant'?'下包 · '+escape(e.area):'拆包 · '+escape(e.area)}</li>`).join('')}</ol></details>`).join('')}<p><a class="btn" href="${currentPlay(model,part,m)}">在沙盘里回放 ${m.map} →</a></p>`;};$('#current-report-map').onchange=show;show();
}
function renderChannel(){
 const model=currentData.models[selected],part=model.cases[currentCase]||model.cases[0];if(!part){$('#channel-content').innerHTML='<p>该模型尚无完整推演。</p>';return;}
 if(tab==='players')renderCurrentPlayers(model);
 else if(tab==='news')renderCurrentReport(model,part);
 else if(tab==='schedule')$('#channel-content').innerHTML=currentMeta()+`<section class="card"><h2>官方赛程</h2>${officialSchedule()}<p class="muted">官方状态采集于 ${formatDate(officialCurrent.fetched_at)}，不会把模型比分写成真实赛果。</p></section><h2 class="section-heading">${escape(channel().name)} 推演的两场比赛</h2>`+currentCards(model);
 else if(tab==='analysis')$('#channel-content').innerHTML=currentMeta()+currentMatchControl(model)+`<section class="card"><h2>BP 与开局判断</h2><p>${escape(part.bp.reason)}</p><p>禁用：${part.bp.bans.join('、')} · 图序：${part.bp.maps.map(m=>m.map).join(' → ')}</p>${part.maps.map(m=>`<details><summary>${m.map} · ${part.teams[0]} ${m.start_side==='ATK'?'进攻':'防守'}开局</summary><p><b>${part.teams[0]}</b> ${escape(m.plans.left)}</p><p><b>${part.teams[1]}</b> ${escape(m.plans.right)}</p><a href="${currentPlay(model,part,m)}">查看这张图的推演 →</a></details>`).join('')}</section>`;
 else if(tab==='process')$('#channel-content').innerHTML=currentMeta()+`<section class="card"><h2>这份结果怎么来的？</h2><ol class="current-process"><li>四家读取同一份冻结资料。</li><li>模型先决定 BP、起始边，再同时确定双方特工阵容。</li><li>模型分批给出回合事件，程序检查移动区域、存活、击杀和爆能器状态，累计比分。</li><li>下一批接着已验算状态往下推。批内没有逐回合外部反馈。</li><li>该模型自己的败决赢家进入总决赛。</li></ol><p>${escape(model.model)} · ${model.calls} 次请求尝试 · ${model.round_count} 个有效回合</p><a href="data/evidence-v2.json" target="_blank">共同资料 ↗</a></section>`;
 else $('#channel-content').innerHTML=currentMeta()+(tab==='bracket'?'<h2>败决赢家进入该模型的总决赛</h2>':'<h2>两场推演结果</h2>')+currentCards(model);
 const selector=$('#current-match-select');if(selector)selector.onchange=()=>{currentCase=Number(selector.value);history.replaceState(null,'','#/channel?'+new URLSearchParams({ai:selected,tab,case:currentCase?'gf':'lf'}));renderChannel();};
}
function officialSchedule(){return `<div class="official-current-schedule">${officialCurrent.matches.map(m=>`<div class="history-line" data-official-match="${m.id}"><span>${formatDate(m.start_utc)} · ${m.label}</span><b>${m.teams.join(' vs ')}</b><span>${verifiedCompleted(m,officialCurrent)?m.score.join(' : '):m.state==='unstarted'?'待开赛':m.state==='inProgress'?'进行中':'待核实'}</span><a href="${escape(m.source_url)}" target="_blank" rel="noopener noreferrer">赛程 / 赛果来源 ↗</a></div>`).join('')}</div>`;}
function comparePage(){
 const rows=channels.map(c=>({c,m:currentData.models[c.id]}));main.innerHTML=pageHead('数据对比','四家这次各推演出了什么结果')+`<div class="wrap section current-compare">${currentMeta()}<section class="card"><h2>败决与总决赛</h2><div class="table-wrap"><table id="current-result-comparison"><thead><tr><th>模型</th><th>败者组决赛</th><th>总决赛</th><th>有效回合</th></tr></thead><tbody>${rows.map(({c,m})=>`<tr data-current-model="${c.id}" data-source="${m.source_sha256}"><th>${escape(c.name)}</th>${m.cases.map(p=>`<td data-match="${p.id}"><b>${p.teams.join(' vs ')}</b><strong>${p.score.join(' : ')}</strong><small>${p.winner}${p.id==='lf'?' 晋级':' 夺冠'}</small></td>`).join('')}<td>${m.round_count}</td></tr>`).join('')}</tbody></table></div><p class="muted">以上是 10/17 开赛前冻结的推演，各家原总决赛对手由其败决预测产生。实际决赛为 LOUD 对 VIT；其余情景仅供历史回看，不代表新对阵预测。</p></section><section class="card section-heading"><label>查看逐图结果 <select id="compare-model">${channels.map(c=>`<option value="${c.id}" ${c.id===selected?'selected':''}>${escape(c.name)}</option>`).join('')}</select></label><div id="current-compare-maps"></div></section></div>`;
 const show=()=>{const m=currentData.models[$('#compare-model').value];$('#current-compare-maps').innerHTML=currentCards(m);};$('#compare-model').onchange=show;show();
}
function currentTeamBlock(code){
 const roster=evidencePack.rosters[code];return `<section class="card section-heading"><h2>最近观察到的名单</h2><p>${roster?roster.players.map(escape).join(' / '):'当前冻结资料没有这支队的完整名单。'}</p><p class="muted">${roster?'来自 '+formatDate(roster.event_start_utc)+' 的已完成比赛，未来首发未确认。':''}</p></section><section class="card section-heading current-team-block" data-current-team="${code}"><h2>四家本轮推演中的 ${code}</h2>${channels.map(c=>{const m=currentData.models[c.id],parts=m.cases.filter(p=>p.teams.includes(code));return `<details data-current-model="${c.id}"><summary>${escape(c.name)} · ${parts.length?parts.map(p=>p.label+' '+p.score.join(':')).join(' · '):'未进入本轮两场'}</summary>${parts.map(p=>`<h3>${p.label} · ${p.teams.join(' vs ')}</h3>${p.maps.map(map=>`<p><b>${map.map}</b> ${map.lineup.filter(a=>a.team===code).map(a=>escape(a.player)+' / '+escape(a.agent)).join('、')}</p>`).join('')}`).join('')}</details>`;}).join('')}</section>`;
}
function leaderboardPage(){
 const settled=settleCausal(currentData,officialCurrent).sort((a,b)=>channels.findIndex(c=>c.id===a.channel)-channels.findIndex(c=>c.id===b.channel)),count=Math.max(0,...settled.map(s=>s.settled)),fixture=currentFixture(event,officialCurrent),samePickScope=pick&&validatePick(pick,event)&&pick.upperWinner===fixture.upperWinner&&pick.lowerWinner===fixture.lowerWinner;
 const own=samePickScope?settleCausal({models:{personal:{channel:'personal',status:'ready',recorded_at:pick.created_at,cases:[{match_id:event.matches[0].id,label:'败者组决赛',teams:[event.predecessors[0].teams.find(t=>t!==pick.upperWinner),pick.lowerWinner],winner:pick.lfWinner},{match_id:event.matches[1].id,label:'总决赛',teams:[pick.upperWinner,pick.lfWinner],winner:pick.champion}]}}},officialCurrent)[0]:{settled:0,hits:0};
 const ownRow=`<tr data-personal-settlement><th>我的预测</th><td>${own.settled}</td><td>${own.settled?own.hits+' / '+own.settled:'—'}</td><td>—</td><td>${!pick?'还没保存':!samePickScope?'旧对阵记录，暂不计入本轮':own.settled?'已按赛果核对':'待结算'}</td></tr>`;
 main.innerHTML=pageHead('谁最准',count?'只对照已核实赛果':'比赛还没打完，先把答案留在这里')+`<div class="wrap section">${currentMeta()}<section class="card"><h2>${count?'已核对 '+count+' 场':'等待真实赛果'}</h2>${officialSchedule()}<p>胜者与大比分分别核对，只使用已核实的真实赛果；比分按队名对齐，决赛对手不符的原情景不参与该场结算。当前仅有一场已结束，不据此宣称模型或算法更准确。</p><p class="muted">真实赛果采集时间：${formatDate(officialCurrent.fetched_at)}。仅结算有终局赛果记录、且原始预测入库早于开赛的比赛。</p><div class="table-wrap"><table id="current-leaderboard"><thead><tr><th>模型</th><th>已核对</th><th>胜者命中</th><th>大比分命中</th><th>状态</th></tr></thead><tbody>${settled.map(s=>`<tr data-current-model="${s.channel}"><th>${escape(channels.find(c=>c.id===s.channel).name)}</th><td>${s.settled}</td><td>${s.settled?s.hits+' / '+s.settled:'—'}</td><td>${s.score_settled?s.score_hits+' / '+s.score_settled:'—'}</td><td>${s.settled?'按已核实赛果核对':'待结算'}</td></tr>`).join('')}${ownRow}</tbody></table></div>${pick?`<p>你的记录：${escape(pick.champion||'尚未选冠军')} · ${pick.created_at?formatDate(pick.created_at):'未记录时间'}。${count?'仅在记录时间早于相应开赛时间时参与核对。':'等待两场比赛的真实结果。'}</p>`:'<a class="btn" href="#/pickem">留一份我的预测 →</a>'}</section></div>`;
}
function methodPage(){main.innerHTML=pageHead('AI 赛制介绍','从地图 BP 到最后一个回合')+`<div class="wrap section article">${currentMeta()}<section class="card"><h2>同一份资料，四条独立推演</h2><p>资料冻结于 ${formatDate(currentData.evidence_frozen_at)}。四家只推演 10 月 17 日败者组决赛与 18 日总决赛，共 ${currentData.round_count} 个有效回合；各家总决赛使用自己推演出的败决赢家。</p><ol class="current-process"><li><b>地图 BP：</b>按 BO5 次序禁图、选图、选起始边；总决赛胜者组队有两次禁图。</li><li><b>选特工：</b>双方同时确定阵容；选手名单沿用最近已观察阵容作为假设。</li><li><b>推演回合：</b>模型给出区域移动、击杀、下包、拆包等有序事件。</li><li><b>检查状态：</b>程序检查区域、角色存活与爆能器状态，累计回合和地图比分；无效后缀不进入结果。</li><li><b>继续往下推：</b>下一批读取上一批已验算状态。批内没有逐回合外部反馈，最后由累计比分得到两场胜者。</li></ol></section><section class="card section-heading"><h2>地图与边界</h2><p>使用七张真实地图底图与特工标识。路线是模型选择的区域序列，尚未模拟完整枪械、技能、碰撞、视线和信用点。加时从第25回合第一队先攻，逐轮换边，双方全装。</p><p>旧概率抽样与独立 Ascent 场景不参与本轮结果。个人预测页的战绩/自选排名试算仅供你填表参考。</p></section><section class="card section-heading"><h2>赛后怎么核对？</h2><p>只以已核实终局赛果的目标比赛为真值，核对预测在开赛前已冻结，再核对败决胜者与总冠军。没结束就等，不拿模型之间互相投票当准确率。</p></section><section class="card section-heading"><h2>共同资料</h2><a href="data/evidence-v2.json" target="_blank">共同冻结资料 ↗</a> · <a href="data/causal/map-context.json" target="_blank">地图区域来源 ↗</a></section></div>`;}
function renderTicker(){
 const ticker=$('#simulation-ticker');ticker.hidden=pageRoute==='/';if(ticker.hidden)return;ticker.className=`ticker${tickerOpen?tickerPaused?' paused':'':' ticker-closed'}`;
 if(!tickerOpen){ticker.innerHTML='<button class="ticker-label">展开推演速报</button>';ticker.querySelector('button').onclick=()=>{tickerOpen=true;renderTicker();};return;}
 const reports=channels.flatMap(c=>currentData.models[c.id].cases.map(p=>({c,m:currentData.models[c.id],p}))),row=duplicate=>`<div class="ticker-row"${duplicate?' aria-hidden="true"':''}>${reports.map(({c,m,p})=>`<a class="tick" data-current-model="${c.id}" data-match="${p.id}" data-source="${m.source_sha256}" href="#/channel?ai=${c.id}&tab=prediction&case=${p.id}"${duplicate?' tabindex="-1"':''}><span class="pill">原赛前推演</span><span class="muted">${escape(c.name)} · ${p.label}</span><b>${p.teams[0]} ${p.score.join('–')} ${p.teams[1]}</b><span>${p.winner}${p.id==='lf'?' 晋级':' 夺冠'}</span><small>结果整理 ${formatDate(currentData.prepared_at)}</small></a>`).join('')}</div>`;
 ticker.innerHTML=`<button class="ticker-label" aria-pressed="${tickerPaused}">${tickerPaused?'滚动速报':'暂停速报'}</button><div class="ticker-track"><div class="ticker-move">${row(false)}${tickerPaused?'':row(true)}</div></div><button class="ticker-close" aria-label="收起模拟速报">×</button>`;ticker.querySelector('.ticker-label').onclick=()=>{tickerPaused=!tickerPaused;renderTicker();};ticker.querySelector('.ticker-close').onclick=()=>{tickerOpen=false;renderTicker();};
}

function channelPage() {
  const sections=[["schedule","赛程赛果"],["bracket","淘汰赛"],["players","选手榜"],["news","剧情与战报"],["analysis","赛前评估"],["process","预测过程"],["prediction","推演结果"]];
  main.innerHTML=pageHead("赛事与数据", "本轮四家推演、阵容与回合战报")+`<section class="wrap player-detail channel-hub">${modelGrid()}<div class="tabs home-tabs" role="tablist" aria-label="赛事频道内容">${sections.map(([id,name])=>`<button role="tab" aria-selected="${tab===id}" aria-controls="channel-content" data-tab="${id}" class="${tab===id?'on':''}">${name}</button>`).join('')}</div><div id="channel-content" role="tabpanel"></div></section>`;
  bindModels();document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{location.hash='#/channel?'+new URLSearchParams({ai:selected,tab:b.dataset.tab,case:currentCase?"gf":"lf"});});renderChannel();
}

function formatDate(value) {
  if(!Number.isFinite(Date.parse(value)))return "未记录";
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
      return `<a class="card card-link simulation-card" href="${reviewLink(index)}"><div class="section-head"><span class="pill">新版抽样模拟</span><span class="muted">${formatDate(event.matches[index].start_utc)}</span></div><h3>${event.matches[index].label}</h3><div class="simulation-score">${logo(series.teams[0])}<b>${series.teams[0]}</b><strong>${series.score.join(" : ")}</strong><b>${series.teams[1]}</b>${logo(series.teams[1])}</div><p>${series.winner} ${index === 0 ? "晋级总决赛" : "赢得模拟冠军"} · ${series.maps.length} 图</p>${withReport ? `<p class="muted">${escape(pairReason(series.teams))}</p>` : ""}<small class="muted">${series.teams[0]} 赛前 BO5 概率 ${pct(p)} · 查看逐图回看 →</small></a>`;
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
    `<section class="card review-head"><span class="pill">AI 模拟 · 非真实赛果</span><div class="versus"><div class="vs-team">${logo(series.teams[0])}<b>${series.teams[0]}</b></div><div class="score">${series.score.join(" : ")}<small>BO5 · ${series.maps.length} 图</small></div><div class="vs-team">${logo(series.teams[1])}<b>${series.teams[1]}</b></div></div><h2>${series.winner} ${index === 0 ? "晋级总决赛" : "夺得模拟冠军"}</h2><p class="muted">这是历史概率方案在所选晋级情景和固定随机种子下的模拟回看，与当前首页的因果推演分开保存。</p><div class="odds-bar" aria-label="赛前系列赛概率"><span style="width:${100 * seriesProbability(p)}%">${series.teams[0]} ${pct(seriesProbability(p))}</span><span>${series.teams[1]} ${pct(1 - seriesProbability(p))}</span></div></section><section class="card section-heading"><h2>赛前判断 · ${escape(channel().name)}</h2><p>${escape(pairReason(series.teams))}</p><p class="muted">单图概率 ${pct(p)}；按各图独立且同概率换算，${series.teams[0]} 赢得 BO5 的概率为 ${pct(seriesProbability(p))}。</p></section><section class="card section-heading"><h2>逐图回看</h2><div class="map-tabs" role="group" aria-label="选择模拟地图">${series.maps.map((map, i) => `<button data-review-map="${i}" aria-pressed="${i === 0}" class="${i === 0 ? "on" : ""}">第 ${i + 1} 图 · ${map.winner} 胜</button>`).join("")}</div><div id="review-map" aria-live="polite"></div><div class="table-wrap"><table><thead><tr><th>地图</th><th>模拟胜者</th><th>累计比分</th><th>${series.teams[0]} 此时系列赛概率</th></tr></thead><tbody>${scoreTable}</tbody></table></div></section><section class="card section-heading"><h2>系列赛胜率走势</h2><p class="muted">每图结束后按剩余图数计算的条件概率，沿用模型的固定单图概率。不是实测局内走势。</p><div class="chart-scroll"><svg viewBox="0 0 900 255" class="series-chart" role="img" aria-label="${series.teams[0]} 系列赛条件胜率走势">${[0, 0.25, 0.5, 0.75, 1].map((v) => `<line x1="55" x2="845" y1="${210 - v * 160}" y2="${210 - v * 160}" class="chart-grid"/><text x="42" y="${215 - v * 160}" text-anchor="end">${v * 100}%</text>`).join("")}<polyline points="${points.map((p) => p.join(",")).join(" ")}"/>${points.map(([x, y], i) => `<circle cx="${x}" cy="${y}" r="5"/><text x="${x}" y="240" text-anchor="middle">${i === 0 ? "赛前" : `第 ${i} 图`}</text><text x="${x}" y="${y - 12}" text-anchor="middle" class="chart-value">${pct(chances[i])}</text>`).join("")}</svg></div></section>${fictionDetails(fictionalReview(index), index)}<div class="form-row section-heading"><a class="btn" href="${reviewLink(1 - index)}">${index === 0 ? "下一场 · 总决赛" : "上一场 · 败者组决赛"} →</a><a class="btn" href="#/?ai=${selected}">返回直播</a><button id="share-review">复制回看链接</button></div>`;
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
function v2ComparisonMarkup() {
  const header=channels.map(c=>`<th>${escape(c.name)}</th>`).join("");
  const row=(label,values)=>`<tr><th>${label}</th>${values.map(p=>`<td>${pct(p)}</td>`).join("")}</tr>`;
  return `<section class="card" id="v2-comparison"><span class="kicker">INPUT V2 · 本轮真实数据预测</span><h2>逐图方案推导的系列赛与夺冠概率</h2><p class="muted">共同事实与规则输入；各家自主BP和起始边条件不同，概率差异同时包含方案差异，不是控制变量的模型能力测评。概率均未校准。</p><div class="table-wrap"><table><thead><tr><th>系列赛左队胜率</th>${header}</tr></thead><tbody>${Object.entries({lf:"败决 VIT vs 100T",gf_vit:"总决 LOUD vs VIT",gf_100t:"总决 LOUD vs 100T"}).map(([key,label])=>row(label,channels.map(c=>v2Predictions[c.id]?.computed.cases[key].distribution.filter(r=>r.score[0]===3).reduce((n,r)=>n+r.probability,0)??null))).join("")}</tbody></table></div><div class="table-wrap"><table><thead><tr><th>条件夺冠概率</th>${header}</tr></thead><tbody>${["LOUD","VIT","100T"].map(team=>row(team,channels.map(c=>v2Predictions[c.id]?.computed.champion_probabilities[team]??null))).join("")}</tbody></table></div><p><a class="source-link" href="#/?tab=prediction">查看每家BP、逐因素理由和证据 →</a></p></section>`;
}
function teamsPage(code) {
  const facts=factualEvent(event,officialCurrent);
  if (code && event.teams[code]) {
    const t = event.teams[code],
      s = teamStats(facts, code),
      history = facts.history.filter((m) => m.teams.includes(code));
    main.innerHTML =
      pageHead(t.name, "官方本届系列赛记录 · 历史事实不计入两场预测") +
      `<div class="wrap section"><div class="card"><div class="team-head">${logo(code)}<div><h2>${code}</h2><span class="muted">${escape(t.region?.toUpperCase())}</span></div></div><div class="stats"><div class="stat"><strong>${s.wins} / ${s.played}</strong><span>系列赛获胜 / 已赛</span></div><div class="stat"><strong>${s.mapsWon}–${s.mapsLost}</strong><span>地图胜负</span></div><div class="stat"><strong>${pct(s.mapsWon / (s.mapsWon + s.mapsLost))}</strong><span>地图胜率</span></div></div>${history.map((m) => `<div class="history-line"><small class="muted">${formatDate(m.start_utc)}</small><b>${m.teams.join(" vs ")}</b><span>${m.score.join(" : ")}</span><span class="tag">真实赛果</span></div>`).join("")}</div><div class="actions"><a class="btn" href="#/teams">返回战队</a><a class="btn" href="https://valorantesports.com/en-US/" target="_blank" rel="noreferrer">官方来源 ↗</a></div></div>`;
    main.insertAdjacentHTML('beforeend',`<div class="wrap section">${currentTeamBlock(code)}</div>`);
    return;
  }
  main.innerHTML =
    pageHead("战队", "已核实赛事记录，与本轮模型阵容分开看") +
    `<div class="wrap section">${currentMeta()}<p class="muted">赛事记录截至 ${formatDate(officialCurrent.fetched_at)}；队伍详情另列本轮模型选人和比赛记录。</p><input class="team-search" id="team-search" type="search" placeholder="搜索战队名称或简称" aria-label="搜索战队"><div class="grid" id="team-grid"></div></div>`;
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
            const s = teamStats(facts, t.code);
            return `<a class="card card-link" href="#/team/${t.code}"><div class="team-head">${logo(t.code)}<div><h3>${t.code}</h3><small class="muted">${escape(t.name)}</small></div></div><div class="stats"><div class="stat"><strong>${s.wins}–${s.played - s.wins}</strong><span>系列赛</span></div><div class="stat"><strong>${s.mapsWon}–${s.mapsLost}</strong><span>地图</span></div></div><span class="tag">${finalists.includes(t.code) ? "决赛周末四强" : "本届参赛队"}</span></a>`;
          })
          .join("")
      : '<div class="card empty">没有找到匹配战队</div>';
  };
  renderTeams("");
  $("#team-search").oninput = (e) => renderTeams(e.target.value);
}
function referenceRanking(id) {
  if(currentData.models[id]?.result_order)return [...currentData.models[id].result_order];
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
  editor.innerHTML = `<section class="card rank-editor" aria-label="自定义实力排名"><div class="section-head"><div><h3>我的排名</h3><p class="muted">越靠前越强。拖动抓手、先选队再选位置，或使用上移/下移按钮。</p></div><div class="rank-import"><select id="ranking-import" aria-label="导入排名来源"><option value="baseline">统计基线</option>${channels
    .filter((c) => available(c.id))
    .map((c) => `<option value="${c.id}">${c.name}</option>`)
    .join(
      "",
    )}</select><button id="ranking-import-button">照它排一下</button></div></div><p id="ranking-tip" class="muted" role="status">${rankingSelection === null ? "键盘聚焦一行后，可按上下方向键移动该战队。" : `已选中 ${rankingDraft[rankingSelection]}，点击要放到的位置。`}</p><ol class="ranking-list">${rankingDraft.map((team, i) => `<li data-ranking-row="${i}" tabindex="0" class="${rankingSelection === i ? "selected" : ""}" aria-label="第 ${i + 1} 名 ${team}"><span class="ranking-number">${i + 1}</span><span class="ranking-grip" data-ranking-grip="${i}" aria-hidden="true">⠿</span>${logo(team)}<b>${team}</b><span class="ranking-buttons"><button data-ranking-move="up" data-ranking-index="${i}" aria-label="上移 ${team}" ${i === 0 ? "disabled" : ""}>↑</button><button data-ranking-move="down" data-ranking-index="${i}" aria-label="下移 ${team}" ${i === rankingDraft.length - 1 ? "disabled" : ""}>↓</button></span></li>`).join("")}</ol><div class="actions"><button class="btn primary" id="ranking-use">使用这份排名</button><button class="btn" id="ranking-cancel">取消</button></div><small class="muted">名次差换算沿用参考站的单图公式：1 / (1 + exp(−名次差 × 0.122))。它是个人实力假设，不是 AI 输出。导入模型时，按本轮两场推演的晋级顺序排列。</small></section>`;
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
        ? "排名存好了。"
        : "这次能用，但浏览器没存住。",
    );
  };
}
function pickemPage() {
  const { upperWinner, upperLoser, lowerWinner } = personalFixture(),
    teams = [upperLoser, lowerWinner],
    finalists = [upperWinner, draft.lfWinner];
  const actual=currentFixture(event,officialCurrent),historical=upperWinner!==actual.upperWinner||lowerWinner!==actual.lowerWinner;
  main.innerHTML =
    pageHead("你觉得谁能赢？", "先选败决赢家，再选冠军。比分也由你来定。") +
    `<div class="wrap section"><div class="tabs" role="tablist"><button class="on" role="tab" aria-selected="true" id="my-tab">我来选</button><button role="tab" aria-selected="false" id="sim-tab">先看参考</button></div>${currentMeta()}<p class="pick-current-fixture">当前赛程：${actual.upperLoser} vs ${actual.lowerWinner}，胜者再打 ${actual.upperWinner}。</p>${historical||savedPickIncompatible?`<div class="notice" id="saved-pick-notice">上次那份是另一组对阵，原记录和选择都还在。<button id="current-pick-draft" class="btn">按当前对阵另填</button></div>`:''}${pick?`<details id="saved-pick-record"><summary>看看上次存的预测</summary><pre>${escape(JSON.stringify(pick,null,2))}</pre></details>`:''}<div class="stepper"><span class="on">1 · 选败决赢家</span><span class="${draft.lfWinner ? "on" : ""}">2 · 再选冠军</span><span class="${draft.champion ? "on" : ""}">3 · 存下来</span></div><div class="form-row"><label>先看看谁的判断<select id="reference-model">${channels
      .filter((c) => available(c.id))
      .map(
        (c) =>
          `<option value="${c.id}" ${personalReference === c.id ? "selected" : ""}>${c.name}</option>`,
      )
      .join(
        "",
      )}<option value="baseline" ${personalReference === "baseline" ? "selected" : ""}>按战绩试算</option>${validRanking(customRanking, finalistsList()) ? `<option value="mine" ${personalReference === "mine" ? "selected" : ""}>按我的排名试算</option>` : ""}</select></label><button id="autofill" class="btn gold">照这个参考填</button><button id="custom-ranking" class="btn">自己排个名</button><button id="reset" class="btn">这份重选</button></div><div id="ranking-editor"></div><div class="bracket"><div class="pick-match" id="lower-final"><h3>10 / 17 · 败者组决赛 <span>BO5</span></h3>${teams.map((t) => pickTeam(t, draft.lfWinner, "lf", personalProbability(...teams), teams[0])).join("")}${draft.lfWinner ? scoreSelect("lf", draft.lfWinner, teams, draft.lfScore) : ""}</div><div class="bracket-arrow">→</div><div class="pick-match" id="grand-final"><h3>10 / 18 · 总决赛 <span>BO5</span></h3>${finalists.map((t) => (t ? pickTeam(t, draft.champion, "gf", draft.lfWinner ? personalProbability(...finalists) : null, finalists[0]) : '<button class="pick-team" disabled>等待败者组决赛胜者</button>')).join("")}${draft.champion ? scoreSelect("gf", draft.champion, finalists, draft.gfScore) : ""}</div><div class="bracket-arrow">→</div><div class="card result-card" id="pick-result"><small>你选的冠军</small>${draft.champion ? logo(draft.champion) + "<h2>" + draft.champion + "</h2>" : '<h2>?</h2><p class="muted">先选出败决赢家，再选冠军。</p>'}</div></div><div class="actions"><button class="btn primary" id="save-pick" ${draft.champion ? "" : "disabled"}>存下我的预测</button><button class="btn" id="poster-button" ${draft.champion ? "" : "disabled"}>做张海报</button><button class="btn" id="share-pick" ${draft.champion ? "" : "disabled"}>发给朋友看看</button></div><p class="muted" style="font-size:12px;margin-top:14px" id="save-state">${pick ? "上次预测：" + escape(pick.champion) + " 冠军 · " + escape(formatDate(pick.created_at)) : "选好以后记得存下来，这份预测留在当前浏览器。"}</p><section class="card" id="personal-simulation" hidden style="margin-top:20px"></section></div>`;
  const fresh=$('#current-pick-draft');if(fresh)fresh.onclick=()=>{draftScenario=null;savedPickIncompatible=false;draft={lfWinner:null,lfScore:null,champion:null,gfScore:null};pickemPage();};
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
    const model=currentData.models[personalReference];
    if(model?.status==='ready'){
      const [lf,gf]=model.cases;if(!lf.teams.every(t=>teams.includes(t))||!gf.teams.includes(upperWinner)){notify('这家本轮没推演这组对阵，你可以自己选。');return;}
      draft.lfWinner=lf.winner;draft.lfScore=teams[0]===lf.teams[0]?[...lf.score]:[...lf.score].reverse();draft.champion=gf.winner;draft.gfScore=upperWinner===gf.teams[0]?[...gf.score]:[...gf.score].reverse();pickemPage();sound('champion');notify('两场结果填好了，你还可以改。');return;
    }
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
    notify("按你的参考填好了，你还可以改。");
  };
  $("#reset").onclick = () => {
    draft = { lfWinner: null, lfScore: null, champion: null, gfScore: null };
    pickemPage();
    notify("这份草稿清空了，上次保存的还在。");
  };
  $("#save-pick").onclick = savePick;
  $("#poster-button").onclick = showPoster;
  $("#share-pick").onclick = sharePick;
  $("#sim-tab").onclick=()=>{
    const model=currentData.models[personalReference];$('#personal-simulation').hidden=false;
    if(model?.status==='ready')$('#personal-simulation').innerHTML=`<h2>${escape(channels.find(c=>c.id===personalReference).name)} 这次怎么选</h2>`+currentCards(model);
    else{const lf=simulateSeries(...teams,personalProbability(...teams),Date.now()%4294967296),gf=simulateSeries(upperWinner,lf.winner,personalProbability(upperWinner,lf.winner),(Date.now()%4294967296)+1);$('#personal-simulation').innerHTML=`<span class="pill">你的参考试算</span><h2>${gf.winner} 夺冠</h2><p>${lf.teams.join(' vs ')} · ${lf.score.join(':')}<br>${gf.teams.join(' vs ')} · ${gf.score.join(':')}</p><p>按你选的战绩或排名抽样，不是模型新预测，也没改你选的答案。</p>`;}
    $('#my-tab').classList.remove('on');$('#sim-tab').classList.add('on');$('#my-tab').setAttribute('aria-selected','false');$('#sim-tab').setAttribute('aria-selected','true');
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
  return `<button class="pick-team ${winner === t ? "win" : winner ? "lose" : ""}" data-pick="${phase}" data-team="${t}" aria-pressed="${winner === t}">${logo(t)}<b>${t}</b><small>${p==null?(currentData.models[personalReference]?.cases[phase==='lf'?0:1]?.winner===t?'模型选了这队':'由你来选'):pct(seriesProbability(t===first?p:1-p))}</small></button>`;
}
function scoreSelect(phase, winner, teams, score) {
  const loser = winner === teams[0] ? teams[1] : teams[0],
    losses = score ? Math.min(...score) : 1;
  return `<label class="score-select">${winner} 3 : <select id="${phase}-score" aria-label="${phase === "lf" ? "败者组决赛" : "总决赛"}负方地图数">${[0, 1, 2].map((n) => `<option value="${n}" ${n === losses ? "selected" : ""}>${n}</option>`).join("")}</select> ${loser}</label>`;
}
function makePick() {
  const pair = personalFixture();
  return {
    version: 1,
    source_sha256: currentData.evidence_sha256,
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
    notify("还差两场的赢家或比分，选完再存。");
    return;
  }
  pick = value;
  if (store.set("pick", pick)) {
    sound("stamp");
    notify("这份预测存好了");
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
    `<p class="kicker">CHAMPIONS SHANGHAI 2026</p><h2>我的决赛预测</h2>${logo(draft.champion)}<h1 class="gold" style="margin:18px 0">${draft.champion}</h1><p>10 / 17 · ${personalFixture().upperLoser} ${draft.lfScore.join(" : ")} ${personalFixture().lowerWinner}<br>10 / 18 · ${personalFixture().upperWinner} ${draft.gfScore.join(" : ")} ${draft.lfWinner}</p><p class="muted">个人情景预测 · 非官方赛果</p>`;
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
function evidenceMarkup() {
  const pack = evidencePack, series = pack.facts.filter(f => f.type === "completed_series"), maps = pack.facts.filter(f => f.type === "map_result");
  const source = id => pack.sources.find(s => s.id === id);
  const date = value => new Date(value).toLocaleString("zh-CN", {timeZone:"Asia/Shanghai", hour12:false});
  return `<section class="card section evidence-pack" id="evidence-pack"><span class="kicker">INPUT V2 · 实际运行输入</span><h2>本轮模型读取了哪些资料？</h2><p>已采集 ${series.length} 场四强相关系列赛、${maps.length} 张真实地图、逐图选手表现与特工记录。冻结时间：${escape(date(pack.frozen_at))}（北京时间）。本轮真实数据预测使用这份输入；旧版预测与固定Ascent走位保留原输入，不回填新资料。</p><div class="table-wrap"><table><thead><tr><th>队伍</th><th>本届系列赛</th><th>逐图样本</th><th>最近实际出场名单</th></tr></thead><tbody>${pack.teams.map(team => `<tr><td>${escape(team)}</td><td>${pack.team_summaries[team].series_played}</td><td>${Object.values(pack.team_summaries[team].by_map).reduce((n,m)=>n+m.played,0)}</td><td>${pack.rosters[team].players.map(escape).join(" / ")}</td></tr>`).join("")}</tbody></table></div><p class="muted">名单来自最近已完成比赛，不能视为17/18日确认首发。地图、攻守回合、ACS/KAST和BP来自 VLR 二级赛事数据库；攻守汇总仅含常规回合，加时另列。规则、七图池、比赛版本来自 Riot 官方文件。未采集训练赛、伤病或已校准胜率。</p><details><summary>逐图样本与可追溯来源</summary>${pack.teams.map(team => `<h3>${escape(team)} · 本届地图记录</h3><p>${Object.entries(pack.team_summaries[team].by_map).map(([name,m])=>`${escape(name)} ${m.wins}胜/${m.played}图`).join(" · ")}</p>`).join("")}<ul>${series.slice().sort((a,b)=>b.event_start_utc.localeCompare(a.event_start_utc)).map(f=>`<li><a href="${escape(source(f.source_id).url)}" target="_blank" rel="noreferrer">${escape(f.value.teams.join(" vs "))} ${f.value.score.join(":")} · ${escape(f.event_start_utc.slice(0,10))} ↗</a></li>`).join("")}</ul></details><p><a class="source-link" href="data/evidence-v2.json" target="_blank">下载证据包 v2 · 来源ID、时间与缺口 ↗</a>　<a class="source-link" href="data/forecast-inputs.json" target="_blank">查看旧预测输入时点更正记录 ↗</a></p><p class="muted">当前链路为：共同资料 → BP/选边 → 特工阵容 → 分批回合事件 → 状态验算 → 累计比分与胜者。下一批读取已验算状态，批内没有逐回合外部反馈。旧概率方案作为历史资料保留，不参与本轮结果。</p></section>`;
}
function aboutPage() {
  main.innerHTML =
    pageHead("内容、数据与素材说明", "来源可追溯，未知信息保持未知") + `<div class="wrap section article">${evidenceMarkup()}</div>` +
    `<div class="wrap section article"><section class="card"><h2>赛事数据</h2><p>最近获取：${escape(new Date(event.fetched_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" }))}（北京时间）。官方页面结构化数据中共提取 ${event.history.length} 场已完成系列赛，本应用只预测两场 BO5。</p><ul>${event.sources.map((s) => `<li><a href="${escape(s.url)}" target="_blank" rel="noreferrer">${escape(s.publisher)} · ${s.role === "official_schedule_results" ? "官方赛程与真实结果" : "上海冠军赛赛制说明"} ↗</a></li>`).join("")}</ul><p class="muted">${event.limitations.map(escape).join("<br>")}</p><details><summary>快照与原始数据</summary><p style="overflow-wrap:anywhere">官方响应 SHA-256：${event.source_sha256}</p><a href="data/event.json" target="_blank" class="source-link">查看赛事快照 JSON</a></details></section><section class="card" style="margin-top:20px"><h2>实际模型推演</h2><p>当前首页由四个模型各自读取共同冻结资料，依次选择地图、起始边和特工，再预测同图的有序回合事件。程序验算事件并累计比分，下一批读取已经形成的状态；总决赛使用该模型自己推演出的败决赢家。未结束的链条如实标示。</p><p>这是赛前 AI 模拟，不是官方赛果。区域路径、交锋和经济档位由模型判断，未模拟完整枪械、技能、碰撞或信用点；首发沿用最近出场名单作假设。状态一致性检查不能证明预测更准确。</p><p><a class="source-link" href="data/evidence-v2.json" target="_blank">共同冻结证据 ↗</a> · <a class="source-link" href="data/causal/map-context.json" target="_blank">真实地图区域与来源 ↗</a></p></section><section class="card" style="margin-top:20px"><h2>视觉参考与素材</h2><p>交互与页面结构参考用户指定的 <a href="https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html" target="_blank" rel="noreferrer">S16 AI 预测大赛</a>。赛事内容改为 VALORANT，范围限定为最后两场。前端代码独立编写。</p><p>GPT人物由用户指定为 <a href="https://genderswapai.com/zh-CN/ai-gijinka/gpt" target="_blank" rel="noreferrer">ZipZipPipe 的 GPT 娘主立绘</a>；DeepSeek、豆包、MiMo 人像引用自 <a href="https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html" target="_blank" rel="noreferrer">我叫张大喵的 S16 AI 预测大赛</a>，保留各角色对应关系，素材记录见 data/assets.json。战队标志来自 Riot 赛事官网。图像权利归相应权利人，模型形象不代表提供商背书或合作。</p></section><section class="card" style="margin-top:20px"><h2>字体授权</h2><p>正文与中文标题使用设备系统字体，英文标题与数字按需使用 Anton、JetBrains Mono。历史 OPPO Sans、MiSans 素材和许可保留，但页面不加载这两份大字体；所有字体原文件未修改。</p><ul><li><a class="source-link" href="assets/fonts/OPPO-Sans-LICENSE.txt" target="_blank">OPPO Sans 许可</a></li><li><a class="source-link" href="assets/fonts/MiSans-LICENSE.pdf" target="_blank">MiSans 许可 · Xiaomi Inc.</a></li><li><a class="source-link" href="assets/fonts/anton-OFL.txt" target="_blank">Anton · SIL OFL 1.1</a></li><li><a class="source-link" href="assets/fonts/jetbrainsmono-OFL.txt" target="_blank">JetBrains Mono · SIL OFL 1.1</a></li></ul></section><section class="card" style="margin-top:20px"><h2>本地保存与分享</h2><p>模型选择、个人预测、自定义实力排名、静音和晋级情景保存在当前浏览器。分享链接只包含你选择的晋级情景、两场比分和生成时间。数据不会上传。</p></section></div>`;
}
async function route() {
  clearTimeout(playerTimer);
  playing = false;
  const [path, query = ""] = (location.hash.slice(1) || "/").split("?");
  if(path==="/"&&new URLSearchParams(query).has("at")){location.replace("#/archive?replay=1&"+query);return;}
  pageRoute = path;
  if (path === "/") playing = true;
  const params = new URLSearchParams(query);
  currentCase=params.get("case")==="gf"?1:0;
  if(path==="/"&&!params.has("ai"))selected="deepseek";
  if (
    params.has("tab") &&
    [
      "player",
      "prediction",
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
  else if (path === "/") tab = "player";
  else if (path === "/channel") tab = "schedule";
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
      draftScenario={upperWinner:value.upperWinner,lowerWinner:value.lowerWinner};
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
  if(path.startsWith("/match/")){await ensureLegacy();if(pageRoute!==path)return;buildSimulation();}
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
  stopCausalPlayer();
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
  document.body.classList.toggle("unified-home", pageRoute === "/" && tab === "player");
  if (pageRoute === "/") home();
  else if (pageRoute === "/channel") channelPage();
  else if (/^\/match\/[01]$/.test(pageRoute))
    reviewPage(Number(pageRoute.split("/")[2]));
  else if (pageRoute === "/compare") comparePage();
  else if (pageRoute === "/archive") archivePage();
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
    `10/17  ${personalFixture().upperLoser} ${draft.lfScore.join(":")} ${personalFixture().lowerWinner}`,
    400,
    620,
  );
  ctx.fillText(
    `10/18  ${personalFixture().upperWinner} ${draft.gfScore.join(":")} ${draft.lfWinner}`,
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
let legacyLoad;
async function ensureLegacy(){
 legacyLoad??=(async()=>{const fetchJSON=async path=>{const r=await fetch(path);if(!r.ok)throw Error('历史资料读取失败');return r.json();};[modelManifest,fictionManifest,fictionContext]=await Promise.all(['data/model-forecasts.json','data/model-fiction.json','data/fiction-context.json'].map(fetchJSON));[forecasts,fiction]=await Promise.all([modelManifest,fictionManifest].map(async entries=>Object.fromEntries(await Promise.all(Object.entries(entries).map(async([id,p])=>[id,await fetchJSON('data/'+p)])))));forecast=forecasts.codex;})();await legacyLoad;
}
async function start() {
  try {
    const fetchJSON = async (url) => {
      const response = await fetch(url, { cache: "no-cache" });
      if (!response.ok) throw Error("HTTP " + response.status);
      return response.json();
    };
    [event,assets,officialCurrent,evidencePack,currentData,currentAgents,currentMapArt,archiveData]=await Promise.all(["data/event.json","data/assets.json","data/official-current.json","data/evidence-v2.json","data/current-results.json","data/causal/agents.json","data/causal/map-art.json","data/archive/2026-10-17.json"].map(fetchJSON));
    causalAvailability=(await fetchJSON('data/causal/models.json')).models;
    for(const [id,row] of Object.entries(causalAvailability))if(row.sha256!==currentData.models[id]?.source_sha256)throw Error('当前结果与原始模型摘要不一致');
    if(!causalAvailability[selected]?.file)selected='codex';
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
      draftScenario={upperWinner:pick.upperWinner,lowerWinner:pick.lowerWinner};
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
      savedPickIncompatible=true;
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
