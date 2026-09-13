# -*- coding: utf-8 -*-
r"""把 dpi_aware / v8_max_stack_mb 也纳入 browser_startup_args 回执 + 补齐两份文档的字段表。

理由: 这两个键同样是"启动期生效、改了必须重启", 若不可观测就无法自查; 回执里给出解析值即可证明
"配置读到了"(真正的内核效果仍需各自专项验证, 文档里如实写明)。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYS_FILE = os.path.join(ROOT, 'src', 'MCP_Server_System.wsv')
README = os.path.join(ROOT, 'mcp_config.README.md')
DOCS = os.path.join(ROOT, 'docs', 'MCP工具配置说明书.md')

# 1) 回执补两行(插在 disable_proxy 那行之后)
RECV_ANCHOR = '            启动回执.加入逻辑值成员 ("disable_proxy", MCP命令服务器.启动开关_禁用代理)'
RECV_NEW = [RECV_ANCHOR,
            '            启动回执.加入逻辑值成员 ("dpi_aware", MCP命令服务器.启动DPI感知模式)',
            '            启动回执.加入整数成员 ("v8_max_stack_mb", MCP命令服务器.V8堆栈上限MB)']

# 2) README 字段表补两行(插在 startup_switches 那行之后)
README_ANCHOR_PREFIX = '| `startup_switches` | `{}`（对象）'
README_NEW = [
    '| `dpi_aware` | `false`（bool） | **新增**。为真时启动期调用 `FBrowser_设置程序DPI模式 (按显示器感知V2)`：进程级 DPI 感知，HiDPI 屏上窗口不再被系统位图拉伸。⚠ 副作用：窗口 1000×800 将按**物理像素**解释，CSS 视口变小，鼠标/坐标类工具的观测值随之变化 —— 开启后请重跑坐标相关用例。**仅启动期生效，改动后必须重启进程** |',
    '| `v8_max_stack_mb` | `0`（int） | **新增**。>0 时启动期调用 `FBrowser_初始化_设置V8环境默认堆栈大小 (0, N)`，**只放宽** V8 堆栈上限（深递归/JSVMP 页面防渲染进程崩溃）；`0` = 内核默认（不改动）。上限 4096MB；32 位构建建议 ≤4000。**仅启动期生效，改动后必须重启进程** |',
]

# 3) docs §2.4 表格补两行(插在 startup_switches 那行之后)
DOCS_ANCHOR_PREFIX = '| `startup_switches` | object | `{}` |'
DOCS_NEW = [
    '| `dpi_aware` | bool | `false` | **新增**。启动期调用 `FBrowser_设置程序DPI模式 (按显示器感知V2)`：进程级 DPI 感知（HiDPI 屏上窗口不再被位图拉伸）。⚠ 副作用：窗口按物理像素解释、CSS 视口变小 ⇒ 坐标/鼠标类工具观测值会变，开启后需重跑相关用例。**仅启动期生效，改动后必须重启进程** |',
    '| `v8_max_stack_mb` | int | `0` | **新增**。>0 时启动期调用 `FBrowser_初始化_设置V8环境默认堆栈大小 (0, N)`：**只放宽** V8 堆栈上限（深递归/JSVMP 页面防渲染进程崩溃），`0`=内核默认。校验范围 1..4096。**仅启动期生效，改动后必须重启进程** |',
]


def insert_after_line(lines, prefix, new_lines, label):
    hits = [i for i, l in enumerate(lines) if l.lstrip().startswith(prefix)]
    assert len(hits) == 1, '%s 锚点命中 %d 次' % (label, len(hits))
    s = hits[0]
    return lines[:s + 1] + new_lines + lines[s + 1:], s + 1


def main():
    # 回执
    raw = open(SYS_FILE, 'rb').read()
    assert not raw.startswith(b'\xef\xbb\xbf')
    txt = raw.decode('utf-8')
    assert 'v8_max_stack_mb' not in txt, '回执已改过'
    term = '\r\r\n' if '\r\r\n' in txt else ('\r\n' if '\r\n' in txt else '\n')
    lines = txt.replace(term, '\n').split('\n')
    hits = [i for i, l in enumerate(lines) if l.strip() == RECV_ANCHOR.strip()]
    assert len(hits) == 1, '回执锚点 %d' % len(hits)
    s = hits[0]
    out_sys = lines[:s + 1] + RECV_NEW[1:] + lines[s + 1:]

    # 两份文档
    outs = {}
    for path, prefix, new_lines, label in (
            (README, README_ANCHOR_PREFIX, README_NEW, 'README'),
            (DOCS, DOCS_ANCHOR_PREFIX, DOCS_NEW, '说明书')):
        b = open(path, 'rb').read()
        assert not b.startswith(b'\xef\xbb\xbf')
        t = b.decode('utf-8')
        assert 'dpi_aware' not in t, '%s 已改过' % label
        term2 = '\r\r\n' if '\r\r\n' in t else ('\r\n' if '\r\n' in t else '\n')
        ls = t.replace(term2, '\n').split('\n')
        ls, at = insert_after_line(ls, prefix, new_lines, label)
        outs[path] = ('\n'.join(ls).replace('\n', term2), term2, at + 1)
        print('%-8s 在第 %d 行后插入 %d 行' % (label, at, len(new_lines)))

    if '--apply' in sys.argv:
        with io.open(SYS_FILE, 'w', encoding='utf-8', newline='') as f:
            f.write('\n'.join(out_sys).replace('\n', term))
        for path, (data, _t, _a) in outs.items():
            with io.open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(data)
        print('已写入 3 个文件')
    else:
        print('[dry-run] 未落盘')


main()
