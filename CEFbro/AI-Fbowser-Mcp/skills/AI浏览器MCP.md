---
name: AI浏览器MCP
description: AI浏览器 MCP 服务工具参考 - 268个浏览器自动化工具 (v2.8: 44逆向CDP/7反检测/workflow条件变量/HAR导出/resources+prompts/retry)
version: 2.8.0
trigger: 测试MCP|MCP工具|浏览器MCP|AI浏览器|FBrowser MCP|mcp_config|workflow_run|sync-wait|reverse|CDP|断点|debugger|Hook|反检测|fingerprint|加密|签名|网络抓包
---
# AI 浏览器 MCP 服务技能书 v2.8

## 概述
AI浏览器 MCP Server 基于火山 FBrowser CEF 框架，默认运行在 `ws://127.0.0.1:9222`。
**268 个 MCP 工具**（含 3 个 GUI 受限：`browser_create` / `browser_close` / `browser_create_tab`）。

⏳=默认仍异步（需 mcp_result）　✅=默认 sync-wait　🔒=VIP/高级工具　⚠️=暂未实现　R=需刷新页面　🆕=v2.8新增

### 源码文件 (v2.8)
| 文件 | 类 | 职责 |
|------|-----|------|
| `MCP_Server.wsv` | `MCP命令服务器` | JSON-RPC、sync-wait、batch、工具注册、`执行浏览器命令` |
| `MCP_Server_Core.wsv` | `MCP_核心分派` | 导航/JS/CDP/窗口/网络/collect 等核心工具 (~3400 行) |
| `MCP_Server_Form.wsv` | `MCP_填表分派` | FBrowser 官方填表 API |
| `MCP_Server_Workflow.wsv` | `MCP_编排分派` | workflow_list/get/run/stop、JSON 步骤链 |
| `MCP_Server_System.wsv` | `MCP_系统分派` | ping、全局配置、task_runner |
| `MCP_Server_VIP.wsv` | `MCP_VIP分派` | VIP 命令 (~80 工具) |
| `MCP_Server_HTTP.wsv` | `类_MCP_服务器事件` | HTTP/WS 路由、静态 `/docs` |
| `MCP_BrowserEvents.wsv` | `类_MCP_浏览器事件` | 浏览器事件 Hook |
| `MCP_Callbacks.wsv` | 各类回调 | JS/VIP 异步回调、语义失败检测 |
| `MCP_Stdio.wsv` | `MCPStdio桥` | `--mcp-stdio` stdin 传输 |
| `main.wsv` | `启动类` / 主窗口 | GUI 入口 + FBrowser 初始化 |

**分派链**: `MCP_核心分派` → `MCP_填表分派` → `MCP_VIP分派` → `MCP_系统分派` → `MCP_编排分派`

## 连接

| 协议 | 端点 | 说明 |
|------|------|------|
| WebSocket | `ws://127.0.0.1:9222` | MCP JSON-RPC 主通道 |
| HTTP GET | `http://127.0.0.1:9222/health` | 健康检查 |
| HTTP GET | `http://127.0.0.1:9222/tools` / `/tools/list` | **工具列表 (CORS)** |
| HTTP GET | `http://127.0.0.1:9222/json` / `/json/list` | 浏览器实例列表 (CORS) |
| HTTP GET | `http://127.0.0.1:9222/` | 服务器信息 (CORS) |
| HTTP POST | `http://127.0.0.1:9222/mcp` | JSON-RPC over HTTP (CORS) |
| CDP WS | `ws://127.0.0.1:9222/devtools/browser/{id}` | Chrome DevTools Protocol |

> **所有 HTTP 端点均带 CORS 头** (`Access-Control-Allow-Origin: *`)，前端页面可直接用 `fetch()` 调用。

### 环境变量 (自动注册)
启动时自动设置以下系统环境变量，供 MCP 客户端自动发现：

| 变量 | 值 | 用途 |
|------|-----|------|
| `AI_BROWSER_MCP_URL` | `ws://127.0.0.1:9222` | WebSocket 连接地址 |
| `AI_BROWSER_MCP_PORT` | `9222` | 服务端口 |
| `AI_BROWSER_MCP_HEALTH` | `http://127.0.0.1:9222/health` | 健康检查地址 |

客户端可读取 `process.env.AI_BROWSER_MCP_URL` 自动连接。

## 架构要点

### 异步任务 ID 格式 (v2.0)
```
task_<启动毫秒>_<随机盐>_<计数器>
```
时间戳+5位随机数+单调计数器，碰撞概率趋近于零。

### Sync-Wait 默认同步 (v2.5 UX)

服务端对常用读操作默认 **sync-wait**：提交 async 任务后在同一次 `tools/call` 内轮询完成并返回结果，响应可含 `"_sync_waited":true`。

| 参数 | 说明 |
|------|------|
| _(默认)_ | 白名单工具自动 sync-wait |
| `async_only: true` | 强制纯异步，立即返回 `task_id` |
| `sync_wait: true` | 对非白名单工具也启用 sync-wait |
| `max_ms: N` | 自定义等待超时（毫秒） |

**默认 sync-wait 白名单**：
- 读/写：`get_title`、`evaluate`、`console_eval`、`dom_query`、`dom_set_value`、`dom_click`、`get_frames`、`frame_names`、`fill_exists`、`fill_attr_get`
- 条件：`get_text` / `dom_get_html` 仅当传入 `selector` 时
- 调试器（VIP）：`debugger_enable/pause/resume/step_*`、`debugger_set_breakpoint`、`debugger_evaluate`、`debugger_stack`、`debugger_wait_paused`、`debugger_last_paused`、`debugger_inspect`、`debugger_flow`、`debugger_script_source`

**batch**：默认对子命令自动跟随 async 结果；子命令失败时外层 `success:false`；batch 级 `async_only: true` 关闭跟随；`强制同步` 时忽略子命令 `async_only`。

**HTTP `arguments`**：支持 JSON 字符串（与 batch 相同 fallback），如 `"arguments":"{\"selector\":\"#x\"}"`。

**语义失败 (P0-3)**：`dom_click` / `dom_set_value` 等元素未找到或 `{ok:false}` 时 `success:false`（非假成功）。

### 工作流 workflow (v2.5)

