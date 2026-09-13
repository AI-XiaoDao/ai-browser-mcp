# -*- coding: utf-8 -*-
"""追加报告第 95 节(第79轮)。写入前断言: 无BOM、无CRLF、无重号节。"""
import io
import os
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'MCP工具可用性检测报告.md')
HEAD = ("## 95. 第79轮：browser_reverse_search 必失败（注入JS未终止字符串）"
        "＋ 异常原因被丢弃（横切）＋ 一个「用户代码被执行两遍」的安全缺陷")

SECTION = """

---

%s

### 95.1 `browser_reverse_search` 稳定失败：注入 JS 是解析期错误

台账实录：`脚本搜索错误: JS异常:Uncaught` —— 只有 "Uncaught"，**没有任何原因**，完全不可行动。

注入串里有一处 `t.split('\\r\n')`。该项目的字符串转义惯例（均有代码为据）是
`\\n` 在 `.wsv` 字面量里就是**真实换行**（例：Prometheus 输出 `"...已注册(1/0)\\n"` 依赖它产生真换行），
`\\\\` 是**一个反斜杠**（例：`子文本替换 (安全词, "\\\\", "\\\\\\\\")`）。于是这一处生成给 JS 的是

```
'\\' + 'r' + <真实换行>
```

即**单引号字符串里含裸换行 = 未终止的字符串字面量 = 解析期 SyntaxError**。

判别性 A/B（`_audit/diag_reverse_search_js.py`，先把页面重载并**探针确认干净**再测）：

| 臂 | split 片段 | CDP 原始结果 |
|---|---|---|
| A 现状 | `'\\r\\n'`（反斜杠+r+真换行） | `SyntaxError: Invalid or unexpected token`，`columnNumber: 170` |
| B 修法 | `'\\n'`（JS 的换行转义） | `{"query":"sign","found":0,"results":[]}` 正常 JSON |

修法：`src/MCP_Server_Core.wsv` 的 `srCode` 里 `t.split('\\r\n')` → `t.split('\\n')`。
全库 `.split(` 扫描确认这是**唯一**一处坏写法（其余是 `.split('.')`、`.split(/\\\\s+/)`，均合法）。

### 95.2 横切可诊断性缺陷：异常原因被格式化器丢掉（这才是"只报 Uncaught"的原因）

`browser_reverse_search` 之所以只报 "Uncaught"，不是因为异常简单，而是因为共享格式化器读错了字段：

```
excText = yyjson取文本 (excObj, "text")        # CDP 的 exceptionDetails.text **固定就是 "Uncaught"**
如果 (excText == "") { excText = yyjson取文本 (excObj, "description") }   # 该层根本没有这个键
```

真正的原因在 `exceptionDetails.exception.description`。CDP 原始响应为证：

```
exceptionDetails.text                  = 'Uncaught'                                  <- 旧实现只读这个
exceptionDetails.exception.description = 'SyntaxError: Invalid or unexpected token'  <- 真正原因
```

影响面（`grep CDP执行JS并等待` 命中 82 处调用点）：凡是走 `src/MCP_Server.wsv` 的 `CDP执行JS并等待`
的 JS 异常，**全部**只会得到 "Uncaught"。已改为优先 `exception.description` → 退回 `text`，
并附 `@line/col`（解析期错误只有行列号，靠它才能定位注入串）。同时删掉紧随其后、读取
`exceptionDetails.description` 的冗余兜底块（该键在该层不存在，已成死代码）。

修复后实测：
- 运行期异常 → `JS异常:Error: mcp-fmt-probe-7d21\\n    at <anonymous>:1:7`
- 语法期异常 → `JS异常:SyntaxError: Invalid or unexpected token @line 0 col 8`

### 95.3 顺带查出的安全缺陷：`browser_execute_js` 会把用户代码**再执行一遍**

验收 95.2 时发现 `browser_execute_js {code:"throw ..."}` 返回的仍是
`[无法序列化的值] 可能原因: ①JS返回了DOM对象/函数等…`（来自**原生回退路径** `MCP_Callbacks.wsv:51`），
并不是 CDP 给出的真原因。查 `src/MCP_Server_Core.wsv` 的 `browser_execute_js` 分支：

```
CDP值 = CDP执行JS并等待 (code, …)
如果 (CDP值 != "" && CDP值 != "undefined" && 是否以 (CDP值, "{\\"error\\"") == 假)  -> 成功
// 否则**一律**继续往下走原生回退
```

CDP 侧对异常返回的 `{"error":"JS异常:<真原因>"}` 也以 `{"error"` 开头，于是被判成"CDP 通道不可用"，
进入原生回退。后果三条：

1. **真原因被丢弃**（即便格式化器已给出原因）；
2. **用户代码被再执行一次**（原生路径）—— 写操作类 JS 的副作用会跑两遍，属**安全性**问题；
3. 最终报成与原因无关的 `[无法序列化的值]`。

修法：把 `JS异常:` 认定为**终局结论**（CDP 已明确回答），直接失败返回真原因，不再回退；
`CDP执行失败:` 等**通道类**错误仍照旧回退（那才是回退存在的意义）。

### 95.4 测量卫生：第一版验收跑在被污染的页面上

本轮 A/B 的**第一版没有重载页面**，臂 B 报：

```
RangeError: Maximum call stack size exceeded
    at __obj.<computed> (<anonymous>:1:544)   (反复自递归)
```

那不是本工具的问题，而是**同一批台账里先跑过的 `browser_reverse_instrument` 在页面上装了透明插装**
（包装 `Function.prototype.apply/call`、`Array.prototype.push` 等）。臂 B 的结论建立在**被污染的页面**上，
不可信。改为"先 navigate 重载 + 探针确认三个插装标记均 `undefined`"后才得出 95.1 的结论。

**由此新增一条待办（已记录，未做）**：插装/挂钩类工具（`browser_reverse_instrument`、
`browser_kernel_*` 的注入族）目前**没有卸载/还原**入口，只能靠重载页面清除。这是能力缺口，
也是"同一批测试互相污染"的源头。

### 95.5 测试侧两个缺陷（会让"测到守卫"冒充"测到实现"）

1. **`_audit/mass_probe.py` 漏传工具名**：该文件第 298 行原为 `build_args(schema, desc)`，
   而 `build_args` 需要第 3 个参数 `tool_name` 才能查到 `TOOL_ARG_OVERRIDES` ——
   于是**整张覆盖表在该入口完全失效**，工具仍收到通用兜底值 `mcp_probe`/`1`。
   已修为 `build_args(schema, desc, name)`。（`tool_ledger.py` 一直有传，故台账不受影响。）
2. **`browser_vip_set_css_version` 的覆盖值越界**：原覆盖为 `"110"`，而该工具真实域是 **116-135**，
   即使类型写对也会被第二道范围守卫拦下，仍测不到实现。已统一为域内值 `"120"`。
   改后这三个同族工具全部 pass。

### 95.6 产品文案与自己代码矛盾（已修）

`MCP_Constants.wsv` 的 `错误_版本必须为正整数` 写的是 `有效范围: 1-65535`，
但紧接着的第二道守卫只接受 **116-135** —— 两个数字互相矛盾，且该常量**只**被这三个版本工具使用
（grep 证实：3 处引用全在 `MCP_Server_VIP.wsv`）。已把文案改为真实范围 116-135。

### 95.7 重要前提被推翻：本项目**不是**"嵌入式GUI窗口"架构（子代理复核 + 我独立确认）

子代理只读复核提出并被我独立复核确认：本项目是 `/SUBSYSTEM:CONSOLE` 程序，创建浏览器时
**`窗口信息.父窗口句柄 = 0`**（`src/main.wsv:205`，类库注释：为 0 则以桌面为父窗口），
尺寸写死 0,0,1000×800（`src/main.wsv:206-209`）；用户看到的窗口**就是浏览器窗口本身**。

因此 `browser_move_window` / `browser_set_auto_resize` 的拒绝文案
"⛔ 嵌入式GUI浏览器不支持 … 窗口尺寸由主窗口自动管理" **与代码事实不符** ——
这两个能力和"显示/隐藏窗口"应属**可做到**类别，而不是"本机不支持"。

**本轮只记录、不改实现**（避免半成品）：需要先核实可用 API（`置自动调整大小` 全项目 0 调用、
`置窗口属性` 已被 `browser_set_window_style` 使用），再动手。已把结论与 API 线索存入本节备查。

同批复核还指出：配置键 `window_topmost` / `window_width` / `window_height` 在
`MCP_Server.wsv` 里被读入却**全项目零读取点**，而 `docs/MCP工具配置说明书.md` 对外承诺可用 ——
属"死配置 + 文档不实"，记入待办。

### 95.8 调试器三件套分诊（只读复核，本轮未修）

| 工具 | 根因 | 依据 |
|---|---|---|
| `browser_debugger_flow` | 断点 0 命中却判为"设置成功"，且无 `url` 时无任何触发动作，随后死等默认 45000ms（客户端 15s 就放弃） | `CDP设置断点结果是否成功` 只看 success 标志、从不看 `locations` |
| `browser_debugger_auto` | 同类 0 命中缺陷 + 每命中默认等 60000ms×5，**超时后仍无条件写 `success:true`** → 耐心客户端会拿到 `success:true, hits:0` 的**假成功**（违反"不静默假成功"） | 超时分支只 `跳出循环`，随后无条件 `加入逻辑值成员 ("success", 真)` |
| `browser_debugger_evaluate` | 帧 ID 只来自调用方参数、无校验、不会自取活帧（同族 `inspect` 有自取），错误 `-32000` 原样透传不可行动 | 台账传的 `mcp_probe` 是测试占位串，非 stale |

三项均已定位到 `file:line` 并备好改动清单，**留待下一轮**（其中"让失败可行动"优先于"让它成功"）。

### 95.9 本轮指标

| 项 | 值 |
|---|---|
| 工具数 | 312 |
| 台账 | **253/312** 已测（本轮 244 → 253） |
| 通过 | **209**（本轮 200 → 209） |
| 把实例卡死 | 0 |
| 本轮修复 | 3 个真实缺陷（含 1 个安全类）+ 1 处自相矛盾文案 + 2 个测试侧缺陷 |
| 新增验证脚本 | `verify_reverse_search_and_exc.py`（**6/6**，含反例对照）、`diag_reverse_search_js.py`（判别性 A/B，带页面清洁度探针） |
| 构建 | 0 警告 0 错误；fastcheck 41/41 |
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
