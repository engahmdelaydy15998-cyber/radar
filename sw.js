// رادار service worker: pages network-first (so updates show), assets cache-first, data.json network-first.
var CACHE = "radar-v4";
var SHELL = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png"];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(SHELL); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

function networkFirst(req, key) {
  return fetch(req).then(function (res) {
    var copy = res.clone();
    caches.open(CACHE).then(function (c) { c.put(key || req, copy); });
    return res;
  }).catch(function () { return caches.match(key || req, { ignoreSearch: true }); });
}

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);
  if (url.origin !== location.origin) return;

  var isPage = req.mode === "navigate" || url.pathname.slice(-1) === "/" || url.pathname.slice(-5) === ".html";
  if (isPage) {
    // A share-target visit carries ?url=...; cache the shell under a clean key so it is not stored per link.
    e.respondWith(networkFirst(req, new Request(url.origin + url.pathname)));
    return;
  }
  if (url.pathname.slice(-9) === "data.json") {
    e.respondWith(networkFirst(req));
    return;
  }
  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then(function (hit) {
      return hit || fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copy); });
        return res;
      });
    })
  );
});
