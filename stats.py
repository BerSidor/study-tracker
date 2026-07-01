"""Hour math over sessions. All values derived from segment times; nothing stored.

Domain rules (CONTEXT.md): a session belongs to its start date, even across
midnight; the week runs Monday-Saturday and Sunday never counts toward the goal.
"""
from datetime import date, datetime, timedelta

from duration import active_minutes


def session_hours(session: dict) -> float:
    """Active hours of a session: sum of its closed segments."""
    mins = sum(
        active_minutes(seg["startTime"], seg["endTime"])
        for seg in session["segments"]
        if seg["endTime"] is not None
    )
    return mins / 60


def hours_for_date(sessions: "list[dict]", date_str: str) -> float:
    return sum(session_hours(s) for s in sessions if s["date"] == date_str)


def week_start(day: date) -> date:
    """Monday of the week containing `day`."""
    return day - timedelta(days=day.weekday())


def week_hours(sessions: "list[dict]", today: date) -> float:
    """Hours logged Monday-Saturday of the week containing `today`."""
    monday = week_start(today)
    saturday = monday + timedelta(days=5)
    total = 0.0
    for s in sessions:
        d = datetime.strptime(s["date"], "%Y-%m-%d").date()
        if monday <= d <= saturday:
            total += session_hours(s)
    return total


def daily_totals(sessions: "list[dict]") -> "list[dict]":
    """Per-date totals, newest first: [{date, day, hours}]."""
    totals: dict[str, float] = {}
    for s in sessions:
        totals[s["date"]] = totals.get(s["date"], 0.0) + session_hours(s)
    return [
        {
            "date": d,
            "day": datetime.strptime(d, "%Y-%m-%d").strftime("%A"),
            "hours": round(h, 4),
        }
        for d, h in sorted(totals.items(), reverse=True)
    ]


def weekly_summary(sessions: "list[dict]") -> "list[dict]":
    """Per-week totals (Mon-Sat only), newest first: [{weekStart, hours}]."""
    totals: dict[str, float] = {}
    for s in sessions:
        d = datetime.strptime(s["date"], "%Y-%m-%d").date()
        if d.weekday() == 6:  # Sunday is a rest day
            continue
        totals[week_start(d).isoformat()] = (
            totals.get(week_start(d).isoformat(), 0.0) + session_hours(s)
        )
    return [
        {"weekStart": w, "hours": round(h, 4)}
        for w, h in sorted(totals.items(), reverse=True)
    ]
