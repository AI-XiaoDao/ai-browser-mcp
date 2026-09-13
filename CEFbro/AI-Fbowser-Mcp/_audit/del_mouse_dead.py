# -*- coding: utf-8 -*-
"""删除 browser_mouse_click 分支里"无条件返回之后"的永不可达死代码(2 行)。

依据: 该分支在 如果(kernel==假) 内 CDP 成功后即返回; CDP 失败时落到紧随其后的
      无条件 `返回 (命令失败 ...)`, 于是其后的 `vip_ctrl.高级鼠标_单击(...)` 与
      `返回 (命令成功 "VIP点击...")` 永远执行不到 —— 是上一轮"鼠标改 CDP 优先"时
      留下的残骸(既死代码, 又会让读者误以为还有内核回退)。

自带前置校验: 若这两行不再紧跟在那个无条件失败返回之后, 则中止(不写入)。
"""
import io
import os
import sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, "src", "MCP_Server_Core.wsv")

S = io.open(P, encoding="utf-8").read()
L = S.split("\n")

# 定位: 唯一的 高级鼠标_单击 调用行
idx = [i for i, l in enumerate(L) if "高级鼠标_单击" in l]
if len(idx) != 1:
    print("!! 预期恰好 1 处 高级鼠标_单击, 实际 %d 处 -> 中止" % len(idx))
    sys.exit(2)
i = idx[0]

dead = [i, i + 1]      # 死代码两行
prev = L[i - 1]        # 其前的无条件失败返回

if "vip_ctrl.高级鼠标_单击" not in L[i]:
    print("!! 第 %d 行不是预期的内核点击调用 -> 中止" % (i + 1))
    sys.exit(2)
if "VIP点击" not in L[i + 1] or not L[i + 1].strip().startswith("返回"):
    print("!! 第 %d 行不是预期的 VIP 成功返回 -> 中止" % (i + 2))
    sys.exit(2)
# 前置必须是"无条件"的失败返回(缩进与死代码同层, 且不是 如果/否则 头)
if not prev.strip().startswith("返回 (MCP_响应构建.命令失败"):
    print("!! 死代码之前不是无条件失败返回, 实际为: %s" % prev.strip()[:60])
    sys.exit(2)
if len(prev) - len(prev.lstrip()) != len(L[i]) - len(L[i].lstrip()):
    print("!! 失败返回与死代码缩进不同层, 不能判定为不可达 -> 中止")
    sys.exit(2)

# 再找该分支结束的 '}' 行(i+2), 确认结构如预期
if L[i + 2].strip() != "}":
    print("!! 死代码之后不是分支结束花括号, 实际: %r -> 中止" % L[i + 2])
    sys.exit(2)

new = L[:i] + L[i + 2:]
io.open(P, "w", encoding="utf-8", newline="\n").write("\n".join(new))
print("已删除第 %d-%d 行(共 2 行死代码)" % (i + 1, i + 2))
print("  删除内容1: %s" % L[i].strip())
print("  删除内容2: %s" % L[i + 1].strip()[:70])
print("  保留(其前的无条件失败返回): %s" % prev.strip()[:60] + " ...")
print("行数: %d -> %d" % (len(L), len(new)))
