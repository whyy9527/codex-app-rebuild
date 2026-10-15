// Derive source requirements from saved actual AX, preserving original receipts.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {predictionFacts} from './prediction_native.mjs';

const [reference, output] = process.argv.slice(2);
const root = path.resolve(import.meta.dirname, '../../..');
function inside(value) {
  const absolute = path.resolve(root, value);
  const relative = path.relative(root, absolute);
  if (relative.startsWith('..') || path.isAbsolute(relative)) throw Error('Evidence must stay in worktree');
  return absolute;
}
if (!reference || !output) throw Error('Usage: node freeze_prediction.mjs reference.json private/contract.json');
const target = inside(output);
if (!target.endsWith('.json')) throw Error('Contract output must end in .json');
if (!path.relative(root, target).split(path.sep).includes('private')) throw Error('Expanded source text must stay private');
const raw = await fs.readFile(inside(reference));
const observed = JSON.parse(raw), requirements = [];
if (observed.error) throw Error('Failed source replay cannot define the contract');
for (const [name, state] of Object.entries(observed.states)) {
  const ax = await fs.readFile(inside(state.ax), 'utf8');
  const address = ax.split('\n').find(s => /smart search field|Address and search bar/.test(s)) || '';
  if (!address.includes('Value: https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html')) {
    throw Error('Source address evidence required for ' + name);
  }
  const actual = predictionFacts(ax);
  Object.assign(state, actual);
  for (const [i, text] of [...new Set(actual.accessible_text)].entries()) {
    if (text) requirements.push({id: name + '.text.' + i, state: name, kind: 'accessible_text', text, evidence: [state.ax]});
  }
  for (const [element, facts] of Object.entries(actual.elements)) for (const field of ['checked', 'enabled']) {
    if (field in facts) requirements.push({id: name + '.' + field + '.' + element, state: name,
      kind: 'element_boolean', element, field, expected: facts[field], evidence: [state.ax]});
  }
  const capture = state.capture;
  requirements.push({id: name + '.pixels', state: name, kind: 'image_pixels', reference_image: state.image,
    pixels: capture.content_rect_points.slice(2), reference_capture: Object.fromEntries(
      ['content_rect_points', 'backing_scale', 'window_points'].map(k => [k, capture[k]])), evidence: [state.image]});
}
const digest = crypto.createHash('sha256').update(raw).digest('hex');
observed.derivation = {source_observation: reference, sha256: digest,
  method: 'Reparse saved AX with the shared native fact extractor; repeated toggle labels retain occurrence IDs. Original screenshots and receipt unchanged.'};
const contract = {schema_version: 1, source_observation_sha256: digest,
  scope: 'Official deterministic PI: empty draw, winner change, all six matches and reload; no random Swiss, account permission or final saved score claim.', requirements};
await fs.writeFile(target, JSON.stringify(contract, null, 2) + '\n', {flag: 'wx'});
const parsed = target.replace(/\.json$/, '') + '.reference.json';
await fs.writeFile(parsed, JSON.stringify(observed, null, 2) + '\n', {flag: 'wx'});
console.log(JSON.stringify({contract: path.relative(root, target), parsed_reference: path.relative(root, parsed), requirements: requirements.length}));
