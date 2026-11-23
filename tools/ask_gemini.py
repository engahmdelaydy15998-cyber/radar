#!/usr/bin/env python3
"""Send a prompt file to Gemini and save the answer as markdown. Usage: ask_gemini.py PROMPT.md OUT.md

Tries stronger models first and falls back to lighter ones (free-tier availability changes).
Key: env GEMINI_API_KEY (repo secret). Run from the ask-gemini workflow.
"""
import json
import os
import sys
import urllib.error
import urllib.request

MODELS = ["gemini-3.1-pro-preview", "gemini-pro-latest", "gemini-3-flash-preview", "gemini-flash-latest",
          "gemini-flash-lite-latest"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"


def main():
    prompt_path, out_path = sys.argv[1], sys.argv[2]
    key = os.environ["GEMINI_API_KEY"]
    prompt = open(prompt_path, encoding="utf-8").read()
    body = json.dumps({"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                       "generationConfig": {"temperature": 0.7, "maxOutputTokens": 16000}}).encode("utf-8")
    for model in MODELS:
        req = urllib.request.Request(URL % model, data=body, method="POST",
                                     headers={"x-goog-api-key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                cand = json.loads(r.read().decode("utf-8"))["candidates"][0]
        except urllib.error.HTTPError as ex:
            print(model, "->", ex.code, ex.read()[:200], file=sys.stderr)
            continue
        except Exception as ex:
            print(model, "->", ex, file=sys.stderr)
            continue
        text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []) if not p.get("thought"))
        if not text.strip():
            print(model, "-> empty reply", cand.get("finishReason"), file=sys.stderr)
            continue
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("<!-- model: %s -->\n\n%s\n" % (model, text.strip()))
        print("answered by", model)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
