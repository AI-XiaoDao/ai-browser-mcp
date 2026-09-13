# -*- coding: utf-8 -*-
r"""browser_get_run_style 口径订正: 补 CEF 的真 runtime_style, 并改准工具描述。

依据(只读核对): 类库 `类_FBrowser_浏览器.取窗口运行风格 ()`(FBroLib.wsv:1456, 返回 窗口运行风格 常量
默认0/谷歌1/经典2, FBroConst.wsv:750-757)在项目里**零调用**; 而工具 `browser_get_run_style` 的描述是
"获取窗口运行风格", 实际只回 Win32 GWL_STYLE + is_popup —— 名实不符, 会误导调用方。
本补丁: 补 runtime_style/runtime_style_name(保留原字段不动), 并把描述改准。
MCP_Server_System.wsv 是 CR CR LF 行尾, 按原行尾保留。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYS_FILE = os.path.join(ROOT, 'src', 'MCP_Server_System.wsv')
SRV_FILE = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

ANCHOR = [
    '风格对象.加入逻辑值成员 ("is_popup", browser.是否为弹窗 ())',
    '风格对象.加入整数成员 ("browser_id", browser.取ID ())',
]
NEW = [
    '风格对象.加入逻辑值成员 ("is_popup", browser.是否为弹窗 ())',
    '风格对象.加入整数成员 ("browser_id", browser.取ID ())',
    '// 约束(口径订正): 本工具原先只回 Win32 的 GWL_STYLE, 与工具名/描述里的"窗口运行风格"并不对应。',
    '// CEF 的运行风格是另一件事(默认0/谷歌1/经典2)。此处补上真值, 并**保留**原字段(已有调用方可能依赖)。',
    '变量 运行风格值 <类型 = 整数>',
    '运行风格值 = browser.取窗口运行风格 ()',
    '风格对象.加入整数成员 ("runtime_style", 运行风格值)',
    '变量 运行风格名 <类型 = 文本型>',
    '运行风格名 = "默认"',
    '如果 (运行风格值 == 1)',
    '{',
    '运行风格名 = "谷歌"',
    '}',
    '否则 (运行风格值 == 2)',
    '{',
    '运行风格名 = "经典"',
    '}',
    '风格对象.加入文本成员 ("runtime_style_name", 运行风格名)',
    '风格对象.加入文本成员 ("runtime_style_note", "runtime_style 来自 CEF CefRuntimeStyle(0默认/1谷歌/2经典); 本项目创建浏览器时未设置 窗口信息.运行风格, 故当前恒为 0 —— 它不是 Win32 的 GWL_STYLE(那个在 window_style 字段)")',
]

OLD_DESC = '添加工具JSON ("browser_get_run_style", "获取窗口运行风格")'
NEW_DESC = ('添加工具JSON ("browser_get_run_style", "获取窗口风格信息: window_style=Win32 GWL_STYLE, '
            'is_popup/browser_id, 以及 CEF 的 runtime_style(0默认/1谷歌/2经典, 附 runtime_style_name)。'
            '注意: 本项目创建浏览器时未设置 窗口信息.运行风格, 故 runtime_style 当前恒为 0")')


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


def patch_sys():
    raw = open(SYS_FILE, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    txt = raw.decode('utf-8')
    assert 'runtime_style' not in txt, '已应用过'
    term = '\r\r\n' if '\r\r\n' in txt else ('\r\n' if '\r\n' in txt else '\n')
    lines = txt.replace(term, '\n').split('\n')
    hits = find_block(lines, ANCHOR)
    assert len(hits) == 1, '锚点命中 %d 次' % len(hits)
    s = hits[0]
    indent = lines[s][:len(lines[s]) - len(lines[s].lstrip())]
    assert indent == '                ', '缩进异常 %r' % indent
    p0, b0 = nets(lines)
    new = [indent + l if l else '' for l in NEW]
    out = lines[:s] + new + lines[s + len(ANCHOR):]
    p1, b1 = nets(out)
    assert (p1, b1) == (p0, b0), '净额 %s/%s -> %s/%s' % (p0, b0, p1, b1)
    print('MCP_Server_System.wsv: 锚点 @%d, %d 行 -> %d 行' % (s + 1, len(ANCHOR), len(new)))
    return '\n'.join(out).replace('\n', term), term


def patch_srv():
    raw = open(SRV_FILE, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    assert b'\r\n' not in raw, 'CRLF'
    txt = raw.decode('utf-8')
    n = txt.count(OLD_DESC)
    assert n == 1, '描述命中 %d 次' % n
    print('MCP_Server.wsv: 描述已订正')
    return txt.replace(OLD_DESC, NEW_DESC)


def main():
    sys_out, term = patch_sys()
    srv_out = patch_srv()
    if '--apply' in sys.argv:
        with io.open(SYS_FILE, 'w', encoding='utf-8', newline='') as f:
            f.write(sys_out)
        with io.open(SRV_FILE, 'w', encoding='utf-8', newline='\n') as f:
            f.write(srv_out)
        print('已写入两个文件 (System 行尾=%r 保留)' % term)
    else:
        print('[dry-run] 未落盘')


main()
