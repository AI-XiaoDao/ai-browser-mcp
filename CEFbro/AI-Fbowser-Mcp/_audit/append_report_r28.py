# -*- coding: utf-8 -*-
import io, os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
SEC = u'''
---

## 79. 第 24–28 轮：多浏览器误报纠正、CDP 监控四层修复、台账推进

### 79.1 ★纠正：`browser_select` 是误报 —— 多浏览器其实完全可用

上一版类库缺口核对把 **`browser_select` 列为优先级第 1 的"真缺口"**，理由是"全项目 118 处 `取主浏览器()`，
只有 `browser_close` 暴露 `browser_id`，`browser_create` 造出的第二个浏览器无法被任何工具操作"。

**真机验证证明它完全可用**（`_audit/verify_browser_id.py`，可复现）：

```
browser_create                       -> 新建 id=2
browser_navigate {browser_id:2}      -> b2=1
browser_get_url  {browser_id:2}      -> b2=1   ✅
browser_get_url  {browser_id:1}      -> b1=1   ✅（隔离正确）
browser_get_url  {}                  -> b1=1   ✅（默认主浏览器）
```

**机制**：`MCP_Server.wsv:10229-10233` 在**每个请求**上从参数里取 `browser_id` 赋给静态变量
`目标浏览器ID`，用完恢复；而 `取主浏览器()`（`MCP_Server.wsv:7530`）优先按 `目标浏览器ID` 取浏览器。
即 **`browser_id` 是请求级公共参数，301 个工具天生全支持多浏览器**，无需任何工具单独声明。

**误报成因**：核对只检查了工具 schema（`添加工具JSON`），没看到这个**请求级公共入口**。
**教训（已写入目标）**：候选缺口必须交叉核对"是否已由**请求级公共参数** / 批量工具 action 枚举 /
参数化入口"覆盖 —— 这是目前已知的第三类误报来源。

**顺带修掉的真实缺口 = 可发现性**：`browser_id` 从未写进任何工具 schema/AI 可见文档，AI 代理无从知道
它存在。已在 `browser_list` / `browser_create` 的描述里补齐用法（含"这是请求级公共参数、
无需在单个工具 schema 声明"）。

### 79.2 ★`browser_kernel_cdp_monitor` 四层缺陷（每层单独都足以让它形同虚设）

| 层 | 缺陷 | 证据 | 修法 |
|---|---|---|---|
| ① 写 | `检查CDP监控` 钩子**从未被调用**（其自身注释就写明"钩子: 存储CDPDevTools事件 内调用"） | 全项目零调用点 | 按设计意图接上（`MCP_Server.wsv:2194-2196`）|
| ② 读 | 钩子写入 `event_log` 的 `log_type="cdp_monitor"`，但**全项目无任何读取方**（读取方只有 network/console/app_event/browser_event/cdp_event） | grep 确认 | `action=list` 增加 `events_json` |
| ③ 匹配 | 文档示例写法 `Network.*` 恒不命中：匹配只做精确相等或 `是否以` 前缀比较，而 `是否以("Network.requestWillBeSent","Network.*")` 为假 | 订阅后 `events_json` 仍为 `[]` | 支持尾部 `*` 通配（去尾 `*` 后按前缀匹配）|
| ④ 前置 | **CDP 域事件只在 `域.enable` 之后才下发** | A/B 实测：未启用时查 `Network.requestWillBeSent` 未找到；手工 `Network.enable` 后同一事件**立即到达**；`Page.frameNavigated` 同理 | `action=add` 时按模式前缀自动 `域.enable`，经 `auto_prepared` 如实上报 |

**端到端复测通过**（`_audit/verify_cdpm2.py`）：

```
0) 订阅前 list        -> events_json: "[]"
1) 订阅 Network.*     -> 成功, auto_prepared: "Network.enable(CDP监控订阅所需)"
2) 导航
3) 订阅后 list        -> events_json 非空: {"requestId":"C73EB4AD...","timestamp":27109.38,...}  ✅
```

### 79.3 ★系统性发现：CDP 域事件需要 `域.enable`，否则**静默无事件**

第 79.2 的 ④ 不是单点问题。**CDP 的事件类能力普遍需要先启用对应域**，不启用时**不报错、只是永远收不到事件**
（与"agent is not enabled"那种会报错的情形不同）。

由此可解释两处历史现象：
1. `Page.frameNavigated` 清表路径**从未生效**（`Page.enable` 未调用）—— 我此前归因为"事件不送达"，
   真正原因是**域未启用**；该清表已由"失效即剔除"自愈机制兜底，故不影响功能。
2. 先前实现的**中央反应式自动补域只在 `agent is not enabled` 报错时触发** —— 对这类**静默隐式前提无效**。
   故"零前置"必须区分两种隐式前提：**会报错的**（可反应式补救）与**静默的**（必须主动启用）。

**下一轮待查**（同类风险）：`browser_collect` 的 `event_*` 事件族、`browser_kernel_reactor`（依赖浏览器事件）
是否也需要（且缺少）对应域的 `enable`。

### 79.4 台账推进（逐个功能测试）

`_audit/tool_ledger.py`：**60/301 已测**，本轮 30 个功能仅 **0.9 秒**。
失败项均为"参数非法 / 目标不存在 / 本机架构不支持"三类且**错误可行动**，**前置缺失类 = 0、卡死 = 0**。
其中 `browser_set_auto_resize` / `browser_move_window` 如实返回
"⛔ 嵌入式GUI浏览器不支持 …（尺寸由主窗口管理）" —— 属**诚实的架构性限制**，与类库缺口核对的
"不适用"判定一致，不是假成功。

### 79.5 鼠标三件套：CDP 失败不再静默回退内核注入

原实现里 `CDP派发鼠标事件` 失败会**静默落到**内核注入分支，而内核注入会让 CDP 通道在**整个会话内**
永久失效（需重启进程）—— 一次点击失败即可连累其后所有 CDP 优先工具。已改为：CDP 失败时**如实报错**
并给出可用替代（`browser_element_action` / `browser_execute_js`），仅在显式 `kernel:true` 时才走内核注入。
修复脚本 `_audit/fix_mouse_fallback.py` 采用"与空白无关的锚点 + 括号配对插入"，自带备份/BOM/行尾保持与演练模式。

实测（`_audit/verify_mouse_fix.py`）：`mouse_click` 0.04s / `mouse_move` 0.02s / `mouse_wheel` 0.02s
均"经 CDP 派发"，且随后 `execute_js` 0.01s、`get_text` 0.03s —— **通道完好**。

### 79.6 并行协同（10 子代理）与代码卫生

6 个子代理按**文件所有权**并行完成：VIP 14 处 / Reverse+Kernel 28 处 / Core 56 处 / 9 个小文件 54 处
**操作备注清理**（合计 152 处），每份交付都用"剥离注释后代码行逐字节比对"自证未动代码（如 Core：
6547 行前后完全一致）；另 2 个只读分析（零引用证实、类库缺口核对）也已交付。
**22 个 wsv 的 BOM/行尾与备份逐字节一致**（子代理还发现并修复了 `edit` 工具会丢 BOM 的问题，
`MCP_Kernel.wsv` 原本带 UTF-8 BOM）。
'''
with io.open(P, 'a', encoding='utf-8') as f:
    f.write(SEC)
print('已追加, 行数=%d' % len(io.open(P, encoding='utf-8').read().splitlines()))
