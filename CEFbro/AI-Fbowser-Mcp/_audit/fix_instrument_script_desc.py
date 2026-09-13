# -*- coding: utf-8 -*-
"""按实测更正 browser_reverse_instrument_script 的"后果说明"(不改行为, 只改承诺)。

实测(_audit/diag_instrument_script_wedge.py, 干净重启后):
  基线:            browser_status 0.00s / execute_js 0.03s
  装 action=install 之后: browser_status 仍 0.02s(它走原生, 不经 CDP)
                          **browser_execute_js 30s 超时**
                          browser_debugger_last_paused 30s 超时
  再 resume:       返回 ok(5.47s), 但 **execute_js 仍 30s 超时**
  再 action=suppress: 45s 超时; 之后 status 恢复(5.87s), 但 **execute_js 仍 30s 超时**
  => 只有**重启进程**能恢复(台账此前也是这样处理的)。

也就是说: 该工具"命中后暂停, 分析完 resume 即可"的既有说明在**本机 CEF 构建上不成立** ——
它会让本会话的 JS 通道持续阻塞, 而 resume/suppress 都救不回来。行为本身是刻意设计的
(在脚本执行前暂停, 才能抢先拿到原始源码), 故本轮**不改行为**, 只把文案与注释按实测更正,
避免调用方以为"resume 一下就好了"而陷在反复失败里。
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRV = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
REV = os.path.join(ROOT, 'src', 'MCP_Server_Reverse.wsv')
BAK = os.path.join(ROOT, '备份', '插装脚本工具后果更正-写入前')

DESC_OLD = ('需先browser_debugger_enable; 命中后页面暂停, 分析完务必browser_debugger_resume'
            '(调试器未启用时会自动启用并上报)')
DESC_NEW = ('需先browser_debugger_enable(未启用会自动启用并上报)。'
            '⚠ 实测更正(本机CEF构建): 装上后本会话的 **JS 通道即被阻塞** —— '
            'browser_execute_js / browser_debugger_last_paused 等会 30s 超时'
            '(browser_status 仍正常, 它走原生不经 CDP); 且 **browser_debugger_resume 与 '
            'action=suppress 都无法恢复, 只有重启进程才能恢复** —— 原来的"分析完务必 resume"'
            '在本机不成立, 已按实测更正。故请仅在**你打算随后重启进程**时使用; '
            '只是读取源码请改用 browser_reverse_search_script / browser_reverse_detect_traps')

CMT_OLD = '            // 注意: 命中后页面处于暂停态, 分析完必须 resume, 否则页面一直卡住。'
CMT_NEW = ('            // ⚠ 实测更正(本机CEF构建, 见 _audit/diag_instrument_script_wedge.py): 装上之后本会话的',
           '            //   **JS 通道即被阻塞** —— browser_execute_js / last_paused 等 30s 超时(browser_status 仍正常,',
           '            //   它走原生不经 CDP); 而且 browser_debugger_resume 与 action=suppress **都无法恢复**,',
           '            //   只有重启进程才行。原注释"分析完必须 resume 即可"在本机不成立, 故已按实测更正。')

EDITS = [
    ('SRV 工具描述', SRV, DESC_OLD, DESC_NEW),
    ('REV 代码注释', REV, CMT_OLD, '\n'.join(CMT_NEW)),
]


def main():
    texts = {SRV: io.open(SRV, encoding='utf-8', newline='').read(),
             REV: io.open(REV, encoding='utf-8', newline='').read()}
    for label, path, old, new in EDITS:
        n = texts[path].count(old)
        print("[%-12s] %s 出现 %d 次" % (label, os.path.basename(path), n))
        if n != 1:
            print("  !! 预期 1 次, 中止")
            return 1
    if not os.path.isdir(BAK):
        os.makedirs(BAK)
    for p in (SRV, REV):
        shutil.copy2(p, os.path.join(BAK, os.path.basename(p)))
    print("已备份到 %s" % BAK)
    for label, path, old, new in EDITS:
        texts[path] = texts[path].replace(old, new)
    for p, t in texts.items():
        io.open(p, 'w', encoding='utf-8', newline='').write(t)
    print("OK: 2 处文案/注释按实测更正")
    for p in (SRV, REV):
        raw = io.open(p, 'rb').read()
        print("复核 %-24s BOM=%s CRLF=%s 字节=%d"
              % (os.path.basename(p), raw.startswith(b'\xef\xbb\xbf'), b'\r\n' in raw, len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
