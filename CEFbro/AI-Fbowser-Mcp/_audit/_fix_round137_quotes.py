# -*- coding: utf-8 -*-
r"""第137轮补丁收尾: 修掉新写的**工具描述里误用的 ASCII 双引号**(火山要求字符串内部用「」)。

实测报错: `<MCP_Server.wsv>, 11566: 错误: 发现字符处于无效位置`
成因: 描述字符串内部写了 ASCII 双引号, 提前把字符串字面量闭合掉了。

用法: py -3 _audit\_fix_round137_quotes.py [--apply]
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'src', 'MCP_Server.wsv')
APPLY = '--apply' in sys.argv

FIXES = [
    ('第135轮"装上即阻塞需重启"的结论', '第135轮「装上即阻塞需重启」的结论'),
    ('经"卡死自救"继续可用', '经「卡死自救」继续可用'),
]


def main():
    txt = io.open(SERVER, encoding='utf-8', newline='').read()
    for old, new in FIXES:
        n = txt.count(old)
        print('%s  %d 处  %s' % ('· 替换' if n else '· 未出现', n, old))
        if n:
            txt = txt.replace(old, new)
    # 校验: 只看本次新增的两条描述行, ASCII 双引号必须成对
    bad = []
    for i, ln in enumerate(txt.split('\n')):
        if 'browser_reverse_instrument_script' in ln and '添加工具JSON' in ln:
            if ln.count('"') % 2:
                bad.append(i + 1)
    print('· 描述行 ASCII 双引号奇偶校验: %s' % ('❌ 第 %s 行' % bad if bad else 'OK(成对)'))
    if APPLY:
        io.open(SERVER, 'w', encoding='utf-8', newline='').write(txt)
        print('   ✔ 已写入 MCP_Server.wsv')
    else:
        print('(预演; 加 --apply 写入)')


if __name__ == '__main__':
    main()
