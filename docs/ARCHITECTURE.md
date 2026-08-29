
# AI浏览器 MCP Server — 架构说明

> 版本 3.1.0 · 265 个 MCP 工具 · 火山视窗 (Volcano Windows) + FBrowser CEF 内核 · MIT

## 1. 系统概览

AI浏览器 MCP Server 是一个 **Windows 本地浏览器自动化 MCP 服务端**：进程内嵌真实 **FBrowser CEF (Chromium)** 内核，以标准 **Model Context Protocol (MCP / JSON-RPC 2.0)** 向任意 AI 客户端（Cursor / Claude Code / Claude Desktop / Trae / Cline）暴露 265 个浏览器自动化工具。

```
┌─────────────────────────── AI 客户端 (Cursor/Claude Code/Trae) ───────────────────────────┐
│   MCP 客户端 (官方 SDK 帧格式: 换行分隔 JSON / 兼容 Content-Length)                          │
└──────────────┬──────────────────────────────────────┬────────────────────────────────────┘
               │ stdio (--mcp-stdio 子进程)            │ HTTP POST /mcp · WS ws://9222/mcp
┌──────────────▼──────────────────────────────────────▼────────────────────────────────────┐
│                        AI-Fbowser-Mcp.exe (控制台程序, 单进程)                             │
│  ┌────────────┐  ┌───────────────────┐  ┌────────────────────────────┐                   │
│  │ MCPStdio桥 │  │ FBrowser HTTP/WS  │  │ MCP命令服务器 (MCP引擎)      │                   │
│  │ (stdin/    │  │ 服务器 (9222)     │  │ · JSON-RPC 2.0 解析/响应     │                   │
│  │  stdout)   │  │ 事件驱动回调       │  │ · 协议锁串行化 · 路由分发     │                   │
│  └────────────┘  └───────────────────┘  └────────────┬───────────────┘                   │
│                                                      │ 处理MCP请求 (统一入口)             │
│  ┌───────────────────────────────────────────────────▼────────────────────────────────┐  │
│  │ 工具注册表 (265) → 路由: browser_kernel_ / browser_fill_ / browser_vip_ /          │  │
│  │ fingerprint_ / workflow / reverse_ / 系统工具 → 引擎执行 (浏览器/CDP/SQLite)         │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────── FBrowser CEF 内核 (浏览器容器) ────────────────────────┐  │
│  │ 43 个浏览器事件回调 → 状态同步 (锁保护) · CDP DevTools 观察者 · V8 注入 · 网络拦截    │  │
│  └─────────────────────────────────────────────────────────────────────────────────────┘  │
│  SQLite (mcp_cache.db): 异步结果 / 事件日志 / 响应缓存                                       │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. 进程与实例模型

| 模式 | 启动方式 | 说明 |
|---|---|---|
| 常驻 HTTP 实例 | 双击 exe | 独占单实例互斥体 Global\AI-Fbowser-Mcp-Singleton，监听 127.0.0.1:9222（HTTP + WS），浏览器常驻 |
| 原生 stdio 子进程 | AI-Fbowser-Mcp.exe --mcp-stdio | 由 AI 客户端直接拉起；**跳过**单实例互斥体（可与常驻实例并存）、**不创建** HTTP 服务器、使用**独立 CEF 缓存目录** CacheData\GlobalData_Stdio（避免与常驻实例文件锁互斥）、欢迎页 about:blank；stdin EOF → 优雅退出 |

两模式共用同一 MCP 引擎（MCP命令服务器.处理MCP请求），请求由协议锁端到端串行化。

## 3. 传输层 (MCP Transports)

| 传输 | 端点 | 帧格式 |
|---|---|---|
| stdio | stdin/stdout（--mcp-stdio） | **输出自适应**：客户端发换行分隔 JSON（官方 SDK 2025-06-18 规范）→ 回换行分隔；客户端发 Content-Length 帧 → 回 CL 帧。读取侧字节级解析（PeekNamedPipe 轮询 + ReadFile），双格式兼容 |
| HTTP | POST http://127.0.0.1:9222/mcp（别名 /） | JSON-RPC 2.0，50MB 上限，CORS，另含 /health /tools/list /docs/ 等辅助路由 |
| WebSocket | ws://127.0.0.1:9222/mcp | 同引擎 |

## 4. 协议层 (JSON-RPC 2.0 / MCP 标准合规)

- **生命周期**：initialize（返回 protocolVersion=2025-06-18 / capabilities / serverInfo）→ notifications/initialized → tools/list → tools/call → ping，另实现 resources/list、prompts/list、notifications/cancelled。
- **id 语义**：严格遵循 JSON-RPC 2.0 —— id 可省略（通知不响应）、可为数字 **0**（必须响应）、回显时**保持请求 id 的类型**（数字回数字、文本回文本）。
- **响应纯净**：无自定义扩展字段（曾注入的 _req_id 已移除，官方 SDK 1.30 zod 严格 schema 零拒绝）。
- **错误码**：-32700 解析错误 / -32600 无效请求 / -32601 方法不存在 / -32602 参数无效 / -32603 内部错误 / -32029 限流。
- **工具 schema**：265 个工具全部携带 name / description / inputSchema（JSON Schema 对象）。
- **验证**：通过官方 @modelcontextprotocol/sdk@1.30.0 真客户端全方法测试（connect / listTools / ping / callTool / listResources / listPrompts）。

## 5. 请求处理链

```
MCP命令服务器.处理MCP请求(请求体JSON, 客户端地址)
  ├─ 协议锁.加锁()                          # 请求级静态上下文保护
  ├─ JSON 解析 (YYJSON) + 自动修复常见转义
  ├─ 提取请求 id (键存在性判定, 保类型) + jsonrpc 版本校验
  ├─ API 密钥认证 (可选) / 速率限制
  ├─ 方法路由:
  │    ├─ MCP 协议方法: initialize / notifications/* / resources/* / prompts/* / ping
  │    └─ tools/call → 工具路由:
  │         ├─ browser_kernel_*  → MCP_内核分派 (28 工具)
  │         ├─ browser_fill_*    → Form 填表
  │         ├─ browser_vip_* / fingerprint_* / font_* → MCP_VIP分派
  │         ├─ workflow*         → 工作流引擎
  │         ├─ browser_reverse_* → 逆向工具
  │         ├─ 系统工具 (ping/mcp_status/batch/mcp_result/aliases/...)
  │         └─ 短名映射 (navigate→browser_navigate 等)
  └─ 构建JSONRPC响应 (结果/错误, 保 id 类型)
```

## 6. 同步等待引擎 (sync-wait)

异步工具返回 task_id；客户端可用 mcp_result {request_id, consume} 轮询，或在任意工具参数加 max_ms 让服务端阻塞等待：MCP执行锁（仅一层，不阻塞协议锁）→ 执行期间释放锁 → 结果写入 SQLite（mcp_cache.db）→ 轮询线程读取并返回。

## 7. 浏览器事件层

MCP_BrowserEvents.wsv 挂接 FBrowser 的 43 个事件（导航/加载/证书/下载/快捷菜单/渲染进程消息/资源请求…），所有跨线程共享状态通过命名锁（状态锁/浏览器数组锁/异步缓存锁/待创建锁/事件节流锁/证书错误锁/方案内容锁）保护。主循环 500ms 节拍消费“待创建 URL / 延迟关闭 / 崩溃重建”。

## 8. 内核扩展层 (MCP_Kernel.wsv)

28 个 browser_kernel_* 工具 + 类_MCP_方案资源处理器：证书处理（browser_kernel_cert/auth）、下载接管、自定义协议 mcp://（scheme 资源处理器）、自定义菜单、IPC 队列（渲染进程消息 ↔ MCP 双向）、CDP 观察者、事件反应器、browser_kernel_reverse_* 动态插桩（XHR/fetch/WebSocket/定时器/事件监听五维 API 插桩）。

## 9. 源码布局

```
CEFbro/AI-Fbowser-Mcp/
├── AI-Fbowser-Mcp.vprj / .vsln     # 火山视窗工程 (16 个源文件)
├── src/
│   ├── main.wsv                    # 启动入口: 单实例/stdio模式判定/CEF初始化/主循环/关闭序列/免VIP解锁
│   ├── MCP_Server.wsv              # MCP 引擎核心: JSON-RPC/265工具注册/路由/同步等待/事件层辅助
│   ├── MCP_Server_Core.wsv         # 162 个核心浏览器工具 (导航/DOM/JS/截图/网络/拦截/Cookie/代理/CDP/调试器)
│   ├── MCP_Server_HTTP.wsv         # HTTP/WS 服务器事件 + /health 等路由
│   ├── MCP_Server_System.wsv       # 系统级工具 (窗口/进程/IPC/编辑/查找/编码)
│   ├── MCP_Server_Form.wsv         # 填表 RPA 工具
│   ├── MCP_Server_VIP.wsv          # 指纹伪装/高级键鼠/插件/内核开关 等 (成品已免VIP全解锁)
│   ├── MCP_Server_Workflow.wsv     # 工作流引擎 (JSON 步骤链)
│   ├── MCP_Server_Reverse.wsv      # 逆向分析工具套件
│   ├── MCP_Stdio.wsv               # 原生 stdio 传输层 (帧自适应/断线检测/线程池)
│   ├── MCP_Kernel.wsv              # 内核层分派 + 自定义协议处理器
│   ├── MCP_BrowserEvents.wsv       # FBrowser 43 事件接线
│   ├── MCP_Callbacks.wsv           # 通用回调/参数校验
│   ├── MCP_Constants.wsv           # 常量/版本/错误信息
│   ├── MCP_ResponseBuilders.wsv    # JSON 响应/转义构建器
│   └── MCP_Server_Utils.wsv        # 工具函数
├── workflows/                      # 工作流示例 JSON (编译附属文件)
├── docs/                           # 成品在线文档 (服务器 /docs/ 路由)
├── mcp_bridge.js                   # Node.js 桥 (stdio↔HTTP, 备用接入方式, 帧自适应)
├── mcp_config.json / mcp_config.README.md
└── 备份/                           # 本地备份 (不入 git)
```

## 10. 构建与发布

- **编译**（命令行，非免费版火山）：voldev_awp.exe @compile AI-Fbowser-Mcp.vsln /r（x64）；win32 需临时在 vprj 设置 target_platform = 1（编译后还原，编译器会回写 vprj）。GUI 程序必须用 Start-Process -Wait 等待。
- **产物**：_int/.../release/{x64,win32}/linker/AI-Fbowser-Mcp.exe + 附属文件（CEF DLL/pak/docs/workflows）。
- **打包**：release/pack-release.ps1 -Version 3.1.0 -Platform all → 4 个 zip（x64/win32 运行时 + cpp 参考），上传 GitHub Releases。
- **免 VIP**：FBrowser初始化控制.是否为VIP = 真 强制解锁（类库公开静态变量，DLL 无逐调用校验，假授权码实测可用）。

## 11. 关键设计决策

1. **单进程**：浏览器与 MCP 服务同进程，工具执行零 IPC 开销；事件回调线程安全由锁保证。
2. **帧格式自适应**而非固定 CL 帧：官方 SDK 客户端（Claude Code/Trae/Claude Desktop）只解析换行分隔 JSON。
3. **协议合规优先**：id:0 响应、id 类型保真、无扩展字段 —— 全部通过官方 SDK 严格校验。
4. **stdio 与常驻并存**：互斥体跳过 + 独立缓存目录 + 不占端口，AI 客户端子进程与常驻实例互不干扰。
5. **免 VIP**：成品对所有用户开放全部 265 工具，无需任何授权码。
