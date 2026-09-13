# -*- coding: utf-8 -*-
"""追加报告第 109 节(第93轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 109. 第93轮：一条决定性测量**推翻我上一轮的根因** —— 卡死不是自检探针造成的，"
        "而是「装上插装」本身（并据此否掉一个本来打算做的改动）")

SECTION = """

---

%s

### 109.1 关键测量：把自检关掉，**同样卡死**

上一轮（§108.1）我读源码得出：`install` 的自检探针用 `Runtime.evaluate` 去验证"新脚本是否会暂停"，
于是**探针自己触发刚装上的插装**，导致那条请求永不返回、占住 CDP 队列。
这个解释与当时的实测吻合，看起来已经说清了。**但它是错的。**

决定性对照（`_audit/diag_probe_is_the_trigger.py`，两臂各从干净实例重来）：

| 臂 | 装入前 JS | install 结果 | 装入后 JS |
|---|---|---|---|
| ① `verify=true`（默认，带自检探针） | 正常 0.03s | 成功，`verified:"true"` | **30s 超时** |
| ② `verify=false`（**关掉自检，不发探针**） | 正常 0.03s | 成功，`verified:"skipped"`（0.06s 就返回） | **30s 超时** |

**两臂都卡死** ⇒ **探针不是原因**。真正的原因是：**装上 `beforeScriptExecution` 插装这件事本身**，
就足以让本会话的 JS 通道失效。机理修正为：

> 本项目"执行 JS"的通道**就是 `Runtime.evaluate`**，而 `Runtime.evaluate` **本身是一次脚本执行**；
> 被装上的插装正是拦"执行脚本之前"的 —— 于是**第一次**之后的任何 evaluate 都会被自己的插装拦住，
> 页面暂停、该 CDP 请求永不返回、单条队列被占。
> 探针只是让它**更早**发生（发生在 install 调用内部），并不是必要条件。

### 109.2 价值：**在动手改之前**否掉了一个想做的改动

上一轮我在报告里把"改掉探针的验证方式"列为待办（§108.7），本轮本来打算实施
"探针前先 `setSkipAllPauses` 再探、探完恢复"，以消除 install 的卡死。
这条决定性测量说明：**那样改不会解决问题** —— 卡死来自插装本身，探针改得再好，
调用方**下一次**执行 JS 时照样会撞上。于是这个改动**不做**（省下一次无效改动与一次构建）。

同时确认了 §102 那个**确认闸**（`install` 必须显式 `confirm:true`）是正确判断：
既然 install **无法**做到默认安全，就不该让"顺手空参调一下"把会话搞死。

### 109.3 工具描述按实测更正（把错的解释换成对的）

`browser_reverse_instrument_script` 的描述里原本写着我上一轮的（错误）结论：
"…均**无法恢复, 只有重启进程才能恢复**"。已改为实测事实：

- **根因**：JS 通道即 `Runtime.evaluate`，它本身就是脚本执行，被自己的插装拦住 -> 请求永不返回、队列被占；
- **明确写出"这不是自检探针造成的"**（关掉自检 verify:false 装入后同样卡死），免得后来者重走我这条路；
- **恢复办法（三条逐一实测）**：`action=suppress` **可以**恢复（约 45s，走项目既有的卡死自救；
  客户端请留足 60s 超时），`browser_debugger_resume` 与 `browser_debugger_disable` **都不能**；
  重启也可以但没必要；
- 使用建议改为"准备好随后 `action=suppress` 止血"，不再说"只在你打算重启时使用"。

验证：构建 0 警告 0 错误；`tools/list` 里该描述已含新根因、且**不再含**"只有重启进程才能恢复"。

### 109.4 本轮我自己的失误：**第四次**把 ASCII 双引号写进火山字符串字面量

在长句中文里我又写了 `拦"执行脚本"的` 与 `"装上插装"本身` -> 编译直接报
`MCP_Server.wsv, 9930: 错误: 发现字符处于无效位置`（并且因为编译失败，实例没被重启，
后续验证脚本报连接被拒）。已改用全角引号「」修正。

这是**第四次**同类失误（前三次见 §103/§106）。前面几次我都写了"规则重申"，仍然复发，
说明只"记住"不够。**从本轮起按机械规则执行：凡是给 `.wsv` 生成中文文本，一律不打 ASCII 双引号，
需要引号就写「」；写完先跑 `loop.py --syntax` 再说别的。**
（更稳的做法：把这类文案放进 `.py` 脚本时就用 `chr(34)` 或占位符，不让裸引号出现在我的中文句子里。）

### 109.5 本轮指标（未新增能力；改 1 处描述）

| 项 | 值 |
|---|---|
| 工具数 | 313 |
| 台账 | 307/313 已测 |
| 通过 | **296** |
| 失败 | **11**（OTHER 4 / TARGET 3 / PARAM 2 / GUARD 2） |
| 前置缺失类失败 | **0**；把实例卡死 0；幽灵注册 0 |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
| 新增 | `_audit/diag_probe_is_the_trigger.py`（两臂对照，推翻上一轮的根因） |

### 109.6 仍未做（下一轮）

- 既然 `install` 无法默认安全，可考虑**把 `suppress` 变成 install 的可选尾巴**（例如 `install` 顺带参数
  `auto_suppress:true`：装完立刻 setSkipAllPauses，让调用方在"插装已装但不拦"的状态下继续）——
  这需要先实测"先 install 再立即 suppress"是否真能落在一个可用状态，属新一轮的测量任务。
- 台账剩 6 个"跳过项"未入账；`browser_reverse_return_value` / `set_variable` 需真命中断点。
- 陈旧活帧隐患（§101.4）；能力面其余候选缺口（`命令行` 系列、菜单/快捷键 13 项等）。
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
