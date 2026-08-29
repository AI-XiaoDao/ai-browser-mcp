# 🚀 AI浏览器 MCP Server

> **Windows 本地浏览器自动化 MCP 服务端** — 真实 FBrowser CEF 内核 · **265 个浏览器自动化工具** · 本地 `127.0.0.1:9222` · MIT 开源
>
> Web Scraping · JS Reverse Engineering · CDP Debugger · 内核层扩展 · 指纹反检测 · Form Automation RPA

[![Release](https://img.shields.io/badge/release-v3.1.0-blue)](https://github.com/AI-XiaoDao/ai-browser-mcp/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows_x64_|_win32-lightgrey)](https://github.com/AI-XiaoDao/ai-browser-mcp/releases)

---

## 📖 这是什么？

**AI浏览器 MCP Server** 是一个 **Windows 本地浏览器自动化 MCP 服务端**：运行真实的 **FBrowser CEF（Chromium）浏览器内核**，通过 **Model Context Protocol（MCP）** 向 AI 编程助手（Cursor / Claude Desktop / Cline / 任意 MCP 客户端）暴露 **265 个浏览器自动化工具**。

无需安装 Node 驱动、无需编写 Playwright/Puppeteer 脚本——**下载解压即用**，AI 用自然语言即可操控浏览器完成：

- 🕷️ **Web Scraping 网页采集** — `browser_scrape` 一步爬虫（导航→等待→提取全自动）
- 🔍 **JS 逆向分析** — 函数 Hook / 调用栈追踪 / 算法识别 / 混淆检测 / 动态提取
- 🐛 **CDP 断点调试** — `debugger_flow` 一键断点→求值→resume，定位 sign 算法
- ⚙️ **内核层扩展** — 自定义协议(`mcp://`)、证书管理、HTTP 认证注入、下载控制、事件反应器
- 🤖 **Form Automation RPA** — 原生 CEF 填表 API（非 JS 注入）
- 🎭 **浏览器指纹伪装** — 30+ 维度（Canvas/WebGL/Audio/WebRTC/SSL/字体/硬件）
- 📡 **网络抓包拦截** — HTTP/WS 流量捕获、修改、替换、屏蔽
- 🔄 **工作流编排** — JSON 步骤链批量执行

**隐私**：纯本地 `127.0.0.1:9222`，数据不出本机。

---

## 🆕 v3.1.0 新增（内核层能力扩展）

| 能力 | 工具 | 说明 |
|---|---|---|
| **自定义协议** | `browser_kernel_scheme` | 注册 `mcp://域名` 动态内容（CEF 资源处理器，支持 data/file）|
| **证书管理** | `browser_kernel_cert` | 证书错误收集 / 一键忽略 SSL 错误 |
| **HTTP 认证注入** | `browser_kernel_auth` | Basic/Digest 凭据自动应答（内核事件级）|
| **下载控制** | `browser_kernel_download` | 暂停/恢复/取消进行中下载 |
| **IPC 双向通道** | `browser_kernel_ipc_queue` / `ipc_clear` | 主进程↔渲染进程双工通信（页面队列）|
| **CDP 事件监控** | `browser_kernel_cdp_monitor` | CDP 事件订阅自动落库（`Network.*` 等）|
| **事件反应器** | `browser_kernel_reactor` | 事件触发→自动执行页面 JS（组合引擎）|
| **定时监视** | `browser_kernel_watch` | 表达式周期求值 + 变更检测（`watch_changed` 事件）|
| **一键全事件流** | `browser_kernel_events_all` | 13 项浏览器/应用事件 + 控制台 + 网络详细 |
| **动态插桩** | `browser_kernel_reverse_probe` | XHR/fetch/WebSocket/定时器/监听器五维插桩 |
| **动态调用追踪** | `browser_kernel_reverse_trace` | 目标函数包装：调用栈+参数+返回值+耗时 |
| **动态算法 Hook** | `browser_kernel_reverse_algo` | CryptoJS 全算法 + WebCrypto subtle + 哈希/base64 |
| **动态函数/源码提取** | `browser_kernel_reverse_functions` / `sources` | 枚举函数 toString 源码 / 全脚本提取 |
| **全局变量追踪** | `browser_kernel_reverse_watch_global` | setter 包装记录写入者调用栈+新值 |
| **快捷菜单屏蔽** | `browser_kernel_menu` | 右键菜单内核级拦截 |

另有大量稳定性修复：debugger 参数校验防 CDP 队列堵塞、竞态修复（导航规则锁/原子维护）、HTTP POST 体上限、日志截断合法 JSON 等。

---

## 🚀 快速开始

### 1. 下载

👉 [Releases 页面](https://github.com/AI-XiaoDao/ai-browser-mcp/releases) 下载最新版：

| 包 | 说明 |
|---|---|
| `AI-Browser-MCP-x64-v3.1.0.zip` | 64 位 Windows（~160MB）|
| `AI-Browser-MCP-win32-v3.1.0.zip` | 32 位 Windows（~140MB）|
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

> 也可以用欢迎页 `http://127.0.0.1:9222/` 一键复制 Cursor 配置；或启用 `auto_install_agents` 自动写入 Cursor/Claude/Codex/Cline/Windsurf。

### 4. 自检

```bash
node mcp_bridge.js --check
# 原生 stdio 自检: AI-Fbowser-Mcp.exe --mcp-stdio 启动后向 stdin 发送 ping 请求
```

---

## 🛠 核心能力一览（265 工具）

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

**Sync-Wait 同步等待**：轻量读操作（get_title/evaluate/dom_*）自动同步返回，重量操作（截图/源码）异步 task_id 轮询；`max_ms` 调超时、`async_only:true` 强制异步。

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
| `http://127.0.0.1:9222/docs/` | 完整文档 |

---

## 🧱 技术架构

```text
Cursor / Claude Desktop  ←→  mcp_bridge.js (stdio 桥接)
            │
            ▼
    127.0.0.1:9222 (HTTP/WS JSON-RPC)
            │
    MCP_Server.wsv (MCP引擎/工具注册/路由)
    ├── Core       — 导航/JS/DOM/CDP/截图/拦截/等待 (162工具)
    ├── Form       — FBrowser 填表框架 (10工具)
    ├── VIP        — 指纹/代理/高级键鼠/CDP (68工具)
    ├── Kernel     — 内核层: 自定义协议/证书/认证/下载/IPC/事件引擎 (28工具)
    ├── Reverse    — JS逆向: Hook/断点/堆/混淆检测
    ├── System     — 系统/进程/窗口
    ├── Workflow   — JSON 工作流引擎
    ├── HTTP       — HTTP/WebSocket 路由
    └── Events     — 浏览器事件 Hook 系统 (40+事件)
            │
    FBrowser CEF (libcef.dll)
```

**开发语言**：火山视窗（中文编程）— 全部源码 `src/*.wsv` 开源，运行时零依赖（原生 stdio 直连 / Node 桥两种接入均可）。

> 📐 **完整架构说明见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — 进程模型 / 传输层 / 协议合规 / 请求处理链 / 同步等待引擎 / 事件层 / 源码布局 / 构建发布。

---

## 📁 目录结构

```text
├── CEFbro/AI-Fbowser-Mcp/
│   ├── src/                 # 火山源码 (16 个 .wsv, MCP引擎/工具/事件/stdio/内核)
│   ├── AI-Fbowser-Mcp.vprj / .vsln   # 火山工程
│   ├── workflows/           # 示例工作流 JSON (编译附属)
│   ├── docs/                # 成品在线文档 (服务器 /docs/ 路由)
│   ├── mcp_bridge.js        # Node 桥 (备用接入)
│   └── mcp_config.json / mcp_config.README.md
├── release/                 # 成品打包脚本 + 发布说明
└── .mcp.json / .cursor/     # 一键接入配置
```

---

## 📚 文档

| 文档 | 读者 |
|---|---|
| [客户使用手册](CEFbro/AI-Fbowser-Mcp/docs/客户使用手册.md) | 终端客户 — 安装/Cursor/话术/VIP/FAQ |
| [架构说明](docs/ARCHITECTURE.md) | 开发者/架构 — 进程模型/传输/协议/源码布局 |
| [MCP工具配置说明书](CEFbro/AI-Fbowser-Mcp/docs/MCP工具配置说明书.md) | 部署 — 配置全字段/环境变量 |
| [小白使用指南](CEFbro/AI-Fbowser-Mcp/docs/小白使用指南.md) | 新用户 — 下载即用 |
| [QUICKSTART (EN)](CEFbro/AI-Fbowser-Mcp/docs/QUICKSTART_EN.md) | English quick start |

---

## 🔑 环境变量（启动自动写入）

`AI_BROWSER_MCP_URL` · `AI_BROWSER_MCP_WS` · `AI_BROWSER_MCP_PORT` · `AI_BROWSER_MCP_HOST` · `AI_BROWSER_MCP_HEALTH` · `AI_BROWSER_MCP_HTTP_POST` · `AI_BROWSER_MCP_VERSION`

---

## ⚖️ 开源

- **MIT License** — 源码与文档全部开放（[LICENSE](LICENSE)）
- 仓库：https://github.com/AI-XiaoDao/ai-browser-mcp
- 技术支持：QQ 212577526 · QQ群 737680767

---



<!-- SEO: MCP browser automation · Cursor browser MCP · 浏览器自动化 MCP · web scraping MCP · Playwright alternative · CDP debugger MCP · JS reverse engineering MCP · 浏览器指纹反检测 · 火山视窗 CEF · AI浏览器 MCP · browser kernel extension · 265 MCP tools -->
