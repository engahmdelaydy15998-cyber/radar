"""Build sekkati/eg-pois.json: Egypt's speed cameras, speed bumps, toll booths and checkpoints from OpenStreetMap,
so the app alerts on them offline without the driver reporting anything.

Source: the full Egypt extract from Geofabrik (egypt-latest.osm.pbf), filtered with osmium-tool. This is far more
reliable than the Overpass API, which timed out on a country-wide query. Cameras in Egypt are mostly tagged
enforcement=maxspeed (not only highway=speed_camera), which the first version missed.

Format: {"at": epoch_ms, "src": "...", "p": [[lat, lon, kind, maxspeed, direction|null], ...]}
kind: r=radar, b=bump, t=toll, c=checkpoint.  Data © OpenStreetMap contributors (ODbL)."""
import json, os, re, subprocess, sys, time, urllib.request

PBF = "egypt.osm.pbf"
URL = "https://download.geofabrik.de/africa/egypt-latest.osm.pbf"
FILTERS = ["nwr/highway=speed_camera", "nwr/enforcement=maxspeed,average_speed", "nwr/traffic_calming", "nwr/highway=speed_bump",
           "nwr/barrier=toll_booth", "n/highway=toll_gantry", "nwr/barrier=checkpoint", "nwr/police=checkpoint", "nwr/military=checkpoint"]
BUMPS = {"bump", "hump", "table", "cushion", "yes", "dip", "rumble_strip", "speed_bump"}
CARD = {"N": 0, "NNE": 22, "NE": 45, "ENE": 67, "E": 90, "ESE": 112, "SE": 135, "SSE": 157, "S": 180,
        "SSW": 202, "SW": 225, "WSW": 247, "W": 270, "WNW": 292, "NW": 315, "NNW": 337}


def direction(v):
    if v is None:
        return None
    try:
        return round(float(str(v).split(";")[0])) % 360
    except ValueError:
        return CARD.get(str(v).upper())


def maxspeed(v):
    m = re.search(r"\d+", str(v or ""))
    if not m:
        return 0
    n = int(m.group())
    return int(n * 1.609) if "mph" in str(v) else n


def kind(t):
    if t.get("highway") == "speed_camera" or t.get("enforcement") in ("maxspeed", "average_speed"):
        return "r"
    if t.get("barrier") == "toll_booth" or t.get("highway") == "toll_gantry":
        return "t"
    if t.get("barrier") == "checkpoint" or t.get("police") == "checkpoint" or t.get("military") == "checkpoint":
        return "c"
    if t.get("traffic_calming") in BUMPS or t.get("highway") == "speed_bump":
        return "b"
    return None


def center(geom):
    c = geom["coordinates"]
    if geom["type"] == "Point":
        return c[1], c[0]
    while isinstance(c[0][0], list):  # polygon / multi: flatten one level
        c = c[0]
    return sum(p[1] for p in c) / len(c), sum(p[0] for p in c) / len(c)


def main():
    if not os.path.exists(PBF):
        print("downloading", URL)
        urllib.request.urlretrieve(URL, PBF)
    subprocess.run(["osmium", "tags-filter", PBF] + FILTERS + ["-o", "f.pbf", "--overwrite"], check=True)
    subprocess.run(["osmium", "export", "f.pbf", "-f", "geojsonseq", "-o", "f.geojsonseq", "--overwrite",
                    "--geometry-types=point,linestring,polygon"], check=True)
    out, seen, cnt = [], set(), {"r": 0, "b": 0, "t": 0, "c": 0}
    for line in open("f.geojsonseq", encoding="utf-8"):
        line = line.strip().lstrip("\x1e")
        if not line:
            continue
        f = json.loads(line)
        t = f.get("properties") or {}
        k = kind(t)
        if not k or not f.get("geometry"):
            continue
        lat, lon = center(f["geometry"])
        key = (k, round(lat, 4), round(lon, 4))
        if key in seen:
            continue
        seen.add(key)
        cnt[k] += 1
        out.append([round(lat, 6), round(lon, 6), k, maxspeed(t.get("maxspeed")),
                    direction(t.get("direction") or t.get("camera:direction"))])
    out.sort(key=lambda x: (x[0], x[1], x[2]))
    print("radars %(r)d, bumps %(b)d, tolls %(t)d, checkpoints %(c)d" % cnt)
    print("radars with a speed limit:", sum(1 for x in out if x[2] == "r" and x[3]))
    if cnt["r"] + cnt["t"] + cnt["c"] < 50:
        print("suspiciously little data; keeping the old file")
        sys.exit(1)
    try:
        if json.load(open("sekkati/eg-pois.json"))["p"] == out:
            print("unchanged")
            return
    except Exception:
        pass
    json.dump({"at": int(time.time() * 1000), "src": "© OpenStreetMap contributors (ODbL), via Geofabrik", "p": out},
              open("sekkati/eg-pois.json", "w"), separators=(",", ":"))
    print("written", len(out))


if __name__ == "__main__":
    main()
