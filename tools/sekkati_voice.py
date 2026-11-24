"""Generate سكّتي's spoken alerts with Gemini's Arabic text-to-speech, once, on GitHub (GEMINI_API_KEY secret),
and bundle them as small mp3 files in sekkati/voice/ so the app speaks with that voice offline and with no key on the phone.
Resumable: phrases that already have a file are skipped; stops cleanly on quota errors and keeps what it made.
The phrase list must match the exact text the app passes to speak() (see sayRaw/clipFor in sekkati/index.html)."""
import base64, hashlib, json, os, subprocess, sys, time, urllib.error, urllib.request

KEY = os.environ["GEMINI_API_KEY"]
VOICE = os.environ.get("SEKKATI_VOICE", "Kore")
OUT = "sekkati/voice"
API = "https://generativelanguage.googleapis.com/v1beta/"
STYLE = ""  # an instruction in the prompt got read aloud by the TTS model, so the text goes alone
DIG = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def ar(n):
    return str(n).translate(DIG)


def min_txt(m):  # same as minTxt() in the app
    return "دقيقة" if m == 1 else "دقيقتين" if m == 2 else ar(m) + (" دقايق" if m <= 10 else " دقيقة")


EG1 = ["", "واحد", "اتنين", "تلاتة", "اربعة", "خمسة", "ستة", "سبعة", "تمانية", "تسعة", "عشرة", "حداشر", "اتناشر", "تلاتاشر",
       "اربعتاشر", "خمستاشر", "ستاشر", "سبعتاشر", "تمنتاشر", "تسعتاشر"]
EG10 = ["", "", "عشرين", "تلاتين", "اربعين", "خمسين", "ستين", "سبعين", "تمانين", "تسعين"]
HUN = ["", "مية", "ميتين", "تلتمية", "ربعمية", "خمسمية", "ستمية", "سبعمية", "تمنمية", "تسعمية"]
def eg_num(n):  # same as egNum() in the app: numbers spoken the Egyptian way ("ستين", "مية وعشرين")
    if n == 0:
        return "صفر"
    if n >= 1000:
        return str(n)
    h, r = divmod(n, 100)
    rest = EG1[r] if r < 20 else ((EG1[r % 10] + " و") if r % 10 else "") + EG10[r // 10]
    return HUN[h] + " و" + rest if HUN[h] and rest else HUN[h] or rest
def eg_words(t):
    import re
    return re.sub(r"[٠-٩0-9]+", lambda m: eg_num(int(m.group(0).translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))), t)
