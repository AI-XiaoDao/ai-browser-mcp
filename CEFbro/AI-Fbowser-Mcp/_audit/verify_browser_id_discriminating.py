# -*- coding: utf-8 -*-
"""关键判别: `browser_id` 到底有没有**真的**把 JS 执行到指定的那个浏览器上?

## 为什么必须重测
我此前用"读 document.title 得到 Example Domain"当作"第二个浏览器可用"的证据 —— 但那**没有判别力**:
我恰好把两个浏览器都导航到了 example.com, 两者标题一样。**同值观测不能证明打到了哪个目标**。
本项目纪律里已经吃过同类亏(必须用不可混淆、可区分、不可覆盖的观测)。

## 判别设计
1. 主浏览器导航到 example.com, 并在它上面写入一个**独有标记** `window.__who='MAIN'`;
2. 创建第二个浏览器, 导航到 **about:blank**(与主浏览器页面不同);
3. 通过 `browser_id` 在第二个浏览器上执行:
   · `location.href`  -> 应当得到 about:blank(证明打到了第二个浏览器); 若得到 example.com 则是打到了主浏览器
   · `String(window.__who)` -> 应当是 "undefined"(隔离正确); 若得到 "MAIN" 则说明**串到了主浏览器**
4. 对照: 不带 browser_id 再读一次 `location.href`(应仍是 example.com), 确认主浏览器没被改。
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


def call(name, args, timeout=60):
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
    print("  %-46s %-4s %6.2fs %s" % (tag, "ERR" if e else "OK", dt,
                                      t.replace("\n", " ")[:90]))


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

print("== 1) 主浏览器: 导航 example.com 并写入独有标记 ==")
show("navigate main -> example.com",
     *call("browser_navigate", {"url": "https://example.com/?who=main", "wait_for_load": True}, 45))
show("main: 写 window.__who='MAIN'",
     *call("browser_execute_js", {"code": "window.__who='MAIN';String(location.href)"}))
show("main: 读回 window.__who(应 MAIN)",
     *call("browser_execute_js", {"code": "String(window.__who)"}))

print("\n== 2) 创建第二个浏览器(后台), 导航到 about:blank ==")
show("create background (about:blank)",
     *call("browser_create", {"url": "about:blank", "background": True}, 60))
time.sleep(0.8)

print("\n== 3) 通过 browser_id=2 执行: 判别到底打到了哪个浏览器 ==")
show("browser_id=2: location.href (应 about:blank)",
     *call("browser_execute_js", {"code": "String(location.href)", "browser_id": 2}))
show("browser_id=2: String(window.__who) (应 undefined)",
     *call("browser_execute_js", {"code": "String(window.__who)", "browser_id": 2}))

print("\n== 4) 对照: 不带 browser_id(应仍是 example.com / MAIN) ==")
show("main: location.href", *call("browser_execute_js", {"code": "String(location.href)"}))
show("main: window.__who", *call("browser_execute_js", {"code": "String(window.__who)"}))

print("\n== 5) 另一个角度: browser_get_url 对 id=2 ==")
show("browser_get_url {browser_id:2}", *call("browser_get_url", {"browser_id": 2}))
show("browser_get_url(主)", *call("browser_get_url", {}))

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("\n  已关闭")
