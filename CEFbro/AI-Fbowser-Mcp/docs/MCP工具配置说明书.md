# AI浏览器 — MCP 工具配置说明书

> **版本** 2.6 · 修改配置后需**重启** AI浏览器.exe  
> **客户快速配置** → 见下文「零、给客户看的 3 步」；完整字段见第 2 节。

---

## 零、给客户看的 3 步

### ① 找到配置文件

与 **AI浏览器.exe** 同一文件夹里的 `mcp_config.json`（用记事本打开）。

### ② 按需修改（多数客户只需改 VIP）

```json
{
  "port": 9222,
  "vip_code": "在这里填写您的授权码"
}
```

不填 `vip_code` 时，基础浏览/填表/网络日志仍可用；截图、CDP、指纹等需要 VIP。

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
  "auto_dismiss_js_dialog": false
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

### 2.3 VIP 与浏览器行为

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `vip_code` | string | `""` | FBrowser VIP 授权码；空则 VIP/CDP/指纹等工具返回「VIP控制器不可用」 |
| `auto_download_save` | bool | `true` | 下载是否自动保存 |
| `auto_dismiss_js_dialog` | bool | `false` | 是否自动关闭 alert/confirm 等 JS 对话框 |

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
        "AI_BROWSER_MCP_PORT": "9222",
        "AI_BROWSER_MCP_CURSOR_MODE": "0"
      }
    }
  }
}
```

写入 **`.cursor/mcp.json`**（项目内）或 **`~/.cursor/mcp.json`**（全局），保存后**重启 Cursor**。

桥接会自动修复 Cursor 兼容问题：补全 JSON-RPC `id`、协议版本 `2024-11-05`、schema `text`→`string`。

| 环境变量 | 说明 |
|----------|------|
| `AI_BROWSER_MCP_CURSOR_MODE` | `0` 全量 216 工具（默认）；`1` 精简约 55 个常用工具 |

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
| `AI_BROWSER_MCP_PORT` | exe 启动 | 端口 |
| `AI_BROWSER_MCP_HEALTH` | exe 启动 | 健康检查 URL |
| `AI_BROWSER_MCP_HTTP_POST` | 手动/桥接 | HTTP JSON-RPC 地址 |
| `AI_BROWSER_MCP_CONNECT` | 手动 | `mcp_connect.json` 路径 |
| `AI_BROWSER_MCP_HOST` | 脚本 | 场景客户端主机，默认 `127.0.0.1` |
| `AI_BROWSER_MCP_CURSOR_MODE` | 桥接 | `0` 全量工具；`1` 精简工具（Cursor loading 时可试） |
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

### 7.3 VIP 全功能

```json
{
  "vip_code": "您的授权码"
}
```

启用：CDP、指纹、VIP 鼠标键盘、截图、资源拦截 modify 等。

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
| VIP 工具全失败 | 配置 `vip_code` 并重启 |
| `browsers: 0` | 等待 GUI 创建主浏览器 |
| 网络 list 为空 | `enable_network_log:true` 或 enable 后再 navigate |
| 文档 404 | 确认 `linker/docs/` 存在（重新编译） |
| 扫描 timeout | `debugger_unfreeze.js` 后重试；勿并行 MCP 脚本 |

---

## 10. 相关文档

- [客户使用手册.md](./客户使用手册.md) — **终端客户**安装、Cursor、VIP、FAQ
- [使用技能书.md](./使用技能书.md) — 技术实操与场景脚本
- [index.html](./index.html) — 在线 HTML 文档
- `skills/AI浏览器MCP.md` — 236 工具完整参考
