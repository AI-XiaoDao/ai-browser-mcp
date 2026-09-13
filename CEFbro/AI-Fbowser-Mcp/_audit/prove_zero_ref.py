# -*- coding: utf-8 -*-
"""零引用方法的**删除前证据固定**: 对每个候选, 逐条证实"真的没人调用"。

判据(缺一不可):
  ① 16 个项目源文件里, 除定义行外没有任何出现(含字符串形式的动态调用);
  ② 没有 `<接收事件>` / `@虚拟方法 = 可覆盖` 这类**由框架按符号绑定**的标注;
  ③ 没有出现在 `@` 开头的内嵌 C++ 行里(那种调用不写方法名, 而是写符号名, 也一并查);
  ④ 不是分派入口(分派入口由路由器以字符串调用, 名字会出现在别处)。
同时打印每个方法的定义行原文, 便于人工确认是否还有别的用途。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

FILES = [
    "main.wsv", "MCP_Server.wsv", "MCP_Server_Core.wsv", "MCP_Server_HTTP.wsv",
    "MCP_Server_System.wsv", "MCP_Server_Form.wsv", "MCP_Server_VIP.wsv",
    "MCP_Server_Workflow.wsv", "MCP_Server_Reverse.wsv", "MCP_Stdio.wsv",
    "MCP_Kernel.wsv", "MCP_BrowserEvents.wsv", "MCP_Callbacks.wsv",
    "MCP_Constants.wsv", "MCP_ResponseBuilders.wsv", "MCP_Server_Utils.wsv",
]

CAND = [
    ("MCP_Server.wsv", 124, "尝试恢复欢迎页导航"),
    ("MCP_Server.wsv", 163, "尝试导航欢迎页"),
    ("MCP_Server.wsv", 3606, "CDP获取脚本源"),
    ("MCP_Server.wsv", 5225, "分派网络日志命令"),
    ("MCP_Server.wsv", 7083, "解析匹配模式"),
    ("MCP_Server.wsv", 7652, "记录网络日志项"),
    ("MCP_Server.wsv", 7945, "规范化URL"),
    ("MCP_Server.wsv", 9413, "发送CORS500响应"),
    ("MCP_Stdio.wsv", 327, "缓存线程类_线程运行"),
]

texts = {}
for f in FILES:
    p = os.path.join(SRC, f)
    if os.path.exists(p):
        texts[f] = open(p, 'rb').read().decode('utf-8').split('\n')

all_lines = [(f, i + 1, ln) for f, ls in texts.items() for i, ln in enumerate(ls)]
joined = "\n".join(ln for _, _, ln in all_lines)

for fn, line, name in CAND:
    ls = texts.get(fn)
    if not ls:
        print('!! 读不到 %s' % fn)
        continue
    defln = ls[line - 1] if line - 1 < len(ls) else '(行号越界)'
    occ = []
    for f, i, ln in all_lines:
        if name in ln:
            occ.append((f, i))
    in_at = [x for x in occ if all_lines[[k for k, (a, b, _) in enumerate(all_lines)
                                          if a == x[0] and b == x[1]][0]][2].lstrip().startswith('@')]
    # 事件/虚方法标注: 看定义行的前 8 行内是否有标注
    head = "\n".join(ls[max(0, line - 9):line])
    ev = ('<接收事件' in head) or ('@虚拟方法' in head)
    print('=' * 100)
    print('%s:%d  %s' % (fn, line, name))
    print('   定义: %s' % defln.strip()[:150])
    print('   项目内出现 %d 处: %s' % (len(occ), occ[:8]))
    print('   框架绑定标注(前8行): %s | 出现在 @ 行: %s' % ('有' if ev else '无',
                                                          in_at if in_at else '无'))
