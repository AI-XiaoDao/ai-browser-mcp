# AI Browser MCP — Quick Start (English)

> **Windows local browser automation MCP server** — 334 tools for Cursor, Claude Desktop, Cline, or any MCP client.  
> Repository: https://github.com/AI-XiaoDao/ai-browser-mcp

## What is this?

**AI Browser MCP Server** (AI浏览器 MCP) exposes a real **FBrowser CEF** browser on Windows via the **Model Context Protocol (MCP)**. Instead of writing **Playwright** or **Puppeteer** scripts, your AI agent calls **334 ready-made `browser_*` tools** over HTTP, WebSocket, or stdio.

**One instruction → auto-run:** web scraping · reverse POST fields · locate sign algorithms with the CDP debugger · form automation.

## Download

| Package | Platform | Size |
|---------|----------|------|
| [AI-Browser-MCP-x64-v3.2.0.zip](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v3.2.0/AI-Browser-MCP-x64-v3.2.0.zip) | Windows 64-bit | ~160 MB |
| [AI-Browser-MCP-win32-v3.2.0.zip](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v3.2.0/AI-Browser-MCP-win32-v3.2.0.zip) | Windows 32-bit | ~140 MB |

All **334 tools** included (screenshot, CDP, debugger, fingerprint, network hook, workflows). **MIT** open source.

## 3-step setup

1. Extract zip → run **`AI-Fbowser-Mcp.exe`**
2. Open http://127.0.0.1:9222/health → `"status":"ok"`
3. Connect your AI agent (see below)

## Cursor / Claude Desktop (stdio MCP)

```json
{
  "mcpServers": {
    "ai-browser": {
      "command": "node",
      "args": ["D:/path/to/mcp_bridge.js"],
      "env": {
        "AI_BROWSER_MCP_HTTP_POST": "http://127.0.0.1:9222/mcp"
      }
    }
  }
}
```

Self-check: `node mcp_bridge.js --check`

> Use the **stdio bridge** for Cursor — do not set `url: http://127.0.0.1:9222/mcp` directly. The bridge fixes protocol version and tool schema for Cursor.

## HTTP / WebSocket (any language)

- **HTTP POST:** `http://127.0.0.1:9222/mcp` (JSON-RPC)
- **WebSocket:** `ws://127.0.0.1:9222`
- **Health:** `http://127.0.0.1:9222/health`

## Example prompts (copy to Cursor)

```
Scroll the product list and scrape title + price into a JSON array.

Open https://example.com and scan XHR/fetch POST requests for suspected encrypted fields.

Set a breakpoint on form submit and locate the JS function that computes sign; show source snippet.

Log in with user test / pass 124356, go to order list, export first 20 rows as a table.
```

## vs Playwright / Puppeteer

| | Playwright DIY | AI Browser MCP |
|--|----------------|----------------|
| Setup | Node + drivers + scripts | Download exe, run |
| AI | Agent writes code each time | **334 MCP tools** pre-built |
| Reverse / debug | Manual Hook + DevTools | Built-in inject + **CDP debugger** |
| Privacy | Varies | **127.0.0.1 local only** |

## Docs

| Doc | Link |
|-----|------|
| Full README | [README.md](../README.md) |
| Tool reference | [index.html](./index.html) |
