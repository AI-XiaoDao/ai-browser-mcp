# 🎉 AI浏览器 MCP Server 正式开源

> 可直接复制到 GitHub、论坛、QQ 群、公众号。  
> 仓库：https://github.com/AI-XiaoDao/ai-browser-mcp

---

## 📋 论坛 / 群公告 · 短帖（复制即用）

```
【开源】AI浏览器 MCP Server v2.6.0 — Windows 本地浏览器自动化 MCP 服务

让 Cursor / Claude 用自然语言操控真实浏览器：217 个 browser_* 工具，导航/填表/读 DOM/抓网络/工作流/CDP 断点。

✅ 已开源：火山 .wsv 源码 + 生成 C++ 对照 + 文档/桥接脚本（MIT）
✅ 成品下载：GitHub Releases（exe + CEF，约 157MB）
✅ 本机 127.0.0.1:9222，默认不暴露外网

下载：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
  · AI-Browser-MCP-x64-v2.6.0.zip      — 运行包
  · AI-Browser-MCP-cpp-x64-v2.6.0.zip  — 火山生成 C++ 对照（可选）

Star / Issue 欢迎：https://github.com/AI-XiaoDao/ai-browser-mcp
QQ：212577526 · 群：737680767
```

---

## 一句话介绍

**AI浏览器 MCP Server** —— 基于火山视窗 + FBrowser CEF 的 **Windows 本地浏览器自动化 MCP 服务**。启动 exe 后，Cursor / Claude 通过 `mcp_bridge.js` 调用 **217 个** `browser_*` 工具，完成导航、填表、读 DOM、网络观察、工作流编排、CDP 断点等任务。

---

## 为什么开源？

| 动机 | 说明 |
|------|------|
| **降低门槛** | 无需从零写 Playwright/Puppeteer；MCP 工具已封装，AI 直接调用 |
| **可审计** | `.wsv` 源码 + 生成 C++ 对照公开，协议与工具行为透明 |
| **可扩展** | 工作流 JSON、Hook 场景、`run_all_tests.js` 均可二次开发 |
| **国内友好** | FBrowser CEF 内核，Windows 原生，默认仅监听 `127.0.0.1` |

---

## 核心亮点

| 亮点 | 说明 |
|------|------|
| **217 MCP 工具** | `browser_navigate` / `browser_fill_click` / `browser_network` / `workflow_run` … |
| **双通道 JSON-RPC** | WebSocket + HTTP POST `http://127.0.0.1:9222/mcp` |
| **sync-wait** | 同步等待 DOM / 标题 / JS 结果，便于 Agent 编排 |
| **工作流** | `linker/workflows/*.json`，一键 `workflow_run` |
| **欢迎页控制台** | `http://127.0.0.1:9222/` — 健康检查、复制 Cursor 配置、浏览文档 |
| **VIP 进阶** | 截图、CDP、指纹、资源拦截等（需 VIP 授权码） |

> **说明**：`browser_create` / `browser_close` / `browser_create_background` / `browser_create_tab` 共 4 个 GUI 窗口类工具在嵌入式 GUI 模式下**已禁用**，由主窗口自动管理浏览器实例。

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
5. 对 AI 说：「打开 https://example.com 并读取标题」
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

### ❌ 不在 Git 仓库内

