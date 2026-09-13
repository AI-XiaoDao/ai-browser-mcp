# -*- coding: utf-8 -*-
"""打击面测定: 哪些输入类调用会打死 CDP(每个用例都换**干净实例**)。

为什么全在 Python 里做: 之前用 PowerShell 传 JSON 参数, 单引号与 \\" 被 shell 吃掉导致
json.loads 失败(本会话第 N 次踩 shell 转义)。改为 Python 内部 subprocess 重启应用, 彻底避开。
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')


def call(name, args, timeout=45):
    t0 = time.time()
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                                      "method": "tools/call",
                                                      "params": {"name": name,
                                                                 "arguments": args}},
                                                     ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def restart():
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)
    subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        time.sleep(1)
        try:
            urllib.request.urlopen(BASE + '/health', timeout=3).read()
            time.sleep(3.5)
            return True
        except Exception:
            pass
    return False


def cdp_alive():
    e, t, dt = call("browser_dom_query", {"selector": "h1"})
    return dt < 2.0, dt


CASES = [
    ("CDP派发鼠标 Input.dispatchMouseEvent", "browser_cdp_call",
     {"method": "Input.dispatchMouseEvent",
      "params": json.dumps({"type": "mouseMoved", "x": 400, "y": 300})}),
    ("内核注入 鼠标移动 browser_mouse_move", "browser_mouse_move",
     {"x": 400, "y": 300}),
    ("内核注入 鼠标点击 browser_mouse_click", "browser_mouse_click",
     {"x": 200, "y": 200}),
    ("内核注入 鼠标滚轮 browser_mouse_wheel", "browser_mouse_wheel",
     {"x": 100, "y": 100, "delta_y": 120}),
    ("对照: 纯读 browser_get_title", "browser_get_title", {}),
]

print("=== 打击面测定(每例换干净实例) ===")
rows = []
for label, tool, args in CASES:
    if not restart():
        rows.append((label, "启动失败", "", ""))
        print("  %-42s 启动失败" % label)
        continue
    call("browser_navigate", {"url": "https://example.com/?m=%d" % int(time.time()),
                              "wait_for_load": True}, 45)
    time.sleep(0.6)
    ok0, dt0 = cdp_alive()
    if not ok0:
        rows.append((label, "基线CDP已死", "%.1f" % dt0, ""))
        print("  %-42s 基线CDP已死 -> 作废" % label)
        continue
    e, t, dt = call(tool, args)
    time.sleep(0.5)
    ok1, dt1 = cdp_alive()
    verdict = "CDP 存活 ✅" if ok1 else "CDP 已死 ❌"
    rows.append((label, verdict, "%.1f" % dt0, "%.1f" % dt1))
    print("  %-42s %-12s 调用%.1fs | CDP %.1f -> %.1f | %s"
          % (label, verdict, dt, dt0, dt1, t.replace("\n", " ")[:44]))

print()
print("=== 结论 ===")
for label, verdict, a, b in rows:
    print("  %-42s %s" % (label, verdict))
