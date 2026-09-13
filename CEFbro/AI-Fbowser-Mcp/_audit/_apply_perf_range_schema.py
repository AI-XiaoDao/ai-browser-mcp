# -*- coding: utf-8 -*-
r"""给 browser_vip_disable_console 的 schema 补 performance_min_ms / performance_max_ms(小数)。

依据: 类库 内核开关_禁用Performance检测(是否禁用, 最小值@默认值=0, 最大值@默认值=0) 的注释写着
"默认值0.3 / 默认值1"(即推荐区间), 而真默认是 0 —— 只传布尔会让内核收到 0~0, performance.now 退化为固定 0。
本补丁把区间做成可调参数(缺省由实现侧给 0.3/1), 并如实写进描述, 让调用方知道它在做什么。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

TOOL = '添加工具JSON ("browser_vip_disable_console"'
ADD = (' + "," + 属性项JSON ("performance_min_ms", "number", "performance 伪装区间下限(毫秒, 缺省0.3)")'
       ' + "," + 属性项JSON ("performance_max_ms", "number", "performance 伪装区间上限(毫秒, 缺省1)")')


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    assert b'\r\n' not in raw, 'CRLF'
    lines = raw.decode('utf-8').split('\n')
    hits = [i for i, l in enumerate(lines) if l.lstrip().startswith(TOOL)]
    assert len(hits) == 1, '工具注册行命中 %d 次' % len(hits)
    i = hits[0]
    line = lines[i]
    assert 'performance_min_ms' not in line, '已应用过'
    # 在 required 参数(倒数第二个逗号后的那段)之前插入:
    # 该行形如 ... + 属性项JSON ("performance", "boolean", "..."), "required 串"))
    marker = ', "'
    pos = line.rfind(marker)
    assert pos > 0, '未找到 required 段'
    lines[i] = line[:pos] + ADD + line[pos:]
    out = '\n'.join(lines)
    assert '"performance_max_ms"' in out
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write(out)
        print('已写入 %s' % TARGET)
    else:
        print('[dry-run] 将把 %d 字符插入第 %d 行 required 段之前' % (len(ADD), i + 1))
        print('   尾部预览: ...%s' % lines[i][-220:])


main()
