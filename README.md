# study-tracker

A time-tracking system for study sessions, with a **CLI and a browser UI as co-equal writers**
against one SQLite store — start a session in the terminal, close it in the browser, and both stay
in sync because neither owns the state.

Optionally syncs completed sessions to a Google Sheet via Apps Script.

## Domain model

The design is driven from a written glossary ([`CONTEXT.md`](CONTEXT.md)) rather than from the
schema up. Three terms carry the whole model:

- **Session** — one continuous sitting, from `start` to `done`. It belongs to its _start_ date, so a
  session running 23:00 Thursday → 01:00 Friday is a Thursday session. Never auto-splits.
- **Segment** — a contiguous, **pause-free** block on a single topic. Because segments are pause-free
  by construction, wall-clock duration _is_ active time — no `activeMinutes` field is needed.
- **Pause** — never stored. A pause is the gap between one segment's end and the next one's start,
  derived by diffing consecutive boundaries.

Getting the invariant right ("segments are pause-free") is what deleted three fields from the data model.

## The midnight rule

All duration math lives in one module, `duration.py`. Every caller — close/pause/switch validation,
sheet-sync payloads, weekly stats, the web UI — goes through `active_minutes(start, end)`.

When an end time reads _earlier_ than its start, the **size of the reversal** decides intent:

| Reversal   | Interpretation                                                 |
| ---------- | -------------------------------------------------------------- |
| > 12 hours | genuine midnight crossing → wrap by +24h                       |
| ≤ 12 hours | implausible for one pause-free segment → raise `DurationError` |

`SessionManager` translates that into a `SessionError` at close time. Readers let it surface, so dirty
data **fails loudly instead of silently inflating totals** — the failure mode that makes a time tracker
worthless.

## Architecture

```
cli.py  /  web/server.py     entry points (co-equal writers)
        └ session.py         SessionManager — domain rules, validation
            └ db.py          DbStore — SQLite schema + migrations
        └ duration.py        the single source of duration math
        └ stats.py           weekly/daily aggregates
        └ sheet_sync.py      Google Apps Script sync
        └ notifier.py        pluggable notification seam
```

## Run

```bash
python cli.py start "MCP servers"     # begin a session
python cli.py switch "Databases"      # close current segment, open a new one
python cli.py pause                   # close the open segment
python cli.py resume "MCP servers"
python cli.py done                    # close the session, print a per-topic summary

python web/server.py --port 8766      # browser UI at http://127.0.0.1:8766
```

Times default to now; pass `HH:MM` as a trailing argument to backfill.

## Tests

```bash
python -m pytest
```

Covers duration edge cases (including the midnight rule), session lifecycle, stats, sync payloads,
and plan parsing.

## Notes

`data/` is gitignored — it holds the local database and personal configuration. Copy
`config.example.json` to `data/config.json` to set goals and the optional Sheets endpoint.