def phrases():
    P = []
    POI = {"radar": "رادار", "toll": "كارتة", "uturn": "يوتيرن", "checkpoint": "لجنة", "spot": "وقفة متكررة", "bump": "مطب", "mradar": "رادار متحرك", "jam": "زحمة", "accident": "حادثة", "closed": "طريق مقفول"}
    LIMITS = [30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
    # 1) the alerts that matter most
    for d in ("خمسمية", "ميت وخمسين"):
        for k, name in POI.items():
            P.append("%s بعد %s متر" % (name, d))
        for lim in LIMITS:
            P.append("رادار بعد %s متر، الحد %s" % (d, ar(lim)))
    for lim in LIMITS:
        P.append("هدّي السرعة، الحد %s" % ar(lim))
    for v in range(35, 205, 5):
        P.append("وانت %s" % ar(v))
    # 2) fixed sentences
    P += ["تمام، بدأت أسجّل الطريق، وهنبّهك قبل الرادارات والكارتات", "وصلت، حمد الله على السلامة", "الصوت رجع", "تمام",
          "لسه مستني الموقع", "واقفين ليه؟ قول كارتة أو لجنة أو زحمة أو حادثة", "تمام، سجلت البلاغ", "تمام، سجلت ملاحظة",
          "تمام، سجلت إن الطريق مقفول", "تمام، غيّرت الطريق", "الطريق الحالي هو الأنسب",
          "محتاج وجهة الأول عشان أدورلك على طريق تاني", "محتاج نت عشان أدور على طريق تاني", "ما فهمتش، اضغط على الزرار اللي يناسب",
          "ما سمعتش حاجة", "الموبايل مش بيعرف يسمع الكلام", "ده الصوت الجديد. رادار بعد خمسمية متر",
          "رادار بعد خمسمية متر، الحد ستين. هدّي السرعة", "تمام، هنمشي نفس الطريق، وهقولك انت أسرع ولا أبطأ من المرة اللي فاتت",
          "وصلت في نفس وقت المرة اللي فاتت تقريباً", "خلصت الرحلة."]
    P += ["تمام، سجلت %s هنا" % name for name in POI.values()]
    # 3) trip-again comparisons
    for m in range(1, 16):
        P += ["انت أسرع من المرة اللي فاتت بـ " + min_txt(m), "انت أبطأ من المرة اللي فاتت بـ " + min_txt(m)]
    for m in range(1, 21):
        P += ["وصلت أسرع من المرة اللي فاتت بـ " + min_txt(m), "وصلت أبطأ من المرة اللي فاتت بـ " + min_txt(m)]
    for m in range(1, 31):
        P.append("في طريق أسرع بحوالي %s دقيقة. تغيّر؟" % ar(m))
    # 4) turn-by-turn (street names are dropped when speaking from clips; they stay on screen)
    moves = ["ابدأ السير", "وصلت لوجهتك", "اعمل يوتيرن", "كمّل مستقيم", "خد ميلة يمين", "خد ميلة شمال",
             "لف يمين بحدة", "لف شمال بحدة", "لف يمين", "لف شمال"] + ["ادخل الدوار وخد المخرج " + ar(i) for i in range(1, 6)]
    for pre in ("", "بعد خمسمية متر ", "بعد مية متر "):
        P += [pre + m for m in moves]
    seen, out = set(), []
    for p in map(eg_words, P):
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def commit(msg):  # push progress as we go (CI only), so a cut-off run keeps what it made
    if os.environ.get("SEKKATI_COMMIT") != "1":
        return
    sh = lambda c: subprocess.run(c, shell=True)
    sh('git config user.name "Claude"; git config user.email "noreply@anthropic.com"; git add sekkati/voice')
    if subprocess.run("git diff --cached --quiet", shell=True).returncode == 0:
        return
    sh('git commit -q -m "%s"' % msg)
    b = os.environ.get("GITHUB_REF_NAME", "")
    for _ in range(3):
        if sh("git pull -q --rebase origin %s && git push -q origin HEAD:%s" % (b, b)).returncode == 0:
            break
        time.sleep(5)


def fname(text):
    return hashlib.sha1((VOICE + "|" + text).encode()).hexdigest()[:12] + ".mp3"


def tts_models():
    with urllib.request.urlopen(urllib.request.Request(API + "models?pageSize=200", headers={"x-goog-api-key": KEY}), timeout=60) as r:
        names = [m["name"].split("/")[-1] for m in json.load(r).get("models", []) if "tts" in m["name"]]
    names.sort(key=lambda n: (("lite" in n), ("pro" in n), ("preview" in n), n))  # full flash first, then lite
    print("tts models:", names)
    return names


def speak(model, text):
    body = json.dumps({"contents": [{"parts": [{"text": STYLE + text}]}],
                       "generationConfig": {"responseModalities": ["AUDIO"],
                                            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}}).encode()
    req = urllib.request.Request(API + "models/%s:generateContent" % model, data=body, method="POST",
                                 headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    part = d["candidates"][0]["content"]["parts"][0]["inlineData"]
    rate = 24000
    for bit in part.get("mimeType", "").split(";"):
        if bit.strip().startswith("rate="):
            rate = int(bit.split("=")[1])
    return base64.b64decode(part["data"]), rate


def too_long(text, pcm, rate):  # Arabic speech is ~12 chars/s; 3x that means it read something else too
    sec = len(pcm) / 2.0 / rate
    return sec > max(4.0, len(text) / 12.0 * 3 + 1.5), sec


def to_mp3(pcm, rate, path):
    trim = "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", "pipe:0",
                    "-af", trim, "-ac", "1", "-b:a", "48k", path], input=pcm, check=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    idx_path = os.path.join(OUT, "index.json")
    idx = {"voice": VOICE, "clips": {}}
    if os.path.exists(idx_path):
        old = json.load(open(idx_path, encoding="utf-8"))
        if old.get("voice") == VOICE:
            idx = old
    todo = [p for p in phrases() if p not in idx["clips"] or not os.path.exists(os.path.join(OUT, idx["clips"][p]))]
    limit = int(os.environ.get("SEKKATI_VOICE_MAX", "400"))
    print("voice %s: %d phrases to make (limit %d)" % (VOICE, len(todo), limit))
    models, made, fails = tts_models(), 0, 0
    if not models:
        print("no TTS model available for this key")
        sys.exit(1)
    mi = 0
    for text in todo[:limit]:
        while True:
            try:
                pcm, rate = speak(models[mi], text)
                bad, sec = too_long(text, pcm, rate)
                if bad:
                    print("too long (%.1fs), skipping model %s for: %s" % (sec, models[mi], text))
                    if mi + 1 < len(models):
                        mi += 1; continue
                    break
                f = fname(text)
                to_mp3(pcm, rate, os.path.join(OUT, f))
                idx["clips"][text] = f
                idx["model"] = models[mi]
                made += 1
                print("ok", made, models[mi], text)
                if made % 25 == 0:
                    commit("sekkati: Gemini voice clips (%d)" % len(idx["clips"]))
                json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
                time.sleep(float(os.environ.get("SEKKATI_VOICE_GAP", "4")))
                break
            except urllib.error.HTTPError as e:
                msg = e.read()[:300]
                print("HTTP", e.code, models[mi], msg)
                if e.code == 429 and b"PerDay" in msg or e.code == 429 and fails > 6:
                    if mi + 1 < len(models):
                        mi += 1; fails = 0; continue
                    print("daily quota reached; made", made); return
                if e.code in (429, 500, 503):
                    fails += 1; time.sleep(min(90, 15 * fails)); continue
                if e.code in (400, 404) and mi + 1 < len(models):
                    mi += 1; continue
                print("giving up on:", text); break
            except Exception as e:
                print("error", e); fails += 1
                if fails > 8:
                    return
                time.sleep(10)
    print("done; made", made)
    commit("sekkati: Gemini voice clips (%d)" % len(idx["clips"]))


def samples():  # the same sentence in a few voices, so the driver can pick one
    global VOICE
    os.makedirs(OUT + "/samples", exist_ok=True)
    models = tts_models()
    for v in ["Kore", "Sulafat", "Charon", "Orus", "Aoede"]:
        path = "%s/samples/%s.mp3" % (OUT, v)
        if os.path.exists(path):
            continue
        VOICE = v
        try:
            pcm, rate = speak(models[0], "رادار بعد خمسمية متر، الحد ستين. هدّي السرعة.")
            print("sample %s %.1fs" % (v, len(pcm) / 2.0 / rate))
            to_mp3(pcm, rate, path); print("sample", v)
        except Exception as e:
            print("sample failed", v, e)
        time.sleep(5)
    VOICE = os.environ.get("SEKKATI_VOICE", "Kore")
    commit("sekkati: Gemini voice samples")


if __name__ == "__main__":
    if "--samples" in sys.argv:
        samples()
    elif "--list" in sys.argv:
        print("\n".join(phrases())); print(len(phrases()), "phrases")
    else:
        main()
