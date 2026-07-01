import json
import sqlite3

import pytest

from db import DbStore, SessionDB, migrate_legacy_current_session, migrate_legacy_json
from session import SessionManager

SESSION = {
    "id": "2026-06-11-001",
    "date": "2026-06-11",
    "startTime": "09:22",
    "segments": [
        {"topic": "CLI basics & configuration", "startTime": "09:22", "endTime": "10:45"},
        {"topic": "CLAUDE.md & project context", "startTime": "23:15", "endTime": "00:05"},
    ],
    "endTime": "00:05",
}


def test_append_and_read_roundtrip(tmp_path):
    db = SessionDB(tmp_path / "sessions.db")
    db.append(SESSION)
    assert db.completed_sessions() == [SESSION]


def test_sessions_ordered_by_id(tmp_path):
    db = SessionDB(tmp_path / "sessions.db")
    later = dict(SESSION, id="2026-06-11-002")
    db.append(later)
    db.append(SESSION)
    assert [s["id"] for s in db.completed_sessions()] == ["2026-06-11-001", "2026-06-11-002"]


def test_migration_drops_derived_fields_and_renames(tmp_path):
    legacy = [
        {
            **SESSION,
            "day": "Thursday",
            "durationHrs": 6.33,
            "pauses": [{"startTime": "17:05", "endTime": "18:00"}],
            "segments": [
                {**seg, "activeMinutes": 142, "durationHrs": 2.37}
                for seg in SESSION["segments"]
            ],
        }
    ]
    json_path = tmp_path / "sessions.json"
    json_path.write_text(json.dumps(legacy), encoding="utf-8")

    db = SessionDB(tmp_path / "sessions.db")
    imported = migrate_legacy_json(db, json_path)

    assert imported == 1
    assert db.completed_sessions() == [SESSION]
    assert not json_path.exists()
    assert (tmp_path / "sessions.json.bak").exists()


def test_migration_subtracts_legacy_pauses(tmp_path):
    # Real 2026-06-04 session: wall-clock segments + pauses[], stored
    # durationHrs was 6.33 — derived hours after migration must match.
    legacy = [{
        "id": "2026-06-04-001",
        "date": "2026-06-04",
        "day": "Thursday",
        "startTime": "15:00",
        "endTime": "00:25",
        "durationHrs": 6.33,
        "segments": [
            {"topic": "Claude Code hooks", "startTime": "15:00", "endTime": "18:17"},
            {"topic": "Token usage", "startTime": "18:17", "endTime": "20:05"},
            {"topic": "React and AWS", "startTime": "20:05", "endTime": "22:09"},
            {"topic": "Startups", "startTime": "22:09", "endTime": "00:25"},
        ],
        "pauses": [
            {"startTime": "17:05", "endTime": "18:00"},
            {"startTime": "20:18", "endTime": "21:36"},
            {"startTime": "23:33", "endTime": "00:25"},
        ],
    }]
    json_path = tmp_path / "sessions.json"
    json_path.write_text(json.dumps(legacy), encoding="utf-8")

    db = SessionDB(tmp_path / "sessions.db")
    migrate_legacy_json(db, json_path)

    from stats import session_hours
    migrated = db.completed_sessions()[0]
    assert round(session_hours(migrated), 2) == 6.33
    # pause in the middle of the first segment splits it in two
    assert migrated["segments"][0] == {
        "topic": "Claude Code hooks", "startTime": "15:00", "endTime": "17:05"
    }
    assert migrated["segments"][1] == {
        "topic": "Claude Code hooks", "startTime": "18:00", "endTime": "18:17"
    }
    # final pause runs to session end, so the last segment ends at 23:33
    assert migrated["segments"][-1] == {
        "topic": "Startups", "startTime": "22:09", "endTime": "23:33"
    }


def test_migration_skips_already_imported(tmp_path):
    db = SessionDB(tmp_path / "sessions.db")
    db.append(SESSION)
    json_path = tmp_path / "sessions.json"
    json_path.write_text(json.dumps([SESSION]), encoding="utf-8")

    assert migrate_legacy_json(db, json_path) == 0
    assert len(db.completed_sessions()) == 1


def test_dbstore_migrates_on_init(tmp_path):
    (tmp_path / "sessions.json").write_text(json.dumps([SESSION]), encoding="utf-8")
    store = DbStore(tmp_path)
    assert store.read_all_completed() == [SESSION]
    assert not (tmp_path / "sessions.json").exists()


