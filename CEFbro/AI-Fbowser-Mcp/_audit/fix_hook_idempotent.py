# -*- coding: utf-8 -*-
"""browser_reverse_cdp_hook: 重复安装同一函数时改为**幂等成功**。

A/B 实测(全新进程 vs 同进程重复):
  A 第一次  -> {"breakpointId":"7:1"}                                   ✔
  B 再装一次 -> Breakpoint at specified location already exists.        ← 目标状态**已达成**

为什么该改: 失败会让调用方以为"没装上", 于是反复重试或改用 browser_reverse_hook /
hook_multi / JS 注入等**别的**方法 —— 正是"调用不成功、要试很多方法"的典型形态。
项目已有同一先例: browser_debugger_resume 对"本来就没暂停"返回**幂等成功**
(MCP_Server_Core.wsv 该分支注释: resume 是清场/收尾类工具, 目标状态已达成不是错误)。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
BAK = os.path.join(ROOT, '备份', '函数钩子幂等成功-写入前')

ANCHOR = '            返回 (执行V8CDP命令 (命令ID, "Debugger.setBreakpointOnFunctionCall"'

NEW = '''            变量 chRes <类型 = 文本型>
            chRes = 执行V8CDP命令 (命令ID, "Debugger.setBreakpointOnFunctionCall", chParams.到可读文本 (YYJSON格式化选项.压缩), "函数调用断点已装上(cdp_result.breakpointId 可用 browser_cdp_call method=Debugger.removeBreakpoint 撤销); 该函数被调用时页面暂停, 分析完务必 browser_debugger_resume")
            // 幂等: 内核原话 "Breakpoint at specified location already exists" 说明该函数上**本来就有**
            // 函数调用断点 —— 目标状态已达成, 不是错误。报失败会诱导调用方改用别的注入方式反复尝试
            // (与 browser_debugger_resume 对"本来就没暂停"返回幂等成功是同一处理)。
            如果 (寻找文本 (chRes, "already exists", 0, 假) != -1)
            {
                返回 (MCP_响应构建.命令成功_原始JSON (命令ID, "{\\"success\\":true,\\"already_armed\\":true,\\"cdp_method\\":\\"Debugger.setBreakpointOnFunctionCall\\",\\"note\\":\\"幂等成功: 该函数上本来就有函数调用断点(内核原话 Breakpoint at specified location already exists), 目标状态已达成, 未重复安装。要撤销请用首次安装时返回的 breakpointId 调 Debugger.removeBreakpoint; 或 browser_debugger_enable action=disable 整体停用调试器域(会一并清掉全部断点)\\"}"))
            }
            返回 (chRes)'''


def main():
    data = open(SRC, 'rb').read()
    assert not data.startswith(b'\xef\xbb\xbf'), '不应有BOM'
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    print('换行: %s' % ('CRLF' if nl == '\r\n' else 'LF'))
    idx = [i for i, l in enumerate(text.split(nl)) if l.startswith(ANCHOR)]
    print('锚点命中: %d' % len(idx))
    if len(idx) != 1:
        print('!! 锚点不唯一, 中止')
        return 1
    lines = text.split(nl)
    old_line = lines[idx[0]]
    lines[idx[0]:idx[0] + 1] = NEW.split('\n')
    for ln in NEW.split('\n'):
        if ln.replace('\\"', '').count('"') % 2 != 0:
            print('!! 裸双引号奇数: %s' % ln)
            return 1
    os.makedirs(BAK, exist_ok=True)
    shutil.copy2(SRC, os.path.join(BAK, 'MCP_Server_Reverse.wsv'))
    open(SRC, 'wb').write(nl.join(lines).encode('utf-8'))
    print('已写入(该处 1 行 -> %d 行); 备份 -> %s' % (len(NEW.split('\n')), BAK))
    print('被替换的旧行: %s' % old_line.strip()[:90])
    return 0


sys.exit(main())
