import json
import os
from datetime import datetime
from pathlib import Path


class SessionError(Exception):
    pass


class FileStore:
    def __init__(self, data_dir):
        self._dir = Path(data_dir)
        self._current_path = self._dir / "current-session.json"
        self._completed_path = self._dir / "sessions.json"

    def read_current(self):
        if not self._current_path.exists():
            return None
        return json.loads(self._current_path.read_text(encoding="utf-8"))

    def write_current(self, session):
        self._current_path.write_text(json.dumps(session, indent=2), encoding="utf-8")

    def delete_current(self):
        if self._current_path.exists():
            os.remove(self._current_path)

    def read_all_completed(self):
        if not self._completed_path.exists():
            return []
        return json.loads(self._completed_path.read_text(encoding="utf-8"))

    def append_completed(self, session):
        completed = self.read_all_completed()
        completed.append(session)
        self._completed_path.write_text(json.dumps(completed, indent=2), encoding="utf-8")


class SessionManager:
    def __init__(self, store):
        self._store = store

    def start_session(self, topic: str, time: str, date: str = None) -> None:
        if self._store.read_current() is not None:
            raise SessionError("A session is already active. Close it before starting a new one.")

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        existing = self._store.read_all_completed()
        count = sum(1 for s in existing if s["date"] == date)
        session_id = f"{date}-{count + 1:03d}"

        session = {
            "id": session_id,
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

        for seg in session["segments"]:
            if seg["endTime"] is None:
                seg["endTime"] = time
                break

        session["segments"].append({"topic": topic, "startTime": time, "endTime": None})
        self._store.write_current(session)

    def pause_session(self, time: str) -> None:
        session = self._store.read_current()
        if session is None:
            raise SessionError("No session is currently open.")

        for seg in session["segments"]:
            if seg["endTime"] is None:
                seg["endTime"] = time
                break

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

        for seg in session["segments"]:
            if seg["endTime"] is None:
                seg["endTime"] = time
                break

        session["endTime"] = time
        self._store.append_completed(session)
        self._store.delete_current()
        return session
