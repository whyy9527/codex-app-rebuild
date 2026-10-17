const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function formalPredictions(result){
 if(!result)return [];
 return Object.entries(result.computed.cases).map(([key,c])=>{
  const first=c.distribution.filter(row=>row.score[0]===3).reduce((sum,row)=>sum+row.probability,0);
  const highest=Math.max(...c.distribution.map(row=>row.probability));
  return {key,teams:c.teams,win:[first,1-first],favorite:c.teams[first>=.5?0:1],
   modes:c.distribution.filter(row=>Math.abs(row.probability-highest)<1e-12),distribution:c.distribution};
 });
}

export function playerMarkup(models){
 return `<section class="prediction-player" id="prediction-player" data-status="awaiting-new-chain" aria-label="AI连续推演"><div class="player-models">${models}</div><div class="player-now"><span>逐步比赛推演</span><span>共同赛前资料已冻结</span></div><div class="player-controls"><button disabled aria-label="上一段">←</button><button class="player-play" disabled>等待模型推演</button><button disabled aria-label="下一段">→</button><label class="player-scrub"><span class="sr-only">推演进度</span><input type="range" disabled value="0" aria-label="推演进度"><output>00:00</output></label></div><div class="player-pending"><span>BP → 选边与阵容 → 同图局面 → 结果</span><h2>逐步推演待生成</h2><p>每步将根据上一局面继续决策，比分由模拟过程产生。</p><ol><li><b>01</b> 地图禁选 <small>待决策</small></li><li><b>02</b> 选边与阵容 <small>待决策</small></li><li><b>03</b> 回合内决策 <small>待决策</small></li><li><b>04</b> 比分与下一局面 <small>待决策</small></li></ol></div><details class="player-notes"><summary>输入与当前进度</summary><div><p id="pending-model"></p><p>状态契约与免费测试已准备；真实逐步模型输出尚未运行，当前没有可播放的新链。</p><p><a href="data/evidence-v2.json" target="_blank">共同冻结赛前资料 ↗</a></p></div></details></section>`;
}
export function mountPendingPlayer(model){
 const label={codex:'GPT-6.1 sol',deepseek:'DeepSeek V4.1 Flash',doubao:'豆包',mimo:'MiMo V2.6 Pro'};
 document.querySelector('#prediction-player').dataset.model=model;
 document.querySelector('#pending-model').textContent=(label[model]||model)+' · 新逐步推演尚未生成';
}
