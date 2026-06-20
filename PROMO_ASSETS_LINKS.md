# 宣传素材 · 标准 PDF / 长图 / 链接

> 项目：https://github.com/AI-XiaoDao/ai-browser-mcp  
> 重新生成：`python release/build-promo-pdf-image.py`（需 Playwright + Chromium）

---

## 文件清单

| 文件 | 格式 | 用途 |
|------|------|------|
| [AI-Browser-MCP-Promo-v2.6.pdf](../AI-Browser-MCP-Promo-v2.6.pdf) | PDF（含可点击链接） | 论坛附件、邮件、打印 |
| [AI-Browser-MCP-Promo-v2.6-long.png](../AI-Browser-MCP-Promo-v2.6-long.png) | 长图 1080px 宽 | 论坛 `[img]`、QQ、公众号配图 |
| [AI-Browser-MCP-Promo-v2.6.docx](../AI-Browser-MCP-Promo-v2.6.docx) | Word | 可编辑宣传手册 |
| [promo.html](../promo.html) | 在线页 | 浏览器打开 / GitHub Pages |
| [promo-poster.html](../promo-poster.html) | 海报源码 | PDF/长图导出源 |

---

## GitHub 直链（push 后复制发帖）

**仓库根目录 raw 链接：**

```
PDF 长文档（可点击链接）：
https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/AI-Browser-MCP-Promo-v2.6.pdf

宣传长图（1080px）：
https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/AI-Browser-MCP-Promo-v2.6-long.png

演示截图：
https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/.github/demo-douyin-post-scan.png

在线 HTML 宣传页：
https://github.com/AI-XiaoDao/ai-browser-mcp/blob/main/promo.html

下载运行包：
https://github.com/AI-XiaoDao/ai-browser-mcp/releases/download/v2.6.0/AI-Browser-MCP-x64-v2.6.0.zip

仓库首页：
https://github.com/AI-XiaoDao/ai-browser-mcp
```

**Release 附件链接（推荐大文件）：**  
发版时可将 PDF / 长图上传到 [Releases v2.6.0](https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0) Assets，获得更稳定的下载地址。

---

## Discuz (DZ) BBCode

```
[b][size=4][color=#0066cc]AI浏览器 MCP Server v2.6 — 宣传长图[/color][/size][/b]

[align=center][img]https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/AI-Browser-MCP-Promo-v2.6-long.png[/img][/align]

[b]PDF 宣传手册（含可点击链接）：[/b]
[url=https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/AI-Browser-MCP-Promo-v2.6.pdf]点击下载 PDF[/url]

[b]下载运行包：[/b]
[url=https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0]GitHub Releases v2.6.0[/url]

[b]仓库：[/b][url=https://github.com/AI-XiaoDao/ai-browser-mcp]github.com/AI-XiaoDao/ai-browser-mcp[/url]

作者 QQ：212577526
```

---

## 通用纯文本（带链接）

```
【开源】AI浏览器 MCP Server v2.6

Windows 本地 217 工具 · 任意 AI 代理一句话操控真实浏览器 · MIT

宣传长图：https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/AI-Browser-MCP-Promo-v2.6-long.png
PDF 手册：https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/AI-Browser-MCP-Promo-v2.6.pdf
下载 exe：https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0
仓库：https://github.com/AI-XiaoDao/ai-browser-mcp

作者 QQ：212577526
```

---

## HTML 嵌入长图

```html
<a href="https://github.com/AI-XiaoDao/ai-browser-mcp/releases/tag/v2.6.0" target="_blank" rel="noopener">
  <img src="https://github.com/AI-XiaoDao/ai-browser-mcp/raw/main/AI-Browser-MCP-Promo-v2.6-long.png"
       alt="AI Browser MCP v2.6 宣传长图" width="1080" style="max-width:100%;height:auto;">
</a>
```

---

## 重新生成说明

```bash
# 1. 安装依赖（首次）
pip install playwright
python -m playwright install chromium

# 2. 生成 PDF + 长图
python release/build-promo-pdf-image.py

# 3. 生成 Word（可选）
python release/build-promo-docx.py
```

修改内容请编辑 `promo-poster.html`（导出用）或 `promo.html`（交互网页）后重新运行脚本。

---

*AI Browser MCP Server v2.6.0 · 作者 QQ 212577526*
