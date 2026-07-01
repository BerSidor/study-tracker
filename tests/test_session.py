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


# ── reversed-time guard ────────────────────────────────────────────────────────

class MockStore(InMemoryStore):
    """InMemoryStore that records every write so tests can assert no write happened."""
    def __init__(self):
        super().__init__()
        self.write_count = 0

    def write_current(self, session):
        self.write_count += 1
        super().write_current(session)


class TestReversedTimeGuard:
    """Every path through _close_open_segment must reject endTime < startTime."""

    def _sm(self, start="14:57"):
        store = MockStore()
        sm = SessionManager(store)
        sm.start_session("AI Coding", start, date="2026-06-09")
        return sm, store

    def test_pause_before_start_raises(self):
        sm, store = self._sm("14:57")
        writes_before = store.write_count
        with pytest.raises(SessionError, match="before segment start"):
            sm.pause_session("14:37")
        assert store.write_count == writes_before

    def test_switch_before_start_raises(self):
        sm, store = self._sm("14:57")
        writes_before = store.write_count
        with pytest.raises(SessionError, match="before segment start"):
            sm.switch_topic("MCPs", "14:37")
        assert store.write_count == writes_before

    def test_close_before_start_raises(self):
        sm, store = self._sm("14:57")
        writes_before = store.write_count
        with pytest.raises(SessionError, match="before segment start"):
            sm.close_session("14:37")
        assert store.write_count == writes_before

    def test_segment_remains_open_after_rejection(self):
        sm, store = self._sm("14:57")
        with pytest.raises(SessionError):
            sm.pause_session("14:37")
        current = store.read_current()
        assert current["segments"][-1]["endTime"] is None

    def test_midnight_crossing_is_allowed(self):
        sm, store = self._sm("23:04")
        sm.close_session("00:08")  # crosses midnight — ~1h gap

    def test_exact_same_time_is_allowed(self):
        sm, store = self._sm("14:57")
        sm.pause_session("14:57")

    def test_later_time_is_allowed(self):
        sm, store = self._sm("09:00")
        sm.pause_session("10:30")


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
