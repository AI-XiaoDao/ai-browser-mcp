# 🚀 AI Browser MCP Server

> **Windows local browser automation MCP server** — real FBrowser CEF (Chromium) engine · **265 browser automation tools** · local `127.0.0.1:9222` · MIT open source
>
> Web Scraping · JS Reverse Engineering · CDP Debugger · Kernel Extensions · Fingerprint Anti-Detection · Form Automation RPA

[![Release](https://img.shields.io/badge/release-v3.1.0-blue)](https://github.com/AI-XiaoDao/ai-browser-mcp/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows_x64_|_win32-lightgrey)](https://github.com/AI-XiaoDao/ai-browser-mcp/releases)
[![Stars](https://img.shields.io/github/stars/AI-XiaoDao/ai-browser-mcp?style=social)](https://github.com/AI-XiaoDao/ai-browser-mcp)

[**中文文档**](README.md) | English

---

## What is it?

**AI Browser MCP Server** is a **Windows local browser automation MCP server**: it embeds a real **FBrowser CEF (Chromium)** engine and exposes **265 browser automation tools** to any AI coding assistant (Cursor / Claude Code / Claude Desktop / Trae / Cline) over the standard **Model Context Protocol (MCP)**.

No Node driver, no Playwright/Puppeteer scripts — **download, extract, double-click, done**. AI controls the browser with natural language:

- 🕷️ **Web Scraping** — `browser_scrape` one-step crawler (navigate → wait → extract)
- 🔍 **JS Reverse Engineering** — function hooks / call stack tracing / algorithm identification / obfuscation detection
- 🐛 **CDP Debugger** — `debugger_flow` one-click breakpoint → evaluate → resume
- ⚙️ **Kernel Extensions** — custom scheme (`mcp://`), certificate handling, HTTP auth injection, download control, event reactor
- 🤖 **Form Automation RPA** — native CEF form-filling API (no JS injection)
- 🎭 **Fingerprint Anti-Detection** — 30+ dimensions (Canvas/WebGL/Audio/WebRTC/SSL/fonts/hardware)
- 📡 **Network Interception** — HTTP/WS capture, modify, replace, block
- 🔄 **Workflow Automation** — JSON step chains, batch execution

**Privacy**: 100% local `127.0.0.1:9222`, no data leaves your machine.

## Quick Start

### 1. Download

Download the latest release from the [Releases page](https://github.com/AI-XiaoDao/ai-browser-mcp/releases):

| Package | Description |
|---|---|
| `AI-Browser-MCP-x64-v3.1.0.zip` | 64-bit Windows (~160MB) |
| `AI-Browser-MCP-win32-v3.1.0.zip` | 32-bit Windows (~140MB) |
| `AI-Browser-MCP-cpp-*.zip` | Generated C++ sources (reference) |

### 2. Start

Extract → double-click **`AI-Fbowser-Mcp.exe`** → open `http://127.0.0.1:9222/health`, ready when you see `{"status":"ok"}`.

### 3. Connect an AI agent

**Native stdio mode (no Node.js required)** — Claude Code / Claude Desktop / Trae:

```json
{
  "mcpServers": {
    "ai-browser": {
      "command": "C:/your/path/AI-Fbowser-Mcp.exe",
      "args": ["--mcp-stdio"]
    }
  }
}
```

**Node bridge mode** — Cursor / Cline:

```json
{
  "mcpServers": {
    "ai-browser": {
      "command": "node",
      "args": ["D:/your/path/mcp_bridge.js"]
    }
  }
}
```

Self-check: `node mcp_bridge.js --check`

### 4. Protocol compliance

Verified against the official `@modelcontextprotocol/sdk@1.30.0`: connect / listTools (265) / ping / callTool / listResources / listPrompts all pass strict schema validation. stdio framing is adaptive (official newline-delimited JSON, Content-Length compatible).

## Endpoints

| Endpoint | Description |
|---|---|
| `POST http://127.0.0.1:9222/mcp` | HTTP JSON-RPC main channel |
| `ws://127.0.0.1:9222` | WebSocket JSON-RPC |
| `http://127.0.0.1:9222/` | Welcome page console |
| `http://127.0.0.1:9222/health` | Health check |
| `http://127.0.0.1:9222/tools/list` | Tool list |
| `http://127.0.0.1:9222/docs/` | Full documentation |

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — process model, transports, protocol compliance, request pipeline, sync-wait engine, event layer, source layout, build & release.

- **Language**: Volcano Windows (中文编程) — all source in `CEFbro/AI-Fbowser-Mcp/src/*.wsv`, MIT licensed
- **Runtime**: zero Node dependency (native stdio) with optional Node bridge

## Documentation

| Doc | Audience |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | Developers — process/transport/protocol/source layout |
| [Customer Manual](CEFbro/AI-Fbowser-Mcp/docs/客户使用手册.md) | End users — install/Cursor/FAQ (Chinese) |
| [Configuration Guide](CEFbro/AI-Fbowser-Mcp/docs/MCP工具配置说明书.md) | Deployment — all config fields (Chinese) |

## License

MIT — see [LICENSE](LICENSE). Source, docs and tools are fully open.

## Contact

- Repository: https://github.com/AI-XiaoDao/ai-browser-mcp
- QQ: 212577526 · QQ Group: 737680767
