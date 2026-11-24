Round 7: two driver requests after a real trip. Short, concrete answers please (Arabic UI text in Egyptian dialect).

1) VOICE NOTES + AI. Today, any sentence said to the bubble mic that is not a known report (radar/toll/checkpoint/jam...) is saved as `notes.push({lat, lon, t, text})` and drawn on the map. The driver meets many other things: potholes (حفر), broken road, a good fuel station, a dangerous U-turn, a place he stopped to do something. He wants these notes to "connect to AI" so the app decides what to do with them.
   - Propose a small fixed set of note categories for Egyptian roads, and which ones should become alerts next time (like bumps) vs. stay personal notes vs. be shared on the community server.
   - The phone has no AI key. Options: (a) Arabic keyword rules on the phone (give the keyword lists), (b) a free Cloudflare Worker that calls Gemini with the repo's key to classify a batch of notes after the trip. Recommend one and give the prompt/JSON schema for (b).
   - How should the trip summary present the notes (one line each)?

2) HANDS-FREE WAKE WORD "سكّتي" (like "Hey Google"), so the driver doesn't press the bubble then the mic. App is Capacitor Android; Google Maps is in front and our overlay bubble is visible. Compare for Egyptian Arabic, battery and cost: Picovoice Porcupine custom keyword, Vosk offline (Arabic model size), looping Android SpeechRecognizer during trips only, and any better option. Note Android 14 rules for microphone foreground services. Recommend one, with the main Java pieces.

3) Auto-end: we now end + save a free drive when the car stops 40 s within 90 m of the destination (or home/work), or stays within 60 m for 12 minutes. Any pitfalls (petrol station, long traffic light, parking hunt)?
