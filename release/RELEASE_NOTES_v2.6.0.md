## AI浏览器 MCP Server v2.6.0

**Windows x64 本地浏览器自动化 MCP 服务** — 217 个 `browser_*` 工具，供 **任意 AI 代理**（Cursor / Claude / 自研 MCP 客户端）通过 HTTP、WebSocket 或 `mcp_bridge.js` 调用。

> **🎁 下载即全功能**：本 Release 的 **`AI-Browser-MCP-x64-v2.6.0.zip`** 已包含 **全部 217 个工具**（截图、CDP 调试器、指纹、拦截等），解压运行即可。

---

### 下载

| 文件 | 大小 | 内容 |
|------|------|------|
| **AI-Browser-MCP-x64-v2.6.0.zip** | ~157 MB | **x64 运行包**：`AI浏览器.exe`、CEF、`mcp_bridge.js`、`docs/`、`workflows/` |
| **AI-Browser-MCP-win32-v2.6.0.zip** | ~136 MB | **win32 运行包**（32 位 Windows） |
| **AI-Browser-MCP-cpp-x64-v2.6.0.zip** | ~0.3 MB | **x64 C++ 对照** |
| **AI-Browser-MCP-cpp-win32-v2.6.0.zip** | ~0.3 MB | **win32 C++ 对照** |

**重要说明（四层对照，详见 [README](https://github.com/AI-XiaoDao/ai-browser-mcp#-开源范围与火山编译目录)）：**

| 层级 | 内容 | Release |
|:--:|------|:--:|
| ① | 权威源码 `src/*.wsv` | Git 仓库 |
| ② | 生成 C++ `generated-cpp/`（= 编译时 `project/`） | cpp zip |
| ③ | 中间产物 `linker/out/`（`.obj`/`.pch`，**不是源码**） | **不含** |
| ④ | 运行成品 exe + CEF + 脚本 | x64 / win32 zip |

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
6. 对 AI 说一句话，例如：「滚动商品列表，把标题价格采成 JSON」

**要求**：Windows 10/11 x64 · Node.js 18+（仅 Cursor 桥接需要）

---

### 典型场景（复制到 Cursor）

| 场景 | 示例话术 |
|------|----------|
| **采集数据** | 「滚动加载列表，把标题、价格、链接采成 JSON」 |
| **逆向算法** | 「扫描 XHR/fetch POST，标出疑似加密字段」 |
| **定位算法** | 「提交时下断点，定位 sign 在哪个 JS 函数，给源码片段」 |
| **自动填表** | 「用账号登录后台，导出订单表前 20 行」 |

完整说明：[README · 典型场景](https://github.com/AI-XiaoDao/ai-browser-mcp#-典型场景一句话自动执行) · [OPEN_SOURCE · 场景速查卡](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/OPEN_SOURCE.md#-场景速查卡复制到群--笔记)

**场景速查（复制到 Cursor）**

| 场景 | 一句话 |
|------|--------|
| 采集 | 「滚动列表，采标题价格 JSON」 |
| 逆向 | 「扫描 POST，标疑似加密字段」 |
| 定位 | 「断点跟到 sign 函数，给源码」 |
| 填表 | 「登录后台，导出订单表」 |
| 复用 | 「存成 workflow，下次一键跑」 |

---

### 源码与文档（Git 仓库）

| 资源 | 路径 |
|------|------|
| 仓库 | https://github.com/AI-XiaoDao/ai-browser-mcp |
| 开源公告 / FAQ | [OPEN_SOURCE.md](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/OPEN_SOURCE.md) |
| 客户使用手册 | [docs/客户使用手册.md](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/CEFbro/AI浏览器/docs/客户使用手册.md) |
| 217 工具参考 | [AI浏览器MCP.md](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/CEFbro/AI浏览器/skills/AI浏览器MCP.md) |
| 场景 / Hook / 逆向 | [场景与Hook测试.md](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/CEFbro/AI浏览器/skills/场景与Hook测试.md) |
| 更新日志 | [CHANGELOG.md](https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/CHANGELOG.md) |

---

### 本版本特性

- **217 MCP 工具**：导航、填表、DOM、网络、工作流、CDP 调试等 — **下载即全功能**
- **一句话自动执行**：Agent 串联 navigate → collect / inject / debugger，sync-wait 逐步等结果
- **JSON-RPC**：WebSocket + HTTP POST `http://127.0.0.1:9222/mcp`
- sync-wait、batch、欢迎页控制台、工作流 JSON
- 事件 Hook + 场景脚本（如 `douyin_xhr_encrypt_scan.js`）
- **MIT 开源**：`.wsv` 源码 + `generated-cpp/` + 技能书 + 全量测试

---

### 支持

QQ 212577526 · QQ群 737680767 · [Issues](https://github.com/AI-XiaoDao/ai-browser-mcp/issues) · [Discussions](https://github.com/AI-XiaoDao/ai-browser-mcp/discussions/1)
