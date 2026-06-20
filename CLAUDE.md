# AI浏览器 MCP Server 项目

## 项目概述

本项目是一个基于 **火山视窗 (Volcano Windows)** 编程语言 和 **FBrowser CEF 框架** 构建的 AI 浏览器 MCP (Model Context Protocol) 服务端。

- **入口程序**: `CEFbro/AI浏览器/src/main.wsv` — 主窗口与 MCP 服务启动
- **核心服务**: `CEFbro/AI浏览器/src/MCP_Server.wsv` — JSON-RPC、sync-wait、batch、工具注册 (~6490 行)
- **核心分派**: `CEFbro/AI浏览器/src/MCP_Server_Core.wsv` — 导航/JS/CDP/窗口/网络/collect (~3400 行)
- **填表分派**: `CEFbro/AI浏览器/src/MCP_Server_Form.wsv` — FBrowser 填表 API (~260 行)
- **系统分派**: `CEFbro/AI浏览器/src/MCP_Server_System.wsv` — ping/全局/任务 (~120 行)
- **工作流分派**: `CEFbro/AI浏览器/src/MCP_Server_Workflow.wsv` — workflow_list/get/run/stop
- **VIP 分派**: `CEFbro/AI浏览器/src/MCP_Server_VIP.wsv` — VIP 命令 (~1350 行)
- **HTTP/WS 事件**: `CEFbro/AI浏览器/src/MCP_Server_HTTP.wsv` — HTTP + WebSocket 路由 (~260 行)
- **浏览器事件**: `CEFbro/AI浏览器/src/MCP_BrowserEvents.wsv` — 浏览器事件 Hook 系统
- **回调处理**: `CEFbro/AI浏览器/src/MCP_Callbacks.wsv` — JS/VIP 异步回调类
- **配置**: `CEFbro/AI浏览器/src/mcp_config.json` — MCP 服务端口/速率限制等
- **发布包**: `AI浏览器_MCP_发布包/linker/` — 编译产物与运行时

MCP 服务运行在 `ws://127.0.0.1:9222`，提供 **217 个浏览器自动化工具**（4 个 GUI 受限：create/close/create_background/create_tab）。

---

## 技能书 (Skills) — 必读知识库

所有技能文件位于 `.claude/skills/`（及成品目录 `CEFbro/AI浏览器/skills/`），编写代码前按需查阅：

### 语言与平台核心
| 技能文件 | 用途 |
|---------|------|
| [火山wsv文本格式语法手册.md](.claude/skills/火山wsv文本格式语法手册.md) | `.wsv` 文件语法规则：类/方法/参数/常量/变量/属性表定义格式 |
| [火山视窗AI辅助文件/火山视窗平台封装语法手册.md](.claude/skills/火山视窗AI辅助文件/火山视窗平台封装语法手册.md) | 火山视窗平台封装语法 |
| [火山视窗AI辅助文件/火山视窗模块信息.md](.claude/skills/火山视窗AI辅助文件/火山视窗模块信息.md) | 火山视窗模块结构信息 |
| [火山视窗AI辅助文件/火山视窗项目文件格式技术规范.md](.claude/skills/火山视窗AI辅助文件/火山视窗项目文件格式技术规范.md) | 火山视窗项目文件格式 |

### API 参考
| 技能文件 | 用途 |
|---------|------|
| [volcano-modules.md](.claude/skills/volcano-modules.md) | **67 个核心模块** API：FBrowser CEF (8模块)、火山核心库 w_\* (18模块)、社区库 (41模块) |
| [volcano-core-ext.md](.claude/skills/volcano-core-ext.md) | **10 个核心扩展模块**：ADO数据库、AI问答、C++正则、OpenSSL、cURL、iconv编码、JSON(jsoncpp)、HTML解析、plog日志 |
| [volcano-ext-libs.md](.claude/skills/volcano-ext-libs.md) | **37 个扩展库模块**：MFC/WTL界面、HP-Socket网络、Redis/V8/ELK/Python引擎、图像/多媒体、MMKV/树结构/串口等 |
| [volcano-supplementary.md](.claude/skills/volcano-supplementary.md) | **170+ 社区模块**：XCGUI炫彩、MiniBlink/WebView2、COM封装、STL模板、Lkuaiy系列、Office文档、各种工具库 |
| [yyjson-api.md](.claude/skills/yyjson-api.md) | yyjson JSON 库完整API |
| [客户使用手册.md](CEFbro/AI浏览器/skills/客户使用手册.md) | **终端客户必读** — 安装、Cursor、话术、VIP、FAQ（编译 `docs/客户使用手册.md`） |
| [使用技能书.md](CEFbro/AI浏览器/skills/使用技能书.md) | 技术/Agent 实操（编译 `docs/使用技能书.md`） |
| [MCP工具配置说明书.md](CEFbro/AI浏览器/skills/MCP工具配置说明书.md) | mcp_config / Cursor / VIP（编译 `docs/`） |
| [AI浏览器MCP.md](CEFbro/AI浏览器/skills/AI浏览器MCP.md) | **217 个 MCP 工具完整参考**（sync-wait、workflow、网络逆向） |
| [场景与Hook测试.md](CEFbro/AI浏览器/skills/场景与Hook测试.md) | 场景脚本、Hook、POST 加密扫描、debugger 恢复 |

### 系统 API 知识库
技能文件引用的模块源码 `.wsv` 文件位于 `.claude/skills/火山系统API知识库/`、`.claude/skills/火山FB浏览器样例代码/` 目录中。

---

## 工作流与约束

