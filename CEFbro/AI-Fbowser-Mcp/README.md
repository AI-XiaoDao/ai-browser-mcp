# AI浏览器 MCP Server

> **Windows 真实浏览器自动化 MCP 服务端** — FBrowser CEF 内核 · 234 工具 · 本地 `127.0.0.1:9222`

[![Release](https://img.shields.io/badge/release-v2.6.1-blue)](https://github.com/AI-XiaoDao/ai-browser-mcp/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64%20%7C%20win32-lightgrey)](https://github.com/AI-XiaoDao/ai-browser-mcp/releases)

---

## 这是什么？

**AI浏览器 MCP Server** 在 Windows 上运行一个真实的 **FBrowser CEF** 浏览器，通过 **Model Context Protocol (MCP)** 对外暴露 **234 个 `browser_*` 自动化工具**。

AI Agent (Cursor / Claude Desktop / Cline) 可直接调用这些工具完成：网页数据采集、JS 逆向 Hook、CDP 断点定位 sign 算法、自动填表 RPA、指纹伪装、网络抓包。

无需手写 Playwright / Puppeteer 脚本。

---

## 快速开始

### 1. 下载

| 包 | 说明 |
|----|------|
| [x64 v2.6.1](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v2.6.1/AI-Browser-MCP-x64-v2.6.1.zip) | 64 位 Windows, ~160MB |
| [win32 v2.6.1](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v2.6.1/AI-Browser-MCP-win32-v2.6.1.zip) | 32 位 Windows, ~140MB |

### 2. 启动

解压 → 双击 `AI-Fbowser-Mcp.exe` → 自动启动 MCP 服务  
打开 http://127.0.0.1:9222/health → `{"status":"ok"}`

### 3. 接入 AI Agent

**Cursor** (`mcp.json`):

```json
{
  "mcpServers": {
    "ai-browser": {
      "command": "node",
      "args": ["D:/你的路径/mcp_bridge.js"]
    }
  }
}
```

**Claude Desktop / Cline** 同配置，指向 `mcp_bridge.js`。

自检：`node mcp_bridge.js --check`

---

## 核心能力

| 类别 | 工具 | 说明 |
|------|------|------|
| **导航/内容** | `navigate`, `get_url`, `get_title`, `get_source`, `get_text` | 页面导航与内容获取 |
| **JS 执行** | `evaluate`, `execute_js`, `console_eval`, `inject` | JS 注入、执行、持久 Hook |
| **DOM 操作** | `dom_query`, `dom_click`, `dom_set_value`, `dom_get_html` | 原生填表框架，非 JS |
| **填表 RPA** | `fill_set_value`, `fill_click`, `fill_focus`, `fill_scroll` | FBrowser 原生填表 API |
| **自动化** | `wait`, `scrape`, `extract` | 等待条件、一步爬虫、数据提取 |
| **网络抓包** | `network`, `network_body`, `collect` | 请求/响应捕获、控制台日志 |
| **资源拦截** | `intercept` | 修改/替换/屏蔽资源、导航拦截 |
| **Cookie/代理** | `get_cookies`, `set_cookie`, `set_proxy` | Cookie 管理、代理设置 |
| **截图/PDF** | `screenshot`, `print_to_pdf` | VIP 截图、PDF 输出 |
| **CDP 协议** | `cdp_call`, `cdp_event` | Chrome DevTools Protocol 全能力 |
| **断点调试** | `debugger_flow`, `debugger_auto` | 一键断点→求值→resume 流程 |
| **JS 逆向** | `reverse_hook`, `reverse_strings`, `reverse_verify` | 函数 Hook/字符串提取/验证闭环 |
| **指纹伪装** | `fingerprint`, `fingerprint_ua` | 30+ 种浏览器指纹虚拟 |
| **工作流** | `workflow_list`, `workflow_run`, `workflow_stop` | JSON 工作流编排 |
| **批量** | `batch` | 最多 200 条命令批量执行 |

---

## 端点

| 端点 | 说明 |
|------|------|
| `ws://127.0.0.1:9222` | WebSocket — JSON-RPC 主通道 |
| `POST http://127.0.0.1:9222/mcp` | HTTP JSON-RPC |
| `http://127.0.0.1:9222/` | 欢迎页控制台 |
| `http://127.0.0.1:9222/health` | 健康检查 |
| `http://127.0.0.1:9222/tools/list` | 工具列表 |
| `http://127.0.0.1:9222/docs/` | 完整文档 |

---

## 环境变量

启动后自动写入：

| 变量 | 值 |
|------|-----|
| `AI_BROWSER_MCP_URL` | `ws://127.0.0.1:9222` |
| `AI_BROWSER_MCP_WS` | `ws://127.0.0.1:9222/mcp` |
| `AI_BROWSER_MCP_HOST` | `127.0.0.1` |
| `AI_BROWSER_MCP_PORT` | `9222` |
| `AI_BROWSER_MCP_HEALTH` | `http://127.0.0.1:9222/health` |
| `AI_BROWSER_MCP_HTTP_POST` | `http://127.0.0.1:9222/mcp` |
| `AI_BROWSER_MCP_VERSION` | `2.6.1` |

---

## 文档

| 文档 | 读者 |
|------|------|
| [客户使用手册](docs/客户使用手册.md) | 终端客户 — 安装、Cursor、话术、VIP、FAQ |
| [使用技能书](docs/使用技能书.md) | 技术/Agent — MCP 调用、场景脚本、Hook |
| [MCP工具配置说明书](docs/MCP工具配置说明书.md) | 部署 — mcp_config 全字段、环境变量 |
| [QUICKSTART ZH](docs/QUICKSTART_ZH.md) | 中文快速上手 |
| [QUICKSTART EN](docs/QUICKSTART_EN.md) | English Quick Start |

---

## 配置

`mcp_config.json` (本地桌面优化默认值)：

```json
{
  "port": 9222,
  "bind_address": "127.0.0.1",
  "disable_auth": true,
  "rate_limit_per_minute": 0,
  "enable_network_log": true,
  "window_topmost": true
}
```

---

## 技术架构

```text
Cursor / Claude Desktop  ←→  mcp_bridge.js (stdio 桥接)
            │
            ▼
    127.0.0.1:9222 (HTTP/WS JSON-RPC)
            │
    MCP_Server.wsv (~8000行)
    ├── Core      — 导航/JS/DOM/CDP/截图/拦截/等待
    ├── Form      — FBrowser 填表框架
    ├── VIP       — 指纹/代理/高级键鼠/CDP
    ├── System    — 系统/进程/窗口
    ├── Workflow  — JSON 工作流引擎
    ├── Reverse   — JS逆向/CDP Hook
    ├── HTTP      — HTTP/WebSocket 路由
    └── Events    — 浏览器事件 Hook 系统
            │
    FBrowser CEF (libcef.dll ~236MB)
```

---

## 社区

- 仓库: https://github.com/AI-XiaoDao/ai-browser-mcp
- 群: [737680767](https://qm.qq.com/q/Hpv6qm8qUE)
- QQ: 212577526 | 微信: XSMZAS1

MIT License © AI-XiaoDao
