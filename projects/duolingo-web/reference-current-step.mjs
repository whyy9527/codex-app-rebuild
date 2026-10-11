// Decisions from visible current-page facts, never the initial/future sequence.
export function currentFlowDecision(facts, labels) {
  if (!['/lesson','/practice'].includes(facts.path)) return {kind:'uncovered_state',reason:'Outside observed exercise route'};
  if (facts.dialog_count) return {kind:'uncovered_state',reason:'Visible dialog requires observation'};
  if (facts.challenge_count===1 && facts.challenge_visible && facts.next_text===labels.check)
    return {kind:'challenge'};
  const intros=['哎哟不错哦！要不要玩点刺激的？','一起来复习一下之前你不太熟练的部分吧！'];
  const intro=intros.find(text=>facts.body_text.includes(text));
  if (facts.challenge_count===0 && facts.heading_count===0 && intro &&
      facts.continue_count===1 && facts.continue_enabled)
    return {kind:'interlude',text:intro};
  return {kind:'uncovered_state',reason:'Current page is neither a ready challenge nor an observed exercise introduction'};
}

export function keyboardTranslationValue(challenge, facts) {
  if (challenge.type!=='translate' || (challenge.choices??[]).length) return null;
  if (facts.textbox_count!==1 || !facts.textbox_enabled || facts.bank_count!==0)
    throw Error('Empty-choice translation requires one actual enabled text field and no word bank');
  const value=challenge.correctSolutions?.[0];
  if (typeof value!=='string' || !value.trim()) throw Error('Current keyboard translation has no public solution');
  return value;
}
