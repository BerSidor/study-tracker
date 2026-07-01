import pytest

from duration import MIDNIGHT_WRAP_THRESHOLD_MIN, DurationError, active_minutes


# ── normal intervals ─────────────────────────────────────────────────────────────

def test_simple_interval():
    assert active_minutes("09:00", "10:30") == 90


def test_equal_times_is_zero():
    assert active_minutes("14:57", "14:57") == 0


# ── midnight crossing (reversal > 12h) ───────────────────────────────────────────

def test_midnight_crossing_short_gap():
    # 23:50 → 00:10 is a 20-minute gap across midnight, not a typo
    assert active_minutes("23:50", "00:10") == 20


def test_midnight_crossing_two_hours():
    assert active_minutes("23:00", "01:00") == 120


# ── implausible reversal (≤ 12h) is rejected ─────────────────────────────────────

def test_small_reversal_raises():
    # 14:57 → 14:37 is a 20-minute reversal — a typo, not a midnight crossing
    with pytest.raises(DurationError):
        active_minutes("14:57", "14:37")


def test_reversal_just_under_threshold_raises():
    # exactly 12h reversal (720 min) is NOT > threshold, so it is rejected
    assert MIDNIGHT_WRAP_THRESHOLD_MIN == 720
    with pytest.raises(DurationError):
        active_minutes("12:00", "00:00")


def test_reversal_just_over_threshold_wraps():
    # 12:01 → 00:00 is a 721-min reversal (> 720), so it wraps: 1440 - 721 = 719 min elapsed
    assert active_minutes("12:01", "00:00") == 719
