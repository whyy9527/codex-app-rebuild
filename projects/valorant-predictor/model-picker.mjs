const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let models=[];
export function configureModelCards(channels,assets){models=channels.map(c=>({...c,portrait:assets.models[c.id].portrait}));}
export function modelCards(id,selected,{home=false,details=()=>''}={}){
 return `<div id="${id}" class="model-card-grid ${home?'model-deck channels portraits':''}" role="group" aria-label="选择模型">${models.map(c=>`<button type="button" class="model-choice ${home?'home-model channel portrait':''} ${selected===c.id?'on':''}" data-model-choice="${c.id}" ${home?`data-channel="${c.id}" data-tactical-model="${c.id}"`:''} aria-pressed="${selected===c.id}"><img class="model-portrait" src="${esc(c.portrait)}" alt=""><div class="model-overview">${details(c)}<h2>${esc(c.name)}</h2>${home?'<span data-tactical-status hidden></span>':''}</div></button>`).join('')}</div>`;
}
export function mountModelCards(id,onChange){
 const root=document.getElementById(id);if(!root)return;
 const buttons=[...root.querySelectorAll('[data-model-choice]')];
 const choose=button=>{for(const b of buttons){b.classList.toggle('on',b===button);b.setAttribute('aria-pressed',String(b===button));}const value=button.dataset.modelChoice;onChange(value);queueMicrotask(()=>document.getElementById(id)?.querySelector(`[data-model-choice="${value}"]`)?.focus({preventScroll:true}));};
 buttons.forEach((button,index)=>{button.onclick=()=>choose(button);button.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(e.key))return;e.preventDefault();const step=['ArrowLeft','ArrowUp'].includes(e.key)?-1:1;const target=e.key==='Home'?0:e.key==='End'?buttons.length-1:(index+step+buttons.length)%buttons.length;choose(buttons[target]);};});
}
