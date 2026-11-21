#!/usr/bin/env python3
"""Append a link shared from the app to shared.json from an issue body (env ISSUE_BODY).

Body lines: "url: https://..." and optional "note: ..." (the text the share sheet carried).
The page's public title/description are fetched when available (LinkedIn, Facebook and Instagram
often hide them from bots); the collector then writes an AI headline from whatever text there is.
"""
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "shared.json")
UA = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Mobile Safari/537.36"
PLATFORMS = [("linkedin.com", "LinkedIn"), ("facebook.com", "Facebook"), ("fb.watch", "Facebook"),
             ("instagram.com", "Instagram"), ("x.com", "X"), ("twitter.com", "X"), ("youtube.com", "YouTube"),
             ("youtu.be", "YouTube"), ("github.com", "GitHub"), ("tiktok.com", "TikTok")]


def platform(host):
    host = host.lower()
    for dom, name in PLATFORMS:
        if host == dom or host.endswith("." + dom):
            return name
    return host.replace("www.", "")


def meta(page, prop):
    for pat in (r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]+content=["\']([^"\']*)' % prop,
                r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']%s["\']' % prop):
        m = re.search(pat, page, re.I)
        if m:
            return html.unescape(m.group(1)).strip()
    return ""


def page_info(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en,ar;q=0.8"})
        with urllib.request.urlopen(req, timeout=20) as r:
            page = r.read(400000).decode("utf-8", "replace")
    except Exception as ex:
        print("fetch failed:", ex, file=sys.stderr)
        return "", ""
    title = meta(page, "og:title")
    if not title:
        m = re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
        title = html.unescape(m.group(1)).strip() if m else ""
    return title[:200], (meta(page, "og:description") or meta(page, "description"))[:400]


def slug_words(u):
    """LinkedIn post URLs carry the post's opening words in the path."""
    path = urllib.parse.unquote(u.path)
    m = re.search(r"/posts/[^_]+_(.+?)-(?:activity|ugcPost|share)-\d+", path)
    return m.group(1).replace("-", " ") if m else ""


def main():
    body = os.environ.get("ISSUE_BODY", "")
    f = {}
    for line in body.splitlines():
        m = re.match(r"\s*(url|note)\s*:\s*(.+?)\s*$", line, re.I)
        if m:
            f[m.group(1).lower()] = m.group(2)
    url = f.get("url", "")
    u = urllib.parse.urlparse(url)
    if u.scheme not in ("http", "https") or "." not in u.netloc:
        print("no valid url in issue body", file=sys.stderr)
        return 1
    note = re.sub(r"https?://\S+", "", f.get("note", "")).strip()[:500]
    try:
        with open(PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        data = {"items": []}
    items = data.setdefault("items", [])
    if any(it.get("url") == url for it in items):
        print("already present")
        return 0
    title, desc = page_info(url)
    slug = slug_words(u)
    src = platform(u.netloc)
    items.append({
        "id": "sh-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:12],
        "cat": "news",
        "src": src,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "t": title or slug or note[:120] or ("بوست من " + src),
        "s": " ".join(x for x in (desc, slug, note) if x)[:600],
        "tags": ["مشاركتك"],
        "url": url,
    })
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("added", src, url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
