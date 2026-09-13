# -*- coding: utf-8 -*-
"""localStorage 清不掉, 试一下**显式给 origin**: 也许它是按源定向清理, 空 origin 对它不生效。

用法: 依次尝试 ① 只给 targets=localstorage(已知无效) ② 同时给 origin=<页面URL> ③ origin 带路径/多余斜杠
每次清完都刷新页面再读, 避免"读渲染器内存副本"的假阴性。
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
URL = "https://example.com/?cc3=1"


def call(name, args, timeout=45):
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                                      "method": "tools/call",
                                                      "params": {"name": name,
                                                                 "arguments": args}},
                                                     ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return {"error": str(ex)}


def js(code):
    r = call("browser_execute_js", {"code": code})
    rr = r.get("result") or {}
    t = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                if i.get("type") == "text")
    m = re.search(r'"message":"((?:[^"\\]|\\.)*)"', t)
    return m.group(1) if m else t.strip('"')


def state():
    return js("String((localStorage.getItem('mcpCC')||'NONE'))")


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

cases = [
    ("targets=localstorage (无 origin)", {"targets": "localstorage"}),
    ("targets=localstorage + origin=https://example.com", {"targets": "localstorage", "origin": "https://example.com"}),
    ("targets=localstorage + origin 带斜杠 https://example.com/", {"targets": "localstorage", "origin": "https://example.com/"}),
    ("targets=all", {"targets": "all"}),
]

for label, args in cases:
    call("browser_navigate", {"url": URL, "wait_for_load": True}, 45)
    time.sleep(0.5)
    js("try{localStorage.setItem('mcpCC','1');}catch(e){}")
    before = state()
    call("browser_clear_cache_browser", args)
    time.sleep(1.5)
    call("browser_navigate", {"url": URL, "wait_for_load": True}, 45)
    time.sleep(0.8)
    after = state()
    print("  %-52s 清前=%s 清后(刷新后)=%s  %s"
          % (label, before, after, "已清掉" if "NONE" in str(after) else "**仍在**"))

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
