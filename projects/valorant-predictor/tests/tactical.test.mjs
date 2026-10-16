import test from 'node:test';
import assert from 'node:assert/strict';
import { pointAt, phaseAt, DURATION, MAPS, LINEUPS } from '../tactical-replay.mjs';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

test('distance-based interpolation handles unequal legs, endpoints and stationary actors', () => {
  const path = [[0,0],[3,0],[3,4]];
  assert.deepEqual(pointAt(path, -1), [0,0]);
  assert.deepEqual(pointAt(path, 3 / 7), [3,0]);
  assert.deepEqual(pointAt(path, 5 / 7), [3,2]);
  assert.deepEqual(pointAt(path, 2), [3,4]);
  assert.deepEqual(pointAt([[2,2],[2,2]], 0.5), [2,2]);
});

test('scrubbing reversibly selects the correct narration phase including the end', () => {
  assert.equal(phaseAt(0), 0);
  assert.equal(phaseAt(8), 1);
  assert.equal(phaseAt(20), 2);
  assert.equal(phaseAt(DURATION), 3);
  assert.equal(phaseAt(5), 0);
});

test('each demo map has five bounded routes per side and traceable original game assets', () => {
  const manifest = JSON.parse(readFileSync(new URL('../data/tactical-assets.json', import.meta.url)));
  assert.equal(manifest.assets.length, 12);
  for (const map of Object.values(MAPS)) {
    for (const side of ['attack','defend']) {
      assert.equal(map[side].length, LINEUPS[side].length);
      assert.equal(map[side].length, 5);
      for (const path of map[side]) {
        assert.ok(path.length >= 2);
        for (const point of path) assert.ok(point.every(x => Number.isFinite(x) && x >= 0 && x <= 1000));
      }
    }
  }
  for (const asset of manifest.assets) {
    const bytes = readFileSync(new URL('../' + asset.path, import.meta.url));
    assert.equal(createHash('sha256').update(bytes).digest('hex'), asset.sha256);
  }
});
