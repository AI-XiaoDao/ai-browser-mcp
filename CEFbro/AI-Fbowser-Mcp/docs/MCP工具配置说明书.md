# AI浏览器 — MCP 工具配置说明书

> **版本** 2.6 · 修改配置后需**重启** AI浏览器.exe  
> **客户快速配置** → 见下文「零、给客户看的 3 步」；完整字段见第 2 节。

---

## 零、给客户看的 3 步

### ① 找到配置文件

与 **AI浏览器.exe** 同一文件夹里的 `mcp_config.json`（用记事本打开）。

### ② 按需修改（多数情况无需改动）

```json
{
  "port": 9222,
  "enable_network_log": true
}
```

发布包已开放全部功能（含 CDP、指纹、截图等高级能力），`vip_code` 无需填写，仅保留兼容。

### ③ 保存并重启程序

改完务必**关闭后重新打开** AI浏览器.exe。Cursor 里若改了端口，同步修改 `mcp.json` 中的地址。

**Cursor 接入**：欢迎页 `http://127.0.0.1:9222/` → 点击「复制 Cursor 配置」→ 粘贴到 `.cursor/mcp.json` → 重启 Cursor。  
详细图文见 [客户使用手册.md](./客户使用手册.md) 第六节。

---

## 1. 配置文件位置

| 文件 | 源码 | 编译输出（exe 同目录） |
|------|------|------------------------|
| `mcp_config.json` | `src/mcp_config.json` | `linker/mcp_config.json` |
| `mcp_connect.json` | —（运行时自动生成） | `linker/mcp_connect.json` |
| `mcp_bridge.js` | 项目根 | `linker/mcp_bridge.js` |
| `mcp_client.js` | 项目根 | `linker/mcp_client.js` |
| `mcp_check.js` | 项目根 | `linker/mcp_check.js` |
| 本文 | `docs/MCP工具配置说明书.md` | `linker/docs/` |

火山编译通过 `MCP_Server.wsv` 附属文件自动复制：`docs/`、`mcp_config.json`、`mcp_bridge.js`、`mcp_client.js`、`mcp_check.js`、`workflows/`。

---

## 2. mcp_config.json 完整字段

```json
{
  "port": 9222,
  "bind_address": "127.0.0.1",
  "disable_auth": true,
  "api_key": "",
  "rate_limit_per_minute": 0,
  "enable_network_log": true,
  "enable_console_log": false,
  "enable_response_cache": false,
  "network_log_max_bytes": 262144,
  "vip_code": "",
  "auto_download_save": true,
  "auto_dismiss_js_dialog": false,
  "auto_install_agents": false,
  "window_topmost": true,
  "window_width": 1200,
  "window_height": 800
}
```

### 2.1 网络服务

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `port` | int | `9222` | MCP HTTP/WebSocket 端口，范围 1–65535 |
| `bind_address` | string | `127.0.0.1` | 绑定地址；非本机时**强烈建议**配置 `api_key` |
| `disable_auth` | bool | `true` | `true` 时忽略 API 密钥认证 |
| `api_key` | string | `""` | 非空且非 `YOUR_API_KEY_HERE` 时启用认证；请求头或参数携带密钥 |
| `rate_limit_per_minute` | int | `0` | 每分钟请求上限；`0` = 不限制 |

### 2.2 日志与缓存

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `enable_network_log` | bool | `true` | 启动即记录网络 req/res；逆向推荐开启 |
| `enable_console_log` | bool | `false` | 控制台消息采集；`reverse_prepare` 会临时开启 |
| `enable_response_cache` | bool | `false` | SQLite 响应缓存（`browser_intercept` cache 配合） |
| `network_log_max_bytes` | int | `262144` | 单条 `network_detail` JSON 最大字符数 |

**网络层边界**：记录 URL/method/status/headers，**不记录 POST 请求体**。

### 2.3 高级功能与浏览器行为

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `vip_code` | string | `""` | 类库授权码字段；发布包已开放全部功能，留空即可（仅保留兼容） |
| `auto_download_save` | bool | `true` | 下载是否自动保存 |
| `auto_dismiss_js_dialog` | bool | `false` | 是否自动关闭 alert/confirm 等 JS 对话框 |
| `auto_install_agents` | bool | `false` | 启动时自动写入 Cursor/Claude/Codex/Cline/Windsurf 的 MCP 配置（免手动接入） |
| `window_topmost` | bool | `true` | 浏览器窗口置顶 |
| `window_width` / `window_height` | int | `1200` / `800` | 窗口尺寸（400–3840 / 300–2160 校验） |

