# 🚀 AI浏览器 MCP Server v3.1.0

**Windows 本地浏览器自动化 MCP 服务端** — 真实 FBrowser CEF 内核 · **268 个浏览器自动化工具** · 下载即全功能

## 🎁 下载（解压即用）

| 包 | 平台 | 大小 |
|---|---|---|
| **AI-Browser-MCP-x64-v3.1.0.zip** | 64 位 Windows | ~156 MB |
| **AI-Browser-MCP-win32-v3.1.0.zip** | 32 位 Windows | ~135 MB |
| AI-Browser-MCP-cpp-x64-v3.1.0.zip | x64 C++ 生成源码对照 | ~0.4 MB |
| AI-Browser-MCP-cpp-win32-v3.1.0.zip | win32 C++ 生成源码对照 | ~0.4 MB |

> 运行包已包含全部 268 个工具（截图/CDP 调试器/指纹/拦截/内核扩展等），无需额外配置。

## ✨ v3.1.0 核心新增 — 内核层能力扩展（15 工具）

- **自定义协议** `browser_kernel_scheme` — 注册 `mcp://域名` 动态内容（CEF 资源处理器）
- **证书管理** `browser_kernel_cert` — 证书错误收集 / 一键忽略 SSL 错误
- **HTTP 认证注入** `browser_kernel_auth` — Basic/Digest 凭据内核级自动应答
- **下载控制** `browser_kernel_download` — 进行中下载暂停/恢复/取消
- **IPC 双向通道** `browser_kernel_ipc_queue` / `ipc_clear` — 主进程↔渲染进程双工
- **CDP 事件监控** `browser_kernel_cdp_monitor` — CDP 事件订阅自动落库
- **事件反应器** `browser_kernel_reactor` — 事件触发→自动执行页面 JS（组合引擎）
- **定时监视** `browser_kernel_watch` — 表达式周期求值 + 变更检测
- **一键全事件流** `browser_kernel_events_all` — 13 项事件 + 控制台 + 网络详细
- **动态插桩** `browser_kernel_reverse_probe` — XHR/fetch/WS/定时器/监听器五维插桩
- **动态调用追踪** `browser_kernel_reverse_trace` — 调用栈+参数+返回值+耗时
- **动态算法 Hook** `browser_kernel_reverse_algo` — CryptoJS 全算法 + WebCrypto + 哈希
- **动态函数/源码提取** `browser_kernel_reverse_functions` / `sources`
- **全局变量追踪** `browser_kernel_reverse_watch_global` — 写入者调用栈+新值
- **快捷菜单屏蔽** `browser_kernel_menu`

## 🔧 稳定性与修复（本轮大量）

- debugger_flow/script_source 参数校验 — 防 CDP 队列堵塞级联超时
- dom_query null 值误判修复（同步返回正常化）
- 关闭序列清理死代码修复（关库/关服务器不再被跳过）
- 竞态修复：导航规则锁快照 / 关库加锁 / 维护原子占位 / 无主解锁契约 / 下载每日清理
- HTTP POST 体 50MB 上限（OOM 防护）; 事件日志截断合法 JSON; uptime/限流墙钟基准
- tools/list JSON 转义完备（描述含引号不再破坏 schema）
- browser_send_message 方向修正; 崩溃标记写失败告警; stdio 停止超时防死等
- 编译修复：return 关键字、数组置成员、裸嵌套引号、workflows 目录等

## 📖 快速开始

1. 解压 → 双击 `AI-Fbowser-Mcp.exe`
2. `http://127.0.0.1:9222/health` → `{"status":"ok"}`
3. Cursor 配置 `mcp_bridge.js`（欢迎页一键复制配置）
4. 自检：`node mcp_bridge.js --check`

## 📚 文档

- [客户使用手册](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/CEFbro/AI-Fbowser-Mcp/docs/客户使用手册.md)
- [使用技能书](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/CEFbro/AI-Fbowser-Mcp/docs/使用技能书.md)
- [MCP工具配置说明书](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/CEFbro/AI-Fbowser-Mcp/docs/MCP工具配置说明书.md)
- [AI浏览器MCP.md 工具参考](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/CEFbro/AI-Fbowser-Mcp/skills/AI浏览器MCP.md)

## 支持

QQ 212577526 · QQ群 737680767 · [Issues](https://github.com/AI-XiaoDao/ai-browser-mcp/issues) · MIT 开源
