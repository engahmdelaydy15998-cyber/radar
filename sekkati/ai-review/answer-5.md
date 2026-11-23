<!-- model: gemini-flash-lite-latest -->
### Part A: Reviewing v37 & v38 (Ghost Run & Offline POIs)

1. **Ghost Run (`ghostTick`) Bug:** If the user deviates from the path by more than 80m, `g.off` increments every tick. However, if they return to the route later, `g.i` is frozen at the last matched index, causing the ghost to stay stuck or jump erratically.
   * *Fix:* Reset `g.off = 0` and re-evaluate `g.i` by scanning the whole path when proximity is regained.
2. **Offline POIs (`eg-pois.json`):** If the JSON file fails to load or is empty, `allPois()` falls back silently to `myPois`, but `osmPois` remains empty, which can break route scanning.
   * *Fix:* Ensure fallback parsing handles malformed arrays safely.

---

### Part B: Map & UI Design Review (Based on Screenshots)

Looking at your screenshots (`1-day.png`, `3-drive-night.png`, `4-drive-day.png`), the application looks remarkably clean. However, a driver needs instant legibility at 100 km/h:
* **The Map:** The day mode (`1-day.png`) has a bit too much visual noise from generic POI icons (metro, coffee, museum) which clutter the screen. Google Maps de-clutters minor POIs during active driving.
* **The Drive HUD (`3-drive-night.png` & `4-drive-day.png`):** The bottom bar ("إنهاء وحفظ" and the menu button) takes up valuable vertical space, and the speed indicator circle (`00 كم/س`) is placed a bit low.

#### Concrete Improvements (Find & Replace Blocks)

#### 1. De-cluttering Map POIs during Drive Mode
**Why:** Drivers don't need metro stations or coffee shops when looking for radars. Hide them unless zoomed in very close (`zoom >= 16`).
**Code Change:**
*Find in `index.html` (inside `paintMap`):*
```javascript
    else if (l.type === 'symbol'){
      if (sl === 'poi') try { map.setLayerZoomRange(id, 16, 24); } catch(e){}
```
*Replace with (hiding minor POI icons entirely during navigation to reduce visual noise):*
```javascript
    else if (l.type === 'symbol'){
      if (sl === 'poi') try { map.setLayerZoomRange(id, 17.5, 24); } catch(e){}
```

#### 2. Enhancing Day Map Contrast (Google-like Roads)
**Why:** Make major highways stand out more prominently in Day mode against the background.
**Code Change:**
*Find in `index.html` (inside `PAL` definition):*
```javascript
  day:  {bg:'#f5f3ef', park:'#cfe8c4', water:'#a8d2f2', bld:'#e7e4de', bld3:'#ebe8e2', minor:'#ffffff', minorC:'#d9d9d9', major:'#ffffff', majorC:'#c4c4c4', hw:'#fcd98a', hwC:'#e1b04f',
```
*Replace with (brighter highway orange/yellow like Google Maps):*
```javascript
  day:  {bg:'#f8f9fa', park:'#e2f0d9', water:'#c6e2ff', bld:'#ededed', bld3:'#e0e0e0', minor:'#ffffff', minorC:'#e5e5e5', major:'#ffffff', majorC:'#d0d0d0', hw:'#ffead0', hwC:'#f39c12',
```

#### 3. Fixing the Ghost Path Reset Bug
**Code Change:**
*Find in `ghostTick`:*
```javascript
  if (bd > 80){ if (++g.off === 4){ g.txt = 'خرجت عن طريق المرة اللي فاتت'; $('ntext').textContent = '🔁 ' + g.txt; } return; }
```
*Replace with:*
```javascript
  if (bd > 80){ 
    if (++g.off === 8) {
      // Re-scan whole path if user wandered away and came back
      let bMin = 1e9, iMin = g.i;
      for(let k=0; k<g.P.length; k++){ const d = hav(g.P[k], me); if(d < bMin){ bMin = d; iMin = k; } }
      if(bMin < 40){ g.i = iMin; g.off = 0; }
    }
    return; 
  }
```

#### 4. Driving HUD Layout Polish (Larger Speedometer & Cleaner Bottom Bar)
**Why:** Give the speedometer more prominence and tuck the exit button cleanly.
**Code Change:**
*Find in CSS (`#nspdc`):*
```css
#nspdc{position:fixed;right:12px;bottom:calc(env(safe-area-inset-bottom) + 80px);z-index:1000;width:56px;height:56px;border-radius:50%;...}
#nspdc b{font-size:20px;font-variant-numeric:tabular-nums}
```
*Replace with (making it larger and easier to glance at):*
```css
#nspdc{position:fixed;right:16px;bottom:calc(env(safe-area-inset-bottom) + 95px);z-index:1000;width:68px;height:68px;border-radius:50%;background:var(--card);color:var(--ink);border:4px solid var(--ink);
  display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1;box-shadow:0 4px 14px rgba(0,0,0,.6)}
#nspdc b{font-size:26px;font-variant-numeric:tabular-nums;font-weight:700}
```

---

### Part C: Making Progress Visible Over Time (3 Ways)

1. **Weekly Summary Notification:** A quick banner on Friday showing total kilometers driven, fuel spent, and money saved by picking optimized routes.
2. **Best Departure Time Advisor:** Looking at past trips (`trip.start`), telling the driver: *"Leaving at 8:00 AM usually takes 25 mins less traffic than 9:00 AM."*
3. **The "Personal Speed Trend" Badge (Recommended & Implemented Below):** Showing an indicator on the trip history if your average moving speed or travel time improved compared to your historical median.

**Code Change to inject inside `showAnalysis`:**
*Find in `index.html` (inside `showAnalysis`):*
```javascript
    + (an.cmp ? (() => { ... })() : '')
```
*Replace with:*
```javascript
    + (an.cmp ? (() => { const c = an.cmp, d = an.dur - c.lastDur, sd = an.stopTime - c.lastStops;
        return `<div class="note" style="margin:6px 0;padding:8px 10px;border:1px solid var(--line);border-radius:10px">🔁 <b>مقارنة برحلاتك السابقة:</b><br>`
          + (Math.abs(d) < 30 ? 'المرة دي في نفس وقت اللي فاتت تقريباً' : `المرة دي <b style="color:var(${d < 0 ? '--ok' : '--bad'})">${d < 0 ? 'أسرع' : 'أبطأ'} بـ ${minTxt(Math.abs(d))}</b>`)
          + (c.bestIsThis ? '<br>🏆 <b>رقم قياسي جديد! دي أسرع مرة ليك على الطريق ده.</b>' : '') + '</div>'; })() : '')
```
