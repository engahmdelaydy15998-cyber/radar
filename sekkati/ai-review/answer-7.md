<!-- model: gemini-3-flash-preview -->
This is a great direction. Moving from a "passive recorder" to an "active AI assistant" is what will make **سكّتي** indispensable for the Egyptian driver.

### 1. Voice Notes + AI: The "Smart Road Memory"

Egyptian roads change daily. A "note" shouldn't just be a dot; it should be a memory that helps the driver (and others) later.

**A. Categories & Actions:**
*   **`pothole` (حفرة / تكسير):** *Action:* Alert next time + Share. (Critical for low cars).
*   **`danger` (خطر / يوتيرن وحش):** *Action:* Alert next time + Share.
*   **`fuel` (بنزينة / تموين):** *Action:* Personal note + Update car log.
*   **`stop` (وقفة / مشوار):** *Action:* Personal (e.g., "جبت عيش من هنا").

**B. Recommendation: Hybrid Keyword + AI Batching**
Don't use AI for the "immediate" feedback (too slow/expensive). Use **Keywords** on the phone for instant confirmation, then use the **Cloudflare Worker** to "clean up" and summarize the notes using Gemini after the trip.

**Cloudflare Worker Prompt (Gemini 1.5 Flash):**
> "You are a road assistant in Egypt. Classify this Egyptian Arabic voice note into: pothole, danger, fuel, or personal. Extract the specific location or brand if mentioned (e.g., 'بنزينة شيل'). Return JSON: `{"cat": "...", "clean_text": "...", "is_community": true/false}`."

**Code Change (Keyword Logic):**
*Find in `saveNote`:*
```javascript
  notes.push({lat:p.lat, lon:p.lon, t:Date.now(), text:t}); save(); drawMarks();
  speak('تمام، سجلت ملاحظة');
```
*Replace with:*
```javascript
  let cat = 'note', msg = 'سجلت ملاحظة';
  if (/حفر[هة]|تكسير|مكسر/.test(t)) { cat = 'pothole'; msg = 'تمام، هفكرك بالحفرة دي المرة الجاية'; shareReport('pothole', p.lat, p.lon); }
  else if (/خطر|يوتيرن وحش|موت/.test(t)) { cat = 'danger'; msg = 'تمام، سجلت إن المكان ده خطر'; shareReport('danger', p.lat, p.lon); }
  else if (/بنزين[هة]|فول|تموين|شيل|توتال|وطني[هة]|امارات/.test(t)) { cat = 'fuel'; msg = 'تمام، سجلت البنزينة'; }
  notes.push({lat:p.lat, lon:p.lon, t:Date.now(), text:t, cat}); save(); drawMarks();
  speak(msg);
```

**Trip Summary Presentation:**
*Find in `showAnalysis` (near notes):*
```javascript
    + ((an.notes || []).length ? `<div class="note" style="margin-top:4px">📝 ملاحظاتك: ${an.notes.map(esc).join(' · ')}</div>` : '') + alt;
```
*Replace with:*
```javascript
    + ((an.notes || []).length ? `<div class="note" style="margin-top:4px">📝 <b>ملاحظات الطريق:</b><br>${an.notes.map(n => {
        const ic = {pothole:'🕳️', danger:'⚠️', fuel:'⛽'}[n.cat] || '📌';
        return ic + ' ' + esc(n.text);
      }).join('<br>')}</div>` : '') + alt;
```

---

### 2. Hands-Free Wake Word: "سكّتي"

**Recommendation: Android `SpeechRecognizer` in the Foreground Service.**
*   **Picovoice:** Too expensive/complex for a PWA.
*   **Vosk:** Too heavy for a single-file project.
*   **Android `SpeechRecognizer`:** Best for this. Since we already have a **Foreground Service** (via the background-geolocation plugin), we can keep the microphone listener active *only* when `navOn` is true.

**Java Implementation (BubblePlugin.java):**
We add a simple listener that stays active. *Note: Android 14 requires the `FOREGROUND_SERVICE_MICROPHONE` type if the app is in background, but since we are an overlay, we can trigger it from the Bubble.*

