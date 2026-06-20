# 各大论坛发帖文案 · AI浏览器 MCP Server v2.6

> **用途**：复制粘贴到 QQ 群、火山论坛、V2EX、掘金、知乎、Reddit 等，宣传开源项目。  
> **仓库**：https://github.com/AI-XiaoDao/ai-browser-mcp  
> **下载**：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0  
> **演示图**（外链可用）：https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/.github/demo-douyin-post-scan.png  
> **技术支持**：作者 QQ 212577526

---

## 📑 平台索引（点章节复制）

| 平台 | 章节 | 建议形式 |
|------|------|----------|
| **通用纯文本（全平台）** | **[§0](#0-通用发帖文字全平台--复制即用)** | **首选复制** |
| QQ / Telegram 群公告 | [§1](#1-qq--telegram-群公告) | 短帖 |
| 火山视窗论坛 | [§2](#2-火山视窗论坛) | 专帖 |
| **Discuz (DZ) BBCode** | **[§2-A](#2-a-discuz-dz-论坛--bbcode-格式)** | **纯 BBCode 复制** |
| V2EX | [§3](#3-v2ex) | 分享帖 |
| 掘金 | [§4](#4-掘金) | 文章 / 沸点 |
| CSDN | [§5](#5-csdn) | 博客 |
| 知乎 | [§6](#6-知乎) | 回答 / 文章 |
| 即刻 | [§7](#7-即刻) | 动态 |
| 吾爱破解 | [§8](#8-吾爱破解) | 工具发布 |
| 看雪论坛 | [§9](#9-看雪论坛) | 逆向向 |
| Linux.do | [§10](#10-linuxdo) | 分享 |
| 百度贴吧 | [§11](#11-百度贴吧) | 主楼 |
| 微信公众号 | [§12](#12-微信公众号) | 长文 |
| 微信朋友圈 | [§13](#13-微信朋友圈) | 短文案 |
| B 站 | [§14](#14-b-站) | 简介 / 动态 |
| Twitter / X | [§15](#15-twitter--x) | 推文 |
| Reddit | [§16](#16-reddit) | 帖子 |
| Hacker News | [§17](#17-hacker-news) | Show HN |
| Dev.to | [§18](#18-devto) | 文章 |
| Discord | [§19](#19-discord) | 频道公告 |
| **场景速查卡** | [§20](#20-场景速查卡) | 群精华 |
| **论坛回帖 FAQ** | [§21](#21-论坛回帖-faq) | 评论回复 |

更完整的开源公告与 FAQ 见 [OPEN_SOURCE.md](OPEN_SOURCE.md) · 英文论坛文案见 [FORUM_POSTS_EN.md](FORUM_POSTS_EN.md) · 英文公告 [OPEN_SOURCE_EN.md](OPEN_SOURCE_EN.md)。

---

## §0 通用发帖文字（全平台 · 复制即用）

> **纯文本**，QQ 群 / V2EX / 贴吧 / 知乎 / 火山论坛 均可直接粘贴。  
> **Discuz 论坛**要排版请用 [§2-A BBCode](#2-a-discuz-dz-论坛--bbcode-格式)。  
> **完整 HTML 宣传页**（可本地打开 / 托管 / 论坛外链）：[promo.html](../promo.html)  
> **Word 宣传手册**（高级样式 · 可打印 / 论坛附件）：[AI-Browser-MCP-Promo-v2.6.docx](../AI-Browser-MCP-Promo-v2.6.docx) · 重新生成：`python release/build-promo-docx.py`

**通用标题：**

```
【开源】AI浏览器 MCP Server v2.6 — 217 工具 · 任意 AI 代理 · Windows 本机
```

**通用正文（推荐这一版）：**

```
【开源】AI浏览器 MCP Server v2.6.0

Windows 本地 MCP 浏览器自动化服务。启动 exe 后，本机 9222 端口对外提供标准 MCP 协议；任意 AI 代理（Cursor、Claude、Cline、自研客户端）可调用 217 个 browser_* 工具，操控 FBrowser CEF 真实浏览器。

和 Playwright 脚本链不同：你说目标，Agent 自动选工具、逐步执行，不用从零写自动化代码。

【一句话示例】
· 采集：「滚动商品列表，把标题价格采成 JSON」
· 逆向：「扫描 XHR/fetch POST，标出疑似加密字段」（persist Hook 抓 body）
· 定位：「提交时下断点，跟到 sign 函数，给源码片段」（CDP 调试器）
· 填表：「登录后台，导出订单表」
· 复用：「把流程存成 workflow JSON，下次一键跑」

【亮点】
· 217 工具全开放：导航 / 填表 / DOM / 网络 / 截图 / CDP / Hook / 工作流 …
· MIT 开源：11 个 .wsv 模块 + 文档 + mcp_bridge.js + 场景脚本
· Release 下载即用（约 157MB，含 CEF 运行时）
· sync-wait + batch，Agent 编排更省轮次
· 默认 127.0.0.1，本机运行，数据不出机器

【3 步上手】
1. 下载 Release → 解压 → 运行 AI浏览器.exe
2. 打开 http://127.0.0.1:9222/health 确认 ok
3. 配置 mcp_bridge.js 接入 AI 代理 → 说上面任一句话

下载：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
仓库：https://github.com/AI-XiaoDao/ai-browser-mcp
演示：https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/.github/demo-douyin-post-scan.png

作者 QQ：212577526
欢迎 Star / Issue / PR
```

**超短版（群公告 / 动态）：**

```
【开源】AI浏览器 MCP v2.6 — Windows 本机 217 工具，AI 一句话采集·逆向·断点，MIT 解压即用

https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
作者 QQ：212577526
```

---

## 通用信息块（可拼到任意帖子末尾）

```
项目：AI Browser MCP Server v2.6.0
协议：MIT 开源
平台：Windows 10/11 x64
技术：火山视窗 + FBrowser CEF + MCP JSON-RPC（127.0.0.1:9222）
能力：217 个 browser_* 工具 — 导航/填表/DOM/网络/工作流/CDP 调试/Hook
接入：Cursor · Claude Desktop · Cline · 任意 MCP 客户端 · HTTP POST 直连

下载运行包：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
  AI-Browser-MCP-x64-v2.6.0.zip（~157MB，217 工具全开放，解压即用）

源码仓库：https://github.com/AI-XiaoDao/ai-browser-mcp
作者 QQ：212577526
Star / Issue / PR 欢迎
```

---

## 1. QQ / Telegram 群公告

```
【开源】AI浏览器 MCP Server v2.6 — Windows 本地浏览器自动化

任意 AI 代理（Cursor / Claude / Cline / 自研 MCP）一句话操控真实浏览器：
217 个 browser_* 工具 · 采集 · 逆向 POST · CDP 定位 sign · 自动填表

✅ MIT 开源（.wsv 源码 + 文档 + 桥接脚本）
✅ GitHub Release 下载即用，217 工具全开放
✅ 本机 127.0.0.1:9222，数据不出机器

下载：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
仓库：https://github.com/AI-XiaoDao/ai-browser-mcp

一句话示例：
「打开抖音，扫描 XHR/fetch POST，标出疑似加密字段」
「滚动商品列表，把标题价格采成 JSON」

作者 QQ：212577526
```

---

## 2. 火山视窗论坛

**标题**：【开源】AI浏览器 MCP Server v2.6 — 217 工具 · FBrowser CEF · 任意 AI 代理

```
各位火山开发者好，

基于火山视窗 + FBrowser CEF 的 MCP 浏览器自动化服务现已 MIT 开源，欢迎学习、Star、PR。

【项目】AI Browser MCP Server v2.6.0
【仓库】https://github.com/AI-XiaoDao/ai-browser-mcp
【成品】https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0

【这是什么】
启动 AI浏览器.exe 后，本机暴露 MCP 服务（9222 端口）。
Cursor / Claude / 任意 MCP 客户端可用自然语言调用 217 个 browser_* 工具，
不用从零写 Playwright 脚本。

【一句话场景】
· 采集：「滚动列表，采标题价格 JSON」
· 逆向：「扫描 POST，标出疑似加密字段」（Hook 抓 body）
· 定位：「断点跟到 sign 函数，给源码片段」（CDP 调试器）
· 填表/RPA：「登录后台，导出订单表」

【技术栈】
· 权威源码：src/*.wsv（11 个模块，~2 万行）
· 生成 C++：generated-cpp/release-x64/（33 cpp + 218 h）
· 协议：MCP + JSON-RPC，WebSocket + HTTP POST
· 桥接：mcp_bridge.js → Cursor / Claude Desktop

【开源内容】
· .wsv 源码、generated-cpp 对照、217 工具文档、技能书
· workflows / scenarios / run_all_tests.js 全量测试
· 欢迎 PR（请改 src/*.wsv）

【二次开发】
打开 AI浏览器.vprj → Release x64 → 详见仓库 CONTRIBUTING.md

作者 QQ：212577526
```

> **火山论坛 / 其他 Discuz 站点**：请用下方 [§2-A DZ BBCode 专帖](#2-a-discuz-dz-论坛--bbcode-格式)，粘贴到论坛「高级模式」发帖框。

---

## 2-A. Discuz (DZ) 论坛 · BBCode 格式

> **适用**：Discuz! X / 火山视窗论坛 / 看雪（部分版）/ 各类 `[b][url][img]` 标签站。  
> **用法**：复制下方代码块 **整段** → 论坛发帖 → 切换到 **高级模式 / 纯文本** → 粘贴 → 预览 → 发表。  
> **演示图外链**：`https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/.github/demo-douyin-post-scan.png`

### BBCode 标签速查（发帖常用）

| 效果 | 写法 |
|------|------|
| 粗体 | `[b]文字[/b]` |
| 颜色 | `[color=#0066cc]文字[/color]` |
| 字号 | `[size=4]标题[/size]` |
| 链接 | `[url=https://github.com/...]显示文字[/url]` |
| 图片 | `[img]https://...png[/img]` |
| 代码 | `[code]内容[/code]` |
| 引用 | `[quote]内容[/quote]` |
| 列表 | `[list][*]第一项[*]第二项[/list]` |
| 分割线 | `[hr]` |
| 居中 | `[align=center]内容[/align]` |

---

### DZ · 标题建议

```
【开源】AI浏览器 MCP Server v2.6 — 217 工具 · 任意 AI 代理 · FBrowser CEF
```

或短标题：

```
【开源工具】Windows MCP 浏览器自动化 — Cursor 一句话采集/逆向/断点
```

---

### DZ · 短帖 BBCode（推荐，适合「软件分享」版块）

```
[b][size=4][color=#0066cc]【开源】AI浏览器 MCP Server v2.6.0[/color][/size][/b]

Windows 本地 [b]MCP 浏览器自动化[/b]服务 — [b]217 个[/b] browser_* 工具，[b]任意 AI 代理[/b]（Cursor / Claude / Cline / 自研 MCP）一句话操控 [b]FBrowser CEF 真实浏览器[/b]。

[b]一句话自动执行：[/b]
[list]
[*][b]采集[/b]：「滚动列表，采标题价格 JSON」
[*][b]逆向[/b]：「扫描 POST，标出疑似加密字段」（Hook 抓 body）
[*][b]定位[/b]：「断点跟到 sign 函数，给源码片段」（CDP 调试器）
[*][b]填表[/b]：「登录后台，导出订单表」
[/list]

[b]亮点：[/b]
[list]
[*]MIT 开源：火山 .wsv 源码 + 文档 + mcp_bridge.js
[*]GitHub Release [b]217 工具全开放[/b]，解压即用（约 157MB）
[*]本机 [url=http://127.0.0.1:9222/]127.0.0.1:9222[/url]，默认不暴露外网
[*]sync-wait + batch + 工作流 JSON
[/list]

[b]下载：[/b][url=https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0]GitHub Releases v2.6.0[/url]
[b]仓库：[/b][url=https://github.com/AI-XiaoDao/ai-browser-mcp]github.com/AI-XiaoDao/ai-browser-mcp[/url]

[align=center][img]https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/.github/demo-douyin-post-scan.png[/img][/align]
[i]实测：Cursor 一句话 → 抖音 POST 扫描 + Hook + 分析 33 条请求[/i]

[b]作者 QQ：[/b]212577526

欢迎 [b]Star ⭐[/b] / Issue / PR
```

---

### DZ · 长帖 BBCode（适合「教程 / 综合讨论」版块）

```
[b][size=5][color=#0066cc]AI浏览器 MCP Server 正式开源[/color][/size][/b]
[size=3][color=#666666]任意 AI 代理 · 一句话操控 Windows 真实浏览器 · MIT[/color][/size]

[hr]

[b]一、这是什么？[/b]

在 Windows 上运行 [b]AI浏览器.exe[/b]，本机暴露 [b]Model Context Protocol (MCP)[/b] 服务（端口 [b]9222[/b]）。
不限于 Cursor — Claude Desktop、Cline、OpenCode 或 HTTP POST 脚本均可调用 [b]217 个[/b] browser_* 工具。
说一句话，Agent 自动串联执行，[b]不用手写 Playwright[/b]。

[b]二、核心能力[/b]
[list]
[*][b]217 MCP 工具[/b]：导航 / 填表 / DOM / JS / 网络 / 工作流 / CDP 调试 / Hook / 截图 / 指纹 …
[*][b]sync-wait + batch[/b]：同次调用等结果，批量串联，省 Token
[*][b]工作流 JSON[/b]：多步骤任务 workflow_run 一键复跑
[*][b]真实 CEF 窗口[/b]：FBrowser 内核，行为贴近日常浏览
[*][b]本机优先[/b]：默认 127.0.0.1，数据不出机器
[/list]

[b]三、一句话场景（复制到 AI 代理）[/b]

[quote]
帮我把商品列表滚动 5 屏，把标题、价格、链接采成 JSON。
打开抖音，扫描 XHR/fetch 的 POST，标出疑似加密字段和依据。
提交时下断点，跟到计算 sign 的 JS 函数，给我函数名和源码片段。
用账号登录后台，导出订单表前 20 行。
[/quote]

[b]四、3 步上手[/b]
[list=1]
[*]下载 [url=https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0]AI-Browser-MCP-x64-v2.6.0.zip[/url] → 解压 → 运行 [b]AI浏览器.exe[/b]
[*]浏览器打开 [url=http://127.0.0.1:9222/health]http://127.0.0.1:9222/health[/url] 看到 [code]"status":"ok"[/code]
[*]配置 [b]mcp_bridge.js[/b] 接入 Cursor / Claude → 对 AI 说上面任一句
[/list]

[b]五、开源内容[/b]
[list]
[*][b]src/*.wsv[/b] — 11 个 MCP 模块（~2 万行，MIT）
[*][b]generated-cpp/[/b] — 火山生成 C++ 对照
[*][b]docs / skills[/b] — 217 工具参考、客户手册、场景脚本
[*]欢迎 PR（请改 .wsv 源码）
[/list]

[b]六、演示截图[/b]
[align=center][img]https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/.github/demo-douyin-post-scan.png[/img][/align]

[hr]

[b]链接汇总[/b]
[list]
[*][b]仓库[/b]：[url=https://github.com/AI-XiaoDao/ai-browser-mcp]https://github.com/AI-XiaoDao/ai-browser-mcp[/url]
[*][b]下载[/b]：[url=https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0]v2.6.0 Release[/url]
[*][b]论坛发帖文案[/b]：[url=https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/FORUM_POSTS.md]FORUM_POSTS.md[/url]
[/list]

[b]作者 QQ：[/b]212577526

欢迎 [b]Star ⭐[/b] · Issue · PR
```

---

### DZ · 回帖 FAQ BBCode（评论回复用）

```
[b]Q：和 Playwright 有什么区别？[/b]
A：217 工具已封装成 MCP，AI 代理直接调用，不用在 Agent 里写 Node 浏览器脚本。真实 FBrowser CEF 窗口，本机 9222。

[b]Q：只能 Cursor 吗？[/b]
A：否。任意 MCP 客户端或 HTTP POST [code]127.0.0.1:9222/mcp[/code] 均可。

[b]Q：能抓 POST body 吗？[/b]
A：默认网络工具不记 POST 正文；须 [code]browser_inject[/code] persist Hook。仓库有 [code]douyin_xhr_encrypt_scan.js[/code] 范例。

[b]Q：Mac 支持吗？[/b]
A：当前仅 Windows x64。Release 已含 CEF 运行时。

下载：[url=https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0]点这里[/url]
```

---

### DZ · 发帖注意事项

| 项目 | 建议 |
|------|------|
| 编辑器 | 用 **高级模式**，勿用「可视化」粘贴（易丢标签） |
| 图片 | 外链 `[img]` 若被禁，改用附件上传后 `[attach]id[/attach]` |
| 外链 | 部分论坛需发帖满级才显示链接，可留 `github.com/AI-XiaoDao/ai-browser-mcp` 纯文本 |
| 版块 | 软件分享 / 编程交流 / 资源发布；勿同一内容多版块刷屏 |
| 标签 | `[b]开源[/b]` `[b]MCP[/b]` `[b]Cursor[/b]` `[b]浏览器自动化[/b]` |

---

## 3. V2EX

**节点**：分享创造 / 程序员  
**标题**：[开源] Windows 本地 MCP 浏览器自动化 — 217 工具，Cursor 一句话采集/逆向/断点

```
做了很久的 AI 浏览器 MCP 服务开源了，MIT，跑在 Windows 本机。

和 Playwright 脚本链不同：把 217 个浏览器操作封装成 MCP 工具，Cursor / Claude 里直接说目标，Agent 自己串联 navigate、inject Hook、network、debugger 等。

实测场景：
· 数据采集：滚动懒加载列表 → DOM/collect → JSON
· 逆向：打开抖音，扫描 XHR/fetch POST，标疑似加密字段（须 persist Hook）
· 定位：CDP 断点跟到 sign 计算函数，返回源码片段
· RPA：填表登录 + workflow JSON 固化复用

技术：火山视窗 + FBrowser CEF，127.0.0.1:9222，HTTP/WebSocket 双通道。
Release 约 157MB，解压即用，217 工具全开放。

仓库：https://github.com/AI-XiaoDao/ai-browser-mcp
下载：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0

欢迎 Star / Issue。有演示图在 README（抖音 POST 扫描一句话跑通）。
```

---

## 4. 掘金

**标题**：开源 | 让任意 AI 代理一句话操控 Windows 真实浏览器 — AI Browser MCP v2.6  
**标签**：`MCP` `Cursor` `浏览器自动化` `开源` `Windows`

```
## 背景

做 Agent 浏览器自动化，常见路径是 Playwright + 自己写 MCP 封装。我们换了一种方式：
在 Windows 跑 FBrowser CEF 真实浏览器，对外暴露标准 MCP，预封装 217 个 browser_* 工具。

## 能做什么

| 场景 | 一句话示例 |
|------|------------|
| 采集 | 滚动商品列表，采标题价格 JSON |
| 逆向 | 扫描 POST，标出疑似加密字段 |
| 定位 | 断点跟到 sign 函数，给源码 |
| RPA | 登录后台，导出订单表 |

Agent 自动选工具链，sync-wait 逐步等结果，支持 workflow JSON 复用。

## 3 步上手

1. 下载 Release zip（~157MB）→ 运行 AI浏览器.exe
2. 打开 http://127.0.0.1:9222/health 确认 ok
3. 配置 mcp_bridge.js 接入 Cursor / Claude

## 开源内容

MIT：11 个 .wsv 模块 + generated-cpp 对照 + 完整文档/技能书/测试脚本。

链接：
· 仓库 https://github.com/AI-XiaoDao/ai-browser-mcp
· 下载 https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0

欢迎 Star ⭐
```

**沸点版（更短）**：

```
开源了一个 Windows 本地 MCP 浏览器服务，217 工具，Cursor 一句话采集/逆向/断点定位 sign，不用写 Playwright。

FBrowser CEF 真实窗口 · 127.0.0.1:9222 · MIT

https://github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 5. CSDN

**标题**：【开源】AI Browser MCP Server：217 个 MCP 工具，让 AI 代理自然语言操控 Windows 浏览器  
**分类**：人工智能 / 开发工具  
**标签**：MCP, Cursor, 浏览器自动化, FBrowser, 开源

```
## 项目简介

AI Browser MCP Server 是基于火山视窗 + FBrowser CEF 的 Windows 本地 MCP 服务。
启动 exe 后，Cursor、Claude Desktop 或任意 MCP 客户端可通过 217 个 browser_* 工具完成浏览器自动化。

## 核心特性

- 217 MCP 工具：导航、填表、DOM、JS、网络、工作流、CDP 调试、Hook 等
- sync-wait + batch：Agent 编排更省轮次
- 工作流 JSON：多步骤任务可版本管理
- 本机 127.0.0.1:9222，默认不暴露外网
- MIT 开源：.wsv 源码 + generated-cpp + 文档

## 典型用法（自然语言）

```
帮我把商品列表滚动 5 屏，采标题和价格 JSON。
打开某站，扫描 POST 请求，标出疑似加密字段。
提交表单时下断点，定位 sign 函数并给源码片段。
```

## 快速开始

1. GitHub Releases 下载 AI-Browser-MCP-x64-v2.6.0.zip
2. 解压运行 AI浏览器.exe
3. 配置 mcp_bridge.js 连接 Cursor

仓库：https://github.com/AI-XiaoDao/ai-browser-mcp
Release：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0

欢迎 Star 与 Issue 反馈。
```

---

## 6. 知乎

### 6.1 短回答（复制到「如何用 Cursor 做浏览器自动化」类问题）

```
不用从零写 Playwright。Windows 上跑 AI浏览器 MCP，任意 AI 代理里一句话：

· 采集：「滚动商品列表，采标题价格 JSON」
· 逆向：「扫描 POST，标出疑似加密字段」（须 Hook 抓 body）
· 定位：「提交时下断点，给 sign 函数源码」（CDP 调试器）

217 个 browser_* 工具已封装，Agent 自动串联，MIT 开源，Release 下载 217 工具全开放。

https://github.com/AI-XiaoDao/ai-browser-mcp
```

### 6.2 文章标题建议

《AI浏览器 MCP 开源：任意 AI 代理一句话操控 Windows 真实浏览器》

### 6.3 文章正文

见 [OPEN_SOURCE.md · 公众号/知乎长文](OPEN_SOURCE.md#-公众号--知乎--长文复制即用)（可直接粘贴发布）。

**配图**：插入演示图  
`https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/.github/demo-douyin-post-scan.png`

---

## 7. 即刻

```
开源了一个 Windows MCP 浏览器自动化服务 🚀

Cursor / Claude 一句话：
· 采数据
· 扫 POST 找加密字段
· CDP 断点定位 sign

217 工具 · FBrowser 真实浏览器 · 本机 9222 · MIT

github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 8. 吾爱破解

**标题**：【原创开源】AI Browser MCP — Cursor/AI 一句话操控浏览器（217 工具 · Windows）

```
【软件名称】AI浏览器 MCP Server v2.6
【开发语言】火山视窗 + FBrowser CEF（MCP 服务层 MIT 开源）
【运行环境】Windows 10/11 x64
【软件用途】本地浏览器自动化，供 Cursor / Claude 等 AI 代理调用

【功能摘要】
· 217 个 MCP 工具：导航、填表、读 DOM、网络、截图、CDP 断点、Hook 等
· 自然语言驱动：说目标即可，Agent 自动串联工具
· 本机 127.0.0.1:9222，默认仅本机访问
· 工作流 JSON 多步骤复用

【使用说明】
1. GitHub Releases 下载 AI-Browser-MCP-x64-v2.6.0.zip（~157MB）
2. 解压运行 AI浏览器.exe
3. 安装 Node.js，配置 mcp_bridge.js 接入 Cursor
4. 对 AI 说任务，例如「滚动列表采 JSON」

【开源地址】https://github.com/AI-XiaoDao/ai-browser-mcp
【下载地址】https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0

【声明】MIT 开源 MCP 服务源码；CEF 运行时随 Release 附带。仅供学习与研究，请遵守目标网站 ToS 与当地法律。
```

---

## 9. 看雪论坛

**板块**：软件逆向 / 编程语言  
**标题**：【工具】AI Browser MCP — Hook 抓 POST + CDP 断点定位 sign（MCP 协议 · 开源）

```
分享一个 Windows 本地 MCP 浏览器服务，适合配合 Cursor 做 Web 逆向辅助（非脱壳工具）。

【逆向相关能力】
· browser_inject：persist Hook XMLHttpRequest.send / fetch，抓 POST body
· browser_reverse_prepare：开网络详情 + console，返回逆向指引
· browser_network / browser_collect：请求列表与聚合
· browser_debugger_*：CDP 断点、单步、call stack、script source
· scenarios/douyin_xhr_encrypt_scan.js：抖音 POST 加密字段扫描范例

【典型话术】
「打开某站，扫描 XHR/fetch POST，标出疑似加密字段并说明依据」
「提交时下断点，跟到计算 sign 的 JS 函数，给源码片段」

【说明】
MCP 网络层默认不记录 POST 正文，须 persist Hook。
项目 MIT 开源，.wsv 源码可审计。

仓库：https://github.com/AI-XiaoDao/ai-browser-mcp
下载：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0

演示：README 含抖音 POST 扫描实测截图。
```

---

## 10. Linux.do

**标题**：[开源] AI Browser MCP — Windows 本地 217 工具，Cursor 一句话浏览器自动化

```
虽然名字带 Linux 社区，但这个项目是 Windows 向 😂

开源自研的 MCP 浏览器服务：
· FBrowser CEF 真实窗口（非纯无头）
· 217 browser_* 工具，MCP 标准协议
· Cursor / Claude / HTTP POST 均可接入
· 采集 / Hook 逆向 / CDP 断点 一句话场景

本机 127.0.0.1:9222，MIT，Release 217 工具全开放。

https://github.com/AI-XiaoDao/ai-browser-mcp
https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
```

---

## 11. 百度贴吧

**吧**：cursor吧 / 编程吧 / 浏览器吧  
**标题**：【开源】Windows MCP 浏览器自动化，217 工具，AI 一句话采集逆向

```
【开源】AI浏览器 MCP Server v2.6

Windows 本地跑真实浏览器，Cursor 里一句话自动化：
- 采数据：滚动列表采 JSON
- 逆向：扫 POST 找加密字段
- 定位：断点找 sign 函数

217 工具 · MIT · 下载即用
github.com/AI-XiaoDao/ai-browser-mcp

有问题可留帖，或联系作者 QQ：212577526
```

---

## 12. 微信公众号

**标题**：《AI浏览器 MCP 正式开源：任意 AI 代理一句话操控 Windows 真实浏览器》

正文全文见 [OPEN_SOURCE.md · 公众号长文](OPEN_SOURCE.md#-公众号--知乎--长文复制即用)。

**开头引流段（可单独作摘要）**：

```
做浏览器自动化，还在手写 Playwright？AI Browser MCP Server 换了一条路：
Windows 本地 FBrowser 真实浏览器 + 标准 MCP + 217 个预封装工具。
Cursor / Claude 里说一句话，Agent 自动完成采集、Hook 逆向、CDP 断点定位。

MIT 开源，Release 免费下载，217 工具全开放。
```

**文末引导**：

```
下载：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
文档：回复「MCP」获取快速上手步骤
交流：作者 QQ 212577526
```

---

## 13. 微信朋友圈

```
【开源】AI浏览器 MCP v2.6

Windows 本地浏览器 + 217 MCP 工具
Cursor / Claude 一句话：采集 · 逆向 POST · 断点定位 sign
MIT · 下载即用

github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 14. B 站

### 视频简介

```
AI浏览器 MCP Server 开源｜任意 AI 代理一句话操控 Windows 真实浏览器

217 MCP 工具｜采集 · 逆向 POST · CDP 定位 sign｜FBrowser CEF｜MIT

说目标 AI 自己跑：Agent 自动串联 navigate / inject / network / debugger

下载：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
仓库：https://github.com/AI-XiaoDao/ai-browser-mcp

#Cursor #MCP #浏览器自动化 #数据采集 #逆向 #火山编程 #FBrowser #开源
```

### 动态（短）

```
项目开源啦 ⭐ AI Browser MCP v2.6
217 工具 · 一句话采集/逆向/断点 · Windows 本机
https://github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 15. Twitter / X

**Thread 首条**：

```
[Open Source] AI Browser MCP v2.6 — 217 tools for ANY MCP agent on Windows

One sentence → auto-runs:
· Scrape data from pages
· Reverse POST crypto fields (Hook)
· Locate sign JS via CDP breakpoints

Real FBrowser CEF · Local 127.0.0.1:9222 · MIT

https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
```

**Follow-up（可选）**：

```
Not Cursor-only — Claude Desktop, Cline, OpenCode, or HTTP POST to :9222/mcp

Demo: open douyin.com, scan XHR POST, flag encrypted fields — Agent chains tools automatically.

Star welcome ⭐
```

---

## 16. Reddit

**Subreddit**：r/cursor · r/LocalLLaMA · r/mcp · r/selfhosted

**Title**：`[Release] AI Browser MCP Server v2.6 — local Windows browser automation (217 MCP tools, any agent)`

```
I open-sourced a Windows-native MCP server that wraps a real FBrowser CEF browser with 217 browser_* tools.

Works with Cursor, Claude Desktop, Cline, or any MCP client / raw HTTP POST.

Instead of writing Playwright scripts, describe the goal in plain language:
- "Scroll this list and collect title/price as JSON"
- "Scan XHR/fetch POST and flag encrypted-looking fields"
- "Break on submit and show the JS function that computes sign"

Features: sync-wait, batch calls, workflow JSON, persist Hook, CDP debugger.

Runs locally on 127.0.0.1:9222. MIT license, .wsv source included.
Release zip includes all 217 tools — download and go.

Download: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
Repo: https://github.com/AI-XiaoDao/ai-browser-mcp

Happy to answer questions in comments.
```

---

## 17. Hacker News

**Title**：`Show HN: AI Browser MCP – 217 local browser tools for MCP agents on Windows`

```
Hi HN,

I built an open-source MCP server (MIT) that exposes 217 browser automation tools on Windows using FBrowser CEF.

Any MCP-compatible agent (Cursor, Claude Desktop, custom) can drive a real browser via HTTP/WebSocket on 127.0.0.1:9222.

Typical prompts:
- Scrape lazy-loaded lists to JSON
- Hook XHR/fetch to analyze POST bodies
- CDP breakpoints to locate crypto/sign functions

Source (.wsv + generated C++ reference) and docs are on GitHub. Binary release ~157MB.

https://github.com/AI-XiaoDao/ai-browser-mcp
https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0

Feedback welcome.
```

---

## 18. Dev.to

**Title**：`Open-sourcing AI Browser MCP: 217 tools for local browser automation with any MCP agent`  
**Tags**：`mcp` `cursor` `opensource` `automation` `windows`

```
## TL;DR

Local Windows MCP server + real FBrowser CEF browser + 217 pre-built tools.
Tell your agent what you want; it chains navigate / inject / network / debugger for you.

## Why

Writing Playwright wrappers for every agent workflow is repetitive. This project packages common browser ops as MCP tools with sync-wait, batch, and workflow JSON.

## Quick start

1. Download release zip from GitHub
2. Run AI浏览器.exe
3. Point mcp_bridge.js at Cursor or POST to http://127.0.0.1:9222/mcp

## Open source

MIT — Volcano `.wsv` source, generated C++ reference, docs, test scripts.

Repo: https://github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 19. Discord

**#announcements / #showcase 频道**：

```
📢 **AI Browser MCP Server v2.6 is open source (MIT)**

Windows local browser automation for **any MCP agent** — 217 tools, FBrowser CEF, port 9222.

One-liner scenarios:
• Scrape data → JSON
• Reverse POST fields (Hook)
• CDP breakpoint → sign function source

🔗 Repo: https://github.com/AI-XiaoDao/ai-browser-mcp
⬇ Release: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0

Questions → GitHub Issues · 作者 QQ 212577526
```

---

## 20. 场景速查卡

适合群公告置顶、论坛签名、Notion 笔记：

```
┌─ AI浏览器 MCP · 一句话场景 v2.6 ─────────────┐
│ ① 采集  「滚动列表，采标题价格 JSON」         │
│ ② 逆向  「扫描 POST，标疑似加密字段」         │
│ ③ 定位  「断点跟到 sign 函数，给源码」        │
│ ④ 填表  「登录后台，导出订单表」              │
│ ⑤ 复用  「存 workflow JSON，下次一键跑」      │
├──────────────────────────────────────────────┤
│ 配置：exe + mcp_bridge.js → 127.0.0.1:9222   │
│ 仓库：github.com/AI-XiaoDao/ai-browser-mcp   │
└──────────────────────────────────────────────┘
```

**纯文本版**：

```
AI浏览器 MCP · 一句话场景 v2.6

① 采集  「滚动列表，采标题价格 JSON」        → dom_query / collect
② 逆向  「扫描 POST，标疑似加密字段」        → inject Hook + network
③ 定位  「断点跟到 sign 函数，给源码」       → debugger_*
④ 填表  「登录后台，导出订单表」             → fill_* / workflow
⑤ 复用  「存成 workflow，下次一键跑」       → workflow_*

配置：exe + mcp_bridge.js → 127.0.0.1:9222
仓库：github.com/AI-XiaoDao/ai-browser-mcp
```

---

## 21. 论坛回帖 FAQ

复制到评论回复：

**Q：和 Playwright 有什么区别？**  
A：217 工具已封装成 MCP，AI 代理直接调用，不用在 Agent 里写 Node 浏览器脚本。真实 FBrowser CEF 窗口，本机 9222。

**Q：只能 Cursor 吗？**  
A：否。任意 MCP 客户端（Claude Desktop、Cline 等）或 HTTP POST `127.0.0.1:9222/mcp` 均可。

**Q：安全吗？**  
A：默认仅监听 127.0.0.1，本机访问。详见 mcp_config.json。

**Q：能抓 POST body 吗？**  
A：默认网络工具不记 POST 正文；须 `browser_inject` persist Hook。见 scenarios/douyin_xhr_encrypt_scan.js。

**Q：Mac / Linux 支持吗？**  
A：当前仅 Windows x64。CEF 运行时随 Release 附带。

**Q：要付费吗？**  
A：MIT 开源；GitHub Release zip 217 工具全开放，免费下载使用。

**Q：怎么上手？**  
A：下载 zip → 运行 exe → health 检查 ok → 配置 mcp_bridge.js → 对 AI 说一句话。详见 README。

---

## 发帖小贴士

| 平台 | 建议 |
|------|------|
| 带图帖子 | 用演示图外链（见文首 URL）或上传截图 |
| 技术论坛 | 强调 Hook + CDP + MCP 协议，附仓库链接 |
| 小白社区 | 强调「下载 exe → 配置 Cursor → 说一句话」三步 |
| 英文社区 | 强调 any MCP agent, not Cursor-only |
| 所有平台 | 文末加 Star / Issue 引导；勿刷多个板块同一内容（防删帖） |

---

*AI浏览器 MCP Server v2.6.0 · MIT · 更新同步见 [CHANGELOG.md](CHANGELOG.md)*
