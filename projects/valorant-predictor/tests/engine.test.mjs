import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  seriesDistribution,
  seriesProbability,
  mapProbability,
  validScore,
  validatePick,
  simulateSeries,
  teamStats,
} from "../engine.mjs";
const event = JSON.parse(
  readFileSync(new URL("../data/event.json", import.meta.url)),
);
const forecast = JSON.parse(
  readFileSync(new URL("../data/gpt-6.1-sol-forecast.json", import.meta.url)),
);
test("BO5 exact distribution conserves probability and swaps teams", () => {
  for (const p of [0, 0.13, 0.5, 0.77, 1]) {
    const rows = seriesDistribution(p);
    assert.ok(
      Math.abs(rows.reduce((s, r) => s + r.probability, 0) - 1) < 1e-12,
    );
    assert.ok(
      Math.abs(seriesProbability(p) + seriesProbability(1 - p) - 1) < 1e-12,
    );
  }
  assert.equal(seriesProbability(0.5), 0.5);
  assert.throws(() => seriesProbability(NaN));
});
test("official snapshot retains two unique BO5 targets and no future results", () => {
  assert.deepEqual(
    event.matches.map((m) => m.start_utc.slice(0, 10)),
    ["2026-10-17", "2026-10-18"],
  );
  assert.ok(event.matches.every((m) => m.best_of === 5));
  assert.ok(
    event.history.every((m) => m.state === "completed" && m.score && m.winner),
  );
  assert.equal(
    new Set(event.history.map((m) => m.id)).size,
    event.history.length,
  );
  assert.deepEqual(teamStats(event, "VIT"), {
    played: 4,
    wins: 4,
    mapsWon: 8,
    mapsLost: 2,
  });
});
test("pick rejects inconsistent downstream bracket and illegal BO5 scores", () => {
  const p = {
    version: 1,
    source_sha256: event.source_sha256,
    upperWinner: "VIT",
    lowerWinner: "100T",
    lfWinner: "LOUD",
    lfScore: [3, 1],
    champion: "VIT",
    gfScore: [3, 2],
    created_at: "2026-10-15T11:00:00Z",
  };
  assert.ok(validatePick(p, event));
  for (const score of [
    [3, 3],
    [2, 1],
    [-1, 3],
    [3, 1.2],
  ])
    assert.equal(validScore(score), false);
  assert.equal(validatePick({ ...p, lfWinner: "G2" }, event), false);
  assert.equal(validatePick({ ...p, champion: "100T" }, event), false);
  assert.equal(validatePick({ ...p, lfScore: [1, 3] }, event), false);
  assert.ok(
    validatePick(
      {
        ...p,
        match_ids: event.matches.map((m) => m.id),
        source_sha256: "a".repeat(64),
      },
      event,
    ),
  );
  assert.equal(
    validatePick({ ...p, match_ids: ["other", "event"] }, event),
    false,
  );
  assert.equal(validatePick({ ...p, created_at: "invalid" }, event), false);
});
test("missing AI forecasts remain absent and simulation stops at three map wins", () => {
  assert.equal(mapProbability(forecast, "VIT", "UNKNOWN"), null);
  for (let seed = 0; seed < 100; seed++) {
    const result = simulateSeries("A", "B", 0.55, seed);
    assert.ok(validScore(result.score));
    assert.ok(result.maps.length >= 3 && result.maps.length <= 5);
    assert.deepEqual(result, simulateSeries("A", "B", 0.55, seed));
  }
});

test("custom ranking preserves teams and gives reciprocal, ordered probabilities", async () => {
  const { validRanking, rankingProbability, moveRanking } = await import(
    "../engine.mjs"
  );
  const teams = ["VIT", "LOUD", "100T", "G2"];
  assert.ok(validRanking(teams, teams));
  assert.equal(validRanking(["VIT", "VIT", "100T", "G2"], teams), false);
  assert.deepEqual(moveRanking(teams, 3, 0), ["G2", "VIT", "LOUD", "100T"]);
  assert.deepEqual(teams, ["VIT", "LOUD", "100T", "G2"]);
  for (let first = 0; first < teams.length; first++)
    for (let second = 0; second < teams.length; second++)
      if (first !== second) {
        const p = rankingProbability(teams, teams[first], teams[second]);
        assert.ok(
          Math.abs(
            p + rankingProbability(teams, teams[second], teams[first]) - 1,
          ) < 1e-12,
        );
        assert.equal(p > 0.5, first < second);
      }
  assert.throws(() => rankingProbability(teams, "VIT", "UNKNOWN"));
  assert.throws(() => simulateSeries("VIT", "LOUD", null, 1));
});

test("conditional series probability agrees at the start and reaches exact terminal values", async () => {
  const { remainingSeriesProbability: chance } = await import("../engine.mjs");
  for (const p of [0, 0.1, 0.5, 0.9, 1]) {
    assert.ok(Math.abs(chance([0, 0], p) - seriesProbability(p)) < 1e-12);
    assert.equal(chance([3, 2], p), 1);
    assert.equal(chance([1, 3], p), 0);
    assert.equal(chance([2, 2], p), p);
  }
  assert.throws(() => chance([3, 3], 0.5));
  assert.throws(() => chance([1, -1], 0.5));
});
