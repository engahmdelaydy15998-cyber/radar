You are a senior mobile/PWA engineer and a UX designer for drivers in Egypt. Above is the full code of "سكّتي" (Sekkati) and a summary of the project. Another AI (Claude) built it with the user over 33 versions. Claude will read your reply and apply the good ideas, then come back to you for more rounds.

Please:
1. Review the app honestly as the Egyptian driver who uses it daily on an Android phone, on top of Google Maps.
2. Find real bugs (logic, Android/Capacitor, background GPS, the bubble, voice, storage, edge cases) with the exact place in the code.
3. Propose the **10 most valuable improvements**, ranked by value for that driver. Each one gets:
   - what and why (one or two lines)
   - the concrete code change, as exact "find this text → replace with this text" blocks against the current files, or a small new function plus where it's called
   - the risk, if any
4. Keep within the constraints: no Google Maps scraping, no paid services, no server for now, a single-file web app (no bundler), Arabic (Egyptian) UI text, and keys stay on the user's device.

Answer in English for the technical parts. Write any user-facing UI text in Egyptian Arabic.
