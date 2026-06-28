---
name: AI浏览器MCP配置
description: mcp_config.json / Cursor / VIP — MCP 配置说明书（客户见「零、给客户看的3步」）
version: 2.8.1
trigger: mcp_config|配置文件|vip_code|端口|bind_address|Cursor配置|mcp.json|环境变量|客户配置
---
# AI浏览器 — MCP 工具配置说明书

> 编译输出：`linker/mcp_config.json` + `linker/docs/MCP工具配置说明书.md`

## 客户 3 步（详见 docs 完整版）

1. 打开 exe 同目录 `mcp_config.json`
2. 填写 `"vip_code": "授权码"`（基础功能可不填）
3. 保存并**重启** AI浏览器.exe

Cursor：欢迎页 `http://127.0.0.1:9222/` → 复制 Cursor 配置 → `.cursor/mcp.json` → 重启 Cursor。

## 字段速查

| 字段 | 默认 | 说明 |
|------|------|------|
| `port` | 9222 | MCP 端口 |
| `bind_address` | 127.0.0.1 | 非本机须配 `api_key` |
| `vip_code` | "" | VIP 授权（CDP/截图/指纹等） |
| `enable_network_log` | true | 网络日志 |
| `enable_console_log` | false | 控制台日志 |

## Cursor mcp.json

```json
{
  "mcpServers": {
    "ai-browser": {
      "command": "node",
      "args": ["安装路径/mcp_bridge.js"],
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

## 详见

- `docs/客户使用手册.md` — 客户安装与 Cursor 分步
- `docs/MCP工具配置说明书.md` — 全字段与场景配置
- `src/mcp_config.README.md` — 简表

## 客户排错

- 网络 list 空 → `enable_network_log:true` 后重新 navigate
- 扫描 timeout → `debugger_unfreeze.js`；勿并行 MCP 脚本
