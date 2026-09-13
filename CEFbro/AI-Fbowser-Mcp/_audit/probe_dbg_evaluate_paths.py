# -*- coding: utf-8 -*-
"""定案: browser_debugger_evaluate 的**默认**路径(parse 缺省)到底带回数据还是只回回执?

源码读法: parse=true -> 执行Debugger帧求值并等待(内含 同步等待异步任务) -> 真数据
          parse 缺省(false) -> 执行CDP命令_带参数 -> 只回 {"_async":true,"message":"CDP已提交:..."}
而台账第166轮把 {expression:"1"} 记成了真数据 {"type":"number","value":1} —— 与源码读法矛盾。
两者只能有一个对, 故实测三分支(缺省 / parse=false / parse=true)对照。
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


def c(n, a, to=90):
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
c("browser_navigate", {"url": "https://example.com/?eval=1", "wait_for_load": True})
c("browser_debugger_enable", {"action": "enable"})

for label, extra in [("A 缺省(parse 不传)", {}),
                     ("B parse=false", {"parse": False}),
                     ("C parse=true", {"parse": True})]:
    args = {"expression": "1+1"}
    args.update(extra)
    e, t = c("browser_debugger_evaluate", args)
    has_data = ('"value"' in t) and ('CDP已提交' not in t)
    print("== %s ==" % label)
    print("   isError=%s | 带回真实数据=%s" % (e, has_data))
    print("   %s" % t[:420])
    print()
