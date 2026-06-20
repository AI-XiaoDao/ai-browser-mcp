# Forum Post Templates · AI Browser MCP Server v2.6

> **Use**: Copy-paste to Reddit, HN, Dev.to, Twitter/X, Discord, etc.  
> **Repo**: https://github.com/AI-XiaoDao/ai-browser-mcp  
> **Download**: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0  
> **Demo screenshot**: https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/.github/demo-douyin-post-scan.png  
> **Chinese forums**: [FORUM_POSTS.md](FORUM_POSTS.md) (V2EX, Zhihu, Juejin, etc.)

---

## 📑 Platform index

| Platform | Section | Format |
|----------|---------|--------|
| Twitter / X | [§1](#1-twitter--x) | Tweet / thread |
| Reddit | [§2](#2-reddit) | Post |
| Hacker News | [§3](#3-hacker-news) | Show HN |
| Dev.to | [§4](#4-devto) | Article |
| Discord | [§5](#5-discord) | Announcement |
| LinkedIn | [§6](#6-linkedin) | Post |
| Product Hunt | [§7](#7-product-hunt) | Launch blurb |
| Lobsters | [§8](#8-lobsters) | Link post |
| Mastodon | [§9](#9-mastodon) | Toot |
| Telegram | [§10](#10-telegram) | Channel post |
| **Scenario cheat sheet** | [§11](#11-scenario-cheat-sheet) | Pin / signature |
| **Comment FAQ** | [§12](#12-comment-faq) | Replies |

Full announcement: [OPEN_SOURCE_EN.md](OPEN_SOURCE_EN.md) · README: [README.md](README.md)

---

## Universal footer (append to any post)

```
Project: AI Browser MCP Server v2.6.0
License: MIT
Platform: Windows 10/11 x64
Stack: Volcano IDE + FBrowser CEF + MCP JSON-RPC (127.0.0.1:9222)
Tools: 217 browser_* — navigate, fill forms, DOM, network, workflows, CDP, Hook
Clients: Cursor · Claude Desktop · Cline · any MCP client · raw HTTP POST

Release: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
  AI-Browser-MCP-x64-v2.6.0.zip (~157MB, all 217 tools, download and go)

Repo: https://github.com/AI-XiaoDao/ai-browser-mcp
Stars / Issues / PRs welcome
```

---

## 1. Twitter / X

**Single tweet**:

```
[Open Source] AI Browser MCP v2.6 — 217 local browser tools for ANY MCP agent on Windows

One sentence → auto-runs:
· Scrape data
· Reverse POST crypto fields (Hook)
· CDP breakpoints → sign function source

Real FBrowser CEF · 127.0.0.1:9222 · MIT

https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
```

**Thread (optional follow-ups)**:

```
1/ Not Cursor-only — Claude Desktop, Cline, OpenCode, or POST to http://127.0.0.1:9222/mcp

2/ Demo: "Open douyin.com, scan XHR POST, flag encrypted fields" — Agent chains inject + network + analysis automatically.

3/ MIT source: .wsv modules + generated C++ + docs + test scripts. Star welcome ⭐
```

---

## 2. Reddit

**Subreddits**: r/cursor · r/ClaudeAI · r/LocalLLaMA · r/mcp · r/selfhosted · r/automation

**Title**: `[Release] AI Browser MCP Server v2.6 — local Windows browser automation (217 MCP tools, any agent)`

```
I open-sourced a Windows-native MCP server that wraps a real FBrowser CEF browser with 217 browser_* tools.

Works with Cursor, Claude Desktop, Cline, or any MCP client — plus raw HTTP POST to 127.0.0.1:9222/mcp.

Instead of writing Playwright scripts, describe the goal in plain language:

- "Scroll this product list and collect title/price as JSON"
- "Scan XHR/fetch POST and flag encrypted-looking fields"
- "Break on submit and show the JS function that computes sign"
- "Log in and export the first 20 rows of the order table"

Features:
· sync-wait + batch (fewer agent round-trips)
· workflow JSON for repeatable multi-step tasks
· persist Hook for POST bodies (network layer doesn't log bodies by default)
· CDP debugger: breakpoints, stack, script source

Runs locally on 127.0.0.1:9222. MIT license. Release zip includes all 217 tools.

Download: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
Repo: https://github.com/AI-XiaoDao/ai-browser-mcp

Demo screenshot in README (Douyin POST scan, one prompt). Happy to answer in comments.
```

**Shorter comment version** (when someone asks for local browser MCP):

```
Check out AI Browser MCP — 217 pre-built tools, Windows local, FBrowser CEF, MIT.
Any MCP agent, not just Cursor. Release has everything included.

https://github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 3. Hacker News

**Title**: `Show HN: AI Browser MCP – 217 local browser tools for MCP agents on Windows`

```
Hi HN,

I built an open-source MCP server (MIT) that exposes 217 browser automation tools on Windows using FBrowser CEF (Chromium-based embedded browser).

Any MCP-compatible agent can drive a real browser via HTTP/WebSocket on 127.0.0.1:9222 — Cursor, Claude Desktop, Cline, or your own app.

Typical one-liner prompts:
- Scrape lazy-loaded lists to JSON
- Hook XHR/fetch to analyze POST bodies for crypto-looking fields
- CDP breakpoints to locate sign/hash functions in page JS
- Fill forms + save flows as workflow JSON

Why not Playwright in the agent? The tools are pre-packaged with sync-wait, batch, and semantic failure detection so the agent doesn't rewrite boilerplate each time.

Source (.wsv + generated C++ reference) and docs on GitHub. Binary release ~157MB, all tools included.

https://github.com/AI-XiaoDao/ai-browser-mcp
https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0

Windows only for now. Feedback welcome.
```

---

## 4. Dev.to

**Title**: `Open-sourcing AI Browser MCP: 217 tools for local browser automation with any MCP agent`

**Tags**: `mcp`, `cursor`, `opensource`, `automation`, `windows`, `ai`

```
## TL;DR

Local Windows MCP server + real FBrowser CEF browser + 217 pre-built `browser_*` tools.
Tell your agent what you want — it chains navigate / inject / network / debugger for you.

## The problem

Every agent workflow reimplements Playwright wrappers: wait for DOM, scroll lazy lists, hook fetch, set breakpoints…

## What this project does

Packages common browser operations as MCP tools with:
- **sync-wait** — read DOM/title/JS in the same call
- **batch** — multiple tools in one request
- **workflows** — JSON step chains in `workflows/`
- **Hook + CDP** — reverse engineering helpers built in

## Quick start

1. Download [AI-Browser-MCP-x64-v2.6.0.zip](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0) (~157MB)
2. Run **AI浏览器.exe**
3. Check http://127.0.0.1:9222/health → `"status":"ok"`
4. Point `mcp_bridge.js` at Cursor or POST JSON-RPC to `/mcp`

Try: *"Scroll this list and collect title and price as JSON."*

## Open source

MIT — 11 Volcano `.wsv` modules (~20k lines), generated C++ reference, 217-tool docs, `run_all_tests.js`.

Repo: https://github.com/AI-XiaoDao/ai-browser-mcp

⭐ Stars help — issues and PRs welcome.
```

---

## 5. Discord

**#announcements / #showcase**:

```
📢 **AI Browser MCP Server v2.6 is open source (MIT)**

Windows local browser automation for **any MCP agent** — 217 tools, FBrowser CEF, port 9222.

**One-liner scenarios:**
• Scrape → JSON
• Hook POST bodies → flag crypto fields
• CDP breakpoint → sign function source
• Login + export table → workflow JSON

**Not Cursor-only** — Claude Desktop, Cline, HTTP POST all work.

🔗 Repo: https://github.com/AI-XiaoDao/ai-browser-mcp
⬇ Release: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0

Questions → GitHub Issues
```

---

## 6. LinkedIn

```
Excited to open-source **AI Browser MCP Server v2.6** (MIT) 🚀

A Windows-native MCP service that lets any AI agent (Cursor, Claude Desktop, custom MCP clients) drive a real browser with **217 pre-built tools** — no Playwright scripting from scratch.

One sentence in your agent:
→ "Scroll this page and collect product data as JSON"
→ "Scan POST requests and flag encrypted-looking fields"
→ "Break on form submit and show the sign function source"

Local-first (127.0.0.1:9222). Full tool set in the free release zip.

GitHub: https://github.com/AI-XiaoDao/ai-browser-mcp

#MCP #OpenSource #AIAgents #BrowserAutomation #Windows
```

---

## 7. Product Hunt

**Tagline**: Local browser automation for any MCP AI agent — 217 tools, one sentence.

**Description**:

```
AI Browser MCP Server runs a real FBrowser CEF browser on Windows and exposes 217 MCP tools over JSON-RPC.

Instead of writing Playwright code, describe your goal in natural language. Your agent chains navigation, DOM queries, network hooks, and CDP breakpoints automatically.

Great for: data scraping, web RPA, POST analysis, locating client-side crypto/sign logic.

· MIT open source
· All 217 tools in the release download
· Cursor, Claude, Cline, or HTTP API
· Local-only by default (127.0.0.1:9222)

https://github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 8. Lobsters

**Title**: `AI Browser MCP – 217 local browser tools for MCP agents (Windows, MIT)`

```
Windows MCP server wrapping FBrowser CEF with 217 browser_* tools. Any MCP agent or HTTP client on localhost:9222.

Useful if you're tired of rewriting Playwright glue for Cursor/Claude workflows: scrape, Hook POST bodies, CDP breakpoints for sign functions, workflow JSON.

MIT, source + ~157MB release with all tools included.

https://github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 9. Mastodon

```
[Open Source] AI Browser MCP v2.6

217 local browser tools for any MCP agent on Windows
Scrape · reverse POST fields · CDP breakpoints
FBrowser CEF · MIT · 127.0.0.1:9222

https://github.com/AI-XiaoDao/ai-browser-mcp

#MCP #OpenSource #Cursor #BrowserAutomation
```

---

## 10. Telegram

```
🚀 AI Browser MCP Server v2.6 — Open Source (MIT)

217 browser tools for Cursor / Claude / any MCP agent on Windows
One sentence: scrape data · reverse POST · locate sign via CDP

Local 127.0.0.1:9222 · Download and go

📦 Release: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
📂 Repo: https://github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 11. Scenario cheat sheet

```
AI Browser MCP · One-sentence scenarios v2.6

① Scrape   "Scroll list, collect title/price as JSON"     → dom_query / collect
② Reverse  "Scan POST, flag likely encrypted fields"      → inject Hook + network
③ Locate   "Break on submit, show sign function source"   → debugger_*
④ Fill     "Log in and export order table"                → fill_* / workflow
⑤ Reuse    "Save as workflow JSON, run next time"        → workflow_*

Setup: exe + mcp_bridge.js → 127.0.0.1:9222
Repo: github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 12. Comment FAQ

**Q: Playwright / Puppeteer?**  
A: 217 tools are pre-wrapped as MCP. Your agent calls tools directly instead of generating Node browser scripts. Real FBrowser CEF window, localhost:9222.

**Q: Cursor only?**  
A: No. Any MCP client or HTTP POST to `127.0.0.1:9222/mcp`.

**Q: Safe / exposed to internet?**  
A: Binds 127.0.0.1 by default. See `mcp_config.json`.

**Q: POST bodies?**  
A: Network tools don't log bodies by default. Use `browser_inject` persist Hook. See `scenarios/douyin_xhr_encrypt_scan.js`.

**Q: Mac / Linux?**  
A: Windows x64 only for now. CEF runtime bundled in release.

**Q: Cost?**  
A: MIT open source. Release zip includes all 217 tools, free download.

**Q: Getting started?**  
A: Download zip → run exe → health ok → configure bridge → one sentence to your agent. See README.

---

## Posting tips

| Platform | Tip |
|----------|-----|
| With image | Use demo URL from top of this file |
| Technical | Lead with Hook + CDP + MCP protocol |
| General | Lead with "download → configure → one sentence" |
| All | Ask for ⭐ / feedback; don't spam identical posts |

---

*AI Browser MCP Server v2.6.0 · MIT · [CHANGELOG.md](CHANGELOG.md)*