| 工具 | 参数 | 说明 |
|------|------|------|
| `workflow_list` | - | 列出 `linker/workflows/*.json` |
| `workflow_get` | `name` 或 `file` | 返回工作流定义 JSON 文本 |
| `workflow_run` | `name` / `file` / `definition` / `steps` | 顺序执行步骤；默认 sync-wait |
| `workflow_stop` | - | 中止运行中工作流；空闲时清除停止标志 |

**步骤 JSON**（数组元素）：
- `{ "tool": "browser_navigate", "args": { "url": "..." } }`
- `{ "delay_ms": 500 }` — 延时
- `{ "wait_async": true, "max_ms": 45000 }` — CDP/截图等慢步骤（默认 workflow sync-wait 15s，Debugger 建议 ≥45s）
- `on_error`: `"stop"`（默认）或 `"continue"`

**场景预备**（`browser_collect` action）：

| 分类 | action | 说明 |
|------|--------|------|
| 预备 | `reverse_prepare` | 开 network_detail + console，可选 `clear:true` 清日志，返回逆向指南 |
| 预备 | `debug_prepare` | 开 network_detail，返回断点调试指南 |
| 预备 | `automation_prepare` | 返回填表/自动化指南 |
| 调试快捷 | `debug_wait_paused` / `debug_inspect` / `debug_resume` / `debug_flow` / `debug_script_source` | 等同同名 `browser_debugger_*` |
| 网络 | `network_enable` / `network_detail_enable` / `network_disable` / `network_get` / `network_clear` | 等同 `browser_network`（别名 `enable`/`list`/`clear`/`detail_enable`） |
| 控制台 | `console_enable` / `console_get` / `console_clear` | 控制台采集 |
| 缓存 | `cache_enable` / `cache_clear` | SQLite 响应缓存开关/清空 |
| 事件监控 | `event_load_enable` / `event_title_enable` / `event_progress_enable` / `event_resource_enable` / `event_dialog_enable` / `event_fullscreen_enable` / `event_lifecycle_enable` / `event_favicon_enable` / `event_find_enable` / `event_frame_enable` / `event_download_enable` / `event_focus_enable` / `event_app_enable` | 单项浏览器事件 Hook |
| 事件监控 | `event_all_enable` / `event_all_disable` | 批量开/关上述事件 |

**示例文件**：`workflows/hello.json`、`ping_navigate.json`、`reverse_analyze.json`、`automation_form.json`、`debugger_breakpoint.json`、`debugger_full.json`

**加载优先级**：`name`/`file` **优先**读 `workflows/` 目录；内联 `definition` 仅作 fallback（避免空 `definition:{}` 占位拦截文件加载）。

**目录**：运行时 `linker/workflows/`，环境变量 `AI_BROWSER_WORKFLOWS_DIR` 可覆盖。

**workflow_run**：步骤默认 sync-wait；`browser_wait` 通过内部轮询 `_waiting` 推进；`workflow_stop` 可在等待中中止；运行结束自动重置 `工作流应停止`。

### 事件 Hook 系统
参照网络日志 toggle 模式，预注册+动态启用：
```
MCP_Server.wsv (开关+数据)  →  MCP_BrowserEvents.wsv (事件执行)
是否记录网络/控制台 → 浏览器_获取资源处理器/控制台消息
是否缓存响应       → 浏览器_获取资源过滤器
是否Hook导航       → 浏览器_即将导航 (block/redirect)
是否Hook资源       → 浏览器_获取资源处理器 (VIP控制器处理)
是否Hook弹窗       → 浏览器_即将打开新窗口 (自定义属性)
持久V8扩展列表     → 浏览器_载入开始 → 应用持久V8到框架 (浏览器进程执行JS)
                     inject_id 去重，同页仅应用最新一条；handler/js 均在框架内执行
持久代理/缩放/静音 → 浏览器_创建完毕 (自动应用)
持久CDP观察者      → 浏览器_创建完毕 (自动注册)
```

### 双通道拦截
`browser_intercept` 同时使用 VIP API + 事件Hook：
- VIP可用时：VIP控制器处理拦截（高效）
- VIP不可用时：事件Hook记录规则（降级日志）
- 资源规则存储：文本格式 `action|url|params`，换行分隔
- 导航规则存储：`block|url` 或 `redirect|url|target`

### 回调类型全覆盖 (v2.0)
- `类_MCP_JS异步回调`：JS返回值 11 种类型全覆盖
- `类_MCP_VIP通用回调.列表数据回调`：CEF值类型 9 种全覆盖
- 所有 12 个回调类均正确调用 `存储异步结果`，无结果丢失

### HTTP CORS 辅助层 (v2.1)
所有 HTTP 响应统一通过 `发送CORS响应()` 基础方法 + 便捷封装：
```火山
发送CORS响应 (服务器, 连接ID, 状态码, 内容类型, 数据指针, 数据大小)
├── 发送CORS200响应 (服务器, 连接ID, 内容类型, 数据指针, 数据大小)
├── 发送CORS404响应 (服务器, 连接ID)
└── 发送CORS500响应 (服务器, 连接ID, 错误消息)
```
- 懒初始化 `CORS响应头`（首次使用时创建，全局复用）
- 自动注入 `Access-Control-Allow-Origin/Methods/Headers` 三个头
- 非 200 响应同样带 CORS 头，前端可获取完整错误信息
- 替换了全部 6 处 `发送Http200响应` 调用

### 欢迎页工具列表 (v2.1)
内嵌欢迎页不再依赖 WebSocket 握手获取工具列表，改用 HTTP `fetch()`：
- 加载时显示 "正在加载工具列表..."
- `fetch('http://127.0.0.1:9222/tools/list')` 直接 GET
- 最多 30 次重试（2 秒间隔），应对服务端尚未就绪的竞态
- 成功后按 8 个分类渲染工具网格，支持关键字搜索筛选

---

## 工具列表

### 一、系统/元工具 (10)

| 工具 | 参数 | 说明 |
|------|------|------|
| `mcp_status` | - | 服务器状态(浏览器数/运行时间) |
| `mcp_help` | - | 帮助信息/工具清单 |
| `mcp_result` | `request_id` | 查询异步任务结果 |
| `ping` | - | 连通性检查 |
| `batch` | `commands` | 批量执行(JSON 数组)；默认 sync-wait 子命令 |
| `aliases` | - | 短名别名列表 |
| `workflow_list` | - | 工作流 JSON 文件列表 |
| `workflow_get` | `name` / `file` | 获取工作流定义 |
| `workflow_run` | `name` / `steps` / `definition` | 执行工作流（步骤 sync-wait） |
| `workflow_stop` | - | 停止运行中工作流 |

