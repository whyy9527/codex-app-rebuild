import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { fictionFor, aggregateFictionPlayers } from '../fiction.mjs';

test('fiction is absent for pending, stale or different simulated outcomes', () => {
  const dataset = JSON.parse(fs.readFileSync(new URL('../data/codex-fiction.json', import.meta.url)));
  const row = dataset.cases.VIT_100T_1, scenario = row.input.scenario, series = row.input.series;
  assert.equal(fictionFor(dataset, scenario, 1, series, dataset.event_source_sha256), row);
  assert.equal(fictionFor(null, scenario, 1, series, dataset.event_source_sha256), null);
  assert.equal(fictionFor(dataset, scenario, 1, series, 'new-official-snapshot'), null);
  assert.equal(fictionFor(dataset, scenario, 1, { ...series, score:[0,3] }, dataset.event_source_sha256), null);
});

test('fiction leaderboard averages only the series a player actually appears in', () => {
  const rows = aggregateFictionPlayers([
    {players:{'A:one':{rating:9,comment:'first'},'B:two':{rating:8,comment:'only'}}},
    {players:{'A:one':{rating:5,comment:'second'},'C:three':{rating:7.5,comment:'only'}}},
  ]);
  assert.deepEqual(rows.map(r=>[r.id,r.rating,r.appearances.length]), [['B:two',8,1],['C:three',7.5,1],['A:one',7,2]]);
  assert.deepEqual(aggregateFictionPlayers([null,null]), []);
});
