# 8-Week Claude Code Mastery → Startup Thesis (Summer 2026)

> **Goal:** By end of summer, (1) master Claude Code deeply, and (2) exit with a *validated
> startup thesis* — a committed, researched idea ready to execute in Fall.
>
> **Strategy:** Build-first. Freelance gigs double as market research. The niche emerges from
> real observed pain, not desk-guessing.

---

## How to use this plan

- Run **~40 h/week** (the tracker goal). ~130 h is structured study; the rest is building,
  gigs, and slack — intentional.
- Every week ends with a **shipped artifact**, not just notes.
- Log every study block with the tracker: `python cli.py start "<topic>"` → `done`.
- Keep the **Discovery Log** (`../data/discovery-log.md`) open at all times. It's the most
  important artifact you produce this summer.
- **Use Claude Code to build everything** — that's how you master it.

### Non-negotiables (if time slips, protect these)
1. MCP mastery + **1 published, documented MCP server**.
2. **1 deployed, end-to-end AI web app**.
3. Discovery Log → **validated startup thesis**.

---

## Phase A — Master the Tool (Weeks 1–3)

### Week 1 — Claude Code Core & Configuration
**Learn:** CLI basics; `settings.json` vs `settings.local.json`; the permissions model (study
the wildcard-permission fix in *this* repo as a real case study); `CLAUDE.md` & project
context; the hooks system (read + extend the existing `toast-session-saved.ps1` PostToolUse
hook).
**Ship:** a fresh project with a tailored `CLAUDE.md` + one custom hook you wrote yourself.
**Tracker topics:** `CLI basics & configuration`, `CLAUDE.md & project context`,
`Tool use & permissions model`, `Hooks system`.

### Week 2 — MCP Servers Deep Dive *(the core money skill)*
**Learn:** beyond fundamentals — tool JSON schema, Pydantic `Field`/validation, error handling,
stdio vs HTTP transports, auth, deployment. Build three servers: (a) notes/filesystem,
(b) one wrapping a real third-party API, (c) one over a database.
**Ship:** one polished, documented MCP server on GitHub → **portfolio piece #1** (directly sellable).
**Tracker topics:** `MCP servers`, `MCP server (published)`.

### Week 3 — Agents, Subagents, Skills & Plugins
**Learn:** subagents & multi-agent workflows; building skills/slash commands; plugins & the
marketplace; the **Agent SDK** (headless Claude Code → the basis for automation *products*).
**Ship:** a custom slash command + a small multi-agent workflow → **portfolio piece #2**.
**Tracker topics:** `Subagents & multi-agent workflows`, `Skills, plugins & slash commands`,
`Agent SDK (headless automation)`, `Multi-agent workflow`.

---

## Phase B — Foundations for Builders (Weeks 4–5)

### Week 4 — AI/ML for Builders + Software Architecture
**Learn:** prompt engineering; RAG (build a small one); agent architectures; LLM evaluation
basics. **Internalize design patterns here** (your stated goal): map classic patterns → AI
system design. Anthropic API depth: tool use, prompt caching, streaming, and **token economics
= your future startup's margin**.
**Ship:** a small RAG-backed tool + notes linking design patterns to AI architecture.
**Tracker topics:** `Prompt engineering`, `RAG systems`, `Agent architectures`,
`LLM evaluation basics`, `AI system design patterns`, `Anthropic API & cost economics`,
`RAG tool`.

### Week 5 — End-to-End Product Build *(capstone — fills your biggest gap)*
**Learn:** ship a real full-stack app — backend API, simple frontend, auth, database, and
actual **deployment**. Build it *with* Claude Code (meta-practice).
**Ship:** one deployed, real AI-powered web app → **portfolio piece #3** ("I can actually ship").
**Tracker topics:** `Building a project end-to-end`, `Deployed end-to-end app`.

---

## Phase C — Earn & Discover (Weeks 4–7, parallel)

Runs *alongside* Phases B & D — this is the freelance-first engine.

- **Week 4 — set up shop:** freelance profile + portfolio (use Wks 1–3 artifacts). Hunt where
  the work is: Upwork/Contra, indie-hacker & AI communities, local businesses, your university
  network.
- **Weeks 5–7 — deliver gigs:** land & deliver 1–3 small jobs. **Free pilots count** — they are
  research. Good first gigs: build an MCP server for someone's tool, automate a repetitive
  workflow, ship a tiny AI tool for a real person/business.
- **The Discovery Log:** after *every* gig and every painful integration, log it. "This should
  be easier." Recurring requests. Underserved workflows. → `../data/discovery-log.md`.

**Tracker topics:** `Freelance setup`, `Client gigs & delivery`, `Discovery log upkeep`.

---

## Phase D — Synthesize the Niche (Weeks 6–8)

### Week 6 — Market & Competitor Analysis
Pull 3–5 candidate niches from the Discovery Log. For each: who's the customer, what's the
pain, who else solves it, where's the gap? Sketch how each would make money.
**Tracker topics:** `AI product research & trends`, `Competitor & market analysis`,
`Business model basics`.

### Week 7 — Validation
Talk to real potential customers (your gig clients are warm leads). Scope an MVP with Claude
Code. Narrow to one thesis.
**Tracker topics:** `Customer conversations`, `MVP scoping with Claude Code`.

### Week 8 — Startup Thesis + Fall Launch Plan
**Ship:** a one-page thesis — problem, customer, solution, why-Claude-Code, why-now, business
model, defensibility — plus an MVP scope and a Fall roadmap (what to build first, path to first
5 customers). **This is the summer goal achieved.**
**Tracker topics:** `Startup thesis & MVP scope`.

---

## Where the money comes from (reference)

| Path | What you sell | When |
|---|---|---|
| Freelance MCP builds | Connecting a client's internal tools/APIs/DB to Claude | Now (Wks 5–7) |
| Automation gigs | Headless Claude Code pipelines that save recurring human time | Now (Wks 5–7) |
| Setup & training | Configuring hooks, MCPs, `CLAUDE.md` for teams | Now / Fall |
| **The startup** | A product built on the niche the gigs reveal | Fall onward |

The through-line: don't just *use* Claude Code — **integrate it into systems other people
depend on**. MCPs + the Agent SDK are where that value (and money) lives.
