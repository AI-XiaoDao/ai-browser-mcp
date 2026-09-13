# -*- coding: utf-8 -*-
"""判定新事件族是否真能落库并可经 browser_event 查询。

严格断言（吸取本会话两次假阳性教训）:
  成功 = 有 "result" 且 无 "error" 且 无 "isError":true 且 content 文本不是"未找到事件"

触发手段（主动制造事件，而非被动等）:
  - navigate            -> 载入类事件（对照组）
  - vip_mouse_click 右击 -> context_menu_* 族
  - execute_js alert     -> js_dialog 族（既有族，作为"触发即记录"的对照）
  - execute_js window.open -> nav_intent / popup
"""
import io
import json
import os
import time
import urllib.request
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
HERE = os.path.dirname(os.path.abspath(__file__))


def call(tool, args, timeout=25):
    """返回 (ok, text, raw)。ok 严格判定为'成功响应'。"""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}},
                      ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + "/mcp", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return False, "TRANSPORT:%s" % ex, None
    if "error" in raw:
        return False, "RPC_ERR:%s" % json.dumps(raw["error"], ensure_ascii=False)[:160], raw
    res = raw.get("result", {})
    txt = "".join(c.get("text", "") for c in res.get("content", []) if isinstance(c, dict))
    if res.get("isError"):
        return False, txt[:200], raw
    return True, txt[:200], raw


def q(event_type):
    ok, txt, _ = call("browser_event", {"event_type": event_type, "limit": 5})
    if not ok:
        return False, txt
    # 双重保险: 成功文本不应是"未找到事件"
    if "未找到事件" in txt:
        return False, txt
    return True, txt


print("=" * 96)
print("A. 逐族单独开启（不用全开），确认开关本身可用")
print("=" * 96)
FAM = [("event_menu_enable", "菜单"),
       ("event_ui_enable", "界面细节"),
       ("event_navintent_enable", "导航意图"),
       ("event_quickmenu_enable", "快捷菜单")]
for act, label in FAM:
    ok, txt, _ = call("browser_collect", {"action": act})
    print("  %s %-22s %s  %s" % ("OK " if ok else "!! ", act, label, txt[:90]))

print()
print("=" * 96)
print("B. 主动触发事件")
print("=" * 96)
ok, txt, _ = call("browser_navigate", {"url": "https://example.com", "sync_wait": True})
print("  导航         : %s %s" % ("OK " if ok else "!! ", txt[:90]))
time.sleep(1)
ok, txt, _ = call("browser_vip_mouse_click", {"x": 120, "y": 120, "button": 2})
print("  右键(x2)     : %s %s" % ("OK " if ok else "!! ", txt[:90]))
time.sleep(1)
ok, txt, _ = call("browser_execute_js", {"code": "window.__mcp_dlg=1;void 0"})
print("  JS(对照)     : %s %s" % ("OK " if ok else "!! ", txt[:90]))
ok, txt, _ = call("browser_execute_js", {"code": "window.open('https://example.com','_blank');void 0"})
print("  window.open  : %s %s" % ("OK " if ok else "!! ", txt[:90]))
time.sleep(3)

print()
print("=" * 96)
print("C. 查询判定  (对照=既有族, 其余=本轮新增)")
print("=" * 96)
CASES = [
    ("load_end", "对照·既有"),
    ("js_dialog", "对照·既有(需弹窗)"),
    ("context_menu_opening", "新增·菜单"),
    ("context_menu_command", "新增·菜单"),
    ("context_menu_dismissed", "新增·菜单"),
    ("ui_render_view_ready", "新增·界面"),
    ("ui_auto_resize", "新增·界面"),
    ("nav_intent_main_document_creating", "新增·导航意图"),
    ("nav_intent_open_url_from_tab", "新增·导航意图"),
    ("quick_menu_command", "新增·快捷菜单"),
    ("render_load_end", "新增·渲染(渲染进程)"),
    ("render_v8_context_created", "新增·渲染(渲染进程)"),
    ("startup_request_context_ready", "新增·启动"),
    ("permission_media_request", "新增·许可"),
]
yes, no = [], []
for t, label in CASES:
    ok, txt = q(t)
    (yes if ok else no).append((t, label, txt))
    print("  %s %-36s %-22s %s" % ("有记录" if ok else "无记录", t, label, "" if ok else txt[:60]))

print()
print("=" * 96)
print("汇总: 有记录 %d / %d" % (len(yes), len(CASES)))
print("=" * 96)
for t, label, _ in yes:
    print("  ✅ %-36s %s" % (t, label))
print()
for t, label, txt in no:
    print("  ❌ %-36s %-22s %s" % (t, label, txt[:70]))
