# -*- coding: utf-8 -*-
"""确认诊断: 未加 app_ 前缀的应用事件**是否确实已被写入** app_event 日志?

思路: 带 event_type 查询会按前缀分流, 所以查不到是**必然**的;
但 timeline 模式(不带 event_type)不按名字过滤 —— 若里面出现了
render_load_end / startup_cmdline 等**未加前缀**的名字, 就证明:
  事件写入正常, 只是"名字没带前缀 -> 查询被分到浏览器事件分支" => 命名问题而非架构问题。
"""
import json
import time
import urllib.request

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
    return (not res.get("isError")) and ("error" not in raw), txt


print("1) 开启全部事件族")
ok, txt = call("browser_kernel_events_all", {"action": "enable"})
print("   %s %s" % ("OK " if ok else "!! ", txt[:150]))

print("2) 导航 + 右键 (制造渲染/界面/菜单类事件)")
call("browser_navigate", {"url": "https://example.com", "sync_wait": True})
time.sleep(1)
call("browser_vip_mouse_click", {"x": 130, "y": 130, "button": 2})
time.sleep(3)

print("3) timeline 模式 (不带 event_type, 不按名字过滤) 取 120 条")
ok, txt = call("browser_event", {"limit": 120})
print("   查询成功=%s  响应长度=%d" % (ok, len(txt)))

# timeline_json 是被转义的 JSON 字符串, 用正则宽松匹配事件名
import re
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)
names = set()
for m in re.finditer(r'event\\+"?\s*:\s*\\+"?([a-z_0-9]+)', txt):
    names.add(m.group(1))
for m in re.finditer(r'\\"event\\":\\"([a-z_0-9]+)', txt):
    names.add(m.group(1))

print()
print("=" * 88)
print("timeline 中出现的事件名 (共 %d 种)" % len(names))
print("=" * 88)
for n in sorted(names):
    print("   %s" % n)

print()
NEW_UNP = [n for n in names if (n.startswith("render_") or n.startswith("startup_")
                                or n.startswith("extension_") or n.startswith("ui_")
                                or n.startswith("nav_intent_") or n.startswith("context_menu_"))]
if NEW_UNP:
    print("★ 发现未加前缀的新应用事件已写入日志 (%d 种):" % len(NEW_UNP))
    for n in NEW_UNP:
        print("     %s" % n)
    print()
    print("=> 证实: 事件写入链路正常, 查不到的原因是**名字缺 app_ 前缀导致查询分流错误**(命名缺陷)")
else:
    print("未在 timeline 中发现新事件名 —— 需进一步排查")
