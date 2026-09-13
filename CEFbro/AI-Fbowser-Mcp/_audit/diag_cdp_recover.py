# -*- coding: utf-8 -*-
"""确认"哪些输入类工具会打死 CDP", 以及**能否恢复**(目标 ≤60 秒)。

已复现: browser_mouse_move {x:400,y:300} 之后 browser_dom_query 从 0.0s 变 10.3s(null)。
本脚本:
  1) 用同一实例后续测试"恢复手段"是否有效(注销+重注册监管者 / 重新导航 / 等待);
  2) 输出结论, 供决定修法(自动恢复 or 仅告警)。
"""
import json
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"


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


def cdp(tag):
    e, t, dt = call("browser_dom_query", {"selector": "h1"})
    alive = dt < 2.0
    print("    [CDP %s] %-38s %5.1fs %s" % ("存活" if alive else "已死", tag, dt,
                                           t.replace("\n", " ")[:50]))
    return alive


print("== 预检 ==")
try:
    h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
    print("  tools=%s latency_max=%s" % (h.get("tool_count"), h.get("latency_max_ms")))
except Exception as ex:
    print("  !! 服务未就绪(%s)" % ex)
    sys.exit(2)

call("browser_navigate", {"url": "https://example.com/?rc=%d" % int(time.time()),
                          "wait_for_load": True}, 45)
time.sleep(0.8)
if not cdp("基线"):
    print("  !! 基线 CDP 就不可用, 作废")
    sys.exit(2)

print("\n== 触发: browser_mouse_move ==")
e, t, dt = call("browser_mouse_move", {"x": 400, "y": 300})
print("  %5.1fs err=%s %s" % (dt, e, t.replace("\n", " ")[:60]))
time.sleep(0.5)
if cdp("mouse_move 之后"):
    print("  !! 本次未复现失效(可能偶发), 仍继续测恢复手段")
    sys.exit(0)

print("\n== 恢复尝试 ==")
print("  1) 注销 + 重注册 CDP 监管者")
call("browser_vip_enable_inspector", {"enable": False})
time.sleep(1.0)
call("browser_vip_enable_inspector", {"enable": True})
time.sleep(2.0)
cdp("注销+重注册之后")

print("  2) 重新导航")
call("browser_navigate", {"url": "https://example.com/?rc2=%d" % int(time.time()),
                          "wait_for_load": True}, 45)
time.sleep(2.0)
cdp("重新导航之后")

print("  3) 再等 5 秒(看是否自愈)")
time.sleep(5)
cdp("等待 5 秒之后")

print("  4) 主动发一次 CDP 调用后立即再探(看是否只是首次慢)")
call("browser_dom_query", {"selector": "h1"})
time.sleep(0.5)
cdp("二次 CDP 调用之后")

h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
print("\n  health: cdp_ready=%s latency_max=%s" % (h.get("cdp_ready"),
                                                   h.get("latency_max_ms")))
