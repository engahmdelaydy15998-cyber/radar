"""Download Egypt's speed cameras, toll booths and checkpoints from OpenStreetMap (Overpass)
into sekkati/eg-pois.json, so the app has them offline without the driver reporting anything.
Format: {"at": epoch_ms, "p": [[lat, lon, kind, maxspeed, direction|null], ...]}, kind: r=radar t=toll c=checkpoint."""
import json, sys, time, urllib.parse, urllib.request

Q = """[out:json][timeout:180];
area["ISO3166-1"="EG"][admin_level=2]->.eg;
rel["type"="enforcement"](area.eg)->.enf;
node(r.enf:"device")->.dev;
(
  node["highway"="speed_camera"](area.eg);
  .dev;
  nwr["barrier"="toll_booth"](area.eg);
  node["highway"="toll_gantry"](area.eg);
  nwr["barrier"="checkpoint"](area.eg);
  nwr["police"="checkpoint"](area.eg);
  nwr["military"="checkpoint"](area.eg);
);
out center tags;"""
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


data = None
for url in MIRRORS:
    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": Q}).encode(),
                                     headers={"User-Agent": "sekkati-pois/1.0"})
        with urllib.request.urlopen(req, timeout=240) as r:
            data = json.load(r)
        print("ok from", url)
        break
    except Exception as e:
        print("failed", url, e)
        time.sleep(5)
if not data or not data.get("elements"):
    print("no data; keeping the old file")
    sys.exit(1)

out, seen, cnt = [], set(), {"r": 0, "t": 0, "c": 0}
for e in data["elements"]:
    t = e.get("tags", {})
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
