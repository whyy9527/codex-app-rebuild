// The author bar consumes the same public author snapshot as the host sidebar.
let responses;
const read = () => responses ||= fetch('/content/host/responses.json').then(r => {
  if (!r.ok) throw new Error('Author snapshot unavailable');
  return r.json();
});
window.toy = {
  isSupport: async name => ['getAuthorProfile', 'getAuthorRelation'].includes(name),
  getAuthorProfile: async () => (await read())['/x/toy/sdk/author/profile'].data,
  getAuthorRelation: async () => {
    const action = (await read())['/x/toy/detail'].data.user_action;
    return {status: 'ok', data: {isFollowing: !!action.follow, hasFanMedal: false, isSeniorFan: false}};
  }
};
