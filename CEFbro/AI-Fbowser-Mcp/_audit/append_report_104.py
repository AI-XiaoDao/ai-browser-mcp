# -*- coding: utf-8 -*-
"""追加报告第 104 节(第88轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = "## 104. 第88轮：能力面反查补上一个真缺口 —— 新增 browser_show_window（显示/隐藏窗口），带位级回读验证"

SECTION = """

---

%s

### 104.1 把"被推翻的前提"变成"真的能力"：`browser_show_window`（工具数 312 -> **313**）

报告 §95.7/§96.2 已经用代码事实推翻了旧前提（本项目是控制台程序、`父窗口句柄=0`、
**用户看到的窗口就是浏览器窗口本身**），§96.2 据此补齐了 `browser_move_window` / `browser_set_auto_resize`。
只读的窗口能力复核还指出：`显示隐藏窗口` 是**真缺口**（全 `src` 0 命中、台账无 show/hide 类工具），
且类库确有该 API。本轮把它补上：

| 项 | 内容 |
|---|---|
| 类库 API | `显示隐藏窗口 (显示隐藏:逻辑)`（`FBroLib.wsv:1071`）-> `FBroHsBrowserHost_ShowWindows`，**不需要 HWND** |
| 新增工具 | `browser_show_window {visible: boolean}`（**必填**，缺省语义不明故不接受缺省） |
| 改动点 | 三处：工具注册（`MCP_Server.wsv`）+ 命令注册表（`browser_show_window`=1031）+ 派发分支（`MCP_Server_Core.wsv`） |

### 104.2 关键：用**位级回读**验证，而不是听工具自报

"隐藏/显示"最常见的坏结局是**静默没生效**。本项目已有现成的回读手段：
`browser.取窗口属性 (窗口样式_GWL_STYLE)`（项目自己在 `MCP_Server_System.wsv:67/104` 就在用），
而 `WS_VISIBLE` 正是该位掩码的一位（`0x10000000` = 268435456）。
于是实现里做**调用前后各读一次样式**，按位判断是否变成请求的状态；没变就如实 `verified:false`，不谎报。

### 104.3 验收 9/9（含**独立**回读对照）

`_audit/verify_show_window.py`：工具自报之外，另用**另一个工具**（`browser_get_run_style`）读原始样式，
在脚本里**自己按位判断**，不让被测工具自己给自己打分。

| 判据 | 实测 |
|---|---|
| 基线独立读样式 | `window_style=382664704`（WS_VISIBLE=True） |
| ① 隐藏 `visible=false` | 成功，`verified:true`，`visible_after:false` |
| ② **独立回读：位必须被清掉** | `window_style=114229248`（WS_VISIBLE=**False**） |
| ③ 显示 `visible=true` | 成功，`verified:true`，`visible_after:true` |
| ④ 独立回读：位必须回来 | `window_style=382664704`（WS_VISIBLE=**True**） |
| ⑤ 缺 `visible` | 拒绝：`visible 不能省略 \\| true=显示窗口 / false=隐藏窗口 \\| 缺省语义不明, 故不接受缺省` |

**位级证据（最硬的一条）**：`382664704 - 114229248 = 268435456 = 0x10000000` ——
差值**正好就是 WS_VISIBLE 这一位**，不多不少。也就是说这次调用精确地翻转了可见性位，
既没有碰其它样式位，也不是"看起来成功"。

### 104.4 测试自身的安全设计

隐藏的是**用户眼前的窗口**，所以验收脚本把"显示回来"放在 `finally` 里 ——
**无论中间哪一条失败都会恢复可见性**，并且收尾再独立读一次样式确认（实测收尾 `WS_VISIBLE=True`）。
工具描述里也明确写了"隐藏后你需要再调一次 `visible:true` 把它显示回来"。

### 104.5 本轮指标

| 项 | 值 |
|---|---|
| 工具数 | **313**（本轮 312 -> 313，新增 1 个能力） |
| 台账 | 307/313 已测（新增工具已测为 pass） |
| 通过 | **266**（本轮 265 -> 266） |
| 把实例卡死 | 0；`CAPABILITY` 失败 = 0 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增 | `browser_show_window` + `verify_show_window.py`（**9/9**，含独立回读对照） |

### 104.6 仍未做（下一轮）

- **41 个失败的分诊**：只读复核仍在跑（`_audit/_failure_triage.md`），下一轮据它逐条收口。
- `browser_reverse_instrument_script` 装上后阻塞 JS 通道的**根因**。
- 陈旧活帧隐患（§101.4）；algo/gwatch 的 `push`/`shift`（噪音）。
- 能力面还有若干候选缺口待核对（`类_FBrowser_命令行` 系列、菜单/快捷键 13 项等）。
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
