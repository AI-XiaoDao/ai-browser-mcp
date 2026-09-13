# -*- coding: utf-8 -*-
"""追加报告第 126 节（第 109 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 126. 第109轮：`browser_context_menu` 增加 7 种"修改已存在条目"类型（含**默认菜单项**）、并顺带完成 8 个类库方法的可用性冒烟

### 126.1 从"只能加"到"能改能删"

第105轮的规格只认 5 种**创建**类型（item/check/radio/sep/sub）—— 只能往菜单里**加**东西。
本轮补上 7 种**修改已存在条目**的类型（对应类库 8 个写方法）：

| 类型 | 类库方法 | 作用 |
|---|---|---|
| `del` | `删除菜单 (命令ID)` | 删除条目 |
| `relabel` | `置菜单标签 (命令ID, 标签)` | 改标签 |
| `vis` | `置可见状态 (命令ID, 可见)` | 显示/隐藏（参数 1/0） |
| `dis` | `置禁止状态 (命令ID, 禁止)` | 禁用/启用（参数 1/0） |
| `mark` | `选中状态 (命令ID, 选中)` | 勾选状态 |
| `accel` | `设置快捷键 (命令ID, 键码, shift, ctrl, alt)` | 设快捷键（复用第 6 列，如 `70C`） |
| `noaccel` | `存在快捷键` + `移除快捷键` | 移除快捷键 |

### 126.2 ★关键语义：**修改类必须允许 CEF 标准区间**

创建新条目时命令ID 必须落在 CEF 自定义区间 `26500..28500`（留 0 自动分配）；
但**修改类作用于已存在的条目**，其中包括**浏览器默认菜单项** —— 它们的命令ID 是 **CEF 标准ID**
（如 后退=100）。若沿用"必须 26500..28500"的校验，**恰好会把最有价值的一类操作（改默认菜单）全部拒掉**。
故按类型分档：创建类→自定义区间；修改类→`>= 1` 即可。
错误文案也据此给出两条路：「自建项用你分配的 26500..28500，浏览器默认项用其 CEF 标准ID（如 后退=100）」。

### 126.3 验收 6/6（`_audit/verify_menu_spec_types.py`）

一次右键施加 9 行规格：创建 → 改标签 → 禁用 → 隐藏 → 勾选 → 设快捷键 → 移除快捷键
→ **对默认菜单项（标准ID 100）设快捷键** → 删除。

```
{"apply_count":1,"last_applied_items":9,"last_error":"", …}
```

| 臂 | 期望 | 实测 |
|---|---|---|
| 修改类给 `ID=0` | 明确拒绝 + 指引 | `修改类(del)但命令ID 为 0 \\| …浏览器默认项用其 CEF 标准ID(如 后退=100)` ✔ |
| `set` 九行规格 | 全部接受 | `spec_lines:9` ✔ |
| 右键施加 | 类库方法真的成功 | **`last_applied_items:9`** ✔ |
| **默认项标准ID(100)** | 不被区间校验拒掉 | `last_error:""` ✔ |
| 非法类型 | 仍被拒绝 | `类型非法: bogus \\| 创建类:…; 修改类:…` ✔ |

`last_applied_items:9` 依然是**类库返回值计数**（不是本工具自述），故它同时证明这 9 次调用**都真的成功了**。

### 126.4 顺带完成：8 个类库方法的可用性冒烟（回应第108轮那条线索）

第108轮发现类库方法 `是否存在图片()` **本机编译不过**（`FBroHSContextMenuParams_HasImageContents` 找不到标识符），
并提出"声明 ≠ 本机可用，只有用一次才知道"。本轮把 8 个菜单写方法**真正接上线**，于是：

**构建成功即是冒烟通过** —— 这 8 个方法（`删除菜单`/`置菜单标签`/`置可见状态`/`置禁止状态`/`选中状态`/
`存在快捷键`/`移除快捷键`/`设置快捷键`）在本机**可编译、可链接、且运行期返回成功**（`last_applied_items:9`）。
与 `是否存在图片()` 形成明确对照。

**这条经验值得固化成方法**：**"接上线 + 编译"本身就是类库可用性冒烟测试** ——
不需要另造批处理框架；每实现一个用到类库方法的工具，就等于对那几个方法做了一次可用性验证，
而不可用的会**在构建阶段直接暴露**（不会静默）。

### 126.5 状态与下一步

工具总数 **314**；台账 **314/314** 已测，通过 **307** / 失败 7
（TARGET 3 / OTHER 2 / GUARD 1 / PARAM 1），**前置缺失 0、能力缺失 0、卡死 0**；
编译 0 警告；fastcheck 41/41。

1. 补 `browser_fill_get_text`（innerText 读）—— 填表族 13 个工具里唯独缺"取元素 innerText"，
   且 innerText 与 innerHTML 语义不同、不能互替。
2. `FBrowser_JS交互_注册/删除`（类库原生双向 JS↔宿主查询通道，与 CDP `Runtime.addBinding` 不是一回事）。
3. `browser_vip_execute_js_context` 加 `main`/`all_frames`/`frame_index` 三档 target。
4. B 组 55 条"仅启动期生效"是否做启动参数通道。
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
    if '## 126. 第109轮' in text:
        print('!! §126 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 126. 第109轮') == 1
    print('已追加 §126; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
