# -*- coding: utf-8 -*-
"""定案: 类库事件 浏览器_即将打开菜单 在本项目里**到底会不会被 CEF 触发**?

为什么值得单独测: 子代理静态分析确认 `类_FBrowser_菜单模式` 的 34 个方法在 src 中**零调用**,
是当前最大的能力缺口块; 但整块都建立在"该事件会被触发"之上 —— 若不触发, 这块不可达, 不值得实现。

链路: browser_collect{event_menu_enable} -> 是否监控菜单事件=真
      MCP_BrowserEvents.wsv:2658 浏览器_即将打开菜单 -> 记录监控事件(真,"context_menu_opening",...)
      browser_event 查询

触发手段: CDP Input.dispatchMouseEvent 右键按下+抬起(项目自有鼠标工具走的就是这条 CDP 路径,
不碰内核注入那条会杀死 CDP 的通道)。
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


def c(n, a, to=60):
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

c("browser_navigate", {"url": "https://example.com/?menuprobe=1", "wait_for_load": True})
c("browser_debugger_enable", {"action": "enable"})

print("== 1) 启用右键菜单事件监控 ==")
e, t = c("browser_collect", {"action": "event_menu_enable"})
print("   isError=%s -> %s" % (e, t[:200]))

print("\n== 2) 基线: 触发前查一次(应为空) ==")
e, t = c("browser_event", {"event_name": "context_menu_opening"})
print("   isError=%s -> %s" % (e, t[:250]))

print("\n== 3) CDP 右键(按下+抬起) ==")
for typ in ("mousePressed", "mouseReleased"):
    r = c("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                               "params": {"type": typ, "x": 60, "y": 60,
                                          "button": "right", "clickCount": 1,
                                          "buttons": 2 if typ == "mousePressed" else 0}})
    print("   %-14s -> %s" % (typ, r[1][:150]))
time.sleep(1.2)

print("\n== 4) 触发后查 context_menu_opening ==")
e, t = c("browser_event", {"event_name": "context_menu_opening"})
print("   isError=%s -> %s" % (e, t[:600]))
hit = ("context_menu_opening" in t) and ("count" not in t or '"count":0' not in t)
print("   [%s] 事件被触发" % ("PASS" if hit else "FAIL(未触发)"))

print("\n== 5) 兜底: 查全部事件缓冲(看有没有别的菜单相关事件) ==")
e, t = c("browser_event", {})
print("   isError=%s -> %s" % (e, t[:500]))
for kw in ("context_menu", "menu"):
    print("   含 '%s': %s" % (kw, kw in t))

print("\n== 6) 再用类库原生路径右键一次(内核执行JS触发 contextmenu 事件) ==")
c("browser_execute_js", {"code": ("document.body.dispatchEvent(new MouseEvent("
                                  "'contextmenu',{bubbles:true,cancelable:true,"
                                  "clientX:60,clientY:60,button:2}))")})
time.sleep(1.0)
e, t = c("browser_event", {"event_name": "context_menu_opening"})
print("   isError=%s -> %s" % (e, t[:400]))
