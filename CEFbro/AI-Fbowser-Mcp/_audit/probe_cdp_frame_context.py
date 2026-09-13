# -*- coding: utf-8 -*-
r"""探针: 用 CDP 在**指定 iframe 的执行上下文**里求值, 能否读到 iframe 内部 DOM?

若可行 ⇒ ① 今天就有可用的逃生通道给 AI(`browser_cdp_call` 两连发);
          ② 下一轮把它包成 `browser_execute_js {frame_id}` 是有把握的(有本机证据)。
步骤: Page.createIsolatedWorld {frameId} -> 取 executionContextId -> Runtime.evaluate {contextId}。
注意: 本项目 `browser_cdp_call` 是**全量透传**, 故这两步都能直接发。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    if o.get("error"):
        return True, "JSONRPC_ERROR: " + json.dumps(o["error"], ensure_ascii=False)
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


call("browser_navigate", {"url": "https://example.com/?cdpframe=%d" % int(time.time()),
                          "wait_for_load": True})
call("browser_execute_js", {"code":
     "document.body.insertAdjacentHTML('beforeend',"
     "'<iframe id=\"f1\" name=\"mcpfr2\" srcdoc=\"<p id=inner>FROM_IFRAME</p>\"></iframe>');'ok'"})
time.sleep(1.0)

e, t = call("browser_get_frames", {})
frames = []
try:
    frames = json.loads(t).get("frames") or []
except Exception as ex:
    print('解析 frames 失败: %r' % ex)
sub = next((f for f in frames if f.get('is_main') is False), None)
fid = (sub or {}).get('id')
print('子框架 id = %r' % fid)

print('\n== ① Page.createIsolatedWorld {frameId} ==')
e1, t1 = call("browser_cdp_call", {"method": "Page.createIsolatedWorld",
                                   "params": {"frameId": fid, "worldName": "mcp_probe",
                                              "grantUniversalAccess": True}}, 40)
print('   isError=%s %s' % (e1, t1[:300]))
ctx = None
import re
m = re.search(r'"executionContextId":\s*(\d+)', t1.replace('\\"', '"'))
if m:
    ctx = m.group(1)
print('   executionContextId = %s' % ctx)

print('\n== ② Runtime.evaluate {contextId, expression} ==')
if ctx:
    e2, t2 = call("browser_cdp_call", {"method": "Runtime.evaluate",
                                       "params": {"expression":
                                                  "(function(){var e=document.getElementById('inner');"
                                                  "return 'CTX_OK:'+(e?e.textContent:'__NO_ELEM__')})()",
                                                  "contextId": int(ctx),
                                                  "returnByValue": True}}, 40)
    print('   isError=%s %s' % (e2, t2[:400]))
    ok = 'CTX_OK:FROM_IFRAME' in t2.replace('\\"', '"')
    print('\n   [%s] 在 iframe 上下文里读到了 iframe 内部 DOM' % ('PASS' if ok else 'FAIL'))
else:
    print('   (没拿到 executionContextId, 无法继续)')

print('\n== ③ 对照: 主框架求值读同一个选择器(应为空/无元素) ==')
e3, t3 = call("browser_execute_js", {"code":
     "(function(){var e=document.getElementById('inner');return e?e.textContent:'__NO_ELEM_IN_MAIN__'})()"})
print('   %s' % t3[:200])
