export function mapProbability(forecast, a, b) {
  if (a === b) throw Error("两队不能相同");
  const pair = forecast.pairs.find(
    (r) => r.teams.includes(a) && r.teams.includes(b),
  );
  if (!pair) return null;
  return pair.teams[0] === a ? pair.p_first : 1 - pair.p_first;
}
export function seriesDistribution(p, bestOf = 5) {
  if (!Number.isFinite(p) || p < 0 || p > 1 || bestOf !== 5)
    throw Error("需要合法单图概率和 BO5 赛制");
  const choose = (n, k) => {
    let c = 1;
    for (let i = 1; i <= k; i++) c = (c * (n - k + i)) / i;
    return c;
  };
  const rows = [];
  for (let k = 0; k < 3; k++) {
    rows.push({
      score: [3, k],
      probability: choose(2 + k, k) * p ** 3 * (1 - p) ** k,
    });
    rows.push({
      score: [k, 3],
      probability: choose(2 + k, k) * (1 - p) ** 3 * p ** k,
    });
  }
  return rows;
}
export function seriesProbability(p) {
  return seriesDistribution(p)
    .filter((r) => r.score[0] === 3)
    .reduce((s, r) => s + r.probability, 0);
}
// Exact two-series tree, conditional on the chosen preceding-day qualifiers.
// pUpperA/B are the upper finalist's single-map chances against each lower team.
export function finalsProbabilities(pLower, pUpperA, pUpperB) {
  const lowerA = seriesProbability(pLower),
    upperA = seriesProbability(pUpperA),
    upperB = seriesProbability(pUpperB);
  return [
    lowerA * upperA + (1 - lowerA) * upperB,
    lowerA * (1 - upperA),
    (1 - lowerA) * (1 - upperB),
  ];
}
// Conditional chance of winning the series after the observed map score.
export function remainingSeriesProbability(score, p) {
  if (
    !Array.isArray(score) ||
    score.length !== 2 ||
    score.some((n) => !Number.isInteger(n) || n < 0 || n > 3) ||
    score.every((n) => n === 3) ||
    !Number.isFinite(p) ||
    p < 0 ||
    p > 1
  )
    throw Error("需要合法 BO5 比分与单图概率");
  const chance = (a, b) =>
    a === 3
      ? 1
      : b === 3
        ? 0
        : p * chance(a + 1, b) + (1 - p) * chance(a, b + 1);
  return chance(...score);
}
export function teamStats(event, code) {
  const matches = event.history.filter((m) => m.teams.includes(code));
  return {
    played: matches.length,
    wins: matches.filter((m) => m.winner === code).length,
    mapsWon: matches.reduce((s, m) => s + m.score[m.teams.indexOf(code)], 0),
    mapsLost: matches.reduce(
      (s, m) => s + m.score[1 - m.teams.indexOf(code)],
      0,
    ),
  };
}
export function baselineProbability(event, a, b) {
  const strength = (c) => {
    const s = teamStats(event, c);
    return (s.mapsWon + 1) / (s.mapsLost + 1);
  };
  return strength(a) / (strength(a) + strength(b));
}
export function validScore(value) {
  return (
    Array.isArray(value) &&
    value.length === 2 &&
    value.every(Number.isInteger) &&
    ((value[0] === 3 && value[1] >= 0 && value[1] < 3) ||
      (value[1] === 3 && value[0] >= 0 && value[0] < 3))
  );
}
export function validatePick(pick, event) {
  if (
    !pick ||
    pick.version !== 1 ||
    typeof pick.source_sha256 !== "string" ||
    !/^[a-f0-9]{64}$/.test(pick.source_sha256)
  )
    return false;
  if (
    pick.match_ids
      ? JSON.stringify(pick.match_ids) !==
        JSON.stringify(event.matches.map((m) => m.id))
      : pick.source_sha256 !== event.source_sha256
  )
    return false;
  const upper = event.predecessors[0].teams,
    lower = event.predecessors[1].teams;
  if (!upper.includes(pick.upperWinner) || !lower.includes(pick.lowerWinner))
    return false;
  const loser = upper.find((c) => c !== pick.upperWinner);
  if (
    ![loser, pick.lowerWinner].includes(pick.lfWinner) ||
    !validScore(pick.lfScore) ||
    !validScore(pick.gfScore)
  )
    return false;
  const lfWinner = pick.lfScore[0] === 3 ? loser : pick.lowerWinner;
  const gfWinner = pick.gfScore[0] === 3 ? pick.upperWinner : lfWinner;
  return (
    pick.lfWinner === lfWinner &&
    pick.champion === gfWinner &&
    typeof pick.created_at === "string" &&
    Number.isFinite(Date.parse(pick.created_at))
  );
}
export function seededRandom(seed) {
  let n = seed >>> 0;
  return () => {
    n = (1664525 * n + 1013904223) >>> 0;
    return n / 4294967296;
  };
}
export function simulateSeries(a, b, p, seed) {
  if (a === b || !Number.isFinite(p) || p < 0 || p > 1)
    throw Error("需要两支战队与合法单图概率");
  const random = seededRandom(seed),
    score = [0, 0],
    maps = [];
  while (Math.max(...score) < 3) {
    const winner = random() < p ? 0 : 1;
    score[winner]++;
    maps.push({ winner: winner === 0 ? a : b, score: [...score] });
  }
  return { teams: [a, b], score, maps, winner: score[0] === 3 ? a : b };
}

