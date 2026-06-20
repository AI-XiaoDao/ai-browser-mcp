## AI浏览器 MCP Server v2.6.0

**Windows x64 本地浏览器自动化 MCP 服务** — 217 个 `browser_*` 工具，供 Cursor / Claude 通过 `mcp_bridge.js` 调用。

---

### 下载（二选一或都下）

| 文件 | 大小 | 内容 |
|------|------|------|
| **AI-Browser-MCP-x64-v2.6.0.zip** | ~157 MB | **运行包**：`AI浏览器.exe`、CEF 运行时、`mcp_bridge.js`、`docs/`、`workflows/` |
| **AI-Browser-MCP-cpp-x64-v2.6.0.zip** | ~0.3 MB | **C++ 对照**：火山编译生成的 `vpkg_*.cpp` / `vcls_*.h`（33 + 218 文件） |

**重要说明（四层对照，详见 [README](https://github.com/AI-XiaoDao/ai-browser-mcp#-开源范围与火山编译目录)）：**

| 层级 | 内容 | Release |
|:--:|------|:--:|
| ① | 权威源码 `src/*.wsv` | Git 仓库 |
| ② | 生成 C++ `generated-cpp/`（= 编译时 `project/`） | cpp zip |
| ③ | 中间产物 `linker/out/`（`.obj`/`.pch`，**不是源码**） | **不含** |
| ④ | 运行成品 exe + CEF + 脚本 | x64 zip |

---

### 快速开始

1. 下载并解压 **AI-Browser-MCP-x64-v2.6.0.zip**（文件与 exe **同目录**，无额外 `linker/` 子文件夹）
2. 双击 **AI浏览器.exe**
3. 浏览器打开 http://127.0.0.1:9222/health ，确认 `"status":"ok"`、`"version":"2.6.0"`
4. Cursor 配置解压目录下的 **mcp_bridge.js**：

```json
{
  "mcpServers": {
    "ai-browser": {
      "command": "node",
      "args": ["D:/你的解压路径/mcp_bridge.js"],
      "env": {
        "AI_BROWSER_MCP_HTTP_POST": "http://127.0.0.1:9222/mcp"
      }
    }
  }
}
```

5. 自检：`node mcp_bridge.js --check`

**要求**：Windows 10/11 x64 · Node.js 18+（仅 Cursor 桥接需要）

---

### 源码与文档（Git 仓库）

| 资源 | 路径 |
|------|------|
| 仓库 | https://github.com/AI-XiaoDao/ai-browser-mcp |
| 开源公告 / FAQ | [OPEN_SOURCE.md](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/OPEN_SOURCE.md) |
| 客户使用手册 | [docs/客户使用手册.md](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/CEFbro/AI浏览器/docs/客户使用手册.md) |
| 217 工具参考 | [AI浏览器MCP.md](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/CEFbro/AI浏览器/skills/AI浏览器MCP.md) |
| 更新日志 | [CHANGELOG.md](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/CHANGELOG.md) |

---

### 本版本特性

- 217 MCP 工具：导航、填表、DOM、网络、工作流、CDP 调试（部分 VIP）
- JSON-RPC：WebSocket + HTTP POST `http://127.0.0.1:9222/mcp`
- sync-wait、欢迎页控制台、工作流 JSON
- MIT 开源

---

### 支持

QQ 212577526 · QQ群 737680767 · [Issues](https://github.com/AI-XiaoDao/ai-browser-mcp/issues) · [Discussions](https://github.com/AI-XiaoDao/ai-browser-mcp/discussions/1)
