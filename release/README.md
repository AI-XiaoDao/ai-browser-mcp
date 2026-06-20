# AI浏览器 — 成品发布包说明

本目录为**可直接分发给终端用户**的运行时配置包（不含 CEF 二进制时需配合 `AI浏览器.exe`）。

## 目录

| 路径 | 内容 |
|------|------|
| `linker/` | 与编译输出 `linker/` 同结构：桥接脚本、配置、文档、工作流（**无 exe/dll**） |

## 火山编译目录对照（Release x64）

与仓库 [README · 四层对照表](../README.md#四层对照先看这张表) 一致：

| 层级 | 本地 `_int/.../release/x64/` | 入 Git | 成品 zip |
|:--:|------------------------------|:--:|:--:|
| ② 生成 C++ | `project/` | `generated-cpp/release-x64/` | cpp zip |
| ③ 中间产物 | `linker/out/` | ❌ | ❌ **必须排除** |
| ④ 运行成品 | `linker/`（除 `out/`） | ❌ | x64 zip |

```
src/*.wsv → project/ → linker/out/ → linker/AI浏览器.exe
  ①           ②           ③              ④
```

**误区**：`out/` 只有 `.obj`/`.pch`，不是 C++；C++ 在 **`project/`**（= Git `generated-cpp/`）。

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

从 `_int/AI浏览器/release/x64/linker/` 打包时，**不要包含 `out/` 目录**（火山编译中间产物：`.obj`、`.pch`、`make_params.txt` 等，非运行所需，体积约 400MB）。

打包 zip 结构示例：

```
AI-Browser-MCP-x64-v2.6.0.zip
├── AI浏览器.exe
├── *.dll / CEF 运行时
├── docs/
├── workflows/
├── locales/
├── mcp_bridge.js
├── mcp_config.json
└── index.html
（不含 out/）
```

## 版本

与源码 `MCP_版本号`（当前 2.6.0）保持一致。

## 一键打包

编译 **Release x64** 后，在仓库根目录执行：

```powershell
.\release\pack-release.ps1 -Version 2.6.0
```

输出：

- `AI-Browser-MCP-x64-v2.6.0.zip` — 运行包（自动排除 `out/`）
- `AI-Browser-MCP-cpp-x64-v2.6.0.zip` — C++ 对照
- 同步 `CEFbro/AI浏览器/generated-cpp/release-x64/`

上传：`gh release upload v2.6.0 AI-Browser-MCP-*.zip -R AI-XiaoDao/ai-browser-mcp --clobber`

完整说明模板见 [`RELEASE_NOTES_v2.6.0.md`](RELEASE_NOTES_v2.6.0.md)。重新发版可先 `gh release delete v2.6.0 --yes` 再 `gh release create ... --notes-file release/RELEASE_NOTES_v2.6.0.md`。
