# -*- coding: utf-8 -*-
"""① 卫生扫描: 把"跨层同名分支"从重复告警里排除(以 ping 为已知样本, 附依据);
② 追加报告 §131(第114轮: 五路并行只读审计 + 死代码清零 + 花括号事故与恢复 + 能力修补)。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN = os.path.join(ROOT, '_audit', 'cleanup_scan.py')
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

# ── ① 扫描器: 跨层同名分支排除 ──
src = open(SCAN, 'rb').read().decode('utf-8')
if 'DUPLICATE_OK' not in src:
    OLD = "    dup = {k: v for k, v in per_tool.items() if len(v) > 1}\n"
    NEW = ("    dup = {k: v for k, v in per_tool.items() if len(v) > 1}\n"
           "    # 跨层同名分支不是死代码: 协议层(处理MCP请求_内部 里的 ping 回应 JSON-RPC ping)\n"
           "    # 与 工具层(分类分派_系统操作 里的 ping)是两条真实入口, 各自可达。\n"
           "    # 依据: _audit/diag_ping_dup.py 实测(执行浏览器命令 → MCP_系统分派.分类分派_系统操作)。\n"
           "    dup = {k: v for k, v in dup.items() if k not in DUPLICATE_OK}\n")
    if src.count(OLD) == 1:
        src = src.replace(OLD, NEW, 1)
        src = src.replace("DELIBERATE_GATES = {",
                          "DUPLICATE_OK = {'ping': '协议层 ping 与工具层 ping 两条真实入口'}\n\n"
                          "DELIBERATE_GATES = {", 1)
        open(SCAN, 'wb').write(src.encode('utf-8'))
        print('扫描器: 已排除跨层同名分支')
    else:
        print('!! dup 锚点命中 %d 次' % src.count(OLD))
else:
    print('扫描器: 已含 DUPLICATE_OK, 跳过')

SEC = u"""
---

## 131. 第114轮：五路并行只读审计落地 —— 幽灵清单结案、死代码清零、以及一次"删多一行"引发的编译事故

本轮按并行协同规约**同时开 5 个子代理**做**只读**审计（禁止编译 / 禁止调用 MCP / 禁止重启，交付物各自
一个 md，均带 `文件:行号` 依据、均声明"未做真机验证"），主代理独占编译与真机验证：

| 交付物 | 覆盖面 |
|---|---|
| `_audit/_gap_core_r114.md` | `类_FBrowser_浏览器`(95) + `FBrowser辅助功能`(18) 共 113 方法逐个核对 |
| `_audit/_gap_cmdline_r114.md` | `类_FBrowser_命令行` 全量 31 方法 + 启动期分类 |
| `_audit/_gap_vip_r114.md` | `FBroVip.wsv` 6 类 / 198 方法（含控制器 117 条）逐个核对 |
| `_audit/_gap_events_r114.md` | 事件面 150 + 26 个可覆盖虚方法，三重口径核对 |
| `_audit/_gap_types_r114.md` | 类型/值/帮助 284 方法 + 编解码/哈希/时间戳等实用缺口 |

**子代理一致纠正了任务书的类名**：`类 FBrowser浏览器` → 实为 `类_FBrowser_浏览器`(`FBroLib.wsv:539`)；
`FBrowser辅助功能` 在 `:377`；`类 FBrowser命令行` → 实为 `类_FBrowser_命令行`(`:1733`)；
`类 FBrowserVIP控制器` → 实为 `类_FBrowserVIP_控制器`(`FBroVip.wsv:175`)。

### 131.1 执行线 C 结案：幽灵注册 **16 → 0**（而且是"清单本身过期"，不是"删注册项"）

先做**交叉核对再动手**（这正是目标里写明的纪律）：
- 拿现有台账逐条对齐那 16 个名字 → **11 个是 `pass`**（有实现、真机跑过）；扫描器只认精确分支名，
  漏了前缀路由，所以把它们误报成幽灵。
