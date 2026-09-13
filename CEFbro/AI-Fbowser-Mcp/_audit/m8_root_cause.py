# -*- coding: utf-8 -*-
r"""M8 — 验证 CDP 失效根因 + 检查该工具的危险默认值

假设: 探针用空参数调用 browser_vip_enable_devtools_observer,
      其 enable 缺省为假 -> 注销了 CDP 观察者 -> 所有 CDP 工具失效。
验证: 显式 enable:true 重新开启, 再测 CDP 是否恢复。
同时检查该工具 schema 是否声明 required。
"""
import json, time, urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"


def call(name, args, rid, timeout=25.0):
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
        try:
            txt = res["content"][0]["text"]
        except Exception:
            txt = json.dumps(d, ensure_ascii=False)
        return dt, ("ERR" if res.get("isError") else "OK"), txt[:150].replace("\n", " ")
    except Exception as e:
        return time.time() - t0, ("TIMEOUT" if "timed out" in str(e).lower() else "TRANSPORT"), str(e)[:100]


print("=" * 100)
print("1. schema 检查: browser_vip_enable_devtools_observer")
print("=" * 100)
tools = json.loads(urllib.request.urlopen(BASE + "/tools/list", timeout=20).read().decode("utf-8"))["tools"]
for t in tools:
    if t["name"] in ("browser_vip_enable_devtools_observer", "browser_vip_enable_inspector",
                     "browser_kernel_cdp_monitor"):
        print()
        print("  %s" % t["name"])
        print("    描述: %s" % (t.get("description") or "")[:110])
        s = t.get("inputSchema") or {}
        print("    required: %s" % (s.get("required") or "(未声明)"))
        for pn, pv in (s.get("properties") or {}).items():
            print("      - %-12s %-8s %s" % (pn, pv.get("type"), (pv.get("description") or "")[:60]))

print()
print("=" * 100)
print("2. 修复验证: 显式 enable:true 重新开启 CDP 观察者, 再测 CDP")
print("=" * 100)
dt, st, tx = call("browser_vip_enable_devtools_observer", {"enable": True}, 3001)
print("  开启观察者: %6.2fs %-6s %s" % (dt, st, tx))
time.sleep(1.5)

dt, st, tx = call("browser_cdp_call", {"method": "Browser.getVersion", "max_ms": 10000}, 3002, 20)
print("  之后 Browser.getVersion: %6.2fs %-6s %s" % (dt, st, tx))

time.sleep(0.5)
dt, st, tx = call("browser_debugger_enable", {"max_ms": 10000}, 3003, 20)
print("  之后 debugger_enable   : %6.2fs %-6s %s" % (dt, st, tx))

print()
print("=" * 100)
print("3. 反向验证: 再用空参数调用它, 看是否再次关闭")
print("=" * 100)
dt, st, tx = call("browser_vip_enable_devtools_observer", {}, 3004)
print("  空参数调用: %6.2fs %-6s %s" % (dt, st, tx))
time.sleep(1.0)
dt, st, tx = call("browser_cdp_call", {"method": "Browser.getVersion", "max_ms": 8000}, 3005, 15)
print("  之后 Browser.getVersion: %6.2fs %-6s %s" % (dt, st, tx))
