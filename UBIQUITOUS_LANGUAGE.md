# Ubiquitous Language — Study Tracker

## Session lifecycle

| Term | Definition | Aliases to avoid |
|------|-----------|-----------------|
| **Session** | A single continuous study sitting, from `start` to `done`, scoped to its start date. | study session, work session |
| **Segment** | A contiguous, pause-free block of time within a Session dedicated to exactly one Topic. | block, interval, slot |
| **Pause** | The implicit gap between the `endTime` of one Segment and the `startTime` of the next — never stored explicitly. | break, stop |
| **Topic** | A free-form string the user names when starting or switching focus (e.g. `"MCP servers"`). | subject, task, activity |
| **Track** | A named category that groups related Topics for weekly reporting. Current Tracks: Claude Code, AI/ML Foundations, Business Ideation. | category, area, domain |
| **Topic Classification** | The act of assigning a Topic to a Track. Happens at weekly report time; confirmed mappings persist in `topic-map.json`. | topic tagging, categorisation |

## State machine

| Term | Definition | Aliases to avoid |
|------|-----------|-----------------|
| **Idle** | The SessionManager state when no Session is open. | stopped, empty, inactive |
| **Active** | The SessionManager state when a Session is open and a Segment is running. | running, started, in-progress |
| **startSession** | The command that transitions the SessionManager from Idle → Active and opens the first Segment. | open session, begin, create session |
| **switchTopic** | The command that closes the current Segment and opens a new one for a different Topic, without leaving Active. | change topic, switch, now doing |
| **pauseSession** | The command that closes the current Segment without opening a new one — leaving Active with no open Segment. | pause, break |
| **resumeSession** | The command that opens a new Segment (same Topic as the last) after a Pause. | resume, continue |
| **closeSession** | The command that closes the final Segment, writes the Session to the store, and transitions to Idle. User-facing alias: `done`. | finish, end, stop, complete |

## Data model

| Term | Definition | Aliases to avoid |
|------|-----------|-----------------|
| **Session model** | The lean, stored representation of a Session — contains only what is necessary to reconstruct facts. Lives in `sessions.json`. No derived fields. | session record, session object |
| **Sync Payload** | A richer object computed from the Session model at sync time. Adds derived fields the Google Sheet requires: `day`, `durationHrs`, per-Segment `durationHrs`. Never stored. | sheet payload, sync object, report payload |
| **Session ID** | The unique identifier for a Session, formatted `YYYY-MM-DD-NNN`. The counter is scoped to the calendar date. | id, session key |
| **date** | The ISO date string (`YYYY-MM-DD`) derived from the Session's `startTime`. A Session always belongs to its start date, even if it crosses midnight. | start date, session date |
| **day** | The human-readable day name (`"Monday"`) derived from `date` at sync time. Lives only on the Sync Payload, never on the Session model. | weekday, day name |
| **durationHrs** | A float representing elapsed time in hours. Appears only on the Sync Payload — on the Session total and per Segment. Never stored on the Session model. | duration, hours, totalHrs |

## Reporting

| Term | Definition | Aliases to avoid |
|------|-----------|-----------------|
| **Weekly Report** | A summary of Sessions for the current Monday–Saturday period, written to the Google Sheet. | report, weekly summary, weekly stats |
| **Weekly Goal** | The target number of study hours for the week (configured in `config.json`). | weekly target, goal |
| **Daily Target** | The average hours per study day implied by the Weekly Goal (Weekly Goal ÷ study days). | daily goal, daily hours |

## Relationships

- A **Session** contains one or more **Segments**.
- A **Pause** is the gap between two consecutive **Segments** — it has no record of its own.
- A **Segment** is always dedicated to exactly one **Topic**.
- A **Topic** is classified into at most one **Track**; unclassified Topics have no Track until classified.
- A **Sync Payload** is derived from exactly one **Session model** and is never persisted.
- A **Session ID** counter resets per calendar **date** — two Sessions on the same date get `...-001` and `...-002`.

## Example dialogue

> **Dev:** "When the user says `done`, what actually happens?"

> **Domain expert:** "The SessionManager closes the open **Segment**, stamps `endTime` on the **Session**, writes the lean **Session model** to `sessions.json`, and transitions to **Idle**. That's `closeSession`. The **Sync Payload** is computed after that, separately."

> **Dev:** "So `durationHrs` isn't stored in the **Session model**?"

> **Domain expert:** "Never. `durationHrs` is derived when we build the **Sync Payload** — we compute it from segment boundaries right before the POST. The **Session model** only has `startTime` and `endTime` strings."

> **Dev:** "What if the user pauses and resumes the same **Topic**? Does that produce one **Segment** or two?"

> **Domain expert:** "Two. A **Pause** closes the current **Segment**. When the user resumes, a new **Segment** opens — same **Topic**, different time boundaries. **Segments** are never merged. The **Pause** itself is the gap between them; there's no record for it."

> **Dev:** "And when does **Topic Classification** happen?"

> **Domain expert:** "At **Weekly Report** time. Claude looks at each **Topic** in the week's **Sessions**, checks `topic-map.json` for known mappings, and prompts for any unclassified ones. Once confirmed, the mapping persists so the same **Topic** is never classified twice."

## Flagged ambiguities

- **"done" / "stop" / "end"** — CLAUDE.md accepts all three as user commands but they name different things: `done` is the user-facing word, `closeSession` is the operation. Use `closeSession` in technical discussion and `done` only when quoting user input.

- **"date" vs "day"** — `date` is always the ISO string `"YYYY-MM-DD"`, stored on the Session model. `day` is always the derived human-readable name `"Monday"`, present only on the Sync Payload. Never use "date" when you mean "day of week" or vice versa.

- **"sync" / "sheet sync" / "sync sheet" / "update the sheet"** — all refer to the same operation: building the Sync Payload and POSTing it to the Apps Script Web App. Canonical verb: **sync**. Canonical noun: **sheet sync**.

- **"durationHrs"** — appears in two places in the Sync Payload (session total and per-Segment) but never on the Session model. If someone refers to "the session's durationHrs" they almost certainly mean the Sync Payload field, not something stored. Clarify which context before assuming.

- **"report"** — used loosely to mean both the Weekly Report (the Google Sheet section) and the act of running one. Prefer **"weekly report"** as the noun and **"refresh the report"** as the verb.