### 二、导航与页面 (12)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_navigate` | `url` | 导航到URL |
| `browser_get_url` | - | 获取当前URL |
| `browser_get_title` | - | 获取页面标题（默认 sync-wait；`async_only:true` 改异步） |
| `browser_reload` | `ignore_cache`(可选) | 刷新页面 |
| `browser_back` | - | 后退 |
| `browser_forward` | - | 前进 |
| `browser_stop` | - | 停止加载 |
| `browser_list` | - | 列出所有浏览器实例 |
| `browser_status` | - | 浏览器完整状态 |
| `browser_view_source` | - | 打开源码视图 |
| `browser_popup_info` | - | 弹窗状态 |
| `browser_loading_info` | - | 加载/导航状态 |
| `browser_window_info` | - | 窗口信息 |
| `browser_can_navigate` | - | 可否后退/前进 |

> ⛔ **受限工具（不推荐使用）：** `browser_create` `browser_create_tab` `browser_close` `browser_close_try` — 创建/关闭浏览器可能导致资源泄漏或会话中断，仅在明确需要时使用。

### 三、JS执行 (7)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_execute_js` | `code` | 执行JS(无返回值) |
| `browser_evaluate` | `code` | 执行JS并返回 ⏳ |
| `browser_console_eval` | `expression` | 控制台执行并返回 ⏳ |
| `browser_get_source` | `max_chars`(可选,256KB) | 获取HTML源码 ⏳ |
| `browser_get_text` | `max_chars`(可选,256KB) | 获取页面文本 ⏳ |
| `browser_extract` | `type`(links/images/tables),`limit` | 提取页面结构化数据(链接/图片/表格) ⏳ |
| `browser_scrape` | `url`,`extract_selector`,`wait_selector?`,`max_ms?` | 一站式爬虫: navigate→wait→extract 异步状态机 |

### 四、DOM操作 (10)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_dom_query` | `selector`,`attribute`,`index` | DOM查询 ⏳ |
| `browser_dom_click` | `selector` | DOM点击（默认 sync-wait；失败 success:false） |
| `browser_dom_set_value` | `selector`,`value` | DOM设置值 ⏳ |
| `browser_dom_get_html` | `selector` | DOM获取HTML ⏳ |
| `browser_dom_inner_html` | `selector` | DOM获取innerHTML(原生填表API，非JS) ⏳ |
| `browser_dom_set_html` | `selector`,`html` | DOM设置innerHTML |
| `browser_dom_checked` | `selector` | 获取checkbox checked状态(原生) ⏳ |
| `browser_dom_selected` | `selector` | 获取select选中项(原生) ⏳ |
| `browser_dom_select` | `selector`,`index` | 设置select选项index |
| `browser_dom_rect` | `selector` | 获取元素坐标(原生) ⏳ |

### 五、填表框架 (9)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_fill_set_value` | `selector`,`value` | 设置元素值 |
| `browser_fill_click` | `selector` | 点击元素 |
| `browser_fill_focus` | `selector` | 焦点 |
| `browser_fill_scroll` | `selector` | 滚动 |
| `browser_fill_exists` | `selector` | 检查存在 ⏳ |
| `browser_fill_attr_get` | `selector`,`attribute` | 取属性 ⏳ |
| `browser_fill_attr_set` | `selector`,`attribute`,`value` | 设属性 |
| `browser_fill_trigger` | `selector`,`event` | 触发事件 |
| `browser_fill_select` | `selector`,`value` | 设置select |

### 六、鼠标键盘 — 基本 (4)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_mouse_click` | `x`,`y`,`button` | 窗口消息点击 |
| `browser_mouse_move` | `x`,`y` | 窗口消息移动 |
| `browser_mouse_wheel` | `x`,`y`,`delta_x`,`delta_y` | 窗口消息滚轮 |
| `browser_key_event` | `key_code`,`type`,`modifiers` | 窗口消息键盘 |

### 七、鼠标键盘 — VIP CDP (4) 🔒

> **v2.7合并**: `browser.mouse_click/move/wheel` 和 `browser.key_event` 已内置VIP CDP优先执行路径, 无需再调用 `browser_vip_*` 前缀。VIP不可用时自动退路至窗口消息API。

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_vip_mouse_press` | `x`,`y` | CDP按下(精细) |
| `browser_vip_mouse_release` | `x`,`y` | CDP放开(精细) |
| `browser_vip_key_input` | `char_code`(文本) | CDP输入字符 |
| `browser_vip_key_type` | `text` | CDP输入文本 |

### 八、触摸 (4) 🔒

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_touch_press` | `x`,`y` | 按下 |
| `browser_touch_release` | `x`,`y` | 放开 |
| `browser_touch_move` | `x`,`y` | 移动 |
| `browser_vip_touch_cancel` | - | 取消 |

### 九、编辑操作 (7)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_edit_undo` | - | 撤销 |
| `browser_edit_redo` | - | 恢复 |
| `browser_edit_cut` | - | 剪切 |
| `browser_edit_copy` | - | 复制 |
| `browser_edit_paste` | - | 粘贴 |
| `browser_edit_delete` | - | 删除 |
| `browser_edit_select_all` | - | 全选 |

### 十、缩放/查找/静音 (7)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_set_zoom` | `level` | 缩放级别 |
| `browser_get_zoom` | - | 获取缩放 |
| `browser_find` | `text` | 查找 |
| `browser_stop_find` | - | 停止查找 |
| `browser_set_mute` | `mute` | 静音(持久) |
| `browser_is_muted` | - | 静音状态 |
| `browser_is_loading` | - | 加载状态 |

### 十一、Cookie/代理/缓存 (12)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_get_cookies` | `limit`(默认200) | 获取Cookie(含HttpOnly) ⏳ |
| `browser_get_all_cookies` | - | 全部Cookie ⏳ |
| `browser_set_cookie` | `name`,`value`,`domain`,`url`... | 设置Cookie |
| `browser_delete_cookies` | `confirm` | 删除全部 |
| `browser_refresh_cookies` | - | 刷新到磁盘 |
| `browser_set_proxy` | `address`,`username`,`password` | 代理(VIP SOCKS5优先→HTTP退路,持久) |
| `browser_clear_proxy` | - | 清除代理(VIP SOCKS5优先→HTTP退路) |
| `browser_clear_cache` | - | 全局缓存 ⏳ |
| `browser_clear_cache_browser` | - | 浏览器缓存 ⏳ |
| `browser_cache_dir` | - | 缓存目录 |

