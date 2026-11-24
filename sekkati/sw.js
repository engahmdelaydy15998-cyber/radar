// سكّتي service worker: الصفحة network-first (عشان التحديثات تظهر)، والأصول cache-first.
var CACHE = "sekkati-v50";
var SHELL = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "eg-pois.json", "rtl-text.js",
  "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css", "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"];
self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) {
    return Promise.all(SHELL.map(function (u) { return c.add(u).catch(function () {}); }));
  }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;
  var u = new URL(req.url);
  // الطرق والبحث والرادارات لازم تكون طازجة، وصور الخريطة يتولاها المتصفح
  if (/osrm|nominatim|photon|overpass|tile\.openstreetmap|cartocdn|openfreemap|arcgisonline|anthropic|fonts\./.test(u.hostname)) return;
  var isPage = req.mode === "navigate" || u.pathname.slice(-1) === "/" || u.pathname.slice(-5) === ".html" || u.pathname.slice(-5) === ".json";  // الصفحة وداتا الرادارات: الأحدث الأول
  e.respondWith(caches.open(CACHE).then(function (c) {
    if (isPage) {
      return fetch(req).then(function (res) { if (res && res.ok) c.put(req, res.clone()); return res; })
        .catch(function () { return c.match(req, { ignoreSearch: true }); });
    }
    return c.match(req).then(function (hit) {
      if (hit) return hit;
      return fetch(req).then(function (res) { if (res && res.ok) c.put(req, res.clone()); return res; });
    });
  }));
});
