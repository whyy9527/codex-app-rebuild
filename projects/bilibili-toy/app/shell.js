// Host-only controls are separate from the locally served published application.
// Their exact source behavior remains unverified; do not mutate a live Bilibili account.
const dialog=document.querySelector('#shell-dialog');
const content=document.querySelector('#shell-dialog-content');
const source='https://www.bilibili.com/toy/LkvCZhw12wgT2Pqx/index.html';
const paths={
  like:'M7 10v11H3V10h4zm0 1 5-8c2 0 2 2 2 3l-1 4h6c2 0 2 1 2 3l-2 7c0 1-1 1-2 1H7',
  comment:'M21 11a9 8 0 0 1-9 8H9l-5 3 1-6a8 8 0 1 1 16-5Z',
  favorite:'m12 3 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z',
  share:'m14 3 7 7-7 7v-4C8 13 5 16 3 20c0-8 3-12 11-13V3Z',
  recent:'M4 5v5h5M4 10a9 9 0 1 1 0 5m8-9v6l-3 2',
  created:'M9 18h6m-5 3h4M8 15c-6-7-1-13 4-13s10 6 4 13l-1 3H9l-1-3Z',
  install:'M9 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9M16 2v8m-4-4h8',
  game:'M7 8h10c5 0 6 12 3 12l-4-4H8l-4 4C1 20 2 8 7 8Zm1 2v5m-3-3h6m5 0h.1m3 2h.1'
};
for(const holder of document.querySelectorAll('.toy-shell-sidebar .icon')){
  const control=holder.closest('[data-dialog],a');const name=control.dataset.dialog||'game';
  holder.innerHTML=`<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="${paths[name]||paths.game}"/></svg>`;
}
document.querySelector('.close').addEventListener('click',()=>dialog.close());
for(const button of document.querySelectorAll('[data-dialog]'))button.addEventListener('click',()=>{
  const action=button.dataset.dialog;
  const titles={detail:'S16AI预测大赛',like:'点赞',comment:'评论',favorite:'收藏',share:'分享',recent:'近期玩过',created:'我创作的',install:'添加到桌面'};
  content.replaceChildren();
  const h=document.createElement('h2');h.textContent=titles[action];content.append(h);
  if(action==='share'){
    const field=document.createElement('input');field.value=source;field.readOnly=true;field.setAttribute('aria-label','分享链接');content.append(field);
    const copy=document.createElement('button');copy.textContent='复制链接';copy.onclick=async()=>{await navigator.clipboard.writeText(source);copy.textContent='已复制'};content.append(copy);
  }else{
    const p=document.createElement('p');p.textContent='Bilibili 平台功能需在原站使用。';content.append(p);
    const a=document.createElement('a');a.href=source;a.target='_blank';a.rel='noreferrer';a.textContent='前往 Bilibili 原站';content.append(a);
  }
  dialog.showModal();
});
