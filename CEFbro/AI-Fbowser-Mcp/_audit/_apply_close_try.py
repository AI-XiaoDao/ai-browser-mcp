# -*- coding: utf-8 -*-
r"""browser_close 增 try_close: 走类库 尝试关闭浏览器(= CEF TryCloseBrowser), 让"页面能否否决关闭"可用且可分辨。

依据(类库原文 FBroLib.wsv:796-805):
    方法 尝试关闭浏览器 <公开 类型 = 逻辑型 注释 = "英文名：TryCloseBrowser ...">
    参数 是否置空 <逻辑型 @默认值 = 假>
    @ if(FBroHsBrowserHost_TryCloseBrowser(m_class)){ ... return true;} return false;
CEF 语义: 返回真 = 已开始/已完成关闭; 返回假 = **关闭被取消**(典型是页面 beforeunload 未确认)。
故返回值本身就是"页面否决"信号 —— 此前只能在文档里写"没有独立信号", 实测类库是给了的。
另加 8 秒轮询确认(项目既有等待风格), 以便把"已关闭"与"已发起但未完成"分开如实回报。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')

OLD = [
    '变量 closingID <类型 = 整数>',
    'closingID = closeBrowser.取ID ()',
    'closeBrowser.关闭浏览器 ()',
    '返回 (MCP_响应构建.命令成功 (命令ID, "浏览器已关闭: id=" + 到文本 (closingID)))',
]
NEW = [
    '变量 closingID <类型 = 整数>',
    'closingID = closeBrowser.取ID ()',
    '// try_close=true: 走类库 尝试关闭浏览器(= CEF TryCloseBrowser) —— 它会**询问页面**,',
    '// 页面可用 beforeunload 否决; 返回值本身就是否决信号(假 = 未开始关闭)。',
    '// 与默认路径(强制关闭, 不问页面)的区别必须让调用方看得见, 故两条路径分开回报。',
    '如果 (MCP命令服务器.yyjson取逻辑 (参数JSON, "try_close"))',
    '{',
    '变量 已开始关闭 <类型 = 逻辑型>',
    '已开始关闭 = closeBrowser.尝试关闭浏览器 ()',
    '如果 (已开始关闭 == 假)',
    '{',
    '返回 (MCP_响应构建.命令失败 (命令ID, "关闭被页面否决: 页面 beforeunload 处理器返回了内容且未确认 | 依据: 类库 尝试关闭浏览器(TryCloseBrowser) 返回假 = 未开始关闭 | 可用替代: ① 不带 try_close 的强制关闭(不询问页面) ② 用 browser_collect 查 js_dialog/before_unload 事件看页面提了什么 ③ 页面允许后再重试"))',
    '}',
    '变量 关闭等待次数 <类型 = 整数 值 = 0>',
    '判断循环 (关闭等待次数 < 40)',
    '{',
    '关闭等待次数 = 关闭等待次数 + 1',
    '如果 (closeBrowser.是否已关闭 ())',
    '{',
    '跳出循环',
    '}',
    'MCP可中断延时 (200, 50, 假)',
    '}',
    '如果 (closeBrowser.是否已关闭 ())',
    '{',
    '返回 (MCP_响应构建.命令成功 (命令ID, "浏览器已关闭(尝试关闭): id=" + 到文本 (closingID)))',
    '}',
    '返回 (MCP_响应构建.命令成功 (命令ID, "关闭已发起但 8 秒内未见关闭完成: id=" + 到文本 (closingID) + " | 页面可能仍在 beforeunload 询问中, 或关闭被延迟 | 请用 browser_list 复查该 id 是否仍在"))',
    '}',
    'closeBrowser.关闭浏览器 ()',
    '返回 (MCP_响应构建.命令成功 (命令ID, "浏览器已关闭: id=" + 到文本 (closingID)))',
]

DESC_OLD = '添加工具JSON ("browser_close", "关闭指定浏览器(默认关闭主浏览器)", 单参数Schema文本 ("browser_id", "integer", "浏览器ID(省略则关闭主浏览器)", 假))'
DESC_NEW = ('添加工具JSON ("browser_close", "关闭指定浏览器(默认关闭主浏览器)。try_close=true 时走类库 尝试关闭浏览器(= CEF TryCloseBrowser): '
            '会**询问页面**因此可被 beforeunload 否决 —— 否决时明确报错(而不是假装已关闭); 缺省为强制关闭, 不询问页面", '
            '多属性Schema文本 (属性项JSON ("browser_id", "integer", "浏览器ID(省略则关闭主浏览器)") '
            '+ "," + 属性项JSON ("try_close", "boolean", "true=先询问页面(可被 beforeunload 否决, 被否决会明确报错); 缺省 false=强制关闭"), ""))')


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
    assert not raw.startswith(b'\xef\xbb\xbf') and b'\r\n' not in raw
    lines = raw.decode('utf-8').split('\n')
    assert not any('try_close' in l for l in lines), '已应用过'
    hits = find_block(lines, OLD)
    assert len(hits) == 1, '锚点命中 %d 次' % len(hits)
    s = hits[0]
    indent = lines[s][:len(lines[s]) - len(lines[s].lstrip())]
    p0, b0 = nets(lines)
    new = [indent + l if l else '' for l in NEW]
    out = lines[:s] + new + lines[s + len(OLD):]
    p1, b1 = nets(out)
    assert (p1, b1) == (p0, b0), '净额 %s/%s -> %s/%s' % (p0, b0, p1, b1)

    sraw = open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), 'rb').read()
    stxt = sraw.decode('utf-8')
    n = stxt.count(DESC_OLD)
    assert n == 1, '描述锚点 %d 次' % n
    sout = stxt.replace(DESC_OLD, DESC_NEW)

    print('分支 @%d 缩进=%d; %d 行 -> %d 行; 描述已更新' % (s + 1, len(indent), len(OLD), len(new)))
    if '--apply' in sys.argv:
        with io.open(TARGET, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out))
        with io.open(os.path.join(ROOT, 'src', 'MCP_Server.wsv'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(sout)
        print('已写入两个文件')
    else:
        print('[dry-run] 未落盘')


main()
