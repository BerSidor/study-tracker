// ─── Study Tracker 2026 — Google Apps Script ───────────────────────────────
// Deploy as Web App: Execute as "Me", Access "Anyone"
// After deploying, copy the URL into config.json → webAppUrl

const SESSIONS_SHEET = "Sessions";
const REPORT_SHEET  = "Weekly Report";
const WEEKLY_GOAL   = 40;
const STUDY_DAYS    = 6;

// ─── HTTP entry points ──────────────────────────────────────────────────────

function doGet(e) {
  const ss  = SpreadsheetApp.getActiveSpreadsheet();
  return json({ status: "ok", sheetUrl: ss.getUrl() });
}

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    if (data.action === "log_session") {
      appendSession(data.session);
      refreshReport();
      return json({ success: true });
    }
    if (data.action === "refresh_report") {
      refreshReport();
      return json({ success: true });
    }
    return json({ success: false, error: "Unknown action" });
  } catch (err) {
    return json({ success: false, error: err.toString() });
  }
}

// ─── Session logging ────────────────────────────────────────────────────────

function appendSession(s) {
  const ss    = SpreadsheetApp.getActiveSpreadsheet();
  let   sheet = ss.getSheetByName(SESSIONS_SHEET);

  if (!sheet) {
    sheet = ss.insertSheet(SESSIONS_SHEET);
    const hdrs = ["Session ID","Date","Day","Start","End","Total Hrs","Segments","Notes"];
    const hdr  = sheet.getRange(1, 1, 1, hdrs.length);
    hdr.setValues([hdrs]).setFontWeight("bold").setBackground("#1a73e8").setFontColor("#ffffff");
    sheet.setFrozenRows(1);
  }

  // Format segments: "Claude Code hooks (2h 22m), MCP servers (1h 10m)"
  const segs = (s.segments || []).map(g => `${g.topic} (${toHM(g.durationHrs)})`).join(", ");

  const row = [s.id, s.date, s.day, s.startTime, s.endTime,
               toHM(s.durationHrs), segs, s.notes || ""];

  // Insert after header so newest is first
  sheet.insertRowAfter(1);
  sheet.getRange(2, 1, 1, row.length).setValues([row]);
  sheet.autoResizeColumns(1, row.length);
}

// ─── Weekly report ──────────────────────────────────────────────────────────

function refreshReport() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // Ensure report sheet is first
  let rSheet = ss.getSheetByName(REPORT_SHEET);
  if (!rSheet) {
    rSheet = ss.insertSheet(REPORT_SHEET, 0);
  } else {
    ss.setActiveSheet(rSheet);
    ss.moveActiveSheet(1);
    rSheet.clear();
  }

  const { monday, saturday } = currentWeekBounds();
  const sSheet = ss.getSheetByName(SESSIONS_SHEET);
  const stats  = computeStats(sSheet, monday, saturday);

  const weekLabel = `${fmtDate(monday)} → ${fmtDate(saturday)}`;
  const goalPct   = stats.totalHours > 0 ? Math.round(stats.totalHours / WEEKLY_GOAL * 100) : 0;
  const bar       = progressBar(goalPct);

  const rows = [
    ["📚  STUDY TRACKER — WEEKLY REPORT", ""],
    ["", ""],
    ["Week",               weekLabel],
    ["Total hours",        toHM(stats.totalHours)],
    ["Daily average",      toHM(stats.dailyAvg) + "  (goal: " + toHM(WEEKLY_GOAL / STUDY_DAYS) + ")"],
    ["Most studied day",   stats.bestDay],
    ["Peak time block",    stats.peakBlock],
    ["Sessions",           stats.sessionCount],
    ["Weekly goal",        bar + "  " + toHM(stats.totalHours) + " / " + toHM(WEEKLY_GOAL) + "  (" + goalPct + "%)"],
    ["", ""],
    ["── TOPIC BREAKDOWN ──", ""],
  ];

  const topicsSorted = Object.entries(stats.topicHours).sort((a, b) => b[1] - a[1]);
  topicsSorted.forEach(([topic, hrs]) => rows.push([topic, toHM(hrs)]));

  rows.push(["", ""]);
  rows.push(["── TRACK BREAKDOWN ──", ""]);
  for (const [track, hrs] of Object.entries(stats.trackHours)) {
    rows.push([track, toHM(hrs)]);
  }

  rows.push(["", ""]);
  rows.push(["── RECOMMENDED NEXT TOPICS ──", ""]);
  getRecommendations(stats).forEach((r, i) => {
    rows.push([`${i + 1}.  ${r.topic}`, r.reason]);
  });

  rows.push(["", ""]);
  rows.push(["Last updated", new Date().toLocaleString()]);

  rSheet.getRange(1, 1, rows.length, 2).setValues(rows);

  // Styling
  rSheet.getRange(1, 1, 1, 2).setFontWeight("bold").setFontSize(14).setBackground("#1a73e8").setFontColor("#ffffff");
  rSheet.getRange(11, 1, 1, 2).setFontWeight("bold").setBackground("#e8f0fe");
  const trackRow = rows.findIndex(r => r[0] === "── TRACK BREAKDOWN ──") + 1;
  const recRow   = rows.findIndex(r => r[0] === "── RECOMMENDED NEXT TOPICS ──") + 1;
  rSheet.getRange(trackRow, 1, 1, 2).setFontWeight("bold").setBackground("#e8f0fe");
  rSheet.getRange(recRow,   1, 1, 2).setFontWeight("bold").setBackground("#e8f0fe");
  rSheet.setColumnWidth(1, 300);
  rSheet.setColumnWidth(2, 420);
}