export function validRanking(order, teams) {
  return (
    Array.isArray(order) &&
    order.length === teams.length &&
    new Set(order).size === teams.length &&
    teams.every((team) => order.includes(team))
  );
}

export function rankingProbability(order, a, b) {
  const first = order.indexOf(a),
    second = order.indexOf(b);
  if (first < 0 || second < 0 || first === second)
    throw Error("排名必须包含两支不同的战队");
  // The reference uses this same logistic conversion for custom ranking.
  return 1 / (1 + Math.exp(-(second - first) * 0.122));
}

export function moveRanking(order, from, to) {
  if (
    !Number.isInteger(from) ||
    !Number.isInteger(to) ||
    from < 0 ||
    to < 0 ||
    from >= order.length ||
    to >= order.length
  )
    throw Error("排名位置无效");
  const next = [...order],
    [team] = next.splice(from, 1);
  next.splice(to, 0, team);
  return next;
}

// Conditional on the frozen ordered map/side probabilities, independent maps.
// No team strength, map weighting or model probability is inferred here.
export function mapSeriesDistribution(maps, score = [0, 0]) {
  if (!Array.isArray(maps) || maps.length !== 5 ||
      maps.some(m => !m || typeof m.map !== 'string' || !m.map || !['ATK', 'DEF'].includes(m.a_start_side) || typeof m.p_first !== 'number' || !Number.isFinite(m.p_first) || m.p_first < 0 || m.p_first > 1) ||
      new Set(maps.map(m => m.map)).size !== 5 ||
      !Array.isArray(score) || score.length !== 2 || score.some(n => !Number.isInteger(n) || n < 0 || n > 3) || score.every(n => n === 3)) throw Error('需要五张不同地图的冻结概率、起始边及合法 BO5 比分');
  const outcomes = new Map();
  const visit = (a, b, probability) => {
    if (a === 3 || b === 3) {
      const key = `${a}:${b}`;
      outcomes.set(key, (outcomes.get(key) || 0) + probability);
      return;
    }
    const p = maps[a + b].p_first;
    visit(a + 1, b, probability * p);
    visit(a, b + 1, probability * (1 - p));
  };
  visit(...score, 1);
  return [...outcomes].map(([key, probability]) => ({score: key.split(':').map(Number), probability}));
}
export function simulateMapSeries(teams, maps, seed) {
  mapSeriesDistribution(maps);
  if (!Array.isArray(teams) || teams.length !== 2 || teams[0] === teams[1]) throw Error('需要两支不同队伍');
  const random = seededRandom(seed), score = [0, 0], played = [];
  for (const map of maps) {
    const draw = random(), winnerIndex = draw < map.p_first ? 0 : 1;
    score[winnerIndex]++;
    played.push({...map, random_draw: draw, winner: teams[winnerIndex]});
    if (score[winnerIndex] === 3) break;
  }
  return {teams, score, maps: played, winner: teams[score[0] === 3 ? 0 : 1]};
}
