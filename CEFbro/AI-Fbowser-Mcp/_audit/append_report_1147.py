# -*- coding: utf-8 -*-
"""追加报告 §114.7（第 97 轮内追加, 不新开节号）。

§114.6 把"执行逆向CDP命令 吞参数错误"列为下一步; 本轮当场做完了, 故在其后补 §114.7。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, 'MCP工具可用性检测报告.md')

SEC = u"""
### 114.7 ★系统性根因当场修掉：7 个"取数据"调用点改走**既有同步出口**

§114.6 把它列为"下一步"，本轮直接做完了 —— 因为它的危害比"掩盖报错"更重：
**这些工具本该返回数据，却只回一句「CDP已提交」。**

台账原文（修复前，且被记为 `pass` —— 实为**假通过**）：

```
browser_reverse_runtime {action:evaluate, expression:"1+1"}
  -> {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:Runtime.evaluate"}
browser_reverse_call_fn {function_name:"parseInt"}
  -> {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:Runtime.callFunctionOn"}
browser_reverse_heap {}
  -> {"id":"1","success":true,"_async":true,"task_id":"1","message":"CDP已提交:HeapProfiler.takeHeapSnapshot"}
```

即：**问 `1+1` 等于几，工具回答"已提交"**。调用方拿不到值，只能反复换工具重试
—— 正是用户抱怨的"调用不成功 / 要试很多方法"的典型形态。

**修法：不重复造轮子。** `MCP_Server_Reverse.wsv` 里**早就有一个为这个问题而生的出口**
`执行V8CDP命令`，其自身注释原文即为：

> V8/插装类工具统一出口: 一律走同步等待, 让 CDP 侧错误(如调试器未启用)显式暴露,
> 避免执行逆向CDP命令那种"CDP已提交"的异步回执掩盖失败 —— 那类假成功会让用户
> 以为插装已生效, 实际什么都没挂上。

它已统一实现：同步等待 / "域未启用"自动补齐并重试(`auto_prepared`) / 可行动的失败分支 /
把 `result` 提取为 `cdp_result`。**这些工具只是一直没接上去。** 故改动是纯替换：

| 调用点 | CDP 方法 | 工具 |
|---|---|---|
| `Runtime.callFunctionOn` | 函数调用 | `browser_reverse_call_fn` |
| `Network.getResponseBody` | 取响应体 | `browser_reverse_websocket` action=query |
| `HeapProfiler.stopSampling` | 取采样结果 | `browser_reverse_heap` action=stop_sampling |
| `HeapProfiler.getObjectByHeapObjectId` | 取堆对象 | `browser_reverse_heap` action=get_object |
| `Runtime.getProperties` | 取属性 | `browser_reverse_runtime` action=properties |
| `Runtime.evaluate` | 求值 | `browser_reverse_runtime` action=evaluate |
| `Runtime.globalLexicalScopeNames` | 全局名字 | `browser_reverse_runtime` action=global |

**验收**（`_audit/verify_data_calls_sync.py`，**8/8**）：

| 臂 | 修复前 | 修复后 |
|---|---|---|
| `evaluate "1+1"` | `CDP已提交:Runtime.evaluate` | `{"result":{"type":"number","value":2,"description":"2"}}` ✔ |
| `evaluate return_by_value=false` | 无 | 真实 `objectId` ✔ |
| `properties {object_id:…}` | 无 | 真实属性数组（`a`/`b`/`two`）✔ |
| `global` | 无 | `{"names":[…]}` ✔ |
| `call_fn parseInt ["42"]` | `CDP已提交` | `{"value":42}` ✔ |
| `websocket query`（无效 id） | **假成功** | 诚实报错 `No resource with given identifier found` ✔ |
| `heap stop_sampling`（未 start） | **假成功** | 诚实报错 `V8 sampling heap profiler was not started.` ✔ |
| `heap get_object`（坏 id） | **假成功** | 诚实报错 `Object is not available` ✔ |

**探针自坑（又一次）**：`call_fn` 首轮实测返回 `NaN` 而非 `42`。当场先怀疑探针 —— 果然：
该工具有 `arguments`（JSON 数组）与 `args`（**单文本**参数，会自动再包一层单元素数组）两个参数，
我传了 `args='["42"]'`，于是实际执行 `parseInt('["42"]')` → `NaN`。
改用 `arguments='["42"]'` 后得 `42`。

#### 仍保留异步的 8 个调用点：已逐个证明"内核接受其参数"

剩下 8 处是"装模式 / 开始"语义（`setXHRBreakpoint`/`setEventListenerBreakpoint`/
`setInstrumentationBreakpoint`/`setBreakpointOnFunctionCall`/`addScriptToEvaluateOnNewDocument`/
`Network.enable`/`takeHeapSnapshot`/`startSampling`）。**不一刀切**：`takeHeapSnapshot` 在堆大时
可能超过同步预算(15s)，改同步反而会制造**假超时**。
但"保留异步"会让参数错误继续被吞，所以逐条向内核求证（`_audit/probe_remaining_async_params.py`）：

```
实测 8 项, 被内核拒绝 0 项
  接受   Network.enable / DOMDebugger.setXHRBreakpoint / setEventListenerBreakpoint
  接受   DOMDebugger.setInstrumentationBreakpoint / HeapProfiler.takeHeapSnapshot / startSampling
  返回数据 Page.addScriptToEvaluateOnNewDocument -> {"identifier":"1"}
  返回数据 Debugger.setBreakpointOnFunctionCall   -> {"breakpointId":"7:1"}
```

⇒ **这 8 处没有被静默吞掉的参数错误**（且顺带确证 `DOMDebugger` 侧三条 `remove*` 清理命令本机可用）。
至此 **15 个逆向 CDP 调用点全部有了定论**：7 处改同步并验证带回数据、8 处证明参数被接受。

#### 台账更正

上述 4 个工具（`browser_reverse_runtime`/`call_fn`/`websocket`/`heap`）原先记的 `pass`
是**基于 `_async` 回执的假通过**，已重测并改记为带真实 `cdp_result` 的 pass（第 195–198 轮）。
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
    if '### 114.7' in text:
        print('!! §114.7 已存在, 中止')
        return 1
    out = text + SEC
    open(REP, 'wb').write(out.encode('utf-8'))
    chk = open(REP, 'rb').read()
    assert not chk.startswith(b'\xef\xbb\xbf')
    t2 = chk.decode('utf-8')
    assert '\r' not in t2
    assert t2.count('### 114.7') == 1
    print('已追加 §114.7; 行数 %d -> %d' % (text.count('\n') + 1, t2.count('\n') + 1))
    print('自检: 无 BOM / 无 CR / 唯一')
    return 0


sys.exit(main())
