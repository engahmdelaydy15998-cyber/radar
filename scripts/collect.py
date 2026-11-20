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
MAX_ITEMS = 320
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
    # architecture / BIM / AEC
    ("@ArchDaily", "ArchDaily", "arch"),
    ("@dezeen", "Dezeen", "arch"),
    ("@TheB1M", "The B1M", "arch"),
    ("@BalkanArchitect", "Balkan Architect", "arch"),
    ("@ParametricArchitecture", "Parametric Architecture", "arch"),
    ("@archicad", "Archicad", "arch"),
    ("@AutodeskAEC", "Autodesk AEC", "arch"),
    ("@rhinoceros3d", "Rhino / McNeel", "arch"),
]

# Agents section: local agents, Claude Code, cheaper alternatives, new tools.
CHANNELS += [
    ("@AllAboutAI", "All About AI", "agents"),
    ("@matthew_berman", "Matthew Berman", "agents"),
    ("@AIJasonZ", "AI Jason", "agents"),
    ("@1littlecoder", "1littlecoder", "agents"),
    ("@intheworldofai", "WorldofAI", "agents"),
    ("@NetworkChuck", "NetworkChuck", "agents"),
]

# Extra channels added from the app live in channels.json: {"channels":[{"handle"|"id","name","kind"}]}
EXTRA = os.path.join(ROOT, "channels.json")

# Watched recurring problems, added from the app (or by Claude in a chat session) via the add-watch
# issue flow: {"watches":[{"id","desc","kw":[...],"active"}]}. See scripts/add_watch.py.
WATCHES = os.path.join(ROOT, "watches.json")

AGENT_RSS = [
    ("https://simonwillison.net/atom/everything/", "Simon Willison"),
    ("https://www.reddit.com/r/LocalLLaMA/top/.rss?t=day", "r/LocalLLaMA"),
    ("https://www.reddit.com/r/ClaudeAI/top/.rss?t=day", "r/ClaudeAI"),
    ("https://www.reddit.com/r/ClaudeCode/top/.rss?t=day", "r/ClaudeCode"),
]
HN_AGENT_QUERIES = ["Claude Code", "Ollama", "local LLM", "MCP server", "DeepSeek", "Qwen", "Kimi", "llama.cpp",
                    "coding agent", "Claude alternative", "open source agent"]
GH_AGENT_TOPICS = ["claude-code", "mcp", "ollama", "ai-agents", "local-llm", "llama-cpp", "coding-agent"]
AGENT_NEWS = [
    "Claude Code alternative",
    "local AI coding agent",
    "Ollama new model",
    "cheaper AI coding subscription",
    "Claude Code usage limits tips",
    "open source AI agent framework",
]
AGENT_KW = re.compile(
    r"agent|Claude|Ollama|local LLM|MCP|DeepSeek|Qwen|Kimi|llama|Codex|Cursor|Gemini CLI|OpenCode|Aider|Cline|"
    r"open[- ]source model|subscription|pricing|token|self-hosted|on-device", re.I)

# (url, display name). Architecture and AEC news feeds.
RSS_FEEDS = [
    ("https://feeds.feedburner.com/Archdaily", "ArchDaily"),
    ("https://www.dezeen.com/feed/", "Dezeen"),
    ("https://architosh.com/feed/", "Architosh"),
    ("https://aecmag.com/feed/", "AEC Magazine"),
    ("https://archinect.com/feed/1/news", "Archinect"),
]

HN_ARCH_QUERIES = ["Revit", "BIM", "Autodesk", "Grasshopper", "generative design", "AI architecture", "AI construction", "AI CAD"]

# Google News searches (free RSS). Focus: AI and computational tools in architecture, BIM, AEC.
NEWS_QUERIES = [
    "AI architecture BIM",
    "Revit AI",
    "Autodesk Forma AI architecture",
    "generative design architecture AI",
    "Rhino Grasshopper AI",
    "Archicad AI",
    "Snaptrude OR Hypar OR TestFit OR Arkio",
    "AI construction BIM",
    "Midjourney architecture visualization",
    "digital twin building AI",
]

