// Route the published host's API reads to local public-data snapshots.
const originalFetch = window.fetch.bind(window);
window.fetch = (input, init) => {
  const url = new URL(typeof input === 'string' || input instanceof URL ? input : input.url, location.href);
  if (url.hostname === 'api.bilibili.com' || url.hostname === 'api.bilibili.co') {
    return originalFetch('/host-api' + url.pathname + url.search, {...init, credentials: 'omit'});
  }
  return originalFetch(input, init);
};
window.__TOY_META__ = {toy_id: 43482999941120};
window.__toyInstall = () => Promise.resolve({outcome: 'unavailable'});
window.reporterPb = {exposure(){},click(){}};
window.__BiliUser__ = {
  watch(){}, unWatch(){},
  quickLogin(callback){
    window.dispatchEvent(new CustomEvent('local-auth-request'));
    callback?.({message: 'cancel'});
  }
};
window.addEventListener('local-auth-request', () => {
  const dialog = document.querySelector('#local-auth');
  if (dialog && !dialog.open) dialog.showModal();
});
window.addEventListener('DOMContentLoaded', () => {
  document.querySelector('#local-auth-close')?.addEventListener('click', () => document.querySelector('#local-auth').close());
});
