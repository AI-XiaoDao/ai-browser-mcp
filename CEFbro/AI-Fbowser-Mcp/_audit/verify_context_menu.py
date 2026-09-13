# -*- coding: utf-8 -*-
"""验收 browser_context_menu（方案甲）。

关键判据: `last_applied_items` —— 它是类库 `添加菜单/添加子菜单/...` 的**返回值计数**,
即"CEF 的菜单模型**真的接受了**我们的条目"。这比"工具自己说成功了"强得多。

臂:
  A set 规格(含 item/sep/sub/子项/check) -> 应报 spec_lines 且自动分配命令ID
  B 右键一次 -> 回调施加; get 应显示 apply_count>=1 且 last_applied_items>=1
  C 非法命令ID(越界) -> 必须**明确拒绝**(不静默丢弃)
  D 非法类型 -> 明确拒绝
  E clear -> 幂等成功; get 显示 disabled
  F get 在未设置时也应正常返回(不报错)
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
R = []


def call(n, a, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def arm(label, ok, detail):
    R.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:300])


def right_click():
    for typ, btn in (("mousePressed", 2), ("mouseReleased", 0)):
        call("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                                 "params": {"type": typ, "x": 80, "y": 80,
                                            "button": "right", "clickCount": 1,
                                            "buttons": btn}}, 40)
    time.sleep(1.0)


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
call("browser_navigate", {"url": "https://example.com/?menu=1", "wait_for_load": True})
call("browser_debugger_enable", {"action": "enable"})

print("== F) 未设置时 get 应正常返回 ==")
e, t = call("browser_context_menu", {"action": "get"})
print("   -> isError=%s %s" % (e, t[:240]))
arm("未设置时 get 不报错且 enabled=false", (not e) and ('"enabled":false' in t), t[:200])

print("\n== A) set 一份规格(含 item/sep/sub/子项/check) ==")
SPEC = "\n".join([
    "item|MCP测试项|0|1|0|",
    "sep||0",
    "sub|更多|0|1|0|",
    "item|子项1|0|1|26501|",
    "check|复选项|0|1|0|",
])
e, t = call("browser_context_menu", {"action": "set", "items": SPEC})
print("   -> isError=%s | %s" % (e, t[:360]))
arm("set 成功并报出条目数", (not e) and ('"spec_lines":5' in t), t[:300])
arm("自动分配了命令ID(>0)", '"spec_lines":5' in t and '含命令ID条目' in t,
    "回包: %s" % t[:200])

print("\n== B) 右键一次 -> 回调应施加规格 ==")
right_click()
e, t = call("browser_context_menu", {"action": "get"})
print("   -> isError=%s | %s" % (e, t[:420]))
applied = '"apply_count":0' not in t
items_ok = '"last_applied_items":5' in t or '"last_applied_items":4' in t
arm("右键后施加次数 > 0(回调确实被调用并施加)", applied, t[:300])
arm("CEF 菜单模型真的接受了条目(last_applied_items>0)", items_ok or '"last_applied_items":' in t and '"last_applied_items":0' not in t,
    t[:300])

print("\n== C) 命令ID 越界必须明确拒绝 ==")
e, t = call("browser_context_menu", {"action": "set", "items": "item|越界项|100|1|0|"})
print("   -> isError=%s %s" % (e, t[:240]))
arm("越界命令ID 被拒绝并说明合法区间", e and ('26500' in t), t[:220])

print("\n== D) 非法类型必须明确拒绝 ==")
e, t = call("browser_context_menu", {"action": "set", "items": "bogus|标签|26501|1|0|"})
print("   -> isError=%s %s" % (e, t[:240]))
arm("非法类型被拒绝并列出支持值", e and ('item/check/radio/sep/sub' in t), t[:220])

print("\n== E) clear 幂等 + get 显示已禁用 ==")
e, t = call("browser_context_menu", {"action": "clear"})
print("   clear -> isError=%s %s" % (e, t[:160]))
e2, t2 = call("browser_context_menu", {"action": "get"})
print("   get   -> %s" % t2[:200])
arm("clear 后 enabled=false 且规格为空",
    (not e) and ('"enabled":false' in t2) and ('"spec":""' in t2),
    "%s | %s" % (t[:100], t2[:160]))

ok = sum(1 for _, v in R if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(R)))
for label, v in R:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))
