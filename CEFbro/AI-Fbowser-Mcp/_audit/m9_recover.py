# -*- coding: utf-8 -*-
r"""M9 — CDP 失效是否可恢复? (新浏览器实例 vs 原实例)"""
import json, time, urllib.request

BASE = "http://127.0.0.1:9222"


def call(name, args, rid, timeout=20.0):
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
        return dt, ("ERR" if res.get("isError") else "OK"), txt[:140].replace("\n", " ")
    except Exception as e:
        return time.time() - t0, ("TIMEOUT" if "timed out" in str(e).lower() else "TRANSPORT"), str(e)[:90]


print("=== 0. 现状: CDP 在原实例上 ---")
print("  cdp Browser.getVersion: %6.2fs %-6s %s" % call("browser_cdp_call",
      {"method": "Browser.getVersion", "max_ms": 6000}, 4001, 12))

print()
print("=== 1. 新建浏览器 (browser_create) ===")
dt, st, tx = call("browser_create", {"url": "about:blank"}, 4002, 25)
print("  %6.2fs %-6s %s" % (dt, st, tx))
time.sleep(2.0)

print()
print("=== 2. 列出浏览器 ===")
dt, st, tx = call("browser_list", {}, 4003, 15)
print("  %6.2fs %-6s %s" % (dt, st, tx))

print()
print("=== 3. 在新实例上测 CDP (指定 browser_id) ===")
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
newid = None
m = re.search(r'"id":(\d+)', tx)
if m:
    newid = int(m.group(1))
if newid:
    dt, st, tx2 = call("browser_cdp_call",
                       {"method": "Browser.getVersion", "browser_id": newid, "max_ms": 8000},
                       4004, 15)
    print("  新实例 id=%d -> %6.2fs %-6s %s" % (newid, dt, st, tx2))
else:
    print("  未能解析新实例 id, 用 -- 直接重试")

print()
print("=== 4. 结论 ===")
print("  若新实例 CDP 通 -> 失效仅限原实例, 需 browser_create 或重启进程恢复")
print("  若新实例 CDP 也不通 -> 进程级 CDP 通道已废, 只能重启进程")
