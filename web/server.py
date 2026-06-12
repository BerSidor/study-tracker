"""Local web UI for the study tracker.

Serves the Forest Dawn dashboard and a JSON API over the same stores cli.py
uses, so the browser and Claude Code chat stay in sync through the database
and current-session.json. Run: python web/server.py [--port 8766] [--no-sync]
"""
import argparse
import json
import re
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import planparse
import stats
from db import DbStore
from session import SessionError, SessionManager
from sheet_sync import SyncError, sync_session
from sync_payload import build_sync_payload

DATA_DIR = ROOT / "data"
PLANS_DIR = ROOT / "docs" / "weekly-plans"
STATIC_DIR = Path(__file__).resolve().parent / "static"

TIME_RE = re.compile(r"^\d{2}:\d{2}$")

LOCK = threading.Lock()
STORE = DbStore(DATA_DIR)
SM = SessionManager(STORE)
SYNC_ENABLED = True


def now_hhmm() -> str:
    return datetime.now().strftime("%H:%M")


def load_config() -> dict:
    return json.loads((DATA_DIR / "config.json").read_text(encoding="utf-8"))


def mtime(path: Path) -> float:
    return path.stat().st_mtime if path.exists() else 0


def version() -> dict:
    return {
        "current": mtime(DATA_DIR / "current-session.json"),
        "sessions": mtime(DATA_DIR / "sessions.db"),
        "plans": max((mtime(p) for p in PLANS_DIR.glob("week*-daily.md")), default=0),
        "config": mtime(DATA_DIR / "config.json"),
    }


def state_payload() -> dict:
    config = load_config()
    completed = STORE.read_all_completed()
    current = STORE.read_current()
    today = datetime.now().strftime("%Y-%m-%d")

    current_closed = stats.session_hours(current) if current else 0
    open_start = None
    if current:
        last = current["segments"][-1]
        if last["endTime"] is None:
            open_start = last["startTime"]

    return {
        "serverTime": datetime.now().strftime("%H:%M:%S"),
        "date": today,
        "current": current,
        "todayClosedHrs": stats.hours_for_date(completed, today),
        "currentClosedHrs": current_closed,
        "openSegmentStart": open_start,
        "dailyTargetHours": config["dailyTargetHours"],
        "weekHrs": stats.week_hours(completed, datetime.now().date()),
        "weeklyGoalHours": config["weeklyGoalHours"],
        "syncEnabled": SYNC_ENABLED,
        "version": version(),
    }


def plan_payload() -> dict:
    weeks = planparse.load_weeks(PLANS_DIR)
    return {"active": planparse.find_active(weeks), "weeks": weeks}


def enrich_session(session: dict) -> dict:
    segments = []
    pauses = []
    prev_end = None
    for seg in session["segments"]:
        mins = (
            stats._minutes_between(seg["startTime"], seg["endTime"])
            if seg["endTime"] is not None
            else 0
        )
        segments.append({**seg, "durationHrs": round(mins / 60, 4)})
        if prev_end is not None and prev_end != seg["startTime"]:
            pauses.append({"startTime": prev_end, "endTime": seg["startTime"]})
        prev_end = seg["endTime"]
    return {
        **session,
        "segments": segments,
        "pauses": pauses,
        "totalHrs": round(stats.session_hours(session), 4),
    }


def history_payload() -> dict:
    config = load_config()
    completed = STORE.read_all_completed()
    return {
        "sessions": [enrich_session(s) for s in completed],
        "dailyTotals": stats.daily_totals(completed),
        "weeks": [
            {**w, "goal": config["weeklyGoalHours"]}
            for w in stats.weekly_summary(completed)
        ],
    }


def topics_payload() -> dict:
    roadmap = json.loads((DATA_DIR / "roadmap.json").read_text(encoding="utf-8"))
    active = planparse.find_active(planparse.load_weeks(PLANS_DIR))
    recent = []
    for session in reversed(STORE.read_all_completed()):
        for seg in reversed(session["segments"]):
            if seg["topic"] not in recent:
                recent.append(seg["topic"])
        if len(recent) >= 10:
            break
    return {
        "today": active["day"]["trackerTopics"] if active else [],
        "roadmap": [
            {"track": track, **topic}
            for track, topics in roadmap["tracks"].items()
            for topic in topics
        ],
        "recent": recent[:10],
    }


