// Preserve the original share-entry query before the app starts its router.
const contentFrame = document.querySelector('.toy-shell-stage iframe');
// Original share shells open a fixed match/world route; their outer query does
// not replace it. The server supplies only routes present in the published data.
contentFrame.src = '/content/index.html' + (contentFrame.dataset.entryHash || window.location.search);
