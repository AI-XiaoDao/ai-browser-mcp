# -*- coding: utf-8 -*-
r"""修正 runtime_style_note 的实测口径: 本机实测 runtime_style = 1(谷歌), 不是 0。

上一版注释写"本项目未设置 运行风格 故恒为 0", 实测打脸 —— 值来自类库默认(1=谷歌)。
如实改成"实测 1(谷歌), 由类库默认给出; 本项目未显式设置该字段"。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server_System.wsv')

OLD = 'runtime_style 来自 CEF CefRuntimeStyle(0默认/1谷歌/2经典); 本项目创建浏览器时未设置 窗口信息.运行风格, 故当前恒为 0 —— 它不是 Win32 的 GWL_STYLE(那个在 window_style 字段)'
NEW = 'runtime_style 来自 CEF CefRuntimeStyle(0默认/1谷歌/2经典); 本机实测为 1(谷歌) —— 该值由类库默认给出, 本项目未显式设置 窗口信息.运行风格; 它不是 Win32 的 GWL_STYLE(那个在 window_style 字段)'


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf')
    txt = raw.decode('utf-8')
    term = '\r\r\n' if '\r\r\n' in txt else ('\r\n' if '\r\n' in txt else '\n')
    n = txt.count(OLD)
    assert n == 1, '锚点命中 %d 次' % n
    out = txt.replace(OLD, NEW)
    print('已替换 runtime_style_note 文案(实测口径)')
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
            f.write(out)
        print('已写入 %s' % TARGET)
    else:
        print('[dry-run] 未落盘')


main()