### 2.4 启动期开关（**仅启动期生效，改动后必须重启进程**）

这些键在 **`启动类.即将处理命令行`** 施加（`src/main.wsv`，`进程类型 == ""` 的浏览器进程分支），结果见只读工具 **`browser_startup_args`**。运行期**无法补做**：改了 `mcp_config.json` 必须**重启 AI浏览器.exe**。

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `enable_media_stream` | bool | `false` | 启动期调用 `命令行.启用摄像头`：放开摄像头/麦克风媒体流采集。**仅启动期生效，改动后必须重启进程** |
| `enable_speech_input` | bool | `false` | 启动期调用 `命令行.启用录音`：放开语音输入/麦克风采集。**仅启动期生效，改动后必须重启进程** |
| `enable_autoplay` | bool | `false` | 启动期调用 `命令行.启用自动播放`：放开带声自动播放策略。**仅启动期生效，改动后必须重启进程** |
| `disable_gpu` | bool | `false` | 启动期调用 `命令行.禁用GPU`：GPU 异常时的排障开关（渲染/截图可能变慢）。**仅启动期生效，改动后必须重启进程** |
| `disable_gpu_cache` | bool | `false` | 启动期调用 `命令行.禁用GPU缓存`：绕开 GPU 着色器缓存损坏。**仅启动期生效，改动后必须重启进程** |
| `ignore_gpu_blocklist` | bool | `false` | 启动期调用 `命令行.忽略GPU禁用清单`：强制启用被内核拉黑的 GPU。**仅启动期生效，改动后必须重启进程** |
| `enable_cross_frame` | bool | `false` | **新增**。启动期调用 `命令行.启用跨框架操作模式 ()`：解除「框架之间不能直接操作」的内核限制（与 iframe 子框架填表互补；**不改同源策略**）；风险＝类库自述「存在不安全性」。**仅启动期生效，改动后必须重启进程** |
| `disable_proxy` | bool | `false` | **新增**。启动期调用 `命令行.禁用代理 ()`：**连 Windows 系统自动检测代理一起关掉**（`browser_clear_proxy` 做不到这点）；用途＝代理设坏导致全站打不开时的干净排障手段。⚠ 实测：本机类库给它下发的是 **`--no-proxy-server=disabled`**（带值形态），而 Chromium 常规写法是无值的 `--no-proxy-server` —— **是否被内核按预期识别未验证**。**仅启动期生效，改动后必须重启进程** |
| `startup_switches` | object | `{}` | **新增**。受控的「名→值」白名单表，逐项 `命令行.置项值 (名, 值)`；**只接受 4 个写死的名**（约束见下），未过校验的条目不生效但记入回执 `rejected_switches`。**仅启动期生效，改动后必须重启进程** |
| `dpi_aware` | bool | `false` | **新增**。启动期调用 `FBrowser_设置程序DPI模式 (按显示器感知V2)`：进程级 DPI 感知（HiDPI 屏上窗口不再被位图拉伸）。实测：本机缩放 100%(dpr=1) 时视口 984×705 前后**无变化**, 即该键只在缩放≠100% 的显示器上有可见效果。⚠ 副作用：窗口按物理像素解释、CSS 视口变小 ⇒ 坐标/鼠标类工具观测值会变，开启后需重跑相关用例。**仅启动期生效，改动后必须重启进程** |
| `v8_max_stack_mb` | int | `0` | **新增**。>0 时启动期调用 `FBrowser_初始化_设置V8环境默认堆栈大小 (0, N)`：设定渲染进程 V8 **堆**上限（类库中文名叫"堆栈大小", 底层为 `FBroSetV8DefaultsHeapSize`；实测改的是 `performance.memory.jsHeapSizeLimit`）。⚠ 实测：本机 x64 默认 **≈4GB(4294705152)**，设 1024 会**压低到 ≈1GB** —— 属"设定值"而非"只放宽"。`0`=内核默认。校验范围 1..4096；32 位 ≤4000。**仅启动期生效，改动后必须重启进程** |

