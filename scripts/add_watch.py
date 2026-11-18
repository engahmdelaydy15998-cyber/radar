#!/usr/bin/env python3
"""Append a watched problem to watches.json from an issue body (env ISSUE_BODY).

Body lines: "desc: ..." (the problem, free text) and "kw: a, b, c" (search keywords).
"""
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "watches.json")


def main():
    body = os.environ.get("ISSUE_BODY", "")
    f = {}
    for line in body.splitlines():
        m = re.match(r"\s*(desc|kw)\s*:\s*(.+?)\s*$", line, re.I)
        if m:
            f[m.group(1).lower()] = m.group(2)
    desc = re.sub(r"[^\w .,!؟\-]", "", f.get("desc", ""))[:200].strip()
    kw = [k.strip() for k in f.get("kw", "").split(",") if k.strip()][:8]
    if not desc or not kw:
        print("missing desc or kw in issue body", file=sys.stderr)
        return 1
    try:
        with open(PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        data = {"watches": []}
    watches = data.setdefault("watches", [])
    if any(w.get("desc") == desc for w in watches):
        print("already present")
        return 0
    watches.append({"id": "w%d" % int(time.time()), "desc": desc, "kw": kw, "active": True})
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("added watch", desc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
