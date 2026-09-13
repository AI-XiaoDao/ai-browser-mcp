# -*- coding: utf-8 -*-
"""把第 83 节(第 62-67 轮)追加到 MCP工具可用性检测报告.md。

报告为 UTF-8 无 BOM / LF —— 追加时保持同样编码与行尾, 避免整文件被改写。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, "MCP工具可用性检测报告.md")

SECTION = """
---

## 83. 第 62–67 轮：★头号缺陷终结 + 11 个幽灵能力补齐 + 两处自伤回归的复盘

### 83.1 ★ 触摸三件套改 CDP 优先 —— 会话级卡死的最后一个来源已消除（验收 20/20）

**病灶（此前一直存在，且是唯一还会"把整场会话搞死"的缺陷）**：`browser_touch_press/_release/_move`
只走 VIP 内核注入（`高级触摸_按下/放开/移动`）。内核级输入注入实测会让 **CDP 通道在本会话内永久失效**，
此后每个 CDP 优先工具都白等超时、连 `browser_status` 都可能挂，只能重启进程 —— 正是用户说的
"调用很多次失败、反复换方法"。

**修法（不新增轮子的做法）**：
① 新增 `CDP派发触摸点一次`（单次 `Input.dispatchTouchEvent` 原语）+ `CDP派发触摸事件`
（`MCP_Server.wsv`），与既有 `CDP派发鼠标事件` 同源同构；参数一律**纯文本拼接**构造
（`touchPoints` 是数组套对象，而项目实测 yyjson 嵌套 `加入数组成员` 会 0xC0000005）；
② 三件套改 **CDP 优先**，内核注入降级为显式 `kernel:true`；
③ **零前置**：`Input.dispatchTouchEvent` 在触摸仿真未开启时会被 CDP 直接拒绝
（"Touch events are not enabled"）—— 这正是以前必须先手工调 `fingerprint touch_enable` 的原因。
现在每次调用都幂等确保一遍 `Emulation.setTouchEmulationEnabled{enabled:true,maxTouchPoints:5}`，
并经 `auto_prepared` 如实上报；调用方无需任何前置。
④ **按下态自维护**：`touchEnd` 要求 `touchPoints` 为空（由浏览器释放），`touchMove` 在无按下点时
会被**静默丢弃**。"直接拖拽而未先按下"是最常见用法，故自动补一次 `touchStart`：
有历史坐标就从上次坐标补（**这才是真拖动**），无历史坐标则如实告知"起点与终点相同，浏览器不会产生
touchmove"，绝不假装成功。导航（`Page.frameNavigated`）时状态清零，避免对着不存在的触摸序列发事件。

**验收（`_audit/verify_touch_cdp_first.py`，20/20 PASS，含反向对照）**：

| 用例 | 关键证据 |
|---|---|
| 1 press 默认路径 | CDP 存活 0.04s→**0.03s**；页面侧真收到 `touchstart:400,300`；`auto_prepared` 含 `setTouchEmulationEnabled` |
| 2 move（新页面无历史） | CDP 存活；页面收到自动补的 `touchstart`；**且不产生 touchmove**，同时在响应里如实说明"起点与终点相同" |
| 2b move（有历史坐标） | 自动锚点为上次坐标：页面事件 `touchstart:120,140 → touchmove:300,200` = **真实拖动** |
| 3 press→move→release | 事件序列**精确等于** `['touchstart:100,150','touchmove:260,320','touchend:260,320']`，坐标全对 |
| 4 **反向对照** `kernel:true` | 走真内核注入（消息含"内核级"），且**CDP 随后 10.19s 失效** —— 证明上面"CDP 仍存活"的断言**有判定力、不是恒真** |
| 收尾 | 冷重启后 CDP 0.01s 可用 |

观测量用的是**页面自己记的事件序列**（`window.__t`，非可覆盖副作用），而非响应文本自述。