### 代码定位
- **主逻辑**: `CEFbro/AI浏览器/src/MCP_Server.wsv` — JSON-RPC、工具注册、命令响应辅助
- **分派链**: `MCP_核心分派` → `MCP_填表分派` → `MCP_VIP分派` → `MCP_系统分派`（各独立 `.wsv`）
- **HTTP/WS**: `CEFbro/AI浏览器/src/MCP_Server_HTTP.wsv` — `类_MCP_服务器事件`
- **事件 Hook**: `CEFbro/AI浏览器/src/MCP_BrowserEvents.wsv`
- **回调类**: `CEFbro/AI浏览器/src/MCP_Callbacks.wsv`
- **主窗口**: `CEFbro/AI浏览器/src/main.wsv` (~100行，窗口 + MCP 连接状态 UI)

### 代码编写规范
1. **始终使用 `.wsv` 格式** — 参考 [火山wsv文本格式语法手册.md](.claude/skills/火山wsv文本格式语法手册.md)
2. **空值检查模式**: 统一使用 `取主浏览器()` / `取VIP控制器()` / `取安全主框架()` + `== 假` 判断
3. **响应类型**: `命令成功` / `命令成功_异步` (返回 `task_` ID) / `命令成功_原始JSON` / `响应_需要刷新`
4. **MCP 工具命名**: 所有工具同时支持 `browser.name` 和 `browser_name` 双路由
5. **异步任务 ID**: 格式 `task_<启动毫秒>_<随机盐>_<计数器>`
6. **测试脚本**: `CEFbro/AI浏览器/run_all_tests.js` — 顺序全量测试；Hook/场景见 `scenarios/run_all_scenarios.js` 与 `CEFbro/AI浏览器/scenarios/README.md`
7. **网络逆向**: `scenarios/douyin_xhr_encrypt_scan.js` — XHR/fetch POST 加密字段扫描（MCP 网络层不记 POST body，须 persist Hook）
8. **场景技能**: `CEFbro/AI浏览器/skills/场景与Hook测试.md` — persist/Hook/workflow/断点恢复稳定性须知
9. **配置文件**: `CEFbro/AI浏览器/src/mcp_config.json` — 端口/速率限制/日志开关（见 `mcp_config.README.md`；默认 `enable_network_log:true`）
10. **备份清理**: 修改前删除旧 `.~vbak.wsv` 备份文件，保持仓库整洁

### 编译输出文件清单

火山 `MCP_Server.wsv` 附属文件 → `linker/`：

| 输出 | 说明 |
|------|------|
| `docs/` | HTML + **客户使用手册** + 使用技能书 + MCP配置说明书 + README |
| `mcp_config.json` | 运行时配置 |
| `mcp_config.README.md` | 配置字段简表 |
| `mcp_bridge.js` | Cursor stdio 桥接 + `--call` / `--feed` |
| `mcp_client.js` | HTTP 客户端库（测试编排 require） |
| `mcp_check.js` | 连接自检（`node mcp_check.js`） |
| `workflows/` | 工作流 JSON |
| `index.html` | 欢迎页控制台 |

### 编译与运行
- 项目使用火山视窗 IDE (`E:\voldev25\`) 编译
- 编译产物输出到 `CEFbro/AI浏览器/_int/AI浏览器/debug/x64/linker/`
- MCP 服务启动后自动注册环境变量 `AI_BROWSER_MCP_URL/PORT/HEALTH`

### 常用操作
```bash
# 代码统计
cd "CEFbro/AI浏览器/src" && wc -l *.wsv

# 清理编译缓存
rm -rf "CEFbro/AI浏览器/_int/AI浏览器/debug/x64/linker/CacheData/MCP_TaskResults/"*
rm -rf "CEFbro/AI浏览器/_int/AI浏览器/debug/x64/linker/CacheData/MCP_ResponseCache/"*

# 清理备份文件
rm "CEFbro/AI浏览器/src/"*.~vbak.wsv

# 运行测试 (需先启动 AI浏览器.exe)
node CEFbro/AI浏览器/run_all_tests.js

# POST 加密字段扫描 (需外网)
node CEFbro/AI浏览器/scenarios/douyin_xhr_encrypt_scan.js [url]

# 发布打包
cp -r "CEFbro/AI浏览器/_int/AI浏览器/release/x64/linker/"* "AI浏览器_MCP_发布包/linker/"
```

### API 查阅优先级
1. FBrowser CEF 框架 API → [volcano-modules.md](.claude/skills/volcano-modules.md) 第一节
2. MCP 工具详情 → [AI浏览器MCP.md](CEFbro/AI浏览器/skills/AI浏览器MCP.md)
3. 用户实操 / 配置 → [客户使用手册.md](CEFbro/AI浏览器/skills/客户使用手册.md) · [使用技能书.md](CEFbro/AI浏览器/skills/使用技能书.md) · [MCP工具配置说明书.md](CEFbro/AI浏览器/skills/MCP工具配置说明书.md)
4. 火山核心库 (文本/数组/文件/线程) → [volcano-modules.md](.claude/skills/volcano-modules.md) 第二节
5. 其他扩展库 → [volcano-core-ext.md](.claude/skills/volcano-core-ext.md) / [volcano-ext-libs.md](.claude/skills/volcano-ext-libs.md) / [volcano-supplementary.md](.claude/skills/volcano-supplementary.md)
6. 火山语法 → [火山wsv文本格式语法手册.md](.claude/skills/火山wsv文本格式语法手册.md)

### 相关资源
- 火山编程交流群: https://qm.qq.com/q/Hpv6qm8qUE
- QQ: 212577526 | QQ群: 737680767 | 微信: XSMZAS1
