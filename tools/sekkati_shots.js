// Screenshots of the real app with real map tiles (GitHub runner has internet; the dev sandbox doesn't).
// Writes sekkati/ai-review/shots/*.png: day map, night map, driving (day/night), after a manual zoom, and the trip minimised.
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..'), OUT = path.join(ROOT, 'sekkati/ai-review/shots');
fs.mkdirSync(OUT, { recursive: true });
const TYPES = { '.html': 'text/html', '.js': 'application/javascript', '.json': 'application/json', '.png': 'image/png', '.webmanifest': 'application/json' };
const srv = http.createServer((q, s) => {
  let f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html';
  fs.readFile(f, (e, d) => { if (e) { s.writeHead(404); s.end(); return; } s.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'text/plain' }); s.end(d); });
}).listen(8090);
const wait = ms => new Promise(r => setTimeout(r, ms));
// Corniche el Nil, Maadi -> Garden City (heading roughly north)
const PATH = Array.from({ length: 40 }, (_, i) => [29.9890 + i * 0.00045, 31.2310 - i * 0.00004]);

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, locale: 'ar-EG' });
  await ctx.addInitScript(() => {
    window.__cb = null;
    navigator.geolocation.watchPosition = cb => { window.__cb = cb; return 7; };
    navigator.geolocation.getCurrentPosition = cb => cb({ timestamp: Date.now(), coords: { latitude: 29.989, longitude: 31.231, accuracy: 5 } });
    navigator.geolocation.clearWatch = () => {};
    try { localStorage.setItem('spotsInit', 'true'); } catch (e) {}
  });
  const page = await ctx.newPage(); const errs = [];
  page.on('pageerror', e => errs.push(String(e)));
  const idle = async (ms = 9000) => { await page.evaluate(() => new Promise(r => { try { if (map.loaded()) return setTimeout(r, 400); map.once('idle', () => r()); } catch (e) { r(); } setTimeout(r, 8000); })); await wait(ms); };
  const shot = async n => { await page.screenshot({ path: path.join(OUT, n + '.png') }); console.log('shot', n); };

  await page.goto('http://localhost:8090/sekkati/');
  await page.evaluate(() => { applyTheme('light'); map.jumpTo({ center: [31.2357, 30.0444], zoom: 15 }); setMapFull(true); });
  await idle(); await shot('1-day');
  await page.evaluate(() => applyTheme('dark')); await idle(4000); await shot('2-night');

  await page.evaluate(() => { setMapFull(false); $('freeGo').click(); });
  for (let i = 0; i < PATH.length; i++) {
    await page.evaluate(([la, lo]) => window.__cb && window.__cb({ timestamp: Date.now(), coords: { latitude: la, longitude: lo, accuracy: 5, speed: 14, heading: 355 } }), PATH[i]);
    await wait(i < PATH.length - 1 ? 250 : 0);
  }
  await idle(5000); await shot('3-drive-night');
  await page.evaluate(() => applyTheme('light')); await idle(4000); await shot('4-drive-day');

  // a manual zoom-out: the camera stops following and the re-center button shows
  await page.mouse.move(195, 500); await page.mouse.wheel(0, 900); await wait(1500); await shot('5-zoomed-by-hand');
  await wait(8500); await idle(2000); await shot('6-recentred');

  await page.evaluate(() => { $('nmenu').click(); }); await idle(3000); await shot('7-trip-minimised');
  console.log('errors', JSON.stringify(errs));
  await b.close(); srv.close();
})().catch(e => { console.error(e); process.exit(1); });
