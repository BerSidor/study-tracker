import argparse
import sys
from datetime import datetime
from pathlib import Path

from session import FileStore, SessionError, SessionManager

DATA_DIR = Path(__file__).parent / "data"


def now() -> str:
    return datetime.now().strftime("%H:%M")


def minutes_between(start: str, end: str) -> int:
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    start_mins = sh * 60 + sm
    end_mins = eh * 60 + em
    if end_mins < start_mins:   # midnight crossover
        end_mins += 24 * 60
    return end_mins - start_mins


def fmt_duration(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def print_session_summary(session: dict) -> None:
    topic_minutes: dict[str, int] = {}
    for seg in session["segments"]:
        mins = minutes_between(seg["startTime"], seg["endTime"])
        topic_minutes[seg["topic"]] = topic_minutes.get(seg["topic"], 0) + mins

    total = sum(topic_minutes.values())
    print(f"\nSession closed — {fmt_duration(total)} total")
    width = max(len(t) for t in topic_minutes)
    for topic, mins in topic_minutes.items():
        print(f"  {topic:<{width}}  {fmt_duration(mins)}")


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

    p_done = sub.add_parser("done", help="Close the current session")
    p_done.add_argument("time", nargs="?", default=None)

    args = parser.parse_args()
    t = args.time if hasattr(args, "time") and args.time else now()

    sm = SessionManager(FileStore(DATA_DIR))

    try:
        if args.command == "start":
            sm.start_session(args.topic, t)
            print(f"Session started — {args.topic} ({t})")

        elif args.command == "switch":
            sm.switch_topic(args.topic, t)
            print(f"Switched to {args.topic} ({t})")

        elif args.command == "pause":
            sm.pause_session(t)
            print(f"Paused ({t})")

        elif args.command == "resume":
            sm.resume_session(t)
            print(f"Resumed ({t})")

        elif args.command == "done":
            session = sm.close_session(t)
            print_session_summary(session)

    except SessionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
