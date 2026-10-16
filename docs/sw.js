// Offline copy, so the game loads at the field with no signal.
// The page comes from the network first, so updates land right away. If the network fails,
// or takes over 3 seconds, the saved copy loads instead. Everything else (fonts, icons) comes
// from the saved copy first.
var CACHE = 'bsb-v3';
var CORE = ['./', 'manifest.webmanifest', 'icon-192.png', 'apple-touch-icon.png'];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(CORE); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener('fetch', function (e) {
  var r = e.request;
  if (r.method !== 'GET' || new URL(r.url).pathname.indexOf('/api/') === 0) return;   // the beta's flag and lock calls always go to the network
  if (r.mode === 'navigate') {
    e.respondWith(new Promise(function (resolve) {
      var done = false;
      function use(res) { if (!done && res) { done = true; resolve(res); } }
      var slow = setTimeout(function () { caches.match('./').then(use); }, 3000);
      fetch(r).then(function (res) {
        if (res.ok) { var copy = res.clone(); caches.open(CACHE).then(function (c) { c.put('./', copy); }); }
        clearTimeout(slow); use(res);
      }).catch(function () {
        clearTimeout(slow); caches.match('./').then(function (m) { use(m || Response.error()); });
      });
    }));
    return;
  }
  e.respondWith(caches.match(r).then(function (m) {
    return m || fetch(r).then(function (res) {
      if (res.ok || res.type === 'opaque') { var copy = res.clone(); caches.open(CACHE).then(function (c) { c.put(r, copy); }); }
      return res;
    });
  }));
});
