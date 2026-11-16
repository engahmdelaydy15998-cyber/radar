#!/usr/bin/env python3
"""Radar collector. Gathers new AI and code items into data.json. Standard library only.

Sources: YouTube channel feeds, Hacker News (Algolia), GitHub search.
A source that fails is logged and skipped; the others still run.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data.json")
UA = "Mozilla/5.0 (compatible; RadarBot/1.0)"
MAX_ITEMS = 200
MAX_AGE_DAYS = 14
PER_CHANNEL = 6

# (handle, display name, kind). kind "co" = official company channel, "creator" = person or educator.
CHANNELS = [
    ("@OpenAI", "OpenAI", "co"),
    ("@anthropic-ai", "Anthropic", "co"),
    ("@GoogleDeepMind", "Google DeepMind", "co"),
    ("@LangChain", "LangChain", "co"),
    ("@AssemblyAI", "AssemblyAI", "co"),
    ("@AndrejKarpathy", "Andrej Karpathy", "creator"),
    ("@Fireship", "Fireship", "creator"),
    ("@TwoMinutePapers", "Two Minute Papers", "creator"),
    ("@YannicKilcher", "Yannic Kilcher", "creator"),
    ("@mreflow", "Matt Wolfe", "creator"),
    ("@ColeMedin", "Cole Medin", "creator"),
    ("@daveebbelaar", "Dave Ebbelaar", "creator"),
    ("@aiexplained-official", "AI Explained", "creator"),
    ("@drfiras_ai", "Dr Firas", "creator"),
    ("@ElzeroWebSchool", "Elzero Web School", "creator"),
]

HN_QUERIES = ["LLM", "Claude", "AI agent", "OpenAI", "Gemini", "coding assistant"]

NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "m": "http://search.yahoo.com/mrss/",
}


def log(*a):
    print(*a, file=sys.stderr)


def get(url, headers=None, timeout=25):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def clip(text, n=150):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


# ---------- YouTube ----------

def channel_id(handle):
    html = get("https://www.youtube.com/" + handle)
    for pat in (
        r"feeds/videos\.xml\?channel_id=(UC[\w-]{22})",
        r'"channelId":"(UC[\w-]{22})"',
        r'"externalId":"(UC[\w-]{22})"',
    ):
        m = re.search(pat, html)
        if m:
            return m.group(1)
    return None


def parse_feed(xml_text):
    root = ET.fromstring(xml_text)
    out = []
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", default="", namespaces=NS)
        title = e.findtext("a:title", default="", namespaces=NS)
        pub = e.findtext("a:published", default="", namespaces=NS)
        desc = e.findtext("m:group/m:description", default="", namespaces=NS)
        if not (vid and pub):
            continue
        out.append({"vid": vid, "title": title, "published": parse_ts(pub), "desc": desc})
    return out


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def is_short(vid):
    """True for a Short, False for a regular video, None if unknown."""
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request("https://www.youtube.com/shorts/" + vid, headers={"User-Agent": UA}, method="HEAD")
    try:
        with opener.open(req, timeout=20) as r:
            return r.status == 200
    except urllib.error.HTTPError:
        return False
    except Exception:
        return None


def collect_youtube(known_ids, cutoff):
    items = []
    for handle, name, kind in CHANNELS:
        try:
            cid = channel_id(handle)
            if not cid:
                log("youtube: no channel id for", handle)
                continue
            feed = get("https://www.youtube.com/feeds/videos.xml?channel_id=" + cid)
            entries = parse_feed(feed)[:PER_CHANNEL]
        except Exception as ex:
            log("youtube: failed", handle, ex)
            continue
        for en in entries:
            if en["published"] < cutoff:
                continue
            item_id = "yt-" + en["vid"]
            if item_id in known_ids:
                continue
            short = is_short(en["vid"])
            if short:
                cat = "reels"
            elif kind == "co":
                cat = "co"
            else:
                cat = "long"
            items.append({
                "id": item_id,
                "cat": cat,
                "src": "YouTube",
                "ts": iso(en["published"]),
                "t": en["title"],
                "s": clip(en["desc"]),
                "tags": [name],
                "url": ("https://www.youtube.com/shorts/" if short else "https://www.youtube.com/watch?v=") + en["vid"],
            })
    return items


# ---------- Hacker News ----------

def parse_hn(json_text, cutoff):
    out = []
    for h in json.loads(json_text).get("hits", []):
        oid = h.get("objectID")
        title = h.get("title")
        if not (oid and title):
            continue
        ts = datetime.fromtimestamp(h.get("created_at_i", 0), tz=timezone.utc)
        if ts < cutoff:
            continue
        url = h.get("url") or ("https://news.ycombinator.com/item?id=" + oid)
        out.append({
            "id": "hn-" + oid,
            "cat": "code",
            "src": "Hacker News",
            "ts": iso(ts),
            "t": title,
            "s": "%s نقطة، %s تعليق" % (h.get("points", 0), h.get("num_comments", 0)),
            "tags": ["نقاش"],
            "url": url,
        })
    return out


def collect_hn(known_ids, cutoff):
    items, seen = [], set()
    since = int(cutoff.timestamp())
    for q in HN_QUERIES:
        url = ("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=20&numericFilters="
               + urllib.parse.quote("points>80,created_at_i>%d" % since) + "&query=" + urllib.parse.quote(q))
        try:
            found = parse_hn(get(url), cutoff)
        except Exception as ex:
            log("hn: failed", q, ex)
            continue
        for it in found:
            if it["id"] in seen or it["id"] in known_ids:
                continue
            seen.add(it["id"])
            items.append(it)
    return items


# ---------- GitHub ----------

def parse_github(json_text):
    out = []
    for r in json.loads(json_text).get("items", []):
        created = parse_ts(r["created_at"])
        out.append({
            "id": "gh-%s" % r["id"],
            "cat": "code",
            "src": "GitHub",
            "ts": iso(created),
            "t": r["full_name"] + (": " + clip(r.get("description"), 90) if r.get("description") else ""),
            "s": "%s نجمة، لغة %s" % (r.get("stargazers_count", 0), r.get("language") or "غير محددة"),
            "tags": ["مشروع جديد"],
            "url": r["html_url"],
        })
    return out


def collect_github(known_ids, cutoff):
    day = cutoff.strftime("%Y-%m-%d")
    q = "topic:llm created:>%s stars:>40" % day
    url = "https://api.github.com/search/repositories?sort=stars&order=desc&per_page=10&q=" + urllib.parse.quote(q)
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    try:
        found = parse_github(get(url, headers))
    except Exception as ex:
        log("github: failed", ex)
        return []
    return [it for it in found if it["id"] not in known_ids]


# ---------- merge ----------

def load_existing():
    try:
        with open(DATA, encoding="utf-8") as f:
            d = json.load(f)
        return d.get("items", []) if isinstance(d, dict) else []
    except Exception:
        return []


def merge(existing, new):
    by_id = {it["id"]: it for it in existing if it.get("ts")}
    for it in new:
        by_id.setdefault(it["id"], it)
    items = sorted(by_id.values(), key=lambda x: x["ts"], reverse=True)
    return items[:MAX_ITEMS]


def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=MAX_AGE_DAYS)
    existing = load_existing()
    known = {it["id"] for it in existing}

    new = []
    for name, fn in (("youtube", collect_youtube), ("hn", collect_hn), ("github", collect_github)):
        try:
            got = fn(known, cutoff)
        except Exception as ex:
            log(name, "crashed:", ex)
            got = []
        log(name, "new items:", len(got))
        new.extend(got)

    items = merge(existing, new)
    if not items:
        log("nothing to write")
        return 0
    if [i["id"] for i in items] == [i["id"] for i in existing] and not new:
        log("no changes")
        return 0
    out = {"updated": iso(now), "demo": False, "items": items}
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    log("wrote", len(items), "items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
