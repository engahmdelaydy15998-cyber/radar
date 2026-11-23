-- سكّتي shared reports (Cloudflare D1 / SQLite). Anonymous by design.
CREATE TABLE IF NOT EXISTS reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  k TEXT NOT NULL,              -- radar, mradar, checkpoint, toll, bump, jam, accident, closed
  lat REAL NOT NULL, lon REAL NOT NULL,
  dir INTEGER, max INTEGER DEFAULT 0,
  up INTEGER DEFAULT 0, down INTEGER DEFAULT 0,
  created INTEGER NOT NULL, last INTEGER NOT NULL,
  expires INTEGER               -- NULL = fixed (radar, toll, ...); temporary things expire unless confirmed again
);
CREATE INDEX IF NOT EXISTS reports_geo ON reports(lat, lon);
CREATE TABLE IF NOT EXISTS votes (
  rid INTEGER NOT NULL, dev TEXT NOT NULL, up INTEGER NOT NULL, at INTEGER NOT NULL,
  PRIMARY KEY (rid, dev)
);
CREATE TABLE IF NOT EXISTS hits (k TEXT PRIMARY KEY, n INTEGER NOT NULL, hr INTEGER NOT NULL);