### 83.2 鼠标三件套的 `kernel:true` 逃生舱此前形同虚设（读码发现，已修）

失败文案写着"如仍要内核注入请显式传 kernel:true"，但 `kernel:true` 只是**跳过 CDP 块**，
随即撞上紧随的无条件失败返回 —— 于是：① 逃生舱从不执行内核注入；② 其后的整段降级退路
（VIP 内核注入 + CEF 事件派发）**永不可达**（死代码）。`browser_mouse_click` 另有一处结构缺陷：
CDP 路径被嵌在"VIP 控制器可用"分支内，与 CDP 毫无关系 —— VIP 不可用时永不尝试 CDP。

三个分支统一重构为：参数校验 →（`kernel≠true`）CDP 派发，失败即**如实报错不静默降级**
→（`kernel=true`）**真执行**内核注入并告知会破坏 CDP →（VIP 不可用）CEF 事件派发退路。
顺带把按钮文本→枚举映射从两份合并为一份。净 **−36 行**（其中含 2 处已确认死代码）。

### 83.3 本轮我自己的两处回归（都是"度量/工具先于我出错"）

1. **误删缺参守卫**：重构 `browser_mouse_click/_wheel` 时我 **`read` 起点选在 596 行**，
   而这两个分支的守卫在 590–593 / 1136–1143 行（我读取区间之前），于是被整段抹掉 ——
   `browser_mouse_click {}` 变成"在 (0,0) 真的点一下并报成功"（静默假成功 + 误点）。
   **`fastcheck` 的 `mouse_click {} 应拒绝` 立刻变红**才发现。已按备份原文回插，
   并给触摸三件套补上同类守卫（按下 (0,0) 同样是真实动作，不该有静默缺省）。
   **教训：替换整个分支前必须读到该分支的第一行。**
2. **正则改字符串边界导致 6 行描述损坏**：给 VIP 内核工具补警告时用 `re.sub` 去"在描述末尾插入"，
   group 多吃了内容，产生"警告插在字符串中部 + 描述重复"，编译器报 6 个"字符串常量无效位置"。
   改为**按已知锚点做确定性插入**（以本轮前备份的行为基准）后一次通过。
   **教训：对方言转义规则不完全掌握时，不要用正则去改字符串字面量的边界。**

为防同类问题，新增 `_audit/review_core_diff.py`：把改动后的 `MCP_Server_Core.wsv` 与"写入前"备份逐行
diff 并**列出每一条被删除的可执行行**（79 删 / 103 增，逐条可解释），把"有没有顺手删掉别的东西"
变成一次可复核的动作。

### 83.4 11 个"幽灵能力"补齐（10 个已实现并实测通过）

`_audit/_ghost_triage.md` 修正了本项目三套互相矛盾的历史分类（`_cleanup_report.md` 的"幽灵注册"、
`_reg_gap.json` 的 `unreg`）：原 16 人名单里 **5 个是误报**（`browser_aliases/batch` 实为
`aliases`/`batch` 的别名且功能完整；`create_tab/task_runner_post/debugger_pause` 是**有意下线**的
显式拒绝分支），真幽灵 **11 个**，全部来自 `MCP_Server.wsv` 的 "v2.8 R7/R8/R9 预留号"块 ——
相邻的 R5/R6 已在 v2.8.2 补齐，这 11 个号被漏了。
`cleanup_scan.py` 的 `ghost = reg - tools` **从头到尾没查分派链**，这正是误报根因（已记录）。

**已补齐并实测（台账 10/10 pass，0.00–0.04s，且全程无冷重启）**：