- 其余 5 个台账里没有：`browser_aliases`/`browser_batch` 的真名是 **`aliases`/`batch`**（`browser_` 前缀
  可省略，`注册命令双变体` 的机制）；`browser_create_tab`/`browser_task_runner_post`/`browser_debugger_pause`
  **压根不在工具清单里**，但可路由，且回包是**刻意的守卫**并给出替代方案。

真机回包原文（`_audit/probe_ghost_names.py`）：
```
browser_aliases      -> {"success":true,"aliases":"快捷别名(browser_前缀可省略): …"}
browser_batch        -> {"success":true,"data":{"success":true,"total":0,…}}
browser_create_tab   -> ⛔ 远程创建标签页已禁用 | 原因: 刻意不实现 … 替代: browser_navigate / browser_create
browser_debugger_pause-> Debugger.pause 已禁用(会冻结无JS执行页面并堵塞CDP队列) … 替代: debugger_flow
browser_task_runner_post-> ⛔ 远程 task_runner 创建浏览器已禁用 … 替代: browser_id / browser_create
```
结论：**真幽灵 = 0**，无需补实现也无需删注册项。扫描器已改为三分类（未广告路由别名 / 刻意守卫分支 /
待核实幽灵），并按实测把 3 个守卫登记进 `DELIBERATE_GATES`，此后报告直接显示 `幽灵注册(待核实) = 0`。

### 131.2 死代码清零：零引用方法 **10 → 0**

删除前**逐条固定证据**（`_audit/prove_zero_ref.py` + `prove_zero_ref_symbols.py`）：
① 中文方法名在 16 个源文件里除定义外 0 次；② **`@输出名` 英文符号**同样 0 次（内嵌 C++ 按英文符号调，
这一步必须单独查）；③ 前 8 行内无 `<接收事件>` / `@虚拟方法 = 可覆盖`；④ 不在 `@` 行里出现。

共删 11 个方法 / 约 250 行：`尝试恢复欢迎页导航`、`尝试导航欢迎页`、`检查欢迎页导航超时`（欢迎页三件套）、
`CDP获取脚本源`、`分派网络日志命令`（与 Core 里活着的 `browser_network` 路径重复）、`记录网络日志项`、
`解析匹配模式`、`规范化URL`、`发送CORS500响应`、`构建网络日志数据JSON`、`统计网络日志条数`
（后两个是级联孤儿：唯一调用者就是先删掉的分派器）。

保留并**在扫描器里登记排除**：`main.wsv 启动方法`（应用入口）、`缓存线程类_线程运行`（`<接收事件>` 绑定）
—— 扫描器原先只排除 `@虚拟方法`，故这两项一直被列成"待确认"，现改为连签名区一起看 `<接收事件>` 与入口名。

### 131.3 ★事故与恢复（必须记录）：删死方法"少删一行" → 类编译不出来 → 30 条级联错误

`delete_dead_methods.py` 把 `vlib.extract_block` 的 `b1` 当成"收尾大括号所在行"，实际它是**方法体最后一行**。
于是 8 个方法各自留下一个孤儿 `}` ⇒ 花括号失衡 ⇒ `类 MCP命令服务器` 编译不出来 ⇒ **其它 9 个文件**里所有
`MCP命令服务器.xxx` 引用级联报 `没有找到所指定的常量/变量/参数名称"MCP命令服务器"`（30 条）。
**症状极像"类被删了"，真因在另一个文件的括号。**

恢复过程（`_audit/recover_server_rebuild.py`）：
① 从 `备份/删除死方法-写入前/` 干净快照恢复；② 改用**自己数花括号配对**定位收尾 `}`（`find_close`），
每段删除前断言"该段 `{` 与 `}` 数量相等"；③ 删完断言全文件花括号 = 快照 − 被删段的量；
④ 重放本轮其余 Server 改动，并断言最终量 = 期望量。此后再删 2 个方法都用同一套断言（含级联孤儿那次：
`(1555,1552) → (1552,1549)`，删 `{8 }8`，配平）。

