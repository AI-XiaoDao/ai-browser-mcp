# -*- coding: utf-8 -*-
"""判定 (C): 渲染进程事件到底能不能落库并被 app_ 前缀查询到?

用**既有且名字未变**的应用事件作探针 —— app_v8_exception 由
`渲染_即将捕获异常`(OnUncaughtException, 渲染进程) 触发, 名字带 app_ 前缀, 一直是可查的。
若它能在"先开监控 -> 再抛异常"后查到, 则证明:
   ① 渲染进程事件能到达主进程日志(无架构限制)
   ② app_ 前缀 + 应用事件查询链路正常
=> 我已改名的 19 个 app_* 事件在编译后同样应可用, (C) 可直接关闭。
"""
import json
import re
import time
import urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"


def call(tool, args, timeout=25):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}},
                      ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + "/mcp", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = json.loads(r.read().decode("utf-8"))
    res = raw.get("result", {})
    txt = "".join(c.get("text", "") for c in res.get("content", []) if isinstance(c, dict))
    ok = ("error" not in raw) and (not res.get("isError"))
    return ok, txt


print("1) 开应用事件监控 (event_app_enable)")
ok, txt = call("browser_collect", {"action": "event_app_enable"})
print("   %s %s" % ("OK " if ok else "!! ", txt[:150]))

print("2) 导航到真实页面")
ok, txt = call("browser_navigate", {"url": "https://example.com", "sync_wait": True})
print("   %s %s" % ("OK " if ok else "!! ", txt[:110]))
time.sleep(1)

print("3) 在页面里制造**未捕获异常** (触发 渲染_即将捕获异常 -> app_v8_exception)")
ok, txt = call("browser_execute_js", {"code": "setTimeout(function(){throw new Error('mcp-probe-uncaught')},0);void 0"})
print("   %s %s" % ("OK " if ok else "!! ", txt[:110]))
time.sleep(3)

print("4) 判定: 查询既有 app_ 事件 (名字未变, 一直可查)")
for t in ("app_v8_exception", "app_dom_focus_changed", "app_render_browser_created"):
    ok, txt = call("browser_event", {"event_type": t, "limit": 5})
    found = ok and ("未找到" not in txt)
    print("   %s %-30s %s" % ("有记录" if found else "无记录", t, "" if found else txt[:60]))
    if found:
        print("        内容片段: %s" % txt[:150])

print()
print("5) timeline 里是否出现 app_ 前缀事件")
ok, txt = call("browser_event", {"limit": 150})
names = set(re.findall(r'\\+"event\\+"?\s*:\s*\\+"?([A-Za-z_0-9]+)', txt)) | set(re.findall(r'\\"event\\":\\"([A-Za-z_0-9]+)', txt))
apps = sorted(n for n in names if n.startswith("app_"))
print("   timeline 事件名共 %d 种, 其中 app_ 前缀 %d 种: %s" % (len(names), len(apps), ", ".join(apps) if apps else "(无)"))
