# -*- coding: utf-8 -*-
import importlib.util, sys, time, json, urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
sys.path.insert(0,'.')
spec=importlib.util.spec_from_file_location("v4","verify_round4.py")
v4=importlib.util.module_from_spec(spec); spec.loader.exec_module(v4)

def raw(name, args):
    body=json.dumps({"jsonrpc":"2.0","id":"probe-1","method":"tools/call",
                     "params":{"name":name,"arguments":args}}, ensure_ascii=False).encode()
    req=urllib.request.Request("http://127.0.0.1:9222/mcp", data=body,
                              headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

print("=== 排除'跨请求参数残留': 先设 2.5, 再发空 {} ===")
print("  1) level=2.5 ->", raw("browser_set_zoom", {"level":2.5})["result"]["content"][0]["text"][:90])
time.sleep(0.3)
print("  2) 空 {}    ->", raw("browser_set_zoom", {})["result"]["content"][0]["text"][:90])
print("     若第2步仍为 0 而不是 2.5 => 不是参数残留, 是确定性行为")
print()
print("=== level 键存在但为空串/空值 ===")
for label, args in (("level=''", {"level":""}), ("level=null", {"level":None})):
    r = raw("browser_set_zoom", args)["result"]["content"][0]["text"]
    print("  %-12s -> %s" % (label, r[:90]))
    time.sleep(0.3)
print()
print("=== 还原 ===")
print("  level=1.0 ->", raw("browser_set_zoom", {"level":1.0})["result"]["content"][0]["text"][:90])
print("  get_zoom  ->", raw("browser_get_zoom", {})["result"]["content"][0]["text"][:120])
