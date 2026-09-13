# -*- coding: utf-8 -*-
r"""回读校验 _apply_touch_hidden_cause.py 的落盘结果(纯静态检查, 不碰运行中的实例)。"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = io.open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), encoding='utf-8').read()
C = io.open(os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv'), encoding='utf-8').read()

RES = []


def chk(tag, ok, detail=''):
    RES.append((tag, ok))
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:90]))


chk('Server: 新增 CDPInput失败原因文本', S.count('方法 CDPInput失败原因文本') == 1)
chk('Server: 可见性判断 3 处(慢因/失败文案/触摸快速失败)',
    S.count('如果 (浏览器窗口可见 () == 假)') == 3, S.count('如果 (浏览器窗口可见 () == 假)'))
chk('Server: 慢因上报挂载 2 处(鼠标/触摸)', S.count('记CDP输入慢因 (派发起始毫秒') == 2)
chk('Server: 触摸入口快速失败已插入',
    '如果 (浏览器窗口可见 () == 假)\n        {\n            返回 (假)\n        }\n        // 零前置①' in S)
chk('Server: 纯 LF 且无 BOM',
    '\r' not in S and not io.open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), 'rb').read().startswith(b'\xef\xbb\xbf'))
chk('Core: 鼠标失败文案改为复用件 3 处', C.count('CDPInput失败原因文本 ("CDP 派发鼠标事件")') == 3,
    C.count('CDPInput失败原因文本 ("CDP 派发鼠标事件")'))
chk('Core: 触摸失败文案改为复用件 3 处', C.count('CDPInput失败原因文本 ("CDP 派发触摸")') == 3,
    C.count('CDPInput失败原因文本 ("CDP 派发触摸")'))
chk('Core: 旧的误导性文案已清除', C.count('本会话 CDP 通道已不可用') == 0, C.count('本会话 CDP 通道已不可用'))
chk('Core: 替代方案尾部保留', C.count('" | 可用替代: ') == 6, C.count('" | 可用替代: '))
chk('Core: 行尾风格未变(LF)', '\r' not in C)

bad = [t for t, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for t in bad:
    print('   未通过: %s' % t)
sys.exit(1 if bad else 0)
