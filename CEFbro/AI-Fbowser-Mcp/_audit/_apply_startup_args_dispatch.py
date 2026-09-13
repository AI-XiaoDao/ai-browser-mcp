# -*- coding: utf-8 -*-
r"""补插 browser_startup_args 的分派分支到 MCP_Server_System.wsv。

自证问题: 上一个补丁脚本(_apply_startup_switches_v2.py)定义了 DISP_NEW 却**从未插入**(断言只查了括号/行数,
所以静默通过) —— 结果工具注册了、路由也加了, 但分派里没有分支, 调用返回空。
本脚本补上, 并断言"插入后文件里必须出现 browser_startup_args"。
行尾: 该文件是 CR CR LF, 按原行尾保留。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'src', 'MCP_Server_System.wsv')

ANCHOR = '''        如果 (方法名 == "browser_get_global_cache_dir")
        {'''

NEW = '''        如果 (方法名 == "browser_startup_args")
        {
            变量 启动回执action <类型 = 文本型>
            启动回执action = "get"
            如果 (参数JSON.是否为空 () == 假)
            {
                启动回执action = MCP命令服务器.yyjson取文本 (参数JSON, "action")
            }
            如果 (启动回执action == "list")
            {
                返回 (MCP_响应构建.构建简单JSON ("applied_switches", MCP命令服务器.命令行开关已应用))
            }
            变量 启动回执 <类型 = YYJSON对象类>
            启动回执.创建自文本 ("{}")
            启动回执.加入逻辑值成员 ("success", 真)
            启动回执.加入文本成员 ("applied_switches", MCP命令服务器.命令行开关已应用)
            启动回执.加入文本成员 ("command_line_raw", MCP命令服务器.命令行开关原文)
            启动回执.加入逻辑值成员 ("cmdline_available", MCP命令服务器.命令行对象可用)
            启动回执.加入文本成员 ("name_value_switches", MCP命令服务器.启动开关_名值表)
            启动回执.加入文本成员 ("rejected_switches", MCP命令服务器.启动开关_被拒表)
            启动回执.加入逻辑值成员 ("enable_cross_frame", MCP命令服务器.启动开关_启用跨框架操作模式)
            启动回执.加入逻辑值成员 ("disable_proxy", MCP命令服务器.启动开关_禁用代理)
            启动回执.加入文本成员 ("note", "启动开关只在启动期由 启动类.即将处理命令行 施加, 运行期无法补做; 改了 mcp_config.json 必须重启进程才生效; applied_switches 为空时看 cmdline_available 判断是没配开关还是命令行对象拿不到")
            返回 (启动回执.到可读文本 (YYJSON格式化选项.压缩))
        }
''' + ANCHOR


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
    assert not raw.startswith(b'\xef\xbb\xbf'), 'BOM'
    txt = raw.decode('utf-8')
    assert 'browser_startup_args' not in txt, '已应用过'
    term = '\r\r\n' if '\r\r\n' in txt else ('\r\n' if '\r\n' in txt else '\n')
    lines = txt.replace(term, '\n').split('\n')
    hits = find_block(lines, ANCHOR.split('\n'))
    assert len(hits) == 1, '锚点命中 %d 次(期望 1)' % len(hits)
    s = hits[0]
    indent = lines[s][:len(lines[s]) - len(lines[s].lstrip())]
    assert indent == '        ', '锚点缩进异常 %r' % indent
    new = [l for l in NEW.split('\n')]
    # 原缩进已是 8 空格, NEW 里各段缩进与之一致, 无需再加
    p0, b0 = nets(lines)
    out = lines[:s] + new + lines[s + len(ANCHOR.split('\n')):]
    p1, b1 = nets(out)
    assert (p1, b1) == (p0, b0), '括号净额 %s/%s -> %s/%s' % (p0, b0, p1, b1)
    joined = '\n'.join(out)
    assert 'browser_startup_args' in joined and joined.count('browser_startup_args') == 1
    print('锚点 @%d 行尾=%r; 行数 %d -> %d; 净额 圆 %d 花 %d 不变' %
          (s + 1, term, len(lines), len(out), p0, b0))
    if '--apply' in sys.argv:
        data = joined.replace('\n', term)
        with io.open(TARGET, 'w', encoding='utf-8', newline='') as f:
            f.write(data)
        back = open(TARGET, 'rb').read()
        assert not back.startswith(b'\xef\xbb\xbf'), '写盘后带 BOM'
        assert back.decode('utf-8') == data, '写盘回读不一致'
        print('已写入 %s' % TARGET)
    else:
        print('[dry-run] 未落盘')


main()