def do_session_action(action: str, body: dict) -> "tuple[int, dict]":
    t = body.get("time") or now_hhmm()
    if not TIME_RE.match(t):
        return 400, {"error": f"Invalid time {t!r} — expected HH:MM."}
    topic = (body.get("topic") or "").strip()
    if action in ("start", "switch") and not topic:
        return 400, {"error": "A topic is required."}

    # No Windows toasts here — the browser shows its own in-page
    # notifications; cli.py keeps toasts for chat-driven commands.
    with LOCK:
        if action == "start":
            SM.start_session(topic, t)
        elif action == "switch":
            SM.switch_topic(topic, t)
        elif action == "pause":
            SM.pause_session(t)
        elif action == "resume":
            SM.resume_session(t)
        elif action == "end":
            session = SM.close_session(t)
            payload = build_sync_payload(session)
            config = load_config()
            synced = False
            if SYNC_ENABLED:
                try:
                    sync_session(config["webAppUrl"], payload)
                    synced = True
                except SyncError as e:
                    return 502, {
                        "error": str(e),
                        "savedLocally": True,
                        "payload": payload,
                    }
            return 200, {
                "payload": payload,
                "sheetUrl": config["sheetUrl"],
                "synced": synced,
            }
        else:
            return 404, {"error": f"Unknown action {action!r}."}
    return 200, {"current": STORE.read_current()}


class Handler(BaseHTTPRequestHandler):
    server_version = "StudyUI/1.0"

    def log_message(self, format, *args):
        pass

    def _send_json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, rel: str) -> None:
        path = (STATIC_DIR / rel).resolve()
        if not path.is_relative_to(STATIC_DIR) or not path.is_file():
            self._send_json(404, {"error": "Not found."})
            return
        types = {".html": "text/html", ".js": "text/javascript", ".css": "text/css",
                 ".svg": "image/svg+xml"}
        body = path.read_bytes()
        self.send_response(200)
        self.send_header(
            "Content-Type",
            f"{types.get(path.suffix, 'application/octet-stream')}; charset=utf-8",
        )
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            if self.path == "/" or self.path == "/index.html":
                self._send_static("index.html")
            elif self.path.startswith("/static/"):
                self._send_static(self.path[len("/static/"):])
            elif self.path == "/api/state":
                self._send_json(200, state_payload())
            elif self.path == "/api/plan":
                self._send_json(200, plan_payload())
            elif self.path == "/api/history":
                self._send_json(200, history_payload())
            elif self.path == "/api/topics":
                self._send_json(200, topics_payload())
            else:
                self._send_json(404, {"error": "Not found."})
        except Exception as e:  # keep the server alive on unexpected errors
            self._send_json(500, {"error": str(e)})

    def do_POST(self):
        match = re.match(r"^/api/session/(\w+)$", self.path)
        if not match:
            self._send_json(404, {"error": "Not found."})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
            code, obj = do_session_action(match.group(1), body)
            self._send_json(code, obj)
        except SessionError as e:
            self._send_json(409, {"error": str(e)})
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body."})
        except Exception as e:
            self._send_json(500, {"error": str(e)})


def main():
    global SYNC_ENABLED
    parser = argparse.ArgumentParser(prog="server.py")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--no-sync", action="store_true",
                        help="Skip Google Sheets sync when ending sessions")
    parser.add_argument("--no-browser", action="store_true",
                        help="Don't open a browser tab (used by the Windows startup task)")
    args = parser.parse_args()
    SYNC_ENABLED = not args.no_sync

    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError:
        print(f"Port {args.port} is already in use — the UI is probably already running.")
        return
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Study tracker UI: {url}" + ("  [sync OFF]" if args.no_sync else ""))
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
