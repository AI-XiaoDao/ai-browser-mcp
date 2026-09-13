# -*- coding: utf-8 -*-
"""把 6 个"只回 CDP已提交、无任何提示"的工具改为同步返回真实结果/诚实报错。

依据(第98轮台账分类): 这 6 个工具的 pass 证据只是 {"_async":true,"message":"CDP已提交:X"},
既没有结果、也没有 poll_hint —— 调用方**根本不知道要再调一次 mcp_result**, 是"静默假成功"的最坏形态。
第98轮又已用原始 CDP 证明这些命令的参数**都被内核接受**, 且多数**有返回值**:
  Page.addScriptToEvaluateOnNewDocument -> {"identifier":"1"}
  Debugger.setBreakpointOnFunctionCall  -> {"breakpointId":"7:1"}
  其余(Network.enable/setXHRBreakpoint/.../takeHeapSnapshot/startSampling) -> {}
改成同步后: 有返回值的拿到值; 没返回值的**参数错误会显式暴露**(不再假成功)。

修法沿用既有出口(不重复造轮子):
  · 逆向分派内 5 个工具 -> 执行V8CDP命令(同步等待 + 域未启用自动重试 + 可行动错误分支 + cdp_result)
  · Core 的 browser_cdp(通用 CDP 直通) -> 执行CDP并同步等待; 保留 async_only 逃生门

★ 本版改为**自定位**: 不硬编码缩进(第一版猜缩进导致 0 命中), 而是按"唯一子串"找到整行,
  取其真实缩进后再替换; 多行块同样如此。
"""
import io
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
BAK = os.path.join(ROOT, '备份', '仅回执工具改同步-写入前')

# (唯一子串, 新方法名, 新 hint)  —— 只替换"整行"里的调用, 前缀缩进沿用原行
REV_SITES = [
    ('执行逆向CDP命令 (命令ID, "DOMDebugger.setXHRBreakpoint"',
     'DOMDebugger.setXHRBreakpoint',
     'XHR 断点已装上: 命中时页面暂停在该请求发起处; 用 browser_debugger_stack / browser_debugger_evaluate 看现场, 分析完务必 browser_debugger_resume'),
    ('执行逆向CDP命令 (命令ID, "DOMDebugger.setEventListenerBreakpoint"',
     'DOMDebugger.setEventListenerBreakpoint',
     '事件监听断点已装上: 该类型事件被派发时页面暂停; 分析完务必 browser_debugger_resume'),
    ('执行逆向CDP命令 (命令ID, "DOMDebugger.setInstrumentationBreakpoint"',
     'DOMDebugger.setInstrumentationBreakpoint',
     '定时器插装断点已装上: setTimeout/setInterval/requestAnimationFrame 被调用时暂停; 分析完务必 browser_debugger_resume'),
    ('执行逆向CDP命令 (命令ID, "Debugger.setBreakpointOnFunctionCall"',
     'Debugger.setBreakpointOnFunctionCall',
     '函数调用断点已装上(cdp_result.breakpointId 可用 browser_cdp_call method=Debugger.removeBreakpoint 撤销); 该函数被调用时页面暂停, 分析完务必 browser_debugger_resume'),
    ('执行逆向CDP命令 (命令ID, "Page.addScriptToEvaluateOnNewDocument"',
     'Page.addScriptToEvaluateOnNewDocument',
     '预注入脚本已注册(每次新文档创建前执行); cdp_result.identifier 即脚本句柄, 可用 browser_cdp_call method=Page.removeScriptToEvaluateOnNewDocument 撤销; 要立刻看到效果请 browser_reload'),
    ('执行逆向CDP命令 (命令ID, "Network.enable"',
     'Network.enable',
     'Network 域已启用: 可配合 browser_kernel_cdp_monitor / browser_cdp_event 观察 Network.* 事件'),
    ('执行逆向CDP命令 (命令ID, "HeapProfiler.takeHeapSnapshot"',
     'HeapProfiler.takeHeapSnapshot',
     '堆快照已开始采集(数据经 HeapProfiler.addHeapSnapshotChunk 事件分片送达, 本命令无返回值)'),
    ('执行逆向CDP命令 (命令ID, "HeapProfiler.startSampling"',
     'HeapProfiler.startSampling',
     '内存采样已开始: 操作目标一段时间后调 action=stop_sampling 取回 profile'),
]

# 说明为何改: 每个站点前面插一行(按需), 用简短依据
REV_NOTE = {
    'DOMDebugger.setXHRBreakpoint':
        '// 改同步: 内核无返回值, 但参数错误/域未启用会显式暴露(原先只回一句"CDP已提交")',
    'Debugger.setBreakpointOnFunctionCall':
        '// 改同步: 内核会回 breakpointId, 调用方需要它才能后续撤销该断点',
    'Page.addScriptToEvaluateOnNewDocument':
        '// 改同步: 内核会回 identifier(脚本句柄), 调用方需要它才能后续移除该预注入脚本',
    'HeapProfiler.takeHeapSnapshot':
        '// 改同步: 原先快照失败也报"CDP已提交"; 数据经 addHeapSnapshotChunk 事件送达',
    'HeapProfiler.startSampling':
        '// 改同步: 采样参数错误应显式暴露',
    'Network.enable':
        '// 改同步: 让域启用失败显式暴露(原先一律"CDP已提交")',
    'DOMDebugger.setInstrumentationBreakpoint':
        '// 改同步。附注: 本机实测 DOMDebugger 侧要的就是 eventName(Debugger 侧才用 instrumentation), 旧代码本就正确',
}

CORE_MARKER = '执行CDP命令 (命令ID, cdpMethod, 参数JSON)'

