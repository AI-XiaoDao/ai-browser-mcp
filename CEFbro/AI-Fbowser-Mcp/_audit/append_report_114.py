# -*- coding: utf-8 -*-
"""追加报告第 114 节（第 97 轮）。

纪律(项目既定): 断言无 BOM、不产生 CRLF、无重复节号。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
---

## 114. 第97轮：UA-CH 四字段回读验收、CDP 参数名审计落地（2 个真缺陷）、台账收官 313/313

### 114.1 UA-CH 四字段：能力落地 + **独立回读**验证

在 `browser_fingerprint_ua` 上补齐 4 个 UA-CH 字段（`MCP_Server_VIP.wsv` 调
`置PlatformVersion`/`置FullVersion`/`置Brands`/`置FullVersionList`；`MCP_Server.wsv` 新增
`解析双文本表` 把 `"Chromium:120,Google Chrome:120"` 解析成 `FBrowser_双文本数组`；schema 增 4 参数）。

**验证不靠工具自报**，而是直接问页面自己（`navigator.userAgentData.getHighEntropyValues()`）：

| 字段 | 设置前（基线） | 设置后 | 我设的值 | 结论 |
|---|---|---|---|---|
| `brands`（低熵） | Chromium:135、Not-A.Brand:8 | Chromium:120、Google Chrome:120 | Chromium:120,Google Chrome:120 | ✔ 一致 |
| `fullVersionList`（高熵） | Chromium:135.0.7049.115、Not-A.Brand:8.0.0.0 | Chromium:120.0.6099.109、Google Chrome:120.0.6099.109 | 同左 | ✔ 一致 |
| `platformVersion`（高熵） | 19.0.0 | 15.0.0 | 15.0.0 | ✔ 一致 |
| `fullVersion`（高熵） | 135.0.7049.115 | 120.0.6099.109 | 120.0.6099.109 | ✔ 一致 |

基线**本就不同**（135 → 120），故这是"真的改了"，不是同值巧合。四项全部命中（`_audit/verify_uach_fields.py`）。

**探针自坑（值得记）**：`platformVersion`/`fullVersion`/`fullVersionList` 是**高熵**字段，
在低熵对象 `navigator.userAgentData` 上是 `undefined`，而 `JSON.stringify` 会把 `undefined` 的键
**直接丢掉**。第一版探针读 `d.platformVersion` → 回包里根本没有这些键 → 三项全 FAIL。
若不当场怀疑探针，就会把"功能完全正常"误判成"功能没生效"。
改用 `getHighEntropyValues()` 后全 PASS —— 又一次印证"**对照臂失败时先怀疑探针**"。

**顺带终结一个长期未知项**：基线读数里内核自报
`Chromium 135.0.7049.115` / `platformVersion 19.0.0`，即**内核确为 Chromium 135**。
因此"`Debugger.setReturnValue` 要旧名 `newValue`、`setInstrumentationBreakpoint` 要
`instrumentation`"**不是"旧内核"**，而是**这个 CEF 构建的定制**。

### 114.2 CDP 参数名审计：总闸探针 + 逐条实测，**推翻 4/5 条静态判定**

先跑"总闸"探针：`Debugger.setSkipAllPauses {"skip":true,"__mcp_probe_unknown_field":1}` → `{}`
⇒ **本机忽略未知字段** ⇒ 凡"多传了一个 PDL 里没有的字段"这一类风险**整体不成立**。

| 条目 | 静态判定 | **实测结论** | 内核原文（节选） |
|---|---|---|---|
| `Network.setRequestInterception` | 方法可能已不存在 / 空参必失败 | **方法存在，但两种形状都发错了** → 真缺陷，已修 | `{}` → `params.patterns - mandatory field missing`；`{"patterns":["*"]}` → `params.patterns - CBOR: map start expected` |
| `Page.addScriptToEvaluateOnNewDocument` | `runImmediately` 是新字段，可能被拒 → preload 100% 失效 | **两臂都接受**，安全 | `{"source":"void 0","runImmediately":true}` → `{"identifier":"2"}` |
| `DOMDebugger.setInstrumentationBreakpoint` | 疑同族改名，应为 `instrumentation` | **恰好相反**：要的就是 `eventName`，旧代码**本来就对** | `{"instrumentation":…}` → `params.eventName - mandatory field missing` |
| `Profiler.setSamplingInterval` | `maxDepth` 非该命令字段 | 字段名**无误**；但顺带查出**更严重的真缺陷**（漏调 `Profiler.start`） | `{"interval":100}` → `{}`；`{"interval":100,"maxDepth":32}` → `{}` |

**教训**：风险**不能按域、更不能按版本批量推断** —— 必须逐命令实测。
（本轮 A1 是"真坏了但机理不同"、A4 是"本来就对"，一正一反即反例。）

更正已同步回交付物 `_audit/_cdp_param_compat.md` **§6**（若只在报告里更正、
下一轮读该文档的人会照着错清单去"修"本来正确的代码）。

### 114.3 真缺陷①：`browser_reverse_network_intercept` 的 enable **两条路径 100% 失效**

`enable` 无论传不传 `url_pattern`，发给内核的 params 都会被拒：

| 情形 | 实际发出 | 内核返回 |
|---|---|---|
| 传了 `url_pattern` | `{"patterns":["<字符串>"]}` | `Failed to deserialize params.patterns - CBOR: map start expected at position 25` |
| 没传 `url_pattern` | `{}` | `Failed to deserialize params.patterns - BINDINGS: mandatory field missing at position 8` |

即 `patterns` 必须是**对象数组**（元素为 `RequestPattern`）。而该工具走
`执行逆向CDP命令`，发完命令立刻回 `{"success":true,"_async":true,...}` **不等 CDP 响应**
⇒ **内核在报错，工具在报成功**，所以这个缺陷长期不可见。

**修复**：① 纯文本拼接对象数组（避开项目实测的"yyjson 嵌套 `加入数组成员` → 0xC0000005"）；
② 改用 `执行CDP并同步等待`，把内核真实结果/错误透出；③ 缺 `url_pattern` 时**明确失败**并给出下一步。
**刻意不默认「拦截全部」**：本项目**没有** `Network.continueInterceptedRequest` 放行通道，
拦下的请求无人放行会把页面**整体挂死**，比直接报错更难恢复。

**验收**（`_audit/verify_network_intercept.py`，4/4）：

| 臂 | 做什么 | 期望 | 实测 |
|---|---|---|---|
| A 守卫 | `enable` 不传 `url_pattern` | 明确失败 | `enable 需要 url_pattern: …` ✔ |
| B 非匹配 | `enable *example.org*` 后导航 example.com | 照常成功 | `href = ?nomatch=1` ✔（命令真被接受且未误伤流量） |
| C 匹配 | `enable *example.com*` 后导航新 URL | **被拦** | 导航 `TIMEOUT`，`href` 未提交到 `?blocked=1` ✔ |
| D 复位 | `disable` 后导航 | 恢复 | `href = ?after=1`、页面存活 ✔ |

C 臂是关键：它区分了"命令被内核接受"与"拦截真的在工作"。

### 114.4 真缺陷②：`browser_reverse_profile` **采样从未开始，profile 被丢弃**

内核实测（全新进程）：

| 调用序列 | 返回 |
|---|---|
| `Profiler.stop`（未 start） | `{"code":-32000,"message":"No recording profiles found"}` |
| `Profiler.enable` → `Profiler.stop` | **同上** ← `enable` 不等于 `start`，这正是旧代码的漏洞 |
| `Profiler.start` → `Profiler.stop` | `{"profile":{"nodes":[{...,"callFrame":{...}}]}}` 真实数据 |

旧代码 `start`/`start_precise` **只调 `Profiler.enable`**，于是：启动"成功"但没采样；
`stop` 的内核错误被 `_async` 回执吞掉、profile 也没回传 —— 整个剖析族"看似成功、拿不到数据"。

**修复**：补齐 `Profiler.start`（顺序：`setSamplingInterval` → `enable` → `start`，采样间隔必须先于 start）；
全部改同步；`stop` 回传真实 `profile_result`（超 20 万字符截断并**明确标注** `profile_truncated`/`profile_total_chars`）；
去掉不属于该命令的 `maxDepth`。

**验收**（`_audit/verify_profiler_lifecycle.py`，4/4）：A 未 start 时 `stop` 明确失败并说明原因；
B `start`→烧 CPU→`stop` **取回 2992 字符真实 profile（含 nodes/callFrame）**；C `start_precise` 路径同样取回；
D `query` 有真实 coverage 返回。

### 114.5 台账收官：**313/313，未测 0**

6 个被台账列为"跳过(致命/污染全局)"的工具（`browser_close`/`close_try`/`shutdown`/`set_s5_proxy`/
`set_preference`/`reverse_patch`）此前**永远进不了台账** —— 因为 `tool_ledger.py` 的 CLI 对
`MP.LETHAL` 直接 `continue`。它们其实早在 §103.1 就做过**不伤主实例**的受控实测且全部存活，
本轮按同一 record schema 补记（`_audit/record_lethal_manual.py`，把**测法**与**原文**一并写入 note）。

```
工具总数 313 | 已测 313 | 未测 0
通过 306 | 失败 7 | 其中把实例卡死 0
失败性质 PARAM 2 / TARGET 2 / OTHER 2 / GUARD 1
```

7 条失败**逐条核实均非产品缺陷**：

| 工具 | 性质 | 核实结论 |
|---|---|---|
| `browser_find_by_hwnd` | TARGET | 探针填 `hwnd=1`（无效句柄），工具如实拒绝并给出取得方式 → **探针填充值问题** |
| `browser_network_body` | PARAM | 探针填 `request_id=mcp_probe`，工具如实拒绝并说明合法形状（数字串）→ **探针填充值问题** |
| `browser_set_window_style` | PARAM | 探针填 `type=1`，合法值为 `-16/-20/-12` → **探针填充值问题** |
| `mcp_result` | TARGET | 探针填不存在的 `request_id`（该工具本就要真实异步任务号）→ **探针填充值问题** |
| `browser_reverse_instrument_script` | OTHER | `install` 需 `confirm:true` —— 本轮**刻意加的门槛**（实测装后阻塞 JS 通道）→ 设计如此 |
| `browser_vip_enable_js_env` | OTHER | 同上需 `confirm`（实测会破坏本会话 JS 通道）→ 设计如此 |
| `browser_vip_mouse_wheel` | GUARD | 必须给 `delta_y`/`delta_x`（省略会滚动 0 像素却报成功）→ 设计如此 |

即 **PREREQ = 0、CAPABILITY = 0、把实例卡死 = 0** 三项关键指标保持干净。

### 114.6 本轮遗留 / 下一步

- **系统性根因（下一步优先）**：`执行逆向CDP命令` 发完命令不等响应就回 `_async` 成功，
  导致**参数错也报 success**。走它的工具（profile/dom_breakpoint/cdp_hook/call_fn/preload/
  websocket/heap/runtime/network_intercept）在台账里的 `pass` **只是"CDP已提交"回执**，
  不能当"参数被接受"的证据。计划把"内核会立即返回结果"的参数设置类调用逐一改同步。
- 上表 4 条**探针伪失败**：补合法覆盖值，使其从"只测到守卫"变成真测量。
"""


def main():
    data = open(REP, 'rb').read()
    if data.startswith(b'\xef\xbb\xbf'):
        print('!! 报告有 BOM, 中止')
        return 1
    text = data.decode('utf-8')
    crlf = text.count('\r\n')
    print('原报告: %d 行, CRLF=%d, LF=%d' % (text.count('\n') + 1, crlf,
                                            text.count('\n') - crlf))
    if crlf:
        print('!! 报告含 CRLF, 为避免混合行尾中止')
        return 1
    if '## 114. 第97轮' in text:
        print('!! 第 114 节已存在, 中止')
        return 1
    body = SEC if SEC.startswith('\n') else '\n' + SEC
    out = text + body
    open(REP, 'wb').write(out.encode('utf-8'))
    print('已追加第 114 节; 新行数 %d' % (out.count('\n') + 1))
    # 回读自检
    chk = open(REP, 'rb').read()
    assert not chk.startswith(b'\xef\xbb\xbf')
    t2 = chk.decode('utf-8')
    assert '\r' not in t2, '写入后出现 CR'
    assert t2.count('## 114. 第97轮') == 1
    print('自检通过: 无 BOM / 无 CR / 节号唯一')
    return 0


sys.exit(main())
