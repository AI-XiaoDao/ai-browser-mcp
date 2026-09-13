# -*- coding: utf-8 -*-
"""补测: 用**正确的触发手段**验证其余新事件族。
上一轮的错误: 我用 window.__mcp_dlg=1 想触发对话框, 但根本没调 alert() -> 自然无记录。
本次: 真正调 alert() / 真正点菜单项 / 真正弹窗。
严格断言同上脚本。
"""
import json
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
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return False, "TRANSPORT:%s" % ex
    if "error" in raw:
        return False, "RPC_ERR:%s" % json.dumps(raw["error"], ensure_ascii=False)[:150]
    res = raw.get("result", {})
    txt = "".join(c.get("text", "") for c in res.get("content", []) if isinstance(c, dict))
    if res.get("isError"):
        return False, txt[:180]
    return True, txt[:180]


def q(t):
    ok, txt = call("browser_event", {"event_type": t, "limit": 5})
    if ok and "未找到事件" in txt:
        return False, txt
    return ok, txt


print("=" * 92)
print("1. 对话框族: 真正调用 alert() (既有族 js_dialog + 新增 js_dialog_closed/reset)")
print("=" * 92)
ok, txt = call("browser_execute_js", {"code": "alert('mcp-probe-dialog')"})
print("   触发 alert : %s %s" % ("OK " if ok else "!! ", txt[:110]))
time.sleep(2)

print()
print("2. 菜单: 右键后按 Esc 关闭 (触发 dismissed), 并点一个菜单项 (触发 command)")
print("=" * 92)
call("browser_vip_mouse_click", {"x": 150, "y": 150, "button": 2})
time.sleep(1)
ok, txt = call("browser_vip_key_click", {"key_code": 27})   # VK_ESCAPE
print("   Esc 关闭菜单: %s %s" % ("OK " if ok else "!! ", txt[:110]))
time.sleep(1)

print()
print("3. 弹窗: 用带 target=_blank 的链接点击触发 open_url_from_tab")
print("=" * 92)
ok, txt = call("browser_execute_js", {"code":
    "(function(){var a=document.createElement('a');a.href='https://example.com';"
    "a.target='_blank';document.body.appendChild(a);a.click();return 'clicked'})()"})
print("   点击 _blank 链接: %s %s" % ("OK " if ok else "!! ", txt[:110]))
time.sleep(3)

print()
print("=" * 92)
print("4. 判定")
print("=" * 92)
CASES = [("js_dialog", "既有·对话框"),
         ("js_dialog_closed", "新增·对话框"),
         ("js_dialog_reset", "新增·对话框"),
         ("context_menu_opening", "新增·菜单(上轮已证)"),
         ("context_menu_dismissed", "新增·菜单"),
         ("nav_intent_open_url_from_tab", "新增·导航意图"),
         ("navigate", "既有·导航(对照)"),
         ("popup", "既有·弹窗(对照)")]
for t, label in CASES:
    ok, txt = q(t)
    print("  %s %-30s %-22s %s" % ("有记录" if ok else "无记录", t, label, "" if ok else txt[:55]))