### 十二、截图/打印/下载 (5)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_screenshot` | `format`(png/jpeg/webp) | 截图 🔒 ⏳ |
| `browser_print` | `format` | 打印 |
| `browser_print_to_pdf` | `path`,`overwrite` | PDF ⏳ |
| `browser_start_download` | `url` | 触发下载 |
| `browser_download_image` | `url` | 下载图片 ⏳ |

### 十三、网络/拦截/CDP (10)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_cdp` | `method`,`params` | CDP命令 🔒 ⏳ |
| `browser_cdp_call` | `method`,`params` | CDP(带结果回传) 🔒 ⏳ |
| `browser_cdp_event` | `event_name` | 读取CDP事件 🔒 |
| `browser_intercept` | `action`,`url`... | 资源拦截(双通道) 🔒 |
| `browser_network` | `action`,`limit`,`auto_enable` | 网络日志（见下表） |
| `browser_collect` | `action` | 网络/控制台/场景预备/事件监控（见上表） |
| `browser_wait` | `what`,`value`,`max_ms` | 异步等待 ⏳ |
| `browser_inject` | `type`,`code`,`persist` | 注入JS/CSS/Handler |
| `browser_event` | `event_type`(load_end/crash) | 查询事件 |
| `browser_network_body` | `request_id` | 响应体 🔒 ⏳ |

#### `browser_network` action 全集

| action | 别名 | 说明 |
|--------|------|------|
| `list` / `get` | `network_get` | 返回 `network_logs` 数组；`limit` 默认 500；`auto_enable` 默认 true（未开时自动 enable） |
| `enable` | `network_enable` | 基础模式：记录 req/res（method/url/status/mime） |
| `detail_enable` | `network_detail_enable` | 详细模式：额外记录 `headers_json`（不含 cookie/set-cookie） |
| `disable` | `network_disable` | 关闭记录 |
| `clear` | `network_clear` | 清空 SQLite `event_log` 中 network 条目 |

**网络层能力边界**（源码 `记录网络请求` / `记录网络请求_详细`）：
- ✅ URL、method、status、mime、响应头、content_length
- ❌ **不记录 POST/PUT 请求体**；要抓 body 须 `browser_inject` persist Hook `XMLHttpRequest.send` / `fetch`
- 仅记录 enable **之后**的新请求；磁盘缓存命中可能无 req/res
- `reverse_prepare` 自动开 `network_detail` + `console`

#### 网络数据与 POST 参数逆向（推荐流程）

```bash
# 1) 打开目标站
browser_navigate { "url": "https://www.douyin.com/" }

# 2) 一键预备 + 注入 XHR/fetch Hook（见 scenarios/douyin_xhr_encrypt_scan.js）
browser_collect { "action": "reverse_prepare", "clear": true }
browser_inject { "type": "js", "code": "<HOOK>", "persist": true, "inject_id": "xhr_post_scan" }

# 3) 触发业务（滚动/登录）后读取
browser_evaluate { "code": "JSON.stringify(window.__MCP_XHR_POST__||[])" }
browser_network { "action": "list", "limit": 500 }   # 补全 POST URL（无 body）
```

**疑似加密字段启发式**（`douyin_xhr_encrypt_scan.js`）：
- 字段名：`a_bogus`、`msToken`、`verifyFp`、`sign`、`x-gorgon` 等
- 值特征：高熵 Base64/hex、超长随机串
- 同时分析 **URL query** 与 **body**（JSON / `URLSearchParams`）

| 脚本 | 用途 |
|------|------|
| `scenarios/douyin_xhr_encrypt_scan.js [url]` | 抖音等站点 XHR/fetch POST 加密字段扫描 |
| `scenarios/reverse_analyze.js [url]` | 页面 script 标签 + 网络 JS 清单 |
| `scenarios/js_http_hook_test.js` | Console / fetch·XHR / network / 导航拦截冒烟 |

#### `browser_intercept` action 全集 (12)

| action | 参数 | 说明 |
|--------|------|------|
| `block` | `url` | 屏蔽资源(VIP) |
| `replace_data` | `url`,`replace_text` | 替换为数据(VIP) |
| `replace_file` | `url`,`file_path` | 替换为文件(VIP) |
| `modify` | `url`,`search_text`,`replace_text` | 修改响应(VIP) |
| `navigate_block` | `url` | 导航拦截(事件Hook) |
| `navigate_redirect` | `url`,`target` | 导航重定向(事件Hook) |
| `popup_config` | `width`,`height`,`x`,`y` | 弹窗自定义(事件Hook) |
| `popup_disable` | - | 禁用弹窗Hook |
| `cache` | `dir`(可选) | 启用响应缓存 |
| `uncache` | - | 禁用响应缓存 |
| `clear` | - | 清除所有规则 |
| `ws_hook` | - | WebSocket拦截 🔒 |

#### `browser.fingerprint` action 全集 (11)

| action | 参数 | 说明 |
|--------|------|------|
| `count` | - | 调用计数 |
| `clear` | - | 清除指纹 |
| `canvas_random` | `min`,`max`,`seed` | Canvas随机 🔒 |
| `webgl_random` | `min`,`max`,`seed` | WebGL随机 🔒 |
| `audio_random` | `min`,`max`,`seed` | Audio随机 🔒 |
| `audio_param` | - | ⚠️ SDK签名待更新 |
| `webrtc` | `public_ip`,`local_ip`,`host`,`disable` | WebRTC 🔒 |
| `geolocation` | `latitude`,`longitude` | 定位 🔒 |
| `timezone` | `offset_hours`,`offset_minutes`,`timezone_name`,`iana_timezone` | 时区 🔒 |
| `ssl` | - | ⚠️ TLS模板错误 |
| `set_batch` | `config`(JSON) | 批量设置 🔒 |

