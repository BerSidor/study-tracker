"""One-off migration (2026-07-13): repair stale-`done` session end times.

See docs/sessions-db-fix-plan.md. Sessions closed with `done` while paused got
sessions.end_time stamped with the clock time of the `done` command — minutes to a full
day after study actually stopped (a next-day `done` can even read *earlier* than the last
segment, since only HH:MM is stored). Segments were always correct; stats/sheet sync sum
segments and are unaffected. Only the sessions table is touched.

Execution note: the plan originally listed the five worst rows (2026-06-05-001,
-06-22-001, -06-26-001, -06-29-001, -07-02-001); inspection during execution showed the
same signature on 14 more rows, so the repair is uniform: every completed session's
end_time becomes its last segment's end_time — the invariant SessionManager.close_session
now maintains.

Run once, with the web UI stopped and a backup taken:
    python scripts/fix_stale_done_2026_07.py
Idempotent: a second run finds nothing to change.
"""

import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "sessions.db"


def main() -> None:
    conn = sqlite3.connect(DB)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT s.id, s.end_time,
                   (SELECT g.end_time FROM segments g
                    WHERE g.session_id = s.id ORDER BY g.seq DESC LIMIT 1)
            FROM sessions s
            WHERE s.end_time IS NOT NULL
            ORDER BY s.id
            """
        )
        changed = 0
        for sid, current_end, last_seg_end in cur.fetchall():
            if last_seg_end is None:
                raise SystemExit(f"{sid}: no closed segment found — aborting, nothing written.")
            if current_end == last_seg_end:
                continue
            cur.execute(
                "UPDATE sessions SET end_time = ? WHERE id = ?", (last_seg_end, sid)
            )
            print(f"{sid}: {current_end} -> {last_seg_end}")
            changed += 1
        conn.commit()
        print(f"{changed} session(s) updated.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