**施加结果自查（`browser_startup_args`，`action` 缺省 `get`、可传 `list`）**：回执字段 `applied_switches`（本次实际应用过的开关）、`command_line_raw`（内核命令行原文）、`name_value_switches`（通过校验的名值对）、`rejected_switches`（被拒条目）、`enable_cross_frame`、`disable_proxy`、`note`。

**新增 3 键的风险与限制**

- **`enable_cross_frame`**（bool，默认 `false`）：启动期调用 `命令行.启用跨框架操作模式 ()`，解除「框架之间不能直接操作」的内核限制（与 iframe 子框架填表互补；**不改同源策略**）。风险：类库自述**「存在不安全性」** —— 按需短开，用完改回 `false` 重启。
- **`disable_proxy`**（bool，默认 `false`）：启动期调用 `命令行.禁用代理 ()`，**连 Windows 系统自动检测代理一起关掉**（`browser_clear_proxy` 做不到这点）。用途：代理设坏导致全站打不开时的干净排障手段；排障完改回 `false` 重启。
- **`startup_switches`**（对象，默认 `{}`）：受控的「名→值」白名单表，启动期逐项调用 `命令行.置项值 (名, 值)`。**只接受代码里写死的 4 个名**：`lang`（语言标签，≤32 字符）、`force-device-scale-factor`（必须在 0.5~4 之间）、`disable-blink-features`、`disable-features`（后两者只允许字母/数字/下划线/连字符/逗号）。名在白名单里而**值非法**的条目不生效，但会被如实记入回执 `rejected_switches`（不静默丢弃）；**不在白名单里的名一律忽略**。不裸透传任意 `--xxx` 串：一个 `--single-process` 就能让内核不可用。

```json
{
  "enable_cross_frame": false,
  "disable_proxy": false,
  "startup_switches": { "lang": "zh-CN", "force-device-scale-factor": "1.25" }
}
```

---

## 3. 运行时生成：mcp_connect.json

启动 MCP 后写入 exe 目录，供 `mcp_bridge.js` 与脚本自动发现：

```json
{
  "mcp_url": "ws://127.0.0.1:9222",
  "mcp_http_post": "http://127.0.0.1:9222/mcp",
  "health_url": "http://127.0.0.1:9222/health",
  "tools_url": "http://127.0.0.1:9222/tools/list",
  "docs_url": "http://127.0.0.1:9222/docs/",
  "bridge_script": "mcp_bridge.js",
  "check_command": "node mcp_bridge.js --check"
}
```

---

## 4. Cursor / IDE 接入

### 4.1 推荐：mcp_bridge.js（stdio）

**Release 解压目录**请将 `args` 改为同目录的 `mcp_bridge.js`（或绝对路径）。

```json
{
  "mcpServers": {
    "ai-browser": {
      "command": "node",
      "args": ["CEFbro/AI浏览器/mcp_bridge.js"],
      "env": {
        "AI_BROWSER_MCP_HTTP_POST": "http://127.0.0.1:9222/mcp",
        "AI_BROWSER_MCP_HOST": "127.0.0.1",
        "AI_BROWSER_MCP_PORT": "9222"
      }
    }
  }
}
```

写入 **`.cursor/mcp.json`**（项目内）或 **`~/.cursor/mcp.json`**（全局），保存后**重启 Cursor**。

桥接会自动修复 Cursor 兼容问题：补全 JSON-RPC `id`、协议版本 `2024-11-05`、schema `text`→`string`。

| 环境变量 | 说明 |
|----------|------|
| `AI_BROWSER_MCP_CURSOR_MODE` | 已移除（v2.8.1 起桥接层不再做工具白名单过滤，全部工具动态显示；变量保留仅为兼容旧配置） |

> **勿**直接用 `"url": "http://127.0.0.1:9222/mcp"` 接 Cursor：服务端协议版本与 schema 需经桥接修正，否则易出现 loading tools 或连接失败。

配置优先级：`AI_BROWSER_MCP_HTTP_POST` → `mcp_connect.json` → 默认 `127.0.0.1:9222`。

### 4.2 自检

```bash
node mcp_bridge.js --check
# 或
curl http://127.0.0.1:9222/health
```

---

## 5. 环境变量

