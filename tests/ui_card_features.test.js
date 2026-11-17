const { JSDOM } = require("jsdom");
const fs = require("fs");
const html = fs.readFileSync("/home/claude/radar-repo/index.html", "utf8").replace(/<link[^>]*fonts[^>]*>/g, "");
const now = Date.now();
const data = { updated: new Date().toISOString(), demo: false, items: [
  { id: "hn1", cat: "agents", src: "Hacker News", ts: new Date(now - 3*3600e3).toISOString(), t: "Ollama ships X", ta: "أولاما تطلق X", s: "40 نقطة، 3 تعليق", tags: ["نقاش"], url: "https://site.com/a", url2: "https://news.ycombinator.com/item?id=1" },
  { id: "yt1", cat: "arch", src: "YouTube", ts: new Date(now - 30*3600e3).toISOString(), t: "Revit AI plugin", ta: "إضافة ذكاء اصطناعي لريفيت", s: "A video about it", sa: "فيديو عنها", tags: ["ArchDaily"], url: "https://www.youtube.com/watch?v=1" },
]};
const dom = new JSDOM(html, { url: "https://u.github.io/radar/", runScripts: "dangerously", pretendToBeVisual: true,
  beforeParse(w) { w.fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve(data) }); w.navigator.share = (o) => { console.log("SHARE", JSON.stringify(o)); return Promise.resolve(); }; } });
setTimeout(() => {
  const d = dom.window.document;
  console.log("tiles:", [...d.querySelectorAll(".tile")].map(t => t.querySelector(".nm").textContent + " new=" + (t.querySelector(".cnt") ? t.querySelector(".cnt").textContent : "-") + " tot=" + t.querySelector(".tot").textContent).join(" | "));
  d.querySelectorAll("article.card").forEach(c => console.log("card:", c.querySelector("h3").textContent, "|", c.querySelector("p").textContent, "|", [...c.querySelectorAll(".actions .act")].map(a => (a.getAttribute("aria-label") || a.textContent.trim())).join(","), "| det hidden:", c.querySelector(".det").hidden));
  const c0 = d.querySelector("article.card");
  c0.querySelector('[aria-label="التفاصيل"]').click();
  console.log("after info click det hidden:", c0.querySelector(".det").hidden, "| det text:", c0.querySelector(".det").textContent);
  c0.querySelector('[aria-label="مشاركة"]').click();
  d.getElementById("btnExp").click();
  console.log("expand all hidden:", [...d.querySelectorAll(".det")].map(x => x.hidden).join(","), d.getElementById("btnExp").textContent);
  process.exit(0);
}, 500);
