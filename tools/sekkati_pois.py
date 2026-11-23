"""Download Egypt's speed cameras, toll booths and checkpoints from OpenStreetMap (Overpass)
into sekkati/eg-pois.json, so the app has them offline without the driver reporting anything.
Format: {"at": epoch_ms, "p": [[lat, lon, kind, maxspeed, direction|null], ...]}, kind: r=radar t=toll c=checkpoint."""
import json, sys, time, urllib.parse, urllib.request

# Egypt's bounding box. Small per-kind queries: one big area query timed out on every Overpass mirror.
BB = "(21.9,24.6,31.8,37.0)"
QUERIES = {
    "radars": 'node["highway"="speed_camera"]%s;' % BB,
    "enforcement": 'rel["type"="enforcement"]%s->.e;node(r.e:"device");' % BB,
    "tolls": 'nwr["barrier"="toll_booth"]%s;node["highway"="toll_gantry"]%s;' % (BB, BB),
    "checkpoints": 'nwr["barrier"="checkpoint"]%s;nwr["police"="checkpoint"]%s;nwr["military"="checkpoint"]%s;' % (BB, BB, BB),
}
MIRRORS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
           "https://overpass.private.coffee/api/interpreter"]
CARD = {"N": 0, "NNE": 22, "NE": 45, "ENE": 67, "E": 90, "ESE": 112, "SE": 135, "SSE": 157, "S": 180,
        "SSW": 202, "SW": 225, "WSW": 247, "W": 270, "WNW": 292, "NW": 315, "NNW": 337}


def direction(v):
    if v is None:
        return None
    try:
        return round(float(v)) % 360
    except ValueError:
        return CARD.get(str(v).upper())


def maxspeed(v):
    try:
        return int(str(v).split()[0])
    except (ValueError, IndexError):
        return 0


def fetch(body):
    q = "[out:json][timeout:120];(" + body + ");out center tags;"
    for url in MIRRORS:
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(),
                                         headers={"User-Agent": "sekkati-pois/1.0"})
            with urllib.request.urlopen(req, timeout=150) as r:
                return json.load(r).get("elements", [])
        except Exception as e:
            print("  failed", url, e)
            time.sleep(3)
    return None


elements, failed = [], []
for name, body in QUERIES.items():
    got = fetch(body)
    print(name, "->", "FAILED" if got is None else len(got))
    if got is None:
        failed.append(name)
    else:
        elements += got
if not elements:
    print("no data; keeping the old file")
    sys.exit(1)
data = {"elements": elements}

out, seen, cnt = [], set(), {"r": 0, "t": 0, "c": 0}
for e in data["elements"]:
    t = e.get("tags", {})
    if t.get("type") == "enforcement":
        continue  # the relation itself; its device nodes are the cameras
    c = e.get("center") or {}
    lat, lon = (e["lat"], e["lon"]) if "lat" in e else (c.get("lat"), c.get("lon"))
    if lat is None:
        continue
    if t.get("barrier") == "toll_booth" or t.get("highway") == "toll_gantry":
        k = "t"
    elif t.get("barrier") == "checkpoint" or t.get("police") == "checkpoint" or t.get("military") == "checkpoint":
        k = "c"
    else:
        k = "r"  # speed_camera, or a device of an enforcement relation
    key = (k, round(lat, 4), round(lon, 4))
    if key in seen:
        continue
    seen.add(key)
    cnt[k] += 1
    out.append([round(lat, 6), round(lon, 6), k, maxspeed(t.get("maxspeed")),
                direction(t.get("direction") or t.get("camera:direction"))])
out.sort(key=lambda x: (x[0], x[1], x[2]))
print("radars %(r)d, tolls %(t)d, checkpoints %(c)d" % cnt)
old = None
try:
    old = json.load(open("sekkati/eg-pois.json"))["p"]
except Exception:
    pass
if old == out:
    print("unchanged")
    sys.exit(0)
json.dump({"at": int(time.time() * 1000), "p": out}, open("sekkati/eg-pois.json", "w"), separators=(",", ":"))
print("written", len(out))
