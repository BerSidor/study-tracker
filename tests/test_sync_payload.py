from sync_payload import build_sync_payload, fmt_hrs


def _session(segments, date="2026-01-15"):
    start = segments[0]["startTime"]
    end = segments[-1]["endTime"]
    return {
        "id": f"{date}-001",
        "date": date,
        "startTime": start,
        "endTime": end,
        "segments": segments,
    }


# ── build_sync_payload ─────────────────────────────────────────────────────────

def test_single_segment_duration():
    s = _session([{"topic": "MCP servers", "startTime": "09:00", "endTime": "10:00"}])
    p = build_sync_payload(s)
    assert abs(p["durationHrs"] - 1.0) < 1e-6
    assert abs(p["segments"][0]["durationHrs"] - 1.0) < 1e-6


def test_multiple_segments_total():
    s = _session([
        {"topic": "MCP servers",      "startTime": "09:00", "endTime": "10:30"},
        {"topic": "Claude Code hooks", "startTime": "10:30", "endTime": "12:00"},
    ])
    p = build_sync_payload(s)
    assert abs(p["durationHrs"] - 3.0) < 1e-6
    assert abs(p["segments"][0]["durationHrs"] - 1.5) < 1e-6
    assert abs(p["segments"][1]["durationHrs"] - 1.5) < 1e-6


def test_midnight_crossover():
    s = _session([{"topic": "Late study", "startTime": "23:00", "endTime": "01:00"}])
    p = build_sync_payload(s)
    assert abs(p["durationHrs"] - 2.0) < 1e-6


def test_day_field_derived_from_date():
    s = _session([{"topic": "X", "startTime": "09:00", "endTime": "10:00"}], date="2026-01-15")
    p = build_sync_payload(s)
    assert p["day"] == "Thursday"


def test_payload_fields_present():
    s = _session([{"topic": "X", "startTime": "09:00", "endTime": "10:00"}])
    p = build_sync_payload(s)
    assert set(p.keys()) == {"id", "date", "day", "startTime", "endTime", "durationHrs", "segments", "notes"}


def test_notes_defaults_to_empty_string():
    s = _session([{"topic": "X", "startTime": "09:00", "endTime": "10:00"}])
    p = build_sync_payload(s)
    assert p["notes"] == ""


def test_pause_gap_excluded_from_total():
    # Pause from 10:00–10:30 should not count toward durationHrs
    s = _session([
        {"topic": "MCP servers", "startTime": "09:00", "endTime": "10:00"},
        {"topic": "MCP servers", "startTime": "10:30", "endTime": "12:00"},
    ])
    p = build_sync_payload(s)
    assert abs(p["durationHrs"] - 2.5) < 1e-6   # 1h + 1.5h, not 3h


# ── fmt_hrs ────────────────────────────────────────────────────────────────────

def test_fmt_hrs_whole_hours():
    assert fmt_hrs(2.0) == "2h 00m"


def test_fmt_hrs_minutes_only():
    assert fmt_hrs(0.5) == "30m"


def test_fmt_hrs_mixed():
    assert fmt_hrs(1.75) == "1h 45m"
