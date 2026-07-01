# Week 3 — Day-by-Day: Agents, Subagents, Skills & Plugins

> **Week goal:** multi-agent orchestration + packaging reusable workflows.
> **Ship by Saturday:** a custom slash command + a small multi-agent workflow — **portfolio piece #2**.
> **Study days:** Mon–Sat (Sunday rest). ~6.7 h/day. Log every block with the tracker.

This is where Claude Code becomes _programmable_. Skills/plugins package your expertise; the
Agent SDK lets Claude run headless — the foundation of automation _products_ you can sell.

---

## Day 1 (Mon) — Subagents & the Agent Tool `~6h` ✅

**Tracker:** `start "Subagents & multi-agent workflows"`

- **Learn (3h):** what a subagent is, the built-in agent types (Explore, Plan, general-purpose),
  when delegating to one beats doing it inline, and how results flow back.
- **Practice (3h):** spawn an Explore agent and a Plan agent on a real question in this repo;
  observe how each is scoped and what it returns.

## Day 2 (Tue) — Multi-Agent Orchestration Patterns `~7h`

**Tracker:** `start "Subagents & multi-agent workflows"`

- **Learn (4h):** parallel vs sequential agents, fan-out/fan-in, how to brief an agent well
  (it starts cold), and failure modes (cost, context duplication).
- **Practice (3h):** design a 2–3 agent workflow on paper for a real task (e.g. "research +
  draft + review"). Define each agent's job and hand-offs.

## Day 3 (Wed) — Skills & Slash Commands `~6h`

**Tracker:** `start "Skills, plugins & slash commands"`

- **Learn (2h):** what a Skill is, how slash commands map to skills, and the structure of a
  skill definition.
- **Build (4h):** write your first custom slash command for a workflow you repeat (e.g.
  `/log-discovery` or `/new-mcp`). Test it.

## Day 4 (Thu) — Plugins & the Marketplace `~6h`

**Tracker:** `start "Skills, plugins & slash commands"`

- **Learn (3h):** how plugins bundle skills/hooks/MCP servers; the marketplace structure
  (browse `~/.claude/plugins/marketplaces/`). How distribution works.
- **Practice (3h):** sketch how you'd package your Week-2 MCP server + a skill as a plugin.

## Day 5 (Fri) — Agent SDK: Headless Claude Code `~7h`

**Tracker:** `start "Agent SDK (headless automation)"`

- **Learn (4h):** the Agent SDK — running Claude Code programmatically with no human in the
  loop. This is how you turn a workflow into a _product_ (a pipeline that runs on a schedule or
  on demand). Read the SDK docs; understand the basic invocation + tool-permission model.
- **Practice (3h):** run a minimal headless script that completes one task autonomously.

## Day 6 (Sat) — Build & Ship: Slash Command + Multi-Agent Workflow `~7h`

**Tracker:** `start "Multi-agent workflow"`

- **Ship:** finish a custom slash command + a small working multi-agent workflow (e.g. one
  agent gathers, another synthesizes). Document both — **portfolio piece #2**.
- **Discovery Log:** note any automation that felt valuable enough that someone would pay for it.
- **Run `report`.**

---

## Week 3 Definition of Done

- [ ] A custom slash command that works
- [ ] A small multi-agent workflow (2–3 agents) that runs end-to-end
- [ ] You ran Claude Code headless once via the Agent SDK
- [ ] You can explain skills vs plugins vs MCP servers and when to use each
- [ ] All study blocks logged; at least one Discovery Log entry
