# -*- coding: utf-8 -*-
r"""修正上一补丁: 类库 取窗口运行风格 () 返回的是**枚举类型** 窗口运行风格(非整数), 直接赋给整数变量编译不过。

证据(编译原文): `MCP_Server_System.wsv, 164: 错误: 无法将数据类型"FBrowser.常量.窗口运行风格"转换到"整数"`。
改法: 用枚举类型变量接收后显式转整数(项目内已有 `(长整数)取文本长度 (...)` 这类显式转换先例)。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server_System.wsv')

OLD = [
    '变量 运行风格值 <类型 = 整数>',
    '运行风格值 = browser.取窗口运行风格 ()',
    '风格对象.加入整数成员 ("runtime_style", 运行风格值)',
]
NEW = [
    '// 类库 取窗口运行风格 () 返回的是**枚举** 窗口运行风格(FBrowser.常量), 不是整数 —— 必须先接枚举再显式转整数',
    '// (实测编译错误原文: 无法将数据类型"FBrowser.常量.窗口运行风格"转换到"整数")',
    '变量 运行风格枚举 <类型 = 窗口运行风格>',
    '运行风格枚举 = browser.取窗口运行风格 ()',
    '变量 运行风格值 <类型 = 整数>',
    '运行风格值 = (整数)运行风格枚举',
    '风格对象.加入整数成员 ("runtime_style", 运行风格值)',
]


def find_block(lines, block):
    n = len(block)
    return [i for i in range(len(lines) - n + 1)
            if [l.strip() for l in lines[i:i + n]] == [x.strip() for x in block]]


def nets(lines):
    p = b = 0
    for ln in lines:
        st = ln.lstrip()
        if st.startswith('@') or st.startswith('//') or st.startswith('#'):
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
    assert not raw.startswith(b'\xef\xbb\xbf')
    txt = raw.decode('utf-8')
    term = '\r\r\n' if '\r\r\n' in txt else ('\r\n' if '\r\n' in txt else '\n')
    lines = txt.replace(term, '\n').split('\n')
    assert not any('运行风格枚举' in l for l in lines), '已应用过'
    hits = find_block(lines, OLD)
    assert len(hits) == 1, '锚点 %d' % len(hits)
    s = hits[0]
    indent = lines[s][:len(lines[s]) - len(lines[s].lstrip())]
    p0, b0 = nets(lines)
    new = [indent + l if l else '' for l in NEW]
    out = lines[:s] + new + lines[s + len(OLD):]
    p1, b1 = nets(out)
    assert (p1, b1) == (p0, b0), '净额 %s/%s -> %s/%s' % (p0, b0, p1, b1)
    print('锚点 @%d; %d 行 -> %d 行; 净额不变' % (s + 1, len(OLD), len(new)))
    if '--apply' in sys.argv:
        data = '\n'.join(out).replace('\n', term)
        with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
            f.write(data)
        print('已写入 %s' % TARGET)
    else:
        print('[dry-run] 未落盘')


main()
