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
