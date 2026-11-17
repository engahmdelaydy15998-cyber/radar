#!/usr/bin/env python3
"""Append a YouTube channel to channels.json from an issue body (env ISSUE_BODY).

Body lines: "id: UC...." or "handle: @name", optional "name: ...", "kind: creator|co|arch|agents".
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "channels.json")


def main():
    body = os.environ.get("ISSUE_BODY", "")
    f = {}
    for line in body.splitlines():
        m = re.match(r"\s*(id|handle|name|kind)\s*:\s*(.+?)\s*$", line, re.I)
        if m:
            f[m.group(1).lower()] = m.group(2)
    ref = None
    if re.fullmatch(r"UC[\w-]{22}", f.get("id", "")):
        ref = f["id"]
    elif re.fullmatch(r"@[\w.\-]{2,40}", f.get("handle", "")):
        ref = f["handle"]
    if not ref:
        print("no valid channel in issue body", file=sys.stderr)
        return 1
    kind = f.get("kind", "creator")
    if kind not in ("creator", "co", "arch", "agents"):
        kind = "creator"
    name = re.sub(r"[^\w .\-&']", "", f.get("name", ""))[:60] or ref
    try:
        with open(PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        data = {"channels": []}
    chans = data.setdefault("channels", [])
    key = "id" if ref.startswith("UC") else "handle"
    if any(c.get(key) == ref for c in chans):
        print("already present")
        return 0
    chans.append({key: ref, "name": name, "kind": kind})
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("added", ref, kind)
    return 0


if __name__ == "__main__":
    sys.exit(main())
