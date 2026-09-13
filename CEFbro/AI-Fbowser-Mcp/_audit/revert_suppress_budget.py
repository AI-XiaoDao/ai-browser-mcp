# -*- coding: utf-8 -*-
"""回退上一版"缩短 suppress 预算"的改动 —— 它把**唯一能恢复的动作**弄坏了(有实测为证)。

上一版我想让恢复更快, 把 resume 预算设 5000ms、setSkipAllPauses 设 8000ms。实测结果:
    suppress -> `setSkipAllPauses 失败: timeout`(38.74s), JS 通道**未恢复**;
而改动前(15000ms)是: suppress 45.71s **成功恢复**。
原因: 该动作能通过靠的是项目既有的"卡死自救"(等满预算 -> 自动 resume -> **重试一次**);
预算压短后, 重试那次也没等到结果就放弃了 -> 恢复失败。
结论: **不要为了"更快"去压这个预算**; 45s 是这个自救链路的真实代价。

本脚本: 从备份恢复该文件, 然后**只**更新那句"恢复方式"的提示为实测事实
(唯一可恢复的动作是 action=suppress; resume 与 debugger_disable 都不行)。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
BAK = os.path.join(ROOT, '备份', 'suppress快速恢复-写入前', 'MCP_Server_Reverse.wsv')

NOTE_OLD = 'ivSupOut.加入文本成员 ("note", "已跳过全部暂停: 插装仍在但不再拦截页面 | 恢复: browser_reverse_skip_pauses skip=false")'
NOTE_NEW = ('ivSupOut.加入文本成员 ("note", "已跳过全部暂停: 插装仍在但不再拦截页面, 本会话的 JS 通道已恢复 '
            '—— 实测这是**唯一**能恢复的动作(耗时约 45s, 走的是项目既有的卡死自救: 超时后自动 resume 并重试一次), '
            'browser_debugger_resume 与 browser_debugger_disable 都**无法**恢复 | 恢复拦截: browser_reverse_skip_pauses skip=false")')

# 若备份里已被上一版改过, 用它反向替换回原样(双保险: 直接对比两种写法)
BAD_RESUME = '                MCP命令服务器.执行CDP并同步等待 (命令ID + "_srs", "Debugger.resume", "{}", 5000)\r\n' \
             '                MCP命令服务器.清除CDP事件记录 ("Debugger.paused")\r\n' \
             '                变量 ivSup <类型 = 文本型>\r\n' \
             '                ivSup = MCP命令服务器.执行CDP并同步等待 (命令ID + "_sup", "Debugger.setSkipAllPauses", "{\\"skip\\":true}", 8000)'
GOOD = '                变量 ivSup <类型 = 文本型>\r\n' \
       '                ivSup = MCP命令服务器.执行CDP并同步等待 (命令ID + "_sup", "Debugger.setSkipAllPauses", "{\\"skip\\":true}", 15000)'


def main():
    if not os.path.exists(BAK):
        print("!! 找不到备份 %s" % BAK)
        return 1
    shutil.copy2(BAK, REV)
    print("已从备份恢复 %s" % os.path.basename(REV))
    t = io.open(REV, encoding='utf-8', newline='').read()
    print("恢复后: 仍含 5000ms 预算? %s" % ('", 5000)' in t))
    n = t.count(NOTE_OLD)
    print("[提示锚点] 出现 %d 次" % n)
    if n != 1:
        print("  !! 预期 1 次, 中止(仅恢复文件, 未改提示)")
        return 1
    io.open(REV, 'w', encoding='utf-8', newline='').write(t.replace(NOTE_OLD, NOTE_NEW))
    print("OK: 仅更新'恢复方式'提示为实测事实")
    raw = io.open(REV, 'rb').read()
    print("复核: BOM=%s CRLF=%s 字节=%d"
          % (raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
