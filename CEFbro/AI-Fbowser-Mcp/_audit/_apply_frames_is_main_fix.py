# -*- coding: utf-8 -*-
r"""修正 browser_get_frames 的 is_main: 由"第 0 项即主框架"改为**问框架对象自己**, 并顺带给出 url。

实测依据(本机): 类库 取框架ID() 的顺序**不保证主框架在前** —— 实测出现过
    [0] name='orderfr' is_main=True(按序号推断)  id=6-BA27…  真实 href=about:srcdoc(是**子框架**)
    [1] name=''        is_main=False             id=6-BC11…  真实 href=https://example.com/(是**主框架**)
后果: 调用方(browser_get_frames 的所有消费者, 含本项目探针)按 is_main 选框架就会选反 ——
本机 fastcheck 的"iframe 写入(G1)"臂因此把值写进了**主框架**, 看起来像工具回归, 实为清单标志位失真。

改法: 用 类_FBrowser_框架.是否为主框架() 判定; 顺带输出 url(框架地址) —— 跨域 OOPIF 不在
CDP 框架树里, 地址是唯一可靠的对照键。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')

ANCHOR_OLD = [
    '帧项.加入文本成员 ("name", name数组.取数据 (fi))',
    '}',
    '如果 (fi == 0)',
    '{',
    '帧项.加入逻辑值成员 ("is_main", 真)',
    '}',
    '否则',
    '{',
    '帧项.加入逻辑值成员 ("is_main", 假)',
    '}',
]
ANCHOR_NEW = [
    '帧项.加入文本成员 ("name", name数组.取数据 (fi))',
    '}',
    '// 约束: is_main 必须问**框架对象本身**(是否为主框架), 不能按"第 0 项就是主框架"推断 ——',
    '// 实测 类库 取框架ID() 的顺序**不保证主框架在前**(本机出现过 [子框架, 主框架] 的次序),',
    '// 按序号推断会把子框架标成 is_main 真、把主框架标成假, 调用方据此选框架就会操作错对象。',
    '变量 帧主判定 <类型 = 逻辑型>',
    '帧主判定 = 假',
    '如果 (fi < id数组.取个数 ())',
    '{',
    '变量 帧实体 <类型 = 类_FBrowser_框架>',
    '帧实体 = browser.取框架_ID (id数组.取数据 (fi))',
    '如果 (帧实体.是否为空 () == 假 && 帧实体.是否有效 ())',
    '{',
    '帧主判定 = 帧实体.是否为主框架 ()',
    '// 地址一并给出: 跨域(OOPIF)框架不在 CDP 框架树里, 按地址对照是唯一可靠的手段',
    '帧项.加入文本成员 ("url", 帧实体.取地址 ())',
    '}',
    '}',
    '如果 (帧主判定)',
    '{',
    '帧项.加入逻辑值成员 ("is_main", 真)',
    '}',
    '否则',
    '{',
    '帧项.加入逻辑值成员 ("is_main", 假)',
    '}',
]


def find_block(lines, block):
    n = len(block)
    return [i for i in range(len(lines) - n + 1)
            if [l.strip() for l in lines[i:i + n]] == block]


def nets(lines):
    p = b = 0
    for ln in lines:
        st = ln.lstrip()
        if st.startswith('@'):
            continue
        k = 0
        in_str = False
        while k < len(ln):
            c = ln[k]
            if in_str:
                if c == '\\':
                    k += 2
                    continue
                if c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == '(':
                    p += 1
                elif c == ')':
                    p -= 1
                elif c == '{':
                    b += 1
                elif c == '}':
                    b -= 1
            k += 1
    return p, b


def main():
    raw = open(TARGET, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    assert b'\r\n' not in raw, 'CRLF'
    lines = raw.decode('utf-8').split('\n')
    hits = find_block(lines, ANCHOR_OLD)
    assert len(hits) == 1, '锚点命中 %d 次(期望 1)' % len(hits)
    s = hits[0]
    indent = lines[s][:len(lines[s]) - len(lines[s].lstrip())]
    print('锚点 @%d, 缩进 %d 空格' % (s + 1, len(indent)))
    assert not any('帧主判定' in l for l in lines), '已应用过'
    p0, b0 = nets(lines)
    new = [indent + x if x else '' for x in ANCHOR_NEW]
    out = lines[:s] + new + lines[s + len(ANCHOR_OLD):]
    p1, b1 = nets(out)
    assert (p1, b1) == (p0, b0), '括号净额 %s/%s -> %s/%s' % (p0, b0, p1, b1)
    assert '取地址 ()' in '\n'.join(new)
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out))
        print('已写入 %s (行数 %d -> %d)' % (TARGET, len(lines), len(out)))
    else:
        print('[dry-run] %d 行 -> %d 行; 净额 圆 %d 花 %d 不变' % (len(ANCHOR_OLD), len(new), p0, b0))


main()
