# -*- coding: utf-8 -*-
"""追加报告第 106 节(第90轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 106. 第90轮：三个 C 类真缺陷收口 —— 补上「用户标识」通路（find_by_tag 由不可达变可用）"
        "＋ 前置缺失类失败归零（覆盖率自动补前置）")

SECTION = """

---

%s

### 106.1 C 类① `browser_find_by_tag`：不是改文案，而是把**缺失的通路补上**

分诊判定它"在本 MCP 内永远不可能成功"。本轮查清了根因，且发现**修复成本很小**：

- 类库里**用户标识只能在创建浏览器时设置**：`FBrowser_创建浏览器` 的**最后一个参数**就是 `标识`
  （`FBroLib.wsv:563`，签名第 8 参）；`FBrowser_创建后台浏览器` 亦然（`:604`，第 7 参）；
  `取用户标识` 注释写"浏览器创建的时候传递设置的值"。**全库没有运行期设置接口**。
- 而本项目两个创建调用都把那个位置**留空**（`main.wsv:228` 可见 / `:221` 后台），
  于是标识恒为空 —— 工具永远查不到东西，文案还建议去用**只读的** `browser_user_tags` "设置"标识。

**修法（复用项目既有的"待创建"握手，不发明新机制）**：
1. 新增静态握手字段 `待创建标识`（与 `待创建URL` 并列）；
2. `browser_create` 增加 `tag` 参数 -> 写入该字段（**未传则写空串**，防止上一个标识泄漏给新浏览器）；
3. `main.wsv` 两个创建调用把该字段放回类库签名里**本来就空着的** `标识` 槽位。

**验收 5/5**（`_audit/verify_browser_tag.py`）：

| 判据 | 实测 |
|---|---|
| ① 带 tag 创建 | 成功 |
| ② `browser_user_tags` 列出该标识 | `{"tags":["","mcpTagProbe"]}`（此前本机只有空标识） |
| ③ **`browser_find_by_tag` 必须查到** | `{"id":2,"url":"","tag":"mcpTagProbe"}` ✔ |
| ④ **对照（防假阳性）**：不存在的 tag 仍须失败 | `未找到标识为: mcpNoSuchTag_zzz 的浏览器…` ✔ |
| ⑤ 不传 tag 创建不继承旧标识 | `tags:["","mcpTagProbe",""]` ✔ |

台账随之 `browser_find_by_tag` **fail -> pass**（用"先按通用 tag 值建一个带标识浏览器"的前置调用，
让探针真正打到实现）。

### 106.2 C 类②③：两条不可行动的失败消息

- `browser_find_by_hwnd`：原先只有一句"未找到窗口句柄为 N 的浏览器"。现补上
  **如何取得有效句柄**（`browser_get_window_handle` / `browser_window_info` 的 hwnd 字段）+
  说明句柄是运行时值无法写死 + 可改用 `browser_list` / `browser_find_by_tag`。
- `browser_find_by_tag`（未命中时）：改为指向**真正的设置方式**（`browser_create` 的 `tag` 参数），
  并明确 `browser_user_tags` 是**只读**清单（旧文案把它当写工具，已更正）。

### 106.3 C 类③ 再进一步：把"前置缺失"变成"自动补前置"（前置缺失类失败 = 0）

上一轮我只把 `Precise coverage has not been started.` 改写成了"请先调 action=start"，
但那只**把前置缺失说得更清楚**，并没有消除它 —— 台账因此多了一条 `PREREQ` 失败，
与本目标"前置缺失类失败 = 0"直接冲突。

本轮改成**自动补前置**（与项目既有的"反应式补域"同一思路）：`take` 未开启时自动
`Profiler.enable` + `startPreciseCoverage` 再取一次，并经 `auto_prepared` 如实上报。
实测空参调用：

```
{"success":true,
 "auto_prepared":"browser_reverse_precise_coverage: 精确覆盖率尚未开启, 已自动 Profiler.enable + startPreciseCoverage 并重新取数",
 "data":{...,"method":"Profiler.takePreciseCoverage","result":"{\\"result\\":[],\\"timestamp\\":39401.1657}"}}
```

台账 `PREREQ` **1 -> 0**，该工具转 pass。

### 106.4 又发现**两处**"GUI管理"错误前提（该前提累计已传播到 4 处）

`MCP_Server_System.wsv` 里 `browser_create_tab` 与 `browser_task_runner_post` 的拒绝理由都写着
**"GUI窗口自动管理浏览器实例"** —— 与 §96.2 已推翻的前提同源（本项目是控制台程序、并无 GUI 管理窗口）。
已改为如实说明"本工具**刻意不实现**（项目未开放该入口）"，不再拿不存在的东西当理由。

### 106.5 本轮我自己的两次失误（都是老问题的变体）

1. **又用 ASCII 双引号写进了火山字符串字面量**（第三次）：`旧文案称"GUI窗口…"` 与
   `tag:"你的标识"`（后者是 Python `\\"` 写成了 `\"`，落盘后变成裸引号）-> 直接报
   3 个 `发现字符处于无效位置`。**规则重申：`.wsv` 字面量内部一律用全角引号「」；**
   若确实要写转义引号，Python 里必须写 `\\\\"`（生成 `\\"`）。
2. **多行锚点在 CRLF 文件上匹配失败**：`MCP_Server_Reverse.wsv` 是 CRLF，而我用 `\\n` 拼的多行锚点
   自然 0 命中（脚本如实报了"预期 1 次, 中止"，没有误改）。此前对该文件的改动都是**单行**片段，
   所以这个坑一直没暴露。已让脚本按文件实际行尾自适应。

### 106.6 本轮指标

| 项 | 值 |
|---|---|
| 工具数 | 313 |
| 台账 | 307/313 已测（+6 个危险项已受控实测） |
| **通过** | **296**（本轮 294 -> 296） |
| **失败** | **11**（本轮 13 -> 11） |
| **前置缺失类失败** | **0**（本轮 1 -> 0）✔ |
| 把实例卡死 | 0；`CAPABILITY` 失败 = 0 |
| 失败性质 | OTHER 4 / TARGET 3 / PARAM 2 / GUARD 2 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增能力 | `browser_create` 的 `tag` 参数（用户标识通路）；覆盖率默认动作自动补前置 |

### 106.7 仍未做（下一轮）

- 台账剩 **6** 个"跳过项"（危险工具，已受控实测过，但未入账）。
- `browser_reverse_return_value` / `browser_reverse_set_variable` 需要**真命中断点**才可能通过
  （当前测试页无脚本）——属取舍，分诊 §4 列为待决断。
- `browser_reverse_instrument_script` 阻塞 JS 通道的根因；陈旧活帧隐患（§101.4）。
- **幽灵注册/反向幽灵**：`browser_create_tab`/`browser_task_runner_post` 可**直接调用**（有实现）
  却**不在工具清单**里（`mcp_probe` 报"没有该工具"）—— 与目标 C 线的"有号无实现"正好相反，
  值得下一轮专门核对。
- 能力面别的候选缺口（类库 `命令行` 系列、菜单/快捷键 13 项等）。
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
