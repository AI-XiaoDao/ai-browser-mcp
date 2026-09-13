# -*- coding: utf-8 -*-
"""browser_dom_set_html 的 DROP 是探针伪失败还是真问题?
上一轮我用 #mcpX(页面上不存在的元素) -> 回 "element not found", 那是**正确的参数校验**,
不能据此判它坏。这里先注入一个真实元素, 再对它 set_html, 并回读验证。
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


def call(n, a, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


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
call("browser_navigate", {"url": "https://example.com/?sh=1", "wait_for_load": True})

print("== 先造一个真实元素 ==")
e, t = call("browser_execute_js",
            {"code": "document.body.insertAdjacentHTML('beforeend','<div id=\"mcpSH\">OLD</div>');'ok'"})
print("   %s | %s" % (e, t[:120]))

print("\n== 对它 set_html(同步后应一次调用即完成) ==")
e, t = call("browser_dom_set_html", {"selector": "#mcpSH", "html": "<i>NEW</i>"})
print("   isError=%s | %s" % (e, t[:250]))

print("\n== 回读验证(不能只听它自己说成功) ==")
e, t = call("browser_dom_inner_html", {"selector": "#mcpSH"})
print("   inner_html -> isError=%s | %s" % (e, t[:200]))
ok = ('NEW' in t)
print("   [%s] 回读到 NEW = 真的写进去了" % ('PASS' if ok else 'FAIL'))
