# 更新日志

本文件记录面向用户的版本变更。发版流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

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
| GitHub Release | 运行成品 (exe + CEF，见 Releases 页面) |
| GitHub Release | 火山生成 C++ 对照 (见 Releases 页面) |

### 说明

- 嵌入式 GUI 模式下 4 个窗口类工具（create/close/create_background/create_tab）已禁用
- **GitHub Release zip** 包含全部 217 个工具（截图、CDP、调试器、指纹、拦截等），解压即用

[2.6.0]: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
