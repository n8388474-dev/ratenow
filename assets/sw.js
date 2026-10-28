var V = 'rn-%V%';
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k !== V; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  e.respondWith(fetch(req).then(function (res) {
    var cp = res.clone();
    caches.open(V).then(function (c) { c.put(req, cp); });
    return res;
  }).catch(function () {
    return caches.match(req).then(function (r) { return r || caches.match(self.registration.scope); });
  }));
});
