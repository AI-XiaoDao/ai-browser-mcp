# -*- coding: utf-8 -*-
"""修掉我在 browser_clear_cache_browser 分支里写下的两处笔误: `值 = ""}` 多了一个右花括号。

为什么用脚本而不是 edit: 这两处一模一样, 用 edit 会因"出现多次"被拒; 而且我要顺带打印出现次数
作为可核对证据(改前 2 处 -> 改后 0 处), 不做"静默替换"。
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _console  # noqa: F401

P = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")
BAD = '值 = ""}'
GOOD = '值 = ""'

s = io.open(P, encoding="utf-8").read()
before = s.count(BAD)
print("改前 BAD 出现次数: %d" % before)
if before == 0:
    print("无需修改")
    sys.exit(0)
s = s.replace(BAD, GOOD)
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
after = io.open(P, encoding="utf-8").read().count(BAD)
print("改后 BAD 出现次数: %d" % after)
# 顺带确认那两处声明的完整形态已正确
chk = io.open(P, encoding="utf-8").read()
for key in ('变量 ccBad <类型 = 文本型 值 = ""',
            '变量 ccTypeBad <类型 = 文本型 值 = ""'):
    print("存在 %-42s : %s" % (key[:40], chk.count(key) == 1))
sys.exit(0 if after == 0 else 1)
