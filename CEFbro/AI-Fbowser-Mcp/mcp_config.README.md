# mcp_config.json 说明

完整配置说明书见：

- **编译输出**：`linker/docs/MCP工具配置说明书.md`
- **在线**：`http://127.0.0.1:9222/docs/MCP工具配置说明书.md`
- **开发**：`docs/MCP工具配置说明书.md`

## 字段简表

| 字段 | 默认 | 说明 |
|------|------|------|
| `port` | 9222 | MCP HTTP/WS 端口 |
| `bind_address` | 127.0.0.1 | 绑定地址 |
| `disable_auth` | true | 禁用 API 认证 |
| `api_key` | — | 非空时启用认证 |
| `rate_limit_per_minute` | 0 | 0=不限制 |
| `enable_network_log` | true | 启动即记网络 |
| `enable_console_log` | false | 控制台采集 |
| `enable_response_cache` | false | SQLite 响应缓存 |
| `network_log_max_bytes` | 262144 | network_detail 单条上限 |
| `vip_code` | — | VIP 授权码（**成品已免VIP全功能解锁**，此字段仅保留兼容，可留空） |
| `auto_install_agents` | false | 启动时自动写入 Cursor/Claude/Codex/Cline/Windsurf 配置 |
| `window_topmost` | true | 窗口置顶 |
| `window_width` / `window_height` | — | 窗口尺寸（400-3840 / 300-2160 校验） |
| `auto_download_save` | true | 下载自动保存 |
| `auto_dismiss_js_dialog` | false | 自动关闭 JS 对话框 |
| `enable_media_stream` | `false`（bool） | 启动期对内核命令行调用 `命令行.启用摄像头`，放开摄像头/麦克风媒体流采集。**仅启动期生效，改动后必须重启进程** |
| `enable_speech_input` | `false`（bool） | 启动期对内核命令行调用 `命令行.启用录音`，放开语音输入/麦克风采集。**仅启动期生效，改动后必须重启进程** |
| `enable_autoplay` | `false`（bool） | 启动期对内核命令行调用 `命令行.启用自动播放`，放开带声自动播放策略。**仅启动期生效，改动后必须重启进程** |
| `disable_gpu` | `false`（bool） | 启动期对内核命令行调用 `命令行.禁用GPU`，GPU 异常时的排障开关（渲染/截图可能变慢）。**仅启动期生效，改动后必须重启进程** |
| `disable_gpu_cache` | `false`（bool） | 启动期对内核命令行调用 `命令行.禁用GPU缓存`，绕开 GPU 着色器缓存损坏。**仅启动期生效，改动后必须重启进程** |
| `ignore_gpu_blocklist` | `false`（bool） | 启动期对内核命令行调用 `命令行.忽略GPU禁用清单`，强制启用被内核拉黑的 GPU。**仅启动期生效，改动后必须重启进程** |
| `enable_cross_frame` | `false`（bool） | **新增**。启动期调用 `命令行.启用跨框架操作模式 ()`，解除「框架之间不能直接操作」的内核限制（与 iframe 子框架填表互补；**不改同源策略**）。风险：类库自述**「存在不安全性」**，按需短开、用完改回 `false` 重启。**仅启动期生效，改动后必须重启进程** |
| `disable_proxy` | `false`（bool） | **新增**。启动期调用 `命令行.禁用代理 ()`，**连 Windows 系统自动检测代理一起关掉**（`browser_clear_proxy` 做不到这点）。用途：代理设坏导致全站打不开时的干净排障手段。**仅启动期生效，改动后必须重启进程** |
| `startup_switches` | `{}`（对象） | **新增**。受控的「名→值」白名单表，启动期逐项调用 `命令行.置项值 (名, 值)`。**只接受代码里写死的 4 个名**：`lang`（语言标签，≤32 字符）、`force-device-scale-factor`（必须在 0.5~4 之间）、`disable-blink-features`、`disable-features`（后两者只允许字母/数字/下划线/连字符/逗号）。名在白名单里而**值非法**的条目不生效，但会如实记入回执 `rejected_switches`；**不在白名单里的名一律忽略**（白名单即契约）。实测：`lang`/`force-device-scale-factor` 会真实出现在内核命令行里。**仅启动期生效，改动后必须重启进程** |
| `dpi_aware` | `false`（bool） | **新增**。为真时启动期调用 `FBrowser_设置程序DPI模式 (按显示器感知V2)`：进程级 DPI 感知，HiDPI 屏上窗口不再被系统位图拉伸。⚠ 副作用：窗口 1000×800 将按**物理像素**解释，CSS 视口变小，鼠标/坐标类工具的观测值随之变化 —— 开启后请重跑坐标相关用例。**仅启动期生效，改动后必须重启进程** |
| `v8_max_stack_mb` | `0`（int） | **新增**。>0 时启动期调用 `FBrowser_初始化_设置V8环境默认堆栈大小 (0, N)`，设定渲染进程 V8 **堆**上限（类库中文名叫"堆栈大小", 底层是 `FBroSetV8DefaultsHeapSize`, 实测改的是 `performance.memory.jsHeapSizeLimit`）。⚠ 实测：本机 x64 默认已是 **≈4GB(4294705152)**，设 1024 会把它**压低到 ≈1GB** —— 它不是"只放宽", 而是设定值；`0` = 内核默认（不改动）。校验范围 1..4096；32 位构建 ≤4000。**仅启动期生效，改动后必须重启进程** |

**启动期开关共用说明**：上表 9 个键**只在启动期**由 `启动类.即将处理命令行` 施加到 CEF 内核命令行，改了必须**重启进程**才生效，运行期没有补做手段。施加结果可调只读工具 **`browser_startup_args` 自查**（`action` 缺省 `get`，可传 `list`）：回执含 `applied_switches`（本次实际应用过的开关）、`command_line_raw`（内核命令行原文）、`name_value_switches`（通过校验的名值对）、`rejected_switches`（被拒条目）、`enable_cross_frame`、`disable_proxy`、`note`。

编译后同步到 `linker/mcp_config.json`。**修改后需重启 AI浏览器。**
