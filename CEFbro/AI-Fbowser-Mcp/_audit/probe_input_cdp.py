# -*- coding: utf-8 -*-
"""单个用例: 在**干净实例**上测"某个工具调用之后 CDP 是否还活着"。

用法: py -3 probe_input_cdp.py <工具名> '<JSON参数>'
判据: CDP 存活 = browser_dom_query 耗时 < 2s (CDP 正常 0.0s 级; 死了会白等 ~10s)。
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


def alive():
    e, t, dt = call("browser_dom_query", {"selector": "h1"})
    return dt < 2.0, dt


def main():
    tool = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    call("browser_navigate", {"url": "https://example.com/?in=%d" % int(time.time()),
                              "wait_for_load": True}, 45)
    time.sleep(0.8)
    ok0, dt0 = alive()
    if not ok0:
        print("  BASELINE_DEAD")
        return 2
    e, t, dt = call(tool, args)
    time.sleep(0.5)
    ok1, dt1 = alive()
    print("  %-26s 调用=%.1fs err=%-5s | CDP 基线%.1fs -> 之后%.1fs  %s"
          % (tool, dt, e, dt0, dt1, "存活 ✅" if ok1 else "已死 ❌"))
    print("      调用回复: %s" % t.replace("\n", " ")[:80])
    return 0 if ok1 else 1


if __name__ == "__main__":
    sys.exit(main())
