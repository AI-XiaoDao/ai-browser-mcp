# -*- coding: utf-8 -*-
"""定位: `browser_get_text {browser_id:2}` 为什么返回字面 null?

`browser_get_text` 的取值链是两段: ① CDP 执行 JS 取 textContent; ② CDP 取不到时退到
原生**填表框架**的 取元素内容(异步)。而 `browser_execute_js` 在第二个浏览器上是好的(已实测 0.01s)。
本脚本把三段分别测出来, 看究竟断在哪一段:
  · A: browser_execute_js 直接取 textContent      —— 若正常, 说明"在第二个浏览器执行 JS"没问题
  · B: browser_get_text  取同一个选择器            —— 复现 null
  · C: browser_fill_exists / fill_attr_get        —— 看原生填表框架对第二个浏览器是否有效
  · D: browser_get_text 不传 browser_id(主浏览器) —— 对照, 应正常
并且用**有判别力的内容**: 两个浏览器分别导航到不同页面, 读到的值必须能区分目标。
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


def show(tag, e, t, dt):
    print("  %-48s %-4s %6.2fs %s" % (tag, "ERR" if e else "OK", dt,
                                      t.replace("\n", " ")[:95]))


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

print("== 造判别性场景: 主浏览器 example.com, 第二个浏览器 about:blank ==")
call("browser_navigate", {"url": "https://example.com/?gt=main", "wait_for_load": True}, 45)
time.sleep(0.4)
show("create background with about:blank",
     *call("browser_create", {"url": "about:blank", "background": True}, 60))
time.sleep(0.8)

print("\n== A: 在第二个浏览器上用 execute_js 直接取(对照, 已知可用) ==")
show("execute_js id=2: location.href",
     *call("browser_execute_js", {"code": "String(location.href)", "browser_id": 2}))
show("execute_js id=2: body 文本前 40 字",
     *call("browser_execute_js",
           {"code": "(document.body&&document.body.innerText||'').slice(0,40)", "browser_id": 2}))

print("\n== B: browser_get_text 对第二个浏览器(复现 null) ==")
show("get_text {selector:'body', browser_id:2}",
     *call("browser_get_text", {"selector": "body", "browser_id": 2}))
show("get_text {browser_id:2} (不传 selector = 全文)",
     *call("browser_get_text", {"browser_id": 2}))

print("\n== C: 原生填表框架对第二个浏览器是否有效 ==")
show("fill_exists {selector:'body', browser_id:2}",
     *call("browser_fill_exists", {"selector": "body", "browser_id": 2}))
show("fill_attr_get {selector:'body', attr:'tagName', browser_id:2}",
     *call("browser_fill_attr_get", {"selector": "body", "attr": "tagName", "browser_id": 2}))

print("\n== D: 对照: 主浏览器 get_text 应正常 ==")
show("get_text {selector:'h1'} (主)",
     *call("browser_get_text", {"selector": "h1"}))

print("\n== E: 第二个浏览器换成有内容的页面后再测 ==")
call("browser_navigate", {"url": "https://example.com/?gt=second", "wait_for_load": True,
                          "browser_id": 2}, 45)
time.sleep(0.8)
show("execute_js id=2: location.href(应为 second)",
     *call("browser_execute_js", {"code": "String(location.href)", "browser_id": 2}))
show("get_text {selector:'h1', browser_id:2}(应为 Example Domain)",
     *call("browser_get_text", {"selector": "h1", "browser_id": 2}))

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("\n  已关闭")
