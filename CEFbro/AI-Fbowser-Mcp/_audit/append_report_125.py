# -*- coding: utf-8 -*-
"""追加报告第 125 节（第 108 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 125. 第108轮：消费"右键上下文"（`类_FBrowser_菜单环境`）—— CDP 完全看不到的一整块信息；并查出**类库自身编译不过**的方法

### 125.1 为什么这是明确的缺口（第107轮刷新的 A 组第 1）

`菜单环境` 形参**早已**出现在三个 CEF 事件签名的函数表里
（`MCP_BrowserEvents.wsv:2661/2679/2694`），却**零消费点** ——
于是 AI 只知道"某处右键了"，**不知道右键在什么上面**。而 **CDP 没有任何右键上下文域**，无替代路径。

### 125.2 实现（两个文件，均在既有通道上，无新增工具）

- `MCP_Server.wsv` 新增 `构建菜单环境摘要 (菜单环境) → 文本`：把 18 个字段取成紧凑 JSON。
- `MCP_BrowserEvents.wsv` 三个 override 调用它：`context_menu_opening` / `context_menu_run`
  （作为事件数据）与 `context_menu_command`（作为 `menu_env` 子字段）。
- **生命周期合规**：与 `菜单模式` 同受 CEF 约束（禁止在回调之外持有），故实现**只在回调内取值成文本**，
  **不保存对象本身**；且仅在 `是否监控菜单事件` 为真时才构造成本。

实测载荷（右键页面上的链接）：

```json
{"available":true,"x":240,"y":217,"type_flags":7,
 "link":"https://iana.org/domains/example","link_unfiltered":"https://iana.org/domains/example",
 "source_url":"","page_url":"https://example.com/?menuenv=1",
 "frame_url":"https://example.com/?menuenv=1","frame_charset":"windows-1252",
 "media_type":0,"media_type_flags":0,"selection_text":"","misspelled_word":"",
 "editable":false,"spellcheck_enabled":false,"edit_state_flags":192,"is_custom_menu":false}
```

### 125.3 验收：**区分性对照**（link 6/6、text 5/5）

因为"字段是否存在"不足以证明"值真的取到了"，故做**两目标对照**：

| 臂 | 期望 | 实测 |
|---|---|---|
| 右键**链接** | `link` 非空 | `"link":"https://iana.org/domains/example"`，`type_flags:7` ✔ |
| 右键**纯文本** | `link` **为空** | `"link":""` ✔（对照成立 ⇒ 字段确实按目标取值） |
| 两臂共同 | 坐标/`page_url`/`available` | `x:240,y:217`、`page_url` 为当前页、`available:true` ✔ |

### 125.4 ★真发现：类库里有一个方法**本机编译不过**（"文档有、本机无"）

第一次构建失败，错误指向**类库自己生成的 C++**：

```
<E:\\HSPC\\plugins\\vprj_win\\classlib\\sys\\FBrowser\\FBroLib.v>, 1895:
  错误: error C3861: 'FBroHSContextMenuParams_HasImageContents': 找不到标识符
```

即技能书类库**声明**了 `类_FBrowser_菜单环境.是否存在图片 ()`，但它生成的 C++ 调用了
**本机 CEF 封装里并不存在的原生函数**。**这类缺口只在"有人真正调用它"时才暴露** ——
类库方法体是按需编译的，所以在此之前一直不可见。

**处置**：不再调用它，改由同类两个可用 getter（`取媒体类型`/`取媒体类型标识`）覆盖图片媒体信息；
**不自行推断 `has_image`** —— 没有枚举值依据时硬猜等于编造语义。注释里写明了原因（含类库文件名与行号）。

**方法论价值（值得推广）**：既然"类库声明 ≠ 本机可用"，那么**任何未被使用的类库方法都可能是不可用的**。
这解释了一类潜在缺口：**静态缺口清单只能给出"声明面"，真实可用性要靠"用一次试试"**。
本节记录的做法（用一次、让编译器说话）可作为后续**批量冒烟**的思路：
对候选类库方法逐个生成最小调用并编译，即可把"声明有、实际不可用"的方法一次性挑出来。

### 125.5 探针教训（第六次）：**原生菜单关不掉**，且两次右键会拿到同一条事件

第一版验收在同一进程里连续右键"链接"再右键"纯文本"，两次都判定失败 —— 因为拿到的**是同一条事件**
（`timestamp_ms` 完全相同）。原因：右键弹出的是**原生 OS 菜单**，而 CDP 的键盘事件只到渲染进程，
**Esc 关不掉它** ⇒ 第二次右键只是"关掉菜单"，不产生新的 `context_menu_opening`。

**修法**：一次运行只右键一次，用两个**全新进程**分别测 link 与 text（并据此得到上面的对照结论）。
**纪律**：涉及原生 UI（菜单/对话框）的用例不要指望用 CDP 复位；**一个用例一个干净会话**最可靠。

### 125.6 状态与下一步

工具总数 **314**；台账 **314/314** 已测，通过 **307** / 失败 7
（TARGET 3 / OTHER 2 / GUARD 1 / PARAM 1），**前置缺失 0、能力缺失 0、卡死 0**；
编译 0 警告；fastcheck 41/41。

1. **类库方法"声明有、本机不可用"批量冒烟**（§125.4 思路）——可能一次性暴露多个同类缺口。
2. 扩展 `browser_context_menu` 规格类型（`del`/`relabel`/`vis`/`check_at`/`accel_at`/`noaccel` 等 8 条）。
3. 补 `browser_fill_get_text`（innerText 读）——填表族 13 个工具里唯独缺这个。
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
    if '## 125. 第108轮' in text:
        print('!! §125 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 125. 第108轮') == 1
    print('已追加 §125; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
