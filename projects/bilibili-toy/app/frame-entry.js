// Preserve the original share-entry query before the app starts its router.
const contentFrame = document.querySelector('.toy-shell-stage iframe');
contentFrame.src = '/content/index.html' + window.location.search;