# Google News results must also clearly be about architecture / AEC, otherwise they are dropped.
AEC_KW = re.compile(
    r"architect|\bBIM\b|Revit|Archicad|Rhino|Grasshopper|\bAEC\b|construction|building design|Autodesk|"
    r"digital twin|Snaptrude|Hypar|TestFit|Arkio|Speckle|Enscape|Twinmotion|Lumion|Vectorworks|Navisworks|"
    r"generative design|floor plan|real estate design|urban design|\bIFC\b|openBIM|Bentley|Trimble|Nemetschek",
    re.I,
)

# Feed and video items in the architecture section must mention AI, BIM or computational tools.
ARCH_KW = re.compile(
    r"\bAI\b|artificial intelligence|machine learning|generative|BIM|Revit|Archicad|Rhino|Grasshopper|Dynamo Revit|"
    r"parametric|computational|digital twin|Autodesk|Navisworks|ChatGPT|Claude|Midjourney|diffusion|"
    r"automation|algorithm|robot|3D print|\bIFC\b|openBIM|Speckle|Enscape|Twinmotion|Lumion|\bCAD\b",
    re.I,
)
GH_ARCH_TOPICS = ["bim", "ifc", "revit", "grasshopper", "dynamo", "building-information-modeling"]
# plugins for BIM/CAD tools; tagged "Add-in" so the app files them under its Add-ins tile
GH_ADDIN_TOPICS = ["revit-addin", "revit-plugin", "revit-api", "grasshopper-plugin", "dynamo-package", "pyrevit"]

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


def all_channels():
    out = [(h, n, k) for h, n, k in CHANNELS]
    try:
        with open(EXTRA, encoding="utf-8") as f:
            for c in json.load(f).get("channels", []):
                ref = c.get("id") or c.get("handle")
                if ref:
                    out.append((ref, c.get("name") or ref, c.get("kind") or "creator"))
    except Exception:
        pass
    return out


def collect_youtube(known_ids, cutoff):
    items = []
    for handle, name, kind in all_channels():
        try:
            cid = handle if re.fullmatch(r"UC[\w-]{22}", handle) else channel_id(handle)
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
            if kind == "arch" and not ARCH_KW.search(en["title"] + " " + en["desc"][:300]):
                continue
            short = is_short(en["vid"])
            if short:
                cat = "reels"
            elif kind == "co":
                cat = "co"
            elif kind == "arch":
                cat = "arch"
            elif kind == "agents":
                cat = "agents"
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

def parse_hn(json_text, cutoff, cat="code"):
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
            "cat": cat,
            "src": "Hacker News",
            "ts": iso(ts),
            "t": title,
            "s": "%s نقطة، %s تعليق" % (h.get("points", 0), h.get("num_comments", 0)),
            "tags": ["نقاش"],
            "url": url,
            "url2": "https://news.ycombinator.com/item?id=" + oid if h.get("url") else "",
        })
    return out


def collect_hn(known_ids, cutoff):
    items, seen = [], set()
    since = int(cutoff.timestamp())
    jobs = [(q, "code", 80) for q in HN_QUERIES] + [(q, "arch", 12) for q in HN_ARCH_QUERIES] + [(q, "agents", 25) for q in HN_AGENT_QUERIES]
    for q, cat, pts in jobs:
        url = ("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=20&numericFilters="
               + urllib.parse.quote("points>%d,created_at_i>%d" % (pts, since)) + "&query=" + urllib.parse.quote(q))
        try:
            found = parse_hn(get(url), cutoff, cat)
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

