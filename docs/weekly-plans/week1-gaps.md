# Week 1 — Observer Notes

## 2026-06-11 (Day 2 — Tool Use & Permissions Model)
- Didn't know why Read is preferred over Bash — needed blast-radius principle explained
- Described the deny tier as a "not-permitted section" — three-tier model (deny/allow/prompt) needed correction
- On wildcard case study: attributed fix to correcting the path name, missing that eliminating the `cd &&` compound was the key structural change

## 2026-06-11 (Day 3 — CLAUDE.md & Project Context)
- Stated a 200-word limit for CLAUDE.md — no standard word limit exists; constraint is about keeping it purposeful, not a specific count
- Described CLAUDE.md hierarchy as "preference/override" — actually cumulative; all applicable files (global + project + subdirectory) are loaded simultaneously
- Said Claude can write both CLAUDE.md and memory files — CLAUDE.md is human-authored and committed to the repo; memory files are Claude-maintained and live outside the repo in ~/.claude/
