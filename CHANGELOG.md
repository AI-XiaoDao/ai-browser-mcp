# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与语义化版本（[SemVer](https://semver.org/lang/zh-CN/)）。

## [v3.2.0] - 2026-09-13

### 新增
- 334 个 MCP 工具全量逐个真机核验通过（311 通过 / 23 受控跳过 / 0 失败），全程零冷重启
- 调试期控制台窗口可见 + 日志双写 `mcp_console.log`（发布成品可去掉）
- 启动器 ShellExecuteW 外壳启动（重启命令 10 分钟 → 6 秒）
- 审计工具链入库：`_audit/sweep334.py`（334 回合逐个测试）、`tool_ledger.py` 台账、全套受控 verify 脚本

### 修复
- AB-BA 死锁（协议锁 × MCP执行锁，原生执行JS并等待 等待期间放锁）
- 非法 browser_id（-1/文本/布尔）静默回退主浏览器 → 入口校验拒绝（防 browser_close 误杀服务）
- browser_close 主窗口缺 confirm 闸门（与 browser_close_try 对称）
- CDP 观察者：注销不再回退到无关浏览器；确保/注销传显式浏览器参数
- 并发 browser_create 握手覆盖 → 命令ID 令牌
- mcp_help 深链最后一个工具详情尾部多 `]}` 非法 JSON
- hwnd 经 32 位整数截断 → 改长整数
- 四处 DB 查询缺"缓存数据库可用"守卫（异常终止请求线程）
- HAR 导出 startedDateTime 恒空 → 网络记录补 timestamp
- 异步取源码/取文本主框架无效时"失败报成成功" → 改失败语义
- 取短名映射点号兜底（防 browser_browser.xxx 畸形别名）
- evaluate/console_eval/extract/view_source 改 CDP 优先（原生通道约 8% 丢回调 → 5s 超时）
- key_event 改 CDP Input.dispatchKeyEvent 优先（内核注入毒化会话通道）
- step 三工具无断点时如实跳过实际单步（根除 pause→step→resume 毒化 CDP）
- browser_fingerprint_ua 会话级毒化警告（UA 变更重启渲染器）
- wheel 遮挡自愈重试、Tracing 残留自愈、指纹设置后渲染器自愈等待
- 活体探针双段判据（browser_status 基线 + 1.5s 短探×2），不误杀不白等

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
