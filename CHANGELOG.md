# 更新日志

本文件记录面向用户的版本变更。发版流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [2.8.0] - 2026-06-28

### 新增

- **268 个 MCP 工具**（从 v2.6.1 的 243 增至 268）：43 个 CDP 逆向工具 + 7 反检测工具 + HAR 导出 + retry + workflow 条件变量 + resources/prompts 协议
- **mcp_bridge.js 全量工具模式**：移除 Cursor 白名单过滤限制，所有 268 工具动态展示

### 修复

- **browser_navigate / browser_reload `wait_for_load` 超时**：`注册加载等待任务` 缺少 `start_time` 导致 mcp_result 状态机立即判定超时（取启动时间() - 0 >= 30000 → true）。新增 `start_time` + `_event_driven` 标记，事件驱动任务由 `解析等待任务` 在 OnLoadEnd 回调中解析，避免轮询状态机假阳性

### 变更

- MCP 版本号 `MCP_版本号` → `"2.8.0"`
- 开源文档全量更新：版本号 2.6.x → 2.8.0，工具数 217/234/243 → 268

---

## [2.6.0] - 2026-06-21

### 新增

- **217 个 MCP 工具**：导航、填表、DOM、网络、工作流、CDP 调试等
- **双通道 JSON-RPC**：WebSocket + HTTP POST `/mcp`
- **sync-wait**：同步等待 DOM / 标题 / JS 结果
- **欢迎页控制台**：`http://127.0.0.1:9222/`
- **Cursor 桥接**：`mcp_bridge.js` stdio ↔ HTTP（自动修复 Cursor 协议版本 / JSON-RPC id / schema）
- **GitHub 开源**：`.wsv` 源码、`generated-cpp/` C++ 对照、完整文档与技能书
- **场景脚本**：`verify_cursor_tools.js`（Cursor 握手自检）、`baidu_search_params_analyze.js`

### 变更

- 同步 Release x64 编译产物至 `release/linker/`、`generated-cpp/release-x64/`
- 精简 MCP Stdio 模块；优化 Server/Core/Callbacks 分派与事件 Hook
- 移除冗余宣传/论坛文案文件（`FORUM_POSTS*`、`promo.*`、根目录 PDF/Word 等），保留 README 演示截图

### 发布包

| 文件 | 说明 |
|------|------|
| GitHub Release x64 | 运行成品 (exe + CEF，~157 MB) |
| GitHub Release win32 | 32 位运行成品 (exe + CEF，~136 MB) |
| GitHub Release cpp | 火山生成 C++ 对照（x64 / win32） |

### 说明

- 嵌入式 GUI 模式下 4 个窗口类工具（create/close/create_background/create_tab）已禁用
- **GitHub Release zip** 包含全部 217 个工具（截图、CDP、调试器、指纹、拦截等），解压即用

[2.6.0]: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
