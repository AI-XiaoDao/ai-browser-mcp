# -*- coding: utf-8 -*-
"""验收菜单别名 + 回读验证。

规格(第 3 列用**别名**指向浏览器默认菜单项, 自建项用自动分配的 26501):
  dis|禁用刷新|reload|1|0|        默认项 102
  vis|隐藏查找|find|0|0|          默认项 130
  mark||copy|1|0|                 默认项 113
  item|自建项|0|1|0|              自建 -> 26501
  dis||26501|1|0|                 自建项禁用
  vis||26501|0|0|                 自建项隐藏

判据:
  · menu_item_count > 0 且 **大于我们自建的条数** -> 说明读的是**真实菜单**(含默认项)
  · verified_items >= 4 -> vis/dis 的回读**逐条比对成功**(期望态 == getter 读回值)
  · verify_mismatch 为空
  · 创建类用别名必须被拒(且新文案引导去用修改类)
一次右键一次(原生菜单无法用 CDP 关闭)。
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
SPEC = "\n".join([
    "dis|禁用刷新|reload|1|0|",
    "vis|隐藏查找|find|0|0|",
    "mark||copy|1|0|",
    "item|自建项|0|1|0|",
    "dis||26501|1|0|",
    "vis||26501|0|0|",
])
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


def flat(t):
    return t.replace('\\"', '"')


def arm(label, ok, detail):
    R.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:300])


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).raise_for_status()
        time.sleep(4.5)
        break
    except Exception:
        pass
call("browser_navigate", {"url": "https://example.com/?alias=1", "wait_for_load": True}, 90)
time.sleep(0.6)

print("== A) 创建类用别名 -> 应被拒绝且新文案引导用修改类 ==")
e, t = call("browser_context_menu", {"action": "set", "items": "item|X|reload|1|0|"})
print("   -> isError=%s %s" % (e, t[:300]))
arm("创建类用别名被拒绝, 文案引导改用修改类",
    e and ('修改类' in t) and ('26500' in t), t[:280])

print("\n== B) 修改类用别名 + 自建项 ==")
e, t = call("browser_context_menu", {"action": "set", "items": SPEC})
print("   -> isError=%s | %s" % (e, t[:300]))
arm("set 接受 6 行(别名已解析为数字)", (not e) and ('"spec_lines":6' in t), t[:260])

print("\n== C) 右键一次 -> 施加 + 回读 ==")
for typ, btn in (("mousePressed", 2), ("mouseReleased", 0)):
    call("browser_cdp_call", {"method": "Input.dispatchMouseEvent",
                             "params": {"type": typ, "x": 130, "y": 130,
                                        "button": "right", "clickCount": 1,
                                        "buttons": btn}}, 40)
time.sleep(1.3)
e, t = call("browser_context_menu", {"action": "get"})
f = flat(t)
print("   -> %s" % f[:560])
cnt = re.search(r'"menu_item_count":(\d+)', f)
ver = re.search(r'"verified_items":(\d+)', f)
app = re.search(r'"last_applied_items":(\d+)', f)
mis = re.search(r'"verify_mismatch":"([^"]*)"', f)
print("   menu_item_count=%s verified_items=%s last_applied_items=%s"
      % (cnt.group(1) if cnt else '?', ver.group(1) if ver else '?',
         app.group(1) if app else '?'))
arm("回调被调用且施加了条目(>0)", bool(app) and int(app.group(1)) > 0,
    "last_applied_items=%s" % (app.group(1) if app else '?'))
arm("★读到**真实菜单项数**(含默认项, >0)",
    bool(cnt) and int(cnt.group(1)) > 2, "menu_item_count=%s" % (cnt.group(1) if cnt else '?'))
arm("★回读验证逐条比对成功(verified_items>=4)",
    bool(ver) and int(ver.group(1)) >= 4, "verified_items=%s" % (ver.group(1) if ver else '?'))
arm("无回读不一致", (mis is None) or (mis.group(1) == ''),
    "verify_mismatch=%r" % (mis.group(1) if mis else None))

print("\n== D) 规格里存的是解析后的数字(便于人工核对) ==")
spec_shown = re.search(r'"spec":"([^"]*)"', f)
print("   spec=%s" % (spec_shown.group(1)[:260] if spec_shown else '?'))
arm("别名已落成数字(reload->102 / find->130 / copy->113)",
    bool(spec_shown) and ('|102|' in spec_shown.group(1)) and ('|130|' in spec_shown.group(1))
    and ('|113|' in spec_shown.group(1)), (spec_shown.group(1)[:200] if spec_shown else ''))

call("browser_context_menu", {"action": "clear"})
ok = sum(1 for _, v in R if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(R)))
for label, v in R:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))
