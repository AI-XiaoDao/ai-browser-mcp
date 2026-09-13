# generated-cpp — 火山视窗生成的 C++ 源码（对照/编译）

本目录由火山视窗（Volcano PC）编译器从 `src/*.wsv` 自动生成，与 `_int\AI-Fbowser-Mcp\release\{x64,win32}\project` 完全一致：

| 目录 | 说明 |
|---|---|
| `x64/` | 64 位 C++ 工程（makefile + vcls_*.h + *.cpp，254 项）|
| `win32/` | 32 位 C++ 工程（254 项）|

## 编译前置条件（不能脱离火山环境独立编译）

生成的 C++ 依赖火山视窗开发环境的**类库头文件/源文件/静态库**（makefile 中 `/I` 与 `.lib` 路径均为 `E:\HSPC\plugins\vprj_win\classlib\...`）：

1. **火山视窗开发环境**（`voldev_awp.exe` + 类库目录 `plugins\vprj_win\classlib`，含 `vol_base`/`vol_mfc`/`yyjson`/`sqlite3`）
2. **FBrowser CEF 内核 SDK**（类库内 `sys\FBrowser\`，含 `FBroBaseDis.h` 与 FBro 静态库/导入库）
3. **Visual Studio 2019（16.x）+ Windows SDK 10**（makefile 由火山编译器调用 VS 工具链 cl/link 执行）

## 编译方式（一条命令产出成品 exe）

在装有上述环境的机器上，用火山工程直接编译（推荐、官方路径）：

```
voldev_awp.exe @compile AI-Fbowser-Mcp.vsln /d
```

产出：`_int\AI-Fbowser-Mcp\debug\x64\linker\AI-Fbowser-Mcp.exe`（调试版）或 `/r` 强制重编译。
本机验证：编译 0 警告，运行后 `http://127.0.0.1:9222/health` 返回 `version:"3.2.0"`、`tool_count:334`。

> makefile 直接执行需要火山环境里完整的 include/lib 路径，故本目录主要用途是**源码对照与审查**；成品重建请走上面的火山工程编译。
