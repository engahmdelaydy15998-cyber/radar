Round 5. Round 4 got no answer (every model returned 503), so it is repeated here, plus the new map/driving work. SCREENSHOTS of the real app with real map tiles are attached (1-day, 2-night, 3-drive-night, 4-drive-day, 5-zoomed-by-hand, 6-recentred, 7-trip-minimised).

## Part A: the round-4 questions

1. v37 "🔁 امشيها تاني" (rideAgain / ghostOf / ghostTick / sameRoute, plus an.cmp in analyzeTrip and showAnalysis). The user said he felt no visible result, so he wants to drive the same trip again and see progress.
2. v38 alerts without reporting:
   - loadEgPois() reads sekkati/eg-pois.json, built by tools/sekkati_pois.py: Egypt-wide OSM cameras, tolls and checkpoints.
   - fetchPois() now also gets checkpoints and toll ways.
   - poisAround() fetches around the driver in free drive.
   - fastStops() / learnSpots() learn short stops between fast driving. After 2 trips they alert as kind 'spot'.

Please:
(a) Review these two features in the attached code for bugs and edge cases: loops in the track, starting mid-route, GPS gaps, thinned tracks, an empty or huge eg-pois.json, Overpass throttling, the same spot learned twice, traffic lights mistaken for tolls. Quote the code and give exact find→replace fixes.
(b) Suggest the **5 most valuable improvements** so the driver gets reliable radar/toll/checkpoint alerts **with zero interaction**. Ideas welcome:
   - better OSM tags or other free open data sources for Egyptian speed cameras (be specific and honest about what exists)
   - inferring from his own trips
   - smarter timing and wording of alerts
   Give exact code for the ones that are small.
(c) Suggest **3 ways to make the progress visible** to the driver over time, using the data already collected (trips, an.cmp, crawl, stops, fuel). Examples: a weekly summary, best departure time for a route, a trend. Give exact code for the best one.

Prefer small, safe changes. Find→replace blocks must match the current files exactly.

## Part B: new since round 4 (v39–v40). The user asked for a map "like Google Maps in day/night mode, very clean, not satellite"; a car that turns with him; re-centering after a manual zoom; and opening the menu/settings without ending the trip.
- paintMap() with PAL.day / PAL.night recolours the OpenFreeMap (OpenMapTiles) style by source-layer. POI icons only show from zoom 16.
- Arabic labels were broken (letters disconnected and reversed), because of a wrong rtl-text plugin URL and a version mismatch. rtl-text 0.2.3 is now bundled.
- Car marker: carMarker() / CAR_SVG, rotationAlignment map, pitchAlignment viewport.
- Camera: camFollow / camUser / recenter (8 s auto re-center, and a "⌖ رجّع على العربية" button).
- Menu without ending the trip: minimizeNav / resumeNav, the ☰ button, a green pill, and Android back.

Please look at the screenshots and:
1. Judge the map design honestly against Google Maps day and night. Give exact PAL colour changes, plus any layer tweaks (widths, label sizes, which layers to hide or show by zoom) that would make it cleaner and more readable for a driver.
2. Judge the driving screen layout: top bar, speed circle, buttons, the car, the bottom bar. Suggest concrete CSS changes.
3. Review the camera/minimise code for bugs.
Use exact find→replace blocks against the current files.
