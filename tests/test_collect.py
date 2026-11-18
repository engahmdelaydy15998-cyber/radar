import importlib.util, json, os, sys, tempfile
from datetime import datetime, timedelta, timezone

spec = importlib.util.spec_from_file_location("collect", "/home/claude/radar-repo/scripts/collect.py")
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)

now = datetime.now(timezone.utc)
def feed(vids):
    ents = ""
    for vid, title, age_h in vids:
        pub = (now - timedelta(hours=age_h)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        ents += f"""<entry><id>yt:video:{vid}</id><yt:videoId>{vid}</yt:videoId><title>{title}</title>
<published>{pub}</published><media:group><media:description>Desc of {title}\nsecond line</media:description></media:group></entry>"""
    return f"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/">{ents}</feed>"""

page = '<link rel="alternate" type="application/rss+xml" href="https://www.youtube.com/feeds/videos.xml?channel_id=UCabcdefghijklmnopqrstuv">'
hn = json.dumps({"hits": [
  {"objectID": "111", "title": "Show HN: tiny LLM tool", "url": "https://example.com/a", "points": 150, "num_comments": 30, "created_at_i": int((now - timedelta(hours=5)).timestamp())},
  {"objectID": "222", "title": "Ask HN: no url", "points": 99, "num_comments": 4, "created_at_i": int((now - timedelta(hours=9)).timestamp())},
  {"objectID": "333", "title": "Too old", "url": "https://old.example", "points": 500, "num_comments": 9, "created_at_i": int((now - timedelta(days=40)).timestamp())},
]})
gh = json.dumps({"items": [{"id": 7, "full_name": "me/cool-llm", "description": "A cool thing", "stargazers_count": 321, "language": "Python",
  "created_at": (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ"), "html_url": "https://github.com/me/cool-llm"}]})

def fake_get(url, headers=None, timeout=25):
    if "youtube.com/@" in url: return page
    if "feeds/videos.xml" in url: return feed([("SHORT111", "A short clip", 3), ("LONG2222", "A long video", 30), ("OLDVID33", "Ancient", 24*30)])
    if "algolia" in url: return hn
    if "api.github.com" in url: return gh
    raise RuntimeError("unexpected " + url)
c.get = fake_get
c.is_short = lambda vid: vid.startswith("SHORT")
c.CHANNELS = [("@Co", "Some Co", "co"), ("@Person", "Some Person", "creator")]
c.HN_QUERIES = ["LLM", "AI agent"]

tmp = tempfile.mkdtemp()
c.DATA = os.path.join(tmp, "data.json")

assert c.main() == 0
d = json.load(open(c.DATA, encoding="utf-8"))
ids = [i["id"] for i in d["items"]]
print("ids:", ids)
cats = {i["id"]: i["cat"] for i in d["items"]}
assert cats["yt-SHORT111"] == "reels"
assert cats["yt-LONG2222"] in ("co", "long")
assert "yt-OLDVID33" not in ids, "old video should be dropped"
assert "hn-333" not in ids, "old HN item should be dropped"
assert cats["hn-111"] == "code" and cats["gh-7"] == "code"
assert len(ids) == len(set(ids)), "duplicates"
assert [i["ts"] for i in d["items"]] == sorted([i["ts"] for i in d["items"]], reverse=True)
co_long = [i for i in d["items"] if i["id"] == "yt-LONG2222"]
print("long video cats across channels:", sorted({i["cat"] for i in d["items"] if i["id"] == "yt-LONG2222"}))
hn_nourl = [i for i in d["items"] if i["id"] == "hn-222"][0]
assert hn_nourl["url"].startswith("https://news.ycombinator.com/item?id=222")
first_count = len(ids)

# second run: nothing new -> no duplicates, stable
before = open(c.DATA, "rb").read()
assert c.main() == 0
after = open(c.DATA, "rb").read()
assert before == after, "second run should not change the file"

# all sources failing must keep existing data
def boom(*a, **k): raise RuntimeError("offline")
c.get = boom
assert c.main() == 0
assert open(c.DATA, "rb").read() == before, "failure must not clobber data"
print("ALL OK", first_count, "items; sample:", json.dumps(d["items"][0], ensure_ascii=False)[:200])

# watches: flags matching items, clears the flag once a watch is removed
c.WATCHES = os.path.join(tmp, "watches.json")
json.dump({"watches": [{"id": "w1", "desc": "مشكلة اللاما", "kw": ["llm", "lama"], "active": True}]}, open(c.WATCHES, "w", encoding="utf-8"))
sample = [{"id": "x1", "t": "cool llm project", "s": ""}, {"id": "x2", "t": "something else", "s": ""}]
c.apply_watches(sample)
assert sample[0]["watch"] == "مشكلة اللاما", "should flag the matching item"
assert "watch" not in sample[1], "should not flag a non-matching item"
json.dump({"watches": []}, open(c.WATCHES, "w", encoding="utf-8"))
c.apply_watches(sample)
assert "watch" not in sample[0], "flag must clear once the watch is gone"
print("WATCH TEST OK")
