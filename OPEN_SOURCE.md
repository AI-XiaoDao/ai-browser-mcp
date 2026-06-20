# 🎉 AI浏览器 MCP Server 正式开源

> 可直接复制到 GitHub、论坛、QQ 群、公众号。  
> 仓库：https://github.com/AI-XiaoDao/ai-browser-mcp  
> **各大论坛专帖文案** → [FORUM_POSTS.md](FORUM_POSTS.md)（V2EX / 掘金 / 知乎 / 看雪 / Reddit 等 21 个平台）

---

## 📋 论坛 / 群公告 · 短帖（复制即用）

```
【开源】AI浏览器 MCP Server v2.6.0 — Windows 本地浏览器自动化 MCP 服务

让 **任意 AI 代理**（Cursor / Claude / Cline / 自研 MCP 客户端）用自然语言操控真实浏览器：217 个 browser_* 工具，导航/填表/读 DOM/抓网络/工作流/CDP 断点。

一句话自动执行：采集数据 · 逆向 POST 加密字段 · CDP 定位 sign 算法 — AI 自己串联工具，不用写 Playwright。

✅ 已开源：火山 .wsv 源码 + 生成 C++ 对照 + 文档/桥接脚本（MIT）
✅ 成品下载：GitHub Releases（exe + CEF，约 157MB）— **217 工具全开放，解压即用**
✅ 本机 127.0.0.1:9222，默认不暴露外网

下载：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
  · AI-Browser-MCP-x64-v2.6.0.zip      — 运行包
  · AI-Browser-MCP-cpp-x64-v2.6.0.zip  — 火山生成 C++ 对照（可选）

Star / Issue 欢迎：https://github.com/AI-XiaoDao/ai-browser-mcp
QQ：212577526 · 群：737680767
```

---

## 一句话介绍

**AI浏览器 MCP Server** —— 基于火山视窗 + FBrowser CEF 的 **Windows 本地浏览器自动化 MCP 服务**。启动 exe 后，**任何支持 MCP 的 AI 代理**（不限 Cursor）均可通过 HTTP/WebSocket 或 `mcp_bridge.js` 调用 **217 个** `browser_*` 工具。

---

## 为什么开源？

| 动机 | 说明 |
|------|------|
| **降低门槛** | 无需从零写 Playwright/Puppeteer；MCP 工具已封装，AI 直接调用 |
| **可审计** | `.wsv` 源码 + 生成 C++ 对照公开，协议与工具行为透明 |
| **可扩展** | 工作流 JSON、Hook 场景、`run_all_tests.js` 均可二次开发 |
| **国内友好** | FBrowser CEF 内核，Windows 原生，默认仅监听 `127.0.0.1` |

---

## 核心亮点（速览）

| 亮点 | 说明 |
|------|------|
| **217 MCP 工具** | 导航 / 填表 / DOM / JS / 网络 / 工作流 / CDP 等，24 大类 |
| **自然语言驱动** | 采集 / 逆向 / 定位算法 — 一句话描述目标，Agent 自动串联工具链 |
| **真实 CEF 窗口** | FBrowser 内核，行为接近日常浏览，非纯无头模拟 |
| **双通道 JSON-RPC** | WebSocket + HTTP POST `http://127.0.0.1:9222/mcp` |
| **sync-wait + batch** | 同步等结果 + 批量调用，Agent 编排更省轮次 |
| **工作流 JSON** | `linker/workflows/*.json`，一键 `workflow_run` |
| **欢迎页控制台** | `http://127.0.0.1:9222/` — 健康检查、复制 Cursor 配置、浏览文档 |
| **MIT 全开源** | `.wsv` 权威源码 + `generated-cpp/` + 技能书 + 测试 |
| **下载即全功能** | GitHub 成品 zip：**截图/CDP/调试器/指纹/拦截等 217 工具全部可用** |
| **强大扩展** | 工作流 JSON、Hook 场景、技能书、MIT 源码欢迎 PR |

