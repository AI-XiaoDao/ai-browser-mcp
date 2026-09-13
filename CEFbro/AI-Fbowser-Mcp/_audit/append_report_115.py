# -*- coding: utf-8 -*-
"""追加报告第 115 节（第 98 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 115. 第98轮：`browser_network_body` 两个真缺陷、系统性异步排查、死代码清理、菜单事件**可行性实证**

### 115.1 `browser_network_body` 有**两个**叠加缺陷 → 该工具此前 100% 不可用

**缺陷一（格式守卫假设错误）**：它按"CDP requestId 是数字串"硬判首字符必须属于 `0123456789`。
但本机内核给出的真实 requestId 是 **32 位十六进制**：

```
真实 requestId = A6EE022756279359D6FE08AC76711D8D           (长度 32, 十六进制)
内核 Network.getResponseBody {requestId: 该值}
  -> {"body":"<!doctype html><html lang="en">...<title>Example Domain</title>..."}   ← 内核**认**它
工具 browser_network_body {request_id: 同一个值}
  -> 非法 CDP request_id: A6EE... | CDP 请求标识为数字串(形如 1000012345.5)
     | 如何取得有效值: ① browser_kernel_cdp_monitor 订阅 ② browser_cdp_event 取 requestId ③ 再调用本工具
```

**报错文案自相矛盾**：它给出的"如何取得有效值"三步，拿到的**正是被它拒绝的那个值** ——
调用方照做一次、被拒一次，永远出不来。**修复**：保留廉价前置校验的本意，但不再假设格式，
改为"长度 ≤ 64 且不含空白/双引号/花括号"，因此**十六进制与数字串两种形态都能通过**；
错误文案同时列出两种合法形态。

**缺陷二（异步入口丢弃响应体）**：修完格式后工具接受了 id，但回包变成
`{"success":true,"_async":true,"task_id":"1","message":"CDP已提交:Network.getResponseBody"}`
—— 它走 `执行CDP命令_带参数`（只提交、不等响应），**响应体没有随调用返回**，
调用方必须再调一次 `mcp_result` 才可能拿到。**修复**：改用 Core 既有同步惯用法
（`执行CDP并同步等待` → `CDP同步结果是否成功` → `取CDP同步结果体文本` → 解析，
与 `browser_move_window` 同一写法），并如实回报 `base64_encoded` / `body_length` /
`body_truncated`（超 20 万字符截断并标注）。

**验收（`_audit/probe_requestid_format.py`，修复后）**：

```
内核直发: {"body":"<!doctype html>...<title>Example Domain</title>..."}      ← 对照
工具调用: {"success":true,"request_id":"7C275176...","base64_encoded":false,
          "body_length":559,"body_truncated":false,"body":"<!doctype html>..."}   ← 一次调用拿到响应体
```

### 115.2 把这类缺陷**系统化**查一遍：机制定案 + 5 个嫌疑点全部有结论

先纠正我自己的一个**过度概括**：上一节曾把这类问题写成"数据全丢"。查清机制后应更准确地说
——**数据没丢，是"一次调用拿不到，必须再调一次 `mcp_result`"**（两步）。机制如下：

| 入口 | 行为 |
|---|---|
| `执行CDP命令_带参数`（`MCP_Server.wsv:1559`） | 提交后**立即**返回 `{"_async":true,"task_id":…}`（:1646-1653），结果存进异步结果表 |
| `执行CDP并同步等待`（`:3075`） | 提交 + `同步等待异步任务` → **一次调用即得真实结果**（含自动补域、卡死自救） |
| `执行逆向CDP命令`（`:8018`） | = 取安全浏览器 + 确保观察者 + `执行CDP命令_带参数`，**只回回执** |
| `尝试同步跟随异步响应`（`:6354`） | 中央层把回执换成真实结果，**但仅当 `应同步等待 (方法名, 参数JSON)` 为真** |
| `应同步等待`（`:5553`） | **一张 52 个工具名的显式白名单；无任何前缀/兜底规则** |

⇒ 结论：**不在白名单、自己也不 `同步等待异步任务` 的工具，就只能让调用方多调一次。**
`browser_debugger_evaluate` / `browser_debugger_stack` **在白名单内**（`:5683`/`:5778`），
故实测三分支（缺省 / `parse:false` / `parse:true`）**全部带回真实值** —— 它们**不是**缺陷。

全库扫描（`_audit/scan_async_data_calls.py`，66 个带方法名的调用点：
`执行V8CDP命令` 44 / `执行逆向CDP命令` 13 / `执行CDP命令` 6 / `执行CDP命令_带参数` 3）
找出 5 个"取数据却走异步"的嫌疑点，**逐个定案**：

| # | 调用点 | 工具 | 定案 |
|---|---|---|---|
| 1 | `Network.getResponseBody` | `browser_network_body` | **真缺陷（非白名单 + 丢数据）→ 本节已修** |
| 2 | `Debugger.evaluateOnCallFrame` | `browser_debugger_evaluate` | **白名单内** → 实测三分支都带回真值，非缺陷 |
| 3 | `Debugger.getStackTrace` | `browser_debugger_stack` | **白名单内** → 非缺陷 |
| 4 | `Profiler.getBestEffortCoverage` | `browser_reverse_profile`（**Core 副本**） | 该副本是**死代码** → 见 §115.4，已删 |
| 5 | `HeapProfiler.takeHeapSnapshot` | `browser_reverse_heap` | **刻意保留异步**（堆大时同步会假超时），其参数已被内核接受 |

### 115.3 4 个"探针伪失败"的正常路径实测：**4/4**

台账里 4 个 fail 其实是探针只会填 generic 值造成的伪失败。本轮**用动态取得的真值**证明正常路径可用
（`_audit/verify_probe_artifacts_happy.py`）：

| 工具 | 探针原来的值 | 本轮做法 | 结果 |
|---|---|---|---|
| `browser_set_window_style` | `type=1`（非法） | 先 `browser_get_window_style` 读当前值，再**原值写回**（安全空操作） | `窗口风格已设置` ✔ |
| `browser_find_by_hwnd` | `hwnd=1`（不存在） | 先 `browser_get_window_handle` 取真句柄 `22352126` | 返回该浏览器 `{id:1,url:...}` ✔ |
| `browser_network_body` | `request_id=mcp_probe` | 订阅 Network.* + 导航 + 从 `cdp_event` 取真 requestId | 取到 559 字节响应体 ✔ |
| `mcp_result` | 不存在的 request_id | 先造一个真异步任务取 `task_id` | 返回该任务的真实结果 ✔ |

**探针自坑（本轮第 3 次）**：`call_fn` 首测返回 `NaN` 而非 `42` —— 该工具有 `arguments`（JSON 数组）
与 `args`（**单文本**参数，会自动再包一层单元素数组）两个参数，传错就变成 `parseInt('["42"]')`。
另外验证脚本里我自己的正则 `"requestId":"([0-9][0-9.]*)"` **也**写死了"数字开头" ——
与被修的产品缺陷是**同一个错误假设**，两处都改了。

### 115.4 死代码 + 孤立段注释清理（38 行，行为中性已验证）

上一轮删掉 Core 里 6 个 `browser_reverse_*` 死分支时，**漏了第 7 个**：`browser_reverse_profile`。
可达性再次核实：主路由 `MCP_Server.wsv:10608` 把 `browser_reverse_` 前缀交给逆向分派，
只有返回**空串**才回落 Core（`:10626-10628`）；而逆向分派的 `browser_reverse_profile`
四个 action 都 `返回(...)`、未知 action 也返回失败 → **恒非空** ⇒ Core 那份**永不可达**。

**危害不是"占地方"**：它是**修复前的旧副本**（还带 `maxDepth`、还漏 `Profiler.start`）。
本轮排查时我本人就被它误导过一次（先读到 Core 的副本，误以为活的剖析工具还是异步的）。

顺带清掉 7 行**孤立段注释**：早先删 6 个死分支时留下的 `// === CDP逆向: ... ===`
（函数调用级别断点 / JS CPU性能分析 / DOM-XHR事件断点 / 预注入脚本 / Runtime.callFunctionOn /
WebSocket消息拦截 / HeapProfiler堆内存分析）—— 它们指向的分支**都已不存在**，读者会去找不存在的代码。

**工具自身的两个坑（第一版 dry-run 暴露，已修）**：
① 分支范围判定把**下一条活分支的头注释**吞了进去（会误删 `browser_snapshot` 的段标题）
→ 改为裁掉尾部注释/空行；
② 孤立注释必须在**删掉死分支之后**再判定 —— 有的注释只有死分支消失后才变孤立
→ 改为"先删分支，再在结果上迭代检测"。

结果：Core **7633 → 7595 行**；编译 0 警告、`tools=313`、fastcheck 41/41；
`browser_reverse_profile` 四臂验收**仍 4/4**（证明删的确实是死代码）。

### 115.5 三个只读子代理的静态成果（并行，未编译/未调 MCP）

| 交付 | 结论 |
|---|---|
| `_audit/_vip_app_gap_round98.md` | `类_FBrowser_应用事件` **零缺口**（30/30 事件已在 `main.wsv:272 类_MCP_初始化事件` 全部 override）；`类_FBrowserVIP_控制器` 101/117 已覆盖，**11 个候选真缺口**，4 项不确定 |
| `_audit/_classlib_gap_verify_r98.md` | 消除误报后：`类_FBrowser_菜单模式` 13/13 真缺口、`类_FBrowser_命令行` 14 项**仅启动期生效（本项目运行期不可达）**、`FBrowser辅助功能` 6 真缺口；另发现菜单类实有 **36** 个方法、src 中菜单方法调用数为 **0** |
| `_audit/_hygiene_r98.md` | 操作备注 **29 条应删 / 156 条应保留（内核实测与外部契约知识）/ 62 条需确认**；同方法内重复分支 0、`无条件返回` 后同级语句 0；零引用非框架方法 8 个（其中 `尝试恢复欢迎页导航` 与 `尝试导航欢迎页` **方法体逐字相同**） |

**注意其局限（我据此没有直接采信）**：卫生扫描的"重复分支 0"只在**单方法内**判重，
看不到**跨文件/跨类**的重复（§115.4 那个死分支正是跨文件的，它扫不出来）；子代理也**无法运行**，
故其"菜单事件是否真会触发"只能标为不确定 —— 由本轮主代理实测解决（下节）。

### 115.6 ★定案：右键菜单事件**真的会触发** → 34 个菜单方法可达

子代理把整块菜单能力建立在"`浏览器_即将打开菜单` 是否真被 CEF 触发"之上，若否整块不可达。
本轮实测（`_audit/probe_menu_event_feasibility.py`）：

```
browser_collect {action:"event_menu_enable"}
  -> 右键菜单事件监控已启用 (context_menu_opening/run/command/dismissed)
CDP Input.dispatchMouseEvent 右键 按下+抬起（x=60,y=60, button=right）
  -> mousePressed {} / mouseReleased {}
browser_event {event_name:"context_menu_opening"}
  -> [{"event":"context_menu_opening","browser_id":1,"timestamp_ms":43149328},
      {"event":"context_menu_run","browser_id":1,"timestamp_ms":43149328}, ...]
```

**两个事件都进了缓冲**（opening + run）⇒ 链路
`browser_collect` → `MCP_BrowserEvents.wsv:2658 浏览器_即将打开菜单` → `记录监控事件` 真实可用。
**结论：`类_FBrowser_菜单模式` 的 34 个方法属"可达且值得实现"的真缺口**，
且 `MCP_BrowserEvents.wsv:2662` 的形参 `菜单模式` **已在手却完全未用**（`:2666` 只记录事件）
—— 实现 `browser_context_menu` 的通道已经打通，只差把该对象存下来并加工具动作。

### 115.7 下一步

1. **实现 `browser_context_menu`**（最大单块能力缺口，通道已实证）：把 `浏览器_即将打开菜单` 的
   `菜单模式` 形参存入类级字段，新增工具动作 `add_item`/`add_submenu`/`add_separator`/
   `add_check`/`add_radio`/`check`/`check_at`；schema 一次设计到位（含 submenu/颜色/字体/可见/禁用），
   避免二次返工。落在 `MCP_BrowserEvents.wsv`（存句柄）+ `MCP_Server_Core.wsv`（分派）+ `MCP_Server.wsv`（注册）。
2. **`browser_intercept` 增加 `unmodify`/`unreplace`**（子代理 T2/T3）：现在**只能全清、不能撤一条**，
   注意 VIP 过滤器与手写通道是**两套状态**（`browser_intercept action=clear` 只清后者）。
3. 按 `_hygiene_r98.md` 删 29 条纯过程性备注（**156 条知识类必须保留**）。
4. 补 `mass_probe` 的"前置调用结果→工具入参"能力，让 `find_by_hwnd`/`network_body`/`mcp_result`
   这类**状态依赖**工具在台账里也能测到实现而非守卫（现只能另行脚本验证）。
"""


def main():
    data = open(REP, 'rb').read()
    if data.startswith(b'\xef\xbb\xbf'):
        print('!! 有 BOM, 中止')
        return 1
    text = data.decode('utf-8')
    if '\r' in text:
        print('!! 含 CR, 中止')
        return 1
    if '## 115. 第98轮' in text:
        print('!! §115 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 115. 第98轮') == 1
    print('已追加 §115; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
