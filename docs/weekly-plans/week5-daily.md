# Week 5 — Day-by-Day: End-to-End Product Build *(capstone — fills your biggest gap)*

> **Week goal:** ship a real, deployed full-stack AI app — and land your first gig.
> **Ship by Saturday:** one deployed AI-powered web app — **portfolio piece #3** ("I can ship").
> **Study days:** Mon–Sat (Sunday rest). ~6.7 h/day. Log every block with the tracker.

This is the week that closes your biggest gap: you've built one academic web app — now you ship
a real, *deployed* one, with Claude Code as your pair. Gigs start in parallel (Phase C).

---

## Day 1 (Mon) — Scope & Architect `~6h`
**Tracker:** `start "Deployed end-to-end app"`

- **Plan (3h):** pick a small but real AI app (e.g. a tool that summarizes/queries documents).
  Define the one core feature. Choose a lean stack you can deploy (e.g. FastAPI + a simple
  frontend + SQLite/Postgres + a host like Render/Fly/Vercel).
- **Architect (3h):** sketch data model, endpoints, and where the Claude API call lives. Apply a
  design pattern deliberately (Week-4 knowledge).

## Day 2 (Tue) — Backend API + Database `~7h`
**Tracker:** `start "Deployed end-to-end app"`

- **Build:** backend endpoints + persistence. Get CRUD working locally with tests. Build it
  *with* Claude Code — practice driving the tool on a real codebase.

## Day 3 (Wed) — Frontend + Auth `~7h`
**Tracker:** `start "Deployed end-to-end app"`

- **Build:** a minimal frontend that talks to your API, plus basic auth (even simple token/login).
  Function over polish.

## Day 4 (Thu) — The AI Feature `~7h`
**Tracker:** `start "Deployed end-to-end app"`

- **Build:** wire in the Claude-powered feature (the reason the app exists). Apply Week-4 cost
  awareness — cache where sensible, watch token usage.

## Day 5 (Fri) — Deploy + First Gig `~7h`
**Tracker:** `start "Deployed end-to-end app"` → `start "Client gigs & delivery"`

- **Deploy (4h):** get it live on a real URL. Env vars, secrets, build config — the unglamorous
  part that proves you can actually ship.
- **Gig (3h):** send outreach / accept a first small gig (free pilot is fine — it's research).

## Day 6 (Sat) — Polish, Deliver, Log `~6h`
**Tracker:** `start "Client gigs & delivery"`

- **Finish:** smooth rough edges; write a short README + demo note. **Portfolio piece #3** done.
- **Gig:** progress or deliver your first gig.
- **Discovery Log:** capture every friction point from building + the gig. **Run `report`.**

---

## Week 5 Definition of Done
- [ ] A real AI app deployed at a public URL
- [ ] Backend + frontend + auth + database + Claude feature all working
- [ ] First freelance gig started or delivered (paid or free pilot)
- [ ] Several Discovery Log entries from building + the gig
- [ ] All study blocks logged
