# -*- coding: utf-8 -*-
"""追加报告第 117 节（第 100 轮）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 117. 第100轮：取数类工具"一次调用即得数据"（10 个）、两次失败的静态扫描、以及一次自伤事故与更正

### 117.1 两次系统性扫描：都是**空结果**（如实记录，避免后人重复投入）

| 扫描 | 脚本 | 结果 |
|---|---|---|
| 类库方法**实参个数**是否与类库声明不符 | `_audit/scan_call_arity.py` | 2590 个调用点、156 个候选，**逐个核对后全为假阳性**。两个原因：① `取整数`/`取文本` 这类名字在多个类里都有（全局 name→arity 表无法区分接收者）；② **更根本：编译器本就强制实参个数**，个数错的项目根本编译不过（本项目 0 警告）。故这条路找不出运行期缺陷 |
| 工具 schema 声明了但**全 src 无任何代码读取**的参数 | `_audit/scan_dead_params.py` | 255 个声明参数名，**零引用的 = 0**。即不存在"AI 传了但没人读"的静默无效参数（第一版按"分支体内是否出现"判，因花括号匹配遇 JS 字符串里的 `{` 会提前截断，报出 29 个假阳性 —— 已用"全 src 扣除 schema 行后无引用"这一更强口径取代） |

> 附带结论：技能书 `资料/类库/*.wsv` 是**参考副本**，不是编译器用的类库源码，因此拿它做 arity 比对本身就不成立。

### 117.2 过程性操作备注清理：20 行 + 2 处改写（**含一次自伤事故**）

按 `_hygiene_r98.md` 的 (a) 类清单清理。**没有照单全删**，而是逐条看过上下文后分三类处理：

- **删 20 行**：自包含、零信息的改动史/进度簿记（如"本次仅补登记, 不改任何实现逻辑。"、
  "v2.8.2 续: …R5-R9 剩余预留号开始补齐实现"）。
- **改写 2 处**：该行其实承载"为什么必须这么做"，只是用了历史口吻 —— 改成约束陈述，**知识保留**：
  `// === v1.8 CDP结果回传 (核心修复: …) ===` → `// === CDP 结果回传 (异步命令的结果经 mcp_result 取回) ===`；
  `MCP_Stdio.wsv` 里注入 C++ 的 `// 修复: 无条件等待并消费空行分隔符…` → `// 必须无条件等待并消费空行分隔符…: 客户端分块写时若漏消费, 帧体会错位`。
- **不动 7 条**：5 条在当前源码里已定位不到（**定位不到就绝不盲删**）；2 条是其后的"于是…"残句所依赖的
  首行（如 `MCP_Server_Core.wsv:281/4934`，删掉会让整段的因果链断裂）。

**★自伤事故（值得永久记住）**：清理脚本是"按内容锚点删整行"，但实现里用
`old + '\\n'` 判断可整行删除 —— 而 `MCP_Server_Utils.wsv` 是 **CRLF**，那两条"备注"又是
**行尾 C++ 注释**（`else out.clear();  // 修复: …`）。于是它只吃掉了 `\\n`、把 `\\r` 留下，
**下一行被粘到本行**，注入的 C++ 里出现裸 `@`：

```
错误: <src\\MCP_Server_Utils.wsv>, 19: error C2018: 未知字符 '0x40'
错误: <src\\MCP_Server_Utils.wsv>, 21: error C2018: 未知字符 '0x40'
```

**是构建抓住的，不是我看出来的** —— 若无 `/d` 这一步，这份"清理注释"会静默损坏注入的 C++。
处置：从备份恢复该文件，改为**只改写注释文本、不动行结构**，并复核 CRLF 数量不变（67）。
教训：**行尾不可假设**；对含 `@` 注入块的文件，注释清理必须走"改写"而不是"删行"。

### 117.3 ★把"取数据类工具"做成**一次调用即得数据**（10 个，逐个真机验收）

第99轮查出 26 个 A 类工具（回执带 `poll_hint`）。其中一批**本来就要把数据交回调用方**
（取 HTML/选中项/链接/源码/DOM 树/Cookie），却要调用方再调一次 `mcp_result` —— 与"一次调用成功"直接冲突。
它们都不长耗时，故纳入中央同步等待（`应同步等待` + `取同步等待毫秒` 两张表）。

**关键机制**（本轮才查清）：两张表同时管两条路径 ——
`尝试同步跟随异步响应`（`MCP_Server.wsv:6354`）把回执换成结果；
`命令成功_异步`（`:6427`）**自己**也查这两张表并等任务落地。所以改名单即可统一生效。

**逐个真机验收**（`_audit/verify_sync_additions.py`）—— **不是"加进去就算完"**：

| 工具 | 同步后实测 |
|---|---|
| `browser_dom_get_html` | `<h1>Example Domain</h1>` ✔ |
| `browser_extract` | `[{"href":"https://iana.org/domains/example","text":"Learn more"}]` ✔ |
| `browser_view_source` | 完整 `<!DOCTYPE html>…` ✔ |
| `browser_vip_dom_get_document` | 完整 DOM 树 JSON ✔ |
| `browser_vip_dom_search` | `{"searchId":"17740.0","resultCount":4}` ✔ |
| `browser_reverse_cookie_sources` | `[]` ✔ |
| `browser_dom_select` / `browser_inject` / `browser_canvas_noise` | 各有真实返回 ✔ |
| `browser_dom_set_html` | `已执行(set_html)`，**并回读 `browser_dom_inner_html` 得到 `<i>NEW</i>`** 确认真的写进去了 ✔ |

**撤回 2 个**（同步后反而更差，已恢复原异步行为）：

| 工具 | 同步后的问题 | 处置 |
|---|---|---|
| `browser_scrape` | 返回**空串** `""` —— 中央转换器 `将异步结果转为命令响应` 处理不了它的载荷形状，比原来的"回执 + poll_hint"**更差**（fastcheck 当场从 41/41 掉到 40/41） | 撤回；待转换器的载荷形状覆盖补齐后再纳入 |
| `browser_permission_spoof` | **20s 超时失败**（任务在该预算内没落地） | 撤回 |

**探针自坑（又一次）**：`browser_dom_set_html` 首轮被判"DROP"，回包是
`element not found: #mcpX` —— 那是**正确的参数校验**，因为我的探针用了页面上不存在的选择器。
换成"先注入真实元素、再对它 set_html、再回读"后 PASS。**再次印证：臂失败先怀疑探针。**

### 117.4 ★测量纪律更正：台账是**历史记录**，不是当前状态

我上一轮据台账 note 判定"`browser_dom_get_html` 只回回执（不在名单内）"。本轮核对源码发现
**它早就在名单里**（`MCP_Server.wsv` 的 `browser_get_text || browser_dom_get_html` 一行），
而我引用的那条 note 来自**第 4 轮**。⇒ 那条"在名单内"的改动是后来才加的，台账不会回溯更新。

**结论（写进纪律）**：台账是**消费视图/历史快照**，不能用来回答"现在是否同步/是否存在某行为"这类
**当前状态**问题；要么读当前源码，要么真机实测。本轮据此把"我加的名单项"逐个与源码现状对照，
发现 `browser_dom_get_html` 属**冗余重复**（已从我这行去掉，并注明上面那组已有它）。

### 117.5 两个只读子代理的静态成果

| 交付 | 关键结论 |
|---|---|
| `_audit/_menu_api_r100.md` | `类_FBrowser_菜单模式` **36 个方法**（34 个一对一映射 CEF；`_索引` 变体 8 个；**22 个 CEF 方法未封装**，含全部 `Insert*At` 与 `Get*At` → 只能追加、**无法按索引反查**）。★**关键一问结论 = B**：`菜单模式` 只能在回调期间使用，依据是 CEF 头**逐字**指名禁止 `cef_context_menu_handler.h:102-103` **"Do not keep references to \\|params\\| or \\|model\\| outside of this callback."**，且 `cef_menu_model.h:48` 要求只能在浏览器进程 UI 线程访问，而本项目 MCP 工具跑在非 UI 线程（`MCP_Stdio.wsv:324`）⇒ **方案乙（保存句柄延迟调用）不可行，只能走方案甲（预置规格、回调内一次性施加）**。命令ID 合法区间 `26500..28500`（`cef_types.h:1730-1731`，类库与 src 均无校验） |
| `_audit/_intercept_unmodify_r100.md` | `browser_intercept` 现有 **13 个 action** 与全部状态字段清单；类库 `过滤器_取消修改内容`/`过滤器_取消替换资源` 签名原文（**只收一个 `目标地址`、无索引** ⇒ 是按 URL 撤销）；当前只走"手写通道"，**VIP 添加侧全树零调用** ⇒ 只需实现手写通道删行；给出精确落点与 3 处必改的外部描述；建议**撤销不存在时幂等成功 + 如实说明**（与 `clear`/`popup_disable` 惯例一致） |

### 117.6 下一步

1. **`browser_intercept` 增 `unmodify`/`unreplace`**（子代理已给出精确落点，本机可验收）。
2. **`browser_context_menu`（方案甲）**：预置菜单规格 + 在 `浏览器_即将打开菜单` 回调内一次性施加；
   注意 16 条边界中最要紧的三条 —— 规格为空必须**跳过而不能清空**（否则右键菜单消失）、
   每次右键都是新模型故**必须重施**、命令ID 必须落在 `26500..28500`。
3. **修 `将异步结果转为命令响应` 的载荷形状覆盖**，然后把 `browser_scrape`（现回空串）
   重新纳入同步 —— 这是本轮唯一"已知可修但未修"的项。
4. 类库 `类_FBrowser_命令行` 14 项属“仅启动期生效”，需先决定是否做**启动参数通道**。
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
    if '## 117. 第100轮' in text:
        print('!! §117 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    t2 = open(REP, 'rb').read().decode('utf-8')
    assert not t2.startswith('\ufeff') and '\r' not in t2
    assert t2.count('## 117. 第100轮') == 1
    print('已追加 §117; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
