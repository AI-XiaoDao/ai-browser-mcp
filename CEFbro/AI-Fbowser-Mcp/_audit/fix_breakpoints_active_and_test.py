# -*- coding: utf-8 -*-
"""把被我自己的清场动作关掉的断点重新激活, 然后复测 auto。

背景(自伤记录): `diag_sourceurl_breakpoint.py` 结尾为了清场调了
`Debugger.setBreakpointsActive {active:false}` —— 该状态是**持续生效**的,
于是之后所有新下的断点都不再触发, 表现成"auto 在任意行号都 0 命中",
看起来像产品缺陷, 实际是我的清场动作污染了调试器状态。
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def c(n, a, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or "" for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def unesc(t):
    return t.replace('\\"', '"')


e, t = c("browser_cdp_call", {"method": "Debugger.setBreakpointsActive",
                              "params": json.dumps({"active": True})})
print("重新激活断点: isError=%s %s" % (e, t[:120]))

e, t = c("browser_status", {})
print("实例活性: isError=%s %s" % (e, t[:90]))

for ln in (3, 2):
    e, t = c("browser_debugger_auto", {"breakpoint": "mcp-breakpoint-probe",
                                       "line": ln, "max_ms": 6000, "max_hits": 2})
    print("line=%s isError=%s -> %s" % (ln, e, unesc(t)[:240].replace("\n", " ")))

c("browser_debugger_resume", {})
print("\n(已 resume)")
