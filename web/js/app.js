import { Client, handle_file } from "https://cdn.jsdelivr.net/npm/@gradio/client@1/dist/index.min.js";
import { validateText, validateImage, isValidSpaceId, pct, sentimentEmoji } from "./utils.js";

const $ = (id) => document.getElementById(id);
let client = null;
let connectedId = null;

// ---------- Space config ----------
async function loadSpaceId() {
  const saved = localStorage.getItem("spaceId");
  if (saved && isValidSpaceId(saved)) return saved;
  try {
    const res = await fetch("config.json", { cache: "no-store" });
    if (res.ok) {
      const cfg = await res.json();
      if (isValidSpaceId(cfg.spaceId)) return cfg.spaceId;
    }
  } catch { /* ignore */ }
  return "";
}

async function getClient() {
  const id = $("space-id").value.trim();
  if (!isValidSpaceId(id)) throw new Error("Set a valid Hugging Face Space ID (user/space) in Settings.");
  if (client && connectedId === id) return client;
  setStatus(`Connecting to ${id}… (first call can take ~1 min while the Space wakes up)`);
  client = await Client.connect(id);
  connectedId = id;
  setStatus(`Connected to ${id}`, "ok");
  return client;
}

function setStatus(msg, kind = "") {
  const el = $("status");
  el.textContent = msg;
  el.className = `status ${kind}`;
}

function showError(target, err) {
  const msg = err?.message || String(err);
  target.innerHTML = `<div class="error">⚠️ ${escapeHtml(msg)}</div>`;
  setStatus(msg, "err");
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// ---------- Tabs ----------
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.setAttribute("aria-selected", b === btn));
    document.querySelectorAll(".panel").forEach((p) => (p.hidden = p.id !== btn.dataset.panel));
  });
});

// ---------- Image caption ----------
const fileInput = $("image-input");
fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  const v = validateImage(file);
  $("caption-result").innerHTML = "";
  if (!v.ok) { showError($("caption-result"), v.error); $("preview").hidden = true; return; }
  $("preview").src = URL.createObjectURL(file);
  $("preview").hidden = false;
});

$("caption-btn").addEventListener("click", async () => {
  const out = $("caption-result");
  const file = fileInput.files[0];
  const v = validateImage(file);
  if (!v.ok) return showError(out, v.error);
  const btn = $("caption-btn");
  btn.disabled = true;
  out.innerHTML = `<div class="loading">Generating caption…</div>`;
  try {
    const c = await getClient();
    const res = await c.predict("/caption", { image: handle_file(file) });
    out.innerHTML = `<div class="card"><h3>Caption</h3><p class="caption">${escapeHtml(res.data[0])}</p></div>`;
    setStatus("Caption generated", "ok");
  } catch (err) {
    showError(out, err);
  } finally {
    btn.disabled = false;
  }
});

// ---------- Text analysis ----------
$("text-input").addEventListener("input", (e) => {
  $("char-count").textContent = `${e.target.value.length} / 5000`;
});

$("examples").addEventListener("click", (e) => {
  if (e.target.dataset.example) $("text-input").value = e.target.dataset.example;
});

$("analyze-btn").addEventListener("click", async () => {
  const out = $("text-result");
  const v = validateText($("text-input").value);
  if (!v.ok) return showError(out, v.error);
  const btn = $("analyze-btn");
  btn.disabled = true;
  out.innerHTML = `<div class="loading">Analyzing…</div>`;
  try {
    const c = await getClient();
    const res = await c.predict("/analyze", { text: v.value });
    out.innerHTML = renderAnalysis(res.data[0]);
    setStatus("Analysis complete", "ok");
  } catch (err) {
    showError(out, err);
  } finally {
    btn.disabled = false;
  }
});

function bar(label, score) {
  return `<div class="bar-row"><span>${escapeHtml(label)}</span><div class="bar"><div style="width:${pct(score)}"></div></div><span>${pct(score)}</span></div>`;
}

function renderAnalysis(r) {
  const s = r.sentiment;
  return `
  <div class="card"><h3>Sentiment: ${sentimentEmoji(s.label)} ${escapeHtml(s.label)}</h3>
    ${Object.entries(s.scores).map(([k, v]) => bar(k, v)).join("")}</div>
  <div class="card"><h3>Top emotions</h3>
    ${r.emotions.map((e) => bar(e.emotion, e.score)).join("")}</div>
  <div class="card"><h3>Stats</h3>
    <p>${r.stats.words} words · ${r.stats.sentences} sentences · ${r.stats.characters} characters</p></div>`;
}

// ---------- Settings ----------
$("save-space").addEventListener("click", () => {
  const id = $("space-id").value.trim();
  if (!isValidSpaceId(id)) return setStatus("Invalid Space ID. Use the format user/space.", "err");
  localStorage.setItem("spaceId", id);
  client = null;
  setStatus(`Saved Space ID ${id}`, "ok");
});

(async () => {
  const id = await loadSpaceId();
  $("space-id").value = id;
  if (id) {
    $("space-link").href = `https://huggingface.co/spaces/${id}`;
    setStatus(`Backend: ${id} (live Hugging Face inference, no mock data)`);
  } else {
    setStatus("No backend configured yet. Deploy the Space via GitHub Actions or enter a Space ID below.", "err");
  }
})();
