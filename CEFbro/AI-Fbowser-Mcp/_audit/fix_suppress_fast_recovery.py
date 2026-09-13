# -*- coding: utf-8 -*-
"""修 browser_reverse_instrument_script 的恢复路径: 让 action=suppress **快速**恢复(实测 45.7s -> 数秒)。

实测(_audit/diag_instrument_recovery.py, 每轮干净重启):
  装入后 JS 通道死(35s 超时) —— 机理: beforeScriptExecution 插装对"执行脚本"生效, 而自检探针
  (Reverse:969)正是用 Runtime.evaluate 去验证, 于是探针自己触发插装 -> 页面暂停 -> 该 evaluate
  永不返回 -> 单条 CDP 队列被占。
  恢复候选: resume 不能恢复; debugger_disable 不能恢复; **suppress 能恢复**(它先是靠项目既有的
  卡死自救"超时->自动 resume->重试"才通过), 但耗时 **45.71s** —— 而客户端常在 45s 就放弃,
  于是恢复动作被掐断, 用户以为"只能重启"。

修法: suppress 里**先主动 resume 并把等待预算压短**, 再设 skipAllPauses。
这样自救不必等满长预算, 恢复从 45.7s 降到数秒级, 能落在客户端耐心之内。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
BAK = os.path.join(ROOT, '备份', 'suppress快速恢复-写入前')

OLD = '\n'.join([
    '            如果 (ivAction == "suppress")',
    '            {',
    '                // 本机 Chromium 缺少 Debugger.removeInstrumentationBreakpoint, 故提供"不丢状态"的止血动作:',
    '                // 插装保留但不再拦截(等价于全局跳过暂停), 不影响断点定义与页面状态。',
    '                变量 ivSup <类型 = 文本型>',
    '                ivSup = MCP命令服务器.执行CDP并同步等待 (命令ID + "_sup", "Debugger.setSkipAllPauses", "{\\"skip\\":true}", 15000)',
])

NEW = '\n'.join([
    '            如果 (ivAction == "suppress")',
    '            {',
    '                // 本机 Chromium 缺少 Debugger.removeInstrumentationBreakpoint, 故提供"不丢状态"的止血动作:',
    '                // 插装保留但不再拦截(等价于全局跳过暂停), 不影响断点定义与页面状态。',
    '                // ★ 修(恢复太慢会被客户端掐断, 实测 45.7s):',
    '                //   插装生效后页面停在断点上, 且队列里还压着一条永不返回的 evaluate;',
    '                //   直接发 setSkipAllPauses 只能靠"卡死自救"(等满预算 -> 自动 resume -> 重试)才通过,',
    '                //   实测耗时 45.71s —— 客户端常在 45s 就放弃, 恢复动作被掐断, 用户会以为"只能重启"。',
    '                //   故这里**先主动 resume 把暂停与队列排空**, 且把两次等待的预算都压短。',
    '                MCP命令服务器.执行CDP并同步等待 (命令ID + "_srs", "Debugger.resume", "{}", 5000)',
    '                MCP命令服务器.清除CDP事件记录 ("Debugger.paused")',
    '                变量 ivSup <类型 = 文本型>',
    '                ivSup = MCP命令服务器.执行CDP并同步等待 (命令ID + "_sup", "Debugger.setSkipAllPauses", "{\\"skip\\":true}", 8000)',
])

# 同时把"恢复"提示改成实测结论(resume/disable 都不行, suppress 才行)
NOTE_OLD = 'ivSupOut.加入文本成员 ("note", "已跳过全部暂停: 插装仍在但不再拦截页面 | 恢复: browser_reverse_skip_pauses skip=false")'
NOTE_NEW = ('ivSupOut.加入文本成员 ("note", "已跳过全部暂停: 插装仍在但不再拦截页面, 本会话的 JS 通道已恢复 '
            '(实测: 这是唯一能恢复的动作 —— browser_debugger_resume 与 browser_debugger_disable 都无法恢复) '
            '| 恢复拦截: browser_reverse_skip_pauses skip=false")')


def main():
    t = io.open(REV, encoding='utf-8', newline='').read()
    crlf = '\r\n' in t
    old = OLD.replace('\n', '\r\n') if crlf else OLD
    new = NEW.replace('\n', '\r\n') if crlf else NEW
    note_old = NOTE_OLD.replace('\n', '\r\n') if crlf else NOTE_OLD
    note_new = NOTE_NEW.replace('\n', '\r\n') if crlf else NOTE_NEW
    for label, frag in (("suppress 主体", old), ("恢复提示", note_old)):
        n = t.count(frag)
        print("[%s] 出现 %d 次 (CRLF=%s)" % (label, n, crlf))
        if n != 1:
            print("  !! 预期 1 次, 中止")
            return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    shutil.copy2(REV, os.path.join(BAK, os.path.basename(REV)))
    print("已备份到 %s" % BAK)
    t = t.replace(old, new).replace(note_old, note_new)
    io.open(REV, 'w', encoding='utf-8', newline='').write(t)
    print("OK: suppress 改为先 resume 且预算压短")
    raw = io.open(REV, 'rb').read()
    print("复核: BOM=%s CRLF=%s 字节=%d"
          % (raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
