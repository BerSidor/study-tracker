import argparse
import json
import sys
from pathlib import Path

from notifier import make_notifier
from session import FileStore, SessionError, SessionManager
from sheet_sync import SyncError, sync_session
from sync_payload import build_sync_payload, fmt_hrs

DATA_DIR = Path(__file__).parent / "data"


def now() -> str:
    from datetime import datetime
    return datetime.now().strftime("%H:%M")


def print_session_summary(payload: dict) -> None:
    topic_hrs: dict[str, float] = {}
    for seg in payload["segments"]:
        topic_hrs[seg["topic"]] = topic_hrs.get(seg["topic"], 0) + seg["durationHrs"]

    print(f"\nSession closed — {fmt_hrs(payload['durationHrs'])} total")
    width = max(len(t) for t in topic_hrs)
    for topic, hrs in topic_hrs.items():
        print(f"  {topic:<{width}}  {fmt_hrs(hrs)}")


def main():
    parser = argparse.ArgumentParser(prog="cli.py")
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="Start a new session")
    p_start.add_argument("topic")
    p_start.add_argument("time", nargs="?", default=None)

    p_switch = sub.add_parser("switch", help="Switch to a different topic")
    p_switch.add_argument("topic")
    p_switch.add_argument("time", nargs="?", default=None)

    p_pause = sub.add_parser("pause", help="Pause the current session")
    p_pause.add_argument("time", nargs="?", default=None)

    p_resume = sub.add_parser("resume", help="Resume the current session")
    p_resume.add_argument("time", nargs="?", default=None)

    p_done = sub.add_parser("done", help="Close the current session and sync the sheet")
    p_done.add_argument("time", nargs="?", default=None)

    args = parser.parse_args()
    t = args.time if hasattr(args, "time") and args.time else now()

    sm = SessionManager(FileStore(DATA_DIR))
    notifier = make_notifier()

    try:
        if args.command == "start":
            sm.start_session(args.topic, t)
            print(f"Session started — {args.topic} ({t})")
            notifier.notify(f"Session started — {args.topic}")

        elif args.command == "switch":
            sm.switch_topic(args.topic, t)
            print(f"Switched to {args.topic} ({t})")
            notifier.notify(f"Now studying: {args.topic}")

        elif args.command == "pause":
            sm.pause_session(t)
            print(f"Paused ({t})")
            notifier.notify("Session paused")

        elif args.command == "resume":
            sm.resume_session(t)
            print(f"Resumed ({t})")
            notifier.notify("Session resumed")

        elif args.command == "done":
            session = sm.close_session(t)
            payload = build_sync_payload(session)
            print_session_summary(payload)

            config = json.loads((DATA_DIR / "config.json").read_text(encoding="utf-8"))
            try:
                sync_session(config["webAppUrl"], payload)
                print(f"\nSheet updated: {config['sheetUrl']}")
                notifier.notify(f"Session saved — {fmt_hrs(payload['durationHrs'])}")
            except SyncError as e:
                print(f"Sync failed: {e}", file=sys.stderr)
                sys.exit(1)

    except SessionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
