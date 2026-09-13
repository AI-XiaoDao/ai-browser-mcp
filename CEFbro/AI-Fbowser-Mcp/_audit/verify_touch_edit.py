# -*- coding: utf-8 -*-
"""校验本轮改动是否都落盘(逐条断言, 失败必须打印原文)。"""
import io
import os
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def read(rel):
    return io.open(os.path.join(ROOT, rel), encoding="utf-8").read()


srv = read(r"src\MCP_Server.wsv")
core = read(r"src\MCP_Server_Core.wsv")

checks = [
    ("MCP_Server: 触摸状态变量 触摸点已按下", "变量 触摸点已按下" in srv),
    ("MCP_Server: CDP派发触摸点一次 定义", "方法 CDP派发触摸点一次" in srv),
    ("MCP_Server: CDP派发触摸事件 定义", "方法 CDP派发触摸事件" in srv),
    ("MCP_Server: 触摸仿真自动开启", "Emulation.setTouchEmulationEnabled" in srv),
    ("MCP_Server: touchEnd 空点写法", "\\\"touchPoints\\\":[]" in srv),
    ("MCP_Server: 触摸工具描述已改(缺省经 CDP)", srv.count("缺省经 CDP") >= 3),
    ("MCP_Server: 旧描述(需先 fingerprint)已消失", "需先 fingerprint touch_enable 开启触摸" not in srv),
    ("Core: touch_press 走 CDP", 'MCP命令服务器.CDP派发触摸事件 ("touchStart"' in core),
    ("Core: touch_release 走 CDP", 'MCP命令服务器.CDP派发触摸事件 ("touchEnd"' in core),
    ("Core: touch_move 走 CDP", 'MCP命令服务器.CDP派发触摸事件 ("touchMove"' in core),
    ("Core: 触摸三件套仍有 kernel 开关", core.count('yyjson取逻辑 (参数JSON, "kernel") == 假') >= 3),
    ("Core: 死代码 高级鼠标_单击 已删除", "高级鼠标_单击" not in core),
    ("Core: 死代码 VIP点击 提示已删除", "VIP点击 (" not in core),
]
bad = 0
for name, ok in checks:
    print("%-46s %s" % (name, "OK" if ok else "!!! 失败"))
    if not ok:
        bad += 1

# 触摸三件套分支仍存在且各一份
for m in ("browser_touch_press", "browser_touch_release", "browser_touch_move"):
    n = core.count('方法名 == "%s"' % m)
    print("%-46s %d 处" % (m + " 分支数", n))
    if n != 1:
        bad += 1

print("\n结果: %s" % ("全部通过" if bad == 0 else "%d 项失败" % bad))
