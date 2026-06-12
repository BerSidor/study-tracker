from datetime import date

from stats import (
    daily_totals,
    hours_for_date,
    session_hours,
    week_hours,
    week_start,
    weekly_summary,
)


def make_session(sid, d, segs):
    return {
        "id": sid,
        "date": d,
        "startTime": segs[0][1],
        "segments": [
            {"topic": t, "startTime": s, "endTime": e} for t, s, e in segs
        ],
        "endTime": segs[-1][2],
    }


def test_session_hours_sums_segments():
    s = make_session("x", "2026-06-11", [
        ("a", "09:00", "10:30"),
        ("b", "13:00", "14:00"),
    ])
    assert session_hours(s) == 2.5


def test_session_hours_midnight_crossing():
    s = make_session("x", "2026-06-11", [("a", "23:15", "00:05")])
    assert round(session_hours(s) * 60) == 50


def test_session_hours_ignores_open_segment():
    s = {
        "id": "x",
        "date": "2026-06-12",
        "startTime": "09:00",
        "segments": [{"topic": "a", "startTime": "09:00", "endTime": None}],
    }
    assert session_hours(s) == 0


def test_hours_for_date_filters_by_start_date():
    sessions = [
        make_session("a", "2026-06-11", [("t", "23:15", "00:05")]),
        make_session("b", "2026-06-12", [("t", "09:00", "10:00")]),
    ]
    assert round(hours_for_date(sessions, "2026-06-11") * 60) == 50
    assert hours_for_date(sessions, "2026-06-12") == 1


def test_week_start_is_monday():
    assert week_start(date(2026, 6, 12)) == date(2026, 6, 8)  # Friday -> Monday
    assert week_start(date(2026, 6, 8)) == date(2026, 6, 8)


def test_week_hours_excludes_sunday_and_other_weeks():
    sessions = [
        make_session("a", "2026-06-08", [("t", "09:00", "10:00")]),  # Monday
        make_session("b", "2026-06-13", [("t", "09:00", "10:00")]),  # Saturday
        make_session("c", "2026-06-14", [("t", "09:00", "10:00")]),  # Sunday (rest)
        make_session("d", "2026-06-05", [("t", "09:00", "10:00")]),  # previous week
    ]
    assert week_hours(sessions, date(2026, 6, 12)) == 2


def test_daily_totals_newest_first():
    sessions = [
        make_session("a", "2026-06-11", [("t", "09:00", "10:00")]),
        make_session("b", "2026-06-12", [("t", "09:00", "11:00")]),
        make_session("c", "2026-06-11", [("t", "14:00", "15:00")]),
    ]
    totals = daily_totals(sessions)
    assert [t["date"] for t in totals] == ["2026-06-12", "2026-06-11"]
    assert totals[1]["hours"] == 2
    assert totals[0]["day"] == "Friday"


def test_weekly_summary_groups_by_monday():
    sessions = [
        make_session("a", "2026-06-08", [("t", "09:00", "10:00")]),
        make_session("b", "2026-06-12", [("t", "09:00", "10:00")]),
        make_session("c", "2026-06-05", [("t", "09:00", "10:00")]),  # week of Jun 1
        make_session("d", "2026-06-14", [("t", "09:00", "10:00")]),  # Sunday dropped
    ]
    summary = weekly_summary(sessions)
    assert summary == [
        {"weekStart": "2026-06-08", "hours": 2},
        {"weekStart": "2026-06-01", "hours": 1},
    ]
