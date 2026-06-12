"""Parse the week{N}-daily.md study plans.

Mirrors how the daily-quiz and learn skills read the plans: the active week is
the first week file with an unmarked day; the active day is its first day
heading without a trailing check mark.
"""
import re
from pathlib import Path

DAY_RE = re.compile(r"^##\s+Day\s+(\d+)\s+\((\w{3})\)\s+—\s+(.*)$")
EST_RE = re.compile(r"`~?([\d.]+)\s*h`")
DOD_RE = re.compile(r"^##\s+Week\s+(\d+)\s+Definition of Done\s*$")
CHECKBOX_RE = re.compile(r"^- \[([ xX])\]\s+(.*)$")
BULLET_RE = re.compile(r"^-\s+\*\*(.+?):\*\*\s*(.*)$")
TRACKER_TOPIC_RE = re.compile(r'start\s+"([^"]+)"')

DONE_MARK = "✅"


def _clean_title(raw_title: str) -> str:
    title = raw_title.replace(DONE_MARK, "")
    title = EST_RE.sub("", title)
    return title.strip()


def _parse_day(heading_match, lines) -> dict:
    n, day_name, raw_title = heading_match.groups()
    day = {
        "n": int(n),
        "dayName": day_name,
        "title": _clean_title(raw_title),
        "estHrs": None,
        "done": DONE_MARK in raw_title,
        "trackerTopics": [],
        "bullets": [],
    }
    est = EST_RE.search(raw_title)
    if est:
        day["estHrs"] = float(est.group(1))

    for line in lines:
        if line.startswith("**Tracker:**"):
            day["trackerTopics"].extend(TRACKER_TOPIC_RE.findall(line))
            continue
        bullet = BULLET_RE.match(line)
        if bullet:
            day["bullets"].append({"label": bullet.group(1), "text": bullet.group(2)})
        elif line.startswith("- "):
            day["bullets"].append({"label": None, "text": line[2:].strip()})
        elif line.startswith("  ") and day["bullets"]:
            day["bullets"][-1]["text"] += " " + line.strip()
    return day


def parse_week(text: str, week_num: int) -> dict:
    lines = text.splitlines()
    week = {"week": week_num, "title": "", "days": [], "dod": [], "raw": text}

    for line in lines:
        if line.startswith("# ") and not week["title"]:
            week["title"] = line[2:].strip()
            break

    # split into ## sections
    sections: list[tuple[str, list[str]]] = []
    current: "tuple[str, list[str]] | None" = None
    for line in lines:
        if line.startswith("## "):
            current = (line, [])
            sections.append(current)
        elif current is not None:
            current[1].append(line)

    for heading, body in sections:
        day_match = DAY_RE.match(heading)
        if day_match:
            week["days"].append(_parse_day(day_match, body))
            continue
        if DOD_RE.match(heading):
            for line in body:
                box = CHECKBOX_RE.match(line)
                if box:
                    week["dod"].append(
                        {"text": box.group(2), "checked": box.group(1) in "xX"}
                    )
    return week


def load_weeks(plans_dir) -> "list[dict]":
    weeks = []
    for n in range(1, 9):
        path = Path(plans_dir) / f"week{n}-daily.md"
        if path.exists():
            weeks.append(parse_week(path.read_text(encoding="utf-8"), n))
    return weeks


def find_active(weeks: "list[dict]") -> "dict | None":
    """First unmarked day in the first week that has one; None if all done."""
    for week in weeks:
        for day in week["days"]:
            if not day["done"]:
                return {"week": week["week"], "day": day}
    return None
