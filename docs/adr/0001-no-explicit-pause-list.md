# ADR-0001: No explicit pause list on Session

## Status
Accepted

## Context
Early versions stored a `session.pauses[]` array recording each pause's startTime and endTime. Segment `activeMinutes` was calculated by subtracting overlapping pause time from the segment's wall-clock duration.

## Decision
Remove `session.pauses[]` entirely. A Pause is now implicit — it is the gap between the `endTime` of one Segment and the `startTime` of the next. Segments close when a pause begins and open when the user resumes, making every Segment pause-free by construction.

## Consequences
- Session active time = sum of all segment durations. No further arithmetic needed.
- Pause timestamps are still derivable by diffing consecutive segment boundaries.
- The data model is simpler: no `pauses[]`, no `activeMinutes`, no `durationHrs` on segments.
- Trade-off: pause metadata (reason, notes) cannot be attached to a pause without adding a separate structure. Accepted — pause analytics are not a goal.
