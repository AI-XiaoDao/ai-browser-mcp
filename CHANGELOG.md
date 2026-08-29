# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与语义化版本（[SemVer](https://semver.org/lang/zh-CN/)）。

## [v3.1.0] - 2026-08-29

### 新增
- 内核层能力扩展：自定义协议 `mcp://`、证书管理、HTTP 认证注入、下载控制、IPC 双向通道、CDP 事件监控、事件反应器、定时监视、一键全事件流、动态插桩/调用追踪/算法 Hook/源码提取/全局变量追踪、右键菜单拦截
- 原生 MCP stdio 直连模式（`--mcp-stdio`，零 Node 依赖，帧格式自适应：官方换行分隔 / 兼容 Content-Length）
- 全功能免 VIP：`FBrowser初始化控制.是否为VIP = 真` 强制解锁，成品对所有用户开放全部 265 工具

### 修复
- MCP 协议标准合规：`id:0` 正确响应、响应 id 类型保真、移除 `_req_id` 扩展字段（通过官方 SDK 1.30.0 严格校验）
- stdio 实例与常驻实例共存时的 CEF 缓存文件锁互斥崩溃（独立缓存目录 `GlobalData_Stdio`）
- debugger 参数校验防 CDP 队列堵塞、导航规则锁/原子维护竞态、HTTP POST 体上限、日志截断合法 JSON

### 变更
- 工具数统一口径：265
- 版本号 / FileVersion 统一 3.1.0

## [v3.0.0] - 2026-08

### 新增
- MCP_Kernel 内核分派模块、方案资源处理器、事件监控系统、工作流引擎
- 逆向分析工具套件（hook/trace/algo/functions/sources/watch_global）

### 修复
- 大量稳定性修复（详见 Release Notes）

## [v2.8.x] - 2026-07

### 新增
- 断点调试引擎（debugger_flow 一键断点）、指纹伪装 30+ 维度、网络拦截流式引擎
- 工作流 JSON 编排、batch 批量（≤200 条）

## [v2.6.0] - 2026-06

### 新增
- 首版公开：FBrowser CEF 内核、265 工具基础集、HTTP/WS MCP 通道、Node 桥

[Unreleased]: https://github.com/AI-XiaoDao/ai-browser-mcp/compare/v3.1.0...HEAD
[v3.1.0]: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v3.1.0
[v3.0.0]: https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v3.0.0