// ─── Stats computation ──────────────────────────────────────────────────────

function computeStats(sheet, monday, saturday) {
  const stats = {
    totalHours: 0, dailyAvg: 0, bestDay: "N/A", peakBlock: "N/A",
    sessionCount: 0, topicHours: {},
    trackHours: { "Claude Code": 0, "AI/ML Foundations": 0, "Business Ideation": 0 }
  };

  if (!sheet) return stats;
  const data = sheet.getDataRange().getValues();
  if (data.length <= 1) return stats;

  const dayHours   = {};
  const hourBuckets = {};

  for (let i = 1; i < data.length; i++) {
    const dateStr = String(data[i][1]);
    const d = new Date(dateStr);
    if (isNaN(d) || d < monday || d > saturday) continue;

    const hrs  = parseHM(data[i][5]);
    const day  = String(data[i][2]);
    const start = String(data[i][3]);

    stats.totalHours  += hrs;
    stats.sessionCount++;
    dayHours[day] = (dayHours[day] || 0) + hrs;

    if (start && start.includes(":")) {
      const h = start.split(":")[0].padStart(2, "0") + ":00";
      hourBuckets[h] = (hourBuckets[h] || 0) + hrs;
    }

    const segsStr = String(data[i][6]);
    const re = /([^,]+?)\s*\(([^)]+)\)/g;
    let m;
    while ((m = re.exec(segsStr)) !== null) {
      const topic    = m[1].trim();
      const topicHrs = parseHM(m[2]);
      stats.topicHours[topic] = (stats.topicHours[topic] || 0) + topicHrs;
      const track = classifyTopic(topic);
      if (track) stats.trackHours[track] = (stats.trackHours[track] || 0) + topicHrs;
    }
  }

  stats.dailyAvg = stats.totalHours / STUDY_DAYS;

  if (Object.keys(dayHours).length > 0) {
    const [bd, bh] = Object.entries(dayHours).sort((a, b) => b[1] - a[1])[0];
    stats.bestDay = `${bd}  (${toHM(bh)})`;
  }

  if (Object.keys(hourBuckets).length > 0) {
    const [ph] = Object.entries(hourBuckets).sort((a, b) => b[1] - a[1])[0];
    const start = parseInt(ph);
    stats.peakBlock = `${ph} – ${String(start + 2).padStart(2, "0")}:00`;
  }

  return stats;
}

