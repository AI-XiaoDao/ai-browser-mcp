# -*- coding: utf-8 -*-
"""查一个可疑现象: `browser_debugger_disable` / `browser_debugger_stop` 调用后
`isError=False` 但**正文为空** —— 这可能是"未知工具名被静默当成成功"(协议级缺陷)。

判据:
  ① 这两个名字在 tools/list 里吗?
  ② 故意传一个**绝不存在**的工具名, 看回包是"报错"还是"空成功"。
     若空成功 ⇒ 任何拼错工具名的调用都会被上游当作成功, 属严重诚实性缺陷。
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def rpc(method, params=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        b["params"] = params
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))


o = rpc("tools/list")
names = [t.get("name") for t in (o.get("result") or {}).get("tools") or []]
print('工具总数 %d' % len(names))
for n in ("browser_debugger_disable", "browser_debugger_stop", "browser_debugger_enable",
          "browser_debugger_wait_paused"):
    print('   %-32s 在清单里? %s' % (n, n in names))
print()
print('含 debugger 的工具: %s' % [n for n in names if 'debugger' in n])

print('\n== 传一个绝不存在的工具名 ==')
o = rpc("tools/call", {"name": "browser_this_tool_does_not_exist_zzz", "arguments": {}})
print(json.dumps(o, ensure_ascii=False)[:700])

print('\n== 传一个存在但空参的工具(对照) ==')
o = rpc("tools/call", {"name": "browser_status", "arguments": {}})
print(json.dumps(o, ensure_ascii=False)[:300])

print('\n== 直接查那两个名字 ==')
for n in ("browser_debugger_disable", "browser_debugger_stop"):
    o = rpc("tools/call", {"name": n, "arguments": {}})
    print('   %-30s -> %s' % (n, json.dumps(o, ensure_ascii=False)[:260]))
