---
name: AI浏览器场景与Hook
description: AI浏览器 MCP 场景脚本、Hook 测试、网络逆向、工作流与稳定性须知 — 配合 AI浏览器MCP.md 使用
version: 1.1
trigger: 场景测试|Hook测试|reverse_analyze|debugger_session|automation_flow|run_all_scenarios|js_http_hook|v8_hook|douyin_xhr|POST加密|debugger_unfreeze
---
# AI 浏览器 — 场景与 Hook 测试技能书

## 何时阅读
- 跑 `scenarios/` 下脚本或扩展 Hook/逆向/自动化流程前
- 用户要查看 **XHR/fetch POST 参数**、判断哪些字段加密/签名时
- 用户反馈 persist 注入、network 日志、workflow 超时、debugger 卡死时

## 快速命令

```bash
# 场景顺序包（勿与 run_all_tests 并行）
node CEFbro/AI浏览器/scenarios/run_all_scenarios.js
node CEFbro/AI浏览器/scenarios/run_all_scenarios.js --quick   # 跳过 reverse_analyze 外网

# 网络 / 逆向
node CEFbro/AI浏览器/scenarios/reverse_analyze.js https://example.com/
node CEFbro/AI浏览器/scenarios/douyin_xhr_encrypt_scan.js
node CEFbro/AI浏览器/scenarios/douyin_xhr_encrypt_scan.js https://www.douyin.com/

# Hook 冒烟
node CEFbro/AI浏览器/scenarios/v8_hook_test.js
node CEFbro/AI浏览器/scenarios/js_http_hook_test.js

# 断点
node CEFbro/AI浏览器/scenarios/debugger_session.js --flow --url URL
node CEFbro/AI浏览器/scenarios/debugger_inspect_demo.js

# 卡死恢复（run_all_tests / tool_test 后）
node CEFbro/AI浏览器/scenarios/debugger_unfreeze.js
node CEFbro/AI浏览器/scenarios/debugger_recover.js
```

## mcp_client.js 公共 API

场景脚本共用 `scenarios/mcp_client.js`（HTTP POST `http://127.0.0.1:9222/mcp`）：

| 函数 | 用途 |
|------|------|
| `getHealth()` / `assertMcpOnline()` | 健康检查 |
| `callTool(name, args)` | MCP tools/call（默认 sync-wait 白名单工具直接返回结果） |
| `callToolSync(name, args, id, waitMs)` | 异步工具轮询 `mcp_result` |
| `unwrapData(payload)` | 解包 `{success,data}` 或嵌套 JSON |
| `runDebuggerFlow(opts)` | 一键 `browser_debugger_flow` |
| `waitDebuggerPaused` / `inspectAtBreakpoint` / `resumeDebugger` | 断点分步 |
| `isJsNetworkEntry` / `uniqueJsUrls` / `PAGE_SCRIPT_SCAN` | `reverse_analyze` 用 |

环境变量：`AI_BROWSER_MCP_HOST`、`AI_BROWSER_MCP_PORT`（默认 9222）

## 网络数据：MCP 层 vs JS Hook

| 能力 | MCP 网络层 | JS persist Hook |
|------|------------|-----------------|
| URL / method / status | ✅ `browser_network` list | ✅ |
| 响应头（detail 模式） | ✅ `network_detail_enable` | — |
| POST 请求体 | ❌ 源码未记录 body | ✅ patch `XHR.send` / `fetch` |
| 加密字段识别 | — | ✅ `douyin_xhr_encrypt_scan.js` 启发式 |

**推荐组合**：
1. `browser_collect` → `reverse_prepare`（开 network_detail + console，清日志）
2. `browser_inject` persist Hook（`inject_id` 去重）
3. 用户操作触发请求后 `browser_evaluate` 读 `window.__MCP_XHR_POST__`
4. `browser_network` list 补全仅有 URL 无 body 的 POST

### XHR POST 加密扫描（douyin_xhr_encrypt_scan.js）

