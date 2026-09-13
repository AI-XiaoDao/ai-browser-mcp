# -*- coding: utf-8 -*-
"""列出指定分派方法体内的全部动作分支 (用于写准确的 inputSchema)。"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

TARGETS = {
    "MCP_Kernel.wsv": ["分派_IPC队列", "分派_CDP监控", "分派_反应器", "分派_定时监视", "分派_全事件流"],
    "MCP_Server_VIP.wsv": ["分派_设置S5代理", "分派_清除S5代理", "分派_VIP鼠标点击",
                           "分派_VIP鼠标移动", "分派_VIP按键按下", "分派_VIP按键抬起",
                           "分派_VIP鼠标滚轮", "分派_VIP按键点击"],
}
ACT = re.compile(r'([\u4e00-\u9fff_A-Za-z][\u4e00-\u9fff_A-Za-z0-9_]*)\s*==\s*"([^"]*)"')
KEY = re.compile(r'yyjson取(?:文本|整数|逻辑|逻辑_默认)\s*\([^,]+,\s*"([^"]+)"')
KEY2 = re.compile(r'yyjson取(?:文本|整数|逻辑|逻辑_默认)\s*\([^,]*,\s*"([^"]+)"')

for f, names in TARGETS.items():
    ms = {m[1]: m for m in find_methods(f)}
    print("=" * 100)
    print(f)
    print("=" * 100)
    for n in names:
        if n not in ms:
            print("\n  !! %s 未找到 (可能方法名不同)" % n)
            continue
        i0, name, sig, b0, b1 = ms[n]
        body = lines_of(f)[0][b0:b1 + 1]
        acts, keys = [], []
        for l in body:
            s = l.strip()
            if s.startswith("//"):
                continue
            for m in ACT.finditer(l):
                if m.group(1) in ("动作", "action"):
                    if m.group(2) not in acts:
                        acts.append(m.group(2))
            for m in KEY2.finditer(l):
                if m.group(1) not in keys:
                    keys.append(m.group(1))
        print("\n  [%s]  L%d  (%d 行)" % (name, i0 + 1, b1 - b0 + 1))
        print("    action 取值 : %s" % (" / ".join(acts) if acts else "(无 action 分支)"))
        print("    读取的参数  : %s" % (", ".join(keys) if keys else "(无)"))
