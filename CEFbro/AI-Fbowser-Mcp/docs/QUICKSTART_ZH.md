# AI浏览器 MCP — 中文快速上手（SEO）

> **Windows 本地浏览器自动化 MCP 服务器** — 234 个工具，支持 Cursor、Claude Desktop、Cline 及任意 MCP 客户端。  
> 仓库：https://github.com/AI-XiaoDao/ai-browser-mcp

## 这是什么？

**AI浏览器 MCP Server** 在 Windows 上运行真实 **FBrowser CEF** 浏览器，通过 **Model Context Protocol（MCP 模型上下文协议）** 对外提供 **234 个 `browser_*` 工具**。

无需手写 **Playwright / Puppeteer** 脚本 — 在 Cursor 里**一句话**完成：**网页数据采集**、**POST 逆向 Hook**、**CDP 断点定位 sign 算法**、**自动填表 RPA**。

## 下载（x64 / win32）

| 包 | 说明 |
|----|------|
| [AI-Browser-MCP-x64-v2.6.1.zip](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v2.6.1/AI-Browser-MCP-x64-v2.6.1.zip) | 64 位 Windows，~160MB |
| [AI-Browser-MCP-win32-v2.6.1.zip](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v2.6.1/AI-Browser-MCP-win32-v2.6.1.zip) | 32 位 Windows，~140MB |

MIT 开源 · 本机 `127.0.0.1:9222` · 234 工具全开放。

## 三步上手

1. 解压 → 双击 **AI浏览器.exe**
2. 打开 http://127.0.0.1:9222/health → `"status":"ok"`
3. 配置 Cursor / Claude（见下）

## Cursor 配置（stdio MCP 桥接）

```json
{
  "mcpServers": {
    "ai-browser": {
      "command": "node",
      "args": ["D:/你的路径/mcp_bridge.js"],
      "env": {
        "AI_BROWSER_MCP_HTTP_POST": "http://127.0.0.1:9222/mcp"
      }
    }
  }
}
```

自检：`node mcp_bridge.js --check`

## 一句话话术（复制到 Cursor）

```
滚动商品列表，把标题和价格采成 JSON 数组。

扫描 XHR/fetch 的 POST，标出疑似加密的字段并说明依据。

在登录提交时下断点，定位计算 sign 的 JS 函数，给源码片段。

用账号 test / 密码 123456 登录后台，导出订单表前 20 行。
```

## 与 Playwright 对比

| | 自建 Playwright | AI浏览器 MCP |
|--|----------------|--------------|
| 上手 | 写脚本、装环境 | 下载 exe 即用 |
| AI | Agent 现写代码 | **234 预封装 MCP 工具** |
| 逆向 | 手动 Hook | `browser_inject` + 场景脚本 |
| 隐私 | 视部署 | **本机 127.0.0.1** |

## 相关文档

- [完整 README](../../../README.md)
- [234 工具参考](../skills/AI浏览器MCP.md)
- [SEO 关键词矩阵](../../../docs/SEO_KEYWORDS.md)
- [场景与 Hook 测试](../skills/场景与Hook测试.md)

## 搜索关键词

Cursor 浏览器 MCP · Claude Desktop 浏览器 · Windows MCP 服务器 · 网页数据采集 MCP · Playwright 替代 · POST 逆向 Hook · CDP 调试器 · 浏览器自动化 · 火山 FBrowser CEF · 模型上下文协议 · 自动填表 RPA · 本机浏览器 AI 控制