### 十四、指纹 — 基础 (14) 🔒

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_fingerprint` | `action`,`config` | 统一入口 R |
| `browser_fingerprint_ua` | `ua`,`platform`,`accept_lang`,`brands`,`mobile`,`architecture`,`bitness`,`model`,`wow64` | UA完整 R |
| `browser_fingerprint_appname` | `value` | appName R |
| `browser_fingerprint_appcodename` | `value` | appCodeName R |
| `browser_fingerprint_appversion` | `value` | appVersion R |
| `browser_fingerprint_pixel_ratio` | `value` | devicePixelRatio R |
| `browser_fingerprint_plugins` | `type`,`json` | Plugins R |
| `browser_fingerprint_cookie_enabled` | `value` | cookieEnabled R |
| `browser_fingerprint_java_enabled` | `value` | javaEnabled R |
| `browser_fingerprint_online` | `value` | onLine R |
| `browser_fingerprint_product_sub` | `value` | productSub R |
| `browser_fingerprint_vendor_sub` | `value` | vendorSub R |
| `browser_fingerprint_screen_xy` | `x`,`y` | 屏幕坐标 R |
| `browser_fingerprint_touch_enable` | `enable`,`points` | 触摸事件 R |

### 十五、指纹 — VIP高级 (18) 🔒

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_vip_fingerprint_canvas` | `min`,`max`,`seed` | Canvas随机 R |
| `browser_vip_fingerprint_canvas_fixed` | `value` | Canvas定值 R |
| `browser_vip_fingerprint_webgl` | `min`,`max`,`seed` | WebGL随机 R |
| `browser_vip_fingerprint_webgl_fixed` | `value` | WebGL定值 R |
| `browser_vip_fingerprint_audio` | `min`,`max`,`seed` | Audio随机 R |
| `browser_vip_fingerprint_audio_fixed` | `value` | Audio定值 R |
| `browser_vip_fingerprint_font` | `font_list`,`w_offset`,`h_offset` | CSS字体 R |
| `browser_vip_fingerprint_webrtc` | `public_ip`,`local_ip`,`host`,`disable` | WebRTC IP R |
| `browser_vip_fingerprint_timezone` | `offset_h`,`offset_m`,`name`,`iana` | 时区 R |
| `browser_vip_fingerprint_geolocation` | `lat`,`lng`,`accuracy` | 定位 R |
| `browser_vip_fingerprint_ssl` | `tls_min`,`tls_max`,`ciphers` | SSL ⚠️ |
| `browser_vip_fingerprint_screen` | `width`,`height`,`avail_w`,`avail_h`,`depth`,`pixel_depth` | 屏幕 R |
| `browser_vip_fingerprint_viewport` | `top`,`left`,`width`,`height` | Viewport R |
| `browser_vip_fingerprint_hardware` | `concurrency`,`memory` | 硬件 R |
| `browser_vip_fingerprint_product` | `product`,`vendor` | 产品标识 R |
| `browser_vip_fingerprint_battery` | `charging`,`level`,`charging_time`,`discharging_time` | 电池 R |
| `browser_vip_fingerprint_media_devices` | `type`,`target`,`devices` | 媒体设备 R |
| `browser_vip_fingerprint_rect` | `x`,`y`,`w`,`h` | DOMRect R |

### 十六、内核开关 (6) 🔒 R

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_vip_set_css_version` | `version` | CSS版本 |
| `browser_vip_set_web_version` | `version` | Web版本 |
| `browser_vip_set_v8_version` | `version` | V8版本 |
| `browser_vip_disable_debugger` | `disable` | Debugger检测 |
| `browser_vip_disable_console` | `log`...`performance`(15项) | 控制台输出 |
| `browser_vip_set_is_trusted` | `enable` | Event.isTrusted |

### 十七、调试器 (14) 🔒

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_debugger_flow` | `url`,`breakpoint`,`line`,`column`,`expressions`,`expand`,`return_by_value`,`max_ms`,`resume` | **一键流程**：enable→断点→导航→wait→inspect→resume |
| `browser_debugger_enable` | - | 启用调试器 |
| `browser_debugger_pause` | - | 暂停JS |
| `browser_debugger_resume` | - | 继续JS |
| `browser_debugger_step_over` | - | 单步跳过 |
| `browser_debugger_step_into` | - | 单步进入 |
| `browser_debugger_step_out` | - | 单步跳出 |
| `browser_debugger_stack` | - | 调用栈 |
| `browser_debugger_set_breakpoint` | `url`,`line`,`column` | URL 正则断点（`line` 0 起算，FBrowser 必填） |
| `browser_debugger_evaluate` | `call_frame_id`,`expression`,`parse`,`expand`,`return_by_value` | 单帧求值；`parse:true` 同步返回 `{ok,type,value,properties,source}` |
| `browser_debugger_wait_paused` | `max_ms`,`fresh` | **阻塞等待** `Debugger.paused`，返回 `call_frame_id`/frames/scopes |
| `browser_debugger_last_paused` | `parse` | 读取最近一次暂停（不阻塞） |
| `browser_debugger_inspect` | `call_frame_id`,`expressions`/`expression`,`expand`,`return_by_value` | 断点处批量求值；默认 `expand:true` 展开 object/function |
| `browser_debugger_script_source` | `call_frame_id`,`script_id`,`line`,`column`,`context_lines`,`include_source` | **暂停处脚本源码**：自动 `scriptId` → `Debugger.getScriptSource` + 当前行上下文 |

**典型断点流程**（需 VIP；首次 CDP 调用自动注册观察者）：

```json
{ "name": "browser_debugger_flow", "arguments": {
  "url": "data:text/html,<script>debugger;window.__mcp_dbg=1</script>",
  "breakpoint": ".*",
  "expressions": "[\"location.href\",\"window.__mcp_dbg\",\"Object.keys(window).slice(0,5)\"]",
  "expand": true,
  "resume": true
}}
```

**帧内求值返回**（`expand:true` 默认）：
- 基本类型：`{ok,type,value,description}`
- **object**：附加 `properties[]`（`Runtime.getProperties`，含 name/type/value/objectId）
- **function**：附加 `source`（`.toString()`）与 `properties`（name/length 等）
- 单表达式：`browser_debugger_evaluate { parse:true, expand:true, expression:"myObj" }`

**脚本源码**（`browser_debugger_script_source`）：
- 默认从最近 `Debugger.paused` 读取 `scriptId` / `lineNumber`
- 返回 `{ scriptId, url, lineNumber, columnNumber, scriptSource, currentLine, contextSnippet }`
- `contextSnippet` 带行号，`>` 标记当前行；`include_source:false` 仅返回上下文

分步：`enable` → `set_breakpoint` → `navigate` → `wait_paused`（等待前清除陈旧 paused）→ `inspect` / `script_source` → `resume`

`browser_cdp_event` 支持 `event`/`event_name`；`Debugger.paused` 附带 `paused` 摘要。

