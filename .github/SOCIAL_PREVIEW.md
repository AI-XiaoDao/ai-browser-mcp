# GitHub 仓库展示配置

维护者可在 [仓库 Settings](https://github.com/AI-XiaoDao/ai-browser-mcp/settings) 中配置以下项，提升搜索与推荐曝光。

## Social Preview（1280×640）

1. 打开 **Settings → General → Social preview**
2. 上传图片：推荐基于 [demo-douyin-post-scan.png](demo-douyin-post-scan.png) 制作 1280×640 封面
3. 封面文字建议：**AI Browser MCP · 217 tools · Windows · 一句话采集/逆向/定位**

## About 描述（建议）

**英文（GitHub 默认）：**
```
Windows local MCP browser automation — 217 tools, any AI agent (Cursor/Claude/Cline). One sentence: scrape, reverse, locate. FBrowser CEF · MIT · x64 + win32
```

**中文（Discussions / 简介补充）：**
```
Windows 本地 MCP 浏览器自动化 — 217 工具，Cursor/Claude 一句话：采集、逆向 POST、CDP 定位。下载即用，MIT 开源。
```

## Topics（建议保留/补充）

当前已有：`windows` `mcp` `model-context-protocol` `cursor` `browser-automation` `cef` `fbrowser` `volcano` `ai-browser`

建议追加：

```
web-scraping
playwright-alternative
reverse-engineering
cdp
automation
chinese
```

一键设置（需 `gh auth login`）：

```powershell
gh repo edit AI-XiaoDao/ai-browser-mcp `
  --description "Windows local MCP browser automation — 217 tools, any AI agent (Cursor/Claude/Cline). One sentence: scrape, reverse, locate. FBrowser CEF · MIT · x64 + win32" `
  --add-topic web-scraping,playwright-alternative,reverse-engineering,cdp,automation,chinese
```

## Discussions 置顶

欢迎帖：https://github.com/AI-XiaoDao/ai-browser-mcp/discussions/1 — 请在 Discussions 列表 **Pin** 置顶。

## Release 附件清单（v2.6.0）

| 文件 | 平台 |
|------|------|
| `AI-Browser-MCP-x64-v2.6.0.zip` | 64 位运行包 |
| `AI-Browser-MCP-win32-v2.6.0.zip` | 32 位运行包 |
| `AI-Browser-MCP-cpp-x64-v2.6.0.zip` | x64 C++ 对照 |
| `AI-Browser-MCP-cpp-win32-v2.6.0.zip` | win32 C++ 对照 |

## MCP 目录提交（可选）

- [MCP Registry](https://github.com/modelcontextprotocol/registry)
- Awesome MCP 列表 PR（搜索 `awesome-mcp-servers`）

宣传文案见仓库根目录 [OPEN_SOURCE.md](../OPEN_SOURCE.md) · 英文 [QUICKSTART_EN.md](../CEFbro/AI浏览器/docs/QUICKSTART_EN.md)。

## SEO 检查清单

- [x] GitHub Topics（15 个，含 `web-scraping` `playwright-alternative` 等）
- [x] README 首段 + 对比表 + 常见搜索问题（`<details>`）
- [x] [QUICKSTART_EN.md](../CEFbro/AI浏览器/docs/QUICKSTART_EN.md) 英文长尾词
- [x] docs / 欢迎页 `<meta name="description">`
- [ ] Social Preview 1280×640 图片（Settings 手动上传）
- [ ] Discussions 欢迎帖 Pin 置顶
- [ ] 提交 [MCP Registry](https://github.com/modelcontextprotocol/registry) / Awesome MCP 列表 PR
- [ ] 每月 1 条 Show and tell 案例（Discussions）

## 高价值外链关键词（发帖时使用）

中文：浏览器 MCP · Cursor 浏览器自动化 · 网页采集 MCP · POST 逆向 · CDP 断点 · 火山视窗 FBrowser

English: Cursor browser MCP · Windows MCP server · web scraping MCP · Playwright alternative · Model Context Protocol browser · local CEF automation
