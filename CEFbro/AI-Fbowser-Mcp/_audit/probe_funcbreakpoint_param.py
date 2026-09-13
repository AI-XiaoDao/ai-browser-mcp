# -*- coding: utf-8 -*-
"""A/B 定案: Debugger.setBreakpointOnFunctionCall 到底要 objectId 还是 functionObjectId?

线索冲突:
  · 源码注释(MCP_Server_Reverse.wsv:219)断言"要求 functionObjectId, 非 objectId"
  · 但第98轮探针用 {"objectId": <真句柄>} 得到过 {"breakpointId":"7:1"}
  · 而工具(发 functionObjectId)现在报 Invalid parameters
只能让内核自己说话: 两臂对照。
"""
import json
import os
import re
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


def c(n, a, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


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
c("browser_navigate", {"url": "https://example.com/?funcbp=1", "wait_for_load": True})
c("browser_debugger_enable", {"action": "enable"})

print("== 取一个真实函数 objectId(parseInt) ==")
e, t = c("browser_cdp_call", {"method": "Runtime.evaluate",
                              "params": {"expression": "parseInt", "returnByValue": False}})
m = re.search(r'"objectId":"([^"]+)"', t)
oid = m.group(1) if m else ""
print("   objectId = %r" % oid)

if oid:
    for label, key in (("A 用 objectId(源码注释说不行)", "objectId"),
                       ("B 用 functionObjectId(工具现在发的)", "functionObjectId")):
        print("\n== %s ==" % label)
        print("   %s" % c("browser_cdp_call",
                          {"method": "Debugger.setBreakpointOnFunctionCall",
                           "params": {key: oid}})[1][:300])

print("\n== 收尾: 清掉可能装上的断点 ==")
print("   setSkipAllPauses -> %s" % c("browser_cdp_call",
                                      {"method": "Debugger.setSkipAllPauses",
                                       "params": {"skip": True}})[1][:120])
