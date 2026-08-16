# Study Tracker — Domain Glossary

## Session

A single continuous study sitting. Begins when the user issues `start` and ends when the user issues `done`. May cross midnight. Never auto-splits. Two sessions on the same calendar day are only possible if the user explicitly closes one and opens another.

A Session always belongs to its **start date** — a session that begins Thursday at 23:00 and ends Friday at 01:00 is a Thursday session. The `date` and `day` fields derive from `startTime`, never from `endTime`.

A Session contains one or more Segments. It has no explicit Pause list.

## Segment

A contiguous, pause-free block of time within a Session dedicated to a single topic. A Segment only runs while the user is actively studying — it closes when a pause begins and a new Segment opens when the user resumes (for the same or a different topic).

Because Segments are always pause-free, **wall-clock duration = active time**. No `activeMinutes` field is needed; derive active time as `endTime − startTime`.

If the user pauses and resumes without switching topics, two separate Segments with the same topic name are recorded — they are never merged.

## Duration (the active-minutes rule)

The single rule for "how long between two `HH:MM` clock times", owned by `duration.py`
(`active_minutes(start, end)`). It is the only place a duration may be computed — close/pause/
switch validation, sheet-sync payloads, weekly stats, and the web UI all call it.

A study timeline may cross midnight at most once. When an end time reads earlier than its
start, the **size of the reversal** decides intent: a reversal **greater than 12 hours**
(`MIDNIGHT_WRAP_THRESHOLD_MIN`) is a genuine midnight crossing and wraps by +24h; a reversal
of **12 hours or less** is implausible for a single pause-free Segment and raises
`DurationError`. `SessionManager` translates that into a `SessionError` at close time; readers
(stats, sync) let it surface, so dirty data fails loudly instead of silently inflating totals.

## Pause

A Pause is implicit — it is the gap between the `endTime` of one Segment and the `startTime` of the next. It is never stored explicitly. To find pause durations, diff consecutive segment boundaries.

**Removed from the data model:** `session.pauses[]` and `segment.activeMinutes` and `segment.durationHrs`.

## Topic

A free-form string the user enters when starting or switching study focus (e.g. `"MCP servers"`, `"Startups"`). No validation at entry time. Topics are classified into Tracks at report time.

## Track

A named category that groups related Topics for weekly reporting. The canonical Tracks are defined in `roadmap.json` under `tracks`. New Tracks can be added as study scope grows. Current Tracks (per `docs/startup-study-plan.md`): **Claude Code Mastery** (CLI, config, hooks, MCP servers, subagents, skills, Agent SDK), **AI/ML Foundations** (prompt engineering, RAG, agent architectures, LLM evaluation, AI system design, Anthropic API economics, end-to-end app), **Freelance & Discovery** (freelance setup, client gigs & delivery, discovery log upkeep), and **Business Ideation** (market & competitor analysis, business models, customer conversations, MVP scoping, startup thesis).

## SessionManager State Machine

`SessionManager` has two states: **Idle** (no open session) and **Active** (session in progress).

| Current state | Command         | Result                                                  |
| ------------- | --------------- | ------------------------------------------------------- |
| Idle          | `startSession`  | → Active                                                |
| Active        | `startSession`  | Error — warn user, offer to close current session first |
| Active        | `closeSession`  | → Idle, returns completed Session object                |
| Idle          | `closeSession`  | Error — "No session is currently open"                  |
| Active        | `switchTopic`   | stays Active, closes current Segment, opens new one     |
| Idle          | `switchTopic`   | Error — "No session is open — did you mean start?"      |
| Active        | `pauseSession`  | stays Active, closes current Segment at pause time      |
| Active        | `resumeSession` | stays Active, opens new Segment at resume time          |
| Active (current Segment already open) | `resumeSession` | Error — no data mutated |

No silent failures. Every invalid transition surfaces a clear error message. No data is mutated on error.

## Session ID

Format: `YYYY-MM-DD-NNN` where NNN is a zero-padded counter starting at `001`, scoped to the calendar date. Generated automatically by `SessionManager.startSession()` by counting existing sessions for that date in the completed-session archive and incrementing. Example: `"2026-06-08-001"`, `"2026-06-08-002"`.

## Storage

A `Store` is what `SessionManager` writes through: the active session
(`read_current`/`write_current`/`delete_current`) and the completed-session archive
(`read_all_completed`/`append_completed`).

In production (`DbStore` + `SessionDB`) both live in one SQLite database, `sessions.db`, as a
single `sessions` table: the active session is the row with `end_time IS NULL` (its
still-open segment is likewise the row with `end_time IS NULL` in `segments`); every other row
is a completed session. There is exactly one seam, not two — see `docs/adr/0002-unify-session-
storage-in-sqlite.md` for why the earlier two-seam (file + SQLite) design was collapsed.

`FileStore` still exists as a no-database reference adapter used in tests: it keeps the active
session in `current-session.json` (via `CurrentSessionFile`) and the archive in
`sessions.json`. It is intentionally not wired into production and is unaffected by that ADR.

Two one-time migrations run inside `DbStore.__init__`, each guarded by the legacy file's
existence and each renaming that file to `.bak` after import: a leftover `sessions.json`
(pre-SQLite archive) via `migrate_legacy_json`, and a leftover `current-session.json`
(pre-unification active session) via `migrate_legacy_current_session`.

## Session Model vs Sync Payload

The **Session model** (stored in the completed-session archive — `sessions.db`) is lean — it contains only what is necessary to reconstruct facts. Derived values are not stored.

The **Sync Payload** is a richer object computed at sheet-sync time from the Session model. It adds fields the Google Sheet requires: `day` (derived from `date`), `session.durationHrs` (sum of segment durations ÷ 60), `segment.durationHrs` (segment wall-clock duration ÷ 60). These are computed in the sync layer, never stored.

This means sheet sync and session close are independent operations. `closeSession()` writes a lean Session to the archive. A separate sync step reads that Session, builds the Sync Payload, and POSTs it to the Apps Script Web App.

## Topic Classification

The process of assigning a Topic to a Track. Happens at `weekly report` time. Claude proposes a Track for each unclassified Topic; the user confirms or overrides. Confirmed mappings are persisted in `topic-map.json` so each Topic is classified only once — future sessions that reuse a known Topic skip the prompt entirely.

Topics that appear in `topic-map.json` are considered classified. Topics absent from it are unclassified and trigger the classification prompt at the next report.
