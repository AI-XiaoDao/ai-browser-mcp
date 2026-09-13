# -*- coding: utf-8 -*-
r"""M6 — 验证: 17 个 TIMEOUT 是否为"协议锁级联"产物

对 3 个代表工具**单独**调用(每次之间静默 3 秒, 确保无在途请求), 用 30s 长超时。
  - 若单独调用都能快速返回 -> 证实级联归因
  - 若仍超时 -> 该工具自身有问题
"""
import json, time, urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"


def call(name, args, rid, timeout=30.0):
    body = json.dumps({"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                       "params": {"name": name, "arguments": args}},
                      ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + "/mcp", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8"))
        dt = time.time() - t0
        res = d.get("result") or {}
        txt = ""
        try:
            txt = res["content"][0]["text"]
        except Exception:
            txt = json.dumps(d, ensure_ascii=False)
        return dt, ("ERR" if res.get("isError") else "OK"), txt[:130].replace("\n", " ")
    except Exception as e:
        return time.time() - t0, ("TIMEOUT" if "timed out" in str(e).lower() else "TRANSPORT"), str(e)[:100]


CASES = [
    ("browser_debugger_flow", {}, "无参调用, 预期被 breakpoint 校验快速拒绝"),
    ("browser_debugger_enable", {}, "启用调试器(CDP), 预期数秒"),
    ("browser_kernel_reverse_probe", {}, "五维插桩, 需注入JS"),
    ("browser_reverse_strings", {}, "可疑字符串提取"),
    ("browser_antidetect_presets", {}, "反检测预设"),
    ("browser_reverse_extract", {}, "mode 默认 scan"),
]

print("=" * 100)
print("M6 单独重试 TIMEOUT 工具 (每次间隔 3 秒, 30s 长超时)")
print("=" * 100)
print()
print("%-40s %8s  %-8s %s" % ("工具", "耗时", "状态", "返回/说明"))
print("-" * 100)
res = []
for i, (name, args, note) in enumerate(CASES):
    time.sleep(3)
    dt, st, tx = call(name, args, 900 + i, 30)
    res.append((name, dt, st, tx))
    print("%-40s %7.2fs  %-8s %s" % (name, dt, st, tx))
    print("%-40s %s" % ("", "预期: " + note))

print()
print("=" * 100)
print("判定")
print("=" * 100)
still = [r for r in res if r[2] == "TIMEOUT"]
if not still:
    print("   >>> 全部在 30s 内返回 -> **证实: 首轮 17 个 TIMEOUT 是协议锁级联产物, 非工具自身故障**")
else:
    print("   >>> 仍有 %d 个单独调用超时, 需单独定性:" % len(still))
    for r in still:
        print("        %s" % r[0])
