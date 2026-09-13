# -*- coding: utf-8 -*-
"""追加报告第 96 节(第80轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 96. 第80轮：CAPABILITY 清零（补齐窗口移动/自动调整）+ browser_debugger_auto 不再假成功"
        "＋ 插装家族真根因（崩栈）与卸载缺口")

SECTION = """

---

%s

### 96.1 `browser_debugger_auto`：不再"静默假成功"（核心不变量）

**缺陷**：该工具循环等断点命中，超时只 `跳出循环`，随后**无条件**写
`auto汇总.加入逻辑值成员 ("success", 真)` —— 于是"一次命中都没有"也返回
`success:true, hits:0`；而它每命中默认等 **60000ms**、客户端常在 15s 就放弃，
调用方拿到的是"超时 + 假成功"的双重坏结论。

**修法**：记录停止原因 → 0 命中时返回**诚实失败**（含停止原因 + 可行动建议），
默认预算 60000ms → **12000ms**（让服务端在客户端放弃前给出结论），并新增
`completed` / `stop_reason` 字段如实标注是否跑满。

实测（台账重测）：`fail  12.47s  未捕获到任何断点命中(0 hits) | 停止原因: 等待 Debugger.paused 超时(12000ms)…
| 可行动: 用 browser_reverse_get_possible_breakpoints 查可下断行列; 或用 browser_debugger_flow 并传 url 触发…`
—— 从"假成功/超时"变成"有界、诚实、可行动"。

**本轮最该记住的一次自我纠正**：上一条我先做成"断点 `locations` 为空 且 未传 url ⇒ 立即失败"（省掉白等）。
写完正对照一跑，**正对照自己也撞上了这个快速失败** → 逼我去查，结果
`_audit/diag_breakpoint_locations.py` 实测：本页**所有**已注册脚本的 `url` 都是空串（8/8，含我注入的内联脚本），
于是**任何** urlRegex 都得到 `locations:[]`。也就是说 **"0 位置" ≠ "永远不可能命中"** ——
之后若有带真实 URL 的脚本加载（真实站点外部脚本 / SPA 动态加载），urlRegex 会在那时重新解析并命中。
**立即失败会把这种合法等待误判为失败，反而制造用户最反感的"失败 + 反复换方法"。**
故已改为**只记录不提前失败**（诊断信息只在 0 命中的失败里附带）。
教训与 94.4 一致：**正对照失败时先怀疑自己的判据**。

诚实声明：本轮**未能**验证"真命中时仍然成功"这一路径 —— 在上述空 URL 环境下无法构造出真实命中。
代码上成功分支（`autoHits >= 1`）逻辑未改动，但这属于"按构造推断"，不是实测。

### 96.2 CAPABILITY 清零：把两个"恒失败"桩改成真能力

原状：`browser_move_window` / `browser_set_auto_resize` 恒返回
"⛔ 嵌入式GUI浏览器不支持 … 由主窗口自动管理"，被台账记为 `CAPABILITY`。

**前提被推翻（只读复核 + 主代理独立确认）**：本项目是 `/SUBSYSTEM:CONSOLE` 程序，
创建浏览器时 **`窗口信息.父窗口句柄 = 0`**（`src/main.wsv`，类库注释：为 0 则以桌面为父窗口），
**用户看到的窗口就是浏览器窗口本身**。故该拒绝文案与代码事实不符，能力属**可做到**。

**类库确有对应 API，且都不需要 HWND**（宿主经 `CefBrowserHost` 隐式定位窗口）：

| 类库方法 | 宿主调用 | 生成物符号 |
|---|---|---|
| `移动窗口 (左边,顶边,宽度,高度,是否重画)` | `FBroHsBrowserHost_MoveWindow` | `rg_YiDongChuangKou` |
| `置自动调整大小 (启用,最小高度,最小宽度,最大高度,最大宽度)` | `FBroHsBrowserHost_SetAutoResizeEnabled` | `rg_ZhiZiDongDiaoZhengDaXiao` |

