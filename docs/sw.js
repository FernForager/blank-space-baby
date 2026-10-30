// Offline copy, so the game loads at the field with no signal.
// The page comes from the network first, so updates land right away. If the network fails, answers with an error,
// or takes over 3 seconds, the saved copy loads instead. Everything else (fonts, icons) comes from the saved copy first.
// Caches belong to the whole address, and fernforager.github.io holds Morg's other games too, so this worker only ever
// deletes its own old caches, the ones named bsb- (the audit, Oct 30, 2026).
var CACHE = 'bsb-v5';
var CORE = ['./', 'manifest.webmanifest', 'icon-192.png', 'apple-touch-icon.png'];
var ROOT = new URL('./', self.location).href;   // the game's own page, the only page kept as the offline copy

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(CORE); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k.indexOf('bsb-') === 0 && k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener('fetch', function (e) {
  var r = e.request;
  if (r.method !== 'GET' || new URL(r.url).pathname.indexOf('/api/') === 0) return;   // the beta's flag and lock calls always go to the network
  if (r.mode === 'navigate') {
    var page = r.url.split(/[?#]/)[0], game = page === ROOT || page === ROOT + 'index.html';
    var saved = function () { return game ? caches.match('./') : Promise.resolve(); };
    var net = fetch(r);
    e.waitUntil(net.then(function (res) {   // keep only the game's own page, and only a good one
      if (game && res.ok && (res.headers.get('content-type') || '').indexOf('text/html') === 0) {
        var copy = res.clone(); return caches.open(CACHE).then(function (c) { return c.put('./', copy); });
      }
    }).catch(function () {}));
    e.respondWith(new Promise(function (resolve) {
      var done = false;
      function use(res) { if (!done && res) { done = true; resolve(res); } }
      var slow = setTimeout(function () { saved().then(use); }, 3000);
      net.then(function (res) {
        clearTimeout(slow);
        if (res.ok) use(res); else saved().then(function (m) { use(m || res); });   // an error page: the saved game if there is one
      }).catch(function () {
        clearTimeout(slow); saved().then(function (m) { use(m || Response.error()); });
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
