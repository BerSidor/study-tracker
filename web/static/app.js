"use strict";

/* ---------- tiny helpers ---------- */

const $ = (id) => document.getElementById(id);

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

// inline markdown: `code`, **bold**, *italic*, [text](url) — input is escaped first
function md(s) {
  return esc(s)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2" target="_blank">$1</a>');
}

// matches python fmt_hrs: "2h 05m" or "38m"
function fmtHrs(hrs) {
  const totalMin = Math.round(hrs * 60);
  const h = Math.floor(totalMin / 60), m = totalMin % 60;
  return h ? `${h}h ${String(m).padStart(2, "0")}m` : `${m}m`;
}

function fmtTimer(seconds) {
  seconds = Math.max(0, Math.floor(seconds));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

// seconds since HH:MM today; +24h if it looks like yesterday evening
function elapsedSec(hhmm) {
  const [h, m] = hhmm.split(":").map(Number);
  const start = new Date();
  start.setHours(h, m, 0, 0);
  let diff = (Date.now() - start.getTime()) / 1000;
  if (diff < 0) diff += 86400;
  return diff;
}

function minutesBetween(a, b) {
  const [ah, am] = a.split(":").map(Number);
  const [bh, bm] = b.split(":").map(Number);
  let d = bh * 60 + bm - (ah * 60 + am);
  if (d < 0) d += 1440;
  return d;
}

/* ---------- in-page notifications ---------- */

function notify(msg, type = "info") {
  const el = document.createElement("div");
  el.className = "note" + (type === "error" ? " error" : "");
  el.textContent = msg;
  $("notes").appendChild(el);
  setTimeout(() => {
    el.classList.add("out");
    setTimeout(() => el.remove(), 450);
  }, 4200);
}

const toast = (msg) => notify(msg, "error");

/* ---------- enchanted forest scene (generated foliage) ---------- */

function rng(seed) {
  let n = seed;
  return () => (n = (n * 9301 + 49297) % 233280) / 233280;
}

const SVGNS = "http://www.w3.org/2000/svg";

function circles(groupId, items) {
  const g = $(groupId);
  for (const it of items) {
    const c = document.createElementNS(SVGNS, "circle");
    c.setAttribute("cx", it.x.toFixed(0));
    c.setAttribute("cy", it.y.toFixed(0));
    c.setAttribute("r", it.r.toFixed(1));
    if (it.fill) c.setAttribute("fill", it.fill);
    if (it.cls) c.setAttribute("class", it.cls);
    if (it.style) c.setAttribute("style", it.style);
    g.appendChild(c);
  }
}

function band(groupId, y, count, rMin, rMax, jitterY, seed, x0 = -40, x1 = 1640) {
  const rand = rng(seed);
  const items = [];
  for (let i = 0; i < count; i++) {
    items.push({
      x: x0 + ((x1 - x0) * i) / (count - 1) + (rand() - 0.5) * 50,
      y: y + (rand() - 0.5) * 2 * jitterY,
      r: rMin + rand() * (rMax - rMin),
    });
  }
  circles(groupId, items);
}

function mass(groupId, cx, cy, count, spreadX, spreadY, rMin, rMax, seed) {
  const rand = rng(seed);
  const items = [];
  for (let i = 0; i < count; i++) {
    items.push({
      x: cx + (rand() - 0.5) * 2 * spreadX,
      y: cy + (rand() - 0.5) * 2 * spreadY,
      r: rMin + rand() * (rMax - rMin),
    });
  }
  circles(groupId, items);
}

function buildScene() {
  // thin trunks deep in the glow
  const g = $("distant-trunks");
  const rand = rng(11);
  for (let i = 0; i < 14; i++) {
    const x = 420 + rand() * 760;
    const w = 6 + rand() * 10;
    const h = 220 + rand() * 240;
    const rect = document.createElementNS(SVGNS, "rect");
    rect.setAttribute("x", x.toFixed(0));
    rect.setAttribute("y", (640 - h).toFixed(0));
    rect.setAttribute("width", w.toFixed(0));
    rect.setAttribute("height", h.toFixed(0));
    rect.setAttribute("rx", "3");
    g.appendChild(rect);
  }

  // canopy: lighter inner ring, then a dark frame thickest at edges/corners,
  // with a band of small leaves for texture along the lower edge
  band("canopy-far", 110, 26, 40, 80, 30, 31);
  band("canopy-far", 160, 40, 14, 30, 24, 37);
  band("canopy-dark", 20, 30, 60, 110, 35, 47);
  band("canopy-dark", 95, 46, 18, 42, 28, 49);
  mass("canopy-dark", 120, 170, 16, 190, 120, 50, 105, 53);
  mass("canopy-dark", 1480, 160, 16, 190, 120, 50, 105, 59);
  mass("canopy-dark", 330, 60, 10, 130, 70, 45, 90, 61);
  mass("canopy-dark", 1270, 55, 10, 130, 70, 45, 90, 67);
  mass("canopy-dark", 150, 320, 12, 90, 110, 22, 55, 101);
  mass("canopy-dark", 1450, 310, 12, 90, 110, 22, 55, 103);

  // undergrowth rows (sunlit tops in the middle where the clearing glows)
  band("bush-mid", 740, 30, 30, 60, 18, 71);
  mass("bush-glow", 800, 728, 16, 330, 16, 14, 34, 113);
  band("bush-low", 800, 32, 28, 55, 15, 79);
  band("bush-front", 880, 26, 45, 85, 18, 83);
  mass("bush-front", 90, 800, 10, 140, 70, 40, 85, 89);
  mass("bush-front", 1510, 800, 10, 140, 70, 40, 85, 97);

  // flowers sprinkled on the bush tops, clustered toward the open margins
  const fr = rng(123);
  const palette = ["#e8923f", "#f0c952", "#f5f1dd", "#e8923f", "#f0c952"];
  const flowers = [];
  const spot = () => {
    const lane = fr();
    if (lane < 0.35) return 30 + fr() * 290;        // left margin
    if (lane < 0.7) return 1280 + fr() * 290;       // right margin
    return 330 + fr() * 950;                        // center, behind cards
  };
  for (let i = 0; i < 90; i++) {
    flowers.push({
      x: spot(),
      y: 690 + fr() * 150,
      r: 2.6 + fr() * 3.2,
      fill: palette[Math.floor(fr() * palette.length)],
    });
  }
  circles("flowers", flowers);

  // fireflies drifting in the clearing
  const ff = rng(7);
  const flies = [];
  for (let i = 0; i < 14; i++) {
    const x = 350 + ff() * 900;
    const y = 220 + ff() * 420;
    const dur = (8 + ff() * 8).toFixed(1);
    const delay = (-ff() * 12).toFixed(1);
    flies.push({
      x, y, r: 7 + ff() * 6, fill: "#fdf6c5", cls: "fly halo",
      style: `animation-duration:${dur}s;animation-delay:${delay}s`,
    });
    flies.push({
      x, y, r: 1.8 + ff() * 1.6, fill: "#fdf6c5", cls: "fly",
      style: `animation-duration:${dur}s;animation-delay:${delay}s`,
    });
  }
  circles("fireflies", flies);
}

buildScene();

/* ---------- app state ---------- */

let state = null;        // /api/state
let plan = null;         // /api/plan
let history = null;      // /api/history
let topics = null;       // /api/topics
let lastVersion = null;
let pendingAction = null; // "start" | "switch"
let connectionLost = false;
let prevSnap = null;       // for detecting external session changes
let suppressNotify = false; // set while a browser-initiated action refreshes

async function getJSON(url) {
  const r = await fetch(url);
  const body = await r.json();
  if (!r.ok) throw new Error(body.error || `${url} -> ${r.status}`);
  return body;
}

function snapshot() {
  const mode = sessionMode();
  return {
    mode,
    topic: state.current
      ? state.current.segments[state.current.segments.length - 1].topic
      : null,
  };
}

function emitTransition(prev, cur) {
  if (prev.mode === cur.mode && prev.topic === cur.topic) return;
  if (prev.mode === "idle" && cur.mode === "active") {
    notify(`Session started — ${cur.topic}`);
  } else if (cur.mode === "idle") {
    notify("Session ended & saved");
  } else if (cur.mode === "paused" && prev.mode === "active") {
    notify("Session paused");
  } else if (cur.mode === "active" && prev.mode === "paused" && prev.topic === cur.topic) {
    notify("Session resumed");
  } else if (cur.mode === "active" && prev.topic !== cur.topic) {
    notify(`Now studying: ${cur.topic}`);
  }
}

async function refreshState() {
  state = await getJSON("/api/state");
  const snap = snapshot();
  if (prevSnap && !suppressNotify) emitTransition(prevSnap, snap);
  prevSnap = snap;
  renderState();

  const v = state.version;
  if (lastVersion) {
    if (v.plans !== lastVersion.plans) { refreshPlan(); refreshTopics(); }
    if (v.sessions !== lastVersion.sessions) { refreshHistory(); refreshTopics(); }
  }
  lastVersion = v;
}

async function refreshPlan() {
  plan = await getJSON("/api/plan");
  renderPlanBadge(); renderTodayPlan(); renderPlanTab();
}

async function refreshHistory() {
  history = await getJSON("/api/history");
  renderHistoryTab();
}

async function refreshTopics() {
  topics = await getJSON("/api/topics");
  renderTopicOptions();
}

async function poll() {
  try {
    await refreshState();
    if (connectionLost) { connectionLost = false; toast("Reconnected."); }
  } catch (e) {
    if (!connectionLost) { connectionLost = true; toast("Lost contact with the tracker server."); }
  }
}

/* ---------- live numbers (1s tick) ---------- */

function liveOpenHrs() {
  if (!state || !state.openSegmentStart) return 0;
  return elapsedSec(state.openSegmentStart) / 3600;
}

function tick() {
  const now = new Date();
  $("clock").textContent = now.toLocaleTimeString("en-GB");
  if (!state) return;

  const open = liveOpenHrs();
  const sessionHrs = state.currentClosedHrs + open;
  $("timer").textContent = fmtTimer(sessionHrs * 3600);

  setBar("today", state.todayClosedHrs + state.currentClosedHrs + open, state.dailyTargetHours);
  setBar("week", state.weekHrs + state.currentClosedHrs + open, state.weeklyGoalHours);
}

function setBar(name, value, target) {
  const pct = target > 0 ? value / target : 0;
  const fill = $(`${name}-fill`);
  fill.style.width = `${Math.min(100, pct * 100)}%`;
  fill.classList.toggle("over", pct >= 1);
  $(`${name}-label`).textContent =
    `${fmtHrs(value)} / ${fmtHrs(target)} · ${Math.round(pct * 100)}%`;
}

/* ---------- rendering ---------- */

function sessionMode() {
  if (!state || !state.current) return "idle";
  return state.openSegmentStart ? "active" : "paused";
}

function renderState() {
  const mode = sessionMode();
  const lamp = $("lamp");
  lamp.className = "lamp" + (mode === "active" ? " active" : mode === "paused" ? " paused" : "");
  $("status-word").textContent =
    mode === "active" ? "Studying" : mode === "paused" ? "Paused" : "Resting";

  if (state.current) {
    const last = state.current.segments[state.current.segments.length - 1];
    $("topic-line").textContent = last.topic;
  } else {
    $("topic-line").textContent = "No session — the forest is quiet.";
  }

  $("date-line").textContent = new Date().toLocaleDateString("en-GB", {
    weekday: "long", day: "numeric", month: "long",
  });
  $("sync-off").classList.toggle("hidden", state.syncEnabled);

  renderChips();
  setButtons(mode);
  tick();
}

function renderChips() {
  const box = $("segment-chips");
  box.innerHTML = "";
  if (!state.current) return;
  let prevEnd = null;
  for (const seg of state.current.segments) {
    if (prevEnd && prevEnd !== seg.startTime) {
      const gap = document.createElement("span");
      gap.className = "chip gap";
      gap.textContent = `${minutesBetween(prevEnd, seg.startTime)}m break`;
      box.appendChild(gap);
    }
    const chip = document.createElement("span");
    chip.className = "chip";
    const dur = seg.endTime
      ? fmtHrs(minutesBetween(seg.startTime, seg.endTime) / 60)
      : "now";
    chip.textContent = `${seg.topic} · ${dur}`;
    box.appendChild(chip);
    prevEnd = seg.endTime;
  }
}

function setButtons(mode) {
  $("btn-start").disabled = mode !== "idle";
  $("btn-switch").disabled = mode === "idle";
  $("btn-pause").disabled = mode !== "active";
  $("btn-resume").disabled = mode !== "paused";
  $("btn-end").disabled = mode === "idle";
}

function renderPlanBadge() {
  const a = plan && plan.active;
  $("plan-badge").textContent = a
    ? `Week ${a.week} · Day ${a.day.n} — ${a.day.title}`
    : "Program complete 🌲";
}

function renderTodayPlan() {
  const a = plan && plan.active;
  const body = $("today-plan-body");
  if (!a) {
    $("today-plan-title").textContent = "Today's plan";
    body.innerHTML = `<div class="sub">All eight weeks are done. Walk out of the forest proud.</div>`;
    return;
  }
  const est = a.day.estHrs ? ` · ~${a.day.estHrs}h` : "";
  $("today-plan-title").textContent =
    `Today — Day ${a.day.n} (${a.day.dayName}): ${a.day.title}${est}`;
  body.innerHTML = a.day.bullets.map((b) =>
    `<div class="bullet">${b.label ? `<span class="label">${esc(b.label)}:</span>` : ""}${md(b.text)}</div>`
  ).join("");
}

function dayBlock(day, isActive) {
  const cls = "day-block" + (day.done ? " done" : "") + (isActive ? " today" : "");
  const meta = [day.dayName, day.estHrs ? `~${day.estHrs}h` : null]
    .filter(Boolean).join(" · ");
  const bullets = day.bullets.map((b) =>
    `<div class="bullet">${b.label ? `<span class="label">${esc(b.label)}:</span>` : ""}${md(b.text)}</div>`
  ).join("");
  return `<div class="${cls}">
    <div class="day-head">
      <span class="day-num">${day.done ? "✓" : day.n}</span>
      <span class="day-title">${esc(day.title)}</span>
      ${isActive ? `<span class="pill today-pill">today</span>` : ""}
      <span class="day-meta">${esc(meta)}</span>
    </div>
    <div class="day-bullets">${bullets}</div>
  </div>`;
}

function renderPlanTab() {
  const active = plan.active;
  $("tab-plan").innerHTML = plan.weeks.map((w) => {
    const doneCount = w.days.filter((d) => d.done).length;
    const isActiveWeek = active && active.week === w.week;
    const days = w.days.map((d) =>
      dayBlock(d, isActiveWeek && active.day.n === d.n)
    ).join("");
    const dod = w.dod.length
      ? `<div class="dod"><strong>Definition of Done</strong>` +
        w.dod.map((i) =>
          `<div class="item${i.checked ? " checked" : ""}">${i.checked ? "☑" : "☐"} ${md(i.text)}</div>`
        ).join("") + `</div>`
      : "";
    return `<details class="week"${isActiveWeek ? " open" : ""}>
      <summary><span>${esc(w.title || `Week ${w.week}`)}</span>
        <span class="sub mono">${doneCount}/${w.days.length} days</span></summary>
      ${days}${dod}
    </details>`;
  }).join("");
}

function renderHistoryTab() {
  const byDate = {};
  for (const s of history.sessions) (byDate[s.date] = byDate[s.date] || []).push(s);

  const groups = history.dailyTotals.map((d) => {
    const sessions = (byDate[d.date] || []).map((s) => {
      const rows = s.segments.map((seg) =>
        `<tr><td>${esc(seg.topic)}</td><td class="mono">${seg.startTime}–${seg.endTime}</td>
         <td class="mono">${fmtHrs(seg.durationHrs)}</td></tr>`
      ).join("");
      return `<details>
        <summary class="sub">${s.startTime} → ${s.endTime} · ${fmtHrs(s.totalHrs)}
          ${s.pauses.length ? `· ${s.pauses.length} break${s.pauses.length > 1 ? "s" : ""}` : ""}</summary>
        <table class="segments">${rows}</table>
      </details>`;
    }).join("");
    return `<div class="day-group">
      <div class="row"><strong>${esc(d.day)}, ${d.date}</strong>
        <span class="mono">${fmtHrs(d.hours)}</span></div>
      ${sessions}
    </div>`;
  }).join("");

  const weeks = history.weeks.map((w) => {
    const pct = Math.min(100, (w.hours / w.goal) * 100);
    return `<div class="bar-block">
      <div class="bar-head"><span>Week of ${w.weekStart}</span>
        <span class="mono">${fmtHrs(w.hours)} / ${w.goal}h</span></div>
      <div class="bar"><div class="fill week" style="width:${pct}%"></div></div>
    </div>`;
  }).join("");

  $("tab-history").innerHTML =
    (groups || `<div class="sub">No sessions logged yet.</div>`) +
    (weeks ? `<div class="week-summary"><h2>Week by week</h2>${weeks}</div>` : "");
}

function renderTopicOptions() {
  const seen = new Set();
  const opts = [];
  for (const t of [...topics.today, ...topics.recent, ...topics.roadmap.map((r) => r.topic)]) {
    if (!seen.has(t)) { seen.add(t); opts.push(t); }
  }
  $("topic-options").innerHTML = opts.map((t) => `<option value="${esc(t)}">`).join("");
}

/* ---------- actions ---------- */

async function act(action, body) {
  const r = await fetch(`/api/session/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const data = await r.json();
  if (!r.ok) {
    const err = new Error(data.error || `HTTP ${r.status}`);
    err.data = data;
    err.status = r.status;
    throw err;
  }
  suppressNotify = true;
  try {
    await refreshState();
  } finally {
    suppressNotify = false;
  }
  return data;
}

function showTopicForm(action) {
  pendingAction = action;
  $("topic-form").classList.remove("hidden");
  $("topic-input").value = "";
  $("topic-input").focus();
}

function hideTopicForm() {
  pendingAction = null;
  $("topic-form").classList.add("hidden");
}

$("btn-start").addEventListener("click", () => showTopicForm("start"));
$("btn-switch").addEventListener("click", () => showTopicForm("switch"));
$("topic-cancel").addEventListener("click", hideTopicForm);

$("topic-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const topic = $("topic-input").value.trim();
  const action = pendingAction;
  if (!topic || !action) return;
  try {
    await act(action, { topic });
    hideTopicForm();
    notify(action === "start" ? `Session started — ${topic}` : `Now studying: ${topic}`);
  } catch (err) { toast(err.message); }
});

$("btn-pause").addEventListener("click", async () => {
  try { await act("pause"); notify("Session paused"); } catch (err) { toast(err.message); }
});
$("btn-resume").addEventListener("click", async () => {
  try { await act("resume"); notify("Session resumed"); } catch (err) { toast(err.message); }
});

/* ---------- end-session modal ---------- */

function openEndModal() {
  if (!state.current) return;
  const perTopic = {};
  for (const seg of state.current.segments) {
    const hrs = seg.endTime
      ? minutesBetween(seg.startTime, seg.endTime) / 60
      : elapsedSec(seg.startTime) / 3600;
    perTopic[seg.topic] = (perTopic[seg.topic] || 0) + hrs;
  }
  const total = Object.values(perTopic).reduce((a, b) => a + b, 0);
  $("end-preview").innerHTML = `<table>` +
    Object.entries(perTopic).map(([t, h]) =>
      `<tr><td>${esc(t)}</td><td>${fmtHrs(h)}</td></tr>`).join("") +
    `<tr><td><strong>Total</strong></td><td><strong>${fmtHrs(total)}</strong></td></tr></table>`;
  $("end-note").textContent = state.syncEnabled
    ? "Saving will log the session and update the Google Sheet."
    : "Sheet sync is off — the session will be saved locally only.";
  $("end-confirm").classList.remove("hidden");
  $("end-cancel").textContent = "Keep studying";
  $("end-overlay").classList.remove("hidden");
}

$("btn-end").addEventListener("click", openEndModal);
$("end-cancel").addEventListener("click", () => $("end-overlay").classList.add("hidden"));

$("end-confirm").addEventListener("click", async () => {
  $("end-confirm").disabled = true;
  try {
    const result = await act("end");
    const link = result.synced
      ? ` <a href="${esc(result.sheetUrl)}" target="_blank">Open sheet ↗</a>`
      : "";
    $("end-preview").innerHTML =
      `<p>Session saved — <strong>${fmtHrs(result.payload.durationHrs)}</strong>.` +
      `${result.synced ? " Sheet updated." : ""}${link}</p>`;
    $("end-note").textContent = "Well done. Rest your eyes on the trees for a minute.";
    $("end-confirm").classList.add("hidden");
    $("end-cancel").textContent = "Close";
    notify(`Session saved — ${fmtHrs(result.payload.durationHrs)}`);
    refreshHistory();
  } catch (err) {
    if (err.status === 502 && err.data && err.data.savedLocally) {
      $("end-preview").innerHTML =
        `<p>Session saved locally — <strong>${fmtHrs(err.data.payload.durationHrs)}</strong>.</p>
         <p class="sub">Sheet sync failed: ${esc(err.data.error)}. It will appear in History;
         run <code>report</code> later to refresh the sheet.</p>`;
      $("end-confirm").classList.add("hidden");
      $("end-cancel").textContent = "Close";
      refreshState(); refreshHistory();
    } else {
      toast(err.message);
    }
  } finally {
    $("end-confirm").disabled = false;
  }
});

/* ---------- side rail navigation ---------- */

for (const btn of document.querySelectorAll(".rail-btn")) {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".rail-btn").forEach((b) =>
      b.classList.toggle("active", b === btn));
    document.querySelectorAll(".view").forEach((v) =>
      v.classList.toggle("hidden", v.id !== `view-${btn.dataset.view}`));
    window.scrollTo({ top: 0 });
    if (btn.dataset.view === "plan") {
      const today = document.querySelector(".day-block.today");
      if (today) today.scrollIntoView({ block: "center" });
    }
  });
}

/* ---------- boot ---------- */

(async function boot() {
  try {
    await Promise.all([refreshState(), refreshPlan(), refreshHistory(), refreshTopics()]);
  } catch (e) {
    toast("Could not load tracker data: " + e.message);
  }
  setInterval(poll, 2000);
  setInterval(tick, 1000);
})();
