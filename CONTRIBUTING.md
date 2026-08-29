# 贡献指南 (Contributing)

感谢你愿意为 **AI浏览器 MCP Server** 贡献！以下是参与开发的快速指南。

## 开发环境

- **火山视窗 (Volcano Windows)** 开发平台（本项目为火山 PC 视窗工程）
- Windows 10/11 x64
- 可选：Node.js（仅测试/桥接脚本需要）

## 目录速览

| 路径 | 说明 |
|------|------|
| `CEFbro/AI-Fbowser-Mcp/src/` | 火山源码（16 个 .wsv），**主要开发位置** |
| `CEFbro/AI-Fbowser-Mcp/AI-Fbowser-Mcp.vprj/.vsln` | 火山工程/解决方案 |
| `CEFbro/AI-Fbowser-Mcp/docs/` | 成品在线文档 |
| `docs/ARCHITECTURE.md` | 架构说明（改代码前先读） |
| `release/` | 打包发布脚本 |

## 构建

```powershell
# x64 发布版（GUI 程序必须用 Start-Process -Wait 等待）
$vsln = "路径\\AI-Fbowser-Mcp.vsln"
$p = Start-Process 'E:\\HSPC\\bin\\x64\\voldev_awp.exe' -ArgumentList ('@compile "' + $vsln + '" /r') -Wait -PassThru
# win32: 需临时在 vprj 设置 target_platform = 1（编译后还原，编译器会回写 vprj）
```

产物在 `_int/AI-Fbowser-Mcp/release/{x64,win32}/linker/`。

## 提交规范

1. **先备份再改**：修改 .wsv 前复制一份到 `备份/` 目录
2. **编码**：UTF-8 无 BOM；`.wsv/.vprj` 是解析敏感文件，禁止静默转码
3. **最小增量**：一次一个小改动，保持文件顶层结构不变
4. **不臆造 API**：火山类库 API 以官方文档/类库源码为准，不确定先查证
5. **提交信息**：`type: 简述`（feat/fix/chore/docs/perf），中文描述

## Issue / PR 流程

1. 提交 issue 前先搜索是否已存在；提供复现步骤与日志
2. PR 请描述改动目的与验证方式，保持改动聚焦
3. 大改动（新增工具类）建议先开 issue 讨论设计

## 测试

- 启动服务后 `node mcp_bridge.js --check` 自检
- 协议合规：官方 SDK 客户端（@modelcontextprotocol/sdk）跑 initialize/tools/list/ping/call
