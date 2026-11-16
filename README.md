# رادار (Radar)

A small dark feed app for AI and code news. It installs on Android from Chrome, takes links through the share menu, and refreshes itself every six hours from YouTube channels, Hacker News and GitHub.

- `index.html`, `sw.js`, `manifest.webmanifest`: the app.
- `scripts/collect.py`: the collector. Edit the `CHANNELS` list to change which YouTube channels are followed.
- `.github/workflows/update.yml`: runs the collector on a schedule and publishes the site.
- `data.json`: the feed the app reads. Written by the workflow.
