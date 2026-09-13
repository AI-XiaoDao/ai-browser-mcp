# -*- coding: utf-8 -*-
r"""M7 — CDP 通道健康度隔离测试

已知: browser_debugger_enable/reverse_strings/reverse_extract 单独调用均卡在内部超时。
需要判定: 是 CDP 通道坏了, 还是 JS 注入通道坏了, 还是页面上下文问题。

分层测试:
  T1 browser_cdp_call {method:"Browser.getVersion"}   —— 纯 CDP 往返(不需页面)
  T2 browser_cdp_call {method:"Runtime.evaluate", ...} —— CDP 里执行 JS(需页面上下文)
  T3 browser_evaluate {code:"1+1"}                     —— 项目的 JS 注入通道(走CEF回调)
  T4 browser_get_url / browser_status                   —— 基础状态(对照基线)
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
        return dt, ("ERR" if res.get("isError") else "OK"), txt[:170].replace("\n", " ")
    except Exception as e:
        return time.time() - t0, ("TIMEOUT" if "timed out" in str(e).lower() else "TRANSPORT"), str(e)[:110]


print("=" * 100)
print("M7 CDP 通道健康度隔离测试")
print("=" * 100)
print()

# T0 环境
print("--- T0 当前环境 ---")
for nm, args in [("browser_get_url", {}), ("browser_status", {}),
                 ("browser_get_title", {}), ("mcp_status", {})]:
    dt, st, tx = call(nm, args, 2000, 20)
    print("  %-20s %6.2fs  %-6s %s" % (nm, dt, st, tx[:120]))
    time.sleep(0.3)

print()
print("--- T1 纯 CDP 往返 (Browser.getVersion, 不需页面上下文) ---")
dt, st, tx = call("browser_cdp_call", {"method": "Browser.getVersion", "max_ms": 12000}, 2101, 25)
print("  %6.2fs  %-6s %s" % (dt, st, tx))

print()
print("--- T2 CDP 内执行 JS (Runtime.evaluate) ---")
dt, st, tx = call("browser_cdp_call",
                  {"method": "Runtime.evaluate",
                   "params": "{\"expression\":\"1+1\",\"returnByValue\":true}",
                   "max_ms": 12000}, 2102, 25)
print("  %6.2fs  %-6s %s" % (dt, st, tx))

print()
print("--- T3 项目 JS 注入通道 (browser_evaluate, 走 CEF 回调不走 CDP) ---")
dt, st, tx = call("browser_evaluate", {"code": "1+1", "max_ms": 12000}, 2103, 25)
print("  %6.2fs  %-6s %s" % (dt, st, tx))

print()
print("--- T4 项目 JS 注入通道 (browser_execute_js) ---")
dt, st, tx = call("browser_execute_js", {"code": "document.title"}, 2104, 25)
print("  %6.2fs  %-6s %s" % (dt, st, tx))

print()
print("=" * 100)
print("判定矩阵")
print("=" * 100)
print("""
  T1 通 T2 通  -> CDP 通道正常, debugger_enable 超时另有原因(如 Debugger.enable 被安全策略拦)
  T1 通 T2 不通-> CDP 命令通道正常, 但页面 JS 上下文不可用(页面是纯文本 md)
  T1 不通      -> CDP 观察者/监管者事件通道已失效
  T3/T4 通     -> CEF JS 回调通道正常(与 CDP 无关的独立通道)
""")