**新增纪律**：任何"按行范围删代码"的脚本，必须 (a) 用括号配对而非 block 返回值定位边界；
(b) 删除前后各做一次**全文件 + 被删段**的括号计数断言；(c) 先 `/c` 语法自检（≈10s）再 `/d` 链接。

另一个操作坑：手动跑编译器必须带 `@compile` 令牌（`voldev_awp.exe @compile x.vsln /c`）。漏了它会
**打开 IDE 而不编译**，表现为命令挂住直到超时（本次 600s 超时就是这么来的）。

### 131.4 能力修补（全部真机验证）

| 项 | 实测发现 | 处置 | 验证 |
|---|---|---|---|
| `browser_uri_decode` | **真 bug**：四种参数组合下 `"a%20b%26c%3Dd"` **原样返回**（类库只还原非 ASCII；第三参被声明为逻辑型，传假则什么都不还原）；页面内 `decodeURIComponent` 才是 `"a b&c=d"` | 默认改回类库原始行为（不回归）；**残留 `%HH` 时自动走页面兜底**补齐，并如实回报 `data.via`；两条路都失败给 `warning` + 替代做法 | 12/13 → 修正探针后 **5/5 组全过**：`{"decoded":"a b&c=d","via":"js:decodeURIComponent"}`；无转义时 `via:"lib:…"` 且无 warning |
| `browser_uri_encode` | `use_plus` 被写死 `假` | 暴露参数 | `use_plus:true` → `"a+b"`；缺省仍 `"a%20b"` ✔ |
| **`browser_frame_by_id`（新工具，317）** | `browser_get_frames` 已把帧标识发给调用方，却没有"按 ID 取回"的入口（名字版早就有）；且回包字段名是 **`id`** 而不是 `frame_id` | 新增工具，`frame_id`/`id` 双接受；先判空再取字段（类库警告"对空类操作会崩溃"） | 真子框架 `6-FA3C…` → `found:true,url:"about:srcdoc",is_main:false`；主框架 → `is_main:true`；假 ID → `found:false`+hint；缺参 → 明确失败 ✔ **3/3** |
| `browser_event` 族名查询 | **工具与自己的文档矛盾**：描述与错误提示都要求用 `resource_*` 这类族名，实现却是 SQL **精确相等** ⇒ 照文档操作 100% 查不到 | 含 `*`/`%` 时改走 `LIKE`（`*`→`%`），否则保持精确相等 | `resource_*` 查到 `resource_response` 事件 ✔；`load_end` 仍可用 ✔；`zzz_*` 可行动报错 ✔ |
| 应用事件条数 | `browser_event` 的 app_ 分支把条数写死 `1`（查 `app_*` 族永远只回 1 条） | 改用调用方给的 `evtLimit` | 编译通过并回归 ✔ |
| `browser_kernel_events_all` 文案 | 实现打开 **26** 个开关，而文案里流传 13 / 13 / 21 三个数字 | 逐行数清后改为 26 并说明构成；enable/disable 各 26 项**逐项对称**（已核对） | 扫描 + 源码核对 ✔ |

### 131.5 事件面：**"事件覆盖 105/105"这个说法不成立**（本轮最重要的更正）

子代理独立核对（`_audit/_gap_events_r114.md`）发现**三重问题**，其中第二重是决定性的：

1. 项目自测脚本 `_audit/event_gap.py:20` 把"事件全集"只算 2 个事件类（应用事件 + 浏览器事件），
   不含 JS交互/资源处理器/资源过滤器/服务器事件/开发者消息/URL请求，也完全没看 `FBroCallback.wsv`。
2. **分母本身就是漏数**：`event_gap.py:21` 的正则要求 `<公开…>` **同行闭合**，而类库有 **13 个方法的属性块跨行**，
   它们从未进入分母 ⇒ 真值是应用事件 **30**(非 27)、浏览器事件 **88**(非 78)。
