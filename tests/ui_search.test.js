const { JSDOM } = require("jsdom");
const fs = require("fs");
const html = fs.readFileSync("/home/claude/radar-repo/index.html", "utf8").replace(/<link[^>]*fonts[^>]*>/g, "");
const calls = [];
const data = { updated: new Date().toISOString(), demo: false, items: [
  { id: "a1", cat: "agents", src: "Hacker News", ts: new Date().toISOString(), t: "Ollama ships X", ta: "أولاما تطلق X", s: "40 نقطة، 3 تعليق", tags: [], url: "https://e.com/1" } ]};
const gh = { items: [{ full_name: "o/repo", description: "agent tool", stargazers_count: 123, language: "Go", html_url: "https://github.com/o/repo" }] };
const hn = { hits: [{ title: "Ask HN: agent tips", points: 50, num_comments: 7, objectID: "9", url: "https://e.com/hn" }] };
const dom = new JSDOM(html, { url: "https://u.github.io/radar/", runScripts: "dangerously", pretendToBeVisual: true,
  beforeParse(w) {
    w.fetch = (u) => {
      calls.push(u);
      var body = u.includes("api.github.com") ? gh : u.includes("algolia") ? hn : data;
      return Promise.resolve({ ok: true, json: () => Promise.resolve(body) });
    };
    w.open = (u) => { calls.push("OPEN " + u); };
  } });
setTimeout(async () => {
  const w = dom.window, d = w.document;
  console.log("tiles:", [...d.querySelectorAll(".tile .nm")].map(x => x.textContent).join(","));
  const c = d.querySelector("article.card");
  console.log("card:", c.querySelector("h3").textContent, "|", c.querySelector("p").textContent);
  d.getElementById("btnSearch").click();
  d.getElementById("q").value = "agent"; d.getElementById("qGo").click();
  await new Promise(r => setTimeout(r, 100));
  console.log("sections:", [...d.querySelectorAll("#sres .sresh")].map(x => x.textContent).join(" | "));
  console.log("gh results:", d.querySelectorAll("#sres .rcard").length, d.querySelector("#sres .rcard b").textContent);
  console.log("external open-links:", d.querySelectorAll("#sres a[href*='search']").length);
  d.querySelector("#sres .go").click();
  console.log("saved mine:", w.localStorage.getItem("radar-mine") ? JSON.parse(w.localStorage.getItem("radar-mine")).length : 0);
  d.getElementById("q").value = "https://www.youtube.com/@Fireship"; d.getElementById("qGo").click();
  d.querySelector("#sres .go").click();
  console.log(calls.filter(x => x.startsWith("OPEN")).map(x => decodeURIComponent(x)).join("\n"));
  process.exit(0);
}, 500);
