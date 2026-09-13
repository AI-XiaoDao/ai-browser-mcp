# -*- coding: utf-8 -*-
"""用 `//# sourceURL` 解锁调试器族的**真机测量**(此前在无脚本页面上无法测到)。

发现(_audit/diag_sourceurl_breakpoint.py, 实测):
  给注入的 <script> 加一行 `//# sourceURL=https://example.com/mcp-breakpoint-probe.js`,
  该脚本就会带着**真实 URL** 注册进 V8 脚本注册表(对比: 不加则 url 为空串) ——
  于是 setBreakpointByUrl 终于能匹配到, browser_debugger_auto 用 urlRegex 下断
  **真的命中了 2 次(0.99s, completed:true)**, 且对照臂(同一行 + 不存在的 urlRegex)仍 0 命中。

这解决了一个长期障碍: 报告 §95/§96 记录过"本页所有脚本 url 都是空串 -> urlRegex 断点永远
locations:[]", 导致 flow/auto 只能记成"目标未命中"、return_value/set_variable 拿不到真帧。

本轮据此给台账补:
  · 共享前置: 启用调试器域 + 幂等注入带 sourceURL 的探针脚本(内含 return 行, 便于 setReturnValue);
  · auto/flow: 用探针 URL 下断 -> 应真命中;
  · return_value/set_variable: 先用 flow(resume:false) 停在该断点上, 拿到**真实的返回位置帧**。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MP = os.path.join(ROOT, '_audit', 'mass_probe.py')
BAK = os.path.join(ROOT, '备份', '调试器族sourceURL前置-写入前')

APPEND = '''

# ============================================================================
# 调试器族的真机测量前置 —— 用 `//# sourceURL` 让注入脚本带上**真实 URL**,
# 从而 setBreakpointByUrl 能匹配到(此前本页脚本 url 全为空串, urlRegex 永远 0 位置)。
# 依据: _audit/diag_sourceurl_breakpoint.py 实测(auto 用该正则命中 2 次, 对照臂 0 命中)。
# ============================================================================

# 幂等注入: 已有则直接返回。第 2 行声明变量 v, 第 3 行是 return —— 断在第 3 行可拿到
# **返回位置**的帧, 这正是 Debugger.setReturnValue / setVariableValue 需要的位置。
_BP_PROBE_LINES = [
    "window.mcpBpTick=0;",
    "window.mcpBpFn=function mcpBpFn(){",
    "  var v=1;",
    "  return v;",
    "};",
    "window.mcpBpTimer=setInterval(window.mcpBpFn,300);",
    "//# sourceURL=https://example.com/mcp-breakpoint-probe.js",
]
_BP_PROBE_SRC = "\\n".join(_BP_PROBE_LINES)
_BP_INJECT = ("browser_execute_js", {
    "code": ("(function(){if(window.mcpBpTimer)return 'exists';"
             "var s=document.createElement('script');s.textContent=%s;"
             "document.body.appendChild(s);return 'ok'})()" % __import__('json').dumps(_BP_PROBE_SRC))})

# 停在探针脚本第 3 行(0 起算)的返回语句上, 且**不自动 resume** -> 后续工具能用到这个活帧
_BP_PAUSE = ("browser_debugger_flow", {"breakpoint": "mcp-breakpoint-probe", "line": 3,
                                      "resume": False, "max_ms": 8000})

TOOL_PRE_CALLS.update({
    "browser_debugger_auto": [("browser_debugger_enable", {}), _BP_INJECT],
    "browser_debugger_flow": [("browser_debugger_enable", {}), _BP_INJECT],
    # 这两个需要"停在断点上的活帧", 故再加一步 flow(resume:false)
    "browser_reverse_return_value": [("browser_debugger_enable", {}), _BP_INJECT, _BP_PAUSE],
    "browser_reverse_set_variable": [("browser_debugger_enable", {}), _BP_INJECT, _BP_PAUSE],
})
TOOL_ARG_OVERRIDES.update({
    # 命中应很快(探针每 300ms 调一次该函数)
    "browser_debugger_auto": {"breakpoint": "mcp-breakpoint-probe", "line": 3,
                              "max_ms": 8000, "max_hits": 2},
    "browser_debugger_flow": {"breakpoint": "mcp-breakpoint-probe", "line": 3,
                              "max_ms": 8000},
    "browser_reverse_return_value": {"value": "true"},
    "browser_reverse_set_variable": {"variable_name": "v", "value": "42"},
})
'''


def main():
    t = io.open(MP, encoding='utf-8', newline='').read()
    if 'mcp-breakpoint-probe' in t:
        print("!! 似乎已追加过, 中止")
        return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    shutil.copy2(MP, os.path.join(BAK, os.path.basename(MP)))
    print("已备份到 %s" % BAK)
    io.open(MP, 'w', encoding='utf-8', newline='').write(t + APPEND)
    print("OK: 已追加调试器族前置与覆盖")
    sys.path.insert(0, os.path.dirname(MP))
    import importlib
    mp = importlib.import_module('mass_probe')
    print("自检: import 成功; TOOL_ARG_OVERRIDES=%d, TOOL_PRE_CALLS=%d"
          % (len(mp.TOOL_ARG_OVERRIDES), len(mp.TOOL_PRE_CALLS)))
    print("自检: auto 前置链 = %s" % [x[0] for x in mp.TOOL_PRE_CALLS.get('browser_debugger_auto', [])])
    print("自检: auto 覆盖 = %r" % (mp.TOOL_ARG_OVERRIDES.get('browser_debugger_auto'),))
    return 0


if __name__ == '__main__':
    sys.exit(main())
