# -*- coding: utf-8 -*-
"""定位"CDP 通道何时开始失效"（目标 ≤30 秒）。

背景: 里程碑全量跑时, 前三个套件全绿, 从 probe_coercion 起全面退化 ——
  该状态实测: browser_dom_query / get_text 各 10.3s(正好是它们内部的 CDP 等待超时),
  browser_execute_js 30.1s(同步等待_JS执行超时), health.latency_max_ms=35453。
结论方向: **CDP 响应不再回来**, 于是每个走 CDP 的工具都要白等满超时。

本脚本在**干净实例**上逐个调用可疑工具, 每次之后探测 CDP 是否还活着:
  判据 = browser_dom_query 的耗时 —— CDP 正常时应为 0.0s 级; 若跳到 ~10s 即"已死"。
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


def cdp_health(tag):
    """CDP 是否还活着: 看 dom_query 的耗时(正常 0.0s 级, 死了会白等 ~10s)。"""
    e, t, dt = call("browser_dom_query", {"selector": "h1"})
    alive = dt < 2.0
    print("    [CDP %s] %-34s %5.1fs %s" % ("存活" if alive else "已死", tag, dt,
                                            t.replace("\n", " ")[:60]))
    return alive


print("== 预检 ==")
try:
    h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
    print("  tools=%s cdp=%s latency_max=%s" % (h.get("tool_count"), h.get("cdp_ready"),
                                                h.get("latency_max_ms")))
except Exception as ex:
    print("  !! 服务未就绪(%s)" % ex)
    sys.exit(2)

call("browser_navigate", {"url": "https://example.com/?pd=%d" % int(time.time()),
                          "wait_for_load": True}, 45)
time.sleep(0.8)
if not cdp_health("基线"):
    print("  !! 基线 CDP 就不可用, 本实验作废")
    sys.exit(2)

# 逐个可疑调用: 每次之后立刻探 CDP
SUSPECTS = [
    ("browser_mouse_move", {"x": 400, "y": 300}),
    ("browser_scroll_by", {"x": 0, "y": 100}),
    ("browser_mouse_click", {"x": 200, "y": 200}),
    ("browser_reload", {"wait_for_load": True}),
    ("browser_fingerprint_online", {"value": True}),
    ("browser_execute_js", {"code": "1+1"}),
    ("browser_dom_set_value", {"selector": "h1", "value": "x"}),
]

dead_at = None
for name, args in SUSPECTS:
    e, t, dt = call(name, args)
    print("  [调用] %-28s %5.1fs err=%-5s %s" % (name, dt, e, t.replace("\n", " ")[:52]))
    time.sleep(0.4)
    if not cdp_health("after " + name):
        dead_at = name
        break

print()
if dead_at:
    print("  => CDP 在调用 **%s** 之后失效" % dead_at)
    print("     (可据此缩小根因; 注意也可能是多次调用累积所致, 需再单独复现确认)")
else:
    print("  => 以上单次调用均未使 CDP 失效 —— 退化更可能是**多次调用累积**或特定组合所致")
    h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
    print("     health: latency_max=%s async=%s" % (h.get("latency_max_ms"),
                                                    h.get("async_tasks")))
