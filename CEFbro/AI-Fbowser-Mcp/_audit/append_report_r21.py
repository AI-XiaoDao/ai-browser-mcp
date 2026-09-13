# -*- coding: utf-8 -*-
"""追加第21轮(目标升级: 零前置一次成功 / 不重复造轮子 / 代码卫生)结论到检测报告"""
import io, os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u'''
---

## 77. 目标升级：一次调用成功 / 不重复造轮子 / 代码卫生（用户三项新要求）

### 77.1 冷启动"一次调用成功"矩阵 —— 新度量工具与首次基线

用户要求："所有功能 MCP 在 AI 代理软件上配置好后，只要加载 MCP 就能一次非常稳定地调用成功，
不要出现很多次调用失败等多次尝试其他方法。"

**度量工具** `_audit/cold_matrix.py`（复用 `mass_probe.py` 的 `build_args`/`classify`）：
先**冷重启程序**（全新会话、无浏览器前置调用、无缓存），再对每个工具用最小合法参数**只调一次**，
按类别统计。与 `mass_probe.py` 的关键区别是后者会**先预置一个页面**（等于给了前置），
无法度量真实体验。

**首次基线（296.4 秒，301 工具，跳过 5 个致命工具）**：

```
总数 301 | 跳过 5 | 一次成功 134 (45%)
【核心指标】前置缺失类失败 = 13  (目标 0)
无浏览器/无页面 = 0 | 能力缺失 = 5 | 目标不存在 = 58 | 其它失败 = 86
```

### 77.2 最致命的发现不在那 13 条里：`Debugger.enable` 冷启动无法完成

```
browser_debugger_enable            20.1s  ERR_GOOD  ⏱ 操作超时(20s)
browser_reverse_blackbox           15.2s  ERR_WEAK
browser_reverse_async_stack        15.3s  ERR_WEAK
browser_reverse_pause_on_exceptions 15.3s ERR_WEAK
browser_reverse_bypass_csp         15.3s  ERR_WEAK
browser_reverse_instrument_script  15.2s  ERR_WEAK
browser_reverse_breakpoints_active 15.2s  ERR_WEAK
browser_reverse_strings            15.4s  ERR_GOOD
browser_kernel_reverse_functions   15.1s  ERR_GOOD  CDP JS 执行无响应(已等待15秒)
browser_kernel_reverse_sources     15.2s  ERR_GOOD  CDP JS 执行无响应(已等待15秒)
```

**结论**：冷启动（程序自带欢迎页）时 `Debugger.enable` 完不成，于是
① `browser_debugger_enable` 自己超时；
② 所有走"自动补 Debugger 域"的逆向工具都在 15.2–15.3s 后带错误返回。

**这才是"一次调用成功"的真正拦路虎** —— 它一次挡住全部 V8/调试类工具。
（对照：此前每轮验证脚本都先 `browser_navigate` 再 enable，所以从未暴露这个冷启动态。）
下一轮首要任务即定位：欢迎页是否让 `Debugger.enable` 阻塞、是否需要先确保页面可交互、
或 `Debugger.enable` 是否需要更低层/异步的提交方式。

### 77.3 分类器需要修正：两类假"前置缺失"

13 条里有 11 条其实**不是**缺前置，是分类器按"含'请先'"误判的：

| 工具 | 真实性质 |
|---|---|
| `browser_debugger_resume/step_over/step_into/step_out/stack/last_paused` | **状态依赖**：页面没暂停时"无法恢复/单步"是正确行为，不是缺前置 |
| `browser_debugger_inspect`、`browser_debugger_script_source` | 同上是状态依赖；但 `script_source` 可像 `browser_reverse_patch` 那样**缺省自动选最大脚本**（可改进） |
| `browser_antidetect_presets`（preset 必填）、`browser_element_action`（index 必填）、`browser_reverse_search_script`（query 必填） | **故意加的防误操作守卫**（省略会静默部署 stealth / 误点快照第 0 个元素），属正确的业务参数要求 |

即：**真实"缺前置"= 0**（除上面的 Debugger 冷启动阻塞外），已被自动补域/自动注册表覆盖。

### 77.4 "不重复造轮子"：本轮已消除的重复

用户要求："火山源码代码不要重复造轮子。"

1. **删除** `执行V8CDP命令` 里那份"域未启用→自动 enable→重试"——它与中央
   `执行CDP并同步等待` 里的实现重复；删掉后只留中央一份，且中央能覆盖**全部工具**而非只有逆向工具。
2. **抽出** `MCP命令服务器.确保脚本注册表就绪`（唯一一份），替换原先抄在
   `search_script` / `get_possible_breakpoints` / `patch` 里的**三份**同样代码。
3. 修正笔误：`取脚本URL按ID` 的 `@强制输出` 漏了 `=`（**编译器未报错**，但已修正）。

### 77.5 零前置改造（本轮实施）

- **中央反应式自动补域**：`执行CDP并同步等待` 收到 `agent is not enabled` 时自动
  `域.enable` 并重试一次，成功则记入 `MCP_响应构建.记录自动补域`，由
  `构建命令嵌套JSON` / `命令成功` / `命令失败` 统一附加 `auto_prepared` 字段后**立即清除**
  （只在真补过时出现，不给普通回复增加体积）→ **零前置但不静默改状态**。
  实测依据：`Runtime.compileScript / queryObjects / awaitPromise` **要求 Runtime 域已启用**，
  而 `Runtime.evaluate` 不需要 —— 这个隐式前提用户无从得知，正是"反复试错"的来源。
- `script_id` 改为**可省略**：自动选**字节长度最大**的脚本（混淆包通常最大）并在回复里
  报告选中项（`【已自动选择】…`）；注册表为空时自动 `Debugger.enable` 并等待上报。
- `search_script` 失败时新增 `stale_first_error` **如实报出失效原因**（原先只报个数 = 不可诊断），
  并**自愈**剔除失效 scriptId（倒序删平行三数组）。
- 发现 `Page.frameNavigated` 需要 `Page.enable`、本机收不到 → 靠它清表不可靠，改由"失效即剔除"兜底。

### 77.6 代码卫生扫描器（用户要求清理 操作备注/死代码备注/死代码）

`_audit/cleanup_scan.py`（**只读**扫描，产出 `_audit/_cleanup_report.md`）：

```
源文件 16 个, 工具定义 301 个
操作备注(开发过程叙述) = 241  (强特征 146 / 版本变更类 95)
死代码备注(注释掉的语句) = 5
残注释(已移除/已废弃…)   = 2
零引用方法              = 13  (已排除 153 个框架虚方法)
零引用成员              = 0
重复分支工具            = 7
幽灵注册                = 16
```

**操作备注按文件**：`MCP_Server.wsv` 91、`MCP_Server_Core.wsv` 56、`MCP_Server_VIP.wsv` 32、
`MCP_Server_Reverse.wsv` 15、`MCP_Kernel.wsv` 10，其余 ≤8。
（判定口径：含"修复:/已修/实测/曾因/踩坑/教训/本轮/原实现/误判/假成功"等**开发过程叙述**；
带"默认/上限/单位/缺省/可选/必填/返回/防"等**行为契约**关键词的注释**保留**。）

**重复分支（已精确定位）**：

```
browser_reverse_call_fn        MCP_Server_Core.wsv:6653  vs  MCP_Server_Reverse.wsv:164
browser_reverse_cdp_hook       MCP_Server_Core.wsv:6495  vs  MCP_Server_Reverse.wsv:98
browser_reverse_dom_breakpoint MCP_Server_Core.wsv:6599  vs  MCP_Server_Reverse.wsv:49
browser_reverse_heap           MCP_Server_Core.wsv:6695  vs  MCP_Server_Reverse.wsv:354
browser_reverse_preload        MCP_Server_Core.wsv:6634  vs  MCP_Server_Reverse.wsv:267
browser_reverse_websocket      MCP_Server_Core.wsv:6675  vs  MCP_Server_Reverse.wsv:321
ping                           MCP_Server.wsv:9022       vs  MCP_Server_System.wsv:115
```

**幽灵注册已从 23 降到 16**（本轮补了 7 个预留名）。剩余 16 个：
`browser_aliases / batch / create_tab / debugger_pause / fingerprint_languages /
fingerprint_webgl_vendor / font_randomize / reverse_cookie_cdp / reverse_css_coverage /
reverse_detect_traps / reverse_emulate_focus / reverse_input_cdp / reverse_layer_tree /
reverse_network_conditions / reverse_trace / task_runner_post`。

### 77.7 零引用方法：一次重要的假阳性纠正（纪律价值）

第一版扫描器报 **101** 个零引用方法，几乎全是**误报** —— 它们是**框架按符号调用的回调**
（`渲染_载入结束`、`收到HTTP请求`、`服务器即将销毁`、`浏览器_控制台消息`…），源码里当然不出现方法名。

- 纠正过程：先按 `<接收事件>` 排除（0 命中，说明该属性不在签名行）→ 再按 `@输出名` 排除
  （**错误**：本项目所有方法都带英文输出名，那样会把 337 个方法全排除）→ 最终确认真正的绑定机制是
  **`@虚拟方法 = 可覆盖`**（覆盖 C++ 基类虚函数），排除 153 个后得 **13** 个真实候选。
- 这 13 个仍需**逐个**确认（`启动方法` 是程序入口、`缓存线程类_线程运行` 带 `<接收事件>` 都应排除），
  真正可疑的是：`尝试恢复欢迎页导航`、`尝试导航欢迎页`、`CDP获取脚本源`、`分派网络日志命令`、
  `解析匹配模式`、`记录网络日志项`、`规范化URL`、`发送CORS500响应`、`检查CDP监控`、`检查反应器`、
  `检查定时监视`。
- **纪律**：删除前必须逐个用引用计数证实（含 `@` 嵌入行与字符串调用），不得按名单批量删。

### 77.8 本轮耗时

```
语法自检(仅/c 不链接)    14.7s / 10.8s
全量编译                 29.7s + 27.7s (均 0 警告)
快检 fastcheck           6.3s / 4.6s  -> 41/41 通过
代码卫生扫描             约 2s
冷启动单次调用矩阵        296.4s (后台 job, 不阻塞)
```

### 77.9 下一轮必做（按优先级）

1. **定位并修复 `Debugger.enable` 冷启动阻塞**（77.2）—— 这是"一次调用成功"的头号障碍。
2. 修正冷矩阵分类器（77.3）：状态依赖类与故意参数守卫不算"缺前置"；`browser_debugger_script_source`
   缺省时自动选最大脚本。
3. `browser_kernel_reverse_functions/sources` 冷启动 15s 超时，需排查（同源问题？）。
4. 清理 241 条操作备注（分文件、分批，保留行为契约类）；清 5 条死代码备注 + 2 条残注释。
5. 删 7 处重复分支（Core 那 6 份不可达 + `ping` 重复），删后回归这 7 个工具。
6. 16 个幽灵注册：能实现的按预留名补齐，不能实现的**删除注册项**，不留永不存在的名字。
7. 13 个零引用方法逐个证实后清理。
'''

with io.open(P, 'a', encoding='utf-8') as f:
    f.write(SEC)
print('已追加, 行数=%d' % len(io.open(P, encoding='utf-8').read().splitlines()))
