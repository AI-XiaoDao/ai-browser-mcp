# generated-cpp — 火山视窗生成的 C++ 源码（可独立编译）

本目录由火山视窗（Volcano PC）编译器从 `src/*.wsv` 自动生成：

| 目录 | 说明 |
|---|---|
| `x64/` | 64 位 C++ 工程（makefile + vcls_*.h + *.cpp）|
| `win32/` | 32 位 C++ 工程 |
| `build.cmd` | 一键独立编译脚本（不依赖火山环境）|
| `../standalone/sdk/` | 编译所需 SDK（火山类库头文件/源 + FBrowser SDK 头/库 + sqlite3/yyjson，全部相对路径）|

## ✅ 独立编译（不依赖火山开发环境，实测通过）

**前置要求（均为微软标准组件，与火山无关）**：
1. Visual Studio 2019/2022 Build Tools，勾选「使用 C++ 的桌面开发」
2. 「适用于最新 v142/v143 生成工具的 C++ **MFC**」组件（**必须**，火山类库 vol_mfc.h 依赖 MFC 头）
3. Windows 10/11 SDK

**编译**：

```cmd
cd generated-cpp
build.cmd x64      :: -> linker\AI-Fbowser-Mcp.exe (64 位)
build.cmd win32    :: -> linker\AI-Fbowser-Mcp.exe (32 位)
```

实测记录（2026-09-13）：x64 全量编译 **0 致命错误 / 0 链接错误 / 51 编译单元 / 17 条良性警告(C4715)**，
产出合法 MZ PE（约 7.7 MB）。makefile 中所有路径均为仓库相对路径（`..\..\standalone\sdk\...`），
不引用 `E:\HSPC` 或任何火山环境路径。

> 说明：编译只产出 `AI-Fbowser-Mcp.exe` 本体；运行时还需 CEF 内核运行时文件
> （libcef.dll / *.pak / locales 等，随成品包 `AI-Browser-MCP-{x64,win32}-v3.2.0.zip` 分发），
> 把 exe 覆盖进成品包即可。

## 仍可用：火山工程编译（原路径）

装有火山环境时一条命令重产成品：

```
voldev_awp.exe @compile AI-Fbowser-Mcp.vsln /d
```
