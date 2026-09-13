# -*- coding: utf-8 -*-
r"""G8 收尾: 规整全局缓存目录里的**双反斜杠**。

实测: 取运行目录() 结尾自带分隔符, 再拼 "\CacheData\GlobalData" 会得到 `...linker\\CacheData\GlobalData`;
而内核回报的活体路径(browser_cache_dir → CefRequestContext::GetCachePath)是**单反斜杠**。
虽然 Windows 容忍双分隔符, 但"推导值与内核值字面不等"会让调用方无法直接比较/拼接, 故规整为单分隔符。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server_System.wsv')

ANCHOR = '缓存目录来源 = "derived: 与 main.wsv 同一开关(是否为Stdio模式), 非内核回报值"'
INSERT = [
    '// 规整双分隔符: 取运行目录() 结尾自带路径分隔符, 再拼 "\\CacheData\\GlobalData" 会得到 "\\\\"',
    '// 而内核回报的活体路径是单分隔符 —— 字面不等会让调用方无法直接比较(Windows 虽容忍, 但对照会失败)。',
    '变量 规整缓存目录 <类型 = 文本型>',
    '规整缓存目录 = 全局缓存目录',
    '子文本替换 (规整缓存目录, "\\\\\\\\", "\\\\", , , 假)',
    '全局缓存目录 = 规整缓存目录',
]


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    txt = raw.decode('utf-8')
    lines = txt.split('\n')
    hits = [i for i, l in enumerate(lines) if l.strip() == ANCHOR]
    assert len(hits) == 1, '锚点 %d' % len(hits)
    s = hits[0]
    assert not any('规整缓存目录' in l for l in lines), '已应用过'
    tail = '\r' if lines[s].endswith('\r') else ''
    indent = lines[s][:len(lines[s]) - len(lines[s].lstrip())]
    new = [indent + x + tail for x in INSERT]
    out = lines[:s + 1] + new + lines[s + 1:]
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
            f.write('\n'.join(out))
        print('已写入 %s (+%d 行)' % (TARGET, len(new)))
    else:
        print('[dry-run] 在 %d 行后插入 %d 行' % (s + 1, len(new)))
        for l in new:
            print('   + %s' % l.rstrip())


main()
