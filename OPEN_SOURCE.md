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
1. 下载 Release 或编译 release/linker + AI浏览器.exe
2. 启动 AI浏览器.exe → 访问 http://127.0.0.1:9222/health
3. Cursor 配置 mcp_bridge.js（见 README）
4. 对 AI 说：「打开 https://example.com 并读标题」
```

---

## 仓库包含什么？

- **`CEFbro/AI浏览器/src/`** — 火山 MCP 服务完整源码（~2 万行 `.wsv`）
- **`release/linker/`** — 成品配置包（桥接脚本、文档、工作流、mcp_config）
- **`docs/` + `skills/`** — 客户手册、配置说明、217 工具参考
- **`run_all_tests.js`** — 顺序全量 MCP 测试

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
- **文档**：仓库内 `docs/客户使用手册.md`
- **Issues / Star**：欢迎反馈与收藏

---

## 技术支持

QQ：212577526 · QQ群：737680767 · 微信：XSMZAS1

---

*AI浏览器 MCP Server v2.6 · MIT License · 基于 FBrowser CEF*
