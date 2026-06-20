# 火山编译生成的 C++ 源码（Release x64）

本目录为火山视窗 IDE 将 `src/*.wsv` **自动翻译**后产出的 MSVC 工程文件，供审计与对照参考。

| 项 | 说明 |
|----|------|
| **来源** | 编译 `AI浏览器.vprj` → `_int/AI浏览器/release/x64/project/` |
| **版本** | 与 `MCP_版本号` 一致（当前 2.6.0） |
| **维护** | 每次 Release 编译后同步更新；**勿手工编辑** |
| **权威源码** | 二次开发请以 [`../src/`](../src/) 中 `.wsv` 为准 |

## 目录内容

- `vpkg_*.cpp` — 由对应 `.wsv` 生成的实现单元（含 `vpkg_MCP_Server.cpp` 等）
- `vcls_*.h` — 火山类/类型头文件
- `stdafx.cpp` / `stdafx.h` — 预编译头
- `makefile` — 火山生成的 nmake 脚本（`OUT_DIR` 指向 `../linker/out`）
- `AI浏览器.rc` — 资源脚本

## 与 `linker/out/` 的区别

| 路径 | 内容 | 是否 C++ 源码 |
|------|------|----------------|
| **`generated-cpp/release-x64/`**（本目录） | `.cpp` / `.h` | ✅ 是（自动生成） |
| `_int/.../linker/out/` | `.obj` / `.pch` | ❌ 否，为链接中间产物 |

成品 zip 与 GitHub Releases **均不应包含** `linker/out/`。

## 重新生成

1. 火山 IDE 打开 `AI浏览器.vprj`
2. 编译 **Release x64**
3. 将 `_int/AI浏览器/release/x64/project/` 复制覆盖本目录 `release-x64/`
