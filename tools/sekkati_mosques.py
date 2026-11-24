"""Build sekkati/eg-mosques.json: Egypt's mosques from OpenStreetMap, minus the ones inside compounds or other
private / gated areas that a passing driver can't enter. The app reads it to say "there's a mosque ahead" at prayer time.

Uses the same Geofabrik extract as sekkati_pois.py (egypt.osm.pbf, downloaded by the workflow).
Output: {"at": ms, "m": [lat1, lon1, lat2, lon2, ...]} with 5 decimals (~1 m).  Data © OpenStreetMap contributors (ODbL)."""
import json, os, re, subprocess, sys, time

PBF = "egypt.osm.pbf"
FILTERS = ["nwr/amenity=place_of_worship", "wr/access=private,no,customers,residents", "wr/residential=gated",
           "wr/gated=yes", "wr/landuse=residential", "wr/barrier=wall,fence"]
NAME_MOSQUE = re.compile(r"مسجد|جامع|mosque|masjid|musall?a|مصلى|مصلي", re.I)
NAME_COMPOUND = re.compile(r"كمبوند|كومباوند|compound|residence|heights|hills|gardens|villas|فيلات|ريزيدنس", re.I)
CELL = 0.02


def center(g):
    c = g["coordinates"]
    t = g["type"]
    if t == "Point":
        return c[1], c[0]
    ring = c if t == "LineString" else c[0] if t == "Polygon" else c[0][0]
    return sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring)


def is_mosque(t):
    if t.get("amenity") != "place_of_worship":
        return False
    if t.get("religion") == "muslim":
        return True
    return not t.get("religion") and bool(NAME_MOSQUE.search(t.get("name", "") + " " + t.get("name:en", "")))


def is_private_area(t):
    if t.get("access") in ("private", "no", "customers", "residents") or t.get("residential") == "gated" or t.get("gated") == "yes":
        return True
    if t.get("landuse") == "residential" and NAME_COMPOUND.search(t.get("name", "") + " " + t.get("name:en", "")):
        return True
    return False


def rings(g):
    if g["type"] == "Polygon":
        return [g["coordinates"]]
    if g["type"] == "MultiPolygon":
        return g["coordinates"]
    if g["type"] == "LineString" and len(g["coordinates"]) > 3 and g["coordinates"][0] == g["coordinates"][-1]:
        return [[g["coordinates"]]]   # a closed wall/fence ring around a compound
    return []


def inside(lon, lat, ring):
    hit = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def main():
    if not os.path.exists(PBF):
        sys.exit("run sekkati_pois.py first (it downloads %s)" % PBF)
    subprocess.run(["osmium", "tags-filter", PBF] + FILTERS + ["-o", "m.pbf", "--overwrite"], check=True)
    subprocess.run(["osmium", "export", "m.pbf", "-f", "geojsonseq", "-o", "m.geojsonseq", "--overwrite",
                    "--geometry-types=point,linestring,polygon"], check=True)
    mosques, areas = [], []
    for line in open("m.geojsonseq", encoding="utf-8"):
        line = line.strip().lstrip("\x1e")
        if not line:
            continue
        f = json.loads(line)
        t, g = f.get("properties") or {}, f.get("geometry")
        if not g:
            continue
        if is_mosque(t):
            if t.get("access") in ("private", "no"):
                continue
            mosques.append(center(g))
        elif is_private_area(t) or (t.get("barrier") in ("wall", "fence") and g["type"] == "LineString"):
            for poly in rings(g):
                outer = poly[0]
                xs, ys = [p[0] for p in outer], [p[1] for p in outer]
                if max(xs) - min(xs) > 0.08 or max(ys) - min(ys) > 0.08:
                    continue                      # a whole city / district, not a compound
                if t.get("barrier") and (max(xs) - min(xs)) * (max(ys) - min(ys)) < 4e-6:
                    continue                      # a wall around one building (often the mosque itself)
                areas.append((min(xs), min(ys), max(xs), max(ys), outer))
    grid = {}
    for a in areas:
        for gx in range(int(a[0] / CELL), int(a[2] / CELL) + 1):
            for gy in range(int(a[1] / CELL), int(a[3] / CELL) + 1):
                grid.setdefault((gx, gy), []).append(a)
    out, seen, dropped = [], set(), 0
    for lat, lon in mosques:
        key = (round(lat, 4), round(lon, 4))
        if key in seen:
            continue
        seen.add(key)
        if any(a[0] <= lon <= a[2] and a[1] <= lat <= a[3] and inside(lon, lat, a[4])
               for a in grid.get((int(lon / CELL), int(lat / CELL)), [])):
            dropped += 1
            continue
        out.append((round(lat, 5), round(lon, 5)))
    out.sort()
    print("mosques %d, inside compounds/private areas (dropped) %d, private areas %d" % (len(out), dropped, len(areas)))
    if len(out) < 1000:
        print("suspiciously few; keeping the old file")
        sys.exit(1)
    flat = [v for p in out for v in p]
    try:
        if json.load(open("sekkati/eg-mosques.json"))["m"] == flat:
            print("unchanged")
            return
    except Exception:
        pass
    json.dump({"at": int(time.time() * 1000), "src": "© OpenStreetMap contributors (ODbL), via Geofabrik", "m": flat},
              open("sekkati/eg-mosques.json", "w"), separators=(",", ":"))
    print("written", len(out))


if __name__ == "__main__":
    main()
