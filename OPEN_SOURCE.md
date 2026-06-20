# 🎉 AI浏览器 MCP Server 正式开源

> 可直接复制到 GitHub Release 说明、论坛帖子、QQ 群公告或公众号。

---

## 一句话介绍

**AI浏览器 MCP Server** —— 基于火山视窗 + FBrowser CEF 的**本地浏览器自动化 MCP 服务**。启动 exe，Cursor 里用自然语言就能操控真实浏览器：**217 个工具**，覆盖导航、填表、网络、工作流、CDP 断点。

---

## 为什么开源？

- **降低门槛**：不想从零写 Playwright/Puppeteer 脚本？MCP 工具已封装好，AI 直接调用。
- **可审计**：火山 `.wsv` 源码公开，MCP 协议与工具行为透明。
- **可扩展**：工作流 JSON、Hook 场景、Node 测试脚本均可二次开发。
- **国内友好**：FBrowser CEF 内核，Windows 原生，本机 `127.0.0.1` 默认不暴露外网。

---

## 核心亮点

| 亮点 | 说明 |
|------|------|
| **217 MCP 工具** | `browser_navigate` / `fill_click` / `network` / `workflow_run` … |
| **双通道 JSON-RPC** | WebSocket + HTTP POST `/mcp` |
| **sync-wait** | 同步等待 DOM/标题/JS 结果，Agent 更好编排 |
| **工作流** | JSON 步骤链，一键 `workflow_run` |
| **欢迎页控制台** | `http://127.0.0.1:9222/` 复制 Cursor 配置、查工具 |
| **VIP 进阶** | 截图、CDP、指纹、资源拦截（需授权码） |

---

## 3 分钟上手

```
1. 下载 Release：https://github.com/AI-XiaoDao/ai-browser-mcp/releases
   文件：AI-Browser-MCP-x64-v2.6.0.zip（约 157MB）
2. 解压 → 双击 AI浏览器.exe → 访问 http://127.0.0.1:9222/health
3. Cursor 配置 mcp_bridge.js（见 README / .mcp.json）
4. 对 AI 说：「打开 https://example.com 并读标题」
```

**环境要求**：Windows x64 · Node.js（Cursor 桥接）· 成品包已含 CEF 运行时

---

## 仓库包含什么？

### ✅ 已开源（Git 仓库内）

| 内容 | 路径 |
|------|------|
| **MCP 服务核心** | `CEFbro/AI浏览器/src/*.wsv`（11 个源文件） |
| **生成 C++ 对照** | `CEFbro/AI浏览器/generated-cpp/release-x64/`（33 cpp + 218 h） |
| 文档 | `CEFbro/AI浏览器/docs/` — 客户手册、配置说明、使用技能书 |
| 工具参考 | `CEFbro/AI浏览器/skills/AI浏览器MCP.md` — 217 工具 |
| Agent 技能书 | `CEFbro/AI浏览器/skills/` — 火山 API 知识库 |
| 桥接与测试 | `mcp_bridge.js`、`mcp_client.js`、`run_all_tests.js` |
| 工作流示例 | `CEFbro/AI浏览器/workflows/`（编译复制到 `linker/workflows/`） |
| 配置包 | `release/linker/` — 脚本/文档/工作流（无 exe） |
| Cursor 示例 | 根目录 `.mcp.json` |
| 许可证 | `LICENSE`（MIT） |

### ❌ 不在仓库内（需另行获取）

| 内容 | 获取方式 |
|------|----------|
| `AI浏览器.exe` + CEF 运行时 | [GitHub Releases](https://github.com/AI-XiaoDao/ai-browser-mcp/releases) → `AI-Browser-MCP-x64-v2.6.0.zip` |
| C++ 源码 zip（可选） | 同上 → `AI-Browser-MCP-cpp-x64-v2.6.0.zip` |
| FBrowser CEF 闭源库 | 安装火山视窗 IDE 时自带 |
| `linker/out/` 中间产物 | **勿下载、勿提交** — 仅为 `.obj`/`.pch`，不是源码 |

---

## 源码说明：`.wsv` vs C++ vs `out/`

**本项目的「源码」指火山视窗 `.wsv` 文件**，不是 MSVC 生成的 C++。

编译 Release x64 后，火山 IDE 在 `_int/AI浏览器/release/x64/` 产出：

| 目录 | 性质 | 是否入 Git |
|------|------|------------|
| **`project/`** / **`generated-cpp/`** | 火山**自动生成**的 C++（`vpkg_*.cpp`、`vcls_*.h`） | ✅ 已入仓 |
| **`linker/`** | **运行成品**（exe、dll、docs、mcp 脚本） | ❌ 大二进制走 Releases |
| **`linker/out/`** | 编译**中间产物**（`.obj`、`.pch`），**不是 C++ 源码** | ❌ 禁止打包 |

```
src/*.wsv  ──火山翻译──►  project/*.cpp  ──MSVC──►  linker/out/*.obj  ──链接──►  linker/AI浏览器.exe
  ↑开源主体              ↑自动生成 C++              ↑中间产物（约 400MB）
```

二次开发、Code Review、提 PR 请以 **`CEFbro/AI浏览器/src/`** 为准。

---

## 适用场景

- Cursor / Claude Desktop **浏览器自动化**
- 表单批量录入、信息采集
- 网络请求观察（list / collect）
- 接口逆向预备（Hook + debugger 工作流）
- 火山 + FBrowser 开发者参考实现

---

## 链接

- **仓库**：https://github.com/AI-XiaoDao/ai-browser-mcp
- **成品下载**：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
- **文档**：仓库内 `CEFbro/AI浏览器/docs/客户使用手册.md`
- **Issues / Star**：欢迎反馈与收藏

---

## 技术支持

QQ：212577526 · QQ群：737680767 · 微信：XSMZAS1

---

*AI浏览器 MCP Server v2.6.0 · MIT License · 基于 FBrowser CEF*
