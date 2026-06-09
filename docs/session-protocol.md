# Session Protocol — Details & Examples

## Mid-session topic switching

You can switch topics freely mid-session. Each switch creates a new segment.

Example flow:
```
"start Claude Code hooks"          → segment 1 begins
"switching to MCP servers"         → segment 1 closes, segment 2 begins
"now doing AI product research"    → segment 2 closes, segment 3 begins
"done"                             → segment 3 closes, session saved
```
