# AI Browser MCP Server — Open Source Announcement

> Copy for GitHub, forums, Twitter/X, Reddit, Dev.to.  
> Repository: https://github.com/AI-XiaoDao/ai-browser-mcp

---

## Short post (copy & paste)

```
[Open Source] AI Browser MCP Server v2.6.0 — Local browser automation for Windows

217 MCP tools for Cursor / Claude: navigate, fill forms, read DOM, network, workflows, CDP debugger.

✅ Open: Volcano .wsv source + generated C++ reference + docs (MIT)
✅ Binary: GitHub Releases (~157MB, exe + CEF runtime)
✅ Local-only: 127.0.0.1:9222 by default

Download: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
  · AI-Browser-MCP-x64-v2.6.0.zip      — runtime
  · AI-Browser-MCP-cpp-x64-v2.6.0.zip  — generated C++ (optional)

Star welcome: https://github.com/AI-XiaoDao/ai-browser-mcp
```

---

## One-liner

**AI Browser MCP Server** is a **Windows-native local MCP service** built with Volcano IDE + FBrowser CEF. Run the exe, connect Cursor via `mcp_bridge.js`, and drive a real browser with **217** `browser_*` tools.

---

## Highlights

| Feature | Details |
|---------|---------|
| **217 MCP tools** | `browser_navigate`, `browser_fill_click`, `browser_network`, `workflow_run`, … |
| **Dual JSON-RPC** | WebSocket + HTTP POST `http://127.0.0.1:9222/mcp` |
| **sync-wait** | Block until DOM / title / JS result — easier agent orchestration |
| **Workflows** | JSON step chains in `workflows/` |
| **Welcome console** | `http://127.0.0.1:9222/` — health, Cursor config, docs |
| **VIP (optional)** | Screenshot, CDP, fingerprint, resource intercept |

> Four GUI window tools (`browser_create`, `browser_close`, `browser_create_background`, `browser_create_tab`) are **disabled** in embedded GUI mode — the main window manages the browser instance.

---

## Quick start

1. Download [AI-Browser-MCP-x64-v2.6.0.zip](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v2.6.0/AI-Browser-MCP-x64-v2.6.0.zip) (~157MB)
2. Extract and run **AI浏览器.exe**
3. Open http://127.0.0.1:9222/health → `"status":"ok"`
4. Configure Cursor:

```json
{
  "mcpServers": {
    "ai-browser": {
      "command": "node",
      "args": ["path/to/mcp_bridge.js"],
      "env": {
        "AI_BROWSER_MCP_HTTP_POST": "http://127.0.0.1:9222/mcp"
      }
    }
  }
}
```

5. Self-check: `node mcp_bridge.js --check`

**Requirements**: Windows 10/11 x64 · Node.js 18+ (for Cursor bridge) · CEF runtime included in zip

---

## What's in the repo?

| Included | Path |
|----------|------|
| **Authoritative source** | `CEFbro/AI浏览器/src/*.wsv` (11 files) |
| **Generated C++ reference** | `CEFbro/AI浏览器/generated-cpp/release-x64/` |
| Docs & 217-tool reference | `docs/`, `skills/AI浏览器MCP.md` |
| Bridge & tests | `mcp_bridge.js`, `run_all_tests.js` |
| License | MIT |

| Not in Git | Get from |
|------------|----------|
| exe + CEF binaries | GitHub Releases |
| FBrowser CEF libs | Volcano IDE install |
| `linker/out/` (.obj/.pch) | **Not source** — never ship in releases |

**Develop against `.wsv`, not generated C++.**

---

## Links

- **Repo**: https://github.com/AI-XiaoDao/ai-browser-mcp
- **Release v2.6.0**: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
- **Chinese announcement**: [OPEN_SOURCE.md](OPEN_SOURCE.md)

---

*AI Browser MCP Server v2.6.0 · MIT · FBrowser CEF · port 9222*
