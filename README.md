# رادار (Radar)

A small dark feed app for AI and code news. It installs on Android from Chrome, takes links through the share menu, and refreshes itself every six hours from YouTube channels, Hacker News and GitHub.

- `index.html`, `sw.js`, `manifest.webmanifest`: the app.
- `scripts/collect.py`: the collector. Edit the `CHANNELS` list to change which YouTube channels are followed.
- `.github/workflows/update.yml`: runs the collector on a schedule and publishes the site.
- `data.json`: the feed the app reads. Written by the workflow.
- `watches.json`, `scripts/add_watch.py`, `.github/workflows/add-watch.yml`: a short list of recurring problems to watch for. Added via the app's "متابعة مشكلة" button (or by Claude, from a chat session) opening a pre-filled issue; the collector flags any matching item with `item.watch`. No push notification yet — matches only show up when the app is opened.
