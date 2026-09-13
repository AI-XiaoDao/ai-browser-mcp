# -*- coding: utf-8 -*-
"""验收 browser_clear_cache_browser 的**按对象粒度**清理(本次补上的能力)。

判别式设计: 同一页面上同时布置两种可观测状态 —— localStorage 与 cookie,
然后只清其中一种, 断言**另一个必须活着**。只清一种、另一种还在, 才证明粒度真的生效;
若两个都没了, 说明还是"全清", 粒度没生效(这正是补能力前的老行为)。
另附: 未知对象名必须**明确失败并指名**, 不能静默忽略(否则"清一半"会被当成成功)。
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
res = []


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


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-52s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:95]))


def js(code):
    e, t, _ = call("browser_execute_js", {"code": code})
    if e:
        return None
    m = re.search(r'"message":"((?:[^"\\]|\\.)*)"', t)
    return m.group(1) if m else t.strip('"')


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

call("browser_navigate", {"url": "https://example.com/?cc=1", "wait_for_load": True}, 45)
time.sleep(0.6)


def seed():
    """同一页面上布置两种可观测状态: localStorage 项 + cookie。"""
    return js("try{localStorage.setItem('mcpCC','1');}catch(e){}"
              "document.cookie='mcpCCcookie=1;path=/';"
              "String((localStorage.getItem('mcpCC')||'NONE')+'|'+(document.cookie.indexOf('mcpCCcookie')>=0?'COOKIE':'NOCOOKIE'))")


def state():
    return js("String((localStorage.getItem('mcpCC')||'NONE')+'|'+(document.cookie.indexOf('mcpCCcookie')>=0?'COOKIE':'NOCOOKIE'))")


s0 = seed()
rec("布置完成(应有 localStorage 与 cookie)", s0 is not None and "1" in str(s0),
    "初始状态=%s" % s0)

print("\n== 用例 1: 只清 localstorage, cookie 必须保留 ==")
e, t, dt = call("browser_clear_cache_browser", {"targets": "localstorage"}, 45)
rec("调用成功", not e, t.replace("\n", " ")[:100])
time.sleep(1.5)
s1 = state()
rec("localStorage 已被清(NONE)", "NONE" in str(s1), "状态=%s" % s1)
rec("**cookie 仍在**(证明是按对象粒度, 不是全清)", "COOKIE" in str(s1), "状态=%s" % s1)

print("\n== 用例 2: 再只清 cookies ==")
seed()
e, t, dt = call("browser_clear_cache_browser", {"targets": "cookies"}, 45)
rec("调用成功", not e, t.replace("\n", " ")[:90])
time.sleep(1.5)
s2 = state()
rec("cookie 已被清(NOCOOKIE)", "NOCOOKIE" in str(s2), "状态=%s" % s2)

print("\n== 用例 3: 未知对象名必须明确失败并指名 ==")
e, t, dt = call("browser_clear_cache_browser", {"targets": "localstorage,nosuchthing"}, 45)
rec("明确失败", e, t.replace("\n", " ")[:100])
rec("错误里指名了那个不认识的项", "nosuchthing" in t, t.replace("\n", " ")[:110])

print("\n== 用例 4: 组合掩码(localstorage+indexeddb)应被接受 ==")
seed()
e, t, dt = call("browser_clear_cache_browser",
                {"targets": "localstorage,indexeddb", "storage_types": "temporary"}, 45)
rec("组合掩码调用成功", not e, t.replace("\n", " ")[:110])
rec("响应回显了掩码(可核对)", "掩码" in t, t.replace("\n", " ")[:110])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
sys.exit(1 if bad else 0)
