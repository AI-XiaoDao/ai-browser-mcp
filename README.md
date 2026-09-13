# 🚀 AI浏览器 MCP Server

> **Windows 本地浏览器自动化 MCP 服务端** — 真实 FBrowser CEF 内核 · **334 个浏览器自动化工具（全量真机核验：0 失败 / 0 闪退）** · 本地 `127.0.0.1:9222` · MIT 开源

[![Release](https://img.shields.io/badge/release-v3.2.0-blue)](https://github.com/AI-XiaoDao/ai-browser-mcp/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows_x64_|_win32-lightgrey)](https://github.com/AI-XiaoDao/ai-browser-mcp/releases)

---

## 📖 这是什么？

**AI浏览器 MCP Server** 运行真实的 **FBrowser CEF（Chromium）浏览器内核**，通过 **Model Context Protocol（MCP）** 向 AI 编程助手（Cursor / Claude / Cline / Trae / 任意 MCP 客户端）暴露 **334 个浏览器自动化工具**。无需安装 Node 驱动、无需编写脚本——**下载解压即用**：

- 🕷️ **Web Scraping** — `browser_scrape` 一步爬虫（导航→等待→提取全自动）
- 🔍 **JS 逆向分析** — Hook / 调用栈 / 算法识别 / 混淆检测 / 动态提取
- 🐛 **CDP 断点调试** — `debugger_flow` 一键断点→求值→resume
- ⚙️ **内核层扩展** — 自定义协议 / 证书 / HTTP 认证注入 / 下载控制 / 事件反应器
- 🤖 **填表 RPA** — 原生 CEF 填表 API（非 JS 注入）
- 🎭 **指纹反检测** — 30+ 维度（Canvas/WebGL/Audio/SSL/字体/硬件）
- 📡 **网络抓包拦截** — HTTP/WS 捕获、修改、替换、屏蔽
- 🔄 **工作流编排** — JSON 步骤链批量执行

**隐私**：纯本地 `127.0.0.1:9222`，数据不出本机。

---

## 🆕 v3.2.0（334 工具全量真机核验版）

| 项 | 说明 |
|---|---|
| **334 工具逐个核验** | 311 通过 / 23 受控跳过 / 0 失败，全程零冷重启（35 秒跑完一遍）|
| **稳定性修复 20+** | AB-BA 死锁、非法 browser_id 静默回退、browser_close confirm 闸门、CDP 观察者归属、并发 create 握手令牌、mcp_help 深链非法 JSON、hwnd 32 位截断、DB 守卫、HAR timestamp 等 |
| **CDP 优先改造** | evaluate/console_eval/extract/view_source/key_event 改走 CDP（原生通道 8% 丢回调 → 5s 超时）；step 无断点如实跳过 |
| **调试体验** | 控制台窗口可见 + 日志双写 `mcp_console.log`；启动器 ShellExecuteW（重启 10 分钟 → 6 秒）|
| **质量基线** | 操作备注/死代码/残注释/幽灵注册全零；fastcheck 56/56；菜单回归 22/22 |

---

## 🚀 快速开始

### 1. 下载

👉 [Releases 页面](https://github.com/AI-XiaoDao/ai-browser-mcp/releases) 下载最新版：

| 包 | 说明 |
|---|---|
| `AI-Browser-MCP-x64-v3.2.0.zip` | 64 位 Windows（~160MB）|
| `AI-Browser-MCP-win32-v3.2.0.zip` | 32 位 Windows（~140MB）|
| `AI-Browser-MCP-cpp-*.zip` | C++ 生成源码对照 |

### 2. 启动

解压 → 双击 **`AI-Fbowser-Mcp.exe`** → 浏览器打开 `http://127.0.0.1:9222/health` 看到 `{"status":"ok"}` 即就绪。

### 3. 接入 AI Agent（Cursor 示例）

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

> 也可以用欢迎页 `http://127.0.0.1:9222/` 一键复制 Cursor 配置；或启用 `auto_install_agents` 自动写入 Cursor/Claude/Codex/Cline/Windsurf。成品包内附带完整使用手册。

### 4. 自检

```bash
node mcp_bridge.js --check
# 原生 stdio 自检: AI-Fbowser-Mcp.exe --mcp-stdio 启动后向 stdin 发送 ping 请求
```

---

## 🛠 核心能力一览（334 工具）

| 类别 | 数量 | 代表工具 |
|---|---|---|
| 系统/元工具 | 9 | `ping` `mcp_status` `mcp_result` `batch`(≤200条) `aliases` |
| 导航/页面 | 10 | `navigate` `get_url` `get_title` `reload`(ignore_cache) |
| JS 执行 | 4 | `evaluate` `execute_js` `console_eval` `inject`(持久V8) |
| DOM 操作 | 14 | `dom_query` `dom_click` `snapshot` `element_action` |
| 填表 RPA | 10 | `fill_set_value` `fill_click` `fill_form`(批量) |
| 网络抓包 | 5 | `network` `network_body` `collect` `network_export`(HAR) |
| 资源拦截 | 1 | `intercept`（modify/block/redirect/replace_file 流式引擎）|
| Cookie/代理 | 8 | `get_cookies` `set_cookie` `set_proxy` `set_s5_proxy` |
| 截图/打印 | 3 | `screenshot` `print` `print_to_pdf` |
| CDP 协议 | 3 | `cdp_call` `cdp_event` `cdp` |
| 断点调试 | 15 | `debugger_flow` `debugger_auto` `set_breakpoint` `inspect` |
| JS 逆向 | 34 | `reverse_hook` `reverse_scan_crypto` `reverse_call_fn` `kernel_reverse_*` |
| 指纹伪装 | 45+ | `fingerprint` `antidetect_presets` `vip_fingerprint_*` |
| 内核层 | 15 | `kernel_scheme` `kernel_cert` `kernel_auth` `kernel_reactor` 等 |
| 输入交互 | 14 | `mouse_*` `key_event` `touch_*` `vip_mouse_*` |
| 窗口/系统 | 15 | `window_info` `file_dialog` `ipc_*` |
| 编码 | 4 | `base64_*` `uri_*` |
| 工作流 | 4 | `workflow_list` `run` `stop` |

**Sync-Wait 同步等待**：轻量读操作自动同步返回，重量操作异步 task_id 轮询；`max_ms` 调超时、`async_only:true` 强制异步。

---

## 🔌 端点

| 端点 | 说明 |
|---|---|
| `POST http://127.0.0.1:9222/mcp` | HTTP JSON-RPC 主通道 |
| `ws://127.0.0.1:9222` | WebSocket JSON-RPC |
| `http://127.0.0.1:9222/` | 欢迎页控制台 |
| `http://127.0.0.1:9222/health` | 健康检查 |
| `http://127.0.0.1:9222/tools/list` | 工具列表 |
| `http://127.0.0.1:9222/api` / `/cursor-config` / `/json/version` / `/json/list` | 元信息/CDP 兼容 |

---

## 🧱 技术架构

```text
Cursor / Claude Desktop  ←→  mcp_bridge.js (stdio 桥接)
            │
            ▼
    127.0.0.1:9222 (HTTP/WS JSON-RPC)
            │
    MCP_Server.wsv (MCP引擎/工具注册/路由)
    ├── Core       — 导航/JS/DOM/CDP/截图/拦截/等待
    ├── Form       — FBrowser 填表框架
    ├── VIP        — 指纹/代理/高级键鼠/CDP
    ├── Kernel     — 内核层: 自定义协议/证书/认证/下载/IPC/事件引擎
    ├── Reverse    — JS逆向: Hook/断点/堆/混淆检测
    ├── System     — 系统/进程/窗口
    ├── Workflow   — JSON 工作流引擎
    ├── HTTP       — HTTP/WebSocket 路由
    └── Events     — 浏览器事件 Hook 系统
            │
    FBrowser CEF (libcef.dll)
```

**开发语言**：火山视窗（中文编程）— 全部源码 `src/*.wsv` 开源，运行时零依赖。

---

## 📁 目录结构

```text
├── CEFbro/AI-Fbowser-Mcp/
│   ├── src/                 # 火山源码 (16 个 .wsv)
│   ├── AI-Fbowser-Mcp.vprj / .vsln   # 火山工程
│   ├── workflows/           # 示例工作流 JSON
│   ├── mcp_bridge.js        # Node 桥 (stdio 接入)
│   └── mcp_config.json / mcp_config.README.md
└── .mcp.json                # 仓库级一键接入配置
```

---

## 🔑 环境变量（启动自动写入）

`AI_BROWSER_MCP_URL` · `AI_BROWSER_MCP_WS` · `AI_BROWSER_MCP_PORT` · `AI_BROWSER_MCP_HOST` · `AI_BROWSER_MCP_HEALTH` · `AI_BROWSER_MCP_HTTP_POST` · `AI_BROWSER_MCP_VERSION`

---

## ⚖️ 开源

- **MIT License** — 源码与文档全部开放（[LICENSE](LICENSE)）
- 仓库：https://github.com/AI-XiaoDao/ai-browser-mcp
- 技术支持：QQ 212577526 · QQ群 737680767

<!-- SEO: MCP browser automation · Cursor browser MCP · 浏览器自动化 MCP · web scraping MCP · Playwright alternative · CDP debugger MCP · JS reverse engineering MCP · 浏览器指纹反检测 · 火山视窗 CEF · AI浏览器 MCP · browser kernel extension · 334 MCP tools -->