3. **更关键**：这 13 个漏数项里 **7 个至今源码里真的没有** —— 缺口与漏数项**完全重合**，这正是"补到 100%"
   时没发现它们的原因：
   `浏览器_即将打开开发者窗口`(763) / `浏览器_即将改变媒体访问`(915) / `浏览器_拖拽进入`(1376) /
   `进程间消息_收到渲染进程消息`(1401) / `离屏渲染_获取根屏幕矩形`(1420) / `获取视图矩形`(1437) / `移动调整弹窗`(1501)。

按类库全量口径的真实覆盖率：`FBroEventControl` **135/150 = 90%**（应用 30/30、浏览器 81/88、资源处理器 6/6、
资源过滤器 4/4、服务器事件 8/8、开发者消息 3/5、URL请求 3/7、JS交互 0/2）；`FBroCallback` 可覆盖虚方法
**11/26 = 42.3%**。反向差集为空（没有抄错的事件名）。
**本轮只改了查询与文案，这 7 个事件尚未接线** —— 记入待办，不声称已完成。

### 131.6 卫生扫描自身的三处误报已修

`_audit/cleanup_scan.py`：① 幽灵注册改为三分类并把实测守卫登记白名单；② 零引用方法排除口径补上
`<接收事件>` 与入口 `启动方法`；③ 跨层同名分支（协议层 ping vs 工具层 ping）不再算重复。修完的扫描输出：
`零引用方法 0 / 零引用成员 0 / 重复分支 0 / 幽灵注册 0`。

### 131.7 状态与待办

工具总数 **317**（新增 `browser_frame_by_id`）；台账 **317/317**（`browser_frame_by_id`/`uri_decode`/
`uri_encode`/`event` 本轮重测均 pass）；编译 **0 警告**；fastcheck **41/41**；卫生扫描四项归零。

**下一轮待办（按子代理给出的优先级，均未做，故不声称完成）**：
1. **VIP P0**：`FBrowser_VIP功能_启用插件高级功能`(`FBroVip.wsv:109`) 全库 0 命中 ⇒ 现状是"能装 CRX 但
   `content_scripts.js` 不执行且无任何报错"；类库原文要求"必须在加载插件前启用"。
2. 事件补齐：上述 **7 个浏览器事件** + 开发者消息 2 + URL请求 3 + 3 个 `离屏渲染_*` 空覆盖；
   并修 `event_gap.py` 的跨行解析（否则永远看不见它们）。
3. `browser_collect action=event_all_enable` 只开 11 项且 enable/disable 集合不对称（与 kernel 的 26 项全开不一致）。
4. 启动期开关通道：子代理已给出最小做法（复用 `mcp_config.json` + `main.wsv:475` 现成的
   `即将处理命令行` 钩子；**不要**走 `取全局命令行`——`_audit/_startup_args.log` 有该路径失败的原文证据，
   且那批代码已被回退），可解锁摄像头/录音/GPU 三连等仅启动期生效的能力。
5. 零前置编解码工具（hex / GBK⇄UTF-8 / 时间戳⇄时间），只依赖已在册的视窗基本类；
   `仰望模块`（MD5/SHA）在册性未证实，需先确认再动。
6. 操作备注（244 条）与死代码备注（6 条）的"叙述改契约"清理：建议按文件分工并行，
   只改写措辞、保留实测结论（删掉会丢回归依据）。
"""


def main():
    data = open(REP, 'rb').read()
    if data.startswith(b'\xef\xbb\xbf'):
        print('!! 报告有 BOM')
        return 1
    text = data.decode('utf-8')
    if '\r' in text:
        print('!! 报告含 CR')
        return 1
    if '## 131. 第114轮' in text:
        print('!! §131 已存在')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 131. 第114轮') == 1
    print('已追加 §131; 行数 %d -> %d (无 BOM / 无 CR / 唯一)' % (text.count('\n') + 1, t2.count('\n') + 1))
    return 0


sys.exit(main())
