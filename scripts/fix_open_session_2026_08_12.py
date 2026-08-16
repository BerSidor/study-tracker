"""One-off repair (2026-08-12): collapse a duplicate-segment trail on the open session.

See the diagnostic in that day's session notes / conversation: session 2026-08-12-001
picked up a duplicate-resume trail (root cause: session.py's resume_session appended a new
open segment without closing an already-open one first — fixed separately in the same
change). Segments 1 and 2 both started at 17:59 (a near-duplicate of the same study block),
followed by a zero-length ghost segment. Every hour total in this app (stats.session_hours,
the web dashboard, sync_payload.py) sums segments naively, so this was double-counting
~118 minutes.

Repair: merge the two 17:59-started segments into one (17:59 -> 19:58, the fuller of the
two recorded ends), drop the zero-length ghost, leave the pause gap (17:19 -> 17:59) and the
still-open segment untouched.

Run once, with the web UI stopped and a backup taken:
    python scripts/fix_open_session_2026_08_12.py
Idempotent: a second run finds the session already in the corrected shape and does nothing.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db import DbStore

DATA_DIR = ROOT / "data"
SESSION_ID = "2026-08-12-001"

EXPECTED_CORRUPT_SEGMENTS = [
    {"topic": "AI agent frameworks", "startTime": "15:21", "endTime": "17:19"},
    {"topic": "AI agent frameworks", "startTime": "17:59", "endTime": "19:57"},
    {"topic": "AI agent frameworks", "startTime": "17:59", "endTime": "19:58"},
    {"topic": "AI agent frameworks", "startTime": "19:58", "endTime": "19:58"},
]


def main() -> None:
    store = DbStore(DATA_DIR)
    session = store.read_current()

    if session is None or session["id"] != SESSION_ID:
        print(f"No open session {SESSION_ID!r} found — nothing to do.")
        return

    segments = session["segments"]
    open_segment = segments[-1] if segments and segments[-1]["endTime"] is None else None
    closed = segments[:-1] if open_segment else segments

    if closed == EXPECTED_CORRUPT_SEGMENTS:
        merged_topic = closed[1]["topic"]
        corrected_closed = [
            closed[0],
            {"topic": merged_topic, "startTime": "17:59", "endTime": "19:58"},
        ]
        print("Before:")
        for seg in segments:
            print(" ", seg)

        new_segments = corrected_closed + ([open_segment] if open_segment else [])
        session["segments"] = new_segments
        store.write_current(session)

        print("After:")
        for seg in new_segments:
            print(" ", seg)
        print("1 session repaired.")
    else:
        current = store.read_current()
        print(f"{SESSION_ID}: segments don't match the expected corrupt shape — aborting, nothing written.")
        print("Current segments:")
        for seg in current["segments"]:
            print(" ", seg)


if __name__ == "__main__":
    main()
