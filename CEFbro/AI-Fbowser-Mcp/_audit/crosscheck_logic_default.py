# -*- coding: utf-8 -*-
"""交叉验证 `yyjson取逻辑_默认` 缺键回落是否真的失效(决定这是"单点缺陷"还是"系统性缺陷")。

背景: `browser_debugger_wait_paused` 的 `fresh`(默认假) 明显被当成了真(它把要等的暂停事件清掉)。
若该读取器对**缺失键**不回落, 那么所有真实默认=假的调用点都会被反转。其中
`browser_reverse_network_conditions` 的 `offline`(默认假) 最危险 —— 反转就等于**把浏览器断网**,
而它的**响应文案里自带 offline 的取值**, 因此一次调用就能判定(还顺便验证是否真有断网副作用)。
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')


def call(name, args, timeout=30):
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


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).read()
        time.sleep(4.5)
        break
    except Exception:
        pass

print("== 1) 基线: 先确认网络可用(能导航) ==")
e, t, dt = call("browser_navigate", {"url": "https://example.com/", "wait_for_load": True}, 40)
print("  navigate: %s %.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:70]))

print("\n== 2) 空参调用 browser_reverse_network_conditions(offline 缺省, 期望 false) ==")
e, t, dt = call("browser_reverse_network_conditions", {}, 30)
print("  %s %.2fs" % ("ERR" if e else "OK", dt))
print("  响应: %s" % t.replace("\n", " ")[:260])
off_true = "offline=true" in t or "offline\": true" in t
print("  >>> offline 被当成: %s" % ("真(读取器缺键回落失效 -> 系统性缺陷!)" if off_true
                                     else "假(读取器工作正常)"))

print("\n== 3) 副作用核对: 现在还能不能上网(断网会立刻暴露) ==")
e, t, dt = call("browser_navigate", {"url": "https://example.com/?after=%d" % int(time.time()),
                                     "wait_for_load": True}, 40)
print("  再次导航: %s %.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:90]))

print("\n== 4) 恢复不限速, 收尾 ==")
e, t, _ = call("browser_reverse_network_conditions",
               {"offline": False, "latency": 0,
                "download_throughput": -1, "upload_throughput": -1}, 30)
print("  恢复: %s %s" % ("ERR" if e else "OK", t.replace("\n", " ")[:90]))
subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("\n  已关闭")
