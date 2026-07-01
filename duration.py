"""The Duration rule — the single source of truth for "how long between two clock times".

A study timeline may cross midnight exactly once (CONTEXT.md: a Session belongs to its
start date and may run past midnight). So when an end time reads *earlier* than its start
time, it is one of two things:

  * a genuine midnight crossing  (e.g. 23:50 → 00:10), or
  * an implausible / mistyped time (e.g. 14:57 → 14:37).

We tell them apart by the size of the reversal: a reversal *larger* than 12 hours is a real
midnight crossing and wraps by +24h; a reversal of 12 hours or less cannot plausibly be a
single study segment, so it is rejected.

This validity policy lives HERE, beside the arithmetic, on purpose. Previously the guard
lived in session.py while the computation (a blind "+24h on any reversal") lived in
sync_payload.py — so any caller that reached for the computation alone could turn a typo
into a ~24h block. Co-locating the rule means no caller can compute a duration without the
guard.
"""

MIDNIGHT_WRAP_THRESHOLD_MIN = 12 * 60  # reversal beyond this = crossed midnight, not a typo


class DurationError(Exception):
    """Raised when two clock times cannot form a valid (pause-free) segment."""


def _to_minutes(clock: str) -> int:
    h, m = map(int, clock.split(":"))
    return h * 60 + m


def active_minutes(start: str, end: str) -> int:
    """Active minutes between two ``HH:MM`` clock times.

    Wraps a >12h reversal as a midnight crossing; raises ``DurationError`` on a smaller
    reversal (an implausible / mistyped pair). Equal times return 0.
    """
    start_mins = _to_minutes(start)
    end_mins = _to_minutes(end)
    if end_mins < start_mins:
        if start_mins - end_mins > MIDNIGHT_WRAP_THRESHOLD_MIN:
            end_mins += 24 * 60  # crossed midnight
        else:
            raise DurationError(
                f"End time {end} is before start {start} by less than 12h — "
                f"implausible for a single segment."
            )
    return end_mins - start_mins
