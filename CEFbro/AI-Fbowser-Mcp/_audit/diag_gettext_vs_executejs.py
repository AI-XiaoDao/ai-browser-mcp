# -*- coding: utf-8 -*-
"""同一个 JS 片段, 分别经 browser_execute_js 与 browser_get_text, 看差在哪。

`browser_execute_js` 与 `browser_get_text` 的取值链在源码里是**同构的**
(都是 CDP执行JS并等待 → 取不到再走原生 取安全主框架+执行JS代码_带返回值)。
所以如果同一个片段经前者能拿到值、经后者拿不到, 差别只可能在:
  · get_text 自己拼的那段 JS(含 简单转义JS 对 selector 的处理);
  · 或 get_text 对返回值做的额外判断(`!= ""` / `!= "null"` / `!= "undefined"` / 不以 {"error" 开头)。
本脚本把这两点分开测。
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


def show(tag, e, t, dt):
    print("  %-52s %-4s %6.2fs %s" % (tag, "ERR" if e else "OK", dt,
                                      t.replace("\n", " ")[:100]))


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

call("browser_navigate", {"url": "https://example.com/?cmp=main", "wait_for_load": True}, 45)
time.sleep(0.4)
call("browser_create", {"url": "https://example.com/?cmp=second", "background": True}, 60)
time.sleep(1.0)

print("== 第二个浏览器上的同一片段, 两条路径对照 ==")
SNIPPET = ("(function(){var e=document.querySelector('h1');"
           "return e?e.textContent:'__MCP_NO_ELEM__'})()")
show("execute_js(id=2) 用 get_text 同款片段",
     *call("browser_execute_js", {"code": SNIPPET, "browser_id": 2}))
show("execute_js(id=2) 简化版 querySelector('h1').textContent",
     *call("browser_execute_js",
           {"code": "document.querySelector('h1').textContent", "browser_id": 2}))
show("execute_js(id=2) 直接返回 JSON.stringify 包裹",
     *call("browser_execute_js",
           {"code": "'['+document.querySelector('h1').textContent+']'", "browser_id": 2}))
show("get_text {selector:'h1', browser_id:2}",
     *call("browser_get_text", {"selector": "h1", "browser_id": 2}))

print("\n== 主浏览器同样三连(对照) ==")
show("execute_js(主) 同款片段", *call("browser_execute_js", {"code": SNIPPET}))
show("get_text {selector:'h1'} (主)", *call("browser_get_text", {"selector": "h1"}))

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("\n  已关闭")
