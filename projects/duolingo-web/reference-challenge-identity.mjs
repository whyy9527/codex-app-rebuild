// Compare API expectations with independently read current UI before any answer.
// Option order can be shuffled; multiplicity must remain the same.
export function challengeIdentity(expected, actual) {
  const normalize = value => String(value ?? '').normalize('NFKC').replace(/\s+/g, ' ').trim();
  const multiset = values => values.map(normalize).sort();
  const choices = expected.type === 'match'
    ? expected.pairs.flatMap(p => [p.fromToken, p.learningToken])
    : (expected.choices ?? []).map(c => typeof c === 'string' ? c : c.phrase ?? c.text);
  const reasons = [];
  if (!actual.type.split(/\s+/).includes('challenge-' + expected.type)) reasons.push('type_changed');
  const expectedBank = multiset(choices), actualBank = multiset(actual.choices);
  if (JSON.stringify(expectedBank) !== JSON.stringify(actualBank)) reasons.push('choice_set_changed');
  // The visible container is broader than a dedicated prompt node. This is
  // evidence of presence, not exact prompt equality; retain that limitation.
  const exactPrompts = actual.prompts ?? [];
  if (expected.prompt && exactPrompts.length && !exactPrompts.some(p => normalize(p) === normalize(expected.prompt))) reasons.push('prompt_changed');
  else if (expected.prompt && !exactPrompts.length && !normalize(actual.text).includes(normalize(expected.prompt))) reasons.push('prompt_not_visible');
  return {matches: reasons.length === 0, reasons, expected: {type: expected.type, prompt: expected.prompt ?? null, choices},
    actual, prompt_check: exactPrompts.length ? 'normalized equality with independently read visible hint container' : 'normalized presence in current challenge text; exact prompt identity not yet proven'};
}
