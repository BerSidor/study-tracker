# Study Tracker — Claude Code Context

## Session Commands

All session state is managed by `cli.py`. Run commands from `study-tracker/`.

| What you say | Command to run |
|---|---|
| `start [topic]` or `start studying [topic]` | `python cli.py start "<topic>"` |
| `started at HH:MM` (in the start message) | `python cli.py start "<topic>" HH:MM` |
| `switching to [topic]` or `now [topic]` | `python cli.py switch "<topic>"` |
| `switching to [topic] at HH:MM` | `python cli.py switch "<topic>" HH:MM` |
| `pause` | `python cli.py pause` |
| `resume` | `python cli.py resume` |
| `done` / `stop` / `end` | `python cli.py done` → print output → sync sheet → return link |
| `done at HH:MM` | `python cli.py done HH:MM` |
| `report` or `weekly report` | Sync sheet → return link (no cli.py call needed) |
| `how many hours today` | Read `sessions.json` → inline summary only, no sheet update |
| `check status` or `update status` | Run `toast-heartbeat.ps1` directly |
| `set goal [N] hours` | Update `weeklyGoalHours` in `config.json` |

`cli.py` prints the per-topic breakdown after `done` — relay it verbatim, then append the sheet link:
```
Session closed — 2h 45m total
  Claude Code hooks  45m
  MCP servers        1h 10m
Sheet updated: [link]
```

Do not edit `current-session.json` or `sessions.json` directly — all writes go through `cli.py`.

## Time Handling

- If no time is given, `cli.py` uses the current Windows local time automatically.
- To override: include "started at 14:30" or "ended at 16:00" — pass it as the time argument.
- Week runs Monday–Saturday. Sunday is a rest day (never counted toward weekly goal).
- Weekly goal: **40 hours** (≈ 6.7 h/day across 6 days).

## Data Files

All data lives in `C:\Users\berna\Claude_Code_Learning\study-tracker\data\`:

| File | Purpose |
|---|---|
| `sessions.json` | Completed sessions — source of truth |
| `current-session.json` | Active session state (deleted on close) |
| `config.json` | Web App URL, sheet URL, weekly goal, study days |
| `roadmap.json` | Three-track learning curriculum with hours logged |

## Reference Docs

- `docs/session-protocol.md` — mid-session switching examples, protocol edge cases
- `docs/roadmap.md` — three learning tracks and topic recommendation logic
- `docs/sheet-reference.md` — Google Sheet, Apps Script Web App, sheet structure
- `SETUP.md` — initial setup instructions

## Agent skills

### Issue tracker

Issues live in GitHub Issues for this repo. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary (needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at the project root. See `docs/agents/domain.md`.
