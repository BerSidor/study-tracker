import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,
    date       TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time   TEXT
);
CREATE TABLE IF NOT EXISTS segments (
    session_id TEXT    NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    seq        INTEGER NOT NULL,
    topic      TEXT    NOT NULL,
    start_time TEXT    NOT NULL,
    end_time   TEXT,
    PRIMARY KEY (session_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date);
"""


def _relax_end_time_notnull(conn: sqlite3.Connection) -> None:
    """Old on-disk databases declared end_time NOT NULL on both tables (from
    when the active session lived in current-session.json and every row in
    sessions.db was necessarily closed). SQLite can't ALTER COLUMN to drop a
    NOT NULL constraint, so rebuild both tables under the relaxed schema and
    copy rows across. No-op once already migrated."""
    info = conn.execute("PRAGMA table_info(sessions)").fetchall()
    notnull = next(c[3] for c in info if c[1] == "end_time")
    if notnull == 0:
        return

    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("ALTER TABLE sessions RENAME TO sessions_old")
    conn.execute("ALTER TABLE segments RENAME TO segments_old")
    conn.execute("DROP INDEX IF EXISTS idx_sessions_date")
    conn.execute(
        "CREATE TABLE sessions (id TEXT PRIMARY KEY, date TEXT NOT NULL,"
        " start_time TEXT NOT NULL, end_time TEXT)"
    )
    conn.execute(
        "CREATE TABLE segments (session_id TEXT NOT NULL REFERENCES sessions(id)"
        " ON DELETE CASCADE, seq INTEGER NOT NULL, topic TEXT NOT NULL,"
        " start_time TEXT NOT NULL, end_time TEXT, PRIMARY KEY (session_id, seq))"
    )
    conn.execute("INSERT INTO sessions SELECT * FROM sessions_old")
    conn.execute("INSERT INTO segments SELECT * FROM segments_old")
    conn.execute("DROP TABLE segments_old")
    conn.execute("DROP TABLE sessions_old")
    conn.execute("CREATE INDEX idx_sessions_date ON sessions(date)")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()


class SessionDB:
    """Every session lives here — the active session is the row with
    end_time IS NULL (and its open segment, likewise); every other row is a
    completed session. One seam, not two. See ADR-0002.

    Connections are short-lived (one per call) so cli.py and the web server
    can operate on the same database concurrently.
    """

    def __init__(self, db_path):
        self._path = Path(db_path)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
        with self._connect() as conn:
            _relax_end_time_notnull(conn)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _upsert(self, conn: sqlite3.Connection, session: dict, end_time: "str | None") -> None:
        conn.execute(
            "INSERT INTO sessions (id, date, start_time, end_time) VALUES (?, ?, ?, ?)"
            " ON CONFLICT(id) DO UPDATE SET date=excluded.date,"
            " start_time=excluded.start_time, end_time=excluded.end_time",
            (session["id"], session["date"], session["startTime"], end_time),
        )
        conn.execute("DELETE FROM segments WHERE session_id = ?", (session["id"],))
        conn.executemany(
            "INSERT INTO segments (session_id, seq, topic, start_time, end_time)"
            " VALUES (?, ?, ?, ?, ?)",
            [
                (session["id"], i, seg["topic"], seg["startTime"], seg["endTime"])
                for i, seg in enumerate(session["segments"])
            ],
        )

    def append(self, session: dict) -> None:
        """Persist a completed session. An upsert, not a plain insert:
        closing a session updates the same row that was its open row (same
        id), it doesn't create a new one."""
        with self._connect() as conn:
            self._upsert(conn, session, session["endTime"])

    def write_current(self, session: dict) -> None:
        with self._connect() as conn:
            self._upsert(conn, session, None)

    def read_current(self) -> "dict | None":
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, date, start_time FROM sessions WHERE end_time IS NULL"
            ).fetchone()
            if row is None:
                return None
            sid, date, start = row
            seg_rows = conn.execute(
                "SELECT topic, start_time, end_time FROM segments"
                " WHERE session_id = ? ORDER BY seq",
                (sid,),
            ).fetchall()
        return {
            "id": sid,
            "date": date,
            "startTime": start,
            "segments": [
                {"topic": topic, "startTime": start, "endTime": end}
                for topic, start, end in seg_rows
            ],
        }

    def delete_current(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE end_time IS NULL")

    def completed_sessions(self) -> "list[dict]":
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, date, start_time, end_time FROM sessions"
                " WHERE end_time IS NOT NULL ORDER BY id"
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


def migrate_legacy_current_session(db: SessionDB, json_path: Path) -> None:
    """Import a leftover current-session.json — the active session from the
    pre-unification two-seam design — as the open row, then rename it to
    .bak. Mirrors migrate_legacy_json's shape for the completed archive."""
    import json

    session = json.loads(json_path.read_text(encoding="utf-8"))
    db.write_current(session)
    json_path.rename(json_path.with_suffix(".json.bak"))


class DbStore:
    """Store entirely backed by SQLite: the active session is the row with
    end_time IS NULL (and its open segment likewise); completed sessions are
    every other row. See ADR-0002.

    A leftover sessions.json (pre-SQLite archive) or current-session.json
    (pre-unification active session) is migrated in on first use, then
    renamed .bak.
    """

    def __init__(self, data_dir):
        self.db = SessionDB(Path(data_dir) / "sessions.db")

        legacy_archive = Path(data_dir) / "sessions.json"
        if legacy_archive.exists():
            migrate_legacy_json(self.db, legacy_archive)

        legacy_current = Path(data_dir) / "current-session.json"
        if legacy_current.exists():
            migrate_legacy_current_session(self.db, legacy_current)

    def read_current(self) -> "dict | None":
        return self.db.read_current()

    def write_current(self, session: dict) -> None:
        self.db.write_current(session)

    def delete_current(self) -> None:
        self.db.delete_current()

    def read_all_completed(self) -> "list[dict]":
        return self.db.completed_sessions()

    def append_completed(self, session: dict) -> None:
        self.db.append(session)
