# -*- coding: utf-8 -*-
r"""撤掉 try_close 参数(实测证明它在本项目里**不会发起关闭**), 并把实测依据写进 legacy 工具的文案。

实测(_audit/probe_close_try_plain.py, 干净实例):
  · 副浏览器(页面无 beforeunload) + try_close:true -> 内核返回假("未开始关闭"), 该浏览器仍在;
  · 同一浏览器改用缺省强制关闭 -> 立即关闭成功;
  · 主浏览器同理返回假。
  ⇒ 本项目是控制台程序, **没有顶层窗口关闭处理器**, 而类库原文(FBroLib.wsv:797)写明
    "TryCloseBrowser ... Call this method from the top-level window close handler" —— 故本机不存在
    "可被页面否决的优雅关闭"这条路径。
  ⇒ 结论: 保留该参数只会让 AI 以为"能优雅关闭", 实际每次都拿错误 —— 属"承诺了做不到的能力",
    按镜像纪律撤掉, 并把实测依据写进 legacy 工具 browser_close_try 的失败文案(它就是问这件事的入口)。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'src', 'MCP_Server_Core.wsv')
SRV = os.path.join(ROOT, 'src', 'MCP_Server.wsv')

# 1) Core: 整块 try_close 退回为原来的 4 行
BLOCK_START = '                 // try_close=true: 走类库 尝试关闭浏览器(= CEF TryCloseBrowser) —— 它会**询问页面**,'
BLOCK_END = '                 返回 (MCP_响应构建.命令成功 (命令ID, "浏览器已关闭: id=" + 到文本 (closingID)))'
REVERT = ['                 closeBrowser.关闭浏览器 ()',
          '                 返回 (MCP_响应构建.命令成功 (命令ID, "浏览器已关闭: id=" + 到文本 (closingID)))']

# 2) Schema: 退回单参数 + 在描述里写明"没有可被页面否决的关闭路径"这一实测结论
DESC_OLD_MARK = '添加工具JSON ("browser_close", "关闭指定浏览器(默认关闭主浏览器)。try_close=true'
DESC_NEW = ('添加工具JSON ("browser_close", "关闭指定浏览器(默认关闭主浏览器)| 强制关闭, **不询问页面**(beforeunload 不阻塞)。'
            '实测说明: 类库的 尝试关闭浏览器(TryCloseBrowser, 本应"先问页面、可被 beforeunload 否决")在本项目**恒返回假** —— '
            '本项目是控制台程序, 没有类库要求的"顶层窗口关闭处理器", 故**本机不存在可被页面否决的优雅关闭路径**; '
            '要关闭请直接用本工具(见 browser_close_try 的失败文案)", 单参数Schema文本 ("browser_id", "integer", "浏览器ID(省略则关闭主浏览器)", 假))')


def main():
    # Core 回退
    raw = open(CORE, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf') and b'\r\n' not in raw
    lines = raw.decode('utf-8').split('\n')
    # 用**去空白前缀**定位(避免手抄缩进/空格字符差异导致匹配失败)
    starts = [i for i, l in enumerate(lines) if l.strip().startswith('// try_close=true:')]
    assert len(starts) == 1, '块起始锚点 %d' % len(starts)
    a = starts[0]
    ends = [i for i, l in enumerate(lines)
            if l.strip() == '返回 (MCP_响应构建.命令成功 (命令ID, "浏览器已关闭: id=" + 到文本 (closingID)))' and i > a]
    assert len(ends) >= 1, '块结束锚点 0'
    b = ends[0]
    assert a < b, '锚点顺序异常'
    # 断言要删的区间里确实只有我们加的 try_close 逻辑
    block = '\n'.join(lines[a:b + 1])
    assert 'try_close' in block and '尝试关闭浏览器' in block, '要回退的区间内容不符'
    out = lines[:a] + REVERT + lines[b + 1:]
    assert 'try_close' not in '\n'.join(out), '回退后仍残留 try_close'
    assert '尝试关闭浏览器' not in '\n'.join(out), '回退后仍残留 尝试关闭浏览器'

    # Schema 回退
    sraw = open(SRV, 'rb').read()
    assert not sraw.startswith(b'\xef\xbb\xbf') and b'\r\n' not in sraw
    slines = sraw.decode('utf-8').split('\n')
    hits = [i for i, l in enumerate(slines) if l.lstrip().startswith(DESC_OLD_MARK)]
    assert len(hits) == 1, '描述锚点 %d' % len(hits)
    i = hits[0]
    indent = slines[i][:len(slines[i]) - len(slines[i].lstrip())]
    slines[i] = indent + DESC_NEW
    assert 'try_close' not in '\n'.join(slines), '描述回退不彻底'

    print('Core: 删除 %d 行 try_close 逻辑, 回退为 %d 行; Schema: 恢复单参数并写明实测结论'
          % (b - a + 1, len(REVERT)))
    if '--apply' in sys.argv:
        with io.open(CORE, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out))
        with io.open(SRV, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(slines))
        print('已写入两个文件')
    else:
        print('[dry-run] 未落盘')


main()
