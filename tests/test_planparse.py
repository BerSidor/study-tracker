import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "web"))

from planparse import find_active, parse_week

WEEK_MD = """# Week 1 — Day-by-Day: Claude Code Core & Configuration

> **Week goal:** total fluency with the tool itself.

---

## Day 1 (Mon) — CLI Basics & Configuration `~6h` ✅
**Tracker:** `start "CLI basics & configuration"`

- **Learn (3h):** how Claude Code works as an *agentic* assistant. Plan mode,
  auto mode, effort levels, context window.
- **Ship today:** a short notes file.

## Day 2 (Tue) — Hooks System `~7.5h`
**Tracker:** `start "Hooks system"` (wrap) / `start "MCP servers"`

- **Learn (4h):** hook types.
- A plain bullet without a bold label.

## Observer Notes

See the gap log.

## Week 1 Definition of Done
- [x] Fresh project exists
- [ ] One custom hook wired in
"""


def test_week_title_and_day_count():
    week = parse_week(WEEK_MD, 1)
    assert week["title"].startswith("Week 1 — Day-by-Day")
    assert [d["n"] for d in week["days"]] == [1, 2]


def test_done_marker_tolerates_trailing_space():
    week = parse_week(WEEK_MD, 1)
    assert week["days"][0]["done"] is True
    assert week["days"][1]["done"] is False


def test_title_cleaned_of_est_and_check():
    day = parse_week(WEEK_MD, 1)["days"][0]
    assert day["title"] == "CLI Basics & Configuration"
    assert day["estHrs"] == 6


def test_fractional_estimate():
    assert parse_week(WEEK_MD, 1)["days"][1]["estHrs"] == 7.5


def test_tracker_topics_extracted():
    days = parse_week(WEEK_MD, 1)["days"]
    assert days[0]["trackerTopics"] == ["CLI basics & configuration"]
    assert days[1]["trackerTopics"] == ["Hooks system", "MCP servers"]


def test_bullet_labels_and_continuation():
    bullets = parse_week(WEEK_MD, 1)["days"][0]["bullets"]
    assert bullets[0]["label"] == "Learn (3h)"
    assert "context window." in bullets[0]["text"]  # continuation line merged
    assert bullets[1]["label"] == "Ship today"


def test_plain_bullet_has_no_label():
    bullets = parse_week(WEEK_MD, 1)["days"][1]["bullets"]
    assert bullets[-1] == {"label": None, "text": "A plain bullet without a bold label."}


def test_definition_of_done():
    week = parse_week(WEEK_MD, 1)
    assert week["dod"] == [
        {"text": "Fresh project exists", "checked": True},
        {"text": "One custom hook wired in", "checked": False},
    ]


def test_find_active_picks_first_unmarked_day():
    week1 = parse_week(WEEK_MD, 1)
    active = find_active([week1])
    assert active["week"] == 1
    assert active["day"]["n"] == 2


def test_find_active_skips_finished_weeks():
    week1 = parse_week(WEEK_MD.replace("`~7.5h`", "`~7.5h` ✅"), 1)
    week2 = parse_week(WEEK_MD.replace("Week 1", "Week 2"), 2)
    active = find_active([week1, week2])
    assert active["week"] == 2


def test_find_active_none_when_all_done():
    week1 = parse_week(WEEK_MD.replace("`~7.5h`", "`~7.5h` ✅"), 1)
    assert find_active([week1]) is None
