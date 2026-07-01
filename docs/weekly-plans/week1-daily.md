# Week 1 — Day-by-Day: Claude Code Core & Configuration

> **Week goal:** total fluency with the tool itself.
> **Ship by Saturday:** a fresh project with a tailored `CLAUDE.md` + one custom hook you wrote.
> **Study days:** Mon–Sat (Sunday rest). ~6.7 h/day. Log every block with the tracker.

Structured study ≈ 12 h; the rest is hands-on practice and building the ship artifact. That
ratio is intentional — you learn this tool by driving it, not reading about it.

---

## Day 1 (Mon) — CLI Basics & Configuration `~6h` ✅
**Tracker:** `start "CLI basics & configuration"`

- **Learn (3h):** how Claude Code works as an *agentic* assistant (not a chatbot). Plan mode,
  auto mode, effort levels, context window. Walk your own config: `~/.claude/settings.json`
  (global) vs project `.claude/settings.json` vs `settings.local.json` — what overrides what.
- **Practice (3h):** try the slash commands you haven't (`/context`, `/model`, `/memory`,
  `/skills`). Inspect your statusline script. Change one setting deliberately and observe the
  effect.
- **Ship today:** a short notes file "How Claude Code actually works" in your own words.

## Day 2 (Tue) — Tool Use & Permissions Model `~7h` ✅
**Tracker:** `start "Tool use & permissions model"`

- **Learn (4h):** the tools Claude has (read/write/edit/bash/search/web) and *when* it reaches
  for each. The permission model: `allow` patterns, wildcards, exact-match, how denials work.
- **Case study (live):** re-read the wildcard-permission fix we did in *this* repo — the
  `cd "..." && python cli.py *` patterns that never matched. Understand exactly *why* they
  failed and why the absolute-path wildcard fixed it. This is the single best teaching example
  you have.
- **Practice (3h):** write 3 permission rules from scratch in a scratch project; test that they
  auto-allow what you intend and prompt for what you don't.

## Day 3 (Wed) — CLAUDE.md & Project Context `~6h` ✅
**Tracker:** `start "CLAUDE.md & project context"`

- **Learn (2h):** what belongs in `CLAUDE.md`, how it's injected, global vs project vs memory.
  Read this repo's `study-tracker/CLAUDE.md` — note how the command table teaches Claude exactly
  how to operate the tracker.
- **Build (4h):** **start your fresh Week-1 project** (a small throwaway app/tool). Write its
  `CLAUDE.md` from scratch: project purpose, conventions, key commands, what to do/avoid.

## Day 4 (Thu) — Hooks System `~7h` ✅
**Tracker:** `start "Hooks system"`

- **Learn (3h):** hook types — PreToolUse, PostToolUse, Stop, etc. What event fires when, and
  what data the hook receives.
- **Read real code:** dissect this repo's `toast-session-saved.ps1` PostToolUse hook (fires on
  `Write` to log a toast). Trace it from `.claude/settings.json` → script → notification.
- **Practice (4h):** design your own hook on paper, then stub it. Decide its trigger and effect.

## Day 5 (Fri) — Build Your Custom Hook `~7h` ✅
**Tracker:** `start "Hooks system"` (continue)

- **Build (all day):** implement a custom hook for your fresh project. Ideas: a PostToolUse
  hook that logs edits to a file, a Stop hook that prints a session summary, or a PreToolUse
  hook that blocks edits to a protected path. Wire it into `.claude/settings.json` and test it
  end-to-end.

## Day 6 (Sat) — Ship, Review & Log `~6h` ✅
**Tracker:** `start "CLAUDE.md & project context"` (wrap) / `Hooks system`

- **Finish the ship artifact:** fresh project + tailored `CLAUDE.md` + working custom hook.
- **Review (2h):** can you explain, without notes, the permission model, what `CLAUDE.md` does,
  and the hook lifecycle? If not, that's next week's warm-up.
- **Discovery Log:** add any "this was harder than it should be" observations from the week.
- **Run `report`** to see Week-1 hours land in the sheet.

---

## Observer Notes

See [week1-gaps.md](week1-gaps.md) for session-by-session gap log.

## Week 1 Definition of Done
- [x] Fresh project exists with a real, tailored `CLAUDE.md`
- [x] One custom hook you wrote, wired in and firing correctly
- [x] You can explain the permissions model using the wildcard-fix case study
- [x] "How Claude Code works" notes written in your own words
- [x] All study blocks logged; at least one Discovery Log entry
