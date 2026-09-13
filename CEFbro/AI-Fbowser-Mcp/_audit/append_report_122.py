# -*- coding: utf-8 -*-
"""追加报告第 122 节（第 105 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 122. 第105轮：新增工具 `browser_context_menu`（**314** 个工具）—— 最大单块能力缺口落地

### 122.1 为什么必须走"预置规格"而不是"即时改菜单"

第100轮子代理给出了**决定性依据**（CEF 头逐字）：

```
cef_context_menu_handler.h:102-103
    "Do not keep references to |params| or |model| outside of this callback."
cef_menu_model.h:48
    "The methods of this class can only be accessed on the browser process the UI thread."
```

而本 MCP 工具跑在**非 UI 线程**（`MCP_Stdio.wsv:324` 缓存线程类）⇒ **保存菜单句柄延迟调用不可行**；
又因每次右键都是**全新的默认菜单模型**，规格必须**每次右键重施**。
故唯一可行形态 = **预置规格 + 在回调内一次性施加**（方案甲）。

### 122.2 实现（四个部件，均已落地）

| 部件 | 位置 | 要点 |
|---|---|---|
| 规格暂存 | `MCP_Server.wsv` 的 `类 MCP命令服务器` 静态字段 ×6 | `菜单规格文本`/`菜单已启用`/`菜单施加次数`/`菜单最近施加条数`/`菜单上次施加时刻`/`菜单上次错误` |
| 施加逻辑 | 同文件 新方法 `应用菜单规格 (顶层菜单) → 施加条数` | 逐行解析 → 按类型调用类库 `添加菜单/添加Check菜单/添加Radio菜单/添加分隔栏/添加子菜单` → 可选 `选中状态/置禁止状态/设置快捷键` |
| 触发点 | `MCP_BrowserEvents.wsv` 的 `浏览器_即将打开菜单` 回调 | 在**模型有效期内**调用施加；顺手保留了原有的 `context_menu_opening` 事件记录 |
| 工具分派 | `MCP_Server_Core.wsv` | `action=set/get/clear` + schema/注册表登记 |

**规格格式（逐行文本，字段用 `|` 分隔，标签经 `规则字段转义` 以容忍 `|`）**：
`类型|标签|命令ID|参数|父命令ID|快捷键`
- 类型：`item`/`check`/`radio`/`sep`/`sub`
- 参数：`item`与`sub`=1可用0禁用；`check`=1选中；`radio`=群ID；`sep` 忽略
- 父命令ID：`0`=顶层；**非 0 = 挂到其上方最近的 `sub` 行**（故子项须紧跟其 sub 行）
- 快捷键：仅用于显示（如 `70C` = 键码70+Ctrl，可组合 `S`/`A`），触发仍需自行发键盘事件

**四条关键设计（都对应一个真实风险）**：
1. **规格为空 / 未启用 → 什么都不做并返回 0**。绝不能在规格为空时 `清空菜单` ——
   那会把 CEF 默认菜单清掉，**右键菜单直接消失**。
2. **命令ID 必须落在 `26500..28500`**（CEF `MENU_ID_USER_FIRST/LAST`），
   越界**明确拒绝并说明区间**；留 `0` 则由服务端从 26501 起**自动分配**（AI 不必自己编号）。
3. **每次右键重施**（每次都是新模型）。
4. **默认动作改为 `get`（只读）**：空参调用应当成功并给出状态，而不是报"缺少 items"。

同时**零前置**：`set` 会自动打开 `是否监控菜单事件`（该开关默认关，且 `event_all_enable` 不含菜单族）。

### 122.3 验收：8/8（行为级，关键判据是"CEF 模型真的接受了条目"）

`_audit/verify_context_menu.py`（**8/8**）：

| 臂 | 期望 | 实测 |
|---|---|---|
| F `get`（未设置时） | 正常返回、`enabled:false` | ✔ |
| A `set` 5 行规格 | 报条目数并自动分配 ID | `spec_lines:5, 含命令ID条目=4` ✔ |
| B 右键一次 | 回调施加 | `apply_count:1`，**`last_applied_items:5`** ✔ |
| C 命令ID 越界 | 明确拒绝 | `命令ID越界: 100 \\| 必须在 26500..28500` ✔ |
| D 类型非法 | 明确拒绝 | `类型非法: bogus \\| 支持 item/check/radio/sep/sub` ✔ |
| E `clear` | 幂等成功 + 状态复位 | `enabled:false, spec:""` ✔ |

**`last_applied_items:5` 是本节最有力的证据** —— 它不是本工具的自述，而是类库
`添加菜单/添加子菜单/添加分隔栏/添加Check菜单` 的**返回值计数**，即 **CEF 的菜单模型确实接受了这 5 个条目**
（item + sep + sub + 其子项 + check，ID 被自动分配为 26501–26504）。

### 122.4 本轮自身失误（编译当场抓住）

补丁用**行前缀** `添加工具JSON ("browser_intercept", ` 作锚点，替换后把该行前缀吃掉、
其余部分（描述+schema）被留在下一行成为**孤立片段**：

```
<MCP_Server.wsv>, 9999: 错误: 括号缺失或不匹配
```

已补回前缀并复核两处注册各 1 条。教训：**替换"整行"时必须把整行作为锚点**，
只拿行首片段当锚点会把尾巴留在原地 —— 这类错误编译器能抓住，但同类错误若落在注释/字符串里就抓不住。

### 122.5 状态与下一步

工具总数 **313 → 314**；台账 **314/314** 已测，通过 **307** / 失败 7
（TARGET 3 / OTHER 2 / GUARD 1 / PARAM 1），**前置缺失 0、能力缺失 0、卡死 0**；
编译 0 警告；fastcheck 41/41。

1. 菜单类库仍有可扩展项：`置颜色`/`置字体`/`取子菜单` 等（第100轮报告列出 22 个未封装 CEF 方法，
   其中 `Insert*At`/`Get*At` **类库未封装**，故只能追加、无法按索引反查 —— 属类库边界，非本项目缺口）。
2. 复查 `browser_back`/`browser_forward` 是否补 `wait_for_load`。
3. 类库 `类_FBrowser_命令行` 14 项属"仅启动期生效"，需先决定是否做启动参数通道。
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
    if '## 122. 第105轮' in text:
        print('!! §122 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 122. 第105轮') == 1
    print('已追加 §122; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