*In `BubblePlugin.java`, add these members:*
```java
private android.speech.SpeechRecognizer recognizer;
private Intent recognizerIntent;
```

*Add this method to start listening for the wake word:*
```java
@PluginMethod
public void startWakeWord(PluginCall call) {
    main.post(() -> {
        if (recognizer != null) return;
        recognizer = android.speech.SpeechRecognizer.createSpeechRecognizer(app());
        recognizerIntent = new Intent(android.speech.RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        recognizerIntent.putExtra(android.speech.RecognizerIntent.EXTRA_LANGUAGE, "ar-EG");
        recognizerIntent.putExtra(android.speech.RecognizerIntent.EXTRA_PARTIAL_RESULTS, true);
        
        recognizer.setRecognitionListener(new android.speech.RecognitionListener() {
            public void onPartialResults(Bundle b) {
                ArrayList<String> matches = b.getStringArrayList(android.speech.SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null) for (String s : matches) if (s.toLowerCase().contains("سكتي")) {
                    emit("wake"); // Trigger mic in JS
                    break;
                }
            }
            public void onResults(Bundle b) { restart(); }
            public void onError(int e) { restart(); }
            private void restart() { if (recognizer != null) recognizer.startListening(recognizerIntent); }
            // ... other empty stubs ...
        });
        recognizer.startListening(recognizerIntent);
    });
    call.resolve();
}
```

---

### 3. Auto-End Pitfalls

The current logic is risky in Cairo's "extreme" traffic or specific stops.

**Pitfalls identified:**
1.  **The "6th October" Jam:** You can stay within 60m for 15 minutes on the bridge. The app would say "شكلك ركنت" and stop recording.
2.  **The "Chill" Petrol Station:** A queue at *Wataniya* on the Desert Road can take 15 minutes.

**Proposed Fixes:**
1.  **The "High-Speed Memory" Guard:** If the car was doing > 60 km/h in the last 10 minutes, don't auto-end for "parking" (12 min rule) unless the distance to destination is < 200m.
2.  **Voice Confirmation:** Before saving, ask. If the driver says "لا" or "لسه", reset the timer.

**Code Change (index.html):**
*Find in `autoArrive`:*
```javascript
  const why = nav.nearSince && now - nav.nearSince > 40000 ? 'arrive' : now - nav.still.t > 12 * 60000 ? 'parked' : '';
```
*Replace with:*
```javascript
  const recentFast = pts.slice(-50).some(p => (p.v * 3.6) > 40);
  const isParked = now - nav.still.t > 12 * 60000 && (!recentFast || near);
  const why = nav.nearSince && now - nav.nearSince > 45000 ? 'arrive' : isParked ? 'parked' : '';
```

---

### 5 Things to make drivers tell their friends:

1.  **"بتقولي الرادار فين بالظبط":** The directional alerts (not alerting for the other side of the road) build massive trust.
2.  **"وفرتلي بنزين":** The fuel cost in the trip summary makes the "cost of traffic" real.
3.  **"سكتي يا سكتي":** The wake word makes it feel like a high-end car assistant (Mercedes MBUX style) but in Egyptian.
4.  **"حفظتلي الحفرة":** When the app says "خد بالك في حفرة قدام" based on a note they made a week ago, it feels like the app is "looking out" for them.
5.  **"خفيفة على الموبايل":** It doesn't heat up the phone like running Google Maps + a heavy Dashcam app simultaneously.

**Final Polish (Egyptian Arabic):**
Change the auto-end message to be more friendly:
*Find:* `speak(why === 'arrive' ? 'وصلت، حمد الله على السلامة. حفظت الرحلة' : 'شكلك ركنت، فحفظت الرحلة...');`
*Replace with:* `speak(why === 'arrive' ? 'حمد الله على السلامة، وصلت بالسلامة. حفظتلك الرحلة' : 'شكلك ركنت هنا، فهقفل التسجيل عشان أحافظ على البطارية. لو لسه مكمل دوس ابدأ السواقة تاني');`
