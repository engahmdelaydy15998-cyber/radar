const { JSDOM } = require("jsdom");
const fs = require("fs");
const html = fs.readFileSync("/home/claude/radar-repo/index.html", "utf8").replace(/<link[^>]*fonts[^>]*>/g, "");
const now = Date.now();
const data = { updated: new Date().toISOString(), demo: false, items: [
  { id: "yt-A", cat: "reels", src: "YouTube", ts: new Date(now - 3*3600e3).toISOString(), t: "Short clip", s: "desc", tags: ["Co"], url: "https://www.youtube.com/shorts/A" },
  { id: "hn-1", cat: "code", src: "Hacker News", ts: new Date(now - 30*3600e3).toISOString(), t: "HN story", s: "150 نقطة", tags: [], url: "https://example.com/x" },
  { id: "yt-B", cat: "co", src: "YouTube", ts: new Date(now - 5*86400e3).toISOString(), t: "Company video", s: "", tags: ["Anthropic"], url: "https://www.youtube.com/watch?v=B" },
]};
const dom = new JSDOM(html, { url: "https://u.github.io/radar/", runScripts: "dangerously", pretendToBeVisual: true,
  beforeParse(w) { w.fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }); } });
setTimeout(() => {
  const d = dom.window.document;
  const tiles = [...d.querySelectorAll(".tile")].map(t => t.querySelector(".nm").textContent + ":" + t.querySelector(".cnt").textContent);
  console.log("tiles:", tiles.join(" | "));
  console.log("tiles outside header:", !d.querySelector("header .tile"));
  const cards = [...d.querySelectorAll("article.card")];
  console.log("cards:", cards.length);
  cards.forEach(c => console.log(" -", c.querySelector("h3").textContent, "|", c.querySelector(".when").textContent, "|", c.querySelector(".badge-new") ? "جديد" : "-", "|", c.querySelector("a.act.open").textContent.trim(), "|", c.querySelector(".badge-mine") ? "has badge" : "no badge"));
  console.log("demo note hidden:", d.getElementById("demoNote").hidden);
  console.log("src pills:", [...d.querySelectorAll("#srcPills .pill")].map(p => p.textContent).join(","));
  // click the reels tile
  [...d.querySelectorAll(".tile")][1].click();
  console.log("after reels click cards:", d.querySelectorAll("article.card").length, "pressed:", d.querySelectorAll('.tile[aria-pressed="true"] .nm')[0].textContent);
  process.exit(0);
}, 400);