| 内容 | 获取方式 |
|------|----------|
| `AI浏览器.exe` + CEF 运行时 | Releases → `AI-Browser-MCP-x64-v2.6.0.zip` |
| C++ zip（与 `generated-cpp/` 相同） | Releases → `AI-Browser-MCP-cpp-x64-v2.6.0.zip` |
| FBrowser CEF 闭源库 | 安装 [火山视窗 IDE](https://www.voldp.com/) 时自带 |
| `linker/out/` | **不存在于 Release** — 仅为本地 `.obj`/`.pch`，不是源码 |

---

## 源码与编译目录（`.wsv` vs C++ vs `out/`）

完整说明见仓库 [README · 开源范围与火山编译目录](https://github.com/AI-XiaoDao/ai-browser-mcp#-开源范围与火山编译目录)。核心对照：

| 层级 | 路径 | 能否改 | Release |
|:--:|------|:--:|:--:|
| **① 权威源码** | `src/*.wsv` | ✅ | — |
| **② 生成 C++** | `generated-cpp/` = 编译时 `project/` | ❌ 只读 | cpp zip |
| **③ 中间产物** | `linker/out/`（`.obj`/`.pch`） | ❌ | **不含** |
| **④ 运行成品** | `linker/` 除 `out/` | — | x64 zip |

```
src/*.wsv → project/ ≡ generated-cpp/ → linker/out/ → AI浏览器.exe
  ① 改这里      ② 对照                  ③ 勿发布        ④ 给用户
```

**二次开发、提 PR 请只改 `src/*.wsv`。**

---

## 适用场景

- Cursor / Claude Desktop **浏览器自动化**
- 表单批量录入、信息采集、简单 RPA
- 网络请求观察（`browser_network` / `browser_collect`）
- 接口逆向预备（Hook + `browser_debugger_*` 工作流）
- 火山视窗 + FBrowser 开发者参考实现

---

## 常见问题（FAQ）

**Q：和 Playwright / Puppeteer 有什么区别？**  
A：本项目的 MCP 服务跑在**真实 FBrowser CEF 窗口**里，工具通过 JSON-RPC 暴露给 AI；你不需要在 Agent 里写 Node 浏览器脚本，直接用自然语言驱动 217 个已封装工具。

**Q：安全吗？会暴露到外网吗？**  
A：默认绑定 `127.0.0.1:9222`，仅本机可访问。详见 `mcp_config.json` 与配置说明书。

**Q：网络层能抓 POST body 吗？**  
A：默认 MCP 网络工具**不记录 POST 正文**；需持久 Hook 或 VIP 拦截，见 `skills/场景与Hook测试.md`（技能书目录）。

**Q：必须会火山编程才能用吗？**  
A：**不需要。** 终端用户下载 Release、配置 Cursor 即可。火山 IDE 仅在你需要改 `.wsv` 源码或自行编译时需要。

**Q：VIP 是什么？**  
A：截图、CDP 深度调试、指纹/代理/资源拦截等进阶能力需 FBrowser VIP 授权码，基础 217 工具中的大部分无需 VIP。

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
**AI浏览器 MCP Server** 换了一条路：在 Windows 上跑一个带 FBrowser CEF 内核的真实浏览器，对外暴露 **Model Context Protocol (MCP)** 接口，把 **217 个**常用操作封装成 `browser_*` 工具。你在 **Cursor** 里说一句话，AI 直接调工具，不用从零写自动化脚本。

项目已 **MIT 开源**，源码、文档、桥接脚本齐全，运行包可从 GitHub Releases 免费下载。

---

### 它能做什么？

- **打开网页、读标题、读 DOM** — 信息采集  
- **自动填表、点击** — 登录、录入、简单 RPA  
- **网络请求列表** — 观察 URL、状态码（POST 正文需 Hook，见 FAQ）  
- **工作流 JSON** — 多步骤任务一键 `workflow_run`  
- **VIP 进阶** — 截图、CDP 断点、指纹、资源拦截（需授权码）

默认监听 **127.0.0.1:9222**，仅本机访问，适合本地 Agent 场景。

---

### 3 步上手

1. 下载 Release：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0  
   解压 **AI-Browser-MCP-x64-v2.6.0.zip**，运行 **AI浏览器.exe**  
2. 浏览器打开 http://127.0.0.1:9222/health ，看到 `"status":"ok"`  
3. 在 Cursor 里配置 `mcp_bridge.js`（解压目录内与 exe 同级），详见仓库 **OPEN_SOURCE.md**

然后对 AI 说：「打开 https://example.com 并读取标题」—— 即可体验。

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
· Cursor Agent 浏览器自动化
· 工作流 JSON、Hook、CDP 调试扩展

欢迎 Star、Issue、PR。QQ：212577526 · 群：737680767
```

---

## 📺 B 站 / 视频简介（复制即用）

```
AI浏览器 MCP Server 开源啦｜让 Cursor 用自然语言操控 Windows 真实浏览器

217 个 MCP 工具｜FBrowser CEF 内核｜本机 9222 端口｜MIT

下载：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
仓库：https://github.com/AI-XiaoDao/ai-browser-mcp
文档：见仓库 OPEN_SOURCE.md

#Cursor #MCP #浏览器自动化 #火山编程 #FBrowser #开源
```

---

## 📑 宣传材料索引

| 场景 | 文件 / 章节 |
|------|-------------|
| QQ 群 / 论坛短帖 | 本文「论坛短帖」 |
| 公众号 / 知乎长文 | 本文「公众号长文」 |
| 火山开发者论坛 | 本文「火山视窗论坛专帖」 |
| B 站 / 视频简介 | 本文「B 站简介」 |
| 英文社区 | [OPEN_SOURCE_EN.md](OPEN_SOURCE_EN.md) |
| 贡献与发版 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| GitHub Issue / PR | [.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE/) |
| Discussions 置顶帖 | [.github/SOCIAL_PREVIEW.md](.github/SOCIAL_PREVIEW.md) |
| Social Preview 出图 | [.github/SOCIAL_PREVIEW.md](.github/SOCIAL_PREVIEW.md) |
| 安全报告 | [SECURITY.md](SECURITY.md) |
| 更新日志 | [CHANGELOG.md](CHANGELOG.md) |
| 行为准则 | [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) |

