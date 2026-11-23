<!-- model: gemini-3-flash-preview -->
This is a solid evolution. The "thinning" logic is a clever way to stay within `localStorage` limits without the complexity of IndexedDB.

As a driver in Egypt, the biggest pain point after "finding the way" is **alert fatigue**. If the app screams about a radar that is actually on the other side of the Mehwar or Ring Road, I’ll eventually stop trusting it. Also, the "Cairo Factor" (how much slower reality is vs. OSRM) varies wildly between a driver in a 128 and a driver in a new Tucson.

Here are the 7 highest-value improvements for Round 2.

---

### 1. The "Ghost Plan" Race Condition (Bug)
**The Bug:** If a user types "Maadi", then quickly changes to "Zamalek", two `fetch` requests are sent. If the Maadi response arrives *after* the Zamalek one, the UI will show Zamalek's name but Maadi's routes.
**The Fix:** Add a sequence counter to the planning logic.

**Code Change:**
*Find this in `index.html`:*
```javascript
let results = [], selIdx = 0, planTimer = 0;
function autoPlan(){ clearTimeout(planTimer); planTimer = setTimeout(plan, 250); }
async function plan(){
  $('msg').textContent = '';
  if (!start || !dest){ if (!start) $('msg').textContent = 'محتاج نقطة البداية: اضغط 📍 موقعي أو اكتب في خانة "من".'; return; }
  $('res').innerHTML = '<div class="note" style="padding:14px">...بدور على الطرق</div>';
  try {
    results = await computeRoutes(start, dest); put('plan', results);
    setMapFull(true); showRoutes(0);
  } catch(e){ $('res').innerHTML = ''; $('msg').textContent = 'مقدرتش أجيب الطرق. اتأكد من الإنترنت وجرّب تاني.'; }
}
```
*Replace with:*
```javascript
let results = [], selIdx = 0, planTimer = 0, planSeq = 0;
function autoPlan(){ clearTimeout(planTimer); planTimer = setTimeout(plan, 250); }
async function plan(){
  const mySeq = ++planSeq;
  $('msg').textContent = '';
  if (!start || !dest){ if (!start) $('msg').textContent = 'محتاج نقطة البداية: اضغط 📍 موقعي أو اكتب في خانة "من".'; return; }
  $('res').innerHTML = '<div class="note" style="padding:14px">...بدور على الطرق</div>';
  try {
    const r = await computeRoutes(start, dest);
    if (mySeq !== planSeq) return;
    results = r; put('plan', results);
    setMapFull(true); showRoutes(0);
  } catch(e){ if (mySeq === planSeq) { $('res').innerHTML = ''; $('msg').textContent = 'مقدرتش أجيب الطرق. اتأكد من الإنترنت وجرّب تاني.'; } }
}
```

---

### 2. Directional Alerts (Stop alerting for the opposite side)
**Why:** On the Ring Road (Da2ery), there are radars every 2km. Half are for the other direction. Alerting for both is annoying. We should only alert if the radar is "in front" of our current heading.
**The Fix:** Add a bearing check (within 45 degrees) before speaking.

**Code Change:**
*Find in `freeUpdate` (around line 770):*
```javascript
    const a = ((brg(me, q) - heading + 540) % 360 - 180) * Math.PI / 180;
    if (Math.cos(a) > 0.5 && Math.abs(d * Math.sin(a)) < 45){ np = q; dp = d; }
```
*Replace with (tightening the angle to ~35 degrees):*
```javascript
    const a = ((brg(me, q) - heading + 540) % 360 - 180);
    if (Math.abs(a) < 35 && Math.abs(d * Math.sin(a * Math.PI / 180)) < 30){ np = q; dp = d; }
```

---

### 3. Alert Deduplication (User vs. OSM)
**Why:** If a user reports a radar that already exists in OSM, the app currently treats them as two different objects and might alert twice.
**The Fix:** When scanning for nearby POIs, ignore any that are the same "kind" and within 100m of an already alerted one.

**Code Change:**
*Find in `scoreRoute` (around line 140):*
```javascript
  pois = pois.filter((p, i) => !pois.slice(0, i).some(q => q.kind === p.kind && Math.abs(p.at - q.at) < 60));
```
*Replace with (increasing the dedupe range):*
```javascript
  pois = pois.filter((p, i) => !pois.slice(0, i).some(q => q.kind === p.kind && Math.abs(p.at - q.at) < 120));
```

