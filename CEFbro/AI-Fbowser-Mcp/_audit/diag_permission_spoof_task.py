# -*- coding: utf-8 -*-
"""browser_permission_spoof 的异步任务到底会不会完成?

第100轮把它纳入同步后 **20s 超时**, 只能撤回。两种可能:
  ① 任务其实很快就完成了, 只是结果存到了**别的 id**(同步等待等的 id 拿不到) -> 修 id 即可
  ② 任务**永远停在 _waiting**            -> 那"权限API伪装已注入"的回执本身就是**假成功**
本脚本: 异步调用拿到 task_id, 然后连续轮询 mcp_result, 看它是否最终收敛为非 _waiting。
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
call("browser_navigate", {"url": "https://example.com/?ps=1", "wait_for_load": True})

print("== 1) 异步调用 ==")
e, t = call("browser_permission_spoof", {"action": "apply", "async_only": True}, 60)
print("   isError=%s | %s" % (e, t[:300]))
m = re.search(r'"task_id"\s*:\s*"([^"]+)"', t)
tid = m.group(1) if m else ''
print("   task_id = %r" % tid)

if tid:
    print("\n== 2) 轮询 12 次(每次 1s), 看是否收敛为非 _waiting ==")
    for i in range(12):
        time.sleep(1.0)
        e2, t2 = call("mcp_result", {"request_id": tid}, 40)
        flag = '仍是 _waiting' if ('_waiting' in t2) else '已收敛'
        print("   [%2d] %-14s %s" % (i + 1, flag, t2[:170].replace('\n', ' ')))

print("\n== 3) 独立回读: 页面上的权限是否真的被伪装了 ==")
e3, t3 = call("browser_evaluate",
              {"code": "(async()=>{try{const p=await navigator.permissions.query({name:'geolocation'});"
                       "return 'perm='+p.state}catch(e){return 'perm_err='+e.message}})()"}, 40)
print("   权限查询: %s" % t3[:200])
