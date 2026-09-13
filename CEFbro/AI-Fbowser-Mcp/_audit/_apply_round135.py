# -*- coding: utf-8 -*-
r"""第135轮: 统一"用户给的路径被安全守卫拒绝"的报错文案 —— 全部改成**可行动**。

现状(本轮 `_audit/_show_path_guard_msgs.py` 实测列出 10 处守卫):
  · 只有 VIP 的两处写清了规则(`| 仅允许运行目录内及无 .. 的路径`);
  · 6 处只说"不允许/不合法"却不说什么允许 —— 调用方只能猜(如 `路径不允许: D:\\x.js`);
  · 2 处没有工具级文案(`解码JS代码` 由调用方兜底=上一轮已改成可行动; 资源过滤器的 replace_file
    越界时把原因写进被替换的响应体 `资源已屏蔽 (replace_file: 文件路径越界)` —— 属请求期回调, 合理)。
处理: 给那 6 处统一追加同一句**可行动**说明(允许范围 + 怎么办), 措辞与 VIP 两处保持一致。

用法: py -3 _audit\_apply_round135.py [--apply]
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HINT = ' | 允许范围: 进程运行目录内的路径(且不得含 ..); 请把文件放到运行目录下再试'
TARGETS = [
    ('MCP_Server_Core.wsv', '"路径不允许: " + 路径'),
    ('MCP_Server_Core.wsv', '"路径安全校验失败: " + 路径'),
    ('MCP_Server_Core.wsv', '"文件路径不允许: " + expression'),
    ('MCP_Server_Core.wsv', '"file_path 不合法 | 路径遍历或非法字符: " + file_path'),
    ('MCP_Server_Core.wsv', '"path 不合法: " + fdPath'),
    ('MCP_Server_Reverse.wsv', '"文件路径不合法: " + plFile'),
]


def enclosing_tool(lines, i):
    for j in range(i, -1, -1):
        if '方法名 ==' in lines[j]:
            return lines[j].strip()[:60]
    return '(未找到工具名)'


def main():
    by_file = {}
    for fn, anchor in TARGETS:
        by_file.setdefault(fn, []).append(anchor)
    for fn, anchors in by_file.items():
        path = os.path.join(ROOT, 'src', fn)
        lines = io.open(path, encoding='utf-8').read().split('\n')
        for anchor in anchors:
            hits = [i for i, ln in enumerate(lines) if anchor in ln]
            assert len(hits) == 1, '%s / %s 命中 %d 处' % (fn, anchor, len(hits))
            i = hits[0]
            assert HINT not in lines[i], '%s 已改过' % anchor
            lines[i] = lines[i].replace(anchor, anchor + ' + "' + HINT + '"', 1)
            print('%s:%d  [%s]  → 已追加可行动说明' % (fn, i + 1, enclosing_tool(lines, i)))
        out = '\n'.join(lines)
        if '--apply' in sys.argv:
            io.open(path, 'w', encoding='utf-8', newline='\n').write(out)
            chk = io.open(path, encoding='utf-8').read()
            assert HINT.strip() in chk
            print('   %s 已写入并回读校验通过' % fn)
    if '--apply' not in sys.argv:
        print('[dry-run] 未落盘 (加 --apply 才写)')


main()
