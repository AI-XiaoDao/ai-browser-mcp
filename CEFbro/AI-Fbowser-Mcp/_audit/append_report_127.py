# -*- coding: utf-8 -*-
"""追加报告第 127 节（第 110 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 127. 第110轮：新增 `browser_fill_get_text` / `browser_fill_set_text`（innerText 读写，**工具数 316**）

### 127.1 先复核"缺什么"：缺口比子代理说的更精确

第107轮刷新报告写的是"填表族 13 个工具里**唯独没有取元素 innerText**"。本轮复核源码后发现更准确的事实：

| 既有工具 | 实际取/写的是 | 依据 |
|---|---|---|
| `browser_fill_attr_get`（省略 `attribute`） | **textContent**（原始文本） | `MCP_Server_Form.wsv:248` 的 JS 用 `e.textContent` |
| `browser_dom_inner_html` | **innerHTML**（含标签） | — |
| `browser_dom_set_html` | 写 **innerHTML** | — |
| `browser_dom_set_value` | 写 **.value**（表单控件） | — |

⇒ 真正**没有任何等价物**的是 **innerText（渲染后可见文本，受 CSS 影响）的读与写**。
所以只加这两个能力，**不复制已有的 textContent / innerHTML 路径**（避免"重复造轮子"）。

### 127.2 实现（沿用项目既有先例，不另造轮子）

- **读** `browser_fill_get_text {selector}`：CDP JS 优先 + **哨兵值**
  （`__MCP_NO_ELEM__` / `__MCP_TEXT__`）区分"元素不存在 / 文本为空 / CDP 取不到" ——
  与 `browser_fill_attr_get` 完全同款写法（`MCP_Server_Form.wsv:206` 起）。
- **写** `browser_fill_set_text {selector, text}`：
  · `text` 用 `简单转义JS` 嵌进**单引号** JS 字符串（与项目对该 helper 的约定一致）；
  · **写后回读验证**（项目横切不变量："不静默假成功"）；不一致则如实报失败；
  · **省略 `text` 直接拒绝**（省略会被当空串而清空元素文本），显式传 `""` 才允许清空 ——
    错误文案写明这一区别。
  · 不实现原生回调式读 API 的回退：项目注释已记载该路径"本内核恒返回空值并被写成字面 null"，
    故 CDP 不可用时给出**可行动失败**，不谎报成功。

### 127.3 验收 7/7 —— 核心是**区分性对照**

"工具返回了东西"不足以证明它读的是 innerText。造一个含**隐藏子元素**的节点做对照：

```html
<div id="tt">可见<span style="display:none">隐藏</span></div>
```

| 工具 | 返回 | 含义 |
|---|---|---|
| `browser_fill_get_text (#tt)` | **`可见`** | innerText：渲染后文本，**隐藏的不算** ✔ |
| `browser_fill_attr_get (#tt)`（不传 attribute） | **`可见隐藏`** | textContent：原始文本，**隐藏的也算** ✔ |

两者结果**不同**，即证明新工具确实读 innerText、**不是既有工具的重复包装**。

其余臂：读 `h1` → `Example Domain` ✔；元素不存在 → `元素不存在: #not-exist-xyz | 建议: 先用 browser_fill_exists…`（不返回空串冒充）✔；
写入 `新文本ABC` → 回读一致 ✔；省略 `text` → `text 不能省略 \\| 省略会被当作空串而清空元素文本; 确实要清空请显式传 text: ""` ✔；
显式 `""` → 清空且回读为空 ✔。

### 127.4 台账：给新工具补探针覆盖值（避免把"守卫"当"实现"测）

通用填充值 `#mcp-probe-nonexistent` 会让两个工具都打到"元素不存在"守卫（**如实报错**，属允许类别，但没测到实现）。
按项目既有做法补上：

- `browser_fill_get_text`：`selector = "h1"`（真实存在、只读、无副作用）。
- `browser_fill_set_text`：**先 `TOOL_PRE_CALLS` 注入**一个专用探针元素 `<div id="mcpProbeText">`，
  再对它写入 —— **不碰页面既有内容**，避免影响同一轮其它用例。

台账随之变为 **316/316** 已测、通过 **309** / 失败 7（TARGET 3 / OTHER 2 / GUARD 1 / PARAM 1）。

### 127.5 本轮自身失误（第二次踩换行）

补丁第一次跑 **0 命中**：`MCP_Server_Form.wsv` 是 **CRLF**，而我的多行锚点用 `\n` 去 `count`。
修法：**锚点按目标文件的换行归一化后再比对**（`old.replace('\\n', nl)`）。
这是本项目第二次因换行吃亏（第一次是第100轮"删行时只吃掉 `\\n` 留下 `\\r` 把两行粘在一起"）。
**纪律：凡与文本锚点相关的事，先把目标文件的换行读出来再动手。**

### 127.6 状态与下一步

工具总数 **316**（首次突破 314）；台账 **316/316**，通过 **309** / 失败 7，
**前置缺失 0、能力缺失 0、卡死 0**；编译 0 警告；fastcheck 41/41。

1. `FBrowser_JS交互_注册/删除`（类库原生双向 JS↔宿主查询通道，与 CDP `Runtime.addBinding` 不是一回事）。
2. `browser_vip_execute_js_context` 加 `main`/`all_frames`/`frame_index` 三档 target（一次打穿所有 iframe）。
3. `类_FBrowser_菜单模式` 剩余未接线方法（该类 36 个，已接线约 15 个）。
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
    if '## 127. 第110轮' in text:
        print('!! §127 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 127. 第110轮') == 1
    print('已追加 §127; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