def test_session_lifecycle_through_dbstore(tmp_path):
    store = DbStore(tmp_path)
    sm = SessionManager(store)

    sm.start_session("Hooks system", "09:00", date="2026-06-12")
    assert store.read_current() is not None

    sm.pause_session("10:00")
    sm.resume_session("10:30")
    sm.switch_topic("MCP servers", "11:00")
    closed = sm.close_session("12:00")

    assert store.read_current() is None
    assert store.read_all_completed() == [closed]
    assert closed["id"] == "2026-06-12-001"

    sm.start_session("Hooks system", "13:00", date="2026-06-12")
    sm.close_session("14:00")
    assert store.read_all_completed()[-1]["id"] == "2026-06-12-002"


def test_nullable_schema_migrates_old_notnull_db(tmp_path):
    db_path = tmp_path / "sessions.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY, date TEXT NOT NULL,
            start_time TEXT NOT NULL, end_time TEXT NOT NULL
        );
        CREATE TABLE segments (
            session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            seq INTEGER NOT NULL, topic TEXT NOT NULL,
            start_time TEXT NOT NULL, end_time TEXT NOT NULL,
            PRIMARY KEY (session_id, seq)
        );
        CREATE INDEX idx_sessions_date ON sessions(date);
        """
    )
    conn.execute(
        "INSERT INTO sessions VALUES (?, ?, ?, ?)",
        (SESSION["id"], SESSION["date"], SESSION["startTime"], SESSION["endTime"]),
    )
    conn.executemany(
        "INSERT INTO segments VALUES (?, ?, ?, ?, ?)",
        [
            (SESSION["id"], i, seg["topic"], seg["startTime"], seg["endTime"])
            for i, seg in enumerate(SESSION["segments"])
        ],
    )
    conn.commit()
    conn.close()

    db = SessionDB(db_path)

    check = sqlite3.connect(db_path)
    info = {row[1]: row[3] for row in check.execute("PRAGMA table_info(sessions)")}
    seg_info = {row[1]: row[3] for row in check.execute("PRAGMA table_info(segments)")}
    check.close()

    assert info["end_time"] == 0
    assert seg_info["end_time"] == 0
    assert db.completed_sessions() == [SESSION]


def test_write_read_delete_current_roundtrip_on_sessiondb(tmp_path):
    db = SessionDB(tmp_path / "sessions.db")
    open_session = {
        "id": "2026-06-20-001",
        "date": "2026-06-20",
        "startTime": "09:00",
        "segments": [{"topic": "MCP servers", "startTime": "09:00", "endTime": None}],
    }

    db.write_current(open_session)
    assert db.read_current() == open_session
    assert db.completed_sessions() == []

    db.delete_current()
    assert db.read_current() is None


def test_append_completed_upserts_matching_open_row(tmp_path):
    db = SessionDB(tmp_path / "sessions.db")
    open_session = {
        "id": "2026-06-21-001",
        "date": "2026-06-21",
        "startTime": "09:00",
        "segments": [{"topic": "MCP servers", "startTime": "09:00", "endTime": None}],
    }
    db.write_current(open_session)

    closed_session = {
        **open_session,
        "segments": [{"topic": "MCP servers", "startTime": "09:00", "endTime": "10:00"}],
        "endTime": "10:00",
    }
    db.append(closed_session)

    assert db.completed_sessions() == [closed_session]
    assert db.read_current() is None


def test_migrate_legacy_current_session(tmp_path):
    db = SessionDB(tmp_path / "sessions.db")
    open_session = {
        "id": "2026-07-01-001",
        "date": "2026-07-01",
        "startTime": "11:20",
        "segments": [
            {"topic": "Deployed end-to-end app", "startTime": "11:20", "endTime": "11:22"},
            {"topic": "Cybersecurity concerns with vibe coding", "startTime": "11:22", "endTime": None},
        ],
    }
    json_path = tmp_path / "current-session.json"
    json_path.write_text(json.dumps(open_session), encoding="utf-8")

    migrate_legacy_current_session(db, json_path)

    assert db.read_current() == open_session
    assert not json_path.exists()
    assert (tmp_path / "current-session.json.bak").exists()


def test_dbstore_migrates_legacy_current_session_on_init(tmp_path):
    open_session = {
        "id": "2026-07-01-001",
        "date": "2026-07-01",
        "startTime": "11:20",
        "segments": [{"topic": "MCP servers", "startTime": "11:20", "endTime": None}],
    }
    (tmp_path / "current-session.json").write_text(json.dumps(open_session), encoding="utf-8")

    store = DbStore(tmp_path)

    assert store.read_current() == open_session
    assert not (tmp_path / "current-session.json").exists()
    assert (tmp_path / "current-session.json.bak").exists()
