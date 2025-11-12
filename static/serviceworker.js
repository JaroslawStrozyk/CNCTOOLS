// static/serviceworker.js

// Ten prosty event listener jest wystarczający, aby przeglądarka
// uznała Service Worker za prawidłowy.
self.addEventListener('fetch', (event) => {
  // Na razie nie robimy nic specjalnego z żądaniami sieciowymi.
});
