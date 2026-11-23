// سكّتي shared reports server (Cloudflare Worker + D1). Anonymous: no accounts, no names, no location history.
// Stores only report points (what + where), votes per random device id, and a short-lived hashed IP for rate limits.
//   GET  /near?lat=&lon=&km=15     -> {items:[{id,k,lat,lon,dir,max,up,down,last}]}
//   POST /report {k,lat,lon,dir?,max?,dev}  -> merges with an existing same-kind point within ~60 m (counts as a vote)
//   POST /vote   {id,up:true|false,dev}
//   GET  /stats                     -> counts per kind (for the app's "community" line)
const KINDS = { radar: 0, mradar: 2 * 3600, checkpoint: 0, toll: 0, bump: 0, jam: 45 * 60, accident: 90 * 60, closed: 6 * 3600 };
const CORS = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' };
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { 'Content-Type': 'application/json', ...CORS } });
const now = () => Math.floor(Date.now() / 1000);
const EG = { s: 21.5, n: 32, w: 24.5, e: 37.2 };   // Egypt only, so the map can't be filled from elsewhere

async function sha(s) {
  const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(b)].slice(0, 12).map(x => x.toString(16).padStart(2, '0')).join('');
}
async function limited(env, req, dev, max) {   // at most `max` writes per hour per device and per (daily-salted) IP
  const day = new Date().toISOString().slice(0, 10), ip = await sha((req.headers.get('CF-Connecting-IP') || '') + day + (env.SALT || 's'));
  const hr = Math.floor(now() / 3600);
  const keys = ['ip:' + ip + ':' + hr, 'dev:' + dev + ':' + hr];
  for (const k of keys) {
    const r = await env.DB.prepare('INSERT INTO hits(k, n, hr) VALUES(?, 1, ?) ON CONFLICT(k) DO UPDATE SET n = n + 1 RETURNING n').bind(k, hr).first();
    if (r && r.n > max) return true;
  }
  return false;
}
function validDev(d) { return typeof d === 'string' && /^[a-f0-9]{16,64}$/.test(d); }

export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
    const u = new URL(req.url);
    try {
      if (u.pathname === '/near' && req.method === 'GET') {
        const lat = +u.searchParams.get('lat'), lon = +u.searchParams.get('lon'), km = Math.min(40, +u.searchParams.get('km') || 15);
        if (!isFinite(lat) || !isFinite(lon)) return json({ error: 'lat/lon' }, 400);
        const dLa = km / 111, dLo = km / (111 * Math.cos(lat * Math.PI / 180));
        const r = await env.DB.prepare(
          'SELECT id,k,lat,lon,dir,max,up,down,last FROM reports WHERE lat BETWEEN ? AND ? AND lon BETWEEN ? AND ? AND (expires IS NULL OR expires > ?) AND down < up + 2 LIMIT 2000'
        ).bind(lat - dLa, lat + dLa, lon - dLo, lon + dLo, now()).all();
        return json({ items: r.results || [], at: now() });
      }
      if (u.pathname === '/stats') {
        const r = await env.DB.prepare('SELECT k, COUNT(*) n FROM reports WHERE (expires IS NULL OR expires > ?) GROUP BY k').bind(now()).all();
        return json({ kinds: r.results || [] });
      }
      if (req.method !== 'POST') return json({ error: 'not found' }, 404);
      const b = await req.json().catch(() => ({}));
      if (!validDev(b.dev)) return json({ error: 'dev' }, 400);
      if (u.pathname === '/report') {
        const k = String(b.k || ''), lat = +b.lat, lon = +b.lon;
        if (!(k in KINDS) || !isFinite(lat) || !isFinite(lon) || lat < EG.s || lat > EG.n || lon < EG.w || lon > EG.e) return json({ error: 'bad report' }, 400);
        if (await limited(env, req, b.dev, 40)) return json({ error: 'slow down' }, 429);
        const t = now(), exp = KINDS[k] ? t + KINDS[k] : null, d = 0.0006;   // ~60 m
        const same = await env.DB.prepare('SELECT id FROM reports WHERE k = ? AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ? AND (expires IS NULL OR expires > ?) LIMIT 1')
          .bind(k, lat - d, lat + d, lon - d, lon + d, t).first();
        let id;
        if (same) id = same.id;
        else {
          const dir = Number.isFinite(+b.dir) ? Math.round(+b.dir) % 360 : null, max = Math.max(0, Math.min(200, Math.round(+b.max || 0)));
          const ins = await env.DB.prepare('INSERT INTO reports(k,lat,lon,dir,max,up,down,created,last,expires) VALUES(?,?,?,?,?,0,0,?,?,?) RETURNING id')
            .bind(k, +lat.toFixed(5), +lon.toFixed(5), dir, max, t, t, exp).first();
          id = ins.id;
        }
        await vote(env, id, b.dev, true, exp);
        return json({ id, merged: !!same });
      }
      if (u.pathname === '/vote') {
        if (await limited(env, req, b.dev, 120)) return json({ error: 'slow down' }, 429);
        const r = await env.DB.prepare('SELECT id,k FROM reports WHERE id = ?').bind(+b.id).first();
        if (!r) return json({ error: 'no such report' }, 404);
        await vote(env, r.id, b.dev, !!b.up, KINDS[r.k] ? now() + KINDS[r.k] : null);
        return json({ ok: true });
      }
      return json({ error: 'not found' }, 404);
    } catch (e) {
      return json({ error: String(e && e.message || e) }, 500);
    }
  }
};

async function vote(env, id, dev, up, exp) {   // one vote per device per report; a new "still there" refreshes the expiry
  const devh = await sha(dev);
  await env.DB.prepare('INSERT INTO votes(rid, dev, up, at) VALUES(?,?,?,?) ON CONFLICT(rid, dev) DO UPDATE SET up = excluded.up, at = excluded.at')
    .bind(id, devh, up ? 1 : 0, now()).run();
  const sql = 'UPDATE reports SET up = (SELECT COUNT(*) FROM votes WHERE rid = ?1 AND up = 1), down = (SELECT COUNT(*) FROM votes WHERE rid = ?1 AND up = 0), last = ?2'
    + (exp && up ? ', expires = ?3' : '') + ' WHERE id = ?1';
  const st = env.DB.prepare(sql);
  await (exp && up ? st.bind(id, now(), exp) : st.bind(id, now())).run();
  if (Math.random() < 0.02) await env.DB.prepare('DELETE FROM hits WHERE hr < ?').bind(Math.floor(now() / 3600) - 2).run();   // old rate-limit counters
}
