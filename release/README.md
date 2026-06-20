# AI浏览器 — 成品发布包说明

本目录为**可直接分发给终端用户**的运行时配置包（不含 CEF 二进制时需配合 `AI浏览器.exe`）。

## 目录

| 路径 | 内容 |
|------|------|
| `linker/` | 与编译输出 `linker/` 同结构：桥接脚本、配置、文档、工作流 |

## 使用方式

### 已有 exe（Release 或自行编译）

1. 将 `linker/` 内全部文件复制到 **AI浏览器.exe 同目录**
2. 双击运行 exe，访问 `http://127.0.0.1:9222/`
3. 按 `docs/客户使用手册.md` 配置 Cursor

### 仅本仓库脚本（开发调试）

若已在本地编译并启动 MCP 服务，也可直接使用仓库内：

```
CEFbro/AI浏览器/mcp_bridge.js
CEFbro/AI浏览器/mcp_config.json  → 编译后位于 linker/
```

## 发布 GitHub Release 建议

打包 zip 结构示例：

```
AI浏览器-x64-v2.6.0.zip
├── AI浏览器.exe
├── *.dll / CEF 运行时（编译产物）
└── linker/          ← 本目录内容
    ├── mcp_bridge.js
    ├── mcp_config.json
    ├── docs/
    └── workflows/
```

## 版本

与源码 `MCP_版本号`（当前 2.6.0）保持一致。