### 十八、DevTools (4)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_open_devtools` | - | 打开DevTools |
| `browser_close_devtools` | - | 关闭DevTools |
| `browser_vip_send_devtools_msg` | `json` | DevTools原始消息 🔒 |
| `browser_vip_enable_devtools_observer` | `enable` | DevTools消息监听 🔒 |

### 十九、窗口与系统 (23)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_meta` | - | 机器码/授权/版本 |
| `browser_fbro_version` | - | CEF内核版本 |
| `browser_get_id` | - | 浏览器ID |
| `browser_compress_memory` | - | V8内存压缩 |
| `browser_get_window_handle` | - | 窗口句柄 |
| `browser_get_window_title` | - | OS窗口标题 |
| `browser_get_window_style` | - | 窗口风格值 |
| `browser_set_window_style` | `type`,`style` | 设置窗口风格 |
| `browser_get_run_style` | - | 运行风格 ⚠️ |
| `browser_set_focus` | `focus` | 焦点 |
| `browser_set_auto_resize` | - | 自动调整大小 |
| `browser_move_window` | `x`,`y`,`width`,`height`,`repaint` | 移动窗口 |
| `browser_set_parent` | `hwnd` | 父窗口 |
| `browser_get_main_browser` | - | 打开者信息 |
| `browser_is_same` | `other_id` | 是否同一实例 |
| `browser_is_view` | - | 视图模式 |
| `browser_set_preference` | `name`,`value` | Chromium首选项 ⚠️ |
| `browser_get_extra_data` | - | 额外数据 |
| `browser_user_tags` | - | 用户标识 |
| `browser_find_by_tag` | `tag` | 按标识查找 |
| `browser_find_by_hwnd` | `hwnd` | 按句柄查找 |
| `browser_request_context` | - | 请求环境 |
| `browser_restore_gui` | - | 恢复嵌入式 GUI 布局与欢迎页（debugger 卡死后可用） |

### 二十、IPC/进程 (5)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_send_message` | `name`,`data` | 主进程消息 |
| `browser_ipc_send_all` | `name`,`data` | 全部渲染进程 |
| `browser_ipc_send_to` | `process_id`,`name`,`data` | 指定渲染进程 |
| `browser_ipc_renderer_count` | - | 渲染进程数 |
| `browser_ipc_renderer_ids` | - | 渲染进程ID |

### 二十一、编码 (4)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_base64_encode` | `data` | Base64编码 |
| `browser_base64_decode` | `data` | Base64解码 |
| `browser_uri_encode` | `data` | URI编码 |
| `browser_uri_decode` | `data` | URI解码 |

### 二十二、框架 (6)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_get_frames` | - | 框架列表 ⏳ |
| `browser_frame_names` | - | 框架名称 ⏳ |
| `browser_frame_by_name` | `name` | 按名查找 |
| `browser_get_focused_frame` | - | 焦点框架 |
| `browser_create_url_request` | `url`,`method` | URL请求 ⏳ |
| `browser_task_runner_post` | `code`,`thread_id` | 线程任务 ⏳ |

### 二十三、VIP高级 (9) 🔒

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_vip_execute_js_context` | `code`,`context_id`,`frame_id` | 指定环境JS |
| `browser_vip_dom_get_document` | `depth` | CDP DOM文档 ⏳ |
| `browser_vip_dom_search` | `query`,`search_id` | CDP文本搜索 ⏳ |
| `browser_vip_enable_js_env` | `enable` | JS执行环境 |
| `browser_vip_get_js_env_ids` | - | JS环境ID |
| `browser_vip_enable_inspector` | `enable`,`repaint` | Inspector |
| `browser_vip_touch_emulation` | `enable`,`max_points` | 触摸模拟 |
| `browser_vip_websocket_intercept` | `enable`,`url` | WS拦截 |
| `browser_vip_orientation` | `type`,`angle` | 屏幕方向 ⚠️ |

### 二十四、VIP插件 (3) 🔒

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_vip_load_extension` | `crx_path` | 加载CRX |
| `browser_vip_unload_extension` | `extension_id` | 卸载插件 |
| `browser_vip_extension_info` | `extension_id` | 插件信息 |

### 二十五、JS逆向/CDP Hook (18) 🔒

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_reverse_hook` | `target`,`type`(function_call/xhr_fetch/websocket),`capture_args`,`capture_return`,`capture_stack` | CDP/V8级无侵入函数Hook |
| `browser_reverse_strings` | `mode`(suspicious/decrypt_array),`min_length`,`max_results` | 提取可疑字符串/加密数组 |
| `browser_reverse_verify` | `original`,`reimplementation`,`test_inputs`,`compare_mode` | 验证重实现算法 |
| `browser_reverse_cookie_sources` | - | Cookie归因分析 |
| `browser_reverse_env` | - | 浏览器环境全量收集(40+变量) |
| `browser_reverse_instrument` | `target`,`mode`(transparent/interpreter) | JSVMP解释器透明插桩 |
| `browser_reverse_search` | `query`,`script_url` | 全局脚本搜索 |
| `browser_reverse_initiator` | `url_pattern`,`request_id` | XHR+fetch调用栈溯源 |
| `browser_reverse_preset` | `preset`(xhr/fetch/cookie/websocket/crypto/debugger/all) | 一键预设Hook |
| `browser_reverse_setup` | `disable_debugger`,`user_agent`,`disable_automation_flag` | 反检测预配置 |
| `browser_reverse_extract` | `mode`(scan/download/analyze),`url_pattern`,`script_index`,`keyword` | 静态加密模块提取+分析 |
| `browser_reverse_cdp_hook` | `function_name`,`object_id`,`condition` | CDP函数调用级别断点(Ghostwire风格) |
| `browser_reverse_profile` | `action`(start/start_precise/stop/query) | JS CPU性能分析 |
| `browser_reverse_dom_breakpoint` | `type`(xhr/fetch/dom_event/timer),`target` | DOM/XHR事件断点 |
| `browser_reverse_preload` | `code`,`file` | Page.addScriptToEvaluateOnNewDocument预注入 |
| `browser_reverse_call_fn` | `object_id`,`arguments` | CDP远程函数调用 |
| `browser_reverse_websocket` | `action`(enable/query) | WebSocket消息拦截 |
| `browser_reverse_heap` | `action`(snapshot/start_sampling/stop_sampling/get_object),`object_id` | 堆内存分析 |
| `browser_reverse_runtime` | `action`(properties/evaluate/global),`object_id`,`expression` | Runtime运行时分析 |
| `browser_reverse_network_intercept` | `action`(enable/disable),`url_pattern` | 网络请求拦截 |
| `browser_reverse_patch` | `target`,`code`,`file`,`mode`(replace/before/after/intercept) | **v2.8** 函数运行时热补丁; 原函数→.__mcp_original__ |
| `browser_reverse_detect_traps` | - | **v2.8** 检测7类反调试陷阱(debugger语句/toString重写等) |

### 二十六、v2.8 反检测增强 (4)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_antidetect_presets` | `preset`(stealth/basic/full) | **v2.8** 一键部署反检测; stealth去webdriver; basic+指纹随机; full全伪装 |
| `browser_permission_spoof` | `action`(apply/reset),`state`(granted/denied/prompt),`permissions` | **v2.8** 权限API伪装(7种); JS注入不需VIP |
| `browser_canvas_noise` | `action`(inject/remove),`level`(1-5) | **v2.8** Canvas指纹噪点注入; 纯JS不需VIP |
| `browser_font_randomize` | `action`(random/reset),`count`,`seed` | **v2.8** 字体枚举随机化(VIP+JS双通道) |