- 默认打开 `https://www.douyin.com/`；`--wait N` 控制最长等待，`--min N` 够条数提前结束
- `--scroll` 串行滚动；**禁止** `setInterval` 并发 MCP（会锁死超时）
- 轮询超时 → 先 `debugger_unfreeze.js`；脚本 20s 短超时，连续 2 次失败退出
- 解析 JSON body / `URLSearchParams` / URL query
- 标注疑似加密：`a_bogus`、`msToken`、`verifyFp`、`sign` 等字段名 + 高熵值
- 过滤抖音相关域名；无则分析全部 POST
- `FormData` / 二进制 body 显示 `[binary]`，无法逐字段分析

## persist 注入（稳定性）

| 要点 | 说明 |
|------|------|
| 执行时机 | `browser_载入开始` → `MCP命令服务器.应用持久V8到框架`（浏览器进程） |
| 去重 | 同一 `inject_id` 仅应用列表中**最新**一条 |
| hook 脚本 | 用 `if (!window.__XXX_INSTALLED__) { ... }` 包裹，**勿**顶层 `return` |
| fetch 探测 | 用 `browser_execute_js`，勿 `browser_evaluate` 返回 Promise |
| POST 抓包 | Hook 须在 `send`/`fetch` 调用前注入；`persist:true` + 导航后仍生效 |

## HTTP / JS Hook

| 能力 | MCP 入口 |
|------|-----------|
| 网络日志 | `browser_network` 或 `browser_collect` → `network_enable` / `network_detail_enable` / `network_get` |
| 控制台 | `browser_collect` → `console_enable` / `console_get` |
| 浏览器事件 | `browser_collect` → `event_*_enable` / `event_all_enable` |
| 导航拦截 | `browser_intercept` → `navigate_block` / `navigate_redirect` |
| 资源 VIP | `block` / `modify` / `replace_data`（需 VIP） |
| JS 层 hook | `browser_inject` `{ type:"js", persist:true, inject_id:"..." }` |

`browser_network` list 默认 `auto_enable:true`；空日志时看返回的 `hint` 字段。

## 断点调试注意

- 需 VIP；`browser_debugger_flow` 默认 sync-wait（`max_ms` 建议 ≥45000）
- `debugger_inspect_demo.js`：演示变量/函数 source/对象 properties
- 卡死恢复：`debugger_unfreeze.js`（resume×3 → disable → navigate 欢迎页 → `browser_restore_gui`）
- `debugger_recover.js`：reload + smoke flow 验证
- `tool_test_all.js` 跳过逐工具 debugger 调用，改由场景脚本覆盖

## 工作流注意

- CDP 步骤：`"wait_async": true, "max_ms": 45000`
- 定义目录：源码 `workflows/`，运行 `linker/workflows/`
- `debugger_breakpoint.json`：`on_error: continue` 允许部分步骤失败后继续

## 勿并行

单浏览器 + MCP 锁：`run_all_tests.js`、`run_all_scenarios.js`、各 scenario 脚本必须**顺序**执行。

## 脚本一览

| 脚本 | 纳入 run_all_scenarios | 用途 |
|------|------------------------|------|
| `v8_hook_test.js` | ✅ | V8 注入 + persist + navigate_block |
| `js_http_hook_test.js` | ✅ | Console / fetch·XHR / network / 导航拦截 |
| `automation_flow.js` | ✅ | 填表 fixture + batch |
| `debugger_session.js` | ✅（`--enable-only`） | 断点预备 |
| `reverse_analyze.js` | ✅（非 `--quick`） | 脚本扫描 + 网络 JS |
| `douyin_xhr_encrypt_scan.js` | — | POST 加密扫描；`--wait` `--min` `--scroll` `--skip-navigate` |
| `debugger_inspect_demo.js` | — | 断点 inspect 演示 |
| `debugger_unfreeze.js` | — | 解除 debugger 卡死 |
| `debugger_recover.js` | — | debugger 恢复验证 |

## 详见

- 用户实操：`skills/客户使用手册.md` · 编译 `docs/客户使用手册.md`
- MCP 配置：`skills/MCP工具配置说明书.md` · 编译 `docs/MCP工具配置说明书.md`
- 工具全集：`skills/AI浏览器MCP.md`
- 脚本文档：`scenarios/README.md`
- 配置简表：`src/mcp_config.README.md`
