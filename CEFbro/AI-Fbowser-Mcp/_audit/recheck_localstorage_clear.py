# -*- coding: utf-8 -*-
"""复核用例1: 清 localStorage 后**刷新页面**再读 —— 判断是"没清掉"还是"读的是渲染器内存副本"。

上一轮结果很说明问题: 同样的调用, cookies 立刻没了, 而 localStorage 还在。
两者的差别在于 cookie 存在浏览器侧、document.cookie 直接反映; 而 localStorage 由渲染器
持有内存副本, **外部清理后未导航的页面仍可能读到旧值**。
故这里在清理后先 reload, 再读 —— 若此时为 NONE 且 cookie 仍在, 说明粒度清理本身是生效的,
之前那条 FAIL 属**测量方式不对**(同一页面同步观测外部存储变更)。
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
URL = "https://example.com/?cc2=1"


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
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt


def js(code):
    e, t = call("browser_execute_js", {"code": code})
    if e:
        return None
    m = re.search(r'"message":"((?:[^"\\]|\\.)*)"', t)
    return m.group(1) if m else t.strip('"')


def read_state():
    return js("String((localStorage.getItem('mcpCC')||'NONE')+'|'"
              "+(document.cookie.indexOf('mcpCCcookie')>=0?'COOKIE':'NOCOOKIE'))")


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

call("browser_navigate", {"url": URL, "wait_for_load": True}, 45)
time.sleep(0.6)
print("布置:", js("try{localStorage.setItem('mcpCC','1');}catch(e){}"
                 "document.cookie='mcpCCcookie=1;path=/';"
                 "String((localStorage.getItem('mcpCC')||'NONE')+'|'"
                 "+(document.cookie.indexOf('mcpCCcookie')>=0?'COOKIE':'NOCOOKIE'))"))

print("\n只清 localstorage(不刷新就读):")
call("browser_clear_cache_browser", {"targets": "localstorage"})
time.sleep(1.5)
print("  未刷新读到:", read_state())

print("\n刷新页面后再读(这才是观测外部存储变更的正确方式):")
call("browser_navigate", {"url": URL, "wait_for_load": True}, 45)
time.sleep(1.0)
st = read_state()
print("  刷新后读到:", st)
ok_ls = "NONE" in str(st)
ok_ck = "COOKIE" in str(st)
print("\n判定: localStorage 已清=%s ; cookie 仍在=%s" % (ok_ls, ok_ck))
print("=> %s" % ("粒度清理**确实生效**, 之前那条 FAIL 是测量方式不对(未刷新就读内存副本)"
                 if (ok_ls and ok_ck) else
                 "仍不是预期: localStorage 没被清掉(需要查掩码或源地址参数)"))

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