def parse_github(json_text, cat="code", tag="مشروع جديد"):
    out = []
    for r in json.loads(json_text).get("items", []):
        created = parse_ts(r["created_at"])
        out.append({
            "id": "gh-%s" % r["id"],
            "cat": cat,
            "src": "GitHub",
            "ts": iso(created),
            "t": r["full_name"] + (": " + clip(r.get("description"), 90) if r.get("description") else ""),
            "s": "%s نجمة، لغة %s" % (r.get("stargazers_count", 0), r.get("language") or "غير محددة"),
            "tags": [tag],
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
    out = [it for it in found if it["id"] not in known_ids]
    seen = {it["id"] for it in out}
    week = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    for topic in GH_ARCH_TOPICS:
        q2 = "topic:%s pushed:>%s stars:>25" % (topic, week)
        u2 = "https://api.github.com/search/repositories?sort=updated&order=desc&per_page=5&q=" + urllib.parse.quote(q2)
        try:
            more = parse_github(get(u2, headers), "arch", "أداة مفتوحة المصدر")
        except Exception as ex:
            log("github arch: failed", topic, ex)
            continue
        for it in more:
            if it["id"] not in known_ids and it["id"] not in seen:
                seen.add(it["id"])
                out.append(it)
    fresh = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
    for topic in GH_AGENT_TOPICS:
        q3 = "topic:%s created:>%s stars:>30" % (topic, fresh)
        u3 = "https://api.github.com/search/repositories?sort=stars&order=desc&per_page=6&q=" + urllib.parse.quote(q3)
        try:
            more = parse_github(get(u3, headers), "agents", "MCP" if topic == "mcp" else "جديد كلياً")
        except Exception as ex:
            log("github agents: failed", topic, ex)
            continue
        for it in more:
            if it["id"] not in known_ids and it["id"] not in seen:
                seen.add(it["id"])
                out.append(it)
    for topic in GH_ADDIN_TOPICS:
        q4 = "topic:%s pushed:>%s" % (topic, week)
        u4 = "https://api.github.com/search/repositories?sort=updated&order=desc&per_page=5&q=" + urllib.parse.quote(q4)
        try:
            more = parse_github(get(u4, headers), "arch", "Add-in")
        except Exception as ex:
            log("github addins: failed", topic, ex)
            continue
        for it in more:
            if it["id"] not in known_ids and it["id"] not in seen:
                seen.add(it["id"])
                out.append(it)
    return out


# ---------- RSS (architecture news) ----------

def strip_html(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    return re.sub(r"&[a-z#0-9]+;", " ", t)


def collect_rss(known_ids, cutoff):
    from email.utils import parsedate_to_datetime
    items = []
    for url, name in RSS_FEEDS:
        try:
            root = ET.fromstring(get(url))
        except Exception as ex:
            log("rss: failed", name, ex)
            continue
        count = 0
        for e in root.iter("item"):
            link = (e.findtext("link") or "").strip()
            title = (e.findtext("title") or "").strip()
            pub = e.findtext("pubDate")
            if not (link and title and pub):
                continue
            try:
                ts = parsedate_to_datetime(pub).astimezone(timezone.utc)
            except Exception:
                continue
            if ts < cutoff:
                continue
            if not ARCH_KW.search(title + " " + strip_html(e.findtext("description"))):
                continue
            item_id = "rss-" + re.sub(r"\W+", "", link)[-60:]
            if item_id in known_ids:
                continue
            items.append({
                "id": item_id, "cat": "arch", "src": name, "ts": iso(ts), "t": title,
                "s": clip(strip_html(e.findtext("description")), 160), "tags": ["AEC"], "url": link,
            })
            count += 1
            if count >= 8:
                break
    return items


def collect_news(known_ids, cutoff):
    from email.utils import parsedate_to_datetime
    items, seen = [], set()
    jobs = [(q, "arch") for q in NEWS_QUERIES] + [(q, "agents") for q in AGENT_NEWS]
    for q, cat in jobs:
        url = "https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q=" + urllib.parse.quote(q + " when:14d")
        try:
            root = ET.fromstring(get(url))
        except Exception as ex:
            log("news: failed", q, ex)
            continue
        n = 0
        for e in root.iter("item"):
            link = (e.findtext("link") or "").strip()
            title = (e.findtext("title") or "").strip()
            pub = e.findtext("pubDate")
            src_el = e.find("source")
            src = (src_el.text if src_el is not None and src_el.text else "News").strip()
            if title.endswith(" - " + src):
                title = title[: -len(src) - 3]
            if not (link and title and pub):
                continue
            try:
                ts = parsedate_to_datetime(pub).astimezone(timezone.utc)
            except Exception:
                continue
            item_id = "gn-" + re.sub(r"\W+", "", title.lower())[:60]
            if ts < cutoff or item_id in known_ids or item_id in seen:
                continue
            if cat == "arch" and not (AEC_KW.search(title) and ARCH_KW.search(title + " " + src)):
                continue
            if cat == "agents" and not AGENT_KW.search(title):
                continue
            seen.add(item_id)
            items.append({"id": item_id, "cat": cat, "src": src, "ts": iso(ts), "t": title,
                          "s": "", "tags": ["AI + AEC" if cat == "arch" else "Agents"], "url": link})
            n += 1
            if n >= 6:
                break
    return items


def collect_agent_feeds(known_ids, cutoff):
    items = []
    A = "{http://www.w3.org/2005/Atom}"
    for url, name in AGENT_RSS:
        try:
            root = ET.fromstring(get(url))
        except Exception as ex:
            log("agent feed: failed", name, ex)
            continue
        n = 0
        for e in root.iter(A + "entry"):
            title = (e.findtext(A + "title") or "").strip()
            link_el = e.find(A + "link")
            link = link_el.get("href") if link_el is not None else ""
            pub = e.findtext(A + "updated") or e.findtext(A + "published")
            if not (title and link and pub):
                continue
            try:
                ts = parse_ts(pub)
            except Exception:
                continue
            item_id = "af-" + re.sub(r"\W+", "", link)[-60:]
            if ts < cutoff or item_id in known_ids:
                continue
            if name.startswith("r/") and not AGENT_KW.search(title):
                continue
            items.append({"id": item_id, "cat": "agents", "src": name, "ts": iso(ts), "t": title,
                          "s": "", "tags": ["نقاش" if name.startswith("r/") else "مدونة"], "url": link})
            n += 1
            if n >= 8:
                break
    return items


# ---------- translation (free Google endpoint, no key) ----------

def has_arabic(t):
    return bool(re.search(r"[\u0600-\u06FF]", t or ""))


def translate(text):
    url = ("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ar&dt=t&q="
           + urllib.parse.quote(text[:300]))
    data = json.loads(get(url, timeout=20))
    return "".join(seg[0] for seg in data[0] if seg and seg[0]).strip()


def add_translations(items, limit=150):
    import time
    done = 0
    for it in items:
        for src_key, dst_key in (("t", "ta"), ("s", "sa")):
            text = it.get(src_key) or ""
            if done >= limit:
                return done
            if it.get(dst_key) or not text or has_arabic(text) or re.match(r"^\d+ ", text):
                continue
            if src_key == "s" and len(text) < 25:
                continue
            try:
                it[dst_key] = translate(text)
                done += 1
                time.sleep(0.15)
            except Exception as ex:
                log("translate failed:", ex)
                return done
    return done


# ---------- watches ----------

def load_watches():
    try:
        with open(WATCHES, encoding="utf-8") as f:
            return json.load(f).get("watches", [])
    except Exception:
        return []


def apply_watches(items):
    """Flag items matching an active watch's keywords with item["watch"] = <problem desc>."""
    compiled = []
    for w in load_watches():
        if not w.get("active", True):
            continue
        pat = "|".join(re.escape(k) for k in w.get("kw", []) if k.strip())
        if pat:
            compiled.append((w.get("desc", ""), re.compile(pat, re.I)))
    for it in items:
        it.pop("watch", None)
        if not compiled:
            continue
        hay = " ".join(str(it.get(k, "")) for k in ("t", "s", "ta", "sa"))
        for desc, rx in compiled:
            if rx.search(hay):
                it["watch"] = desc
                break


# ---------- AI headlines (Google Gemini free tier; key in the GEMINI_API_KEY repo secret) ----------

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
# tried in order; the first model the key can use is kept for the rest of the run
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]
TOPICS = ("arch", "addins", "agents", "mcp", "oss", "courses", "news")
AI_SYSTEM = (
    "أنت محرر أخبار تقنية لمهندس معماري مصري مهتم بالـ BIM والذكاء الاصطناعي والـ agents والكود. "
    "لكل خبر اكتب بالعربي الفصيح المبسط مع ترك المصطلحات التقنية بالإنجليزي (BIM, Revit, MCP, agent...):\n"
    "- h: منشيت قصير جذاب ومفهوم من أول نظرة (أقل من 70 حرف)، مش ترجمة حرفية للعنوان.\n"
    "- x: سطر واحد بالخلاصة أو ليه الخبر ده يهمه (أقل من 140 حرف).\n"
    "- tags: من 1 لـ 3 تاجات قصيرة بالإنجليزي.\n"
    "- topic: واحد بس من: arch (BIM والعمارة والتشييد)، addins (إضافات لبرامج BIM/CAD)، agents، mcp، "
    "oss (مشروع مفتوح المصدر)، courses (شرح أو كورس)، news (أي حاجة تانية). "
    "كلمة architecture عن المعالجات أو البرمجيات مش عمارة.\n"
    'رجّع JSON بالشكل: {"items":[{"id":"...","h":"...","x":"...","tags":["..."],"topic":"..."}]}'
)


def gemini_post(model, payload, key):
    body = json.dumps({
        "systemInstruction": {"parts": [{"text": AI_SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps(payload, ensure_ascii=False)}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3},
    }).encode("utf-8")
    req = urllib.request.Request(GEMINI_URL % model, data=body, method="POST",
                                 headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read().decode("utf-8", "replace")
    try:
        parts = json.loads(raw)["candidates"][0]["content"]["parts"]
        msg = "".join(p.get("text", "") for p in parts)
        return json.loads(re.search(r"\{.*\}", msg, re.S).group(0)).get("items", [])
    except Exception:
        raise RuntimeError("unexpected reply: " + raw[:200].replace("\n", " "))


_ai_model = []


def ai_call(batch, key):
    payload = [{"id": it["id"], "title": it["t"], "about": clip(it.get("s", ""), 200), "source": it.get("src", ""),
                "cat": it.get("cat", "")} for it in batch]
    errors = []
    for model in (_ai_model or GEMINI_MODELS):
        try:
            out = gemini_post(model, payload, key)
            if not _ai_model:
                _ai_model.append(model)
                log("ai model:", model)
            return out
        except urllib.error.HTTPError as ex:
            errors.append("%s -> HTTP %s %s" % (model, ex.code, ex.read()[:200]))
        except Exception as ex:
            errors.append("%s -> %s" % (model, ex))
    raise RuntimeError(" | ".join(errors))


def add_ai_headlines(items, max_calls=3, batch=20):
    """Adds h (Arabic headline), x (one-line takeaway), tg (tags), tp (topic) to items that lack them."""
    token = os.environ.get("GEMINI_API_KEY")
    if not token:
        log("ai headlines: skipped, no GEMINI_API_KEY secret")
        return 0
    todo = [it for it in items if not it.get("h")][: max_calls * batch]
    by_id = {it["id"]: it for it in todo}
    done = 0
    for i in range(0, len(todo), batch):
        try:
            out = ai_call(todo[i:i + batch], token)
        except Exception as ex:
            log("ai headlines failed:", ex)
            break
        for o in out:
            it = by_id.get(o.get("id"))
            h = (o.get("h") or "").strip()
            if not it or not h:
                continue
            it["h"] = h[:90]
            it["x"] = (o.get("x") or "").strip()[:180]
            it["tg"] = [str(t)[:24] for t in (o.get("tags") or [])][:3]
            if o.get("topic") in TOPICS:
                it["tp"] = o["topic"]
            done += 1
    return done


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
    existing = [it for it in load_existing()
                if not (it["id"].startswith("gn-") and it.get("cat") == "arch" and not (AEC_KW.search(it["t"]) and ARCH_KW.search(it["t"])))]
    known = {it["id"] for it in existing}
    watch_before = {it["id"]: it.get("watch") for it in existing}

    new = []
    for name, fn in (("youtube", collect_youtube), ("hn", collect_hn), ("github", collect_github), ("rss", collect_rss), ("news", collect_news), ("agent_feeds", collect_agent_feeds)):
        try:
            got = fn(known, cutoff)
        except Exception as ex:
            log(name, "crashed:", ex)
            got = []
        log(name, "new items:", len(got))
        new.extend(got)

    items = merge(existing, new)
    tr = add_translations(items)
    ai = add_ai_headlines(items)
    log("ai headlines:", ai)
    log("translated:", tr)
    apply_watches(items)
    watch_changed = any(it.get("watch") != watch_before.get(it["id"]) for it in items)
    if not items:
        log("nothing to write")
        return 0
    if [i["id"] for i in items] == [i["id"] for i in existing] and not new and not tr and not ai and not watch_changed:
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
