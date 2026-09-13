# -*- coding: utf-8 -*-
r"""诊断: confirm:true 后进程退出的实际时延(HTTP + 进程双探针, 观察 40s)。
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=5):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(r, timeout=to)
        return True
    except Exception:
        return False


def proc_alive():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq AI-Fbowser-Mcp.exe", "/NH"],
                             capture_output=True, timeout=10)
        return "AI-Fbowser-Mcp.exe" in out.stdout.decode("gbk", "ignore")
    except Exception:
        return None


loop.kill_app()
loop.start_app()
_ok = call("browser_shutdown", {"confirm": True, "delay_seconds": 1}, to=10)
print('shutdown 已发(立即读回)')
t0 = time.time()
last = None
while time.time() - t0 < 40:
    http = call("browser_status", {}, to=3)
    proc = proc_alive()
    if (http, proc) != last:
        last = (http, proc)
        print('  +%.1fs HTTP=%s PROC=%s' % (time.time() - t0, http, proc))
    if not proc:
        print('  +%.1fs 进程已退出' % (time.time() - t0))
        break
    time.sleep(0.8)
else:
    print('  40s 内进程仍未退出!')
