<div align="center">

# AI-Browser-MCP · Windows 浏览器自动化 MCP 服务

### 任意 AI 代理 · 一句话操控真实浏览器 · Cursor / Claude / Cline

**268 工具** · **MCP 协议** · **原生 API 优先** · **FBrowser CEF** · **`127.0.0.1:9222`** · **MIT**

[![Download v2.8.0](https://img.shields.io/badge/⬇_Download-v2.8.0-238636?style=for-the-badge)](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.8.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/AI-XiaoDao/ai-browser-mcp?label=release)](https://github.com/AI-XiaoDao/ai-browser-mcp/releases)
[![MCP](https://img.shields.io/badge/MCP-268_tools-6ec6ff)]()
[![Platform](https://img.shields.io/badge/Platform-Windows_x64_|_win32-0078d4)]()
[![FBrowser](https://img.shields.io/badge/Kernel-FBrowser_CEF-a78bfa)]()

⚡ [3 步上手](#-3-步上手) · [场景演示](#-典型场景) · [对比 Playwright](#-vs-playwright--puppeteer) · [下载](https://github.com/AI-XiaoDao/ai-browser-mcp/releases) · [开源公告](OPEN_SOURCE.md) · [English](OPEN_SOURCE_EN.md)

</div>

---

## ✨ 一句话介绍

下载 `AI-Browser-MCP-x64-v2.8.0.zip`（~157MB），解压运行 `AI-Browser-MCP.exe`。在 Cursor / Claude 里说句话，**268 个预封装工具**自动执行：采集数据、逆向 POST 加密、CDP 定位签名算法、自动填表。

| 接入方式 | 适用 |
|----------|------|
| **stdio MCP** | Cursor、Claude Desktop、Cline — 配置 [`mcp_bridge.js`](CEFbro/AI-Fbowser-Mcp/mcp_bridge.js) |
| **HTTP POST** | 任意语言 / 自研 Agent — `POST http://127.0.0.1:9222/mcp` |
| **WebSocket** | 长连接 JSON-RPC — `ws://127.0.0.1:9222` |

---

## ⚡ 3 步上手

**1.** 下载 [x64](https://github.com/AI-XiaoDao/ai-browser-mcp/releases)（~157MB）或 [win32](https://github.com/AI-XiaoDao/ai-browser-mcp/releases)（~136MB）→ 解压 → 双击 **`AI-Browser-MCP.exe`**

**2.** 确认 [`http://127.0.0.1:9222/health`](http://127.0.0.1:9222/health) → `"status":"ok"`

**3.** Cursor 配置（`.cursor/mcp.json`）：
```json
{
  "mcpServers": {
    "ai-browser": {
      "command": "node",
      "args": ["mcp_bridge.js"]
    }
  }
}
```
自检：`node mcp_bridge.js --check`。然后对 AI 说：**「打开百度搜索今日新闻」**

> **其他 Agent**：任意 MCP 客户端指向 `http://127.0.0.1:9222/mcp` HTTP 或 `ws://127.0.0.1:9222` WebSocket。

---

## 🎯 典型场景

不用写脚本。在 AI 代理里用自然语言描述目标即可。

| # | 场景 | 一句话 | 自动调用的工具 |
|:-:|------|--------|----------------|
| ① | **数据采集** | 「滚动商品列表，采标题价格 JSON」 | `navigate` → `evaluate` → `dom_query` / `collect` |
| ② | **逆向 POST** | 「扫描 XHR/fetch，标出疑似加密字段」 | `reverse_prepare` → `inject` Hook → `network` |
| ③ | **定位算法** | 「提交时下断点，跟到 sign 函数给源码」 | `debugger_enable` → `set_breakpoint` → `stack` |
| ④ | **自动填表** | 「登录后台，导出订单前20行」 | `fill_*` → `click` → `collect` |
| ⑤ | **固化复用** | 「存成 workflow，下次一键跑」 | `workflow_run` |

<details>
<summary><b>📖 查看完整话术示例</b></summary>

```
帮我把 https://example.com/products 前 3 页的商品标题和价格采集成 JSON。

打开 https://www.douyin.com ，找出 POST 请求里疑似加密的字段并说明依据。

在这个登录页提交时下断点，定位计算 password/sign 的 JS 函数，把函数名和源码给我。

用账号 test / 密码 123456 登录后台，进入「订单列表」，把前 20 行导出成表格。

把「打开某站 → 登录 → 翻 3 页采集 → 汇总 JSON」写成 workflow JSON 并跑一遍验证。
```

**执行流程**（AI 自动编排）：
```
你说一句话 → Agent 选工具链 → sync-wait 逐步等结果 → 整理返回
若某步失败（success:false）→ Agent 自动换策略或报告原因
```

</details>

![Douyin POST 逆向扫描演示](.github/demo-douyin-post-scan.png)

---

## 🆚 VS Playwright / Puppeteer

| 维度 | 自建 Playwright / Puppeteer | **AI-Browser-MCP** |
|------|---------------------------|-------------------|
| 上手 | 写脚本、装驱动、调试选择器 | **下载 zip → 运行 exe → AI 一句话** |
| AI 集成 | Agent 现写代码，易出错 | **268 个预封装 MCP 工具**，Agent 直接调用 |
| 浏览器 | 常无头 / 需额外配置 | **FBrowser CEF 真实窗口**，行为接近用户 |
| 逆向 / 断点 | 需自己 Hook + DevTools | 内置 `browser_inject`、**CDP 调试器**、场景脚本 |
| 隐私 | 视部署方式 | 默认 **127.0.0.1 本机**，数据不出机器 |
| 平台 | 跨平台 | **Windows x64 + win32** 专精 |
| 许可 | 视项目 | **MIT** · 完整源码公开 |

---

## 🔌 核心能力（268 工具 · 22 分类）

| 分类 | 工具数 | 能力 |
|------|:------:|------|
| 导航与页面 | 11 | `navigate` `reload` `back` `forward` `get_url` `get_title` … |
| DOM 查询 | 8 | `dom_query` `dom_click` `dom_get_html` `dom_inner_html` … |
| DOM 填表 | 13 | `fill_click` `fill_set_value` `fill_select` `fill_exists` … |
| JS 执行 | 5 | `evaluate` `execute_js` `console_eval` `inject` … |
| 等待与状态 | 4 | `wait` `is_loading` `loading_info` `status` … |
| 网络抓包 | 6 | `network` `network_export` `network_body` `intercept` … |
| 数据提取 | 2 | `scrape` `extract` |
| 截图与打印 | 3 | `screenshot` `print` `print_to_pdf` |
| Cookie / 代理 | 9 | `get_cookies` `set_cookie` `delete_cookies` `set_proxy` … |
| 鼠标键盘 | 7 | `mouse_click` `mouse_move` `key_event` `touch_*` … |
| 窗口管理 | 5 | `create` `close` `move_window` `resize` … |
| CDP 协议 | 3 | `cdp` `cdp_call` `cdp_event` |
| 调试器 | 13 | `debugger_enable` `set_breakpoint` `stack` `step_*` `flow` … |
| JS 逆向 | 25 | `reverse_hook` `reverse_patch` `reverse_search` `reverse_preload` … |
| CDP 逆向 | 19 | `reverse_cdp_hook` `reverse_call_fn` `reverse_heap` `reverse_trace` … |
| 反检测 | 7 | `antidetect_presets` `fingerprint_ua` `canvas_noise` `font_randomize` … |
| 指纹虚拟 | 20+ | `fingerprint_screen` `fingerprint_hardware` `fingerprint_webgl` … |
| 工作流 | 4 | `workflow_list` `workflow_get` `workflow_run` `workflow_stop` |
| 批量与重试 | 2 | `batch` `retry` |
| 系统 | 8 | `ping` `mcp_result` `mcp_status` `fbro_version` `shutdown` … |
| 编码与工具 | 5 | `base64_encode/decode` `uri_encode/decode` `aliases` … |

> 📚 完整 API 参考：[`skills/AI浏览器MCP.md`](CEFbro/AI-Fbowser-Mcp/skills/AI浏览器MCP.md)

---

## 🏗 架构

```
AI 代理 (Cursor/Claude/Cline)
    │ stdio MCP / HTTP POST / WebSocket
    ▼
AI-Browser-MCP Server  ← mcp_bridge.js (stdio 桥接)
    │ FBrowser CEF API
    ▼
真实浏览器窗口 (CEF 内核)
```

| 模块 | 文件 | 职责 |
|------|------|------|
| 入口 | `src/main.wsv` | GUI + FBrowser 初始化 |
| MCP 核心 | `src/MCP_Server.wsv` (~7800 行) | JSON-RPC、工具注册、sync-wait、CDP/Debugger |
| 分派层 | `src/MCP_Server_Core/Form/VIP/System/Workflow/Reverse.wsv` | 268 工具实现 |
| HTTP/WS | `src/MCP_Server_HTTP.wsv` | 欢迎页、健康检查、`/mcp` 端点 |
| 事件 Hook | `src/MCP_BrowserEvents.wsv` | 生命周期/网络/回调事件 |
| 桥接 | `mcp_bridge.js` | stdio ↔ HTTP，Cursor/IDE 接入 |

---

## 📦 下载

| 包 | 平台 | 大小 |
|----|------|------|
| [**AI-Browser-MCP-x64-v2.8.0.zip**](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v2.8.0/AI-Browser-MCP-x64-v2.8.0.zip) | Windows x64 | ~157 MB |
| [**AI-Browser-MCP-win32-v2.8.0.zip**](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v2.8.0/AI-Browser-MCP-win32-v2.8.0.zip) | Windows 32-bit | ~136 MB |
| [**AI-Browser-MCP-cpp-x64-v2.8.0.zip**](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v2.8.0/AI-Browser-MCP-cpp-x64-v2.8.0.zip) | C++ 对照 x64 | ~396 KB |
| [**AI-Browser-MCP-cpp-win32-v2.8.0.zip**](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v2.8.0/AI-Browser-MCP-cpp-win32-v2.8.0.zip) | C++ 对照 win32 | ~396 KB |

**环境要求**：Windows 10/11 · Node.js 18+（Cursor 桥接）· 64 位系统优先用 x64

---

## 📁 仓库结构

```
ai-browser-mcp/
├── CEFbro/AI-Fbowser-Mcp/
│   ├── src/              # 火山 .wsv 源码（MCP 核心，开源主体）
│   ├── generated-cpp/    # 火山生成 C++ 对照（release-x64/、release-win32/）
│   ├── docs/             # 客户手册、配置说明、快速上手
│   ├── skills/           # Agent 技能书 + 268 工具参考 + 火山 API 知识库
│   ├── workflows/        # 工作流 JSON
│   ├── scenarios/        # 场景脚本（逆向、Hook 测试）
│   ├── mcp_bridge.js     # Cursor stdio 桥接
│   └── mcp_config.json   # MCP 服务配置
├── release/              # 发行辅助脚本
├── CONTRIBUTING.md       # 贡献与发版指南
├── CHANGELOG.md          # 版本更新日志
├── OPEN_SOURCE.md        # 开源公告（中文）
├── OPEN_SOURCE_EN.md     # Open-source announcement (English)
└── README.md
```

---

## 📖 文档

| 文档 | 读者 |
|------|------|
| [268 工具完整参考](CEFbro/AI-Fbowser-Mcp/skills/AI浏览器MCP.md) | 开发者 / Agent |
| [客户使用手册](CEFbro/AI-Fbowser-Mcp/docs/客户使用手册.md) | 终端用户 |
| [MCP 工具配置说明书](CEFbro/AI-Fbowser-Mcp/docs/MCP工具配置说明书.md) | 部署 / 集成 |
| [使用技能书](CEFbro/AI-Fbowser-Mcp/docs/使用技能书.md) | 开发者 / Agent |
| [场景与 Hook 测试](CEFbro/AI-Fbowser-Mcp/skills/场景与Hook测试.md) | 逆向 / persist Hook |
| [快速上手（中文/SEO）](CEFbro/AI-Fbowser-Mcp/docs/QUICKSTART_ZH.md) | 中文检索 |
| [Quick Start (English)](CEFbro/AI-Fbowser-Mcp/docs/QUICKSTART_EN.md) | International SEO |

---

## 🤝 参与

- **Issue**：[Bug 报告](https://github.com/AI-XiaoDao/ai-browser-mcp/issues/new?template=bug_report.yml) · [功能建议](https://github.com/AI-XiaoDao/ai-browser-mcp/issues/new?template=feature_request.yml)
- **PR**：见 [CONTRIBUTING.md](CONTRIBUTING.md)，改 `src/*.wsv` 提 PR
- **交流**：QQ 212577526 · 群 737680767 · [火山编程交流群](https://qm.qq.com/q/Hpv6qm8qUE)

## ❓ FAQ

| 问题 | 解决 |
|------|------|
| `/health` 失败 | 确认 exe 已启动；检查 9222 端口未被占用 |
| AI 代理连不上 | 先启动 exe → `node mcp_bridge.js --check`；Cursor 用 stdio 桥接勿直连 URL |
| 工具调用超时 | 增大 `mcp_config.json` 中 `default_timeout_ms` 或给工具加 `max_ms` 参数 |
| POST body 抓不到 | 默认网络层不记 POST 正文，用 `browser_inject` persist Hook |
| 调试器断点不命中 | 确认 `browser_debugger_enable` 已执行且页面已触发目标事件 |
| x64 vs win32 | 64 位系统优先 x64；仅 32 位环境用 win32 |

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">

**如果这个项目对你有帮助，欢迎 Star ⭐**

</div>
