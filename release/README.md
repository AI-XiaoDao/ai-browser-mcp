# 发布说明 (Release Guide)

本目录包含**成品发布**所需的脚本与说明。运行时二进制（zip 包）发布在 [GitHub Releases](https://github.com/AI-XiaoDao/ai-browser-mcp/releases)。

## 文件

| 文件 | 用途 |
|------|------|
| `pack-release.ps1` | 一键打包 x64/win32 运行时 zip + C++ 参考 zip，并同步 generated-cpp |
| `RELEASE_NOTES_v3.1.0.md` | 当前版本发布说明 |

## 打包

```powershell
# 打包全部平台（产物在仓库根目录）
.\release\pack-release.ps1 -Version 3.1.0 -Platform all
# 或仅 x64
.\release\pack-release.ps1 -Version 3.1.0 -Platform x64
```

产出 4 个 zip：

| 包 | 内容 |
|------|------|
| `AI-Browser-MCP-x64-v3.1.0.zip` | x64 运行时（exe + CEF DLL + 配置 + 文档 + 工作流） |
| `AI-Browser-MCP-win32-v3.1.0.zip` | win32 运行时 |
| `AI-Browser-MCP-cpp-x64-v3.1.0.zip` | x64 生成 C++ 参考（`_int/.../release/x64/project/`） |
| `AI-Browser-MCP-cpp-win32-v3.1.0.zip` | win32 生成 C++ 参考 |

运行时 zip 的打包规则：

- 取编译输出 `_int/AI-Fbowser-Mcp/release/{x64,win32}/linker/`
- **排除** `out/`（编译中间产物 .obj/.pch）、`CacheData/`、`mcp_cache.db*`、`log.txt`、历史 zip
- 包含：exe、CEF 运行时（`*.dll`/`*.pak`/`*.bin`/`*.dat`）、`docs/`、`workflows/`、`locales/`、`js/`、`mcp_bridge.js`、`mcp_config.json`、`index.html`

## 发布流程

1. 编译 x64 与 win32 发布版（见 `CONTRIBUTING.md`）
2. 运行 `pack-release.ps1`
3. 上传到 GitHub Release：

```powershell
gh release upload v3.1.0 AI-Browser-MCP-*.zip -R AI-XiaoDao/ai-browser-mcp --clobber
```

## 目录对照

编译产物的生命周期：

```
src/*.wsv (源码) → project/ (生成 C++) → linker/out/ (编译中间) → linker/ (运行成品)
```

其中 `project/`（生成 C++）不进入 git 仓库；需要参考 C++ 时使用 Releases 的 cpp zip 包。
