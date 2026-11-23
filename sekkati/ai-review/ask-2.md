Thanks, round 1 was useful. Here is what Claude did with it (the attached files are the updated code):

APPLIED
- #3 Speeding warning now says the numbers ("هدّي السرعة، الحد ٦٠ وانت ٨٠").
- #5 Speech queue: speak() pushes to a queue (sayQ / sayNext / sayRaw). There's no cancel between alerts, stale items (over 12 s) are dropped, and a guard timeout keeps the queue moving.
- #6 Home/Work: "🏠 البيت / 💼 الشغل" appear in the search suggestions. Set them once, long-press to change. Stored as fav:home / fav:work and included in the backup.
- #10 License renewal and insurance added to CAR_ITEMS.
- #2 (partially) Instead of IndexedDB: saved tracks are thinned (thin(): one point per 5 m or 20 s, with identical analysis results). If localStorage is full, older trips are thinned again before giving up.
- #4 Native battery-optimisation exemption: BubblePlugin.batteryOk/requestBattery plus the REQUEST_IGNORE_BATTERY_OPTIMIZATIONS permission, a button in the bubble card, and a one-time ask when recording starts.

REJECTED (tell me if you disagree, with evidence)
- #1 The background-geolocation plugin's own manifest already merges FINE/COARSE location, FOREGROUND_SERVICE, FOREGROUND_SERVICE_LOCATION and POST_NOTIFICATIONS. It runs a foreground service, so ACCESS_BACKGROUND_LOCATION isn't needed.
- #7 Hard-coded fuel prices: they change, and the user types the price.
- #9 Dropping fixes with acc > 40 in onFix: analyze() already ignores acc > 50, and dropping fixes would break stop detection.
- #8 Bubble quick-radar: postponed.

ROUND 2 REQUEST
Now go deeper. Pick the **7 highest-value next steps** that would make this genuinely better than "Google Maps alone" for an Egyptian driver. Cover at least:
(a) a real bug or race you can find in the current code (quote it)
(b) making the alerts smarter and less annoying (dedupe, direction of travel, which side of a divided road the radar is on)
(c) the trip analysis and the "shorter road" discovery
(d) one feature that uses the data the user already collects (trips, stops, reports) in a clever way

Give exact find→replace code blocks against the current files, as before. Prefer small, safe changes over rewrites.
