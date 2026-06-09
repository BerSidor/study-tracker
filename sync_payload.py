from datetime import datetime


def _minutes_between(start: str, end: str) -> int:
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    start_mins = sh * 60 + sm
    end_mins = eh * 60 + em
    if end_mins < start_mins:   # midnight crossover
        end_mins += 24 * 60
    return end_mins - start_mins


def _day_name(date: str) -> str:
    return datetime.strptime(date, "%Y-%m-%d").strftime("%A")


def build_sync_payload(session: dict) -> dict:
    segments = []
    total_mins = 0
    for seg in session["segments"]:
        mins = _minutes_between(seg["startTime"], seg["endTime"])
        total_mins += mins
        segments.append({"topic": seg["topic"], "durationHrs": round(mins / 60, 6)})

    return {
        "id":         session["id"],
        "date":       session["date"],
        "day":        _day_name(session["date"]),
        "startTime":  session["startTime"],
        "endTime":    session["endTime"],
        "durationHrs": round(total_mins / 60, 6),
        "segments":   segments,
        "notes":      session.get("notes", ""),
    }


def fmt_hrs(hrs: float) -> str:
    h = int(hrs)
    m = round((hrs - h) * 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"