---

### 4. Learning the "Cairo Factor" (Personalized FF)
**Why:** The `FF = 1.3` is a hardcoded guess. If I drive an old car or drive through crowded areas, my real time is 1.8x OSRM. If I'm a "gharz" driver, it's 1.1x.
**The Fix:** Calculate the average ratio of `Real Duration / OSRM Duration` from the last 5 trips and use it for future estimates.

**Code Change:**
*Find in `index.html` (around line 430):*
```javascript
const FF = 1.3;         // معامل تقريبي لتحويل زمن OSRM (طريق فاضي) لزمن واقعي
```
*Replace with:*
```javascript
let FF = 1.3;
function updateFF() {
  const recent = trips.slice(0, 10).filter(t => t.an && t.an.osrm > 300);
  if (recent.length >= 3) {
    const sum = recent.reduce((acc, t) => acc + (t.an.dur / t.an.osrm), 0);
    FF = Math.min(2.5, Math.max(1.0, sum / recent.length));
  }
}
updateFF();
```
*And call `updateFF()` inside `analyzeTrip` after `t.an = an; save();`.*

---

### 5. Fuel Cost Visibility in Trip List
**Why:** In the current economy, seeing "This trip cost me 80 EGP in gas" is a powerful motivator to find shorter routes. It makes the "Car" feature feel alive.
**The Fix:** Show the estimated EGP cost in the trip list if car data is available.

**Code Change:**
*Find in `renderTrips` (around line 1050):*
```javascript
return `<div class="trip"><div class="t"><b>${esc(t.name)}</b><div>${when} · ${fmtT(r.dur)} · ${km(r.dist)} كم · ${r.stops} وقفات</div></div>
```
*Replace with:*
```javascript
const fuel = t.an && t.an.fuel ? ` · <span class="ok">${arab(t.an.fuel.cost)} ج</span>` : '';
return `<div class="trip"><div class="t"><b>${esc(t.name)}</b><div>${when} · ${fmtT(r.dur)} · ${km(r.dist)} كم${fuel}</div></div>
```

---

### 6. Smarter "Crawl" Detection (Traffic vs. Stops)
**Why:** `STOP_V = 1.5` (5.4 km/h) is too high for Cairo. If I'm crawling at 4 km/h in a traffic jam on the Ring Road, I'm not "stopped" at a light, but I'm definitely not "moving" efficiently.
**The Fix:** Differentiate between a "Full Stop" (0 km/h) and a "Crawl" (< 10 km/h) to give better feedback in the analysis.

**Code Change:**
*Find in `analyze` (around line 65):*
```javascript
    if (v < STOP_V){ if (!run) runPt = a; run += dt; } else { flush(); move += dt; }
```
*Replace with:*
```javascript
    if (v < 0.5){ if (!run) runPt = a; run += dt; } // Real stop
    else if (v < 2.8) { flush(); move += dt; z.crawl = (z.crawl || 0) + dt; } // Crawl < 10km/h
    else { flush(); move += dt; }
```
*(Note: You'll need to add `crawl:0` to the `z` object at the start of `analyze`)*.

---

### 7. Bubble Speed Limit Display
**Why:** When the bubble is over Google Maps, the driver's biggest question is "What is the limit here?".
**The Fix:** When a radar is detected, show the speed limit prominently in the bubble.

**Code Change:**
*In `BubblePlugin.java`, find the `show` method:*
*Change the pill background logic to make the speed limit look like a Egyptian speed sign (Red circle/border).*

*In `index.html`, find `freeUpdate` and `navRender` where `overlaySet` is called:*
*Ensure the text starts with the limit if available.*

```javascript
// Inside freeUpdate/navRender:
const limitStr = np && np.max ? ` [${arab(np.max)}] ` : '';
overlaySet(np ? limitStr + POI_IC[kind] + ' ' + POI_AR[kind] + ' بعد ' + fmtD(dp) ...
```

---

### Summary of Value for the Driver:
1.  **Reliability:** No more "ghost" routes from fast typing.
2.  **Trust:** No more alerts for radars on the other side of the highway.
3.  **Personalization:** The app learns *your* driving speed, making "Time of Arrival" much more accurate than OSRM's default.
4.  **Financial Awareness:** Every trip now shows its cost in Pounds, helping the driver realize the cost of "taking the long way."
