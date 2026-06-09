import json
import pytest
from session import SessionManager, SessionError, FileStore


class InMemoryStore:
    def __init__(self):
        self._current = None
        self._completed = []

    def read_current(self):
        return self._current

    def write_current(self, session):
        self._current = session

    def delete_current(self):
        self._current = None

    def append_completed(self, session):
        self._completed.append(session)

    def read_all_completed(self):
        return self._completed


# ── Tracer bullet ──────────────────────────────────────────────────────────────

def test_start_and_close_returns_valid_session():
    store = InMemoryStore()
    sm = SessionManager(store)

    sm.start_session("MCP servers", "09:00", date="2026-01-15")
    session = sm.close_session("10:00")

    assert session["id"] == "2026-01-15-001"
    assert session["date"] == "2026-01-15"
    assert session["startTime"] == "09:00"
    assert session["endTime"] == "10:00"
    assert len(session["segments"]) == 1
    assert session["segments"][0]["topic"] == "MCP servers"
    assert session["segments"][0]["startTime"] == "09:00"
    assert session["segments"][0]["endTime"] == "10:00"


def test_close_session_is_persisted_to_store():
    store = InMemoryStore()
    sm = SessionManager(store)

    sm.start_session("MCP servers", "09:00", date="2026-01-15")
    sm.close_session("10:00")

    assert len(store.read_all_completed()) == 1
    assert store.read_current() is None


# ── switch_topic ───────────────────────────────────────────────────────────────

def test_switch_topic_produces_two_segments():
    store = InMemoryStore()
    sm = SessionManager(store)

    sm.start_session("MCP servers", "09:00", date="2026-01-15")
    sm.switch_topic("Claude Code hooks", "10:30")
    session = sm.close_session("12:00")

    assert len(session["segments"]) == 2
    assert session["segments"][0] == {"topic": "MCP servers",      "startTime": "09:00", "endTime": "10:30"}
    assert session["segments"][1] == {"topic": "Claude Code hooks", "startTime": "10:30", "endTime": "12:00"}


# ── pause / resume ─────────────────────────────────────────────────────────────

def test_pause_and_resume_produces_two_segments_same_topic():
    store = InMemoryStore()
    sm = SessionManager(store)

    sm.start_session("MCP servers", "09:00", date="2026-01-15")
    sm.pause_session("10:00")
    sm.resume_session("10:30")
    session = sm.close_session("12:00")

    assert len(session["segments"]) == 2
    assert session["segments"][0] == {"topic": "MCP servers", "startTime": "09:00", "endTime": "10:00"}
    assert session["segments"][1] == {"topic": "MCP servers", "startTime": "10:30", "endTime": "12:00"}


# ── error states ───────────────────────────────────────────────────────────────

def test_start_while_active_raises():
    store = InMemoryStore()
    sm = SessionManager(store)

    sm.start_session("MCP servers", "09:00", date="2026-01-15")

    with pytest.raises(SessionError):
        sm.start_session("Claude Code hooks", "10:00", date="2026-01-15")


def test_close_while_idle_raises():
    store = InMemoryStore()
    sm = SessionManager(store)

    with pytest.raises(SessionError):
        sm.close_session("10:00")


def test_switch_while_idle_raises():
    store = InMemoryStore()
    sm = SessionManager(store)

    with pytest.raises(SessionError):
        sm.switch_topic("Claude Code hooks", "10:00")


# ── FileStore ──────────────────────────────────────────────────────────────────

def test_file_store_persists_session_across_instances(tmp_path):
    store = FileStore(tmp_path)
    sm = SessionManager(store)

    sm.start_session("MCP servers", "09:00", date="2026-01-15")
    sm.switch_topic("Claude Code hooks", "10:30")
    sm.close_session("12:00")

    # Fresh store — simulates a new process reading the same data directory
    fresh_store = FileStore(tmp_path)
    completed = fresh_store.read_all_completed()

    assert len(completed) == 1
    assert completed[0]["id"] == "2026-01-15-001"
    assert len(completed[0]["segments"]) == 2
    assert fresh_store.read_current() is None
