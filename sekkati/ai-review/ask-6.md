Round 6: product review and plan. The user (the owner) asked for an honest list of the app's strengths and weaknesses, from Claude AND from you, separately. Then we turn weaknesses into strengths, grow the strengths, and prepare to hand the app to other Egyptian drivers. He wants it very easy for them: on first open, "1-2-3" things they can do immediately, with short, clear text everywhere. He thinks the map still needs the most work: it should feel comfortable for the eyes and easy to use.

Claude's view, for you to challenge:

STRENGTHS
1. Lives on top of Google Maps (floating bubble with one-tap reports and alerts), so drivers keep their usual navigation.
2. Free and offline. Bundled Egypt data from OpenStreetMap: tolls ~390, checkpoints ~470, speed bumps, and cameras (few). Gemini Arabic voice clips are bundled. No account, no key on the phone.
3. Learns from your own driving:
   - repeated short stops on fast roads become alerts
   - a personal ETA factor
   - "ride again" ghost (ahead/behind the last run)
   - automatic comparison with earlier runs of the same route (best departure time)
4. Trip analysis: stops, crawl time, fuel cost, shorter/faster road discovery.
5. Car maintenance and fuel reminders.
6. Privacy: everything stays on the phone.

WEAKNESSES
1. Speed cameras, the core promise: OSM has very few in Egypt. Radars come only from the driver's own one-tap reports. Mobile radars are impossible without other drivers.
2. Single-user: no crowd, so no live jams, accidents or mobile radars.
3. UI density: many cards and options, and no onboarding. A new user doesn't know where to start.
4. Map: recoloured OSM, still less polished than Google. In-app turn-by-turn (OSRM) has no live traffic or lanes.
5. Voice: bundled clips for fixed phrases. Dynamic sentences (trip summary, street names) fall back to the phone TTS, so the voice is mixed.
6. Setup friction: overlay permission, battery-optimisation exemption, location "allow all the time". Chinese phones kill background apps.
7. Distribution: an APK from GitHub. "Unknown sources" and Play Protect warnings scare people.
8. Mostly tested in simulation; real-road reliability is still unproven.

PLAN DRAFT
- A first-run wizard ("١ ٢ ٣"): permissions in one guided flow, choose a voice, then "start driving".
- A shared server (Cloudflare Worker + D1, free tier): anonymous reports (radar, mobile radar, checkpoint, jam, accident) with votes and expiry, synced every few minutes while driving. The fixed-radar map grows with every user.
- Map comfort: fewer options on screen, bigger labels, offline tiles for home and work.
- Distribution: a simple install page (QR code, 3 steps). Later the Play Store.

Please give:
(a) YOUR independent list of strengths and weaknesses. Don't just agree; add what Claude missed, judging from the code and the attached screenshots (SCREENSHOTS).
(b) For each weakness, one concrete way to reduce it or turn it into a strength.
(c) The best first-run onboarding for a non-technical Egyptian driver: the exact screens, with short Egyptian Arabic text for each, and what each button does.
(d) A critique of the shared-server design: data model, abuse and spam control without accounts, privacy, and how many confirmations before a radar is trusted.
(e) The 5 things that would make drivers tell their friends about this app.
Keep it concrete and short. Give code only for the onboarding, if you think it helps.