| 变量 | 设置时机 | 说明 |
|------|----------|------|
| `AI_BROWSER_MCP_URL` | exe 启动 | WebSocket 地址 |
| `AI_BROWSER_MCP_WS` | exe 启动 | WebSocket MCP 通道地址（`ws://…/mcp`） |
| `AI_BROWSER_MCP_PORT` | exe 启动 | 端口 |
| `AI_BROWSER_MCP_HEALTH` | exe 启动 | 健康检查 URL |
| `AI_BROWSER_MCP_VERSION` | exe 启动 | 服务版本号 |
| `AI_BROWSER_MCP_HTTP_POST` | 手动/桥接 | HTTP JSON-RPC 地址 |
| `AI_BROWSER_MCP_CONNECT` | 手动 | `mcp_connect.json` 路径 |
| `AI_BROWSER_MCP_HOST` | 脚本 | 场景客户端主机，默认 `127.0.0.1` |
| `AI_BROWSER_MCP_CURSOR_MODE` | 桥接 | 已失效（v2.8.1 起忽略，全部工具动态显示） |
| `AI_BROWSER_MCP_STDIO_LOG` | 桥接 | `1` 开启 stdio 调试日志（默认关闭） |
| `AI_BROWSER_WORKFLOWS_DIR` | 手动 | 工作流目录，默认 `linker/workflows/` |

---

## 6. 工具调用参数（通用）

所有 `tools/call` 的 `arguments` 支持：

| 参数 | 说明 |
|------|------|
| `async_only: true` | 强制异步，返回 `task_id` |
| `sync_wait: true` | 强制同步等待结果 |
| `max_ms: N` | sync-wait / 异步轮询超时 |

工具名双路由：`browser_navigate` ≡ `browser.navigate`。

---

## 7. 推荐配置场景

### 7.1 本地开发（默认）

```json
{
  "port": 9222,
  "bind_address": "127.0.0.1",
  "disable_auth": true,
  "enable_network_log": true,
  "enable_console_log": false
}
```

### 7.2 逆向 / 网络分析

```json
{
  "enable_network_log": true,
  "enable_console_log": true,
  "network_log_max_bytes": 524288
}
```

配合：`browser_collect` → `reverse_prepare`；POST body 用 persist Hook。

### 7.3 高级功能（默认开放）

发布包默认开放全部高级能力：CDP、指纹、高级键鼠、截图、资源拦截 modify 等，无需额外配置。`vip_code` 字段仅保留兼容。

### 7.4 生产/远程（谨慎）

```json
{
  "bind_address": "0.0.0.0",
  "disable_auth": false,
  "api_key": "强随机密钥",
  "rate_limit_per_minute": 300
}
```

---

## 8. 工作流目录

| 路径 | 说明 |
|------|------|
| 源码 `workflows/*.json` | 开发编辑 |
| `linker/workflows/` | 编译输出，`workflow_list` 读取 |
| `AI_BROWSER_WORKFLOWS_DIR` | 环境变量覆盖 |

---

## 9. 常见问题