function classifyTopic(topic) {
  const t = topic.toLowerCase();
  const CC  = ["cli", "claude.md", "tool use", "hooks", "mcp", "subagent", "multi-agent", "claude code", "permissions"];
  const AI  = ["prompt", "rag", "agent architect", "llm eval", "fine-tun", "machine learning", "deep learning", "neural"];
  const BIZ = ["product research", "competitor", "market", "mvp", "business model", "go-to-market", "business"];
  if (CC.some(k => t.includes(k)))  return "Claude Code";
  if (AI.some(k => t.includes(k)))  return "AI/ML Foundations";
  if (BIZ.some(k => t.includes(k))) return "Business Ideation";
  return null;
}

// ─── Recommendations ────────────────────────────────────────────────────────

function getRecommendations(stats) {
  const roadmap = {
    "Claude Code": [
      { topic: "CLI basics & configuration",        targetHrs: 3 },
      { topic: "CLAUDE.md & project context",       targetHrs: 2 },
      { topic: "Tool use & permissions model",      targetHrs: 4 },
      { topic: "Hooks system",                      targetHrs: 3 },
      { topic: "MCP servers",                       targetHrs: 5 },
      { topic: "Subagents & multi-agent workflows", targetHrs: 5 },
      { topic: "Building a project end-to-end",     targetHrs: 8 },
    ],
    "AI/ML Foundations": [
      { topic: "Prompt engineering",    targetHrs: 3 },
      { topic: "RAG systems",           targetHrs: 4 },
      { topic: "Agent architectures",   targetHrs: 4 },
      { topic: "LLM evaluation basics", targetHrs: 3 },
      { topic: "Fine-tuning overview",  targetHrs: 2 },
    ],
    "Business Ideation": [
      { topic: "AI product research & trends",  targetHrs: 3 },
      { topic: "Competitor & market analysis",  targetHrs: 3 },
      { topic: "MVP scoping with Claude Code",  targetHrs: 4 },
      { topic: "Business model basics",         targetHrs: 2 },
    ],
  };

  // Detect dominant track this week
  const total = Object.values(stats.trackHours).reduce((a, b) => a + b, 0);
  const dominantTrack = total > 0
    ? Object.entries(stats.trackHours).find(([, h]) => h / total > 0.6)?.[0]
    : null;

  const recs = [];

  for (const [track, topics] of Object.entries(roadmap)) {
    if (recs.length >= 3) break;
    if (dominantTrack && track === dominantTrack && recs.length >= 1) continue;

    for (const { topic, targetHrs } of topics) {
      const logged = stats.topicHours[topic] || 0;
      if (logged === 0) {
        recs.push({ topic: `${topic}  [${track}]`, reason: "Not started yet — next in sequence" });
        break;
      }
      if (logged < targetHrs * 0.5) {
        recs.push({ topic: `${topic}  [${track}]`, reason: `${toHM(logged)} logged, target ${toHM(targetHrs)} — needs more depth` });
        break;
      }
    }
  }

  while (recs.length < 3) {
    recs.push({ topic: "Review a completed topic", reason: "Spaced repetition strengthens retention" });
  }

  return recs.slice(0, 3);
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function currentWeekBounds() {
  const now = new Date();
  const dow = now.getDay(); // 0=Sun
  const monday = new Date(now);
  monday.setDate(now.getDate() - (dow === 0 ? 6 : dow - 1));
  monday.setHours(0, 0, 0, 0);
  const saturday = new Date(monday);
  saturday.setDate(monday.getDate() + 5);
  saturday.setHours(23, 59, 59, 999);
  return { monday, saturday };
}

function fmtDate(d) {
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}

function progressBar(pct) {
  const filled = Math.round(Math.min(pct, 100) / 10);
  return "▓".repeat(filled) + "░".repeat(10 - filled);
}

function toHM(hrs) {
  const h = Math.floor(hrs);
  const m = Math.round((hrs - h) * 60);
  return h + "h " + m + "m";
}

function parseHM(val) {
  const str = String(val).trim();
  if (/^\d+(\.\d+)?$/.test(str))  return parseFloat(str);
  if (/^\d+(\.\d+)?h$/.test(str)) return parseFloat(str);
  const hMatch = str.match(/(\d+)h/);
  const mMatch = str.match(/(\d+)m/);
  return (hMatch ? parseInt(hMatch[1]) : 0) + (mMatch ? parseInt(mMatch[1]) : 0) / 60;
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
