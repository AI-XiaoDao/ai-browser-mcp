# -*- coding: utf-8 -*-
r"""第127轮收尾: 报告 ## 147 + `_gap_verified.md` 第四节补"已修/遗留"进展 + 记录一条**补丁陷阱**。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')

SECTION = '''
## 147. 第127轮：`browser_dom_query.index` 静默错答案修复 + 9 项 schema 可发现性补齐（含一条补丁陷阱）

### 147.1 最严重的一类缺陷：**静默错答案**
只读审计 A 组 Top 15 第 14 条指出 `browser_dom_query` 的 `index` "静默失效"。源码核实确认：
schema 里**声明了** `index`，而实现（`MCP_Server_Core.wsv`）两条 JS 路径都写死
`document.querySelector(...)`（永远第一个匹配），原生回退路径也把索引写死 0
（`取元素属性 (selector, 0, ...)` / `取元素内容 (selector, 0, ...)`）。
⇒ 调用方传 `index=2` 会**静默拿到第 1 个**元素的值。**这比报错危险得多**：错误会让人重试，错答案会被当成事实用下去。

修法与验收（`_audit/verify_dom_query_index.py` **12/12**，预言机 = 页面上自己注入的三个元素 A/B/C 与属性 k0/k1/k2）：
- 两条 JS 路径改用 `querySelectorAll(sel)[index]`；原生回退路径如实透传索引；
- **越界**不再是"悄悄给第一个"，而是可行动失败：`index 越界: 请求 index=5, 但该选择器**实际只有 3 个匹配** | 索引从 0 开始; 去掉 index 参数即取第 1 个匹配`；
- **负索引**明确拒绝；省略 `index` 仍是第 1 个匹配（回归通过）；
- attribute 模式同样按索引取值（`index=2` → `k2`）。

### 147.2 又一批"实现真读却代理看不到"的参数（9 项，逐条在源码里核实过读取点）
| 参数 | 实现读取点 | 影响 |
|------|-----------|------|
| `browser_dom_set_value.allow_empty` | `MCP_Server_Core.wsv:2011` | 原报错文案**指向一个未声明的参数**（"如需清空请设置 allow_empty:1"）⇒ 照做也无法通过，属**死路**；现已声明 |
| `browser_network.auto_enable` | `MCP_Server_Core.wsv:3511` | 代理不知道能"只查不改开关" |
| `browser_inject.inject_id` | `MCP_Server_Core.wsv:3395 / 3412` | 无法撤销/替换同一次注入 |
| `browser_reverse_hook.url_pattern` | `MCP_Server_Core.wsv:7598` | 无法限定只 Hook 某 URL（xhr/ws 场景） |
| `browser_view_source.max_chars` | `MCP_Server_Core.wsv:4224` | 该工具原本**连 schema 都没有**，现补齐 |
| `browser_touch_press/_move/_release.kernel` | 三件套描述都承诺 `kernel:true` | 同族 `mouse_*` 都声明了 kernel，家族内自相矛盾 |

另修正两处**描述与实现相反**：
- `browser_view_source`：旧描述写"在新标签打开源码视图(view-source:)"，而实现刻意**不调用**类库 `源码视图()`
  （会弹记事本阻塞控制台）—— 只回源码文本；已按实现改写并说明等价工具；
- `browser_file_dialog`：旧描述"打开文件对话框"，实现**不弹真实系统对话框**（无人值守场景弹窗会永久阻塞），
  只登记"若页面触发文件选择则如何响应"；已按实现改写。

验收：`_audit/verify_missing_params.py` **12/12**（声明层 tools/list + 行为层：`dom_set_value{selector}` 的拒绝文案
现在指向一个**确实已声明**的参数）。

### 147.3 本轮踩到并记录的一条**补丁陷阱**（值得后续每轮记住）
第一批改动把 touch 三件套的 schema 写成 `双XY_Schema文本 ("x","y","X","Y") + "," + 属性项JSON ("kernel", ...)`。
编译通过、服务能起、快检也全过 —— 但验收脚本抓出 **3 条 FAIL**：运行时 `properties` 仍只有 `x/y`。
根因：`双XY_Schema文本`（`MCP_Server.wsv:11799`）返回的是**整段** `"inputSchema":{...}` 字符串（自带 `}` 与 `required`），
**在其后拼接**属性片段得到的是**非法 JSON**，MCP 层于是把它整段丢掉 —— 即"改了但没生效"。
正确写法是整段替换为 `多属性Schema文本 (属性项JSON(...)+..., "\\"x\\",\\"y\\"")`。
⇒ 教训：**任何改 schema 的补丁都必须用运行时 `tools/list` 复核参数是否真的出现**（编译与快检都抓不到这类问题）。

### 147.4 状态
工具 **322**；台账 **322/322 已测 = 319 通过 / 3 刻意设计**；快检 **56/56**；编译 **0 警告**；卫生扫描**全零**。
本轮验收：`verify_dom_query_index.py` **12/12**、`verify_missing_params.py` **12/12**、
`verify_schema_audit_fixes.py` **17/17**（无回归）、`verify_urlreq_upload.py` **12/12**（上轮成果未回退）。
剩余（`_audit/_gap_verified.md` 第四节）：`browser_fingerprint` 的 19 个维度参数、debugger 家族的 CDP 原生别名、
`browser_execute_js` 的 `file`/`code_base64`、`workflow_run` 的 steps 字段表、`reverse_websocket query` 语义、
`kernel_scheme`/`kernel_ipc_clear` 的静默成功守卫、**幽灵工具 `browser_debugger_pause`**、公共层参数声明统一。
'''


def main():
    raw = open(REPORT, 'rb').read()
    text = raw.decode('utf-8')
    if '## 147.' in text:
        text = text[:text.index('## 147.')].rstrip('\n') + '\n'
    out = text.rstrip('\n') + '\n' + SECTION
    io.open(REPORT, 'w', encoding='utf-8', newline='\n').write(out)
    print('报告: -> %d 字符' % len(out))
    g = io.open(GAP, encoding='utf-8').read()
    marker = '### 遗留（A 组 Top 15 等，均有 `file:line` 证据，下一轮按序实施）'
    add = (marker + '\n> **第127轮进展**：已修 `browser_dom_query.index`（静默错答案）、`dom_set_value.allow_empty`（死路）、'
           '`network.auto_enable`、`inject.inject_id`、`reverse_hook.url_pattern`、`view_source`（描述+max_chars）、'
           '`file_dialog`（描述）、touch 三件套 `kernel`；并记录一条陷阱：**改 schema 后必须用 tools/list 复核**，'
           '因为"在 helper 生成的整段 schema 后拼接"会产出非法 JSON 而被整段丢弃（编译与快检都发现不了）。')
    if marker in g and '第127轮进展' not in g:
        g = g.replace(marker, add, 1)
        io.open(GAP, 'w', encoding='utf-8', newline='\n').write(g)
        print('_gap_verified.md: 已补第127轮进展')
    else:
        print('_gap_verified.md: 跳过(已有或锚点未命中)')


main()
