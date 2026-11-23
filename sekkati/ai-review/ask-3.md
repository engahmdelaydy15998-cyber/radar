Round 2 applied (see the updated code):
- #1 plan() race: fixed with planSeq.
- #2 Directional alerts. Instead of tightening the angle (that would drop cameras on curves), cameras now carry the OSM `direction` tag (camDir: degrees or N/NE…). facesMe() drops a camera whose direction differs from the travel heading by more than 60°. This applies in free drive (current heading; the lateral window is now 35 m) and when matching cameras to a route (the route's own bearing at that point).
- #3 Dedupe along the route: 120 m.
- #4 Personal factor: learnFF() takes the median of dur/osrm over the last 10 trips. an.osrm is stored only when an OSRM route overlaps the driven track by 85% or more. The result is clamped to 1..2.5.
- #5 Fuel cost in the trip list.
- #6 Crawl time (< 10 km/h) counted separately as an.crawl and shown as "🐢 زحمة". The stop definition is unchanged (changing STOP_V would break stop counting).
- #7 Skipped: the bubble text already includes "الحد NN".

FINAL ROUND (3)
1. Review the round-1 and round-2 changes in the attached code for bugs (speech queue sayQ/sayNext/sayRaw, thin(), save() fallback, favPending / home-work, battery methods in BubblePlugin, camDir/facesMe, learnFF, crawl). Quote any problem and give the exact fix.
2. Then give the **5 best polish items** for the driver experience (UX text, alerts, first-run, trust). Keep them small and safe, with exact find→replace blocks.
3. End with a short list of "big next steps" you'd recommend for the future (no code), ranked.
