# -*- coding: utf-8 -*-
r"""第126轮收尾: ①`_gap_verified.md` 标记缺口#3(上传进度)已完成;
②追加报告 ## 146; ③docs FAQ 补"MCP HTTP 通道 ~1MB arguments 上限"一行。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAP = os.path.join(ROOT, '_audit', '_gap_verified.md')
REPORT = os.path.join(ROOT, 'MCP工具可用性检测报告.md')
DOCS = os.path.join(ROOT, 'docs', 'MCP工具配置说明书.md')

GAP_OLD = '| 3 | `类_FBrowser_URL请求事件.上传进度`（FBroEventControl.wsv:2314） | `_gap_vip_events.md` 真缺口#2 | ⏳ 待做（低成本） | 对照 `MCP_Callbacks.wsv` 下载进度覆盖即可；不碰 CDP、无需重启；对"上传大 body 时判断进度"有用 |'
GAP_NEW = '| 3 | `类_FBrowser_URL请求事件.上传进度`（FBroEventControl.wsv:2314） | `_gap_vip_events.md` 真缺口#2 | ✅ **已实现并运行期验收** | 新增 `上传进度` 覆盖 → 事件 `urlreq_upload`（节流口径与下载进度一致、独立游标）；**零前置**：有请求体时自动置 `UR_FLAG_REPORT_UPLOAD_PROGRESS`（类库原文约束：不置则该回调永不触发）+ 自动开 urlreq 监控，均经 `auto_prepared` 上报；验收 `_audit/verify_urlreq_upload.py` **12/12**：3MB 文件上传 → 服务端实收 3,145,728 字节（预言机一）+ 事件 total=3,145,728（预言机二）+ GET 负对照无事件 + `body_file` 不存在时给可行动错误 |'

REPORT_SECTION = '''
## 146. 第126轮：MCP HTTP 通道的 1MB 参数墙（实测定位 + 无法拦截的证明 + 文件路径替代）+ 上传进度运行期验收

### 146.1 起点：一个"没有响应"的失败
上一轮给 `browser_create_url_request` 做上传进度验收时，用 3MB body 调工具，客户端收到的是
`RemoteDisconnected: Remote end closed connection without response` —— **没有错误码、没有正文**。
对 AI 代理而言这是最坏的失败形态（只能重试或换方法），正是目标 A 线要消灭的体验。

### 146.2 实测定位（`_audit/probe_arg_size_limit.py`，逐步加大入参）
| 入参填充 | 结果 |
|---|---|
| 0.06 / 0.25 / 0.50 / 0.59 / 0.68 / 0.78 / 0.88 / 0.96 / 0.98 / 0.99 MB | 成功 |
| 1020 KB（1,044,480 字节） | **成功** |
| 1024 KB（1,048,576 字节） | **连接被内核直接关闭，无任何响应** |
失败后实例仍健康（健康探针最慢 0.04s）⇒ 是**传输层容量边界**，不是卡死；本项目自身上限是 50MB
（`读取HTTP_POST体` 里的 `WS最大消息字节`），故这道墙在**类库/CEF 侧**（FBroLib 里无对应可调参数）。

### 146.3 关键否定结论：服务端**无法**把它变成可行动错误
第一版做法是在 `POST /mcp` 读到正文前按 `Content-Length` 拦下并回标准 JSON-RPC 错误。加完再测 1.5MB：
**仍然**是 `RemoteDisconnected` —— 说明那道墙**早于** `收到HTTP请求` 事件，处理器里的检查根本不会被执行；
而实测 1020KB 是**能通过**的，若按 100 万字节安全线拒绝，就会把 1,000,001~1,048,575 这段**本来可用**的请求
误判为超限 ⇒ 净损失。故该守卫已**回退**（`_audit/_revert_http_body_guard.py`，同时删掉随之无用的常量），
并把"实测事实 + 替代方案"写进 docs 与工具文案。

### 146.4 有效替代：大参数改走**文件路径**（并顺带完成上传进度的运行期验收）
类库恰好提供 `类_FBrowser_POST元素.置数据_文件`（FBroLib.wsv:2602 → CEF `SetToFile`），故
`browser_create_url_request` 新增 **`body_file`**：请求体**从文件直传**，既不进 arguments（绕开 1MB 墙），
也不读进内存；文件不存在时给**可行动**错误（点明 1MB 墙与绝对路径要求）。
`_audit/verify_urlreq_upload.py` **12/12**（两个独立预言机）：
- 3MB 文件上传 → 本机 HTTP 服务**实收 3,145,728 字节**；
- 事件 `urlreq_upload` 入库且 `total` = 3,145,728、`current` 单调不减不越界；
- GET（无体）负对照：**不产生**上传进度事件（标志只对有体的请求置位）；
- 全程**不手工开任何监控开关** ⇒ 零前置（自动置标志 + 自动开监控）成立。

### 146.5 验收脚本反查出的两个真缺陷（异步路径）
1. **`命令成功_异步` 丢弃 `auto_prepared`**：零前置的"如实上报"在**所有异步工具**上失效 —— 实测
   `browser_create_url_request` 自动置上传进度标志并自动开 urlreq 监控，可异步回包里一句说明都没有。
   已与 `命令成功/命令失败` 对齐（消费一次并附上）。
2. **JSON 回包后追加裸文本**：异步工具会得到 `{...json...}\\n\\n[task_id: xxx]`，整段不再是合法 JSON
   （实测：客户端 `json.loads` 直接失败，我的验收脚本第一版因此把 `task_id` 解析成 None，出现 3 条**假失败**）。
   JSON 里本来就有 `task_id` 字段，故改为**仅在非 JSON 内容**时才追加。

### 146.6 状态
工具 **322**；台账 **322/322 已测 = 319 通过 / 3 刻意设计**；快检 **56/56**；编译 0 警告；
本轮验收：`verify_urlreq_upload.py` **12/12**、`verify_http_body_guard.py` 用于**证明守卫无效**（4/9，失败项即证据）、
`verify_frames_parent.py` **11/11**、`verify_schema_audit_fixes.py` **17/17**。
类库缺口台账（`_audit/_gap_verified.md`）中 #1/#2/#3/#4 均已落地并验收。
'''

DOCS_ROW_ANCHOR = '| 需要**提交式跳转**（POST / 带签名头跳转） |'
DOCS_ROW_NEW = ('| 大参数报“连接被关闭 / 无响应” | **实测限制**：MCP **HTTP** 通道在 arguments 约 1MB 处会被内核直接断开连接'
                '（1020KB 通过、1024KB 失败；且**没有错误码**）。该墙在类库/CEF 侧、早于服务端事件处理，**服务端无法拦截**。'
                '可行做法：①大请求体用 `browser_create_url_request {body_file:"D:\\\\path\\\\big.bin"}`（文件直传，不进 arguments）'
                ' ②改用 WebSocket（`ws://host:port/mcp`，上限 50MB）或 stdio 通道（`mcp_bridge.js`）|')


def main():
    g = io.open(GAP, encoding='utf-8').read()
    if GAP_OLD in g:
        g = g.replace(GAP_OLD, GAP_NEW, 1)
        io.open(GAP, 'w', encoding='utf-8', newline='\n').write(g)
        print('_gap_verified.md: 缺口#3 标记为已完成')
    else:
        print('_gap_verified.md: 缺口#3 行未匹配(可能已更新)')
    raw = open(REPORT, 'rb').read()
    text = raw.decode('utf-8')
    if '## 146.' in text:
        text = text[:text.index('## 146.')].rstrip('\n') + '\n'
    out = text.rstrip('\n') + '\n' + REPORT_SECTION
    io.open(REPORT, 'w', encoding='utf-8', newline='\n').write(out)
    print('报告: -> %d 字符' % len(out))
    d = io.open(DOCS, encoding='utf-8').read()
    if DOCS_ROW_ANCHOR in d and 'body_file' not in d:
        d = d.replace(DOCS_ROW_ANCHOR, DOCS_ROW_NEW + '\n' + DOCS_ROW_ANCHOR, 1)
        io.open(DOCS, 'w', encoding='utf-8', newline='\n').write(d)
        print('docs FAQ: 已补 1MB 墙与替代通道一行')
    else:
        print('docs FAQ: 已存在或锚点未命中')


main()
