# -*- coding: utf-8 -*-
"""追加报告第 105 节(第89轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = "## 105. 第89轮：失败分诊落地 —— 修掉「静默吞覆盖」的结构缺陷，失败 41->13、通过 266->294"

SECTION = """

---

%s

### 105.1 只读分诊的结论：41 个失败 = A(测试假象) 30 / B(合法且可行动) 8 / C(真实缺陷) 3

交付物 `_audit/_failure_triage.md`（逐条给了**失败原文 + 分派行 + 产出消息行**）。
它最有价值的一点是：**先把"哪些失败其实是我的探针造成的"算清楚**，而不是急着去改产品。

### 105.2 先修结构缺陷：`build_args` 在**静默丢弃**覆盖

```python
for pname, v in (TOOL_ARG_OVERRIDES.get(tool_name) or {}).items():
    if pname in props:        # ★ 参数不在 schema.properties 里 -> 覆盖被悄悄丢掉
```

而 `browser_file_dialog` 与 `browser_forward` 的 `inputSchema` 就是空 `{"type":"object"}`（**没有 properties**），
所以给它们写的覆盖**永远不会生效**，而且**不报错、不进 note、台账上看不出来** —— 又是一例"静默"缺陷。
已改为**无条件赋值**，并在 note 里点明"该参数不在 schema.properties 里"（如实，不隐藏）。

**自检（当场证明修好了）**：`build_args({"type":"object"}, "d", "browser_file_dialog")` ->
`args={'path': 'C:\\\\Windows\\\\win.ini'}` —— 覆盖真的落到入参里了（修复前是 `{}`）。

### 105.3 落地 30 个 A 类覆盖（按分诊给的具体值）

分组（每组都在分诊文档里给了"该元素确实存在"的台账证据）：

| 组 | 数量 | 取值 |
|---|---|---|
| A-1 读/交互 | 8 | `selector="h1"`（`browser_highlight{selector:h1}->highlighted:1` 与 `reverse_dom_resolve{selector:h1}->object_id` 双证；**不用 `a`**，点它会跳 iana.org 污染后续测量） |
| A-2 需要可写控件 | 5 | 先注入 `#mcpProbeInput`/`#mcpProbeCheck`/`#mcpProbeSelect`（example.com 现行版本**没有** input/checkbox/select，给任何 selector 都打不到实现），再指向它们 |
| A-3 真实属性 | 2 | `selector="a", attribute="href"` / `attribute="data-mcp-probe"` |
| A-4 语义必填 | 11 | `wait{what,value}`、`intercept{action:clear}`、`file_dialog{path}`、`workflow_get{name:hello}`、`cdp_call{Runtime.evaluate}`、`kernel_{auth,scheme}{list}`、`kernel_{reactor,watch}{action:list}`、`vip_execute_js_context{code}`、`vip_dom_search{query}` |
| A-5 先造状态 | 4 | `cdp_event`(+`browser_debugger_stack` 前置)、`reverse_return_value`/`reverse_set_variable`(同款前置)、`forward`(导航A→导航B→后退 造前进栈) |

实现方式：**追加在 `mass_probe.py` 文件末尾用 `.update()`** ——
上一轮我把 `setdefault` 写在 `TOOL_PRE_CALLS` 定义之前，`import` 直接 `NameError`、整个台账无声失效；
放末尾就不依赖定义顺序。这次加完**第一件事就是自检 import**（脚本里内置）。

**同时按分诊建议明确"不覆盖"的 8 个 B 类**：它们的消息已可行动，或覆盖本身有害
（`browser_vip_enable_js_env` / `browser_reverse_instrument_script` 是显式确认闸门；
`browser_vip_mouse_wheel` 调用即永久坏掉本会话 CDP 通道）。

### 105.4 结果：**通过 266 -> 294，失败 41 -> 13**

新写的批量驱动 `_audit/retest_batch.py --triage-a` 逐条重测，**30 个里 28 个转通过**。
未通过的 2 个属于分诊早就标注的"未知项"，**不是靠覆盖能解决的**：

| 工具 | 实测原文 | 为什么现在过不了 |
|---|---|---|
| `browser_reverse_return_value` | `Debugger.setReturnValue 失败: Invalid…` | `setReturnValue` 要求当前帧停在**返回语句**上；合成的暂停帧撑不起它 |
| `browser_reverse_set_variable` | `无法从暂停事件取到 call_frame_id \\| 请显式传 call_frame_id` | 暂停事件已被前置的 `stack` 调用消费，取不到活帧 |

两者都**只能在真正命中断点的页面上**才可能通过，而当前测试页是 example.com（无 `<script>`）——
这与 `browser_debugger_flow/auto` 是同一个取舍（分诊 §4-3 已把它列为需我决断的事项）。**未强行掩盖**。

### 105.5 本轮我自己的一次"命令没跑却看着像跑了"

批量重测第一版我写在 PowerShell 里：

```powershell
... | Select-String -Pattern '^\s+' + [regex]::Escape($t)
```

这个拼接**语法非法**，`Select-String` 直接报参数错误，于是**30 次重测一次都没执行**，
而脚本最后仍然打印出 `通过 0 / 30` —— 一个看起来像"全军覆没"、实际是"什么都没测"的结果。
已改为 Python 驱动脚本 `_audit/retest_batch.py`。
**教训（与之前几次同源）：循环/正则/拼接这类逻辑不要用 PowerShell 内联写；并且"0 通过"必须先怀疑命令没跑。**

### 105.6 本轮指标

| 项 | 值 |
|---|---|
| 工具数 | 313 |
| 台账 | 307/313 已测（+6 个危险项已受控实测） |
| **通过** | **294**（本轮 266 -> 294） |
| **失败** | **13**（本轮 41 -> 13） |
| 把实例卡死 | 0；`CAPABILITY` 失败 = 0 |
| 失败性质 | OTHER 5 / TARGET 4 / PARAM 2 / GUARD 2 |
| 构建 | 0 警告 0 错误；fastcheck 41/41（本轮未改 `src/`，只改测试侧 + 报告） |

### 105.7 仍未做（下一轮）

- **3 个 C 类真缺陷**（本轮没动，分诊已给位置）：
  ① `browser_find_by_tag` —— 我这轮查清了根因：**类库里用户标识是"创建浏览器时"设置的**
  （`FBroLib.wsv:563/584/604/626` 四个创建变体都带 `标识` 参数，`取用户标识` 注释也写"浏览器创建的时候传递设置的值"），
  而本项目 `browser_create` 只暴露 `url`/`background` -> 没有任何途径设置标识，故该工具**在本 MCP 内不可达**；
  修法二选一：给 `browser_create` 加 `tag` 透传（真能力，但要动创建握手），或把消息改成如实说明。
  ② `browser_find_by_hwnd` 消息零提示（项目明明有 `browser_get_window_handle`）。
  ③ `browser_reverse_precise_coverage` 默认动作 `take` 落在未开启的前置上，且错误是英文裸透传
  （`执行V8CDP命令` 的改写分支漏了 `has not been started`）。
- 分诊 §4 的两个待决断项：`browser_debugger_flow/auto` 是否接受"导航到带脚本页面"这一取舍；
  `browser_forward` 的历史栈反常（本轮实测已通过，但 round 1 的反常现象仍未定案）。
- `browser_reverse_instrument_script` 阻塞 JS 通道的根因；陈旧活帧隐患；algo/gwatch 噪音。
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