CORE_NEW = '''如果 (MCP命令服务器.yyjson取逻辑 (参数JSON, "async_only"))
{ind}    {{
{ind}        返回 (MCP命令服务器.执行CDP命令 (命令ID, cdpMethod, 参数JSON))
{ind}    }}
{ind}    变量 bxParams <类型 = 文本型>
{ind}    bxParams = MCP命令服务器.yyjson取JSON文本 (参数JSON, "params")
{ind}    如果 (bxParams == "")
{ind}    {{
{ind}        bxParams = "{{}}"
{ind}    }}
{ind}    变量 bxRes <类型 = 文本型>
{ind}    bxRes = MCP命令服务器.执行CDP并同步等待 (命令ID, cdpMethod, bxParams, 20000)
{ind}    如果 (MCP命令服务器.CDP同步结果是否成功 (bxRes) == 假)
{ind}    {{
{ind}        返回 (MCP_响应构建.命令失败 (命令ID, "CDP " + cdpMethod + " 失败: " + MCP命令服务器.取CDP同步结果错误 (bxRes) + " | 若该命令本身不返回(如 Debugger.pause)或耗时很长, 请传 async_only:true 改用异步并用 mcp_result 轮询"))
{ind}    }}
{ind}    变量 bxBody <类型 = 文本型>
{ind}    bxBody = MCP命令服务器.取CDP同步结果体文本 (bxRes)
{ind}    变量 bxOut <类型 = YYJSON对象类>
{ind}    bxOut.创建自文本 ("{{}}")
{ind}    bxOut.加入逻辑值成员 ("success", 真)
{ind}    bxOut.加入文本成员 ("cdp_method", cdpMethod)
{ind}    如果 (bxBody != "")
{ind}    {{
{ind}        bxOut.加入文本成员 ("cdp_result", bxBody)
{ind}    }}
{ind}    否则
{ind}    {{
{ind}        bxOut.加入文本成员 ("cdp_result", "{{}}")
{ind}    }}
{ind}    bxOut.加入文本成员 ("note", "cdp_result 为该命令 result 的 JSON 原文; 需要异步提交(长耗时/不返回的命令)请传 async_only:true")
{ind}    返回 (MCP_响应构建.命令成功_原始JSON (命令ID, bxOut.到可读文本 (YYJSON格式化选项.压缩)))'''


def load(path):
    data = open(path, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '%s 有BOM' % path
    t = data.decode('utf-8')
    return t, ('\r\n' if '\r\n' in t else '\n')


def check_quotes(lines):
    for ln in lines:
        if ln.replace('\\"', '').count('"') % 2 != 0:
            return ln
    return None


def main():
    # ---------------- Reverse ----------------
    text, nl = load(REV)
    print('Reverse 换行=%s' % ('CRLF' if nl == '\r\n' else 'LF'))
    lines = text.split(nl)
    hits = 0
    for sub, meth, hint in REV_SITES:
        idx = [i for i, l in enumerate(lines) if sub in l]
        if len(idx) != 1:
            print('!! 子串命中 %d 次(应为1), 中止: %s' % (len(idx), sub))
            return 1
        i = idx[0]
        ind = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        # 原行形如: 返回 (MCP命令服务器.执行逆向CDP命令 (命令ID, "M", PARAMS))
        m = re.search(r'执行逆向CDP命令 \(命令ID, "[^"]+", (.*)\)\)\s*$', lines[i])
        if not m:
            print('!! 无法解析参数表达式: %s' % lines[i])
            return 1
        params = m.group(1)
        new = '%s返回 (执行V8CDP命令 (命令ID, "%s", %s, "%s"))' % (ind, meth, params, hint)
        note = REV_NOTE.get(meth)
        repl = ([ind + note] if note else []) + [new]
        bad = check_quotes(repl)
        if bad:
            print('!! 裸双引号奇数: %s' % bad)
            return 1
        lines[i:i + 1] = repl
        hits += 1
    print('   Reverse 替换 %d 处' % hits)
    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(REV, os.path.join(BAK, 'MCP_Server_Reverse.wsv'))
    open(REV, 'wb').write(nl.join(lines).encode('utf-8'))

    # ---------------- Core ----------------
    text, nl2 = load(CORE)
    print('Core 换行=%s' % ('CRLF' if nl2 == '\r\n' else 'LF'))
    clines = text.split(nl2)
    idx = [i for i, l in enumerate(clines) if CORE_MARKER in l]
    if len(idx) != 1:
        print('!! Core 锚点命中 %d 次(应为1), 中止' % len(idx))
        return 1
    i = idx[0]
    ind = clines[i][:len(clines[i]) - len(clines[i].lstrip())]
    note = ['%s// 通用 CDP 直通工具: **默认同步返回结果**。原先走 执行CDP命令(异步), 而本工具不在' % ind,
            '%s// 应同步等待 白名单内 -> 连 Runtime.evaluate 这种必然有返回值的调用也只回一句' % ind,
            '%s// "CDP已提交:Runtime.evaluate", 调用方拿不到数据(台账第5轮的 pass 即此类假通过)。' % ind,
            '%s// 保留逃生门: async_only=true 仍走异步(Debugger.pause 这类不返回的命令必须异步)。' % ind]
    block = (nl2.join(note) + nl2 + CORE_NEW.format(ind=ind)).split('\n')
    bad = check_quotes(block)
    if bad:
        print('!! 裸双引号奇数: %s' % bad)
        return 1
    clines[i:i + 1] = block
    shutil.copy2(CORE, os.path.join(BAK, 'MCP_Server_Core.wsv'))
    open(CORE, 'wb').write(nl2.join(clines).encode('utf-8'))
    print('   Core 替换 1 处(扩为 %d 行)' % len(block))
    print('完成; 备份 -> %s' % BAK)
    return 0


sys.exit(main())
