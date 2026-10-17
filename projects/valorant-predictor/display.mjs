// Display names only. Raw forecast keys, values and resource URLs remain unchanged.
export const MAP_NAMES = Object.freeze({Ascent:'亚海悬城',Lotus:'莲华古城',Abyss:'幽邃地窟',Haven:'隐世修所',Summit:'天枢云阙',Sunset:'日落之城',Split:'霓虹町'});
const names = new Map(Object.entries(MAP_NAMES).map(([key,value])=>[key.toLowerCase(),value]));
// Exclude URLs and technical identifiers while allowing Chinese-adjacent prose.
const mapWord = /(?<![a-z0-9_/:.\-])(Ascent|Lotus|Abyss|Haven|Summit|Sunset|Split)(?![a-z0-9_/:\-]|\.[a-z0-9])/gi;
export const mapDisplay = value => String(value ?? '').replace(mapWord, key=>names.get(key.toLowerCase()));
export function installMapDisplay(root=document.body) {
  const skipped = 'script,style,pre,code,textarea,input,[data-raw-output]';
  const attrs = ['alt','title','aria-label'];
  const update = node => {
    if(node.nodeType===3) {
      const parent=node.parentElement;
      if(!parent || parent.closest(skipped))return;
      const translated=mapDisplay(node.data);
      if(translated===node.data)return;
      const option=parent.closest('option');
      if(option&&!option.hasAttribute('value'))option.setAttribute('value',option.value);
      node.data=translated;
    } else if(node.nodeType===1 && !node.closest(skipped)) {
      for(const attr of attrs)if(node.hasAttribute(attr)) {
        const old=node.getAttribute(attr),next=mapDisplay(old);
        if(old!==next)node.setAttribute(attr,next);
      }
      for(const child of node.childNodes)update(child);
    }
  };
  update(root);
  const observer=new MutationObserver(records=>{
    for(const record of records) {
      if(record.type==='childList')for(const node of record.addedNodes)update(node);
      else update(record.target);
    }
  });
  observer.observe(root,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:attrs});
  return ()=>observer.disconnect();
}
export const FINAL_START_UTC = '2026-10-18T06:00:00Z';
export function finalCountdown(now=Date.now()) {
  const seconds=Math.max(0,Math.ceil((Date.parse(FINAL_START_UTC)-now)/1000));
  if(!seconds)return '已到开赛时间';
  const days=Math.floor(seconds/86400),hours=Math.floor(seconds%86400/3600),minutes=Math.floor(seconds%3600/60),rest=seconds%60;
  return `距离决赛开赛 ${days?days+'天 ':''}${hours}时${minutes}分${rest}秒`;
}
export function mountFinalCountdown(element) {
  let timer;
  const update=()=>{element.textContent=finalCountdown();};
  const resume=()=>{clearInterval(timer);update();if(!document.hidden)timer=setInterval(update,1000);};
  document.addEventListener('visibilitychange',resume);
  resume();
  return ()=>{clearInterval(timer);document.removeEventListener('visibilitychange',resume);};
}