| 工具 | 实现 | 复用来源（不造轮子） |
|---|---|---|
| `browser_reverse_network_conditions` | `Network.emulateNetworkConditions` | 同域兄弟 `browser_reverse_cache_disable` |
| `browser_reverse_emulate_focus` | `Emulation.setFocusEmulationEnabled` | `browser_reverse_bypass_csp` 布尔开关模板 |
| `browser_reverse_cookie_cdp` | `Storage.getCookies` / `Network.getCookies` | `执行V8CDP命令` 统一出口 |
| `browser_reverse_css_coverage` | `CSS.start/take/stopRuleUsageTracking` | `browser_reverse_precise_coverage` 三段式 |
| `browser_reverse_trace` | `Tracing.start/end` | 同上 |
| `browser_reverse_layer_tree` | `LayerTree.enable/disable` | 同上 |
| `browser_reverse_input_cdp` | `kind=mouse/touch/key` | **鼠标/触摸直接复用** `CDP派发鼠标事件`/`CDP派发触摸事件`（自动带走触摸仿真与按下态） |
| `browser_fingerprint_languages` | `vip.指纹_虚拟Languages` | `Core` 里 `browser_fingerprint set_batch` 的既有调用 |
| `browser_fingerprint_webgl_vendor` | `指纹_虚拟Webglvendor` + `指纹_虚拟Webglrenderer` | 同上（子代理以类库原文证实 renderer 是**独立 API**） |
| `browser_font_randomize` | `指纹_虚拟CSS字体指纹` + `指纹_虚拟Canvas字体指纹` | `browser_vip_fingerprint_font` |

`browser_reverse_trace` 有一处**按证据纠偏**：原设计用 `transferMode:"ReturnAsStream"`，
那样 `Tracing.tracingComplete` 只给一个 IO 流句柄、还需另实现 `IO.read` 才能取数据 ——
会变成"start 成功却取不到 trace"的静默残缺。已改为默认 `ReportEvents`，
使 trace 数据经 `Tracing.dataCollected` **内联**返回，从而能被本项目已验证的事件通道读到
（先用 `browser_kernel_cdp_monitor` 订阅 `Tracing.*`，再用 `events_json` 取回）。

**仍待做 1 个**：`browser_reverse_detect_traps`（反调试陷阱检测）—— 需要新写检测规则集，
现有骨架（`browser_reverse_detect_obfuscator` / `_scan_crypto`）可复用但语义要定，未强行凑数。

### 83.5 `browser_kernel_watch` 的"只写不读"读取路径已补（含一次归因纠偏）

写入段在 `MCP_Kernel.wsv`（`记录事件日志 ("watch_changed", 键, 0, …)`），但 `list` 只回任务定义，
**没有任何读取代码** —— 用户永远看不到监视到的变更（与 `browser_kernel_cdp_monitor` 当初同类缺陷）。
现按**同族已实测可用**的写法补上 `查询事件日志 ("watch_changed","",0,200)`。两个易错点已写进注释：
① 第 4 参浏览器ID 必须传 **0**（写入侧恒写 0，传主浏览器ID 会被 `AND browser_id=?` 过滤掉，永远查不到）；
② 早前那次尝试被回退并归因为"该上下文不能调 `查询事件日志`" —— **该归因很可能是误判**，
真因更可能是 `查询事件日志` 当时**独缺数据库可用守卫**（见 83.6），DB 未就绪时线程异常终止，
客户端看到 200 + 空体。响应改为文本拼接构造（`watches` 与 `changes_json` 都保持 JSON 数组形态，
经 `加入文本成员` 会被转义成字符串）。

### 83.6 `查询事件日志` 的两处健全性缺陷（读码 + 独立分析双证）

1. **独缺 `缓存数据库可用 ()` 守卫**：同族的 `记录事件日志` / `存储任务结果` **都有**，它没有。
   DB 未打开或正在关闭时会对空句柄建语句并绑参数 → 请求线程异常终止 →
   客户端看到 **HTTP 200 + Content-Length: 0**（`MCP_Server_HTTP.wsv` 对空串就是这么发的；
   `MCP_Stdio.wsv` 则一个字节都不写），桥接脚本把它命名为"MCP 服务器返回空响应"，排查代价极高。
   现补守卫并返回 `"[]"`（该函数返回的是 JSON 数组文本，返回空串会让调用方解析失败）。