| 现象 | 处理 |
|------|------|
| 改配置不生效 | 重启 AI浏览器.exe |
| `ECONNREFUSED` | 确认 exe 已启动 |
| 高级功能工具报错 | 确认使用发布包运行；仍失败则重启 AI浏览器.exe |
| `browsers: 0` | 等待 GUI 创建主浏览器 |
| 网络 list 为空 | `enable_network_log:true` 或 enable 后再 navigate |
| 文档 404 | 确认 `linker/docs/` 存在（重新编译） |
| 扫描 timeout | `debugger_unfreeze.js` 后重试；勿并行 MCP 脚本 |
| 隐藏窗口后 `mouse_move` 变慢（约 5 秒） | **正常现象**：窗口不可见时渲染器被浏览器后台化节流。工具仍成功、事件仍真实到达页面；调用 `browser_show_window {visible:true}` 立即回到 30ms 级（回复里的 `auto_prepared` 会直接说明成因） |
| 隐藏窗口后 `mouse_wheel` / `touch_*` 立即失败 | **实测限制**：隐藏态这两类 CDP 事件永不返回（直发 `Input.dispatchMouseEvent(mouseWheel)` / `Input.dispatchTouchEvent` 连续多次 30 秒超时），故程序改为**入口快速失败**并给出成因与恢复手段（不再白等 8 秒后误报“CDP 通道不可用”）。`browser_show_window {visible:true}` 后 0.03 秒即成功 |
| 隐藏窗口后点击还能用吗 | **能**：实测隐藏态 `browser_mouse_click` 仍是 0.05 秒级、且页面真实收到（用页面侧 click 计数器验证过），无需先显示窗口 |
| 工具报“CDP 通道已不可用” | 先看窗口是否可见：隐藏态会给出该成因（并说明通道其实健康）；若窗口本来就可见，才是内核级注入 `kernel:true` / 观察者被关等真损伤，需重启进程 |
| 取响应体提示拿不到 `request_id` | 第125轮起**不用传**：`browser_network_body {url}` 会自动开启 Network 域与 `Network.*` 捕获、按 URL（先精确后包含）解析 requestId，解析来源见回复里的 `resolve_note`；不给 `url` 时取最新一条并自动跳过 `favicon.ico`。注意如实限制：响应体只能对**捕获开启之后**发生的请求取回，所以请重发一次该请求（或重载页面）后再取。等价入口：`browser_network {action:"body", url}` |
| `mcp_result` 该传哪个 id | 两种都能取、语义不同：① 异步工具回包里的 `task_id`（形如 `task_64630937_41850_20`）= 该等待任务的实时/最终状态；② **那次调用的 JSON-RPC id** = 该次调用的即时结果（实测用 `id=4242` 调一次，之后 `request_id:"4242"` 即可取回）。没调过的 id 会明确报“未找到任务结果” |
| 大参数报“连接被关闭 / 无响应” | **实测限制**：MCP **HTTP** 通道在 arguments 约 1MB 处会被内核直接断开连接（1020KB 通过、1024KB 失败；且**没有错误码**）。该墙在类库/CEF 侧、早于服务端事件处理，**服务端无法拦截**。可行做法：①大请求体用 `browser_create_url_request {body_file:"D:\\path\\big.bin"}`（文件直传，不进 arguments） ②改用 WebSocket（`ws://host:port/mcp`，上限 50MB）或 stdio 通道（`mcp_bridge.js`）|
| 需要**提交式跳转**（POST / 带签名头跳转） | `browser_navigate {url, method:"POST", headers:"X-Sign: xxx\nContent-Type: application/json", body:"{\"a\":1}"}` —— 走类库 `载入请求`；只给 `body` 时**自动按 POST**。注意该路径**不做同址快速返回**（同址重放也会真发一次）。实测：请求头与请求体逐字送达服务端，页面正常载入 |
| 菜单事件里的 `command_id` 怎么看懂 | `browser_menu_alias {command_id: 113}` → `copy`（`action` 可省略；空参即列出全部别名的清单）。注意回复里的 `caveat`：这些是 **CEF 标准菜单项ID**，不是本应用菜单的真实内容，只有标识/诊断价值 |

### 9.1 隐藏窗口（`browser_show_window {visible:false}`）时的输入族实测语义

| 事件 | 窗口可见 | 窗口隐藏（WS_VISIBLE=0） | 隐藏态是否真实生效 |
|------|----------|--------------------------|--------------------|
| `mouseMoved`（`mouse_move` / 悬停） | 0.03 秒 | **5.08 秒（仍成功）** | 是（页面 `mousemove` 计数 +1） |
| `mousePressed`/`mouseReleased`（`mouse_click`） | 0.03 秒 | **0.03 秒（不受影响）** | 是（页面 `click` 计数 +1） |
| `mouseWheel`（`mouse_wheel`） | 0.03 秒 | **永不返回**（30 秒超时） | 否（`scrollY` 不变）⇒ 入口快速失败 |
| `Input.dispatchTouchEvent`（`touch_*`） | 0.03 秒 | **永不返回**（30 秒超时） | 否 ⇒ 入口快速失败 |
| `Runtime.evaluate` / `Emulation.*` / 读类工具 | 0.03 秒 | **0.01~0.03 秒** | —（证明 CDP 通道本身健康） |

结论：隐藏窗口时**唯一会变慢的是鼠标移动**；滚轮与触摸不可用（程序会立刻告知，而不是让你反复换方法试错）；恢复可见后全部立即复原（滚轮实测 0.02~2.14 秒、多数在 0.1 秒内，且**未发现**“首次滚轮被吞掉”的现象）。

---

## 10. 相关文档

- [客户使用手册.md](./客户使用手册.md) — **终端客户**安装、Cursor、FAQ
- [index.html](./index.html) — 在线 HTML 文档
- `docs/index.html` — 工具完整参考（以 tools/list 动态接口为准）
