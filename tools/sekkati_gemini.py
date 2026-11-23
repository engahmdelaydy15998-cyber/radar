"""Send the latest sekkati/ai-review/ask-N.md prompt plus project context to Gemini; write answer-N.md."""
import glob, json, os, re, sys, time, urllib.request, urllib.error

KEY = os.environ["GEMINI_API_KEY"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
MODELS = ["gemini-pro-latest", "gemini-3-flash-preview", "gemini-flash-latest", "gemini-flash-lite-latest"]

asks = sorted(glob.glob("sekkati/ai-review/ask-*.md"), key=lambda p: int(re.findall(r"\d+", p)[-1]))
ask = asks[-1]; n = int(re.findall(r"\d+", ask)[-1])
out = "sekkati/ai-review/answer-%d.md" % n
if os.path.exists(out):
    print("already answered", out); sys.exit(0)

def read(p):
    return open(p, encoding="utf-8").read()

ctx = ["# SUMMARY-FOR-AI.md\n" + read("sekkati/SUMMARY-FOR-AI.md")]
for i in range(1, n):  # earlier rounds, so it sees the conversation
    for kind in ("ask", "answer"):
        p = "sekkati/ai-review/%s-%d.md" % (kind, i)
        if os.path.exists(p):
            ctx.append("# Earlier round %d %s\n%s" % (i, kind, read(p)))
files = ["sekkati/index.html", "sekkati/sw.js", "sekkati/manifest.webmanifest"] + \
    sorted(glob.glob("sekkati-android/android/app/src/main/java/com/sekkati/app/*.java")) + \
    ["sekkati-android/android/app/src/main/AndroidManifest.xml", "sekkati-android/capacitor.config.json"]
for f in files:
    if os.path.exists(f):
        ctx.append("# FILE %s\n```\n%s\n```" % (f, read(f)))
prompt = "\n\n".join(ctx) + "\n\n# THE REQUEST (round %d)\n%s" % (n, read(ask))

body = json.dumps({"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                   "generationConfig": {"maxOutputTokens": 32000, "temperature": 0.4}}).encode()
last = ""
for model in MODELS:
    for attempt in range(2):
        req = urllib.request.Request(URL % model, data=body, method="POST",
                                     headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                d = json.load(r)
            text = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
            if text.strip():
                open(out, "w", encoding="utf-8").write("<!-- model: %s -->\n%s\n" % (model, text))
                print("OK", model, len(text), "chars ->", out); sys.exit(0)
            last = "%s: empty (%s)" % (model, d["candidates"][0].get("finishReason"))
        except urllib.error.HTTPError as e:
            last = "%s: HTTP %s %s" % (model, e.code, e.read()[:300])
        except Exception as e:
            last = "%s: %s" % (model, e)
        print(last)
        if "429" not in last and "503" not in last: break
        time.sleep(20)
open(out, "w", encoding="utf-8").write("FAILED: %s\n" % last)
sys.exit(1)