**生成物核对（这一步不能省）**：这些方法此前**从未被引用**，`generated-cpp/**/vpkg_FBroLib.cpp`
里 0 命中。本次接线后核对**实际参与编译**的 `_int/.../project/vpkg_FBroLib.cpp`：
两个符号均已生成（`rg_YiDongChuangKou = 1`）。顺带纠正复核报告的一处拼音猜测：
符号是 `rg_ZhiZiDong**Diao**ZhengDaXiao`（**调→Diao**，不是 Tiao）—— 若按猜测的名字去核对，
会误判成"没生成、是静默 no-op"。**结论：核对生成物必须按实际符号名，不能按拼音猜测。**

**实现要点**：
- `browser_move_window`：调用类库 `移动窗口`；因**类库无返回值**，用 CDP
  `Browser.getWindowForTarget` **回读 bounds** 做验证，不符则如实报 `verified:false`；
  宽/高省略（或 ≤0）时先回读当前尺寸再传，实现"只移动不改尺寸"。
- `browser_set_auto_resize`：**原来连 schema 都没有**（两参 `添加工具JSON`，收不到任何参数）→ 已补 schema；
  调用类库 `置自动调整大小`；该类设置**无可回读的查询接口**，故只报"已调用"并显式 `verified:false`，
  **不谎报生效**；缺 `enable` 一律拒绝（不给缺省语义）。

**验收 12/12**（`_audit/verify_window_capabilities.py`），其中包含一条防"自说自话"的对照：

| 判据 | 结果 |
|---|---|
| 初始 bounds 可独立回读（测量环境有效） | `{"left":0,"top":0,"width":1000,"height":800}` |
| ① 指定 x/y/宽/高 → `verified:true` 且 actual 一致 | `880x660@(160,120)` |
| ② 只给 x/y → 保持尺寸，且宽高**等于①设过的值** | `880x660@(80,70)` ← 同时证明①的缩放真生效 |
| ⑤ **CDP 直读**必须与工具自报 `actual_*` 一致 | 直读 `880x660@(80,70)`，一致 |
| ③ auto_resize 收参成功 + 如实 `verified:false` | 通过 |
| ④ auto_resize 缺 `enable` → 拒绝 | 通过 |
| 收尾把窗口移回初始位置 | `1000x800@(0,0)` |

台账：两个工具由 `CAPABILITY` 失败转为 **pass**；**失败性质中 `CAPABILITY` 已清零**（本轮 2 → 0），
通过数 209 → **211**。

### 96.3 语法自检先行的价值（本轮省掉一次真机浪费）

本轮窗口实现首次编译报了 **3 个错误**，全部被 `loop.py --syntax`（11s，程序运行中也可跑）在真机测试前拦住：
1. `autoBp零命中` **先用后声明**（声明在循环前，赋值在断点处更早）→ 声明前移；
2. `yyjson取对象成员_安全` 第 1 参是 **YYJSON只读对象类**，我误传了 JSON **文本**（2 处）→ 先
   `创建自文本` 再取成员，并用创建成功作守卫。

### 96.4 插装家族的**真根因**（与实测崩栈吻合）与卸载缺口

上一轮我实测到"插装后页面 JS 崩栈"（`RangeError: Maximum call stack size exceeded`，
栈帧 `at __obj.<computed> (<anonymous>:1:544)` 反复自递归），当时只归因于"页面被污染"。本轮只读复核给出了
**静态可证的根因**：

> `browser_reverse_instrument` 的 transparent 包装器内部用 `__results.push({...})` 记录，
> 而它**默认 target 表里第 3 项就是 `Array.prototype.push`** → `__results.push` 解析到**刚装上的包装器自身**
> → 无限自递归；且 `__count++` 写在 push 之后，永远到不了 `__max`。

