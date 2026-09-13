# -*- coding: utf-8 -*-
r"""追加报告章节: ## 143. 第125轮 —— 响应体零前置化 / mcp_result 契约实测 / 三个"探针假目标"归零。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SECTION = '''
## 143. 第125轮：`browser_network_body` 零前置化、`mcp_result` 契约实测、三个"探针假目标"归零

### 143.1 起点：台账里那条 TARGET 失败，其实是**前置缺失**
`browser_network_body` 长期以
`Network.getResponseBody 失败: No resource with given identifier found`（TARGET）记账。静态核实后发现：
- 该工具**只收 `request_id`**；
- 而项目里**没有任何工具回传 CDP requestId** —— `browser_network list` 读的是 CEF 层网络日志
  （`记录网络请求_详细` 只写 method/url/headers/post_body），`browser_get_requests` 同样不含；
- 于是调用方只能"手工订阅 → 抓一条事件 → 手抄 id → 尽快调用"，否则响应体被回收。
这正是目标 A 线要清零的**前置缺失类失败**，不是功能缺陷。

### 143.2 改法：把两步前置做进工具（复用既有件，不重复造轮子）
1. 新增 `确保网络CDP捕获 ()` —— 复用既有 `MCP_内核分派.分派_CDP监控 {action:add, methods:Network.*}`
   （它自带去重、置启用、按前缀自动 `Network.enable`，并经 `auto_prepared` 如实上报）；
2. 新增 `查找CDP请求ID (目标URL)` —— 从既有 `查询事件日志("cdp_monitor","Network.requestWillBeSent",0,300)`
   里解析 `requestId` / `request.url`（数组解析复用既有 `取JSON数组自文本`）；给 url 时先精确、再退化为包含匹配；
   不给 url 时取**最新一条并跳过 `favicon.ico`**（实测浏览器自动请求的 favicon 会在文档之后发出，会把默认值带偏）；
3. `browser_network_body` 新增 `url` / `wait_ms`：不传 `request_id` 时自动解析，给了 url 但尚未出现时在
   `wait_ms`（默认 2000，上限 15000）内轮询等待；解析来源经 `resolve_note` **如实回传**；
4. 命不中时给**可行动**失败：点明"响应体只能对**本 CDP 会话内、捕获开启之后**发生的请求取回"+ 已捕获条数 +
   两条替代路径，而不是原来那句 `request_id 缺少参数`；
5. `browser_network` 新增 `action=body`（直接转交同一分派，零重复实现），其 schema 同时声明
   `request_id/url/wait_ms/limit`，避免"参数存在但代理看不到"。

### 143.3 验收（`_audit/verify_network_body.py`，16/16 通过，全部用**本机自建 HTTP 服务**当预言机）
| 用例 | 结果 |
|------|------|
| 未捕获时不传 id | 自动开启 Network 域+捕获（`auto_prepared` 上报），并给出可行动失败（含"捕获开启之后"与已捕获条数） |
| 捕获后按 url 取 | 成功，`resolve_note` 给出解析来源；**响应体与本地服务载荷逐字一致**（`'{"hello":"world","n":42,...}'`，52/52 字节） |
| bare 调用 | 成功且**没有**把 `favicon.ico` 当默认；响应体与解析出的 URL 载荷一致 |
| `browser_network {action:body}` | 等价可用，内容一致 |
| 不存在的 request_id / 格式非法 id | 仍给出可行动错误 / 仍被快速拒绝（原有守卫语义保留） |
| `browser_network action=list` | 未被破坏（仍含 `network_logs`） |

### 143.4 顺带实测确认：`mcp_result` 的 `request_id` 到底是什么
台账里 `mcp_result` 一直记着 `未找到任务结果: mcp_probe` —— 那是**探针用了个假 id**。本轮用受控实验
（`_audit/probe_mcp_result_contract.py`）把契约钉死：
- 用**独特 JSON-RPC id** 调一个可辨识的工具（`id=4242` 调 `browser_execute_js {"code":"'MARKER-4242'"}`），
  随后 `mcp_result {request_id:"4242"}` **取回了那次调用的结果**（`MARKER-4242`）；
- 负对照：从未用过的 `999042` → 明确报"未找到任务结果"；
- 等待型工具（`browser_wait`）的回包里另有一个内部 `task_id`（形如 `task_64630937_41850_20`），
  **两个键都能取**，语义不同：命令ID = 那次调用的即时结果；内部 task_id = 该等待任务的实时/最终状态。
⇒ 已把这段契约写进 `mcp_result` 的工具描述与参数说明（此前只写了"任务ID或JSON-RPC id"六个字，
调用方无从判断该传哪个）。**注意**：这不是新增行为，只是把既有行为**说清楚**。

### 143.5 三个"探针假目标"归零（台账 315/6 → 318/3）
| 工具 | 原失败 | 真实成因 | 处理 |
|------|--------|----------|------|
| `browser_network_body` | TARGET | **功能前置缺失** | 已实现零前置解析（见 143.2），重测 **pass 0.03s** |
| `mcp_result` | TARGET | **探针用假 id** | `DYNAMIC_ARGS` 改为运行期"独特 id 真调一次再取"，重测 **pass 0.02s** |
| `browser_set_window_style` | PARAM | **探针传了非法 `type=1`**（白名单只收 -16/-20/-12） | `DYNAMIC_ARGS` 改为**读回当前 GWL_STYLE 原值写回**（等价一次无副作用的真调用），重测 **pass 0.02s** |

剩余 3 条非 pass 全部是**刻意设计**且已记录：`browser_reverse_instrument_script` / `browser_vip_enable_js_env`
（需要显式确认的破坏性操作，实测会阻塞本会话 JS 通道）、`browser_vip_mouse_wheel`（缺 `delta_y` 的参数守卫，
属"参数非法"这一可接受类别）。

### 143.6 可发现性补丁（"能回读但不可发现"）
`browser_event` 的描述**漏列了菜单事件族**，而服务端自己的失败文案却列了 —— 即"记录得到、却没人知道能查"。
本轮按其**源码里的真实事件名**补进描述：`context_menu_opening/context_menu_run/context_menu_command/context_menu_dismissed`
与 `quick_menu_command/quick_menu_dismissed`，并注明这两族需先 `browser_collect action=event_menu_enable /
event_quickmenu_enable`（或 `browser_kernel_events_all action=enable`）才会入库。

### 143.7 状态
工具 **321**；台账 **321/321 已测 = 318 通过 / 3 刻意设计**；快检 **56/56**；`verify_network_body.py` **16/16**；
编译 0 警告。新增/修改文件：`src/MCP_Server.wsv`（两个复用件 + 3 处 schema/描述）、`src/MCP_Server_Core.wsv`
（`browser_network_body` 分支 + `action=body` 入口）、`_audit/mass_probe.py`（`probe_call` 支持指定 JSON-RPC id +
3 条运行期真值）、`_audit/verify_network_body.py`、`_audit/probe_mcp_result_contract.py`、
`_audit/probe_async_task_id.py`。
'''

# 注: 本字面量内不含三个连续双引号


def main():
    raw = open(REPORT, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), '报告带 BOM'
    assert b'\r\n' not in raw, '报告含 CRLF'
    text = raw.decode('utf-8')
    assert '## 142.' in text, '章节 142 应已存在'
    if '## 143.' in text:
        assert '--replace' in sys.argv, '章节 143 已存在(要覆盖请加 --replace)'
        text = text[:text.index('## 143.')].rstrip('\n') + '\n'
        print('已截去旧的第 143 章')
    out = text.rstrip('\n') + '\n' + SECTION
    if '--apply' in sys.argv:
        with io.open(REPORT, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('已写入: %d -> %d 字符' % (len(raw.decode('utf-8')), len(out)))
    else:
        print('[dry-run] 将写入 %d 字符' % len(SECTION))


main()
