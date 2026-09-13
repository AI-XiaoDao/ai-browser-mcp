# -*- coding: utf-8 -*-
"""追加报告第 103 节(第87轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = "## 103. 第87轮：覆盖收官（306/312 台账 + 6 个「跳过项」受控实测）＋ 又一处「由GUI管理」的错误前提"

SECTION = """

---

%s

### 103.1 覆盖收官：台账 **306/312**，剩下 6 个"跳过项"本轮做了**受控实测**

台账把 6 个工具列为"跳过(致命/污染全局)"，于是它们一直算"未测"。本轮为它们设计了**不伤主实例**的测法，
逐条实测（`_audit/measure_skipped_tools.py`）：

| 工具 | 测法（为什么安全） | 实测结果（原文） | 存活 |
|---|---|---|---|
| `browser_set_preference` | 把 webkit 首选项设成**它本来就是的值** | `首选项 webkit.webprefs.javascript_enabled 已设置` | ✔ |
| `browser_set_s5_proxy` | 指向**本机无效端口** `127.0.0.1:1`，测完立刻重启清掉 | `S5代理已设置: 127.0.0.1:1 …` + 如实给出 `needs_reload:true` | ✔ |
| `browser_reverse_patch` | 用它自带的 **`dry_run:true`**（只验证编译不替换） | 先失败（见 103.3），重测**成功**：`dryRun 通过(新源码可编译, 未实际替换)` | ✔ |
| `browser_close` | **先建第二个后台浏览器**，只关 `browser_id=2`，不动主浏览器 | `浏览器已关闭: id=2` | ✔ |
| `browser_close_try` | 放靠后（文档说它会关浏览器） | `⛔ 远程关闭浏览器已禁用…`（文案见 103.2） | ✔ |
| `browser_shutdown` | 最后一项，`confirm:true` + 2 秒延迟 | `AI浏览器将在2秒后安全关闭, 感谢使用` | ✔（重启后恢复） |

**6/6 全部实测完毕，且全部没有把实例搞死**。加上台账的 306，**312 个工具至此全部被实际调用过至少一次**。

覆盖推进过程中另有 3 个工具是靠补覆盖值从"只测到守卫"变成真测量的：
`browser_reverse_query_objects`（`prototype_expression="Array.prototype"` —— 任何页面都有）、
`browser_reverse_await_promise`（`Promise.resolve(1)`）、
`browser_fill_form`（先用 `TOOL_PRE_CALLS` 注入一个 `<input id="mcpProbeInput">`，再填它）。

### 103.2 又一处"由GUI管理"的错误前提（与 96.2 是同一个被推翻的前提）

`browser_close_try` 的失败文案原本是：

```
⛔ 远程关闭浏览器已禁用 | 浏览器生命周期由GUI管理
```

**"由GUI管理"与代码事实不符** —— 本项目是控制台程序、没有 GUI（这条前提早在报告 96.2 就被推翻：
创建浏览器时 `父窗口句柄 = 0`，用户看到的窗口**就是浏览器窗口本身**）。而真实原因是：

> 关闭浏览器**等于退出整个 MCP 服务**（`docs/客户使用手册.md`：关闭浏览器窗口会退出整个程序），
> 所以刻意不提供 API 关闭入口。

已按实测改为如实说明，并给出替代路径（`browser_close` 可只关后台浏览器 / `browser_shutdown` 需 `confirm:true`）。
这类"理由本身是错的"的失败文案，正是调用方无法行动、只能反复换方法的根源之一。

### 103.3 顺带改进：`browser_reverse_patch` 的"无脚本"文案（并且它其实**是能用的**）

第一次实测 `browser_reverse_patch`（dry_run）失败：

```
拿不到任何已注册脚本 | 已自动启用调试器并等待上报, 但仍无 Debugger.scriptParsed —— 请重载页面后重试本工具(无需任何前置调用)
```

原文案只说"重载页面后重试"。但真实原因是我当时刚重启、页面是 **example.com 这种纯静态页**——
**重载一万次也不会有脚本**。改后的文案点明两种常见原因（页面根本没有脚本 / 刚重载尚未上报）并给出
可行动路径（先 navigate 到**有 JS 的页面**，或用 `action=list` 确认注册表非空）。
改完重测：**成功** —— `dryRun 通过(新源码可编译, 未实际替换) | 【已自动选择】…自动选中字节最大的脚本 scriptId=34`。

也就是说：这个工具**本来就是好的**，是我第一次的测法选错了页面 —— 而改进后的文案恰好能防止下一个人再踩。

### 103.4 本轮我自己的一次"把台账跑挂"

给 `browser_fill_form` 加前置调用时，我把 `TOOL_PRE_CALLS.setdefault(...)` 写在了
`TOOL_PRE_CALLS` **定义之前**，于是 `import mass_probe` 直接 `NameError`，
**整个台账从此刻起所有命令都没有输出**。所幸第一次重测就没输出、当场发现并改正。
**教训：往共享测试脚本里加东西后，第一件事是确认它还能跑（而不是先看结果数字）。**

### 103.5 本轮指标

| 项 | 值 |
|---|---|
| 工具数 | 312 |
| 台账 | **306/312** 已测；另 6 个"跳过项"本轮**受控实测完毕** -> **312/312 全部实际调用过** |
| 通过 | **265**（本轮 259 -> 265） |
| 把实例卡死 | **0** |
| `CAPABILITY` 失败 | 0 |
| 失败性质 | TARGET 26 / OTHER 9 / PARAM 3 / STATE 2 / GUARD 1 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增 | `measure_skipped_tools.py`（6 个危险工具的受控测法） |

### 103.6 仍未做（下一轮）

- **41 个失败的分诊**：已派只读复核（`_audit/_failure_triage.md`）逐条分类为
  "测试侧缺参 / 合法且可行动 / 真缺陷"，下一轮据此收口。
- `browser_reverse_instrument_script` 装上后阻塞 JS 通道的**根因**（本轮前只做到"知情选择"）。
- 陈旧活帧隐患（101.4）；algo/gwatch 的 `push`/`shift`（噪音）。
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
