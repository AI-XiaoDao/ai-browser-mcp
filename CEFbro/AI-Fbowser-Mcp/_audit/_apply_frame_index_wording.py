# -*- coding: utf-8 -*-
r"""订正文档口径: "序号(0=主框架)" 的说法不成立。

实测: 类库 取框架ID() 的顺序**不保证主框架在前**(本机出现过 [子框架, 主框架]),
故"序号 0 就是主框架"是错的; 序号只是**框架清单里的位置**, 主框架该由 browser_get_frames 的
is_main 字段(现在改为问框架对象自身)判断。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

OLD = '序号(0=主框架)'
NEW = '序号(它在 browser_get_frames 清单里的位置)'
OLD2 = '纯数字序号(清单顺序, 0=主框架)'
NEW2 = '纯数字序号(它在框架清单里的位置, 主框架不一定在 0 位)'


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    assert b'\r\n' not in raw, 'CRLF'
    txt = raw.decode('utf-8')
    n1 = txt.count(OLD)
    n2 = txt.count(OLD2)
    print('命中: %r x %d ; %r x %d' % (OLD, n1, OLD2, n2))
    assert n1 >= 20, '第一处命中过少(%d), 是否尚未应用描述补丁?' % n1
    out = txt.replace(OLD, NEW).replace(OLD2, NEW2)
    assert out.count(NEW) == n1 and out.count(NEW2) == n2
    assert out.count('\n') == txt.count('\n'), '行数变化'
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('已写入 %s (替换 %d + %d 处)' % (TARGET, n1, n2))
    else:
        print('[dry-run] 将替换 %d + %d 处' % (n1, n2))


main()