### 二十七、v2.8 自动化/网络增强 (2)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_retry` | `tool`,`args`,`max_retries`,`backoff_ms`,`max_total_ms` | **v2.8** 带线性退避的重试机制 |
| `browser_network_export` | `format`(har/json),`limit` | **v2.8** 网络日志HAR/JSON导出(兼容Chrome DevTools) |

### 二十八、调试增强 (1)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_debugger_auto` | `breakpoint`,`max_hits`,`expressions`,`max_ms`,`url` | 自动断点求值循环(持续监控) |

### 二十九、系统 (1)

| 工具 | 参数 | 说明 |
|------|------|------|
| `browser_shutdown` | `confirm`,`delay_seconds` | 安全关闭AI浏览器进程 |

---

## 异步工具完整列表 (共 40+ 个)

以下工具返回异步任务ID（`task_` 前缀），需 `mcp_result` 轮询：

**JS/内容类：** `browser_get_title` `browser_evaluate` `browser_console_eval` `browser_get_source` `browser_get_text`

**DOM/填表类：** `browser_dom_query` `browser_dom_set_value` `browser_dom_get_html` `browser_fill_exists` `browser_fill_attr_get`

**Cookie/缓存类：** `browser_get_cookies` `browser_get_all_cookies` `browser_clear_cache` `browser_clear_cache_browser`

**截图/下载类：** `browser_screenshot` `browser_print_to_pdf` `browser_download_image`

**CDP类：** `browser_cdp` `browser_cdp_call` `browser_network_body`

**VIP类：** `browser_vip_execute_js_context` `browser_vip_dom_get_document` `browser_vip_dom_search`

**其他：** `browser_get_frames` `browser_frame_names` `browser_create_url_request` `browser_file_dialog` `browser_task_runner_post` `browser_wait`

**CDP 异步特殊性：** CDP 工具 task_id 使用命令ID格式（`NNN_NNN`），而非 `task_` 前缀。`mcp_result` 需用命令ID查询。

## 已知限制 (6个stub)

| 工具 | 原因 |
|------|------|
| `browser_vip_fingerprint_ssl` / `fingerprint action=ssl` | TLS枚举触发库模板错误 |
| `browser_vip_orientation` | 屏幕方向枚举触发库模板错误 |
| `browser_set_preference` | 值类型构造API待确认 |
| `browser_get_run_style` | 窗口运行风格枚举触发库模板错误 |
| `browser_get_global_cache_dir` | 函数触发库模板错误 (未注册) |
| `browser_get_process_type` | 函数触发库模板错误 (未注册) |

## 未注册隐藏工具

> ✅ v2.7 — 所有工具均已注册，无隐藏工具。

## 编码规范

### 空值检查 (v2.0 统一)
所有 `取主浏览器()`、`取VIP控制器()`、`取安全主框架()` 统一使用 `== 假` 模式：
```火山
变量 browser = 取主浏览器 ()
如果 (browser.是否为空 () == 假)
{
    // ... 使用 browser
}
返回 (命令失败 (命令ID, 错误_无浏览器))
```

### 响应类型规则
- **内核/指纹/VIP修改** → `响应_需要刷新` (设置 `needs_reload: true`)
- **异步操作(回调)** → `命令成功_异步` (返回 `task_` 前缀ID)
- **同步操作** → `命令成功`
- **结构化数据** → `命令成功_原始JSON`

### 命名规则
- 所有工具同时支持 `browser.name` 和 `browser_name`
- 代码内部 `||` 双路由

## 测试

> **单浏览器实例**：全量脚本必须**顺序**执行，勿并行（会争用 MCP 锁与页面状态）。

### 一键全量（推荐）

```bash
# AI浏览器.exe 已启动后
node tests/batch_test.js           # 分类全量测试
node tests/batch_test.js system    # 仅系统类
```

测试覆盖 237 个 MCP 工具，按类别分批执行。

### 分项脚本

| 脚本 | 用途 |
|------|------|
| `regression_sync_wait.js` | sync-wait / workflow / batch 专项（13 项） |
| `full_test.js` | HTTP 冒烟（health、tools/list、ping 等 7 项） |
| `tool_test_all.js` | 237 工具注册表冒烟（动态读 `/tools/list`；FAIL=0 为通过） |
| `scenario_test.js --skip-vip` | 场景集成（fixture 页 + 填表/Cookie/网络） |
| `scenarios/run_all_scenarios.js` | **Hook + 场景顺序包**（v8/js_http/自动化/断点/逆向） |
| `scenarios/v8_hook_test.js` | V8 inject / persist / navigate_block |
| `scenarios/js_http_hook_test.js` | Console / HTTP network / 导航 Hook |
| `scenarios/reverse_analyze.js [url]` | 页面 JS + 网络层脚本清单 |
| `scenarios/douyin_xhr_encrypt_scan.js [url]` | XHR/fetch POST 加密字段扫描（默认抖音） |
| `scenarios/debugger_session.js` | CDP 断点：wait → inspect → resume |
| `scenarios/debugger_inspect_demo.js` | 断点处变量/函数/对象属性演示 |
| `scenarios/debugger_unfreeze.js` | 解除 debugger 暂停导致的页面卡死 |
| `scenarios/debugger_recover.js` | tool_test 后 debugger 恢复冒烟 |
| `scenarios/automation_flow.js` | 填表 + batch 演示 |
| `workflow_runner.js --server hello` | 工作流端到端 |

