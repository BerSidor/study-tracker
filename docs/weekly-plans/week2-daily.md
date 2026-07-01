# Week 2 — Day-by-Day: MCP Servers Deep Dive *(the core money skill)*

> **Week goal:** be able to build a production MCP server for any API or data source.
> **Ship by Saturday:** one polished, documented MCP server on GitHub — **portfolio piece #1**.
> **Study days:** Mon–Sat (Sunday rest). ~6.7 h/day. Log every block with the tracker.

This is the most directly sellable skill of the summer. Most companies have internal tools
Claude can't reach yet — an MCP server is the bridge. Build three this week; publish the best.

---

## Day 1 (Mon) — Protocol Deep Dive `~6h` ✅
**Tracker:** `start "MCP servers"`

- **Learn (3h):** how MCP actually works — JSON-RPC over stdio/HTTP, the client↔server
  handshake, tool/resource/prompt primitives. Why a *standard* protocol matters.
- **Practice (3h):** stand up the minimal `FastMCP` server from the Python SDK; register one
  trivial tool; connect it to Claude Code via `settings.json`; call it. Prove the loop works.

## Day 2 (Tue) — Tool Schemas, Validation & Errors `~7h` ✅
**Tracker:** `start "MCP servers"`

- **Learn (4h):** tool JSON schema in depth; Pydantic `Field` for descriptions/constraints;
  input validation; clean error handling so a bad call never crashes the server.
- **Practice (3h):** take your Day-1 tool and harden it — typed args, `Field` descriptions,
  bounds, graceful errors. Inspect the generated schema and confirm it reads well to Claude.

## Day 3 (Wed) — Server #1: Notes / Filesystem `~7h` ✅
**Tracker:** `start "MCP server (published)"`

- **Build (all day):** a server exposing tools to search/read/write a local notes folder
  (e.g. your `MCP Servers/` study notes). `search_notes`, `read_note`, `append_note`.
  Test each tool end-to-end through Claude Code.

## Day 4 (Thu) — Server #2: Wrap a Real Third-Party API `~7h` ✅
**Tracker:** `start "MCP server (published)"`

- **Build (all day):** pick a real API you use (weather, GitHub, a SaaS). Wrap 2–3 endpoints as
  tools. Handle auth (API keys via env), rate limits, and error responses. This is the exact
  shape of a paid client gig.

## Day 5 (Fri) — Server #3: Database-Backed + Transports `~7h` ✅
**Tracker:** `start "MCP server (published)"`

- **Build (4h):** a server over a small SQLite DB — query/insert tools with validated inputs.
- **Learn (3h):** stdio vs streamable-HTTP transports — when to use each, and how you'd deploy
  an HTTP server so a remote client can reach it.

## Day 6 (Sat) — Polish, Document & Publish `~6h` ✅
**Tracker:** `start "MCP server (published)"`

- **Ship:** pick your strongest of the three. Write a clean README (what it does, install,
  config snippet, tool list). Push to GitHub — **portfolio piece #1**.
- **Discovery Log:** note which integration was hardest and any "this should be easier" pains.
- **Run `report`.**

---

## Week 2 Definition of Done
- [x] Three working MCP servers built (notes, API-wrapper, database)
- [ ] One polished + documented + pushed to GitHub
- [x] You can explain tool schemas, `Field`, transports, and auth without notes
- [x] At least one Discovery Log entry from a hard integration
- [x] All study blocks logged
