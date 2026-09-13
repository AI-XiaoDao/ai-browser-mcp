# -*- coding: utf-8 -*-
"""查清 browser_scrape 同步后回空串的原因: 它的**异步存储载荷**到底长什么样?

方法: 先异步调用拿 task_id(该工具已从同步名单撤回, 恢复异步), 再用 mcp_result 取回真实载荷,
      对照 将异步结果转为命令响应 (MCP_Server.wsv:6260) 的取值逻辑, 看它为什么会产出空串。
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

print("== 1) 异步调用 browser_scrape ==")
e, t = call("browser_scrape", {"url": "https://example.com/", "extract_selector": "h1",
                               "async_only": True}, 60)
print("   isError=%s | %s" % (e, t[:400]))
m = re.search(r'"task_id"\s*:\s*"([^"]+)"', t)
tid = m.group(1) if m else (re.search(r'task_\d+_\d+_\d+', t).group(0)
                            if re.search(r'task_\d+_\d+_\d+', t) else '')
print("   task_id = %r" % tid)

if tid:
    print("\n== 2) mcp_result 取真实存储载荷(转换器的输入) ==")
    for i in range(8):
        time.sleep(1.0)
        e2, t2 = call("mcp_result", {"request_id": tid}, 40)
        print("   第 %d 次: isError=%s | %s" % (i + 1, e2, t2[:500]))
        if ('Example' in t2) or ('失败' in t2) or ('error' in t2.lower()):
            break
