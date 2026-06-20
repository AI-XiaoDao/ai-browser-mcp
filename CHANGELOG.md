# 更新日志

本文件记录面向用户的版本变更。发版流程见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 `release/pack-release.ps1`。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [2.6.0] - 2026-06-20

### 新增

- **217 个 MCP 工具**：导航、填表、DOM、网络、工作流、CDP 调试等
- **双通道 JSON-RPC**：WebSocket + HTTP POST `/mcp`
- **sync-wait**：同步等待 DOM / 标题 / JS 结果
- **欢迎页控制台**：`http://127.0.0.1:9222/`
- **Cursor 桥接**：`mcp_bridge.js` stdio ↔ HTTP
- **GitHub 开源**：`.wsv` 源码、`generated-cpp/` C++ 对照、完整文档与技能书

### 发布包

| 文件 | 说明 |
|------|------|
| `AI-Browser-MCP-x64-v2.6.0.zip` | 运行成品（exe + CEF，不含 `out/`） |
| `AI-Browser-MCP-cpp-x64-v2.6.0.zip` | 火山生成 C++ 对照 |

### 说明

- 嵌入式 GUI 模式下 4 个窗口类工具（create/close/create_background/create_tab）已禁用
- VIP 功能（截图、CDP 深度、指纹等）需 FBrowser VIP 授权码

[2.6.0]: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