> **说明**：`browser_create` / `browser_close` / `browser_create_background` / `browser_create_tab` 共 4 个 GUI 窗口类工具在嵌入式 GUI 模式下**已禁用**，由主窗口自动管理浏览器实例。  
> **完整优点表**见仓库 [README · 核心优点（全景）](README.md#-核心优点全景)。

---

## 🌟 全部优点 · 长帖（复制即用）

适合 QQ 群精华、知乎回答、公众号「产品亮点」段落：

```
【AI浏览器 MCP — 全部优点一览】

▸ 对 AI 用户
  · 217 个 browser_* 工具，Cursor / Claude 直连 MCP，自然语言操控浏览器
  · sync-wait：读 DOM/标题/JS 等同次调用内等结果，少写轮询逻辑
  · batch 批量 + workflow JSON 多步骤编排，复杂任务可版本管理
  · 语义失败检测：元素找不到、{ok:false} 会明确 success:false，AI 不易误判

▸ 一句话场景（不用写脚本）
  · 数据采集：「帮我把这页商品名价格采下来」→ 导航/滚动/DOM/collect/整理 JSON
  · 逆向算法：「找出 POST 里哪个字段加密了」→ reverse_prepare + persist Hook + 网络对比
  · 定位算法：「sign 在哪个 JS 函数里」→ CDP 断点/单步/栈/源码（Release 成品已开放）
  · 自动填表/RPA：「登录并导出订单」→ fill_* + workflow 固化复用
  · Agent 自动串联 217 工具，sync-wait 逐步等结果，你只管说目标

▸ 浏览器与自动化
  · FBrowser CEF 真实窗口，页面行为贴近用户环境
  · 导航、填表、DOM 查询、JS 执行、网络列表/collect、鼠标键盘
  · 事件 Hook 系统 + 资源拦截，支持逆向与改包场景
  · CDP WebSocket 原生暴露，可接 DevTools 生态；调试器断点/单步/flow

▸ 协议与集成
  · 标准 MCP + JSON-RPC；WebSocket 长连接 + HTTP POST 双通道
  · mcp_bridge.js 桥接 Cursor；全 HTTP 端点 CORS，前端可 fetch
  · 启动自注册 AI_BROWSER_MCP_URL/PORT/HEALTH；9222 欢迎页在线文档

▸ 安全与本地
  · 默认 127.0.0.1:9222，本机 Agent，数据不出机器
  · 托盘常驻：关主窗口后 MCP 仍可服务长时间任务

▸ 开源与生态
  · MIT：11 个 .wsv 模块（~2 万行）+ generated-cpp 对照 + 217 工具文档
  · run_all_tests.js 全量回归；mcp_config.json 可配速率/日志/缓存
  · 四层产物清晰（src → cpp → 运行包，不含 linker/out/ 中间文件）
  · 国内栈：火山视窗 + FBrowser，中文技能书与 QQ/火山社群

▸ 对比自建 Playwright
  · 预封装 217 工具 vs 自己写 MCP 封装层
  · 下载 exe 即用 vs 环境+脚本+维护
  · 本地离线 vs 云端 Browser API 依赖网络与计费

下载：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
仓库：https://github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 💬 典型话术 · 一句话自动执行（复制即用）

配置好 Cursor 后，**不用写脚本**，直接说：

**数据采集**
```
帮我把 https://某站/list 滚动加载 5 屏，把标题、价格、链接采成 JSON。
登录后进入订单页，导出表格每一行。
盯着 /api/list 这个接口，把响应里的 data 数组整理给我。
```

**逆向算法**（POST body 须 persist Hook，见 FAQ）
```
打开抖音，扫描 XHR/fetch 的 POST，标出疑似加密字段和依据。
打开某页，Hook fetch，在提交表单时把 request body 完整打出来。
开 console 采集，我点提交后把 sign 相关日志整理给我。
```

![Douyin POST 逆向扫描 — Agent 一句话自动 Hook + 滚动 + 分析 33 条 POST](.github/demo-douyin-post-scan.png)

**定位算法**
```
提交时下断点，单步跟到计算 sign 的 JS 函数，给我函数名和源码片段。
搜索页面脚本里含 md5/sign 的位置，断点命中后把 call stack 列出来。
```
（CDP 调试器已包含在 Release 下载包中）

**自动填表 / RPA**
```
用账号 xxx / 密码 yyy 登录这个后台，进入订单页，导出前 20 行表格。
把「登录 → 翻 3 页 → 采集 JSON」写成 workflow 并跑一遍验证。
```

AI 会自动选择 `browser_navigate`、`browser_dom_query`、`browser_collect`、`browser_inject`、`browser_reverse_prepare`、`browser_debugger_*` 等工具，逐步 **sync-wait** 执行。完整场景说明见 [README · 典型场景](README.md#-典型场景一句话自动执行)。

---

## 📋 场景速查卡（复制到群 / 笔记）

```
AI浏览器 MCP · 一句话场景速查 v2.6

① 采集  「滚动列表，采标题价格 JSON」        → dom_query / collect
② 逆向  「扫描 POST，标疑似加密字段」        → inject Hook + network（body 须 Hook）
③ 定位  「断点跟到 sign 函数，给源码」       → debugger_*
④ 填表  「登录后台，导出订单表」             → fill_* / workflow
⑤ 复用  「存成 workflow，下次一键跑」       → workflow_*

配置：exe + Cursor mcp_bridge.js → 127.0.0.1:9222
仓库：github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 🐦 Twitter / X · 英文短帖（复制即用）

```
[Open Source] AI Browser MCP v2.6 — 217 tools for Cursor on Windows

One sentence → auto-runs:
· Scrape data from pages
· Reverse POST crypto fields
· Locate sign JS via CDP breakpoints

Local FBrowser CEF · MIT · 127.0.0.1:9222

https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
```

---

## 📮 Reddit · r/cursor / r/LocalLLaMA（复制即用）

```
Title: [Release] AI Browser MCP Server v2.6 — local Windows browser automation for Cursor (217 MCP tools)

I open-sourced a Windows-native MCP server that wraps a real FBrowser CEF browser with 217 browser_* tools.

Instead of writing Playwright scripts, you tell Cursor in plain language:
- "Scroll this list and collect title/price as JSON"
- "Scan POST bodies and flag encrypted-looking fields"
- "Break on submit and show me the JS function that computes sign"

Runs locally on 127.0.0.1:9222. MIT license, .wsv source included.

Download: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
Repo: https://github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 💬 知乎 / 即刻 · 短回答（复制即用）

```
不用写 Playwright。Windows 上跑 AI浏览器 MCP，Cursor 里一句话：

· 采集：「滚动商品列表，采标题价格 JSON」
· 逆向：「扫描 POST，标出疑似加密字段」（须 Hook 抓 body）
· 定位：「提交时下断点，给 sign 函数源码」（Release 成品已开放 CDP）

217 个 browser_* 工具已封装，Agent 自动串联，MIT 开源。

https://github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 3 分钟上手

### 1. 下载并运行

| 文件 | 大小 | 用途 |
|------|------|------|
| [AI-Browser-MCP-x64-v2.6.0.zip](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v2.6.0/AI-Browser-MCP-x64-v2.6.0.zip) | ~157MB | **运行包**：exe + CEF + 脚本/文档 |
| [AI-Browser-MCP-cpp-x64-v2.6.0.zip](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v2.6.0/AI-Browser-MCP-cpp-x64-v2.6.0.zip) | ~0.3MB | **C++ 对照**（可选，与仓库 `generated-cpp/` 相同） |

```
1. 解压 AI-Browser-MCP-x64-v2.6.0.zip 到任意目录
2. 双击 AI浏览器.exe
3. 浏览器打开 http://127.0.0.1:9222/health → 确认 "status":"ok"
4. 配置 Cursor（见下方）
5. 对 AI 说：「打开 https://example.com 并读取标题」— 或见下方「典型话术」
```

**环境要求**：Windows 10/11 x64 · Node.js 18+（Cursor 桥接）· 成品包已含 CEF 运行时

### 2. Cursor 配置

**方式 A — 克隆仓库开发**（使用仓库内桥接脚本）：

```json
{
  "mcpServers": {
    "ai-browser": {
      "command": "node",
      "args": ["CEFbro/AI浏览器/mcp_bridge.js"],
      "env": {
        "AI_BROWSER_MCP_HTTP_POST": "http://127.0.0.1:9222/mcp"
      }
    }
  }
}
```

**方式 B — 仅使用 Release 解压目录**（`mcp_bridge.js` 与 exe 同目录）：

```json
{
  "mcpServers": {
    "ai-browser": {
      "command": "node",
      "args": ["D:/你的路径/mcp_bridge.js"],
      "env": {
        "AI_BROWSER_MCP_HTTP_POST": "http://127.0.0.1:9222/mcp"
      }
    }
  }
}
```

自检：`node mcp_bridge.js --check` → 应显示版本 `2.6.0` 且浏览器数量 ≥ 1。

---

## 仓库包含什么？

### ✅ 已开源（Git 仓库内）

| 内容 | 路径 |
|------|------|
| **MCP 服务核心（权威源码）** | `CEFbro/AI浏览器/src/*.wsv`（11 个文件） |
| **火山生成 C++ 对照** | `CEFbro/AI浏览器/generated-cpp/release-x64/`（33 cpp + 218 h） |
| 用户文档 | `CEFbro/AI浏览器/docs/` — 客户手册、配置说明、使用技能书 |
| 217 工具参考 | `CEFbro/AI浏览器/skills/AI浏览器MCP.md` |
| Agent 技能书 | `CEFbro/AI浏览器/skills/` — 火山 API 知识库 |
| 桥接与测试 | `mcp_bridge.js`、`mcp_client.js`、`mcp_check.js`、`run_all_tests.js` |
| 工作流 | `CEFbro/AI浏览器/workflows/` → 编译后复制到 `linker/workflows/` |
| 配置包镜像 | `release/linker/` — 脚本/文档/工作流（**无 exe**） |
| Cursor 示例 | 根目录 `.mcp.json` |
| 许可证 | `LICENSE`（MIT） |

### 运行包与源码（简要）

| 内容 | 获取方式 |
|------|----------|
| `AI浏览器.exe` + CEF 运行时 | [Releases](https://github.com/AI-XiaoDao/ai-browser-mcp/releases) → x64 zip |
| C++ 对照（与 `generated-cpp/` 相同） | Releases → cpp zip |
| MCP 权威源码 | 本仓库 `src/*.wsv`（MIT） |

开发者编译说明见仓库 README「开发者：源码结构与编译说明」折叠章节。

---

## 源码与编译目录（`.wsv` vs C++ vs `out/`）

完整说明见仓库 README「开发者：源码结构与编译说明」。核心对照：

| 层级 | 路径 | 二次开发 |
|:--:|------|:--:|
| **① 权威源码** | `src/*.wsv` | ✅ 改这里 |
| **② 生成 C++** | `generated-cpp/` | 只读对照 |
| **③ 中间产物** | `linker/out/` | 勿发布 |
| **④ 运行成品** | Releases x64 zip | 下载即用 |

```
src/*.wsv → project/ ≡ generated-cpp/ → linker/out/ → AI浏览器.exe
  ① 改这里      ② 对照                  ③ 勿发布        ④ 给用户
```

**二次开发、提 PR 请只改 `src/*.wsv`。**

---

## 适用场景

| 场景 | 一句话示例 | 主要工具 |
|------|------------|----------|
| **数据采集** | 「滚动商品列表，采标题价格 JSON」 | `dom_query` / `collect` / `evaluate` |
| **逆向算法** | 「扫描 POST，标出疑似加密字段」 | `reverse_prepare` / `inject` / `network` |
| **定位算法** | 「断点跟到 sign 函数，给源码」 | `debugger_*` |
| **自动填表** | 「登录并导出订单表」 | `fill_*` / `workflow_run` |
| **工作流复用** | 「把这套流程存成 JSON 下次一键跑」 | `workflow_*` |
| **学习参考** | 火山 + FBrowser 集成 MCP 服务 | `src/*.wsv` 源码 |

Cursor / Claude Desktop 浏览器自动化 · 简单 RPA · 网络观察 · Hook + CDP 逆向预备 · 火山开发者参考实现。

---

## 常见问题（FAQ）

**Q：和 Playwright / Puppeteer 有什么区别？**  
A：本项目的 MCP 服务跑在**真实 FBrowser CEF 窗口**里，工具通过 JSON-RPC 暴露给 AI；你不需要在 Agent 里写 Node 浏览器脚本，直接用自然语言驱动 217 个已封装工具。

**Q：安全吗？会暴露到外网吗？**  
A：默认绑定 `127.0.0.1:9222`，仅本机可访问。详见 `mcp_config.json` 与配置说明书。

**Q：网络层能抓 POST body 吗？**  
A：默认 MCP 网络工具**不记录 POST 正文**；需持久 Hook（`browser_inject`），见 `skills/场景与Hook测试.md`。

**Q：必须会火山编程才能用吗？**  
A：**不需要。** 下载 Release、接入任意 MCP AI 代理即可。火山 IDE 仅在你需要改 `.wsv` 源码时需要。

**Q：真的不用写脚本吗？一句话就够？**  
A：终端用户配置好 Cursor + exe 后，**描述目标即可**（采集/逆向/填表等）。Agent 会自动选 MCP 工具并逐步执行。复杂固定流程可另存 `workflows/*.json`；深度逆向可参考 `scenarios/douyin_xhr_encrypt_scan.js`。

**Q：采集时 AI 说成功了但数据是空的？**  
A：常见原因：页面需登录、列表懒加载未滚动、选择器不对。可让 AI 先 `browser_dom_query` 试探，或明确说「滚动加载 N 屏后再采」。

**Q：逆向和定位有什么区别？**  
A：**逆向**侧重找「哪个请求/字段被加密、body 长什么样」（Hook + 网络对比）；**定位**侧重找「加密逻辑在哪个 JS 函数」（CDP 断点 + 栈 + 源码）。

---

## 链接

| 资源 | URL |
|------|-----|
| **GitHub 仓库** | https://github.com/AI-XiaoDao/ai-browser-mcp |
| **v2.6.0 Release** | https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0 |
| **客户使用手册** | 仓库 `CEFbro/AI浏览器/docs/客户使用手册.md` |
| **217 工具参考** | 仓库 `CEFbro/AI浏览器/skills/AI浏览器MCP.md` |
| **火山编程交流群** | https://qm.qq.com/q/Hpv6qm8qUE |

---

## 技术支持

QQ：**212577526** · QQ群：**737680767** · 微信：**XSMZAS1**

欢迎 Star ⭐ · Issue · PR（核心 `.wsv` 请附测试说明）

---

*AI浏览器 MCP Server v2.6.0 · MIT License · 内核 FBrowser CEF · 端口 9222*

---

## 📰 公众号 / 知乎 · 长文（复制即用）

**标题建议**：《AI浏览器 MCP 正式开源：让 Cursor 用自然语言操控 Windows 真实浏览器》

---

### 前言

做浏览器自动化，很多人第一反应是 Playwright 或 Puppeteer——要写脚本、管环境、还要让 AI Agent 自己拼代码。  
**AI浏览器 MCP Server** 换了一条路：在 Windows 上跑一个带 FBrowser CEF 的真实浏览器，对外暴露 **Model Context Protocol (MCP)** 接口，把 **217 个**常用操作封装成 `browser_*` 工具。你在 **任意 AI 代理**（Cursor、Claude、自研 MCP 客户端）里说一句话，AI 直接调工具，不用从零写自动化脚本。

项目已 **MIT 开源**，源码、文档、桥接脚本齐全，运行包可从 GitHub Releases 免费下载。

---

### 它能做什么？（核心优点）

**对 AI / Agent**

- **217 个 MCP 工具**，Cursor 里说一句话即可导航、填表、读 DOM、抓网络  
- **sync-wait**：同一次调用内等待 DOM/标题/JS 结果，编排更简单  
- **batch + 工作流 JSON**：多步骤任务可批量、可版本管理  
- **语义失败检测**：找不到元素时明确 `success:false`，减少 AI 误判  

**浏览器能力**

- **FBrowser CEF 真实窗口**，非纯无头，行为更贴近用户环境  
- 填表 API、JS 执行、网络 collect、事件 Hook  
- **CDP 调试器**：断点、单步、资源拦截、指纹 — **Release 下载包全部包含**

**三句话场景（复制到 AI 代理）**

| 场景 | 示例话术 |
|------|----------|
| **采集数据** | 「滚动加载商品列表，把标题、价格、链接采成 JSON」 |
| **逆向算法** | 「扫描 POST 请求，标出疑似加密字段；Hook fetch 抓 body」 |
| **定位算法** | 「提交时下断点，定位 sign 在哪个 JS 函数，给我源码片段」 |
| **自动填表** | 「登录后台，导出订单表前 20 行」 |
| **工作流** | 「把登录→采集流程存成 JSON 并跑一遍」 |

说目标即可 — AI 自动选 `browser_navigate` → `browser_collect` / `browser_inject` → `browser_debugger_*` 等工具链，无需手写 Playwright。

**以前 vs 现在**

| 任务 | 以前 | 现在 |
|------|------|------|
| 采列表 | 写 Playwright 选择器 + 循环 | 一句话 + Agent 调 MCP |
| 找加密字段 | 手动 DevTools Hook | 一句话 + `inject` Hook |
| 找 sign 函数 | 手动断点跟栈 | 一句话 + `debugger_*` 编排 |

**集成与安全**

- **MCP 标准** + WebSocket / HTTP 双通道；`mcp_bridge.js` 接 Cursor  
- 默认 **127.0.0.1:9222** 本机绑定；欢迎页控制台 + 在线文档  
- **MIT 开源**：`.wsv` 源码、`generated-cpp` 对照、技能书、全量测试  

完整优点表见 GitHub README「核心优点（全景）」章节。

---

### 3 步上手

1. 下载 Release：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0  
   解压 **AI-Browser-MCP-x64-v2.6.0.zip**，运行 **AI浏览器.exe**  
2. 浏览器打开 http://127.0.0.1:9222/health ，看到 `"status":"ok"`  
3. 在 Cursor 里配置 `mcp_bridge.js`（解压目录内与 exe 同级），详见仓库 **OPEN_SOURCE.md**

然后对 AI 说一句话即可 — 例如：「滚动商品列表，把标题价格采成 JSON」或「扫描 POST 标出加密字段」。更多话术见 [典型场景](README.md#-典型场景一句话自动执行)。

---

### 开源了什么？

| 类型 | 说明 |
|------|------|
| `.wsv` 源码 | 11 个火山源文件，**权威源码**，欢迎 PR |
| 生成 C++ | `generated-cpp/`，编译对照，自动生成 |
| 文档 | 客户手册、217 工具参考、Agent 技能书 |
| 脚本 | `mcp_bridge.js` 桥接 Cursor，`run_all_tests.js` 测试 |

**exe 和 CEF 运行时**在 Releases 下载（约 157MB），不进 Git 仓库体积。

> 常见误解：`linker/out/` 里是 `.obj` 中间文件，**不是 C++ 源码**；真正的生成 C++ 在 `generated-cpp/` 或 cpp zip 里。

---

### 适合谁？

- 用 **Cursor / Claude** 做浏览器自动化的开发者  
- 不想维护 Playwright 脚本链的 Agent 玩家  
- **火山视窗 + FBrowser** 学习者（完整 MCP 服务参考实现）

---

### 链接与支持

- GitHub：https://github.com/AI-XiaoDao/ai-browser-mcp  
- QQ：212577526 · 群：737680767 · 微信：XSMZAS1  
- 英文公告：[OPEN_SOURCE_EN.md](OPEN_SOURCE_EN.md)

**欢迎 Star ⭐ 与 Issue 反馈。**

---

## 🔥 火山视窗论坛 · 专帖（复制即用）

**标题建议**：【开源】AI浏览器 MCP Server v2.6 — 217 工具 · FBrowser CEF · Cursor 桥接

```
各位火山开发者好，

基于火山视窗 + FBrowser CEF 的 MCP 浏览器自动化服务现已 MIT 开源。

【项目】AI Browser MCP Server v2.6.0
【仓库】https://github.com/AI-XiaoDao/ai-browser-mcp
【成品】https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0

【技术栈】
· 源码：火山 .wsv（11 个 MCP 模块，~2 万行）
· 内核：FBrowser CEF
· 协议：MCP JSON-RPC，WebSocket + HTTP POST，端口 9222
· 桥接：Node mcp_bridge.js → Cursor / Claude

【开源内容】
· src/*.wsv — 权威源码
· generated-cpp/release-x64/ — 编译生成的 C++ 对照（33 cpp + 218 h）
· docs / skills / workflows / 全量测试脚本

【编译说明】
打开 AI浏览器.vprj → Release x64 → 产物在 _int/.../linker/
注意：linker/out/ 是 .obj 中间产物，不是 C++ 源码；C++ 在 project/ 或仓库 generated-cpp/

【适合】
· 学习火山 + FBrowser 集成 MCP 服务
· Cursor Agent 浏览器自动化 — 一句话：采集 / 逆向 / 定位 sign 算法
· 工作流 JSON、Hook、CDP 调试扩展

欢迎 Star、Issue、PR。QQ：212577526 · 群：737680767
```

---

## 📺 B 站 / 视频简介（复制即用）

```
AI浏览器 MCP Server 开源啦｜Cursor 一句话操控 Windows 真实浏览器

217 MCP 工具｜采集数据 · 逆向 POST · CDP 定位 sign｜FBrowser CEF｜MIT

说目标 AI 自己跑：不用写 Playwright，Agent 自动串联 navigate/collect/inject/debugger

下载：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
仓库：https://github.com/AI-XiaoDao/ai-browser-mcp
文档：见仓库 OPEN_SOURCE.md

#Cursor #MCP #浏览器自动化 #数据采集 #逆向 #火山编程 #FBrowser #开源
```

---

## 📱 微信朋友圈 · 短文案（复制即用）

```
【开源】AI浏览器 MCP v2.6 — Cursor 一句话操控真实浏览器

✅ 217 工具 · 本机 9222 · MIT
✅ 采集数据 / 逆向 POST / 定位 sign — AI 自己跑 · **下载即全功能**
✅ Windows exe 下载即用

github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 📑 宣传材料索引

| 场景 | 文件 / 章节 |
|------|-------------|
| **各大论坛发帖（中文）** | **[FORUM_POSTS.md](FORUM_POSTS.md)** — V2EX / 掘金 / CSDN / 知乎 / 看雪 等 |
| **Forum posts (English)** | **[FORUM_POSTS_EN.md](FORUM_POSTS_EN.md)** — Reddit / HN / Dev.to / Twitter 等 |
| **Discuz (DZ) BBCode** | **[FORUM_POSTS.md §2-A](FORUM_POSTS.md#2-a-discuz-dz-论坛--bbcode-格式)** |
| QQ 群 / 论坛短帖 | 本文「论坛短帖」 |
| **典型话术（采集/逆向/定位）** | 本文「典型话术 · 一句话自动执行」 |
| **全部优点长帖** | 本文「全部优点 · 长帖」 |
| 公众号 / 知乎长文 | 本文「公众号长文」 |
| 火山开发者论坛 | 本文「火山视窗论坛专帖」 |
| B 站 / 视频简介 | 本文「B 站简介」 |
| 微信朋友圈 | 本文「朋友圈 · 短文案」 |
| **场景速查卡** | 本文「场景速查卡」 |
| Twitter / X | 本文「Twitter / X」 |
| Reddit | 本文「Reddit」 |
| 知乎 / 即刻短答 | 本文「知乎 / 即刻」 |
| 英文社区 | [OPEN_SOURCE_EN.md](OPEN_SOURCE_EN.md) |
| 贡献与发版 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| GitHub Issue / PR | [.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE/) |
| Discussions 置顶帖 | [.github/SOCIAL_PREVIEW.md](.github/SOCIAL_PREVIEW.md) |
| Social Preview 出图 | [.github/SOCIAL_PREVIEW.md](.github/SOCIAL_PREVIEW.md) |
| 安全报告 | [SECURITY.md](SECURITY.md) |
| 更新日志 | [CHANGELOG.md](CHANGELOG.md) |
| 行为准则 | [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) |

