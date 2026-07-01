# ADR-0002: Unify active- and completed-session storage in SQLite

## Status

Accepted

## Context

`DbStore` composed two independent storage seams: the active session lived in a plain file,
`current-session.json` (via `CurrentSessionFile`), while completed sessions lived in
`sessions.db` (`SessionDB`). This bought nothing in production — no process outside this repo
was found to depend on `current-session.json` being a bare, directly-readable file — while
paying for two migration paths, two failure modes, and the risk of the file and the database
silently disagreeing about what's active.

## Decision

Fold the active session into `sessions.db` as the row with `end_time IS NULL` (and its open
segment as the `segments` row with `end_time IS NULL`). `SessionDB` now implements all five
`Store` methods directly; `DbStore` delegates to it 1:1 and no longer composes
`CurrentSessionFile`. `append()` becomes an upsert-by-id, since closing a session updates the
same row that was previously its open row (same `id`) rather than inserting a new one;
`delete_current()` becomes `DELETE FROM sessions WHERE end_time IS NULL`, a correct no-op once
`append_completed` has already set `end_time`. `all_sessions()` is renamed
`completed_sessions()` and filters `WHERE end_time IS NOT NULL` so `read_all_completed()` keeps
excluding the in-progress session. A one-time migration (`migrate_legacy_current_session`)
folds any leftover `current-session.json` into the DB, mirroring the existing
`sessions.json` → archive migration; a second one-time migration relaxes the `end_time NOT
NULL` constraint on pre-existing on-disk databases, which declared it `NOT NULL` under the old
two-seam schema.

`FileStore` (and its `CurrentSessionFile` seam) is untouched — it remains the no-database,
two-seam reference adapter used by `tests/test_session.py`. `SessionManager` and the `Store`
protocol shape are unaffected; this is purely an internal storage change to the
`DbStore`/`SessionDB` production path.

## Consequences

- One database file, one query surface, one migration story for production.
- Every session action (not just close) now writes `sessions.db`, so its mtime changes more
  often; `web/server.py`'s `version().sessions` polling now triggers
  `refreshHistory()`/`refreshTopics()` on pause/resume/switch too, not just close. Harmless —
  those endpoints already exclude the open row.
- `version()`'s `current` key (`current-session.json`'s mtime) is dropped; confirmed dead in the
  frontend.
- Losing `current-session.json` as a bare file means any future external tool wanting live
  session state must go through the HTTP API or SQLite directly, rather than reading a JSON
  file off disk. No such consumer exists today.