报告：`run_all_tests_report.json`、`tool_test_report.json`、`scenario_test_report.json`

### 单工具调试

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"browser_navigate","arguments":{"url":"about:blank"}}}
```

### 异步 / sync-wait

- 白名单工具：默认一次 `tools/call` 返回结果（含 `_sync_waited`）
- 其他：设 `async_only:true` 得 `task_id`，再 `mcp_result` 轮询

## 文档索引

| 文档 | 路径 |
|------|------|
| 使用技能书 | `docs/使用技能书.md`（编译 → `linker/docs/`） |
| 客户使用手册 | `docs/客户使用手册.md`（编译 → `linker/docs/`） |
| MCP 配置说明书 | `docs/MCP工具配置说明书.md` |
| 在线 HTML | `http://127.0.0.1:9222/docs/` |
| 工具全集 | `skills/AI浏览器MCP.md` |

## 联系方式
- QQ: 212577526 | QQ群: 737680767 | 微信: XSMZAS1
- 火山编程交流群: https://qm.qq.com/q/Hpv6qm8qUE

## 配置文件
位置: 源码 `src/mcp_config.json`，编译后 `linker/mcp_config.json`
```json
{
  "port": 9222,
  "bind_address": "127.0.0.1",
  "disable_auth": true,
  "rate_limit_per_minute": 0,
  "enable_network_log": true,
  "enable_console_log": false,
  "enable_response_cache": false,
  "network_log_max_bytes": 262144,
  "auto_download_save": true,
  "auto_dismiss_js_dialog": false
}
```
详见 `src/mcp_config.README.md`。修改后需重启 AI浏览器。

## v2.8 CDP 域覆盖

| CDP 域 | 已封装MCP工具数 | 关键方法 |
|---------|:-----------:|------|
| **Debugger** | 15 | enable/pause/resume/step×3/setBreakpoint/stack/evaluate/wait_paused/last_paused/inspect/flow/script_source/auto/setSkipAllPauses/setBlackboxPatterns/setAsyncCallStackDepth/setBreakpointsActive/searchInContent |
| **Runtime** | 11 | evaluate/getProperties/globalLexicalScopeNames/callFunctionOn/queryObjects/compileScript/awaitPromise |
| **Profiler** | 6 | enable/start/stop/setSamplingInterval/getBestEffortCoverage/startPreciseCoverage/takePreciseCoverage/stopPreciseCoverage |
| **Network** | 5 | enable/getResponseBody/setRequestInterception/setCacheDisabled/emulateNetworkConditions |
| **DOM/DOMD** | 5 | setXHRBreakpoint/setEventListenerBreakpoint/setInstrumentationBreakpoint/getEventListeners/resolveNode/requestNode |
| **Page** | 3 | addScriptToEvaluateOnNewDocument/setBypassCSP |
| **HeapProfiler** | 4 | takeHeapSnapshot/startSampling/stopSampling/getObjectByHeapObjectId |
| **Input** | 2 | dispatchMouseEvent/dispatchKeyEvent |
| **Storage** | 2 | getCookies/clearCookies |
| **Tracing** | 2 | start/end |
| **Emulation** | 1 | setFocusEmulationEnabled |
| **CSS/LayerTree** | 2 | startRuleUsageTracking/stopRuleUsageTracking/snapshotCommandLog/compositingReasons |
| **总计** | **58** | 11个CDP域全覆盖 |

## 版本历史

| 版本 | 变更 |
|------|------|
| 1.6 | 初始版 |
| 1.7 | 移除 `fingerprint_platform`; 补全20+遗漏工具; 异步索引 |
| 2.0 | 全面审计优化: 注册2隐藏工具; 事件Hook架构; 任务ID加密; 双通道拦截; 空值检查统一; 重定向循环保护; CDP异步一致性; JS返回值11种+Cef值类型9种全覆盖; 孤儿功能清理; 5空分发器删除; 测试引擎重写(自动刷新/崩溃检测/async轮询); 代码清理(备份/缓存/测试残留) |
| 2.1 | HTTP CORS 辅助层: 欢迎页 HTTP fetch; `/tools` `/json` CORS |
| 2.4 | 模块拆分 Core/Form/VIP/System/HTTP; 欢迎页 `/docs`; mcp_bridge |
| 2.5 | **sync-wait** 白名单 + batch 跟随; **workflow** 四工具; DOM 语义失败; `workflow_stop` 标志修复; `name/file` 优先读工作流; 测试套件 `run_all_tests.js` |
| 2.5.2 | **断点开发者流** `wait_paused`/`last_paused`/`inspect`/`flow`；求值结果解析 `{ok,type,value}`；等待前清除陈旧 paused；CDP resume/step sync-wait |
| 2.5.1 | **persist V8** 改浏览器进程 `应用持久V8到框架`; 场景脚本 `scenarios/*`; collect 预备 action; Hook 测试文档; debugger 工作流 `max_ms` 45s |
| 2.6 | **客户文档**：`客户使用手册` + 使用技能书 + MCP配置说明书（`docs/` 编译输出）；**客户使用手册**面向终端客户 |
| 2.8.0 | **31新工具** (237→268)：**反检测5** (`antidetect_presets` stealth/basic/full + `permission_spoof` + `canvas_noise` + `font_randomize` + `webgl_vendor` + `languages`)；**逆向12** (`reverse_detect_traps` + `reverse_patch` replace/before/after/intercept + `reverse_skip_pauses` + `reverse_listeners` + `reverse_query_objects` + `reverse_blackbox` + `reverse_async_stack` + `reverse_cache_disable` + `reverse_compile_script` + `reverse_breakpoints_active` + `reverse_search_script` + `reverse_precise_coverage` start/take/stop + `reverse_bypass_csp` + `reverse_await_promise` + `reverse_input_cdp` mouse/key + `reverse_trace` + `reverse_evaluate_silent` + `reverse_cookie_cdp` + `reverse_network_conditions` + `reverse_dom_resolve` + `reverse_emulate_focus` + `reverse_css_coverage` + `reverse_layer_tree`)；**自动化3** (workflow `condition`+`{{step.N.result}}` + `browser_retry` 退避重试)；**网络1** (`browser_network_export` HAR/JSON)；**协议** (`resources/list` + `prompts/list`)；**增强** `browser_extract` tables 自动表头；**代码** `注册命令双变体` 辅助方法 |
