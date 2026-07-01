import json
import os
from datetime import datetime
from pathlib import Path
from typing import Protocol

from duration import DurationError, active_minutes


class SessionError(Exception):
    pass


class CurrentSessionStore(Protocol):
    """The single active session, kept where external watchers can read it."""
    def read_current(self) -> "dict | None": ...
    def write_current(self, session: dict) -> None: ...
    def delete_current(self) -> None: ...


class CompletedSessionStore(Protocol):
    """The archive of finished sessions."""
    def read_all_completed(self) -> "list[dict]": ...
    def append_completed(self, session: dict) -> None: ...


class Store(CurrentSessionStore, CompletedSessionStore, Protocol):
    """Everything SessionManager needs: the active session plus the archive.

    These are two independent seams — the active session lives wherever external
    watchers can read it (a file), the archive wherever queries are cheap (SQLite in
    production). Adapters *compose* the two via CurrentSessionFile rather than fusing
    them by inheritance.
    """


class CurrentSessionFile:
    """The active session as current-session.json.

    Kept as a plain file on purpose: external watchers (toast scripts, Claude Code
    status checks) read live session state from it. Shared by every Store adapter so
    the active-session-on-disk logic lives in exactly one place.
    """

    def __init__(self, data_dir):
        self._path = Path(data_dir) / "current-session.json"

    def read_current(self) -> "dict | None":
        if not self._path.exists():
            return None
        return json.loads(self._path.read_text(encoding="utf-8"))

    def write_current(self, session: dict) -> None:
        self._path.write_text(json.dumps(session, indent=2), encoding="utf-8")

    def delete_current(self) -> None:
        if self._path.exists():
            os.remove(self._path)


class FileStore:
    """Full file-backed Store: active session in current-session.json, archive in
    sessions.json. The no-database reference adapter, used in tests."""

    def __init__(self, data_dir):
        self._current = CurrentSessionFile(data_dir)
        self._completed_path = Path(data_dir) / "sessions.json"

    def read_current(self) -> "dict | None":
        return self._current.read_current()

    def write_current(self, session: dict) -> None:
        self._current.write_current(session)

    def delete_current(self) -> None:
        self._current.delete_current()

    def read_all_completed(self) -> "list[dict]":
        if not self._completed_path.exists():
            return []
        return json.loads(self._completed_path.read_text(encoding="utf-8"))

    def append_completed(self, session: dict) -> None:
        completed = self.read_all_completed()
        completed.append(session)
        self._completed_path.write_text(json.dumps(completed, indent=2), encoding="utf-8")


class SessionManager:
    def __init__(self, store: Store) -> None:
        self._store = store

    def _next_session_id(self, date: str) -> str:
        count = sum(1 for s in self._store.read_all_completed() if s["date"] == date)
        return f"{date}-{count + 1:03d}"

    def _close_open_segment(self, session: dict, time: str) -> None:
        for seg in session["segments"]:
            if seg["endTime"] is None:
                try:
                    active_minutes(seg["startTime"], time)  # validates via the Duration rule
                except DurationError:
                    raise SessionError(
                        f"End time {time} is before segment start {seg['startTime']}."
                    )
                seg["endTime"] = time
                return

    def start_session(self, topic: str, time: str, date: str = None) -> None:
        if self._store.read_current() is not None:
            raise SessionError("A session is already active. Close it before starting a new one.")

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        session = {
            "id": self._next_session_id(date),
            "date": date,
            "startTime": time,
            "segments": [
                {"topic": topic, "startTime": time, "endTime": None}
            ],
        }
        self._store.write_current(session)

    def switch_topic(self, topic: str, time: str) -> None:
        session = self._store.read_current()
        if session is None:
            raise SessionError("No session is open — did you mean start?")

        self._close_open_segment(session, time)
        session["segments"].append({"topic": topic, "startTime": time, "endTime": None})
        self._store.write_current(session)

    def pause_session(self, time: str) -> None:
        session = self._store.read_current()
        if session is None:
            raise SessionError("No session is currently open.")

        self._close_open_segment(session, time)
        self._store.write_current(session)

    def resume_session(self, time: str) -> None:
        session = self._store.read_current()
        if session is None:
            raise SessionError("No session is currently open.")

        last_topic = session["segments"][-1]["topic"]
        session["segments"].append({"topic": last_topic, "startTime": time, "endTime": None})
        self._store.write_current(session)

    def close_session(self, time: str) -> dict:
        session = self._store.read_current()
        if session is None:
            raise SessionError("No session is currently open.")

        self._close_open_segment(session, time)
        session["endTime"] = time
        self._store.append_completed(session)
        self._store.delete_current()
        return session
