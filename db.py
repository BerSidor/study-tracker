import sqlite3
from pathlib import Path

from session import FileStore

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,
    date       TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS segments (
    session_id TEXT    NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    seq        INTEGER NOT NULL,
    topic      TEXT    NOT NULL,
    start_time TEXT    NOT NULL,
    end_time   TEXT    NOT NULL,
    PRIMARY KEY (session_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date);
"""


class SessionDB:
    """Completed-session store backed by SQLite.

    Connections are short-lived (one per call) so cli.py and the web server
    can operate on the same database concurrently.
    """

    def __init__(self, db_path):
        self._path = Path(db_path)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def append(self, session: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions (id, date, start_time, end_time) VALUES (?, ?, ?, ?)",
                (session["id"], session["date"], session["startTime"], session["endTime"]),
            )
            conn.executemany(
                "INSERT INTO segments (session_id, seq, topic, start_time, end_time)"
                " VALUES (?, ?, ?, ?, ?)",
                [
                    (session["id"], i, seg["topic"], seg["startTime"], seg["endTime"])
                    for i, seg in enumerate(session["segments"])
                ],
            )

    def all_sessions(self) -> "list[dict]":
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, date, start_time, end_time FROM sessions ORDER BY id"
            ).fetchall()
            seg_rows = conn.execute(
                "SELECT session_id, topic, start_time, end_time FROM segments"
                " ORDER BY session_id, seq"
            ).fetchall()

        segments: dict[str, list[dict]] = {}
        for session_id, topic, start, end in seg_rows:
            segments.setdefault(session_id, []).append(
                {"topic": topic, "startTime": start, "endTime": end}
            )
        return [
            {
                "id": sid,
                "date": date,
                "startTime": start,
                "segments": segments.get(sid, []),
                "endTime": end,
            }
            for sid, date, start, end in rows
        ]

    def has(self, session_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return row is not None


def _to_minutes(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m


def _from_minutes(m: int) -> str:
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


def _unwrap(intervals, anchor: int) -> "list[tuple[int, int]]":
    """Map HH:MM interval list onto an absolute-minute timeline starting at
    `anchor`, adding 24h whenever a time wraps past midnight."""
    out = []
    prev = anchor
    for start, end in intervals:
        s = _to_minutes(start)
        while s < prev:
            s += 24 * 60
        e = _to_minutes(end)
        while e < s:
            e += 24 * 60
        out.append((s, e))
        prev = e
    return out


def _subtract_pauses(session: dict) -> "list[dict]":
    """Convert legacy wall-clock segments + pauses[] into modern pause-free
    segments by cutting the pause intervals out of each segment's span."""
    anchor = _to_minutes(session["startTime"])
    seg_spans = _unwrap(
        [(seg["startTime"], seg["endTime"]) for seg in session["segments"]], anchor
    )
    pauses = _unwrap(
        [(p["startTime"], p["endTime"]) for p in session["pauses"]], anchor
    )

    segments = []
    for seg, (start, end) in zip(session["segments"], seg_spans):
        pieces = [(start, end)]
        for p_start, p_end in pauses:
            next_pieces = []
            for s, e in pieces:
                if p_end <= s or p_start >= e:
                    next_pieces.append((s, e))
                    continue
                if s < p_start:
                    next_pieces.append((s, p_start))
                if p_end < e:
                    next_pieces.append((p_end, e))
            pieces = next_pieces
        segments.extend(
            {
                "topic": seg["topic"],
                "startTime": _from_minutes(s),
                "endTime": _from_minutes(e),
            }
            for s, e in pieces
            if e > s
        )
    return segments


def migrate_legacy_json(db: SessionDB, json_path: Path) -> int:
    """Import sessions.json into the database, then rename it to .bak.

    Only canonical fields are kept (id/date/startTime/endTime/segments).
    Early sessions stored wall-clock segments with a separate pauses[] list;
    those are converted to pause-free segments so hour math derived from
    segments stays truthful. Other derived fields (day, durationHrs,
    activeMinutes) are dropped — derived values are never stored.
    """
    import json

    sessions = json.loads(json_path.read_text(encoding="utf-8"))
    imported = 0
    for s in sessions:
        if db.has(s["id"]):
            continue
        if s.get("pauses"):
            segments = _subtract_pauses(s)
        else:
            segments = [
                {
                    "topic": seg["topic"],
                    "startTime": seg["startTime"],
                    "endTime": seg["endTime"],
                }
                for seg in s["segments"]
            ]
        db.append(
            {
                "id": s["id"],
                "date": s["date"],
                "startTime": s["startTime"],
                "endTime": s["endTime"],
                "segments": segments,
            }
        )
        imported += 1
    json_path.rename(json_path.with_suffix(".json.bak"))
    return imported


class DbStore(FileStore):
    """Store with the active session on disk and completed sessions in SQLite.

    current-session.json stays a file so external watchers (toast scripts,
    Claude Code status checks) keep working; sessions.db replaces
    sessions.json. A leftover sessions.json is migrated on first use.
    """

    def __init__(self, data_dir):
        super().__init__(data_dir)
        self.db = SessionDB(Path(data_dir) / "sessions.db")
        legacy = Path(data_dir) / "sessions.json"
        if legacy.exists():
            migrate_legacy_json(self.db, legacy)

    def read_all_completed(self) -> "list[dict]":
        return self.db.all_sessions()

    def append_completed(self, session: dict) -> None:
        self.db.append(session)