2. **`WHERE 1=1ORDER BY` 拼串缺空格**：`"… WHERE 1=1" + 条件SQL + "ORDER BY …"`，
   三个过滤条件全空时条件串为空 → 拼出 `1=1ORDER` → SQL 语法错误。
   此前所有调用方都至少传了 `browser_id>0` 才没暴露；一旦有人查全表必然失败。已在 `1=1` 后补空格。

### 83.7 VIP 内核输入工具：给"打断整场会话"这件事补上告知

台账实测：`browser_vip_mouse_click/_move/_wheel` 与 `browser_vip_key_press/_release/_click`
**每调用一次，下一条 CDP 请求就不活了**（台账里每项后面都紧跟"实例不活, 先冷重启"），
而返回文案却是光秃秃的"VIP鼠标点击"/"VIP键盘按下" —— 对会话已被打断**只字未提**。
这 6 个工具的存在意义就是内核注入（过反爬），**不能**改成 CDP 优先，故正确做法是**如实告知代价**：
已在描述里加醒目警告并直接指出 CDP 版替代工具（`browser_mouse_click` / `browser_key_event` 等）。
**未**给 `browser_vip_mouse_press/_release`、`browser_vip_key_input/_key_type` 加同类警告 ——
它们的说明写的是 CDP（非内核注入），未实测其副作用，不臆断。
**附带结论**：VIP 的**指纹类**内核 API（Languages/WebGL/字体）**不会**破坏 CDP 通道
（10 个新工具全部通过且无冷重启）—— 会打断 CDP 的是**内核级输入注入**这一族。

### 83.8 测试基建修复（这一轮栽了三次的同一个坑）

| 问题 | 现象 | 修法 |
|---|---|---|
| 台账 `--status` 崩溃 | 备注含 `⛔` 等字符 → `print` 抛 `UnicodeEncodeError` → **"看进度总览"整个功能 exit 1**，明明有失败项却看不到 | 强制 stdout/stderr 为 utf-8 + `errors="replace"` |
| 同一坑反复出现 | 三个脚本各自踩一遍；两次害得**"反向对照用例"没跑完**（结论缺失却看不出） | 抽成共用 `_audit/_console.py`，新脚本一行导入即生效 |
| 编译"无输出且 120s 超时" | 一个从 00:32 滞留的 **Volcano IDE 进程**持有工程打开状态并阻塞编译；它还是用 `.wsv` 路径启动的（**正确调用是 `voldev_awp.exe @compile <vsln> /c`**，只传路径会打开 IDE 而不是编译） | 结束滞留进程；并把"必须用 `@compile <vsln>` 形式"记为铁律 |

### 83.9 台账进度

**175/311**（本阶段从 113 推进到 175；工具面因新增 10 个工具由 301 → **311**）。
**卡死计数 = 0**；本轮 10 个新工具全 pass。失败项仍全部归入
**参数非法 / 目标不存在 / 故意守卫 / 状态依赖 / 本机架构不支持** 五类，无产品缺陷。
"""

b = io.open(P, "rb").read()
assert b[:3] != b"\xef\xbb\xbf", "报告意外带 BOM, 中止以免改编码"
assert b.count(b"\r\n") == 0, "报告意外含 CRLF, 中止以免改行尾"
txt = b.decode("utf-8")
assert "## 83." not in txt, "第 83 节已存在, 中止(避免重复追加)"
io.open(P, "w", encoding="utf-8", newline="\n").write(txt + SECTION)
nb = io.open(P, "rb").read()
print("追加完成: %d -> %d 字节, 行数 %d -> %d, BOM=%s CRLF=%d"
      % (len(b), len(nb), b.count(b"\n") + 1, nb.count(b"\n") + 1,
         nb[:3] == b"\xef\xbb\xbf", nb.count(b"\r\n")))