这与我实测到的栈帧形态（`__obj.<computed>`、`var __obj=…; __obj[__method]=function(){…}`）吻合。
**注意**：这是静态推断，与实测栈帧吻合但**未做因果实验**（需先改模板才能干净验证）。

**卸载缺口（确认为真缺口，且当前无解）**：复核清点了 **18 个注入家族**，
其中 **F1–F13 全部把原函数只留在不可达的 IIFE 闭包里**（`var __orig=…` 局部量），
没有任何一族回填 `__mcp_orig`、也没有全局注册表 ⇒ **不刷新页面就无法还原**。
三个族的 `__mcp_hooked` / `__mcp_tr` / `__mcp_al` **只是重入护栏，不是备份**；
`disable`/`stop` 只是 `delete window.__X__`（**删数据**，不是还原函数）；
`browser_reverse_hook_logs action=clear` 只是原地截断数组。
全仓库**唯一**真正的"备份+还原"范式是 `browser_canvas_noise`（备份 + 还原），另有
`browser_permission_spoof` 用 `delete` 复位 —— 二者都不在 hook/instrument 家族。

⇒ **修它必须改注入模板**（加一行 `__wrapper.__mcp_orig = __orig` + 全局登记表），不存在纯服务端解法；
且**必须先修 F1 自递归**，否则卸载脚本自身的数组操作也会被递归吞掉。
`Document.prototype.cookie` 族是**描述符整体覆盖**，还原必须回写描述符，不能套"存函数"的统一模板。
已列为下一轮 P0。

### 96.5 顺带记录的三处"文案 ≠ 实现"（待修，属诚实性）

1. `browser_reverse_cookie_sources` 的描述写"Hook document.cookie setter"，但实现**根本不注入 JS**
   （走原生 Cookie 管理器）。
2. 三处描述说 `browser_reverse_instrument` "仅替换 prototype getter"、`browser_reverse_hook` 是
   "CDP/V8级、不修改 fn.toString()" —— 实际都是**页面猴子补丁**且改了 `toString`。
3. 四个 kernel 族的缺参提示让调用方传 `action:status`，而 **`status` 分支根本不存在**。

### 96.6 本轮指标与未决

| 项 | 值 |
|---|---|
| 工具数 | 312 |
| 台账 | 253/312 已测 |
| 通过 | **211**（本轮 209 → 211） |
| 失败性质 `CAPABILITY` | **0**（本轮 2 → 0） |
| 把实例卡死 | 0 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增验证 | `verify_window_capabilities.py`（12/12，含 CDP 直读对照）、`diag_breakpoint_locations.py`（A/B+环境诊断）、`verify_debugger_auto_honest.py` |

未决（下一轮优先级）：**P0** 插装家族卸载入口 + F1 自递归（需改注入模板）；
**P0** `browser_debugger_flow` 同类 0 命中死等 45000ms（本轮只修了 auto）；
**P1** `browser_debugger_evaluate` 缺帧 ID 时不自取活帧、`-32000` 不可行动；
**P1** 96.5 三处文案不实；**P2** `window_topmost`/`window_width`/`window_height` 死配置（读入但零读取点，文档却承诺可用）。
""" % HEAD


def main():
    with io.open(REPORT, 'r', encoding='utf-8', newline='') as f:
        cur = f.read()
    assert not cur.startswith(u'\ufeff'), "报告带 BOM"
    assert '\r' not in cur, "报告含 CRLF"
    assert HEAD not in cur, "该节已存在, 拒绝重复追加"
    with io.open(REPORT, 'a', encoding='utf-8', newline='') as f:
        f.write(SECTION)
    with io.open(REPORT, 'r', encoding='utf-8', newline='') as f:
        new = f.read()
    assert not new.startswith(u'\ufeff') and '\r' not in new, "追加后编码被破坏"
    print("已追加: %s" % HEAD)
    print("行数: %d -> %d" % (cur.count('\n') + 1, new.count('\n') + 1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
