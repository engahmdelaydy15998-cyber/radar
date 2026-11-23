New round (4), at the user's request. Since round 3 Claude added two features. The user is an Egyptian driver who can't talk to or tap the phone while driving, and sometimes misses radars.

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
