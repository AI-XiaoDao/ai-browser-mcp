# -*- coding: utf-8 -*-
r"""验证第124轮"隐藏窗口 ⇒ 输入族表现"的自诊断与快速失败(全部用**页面侧预言机**, 不靠工具自述)。

被验能力(源码 MCP_Server.wsv / MCP_Server_Core.wsv):
  · 浏览器窗口可见()            —— 回读 GWL_STYLE 的 WS_VISIBLE 位
  · 记CDP输入慢因(起始,类别)     —— 只在 >2s 时回读可见性并经 auto_prepared 上报成因与恢复手段
  · CDPInput失败原因文本(动作名) —— 派发失败时区分"窗口不可见"与"通道真损坏", 并按事件类型给事实
  · 触摸 / 滚轮 入口快速失败      —— 这两类在隐藏态**永不返回**, 不再白等 8 秒后报一个指错成因的错

本轮实测基线(见 probe_input_occlusion / probe_hidden_input_semantics / probe_hidden_wheel_cost):
  可见: move 0.03s / click 0.03s(页面 click 计数+1) / wheel 0.03s(scrollY 变) / touch 0.03s / Runtime 0.03s
  隐藏: move **5.08s 成功**(页面 move 计数+1) / click **0.03s 成功**(页面 click 计数+1)
        wheel **30s 不返回** / touch **30s 不返回** / Runtime 0.03s / Emulation.* 0.01s ⇒ 通道健康

用法: py -3 _audit\verify_input_occlusion.py
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
BTN = "occ_verify_btn"
RES = []
WS_VISIBLE = 0x10000000


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    dt = time.time() - t0
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), dt


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:116]))


def note(txt):
    try:
        return str(json.loads(txt).get("auto_prepared") or "")
    except Exception:
        return ""


def js(expr):
    _e, t, _dt = call("browser_execute_js", {"code": expr})
    try:
        return json.loads(t).get("message", "")
    except Exception:
        return t


def style():
    try:
        return int(json.loads(call("browser_get_window_style", {})[1]).get("style", "0"))
    except Exception:
        return -1


def set_visible(v):
    call("browser_show_window", {"visible": v})


def counters():
    try:
        return json.loads(js("JSON.stringify(window.__occv)") or "{}")
    except Exception:
        return {}


print('== 前置: 显示窗口 + 注入带计数器的测试按钮(页面侧预言机) ==')
set_visible(True)
time.sleep(0.8)
s0 = style()
js("(function(){var o=document.getElementById('%s');if(o)o.remove();"
   "window.__occv={move:0,down:0,up:0,click:0};"
   "var b=document.createElement('button');b.id='%s';b.textContent='occv';"
   "b.style.cssText='position:fixed;left:40px;top:120px;width:120px;height:40px;z-index:2147483647';"
   "b.addEventListener('mousemove',function(){window.__occv.move++});"
   "b.addEventListener('mousedown',function(){window.__occv.down++});"
   "b.addEventListener('mouseup',function(){window.__occv.up++});"
   "b.addEventListener('click',function(){window.__occv.click++});"
   "document.body.appendChild(b);return 'ok'})()" % (BTN, BTN))
c0 = counters()
rec("前置: 窗口可见", bool(s0 & WS_VISIBLE), "style=%s" % s0)
rec("前置: 预言机按钮已就位", c0.get("click") == 0, "计数=%s" % c0)
# 滚轮要能被"页面侧"证实: 先注入一段高内容, 否则短页面滚动轴无变化(scrollY 恒为 0, 无法区分真滚动与假成功)
js("(function(){var o=document.getElementById('occv_tall');if(o)o.remove();"
   "var d=document.createElement('div');d.id='occv_tall';d.style.height='3000px';"
   "d.textContent='tall';document.body.appendChild(d);window.scrollTo(0,0);return 'ok'})()")
time.sleep(0.3)
print('   页面已注入 3000px 高内容(scrollY=%s)' % js("String(Math.round(window.pageYOffset||0))"))

print('\n== ① 可见态基线: 全部应快, 且**不误报**慢因 ==')
e1, t1, dt1 = call("browser_mouse_move", {"x": 260, "y": 180})
rec("可见时 mouse_move <0.5s 且无慢因", (not e1) and dt1 < 0.5 and note(t1) == "",
    "%.2fs note=%r" % (dt1, note(t1)[:30]))
e1b, t1b, dt1b = call("browser_touch_press", {"x": 262, "y": 182})
e1c, t1c, dt1c = call("browser_touch_release", {"x": 262, "y": 182})
rec("可见时触摸族成功且快", (not e1b) and (not e1c) and dt1b < 1.0 and dt1c < 1.0,
    "%.2fs / %.2fs" % (dt1b, dt1c))
y1b = js("String(Math.round(window.pageYOffset||0))")
e1d, t1d, dt1d = call("browser_mouse_wheel", {"x": 260, "y": 180, "delta_y": 60})
time.sleep(0.6)
y1 = js("String(Math.round(window.pageYOffset||0))")
rec("可见时滚轮成功且快(页面真的下滚了)", (not e1d) and dt1d < 1.0 and y1 != y1b,
    "%.2fs scrollY %s -> %s" % (dt1d, y1b, y1))

print('\n== ② 隐藏窗口: 鼠标移动应变慢(≈5s)但仍成功, 并带慢因上报 ==')
set_visible(False)
time.sleep(1.2)
s1 = style()
rec("隐藏窗口生效(WS_VISIBLE=0)", not (s1 & WS_VISIBLE), "style=%s" % s1)
c_before = counters()
e2, t2, dt2 = call("browser_mouse_move", {"x": 100, "y": 140})   # 按钮中心
n2 = note(t2)
c_after = counters()
rec("隐藏时 mouse_move 仍成功(≥3s)", (not e2) and dt2 >= 3.0, "%.2fs err=%s" % (dt2, e2))
rec("隐藏时慢因上报出现且点明不可见", "不可见" in n2, n2[:70])
rec("隐藏时慢因给出恢复手段", "browser_show_window" in n2, n2[-58:])
rec("隐藏时移动事件**真实到达页面**(预言机计数+1)",
    c_after.get("move", 0) == c_before.get("move", 0) + 1,
    "move %s -> %s" % (c_before.get("move"), c_after.get("move")))

print('\n== ③ 同状态下 Runtime 应仍快(区分"输入域异常"与"通道损坏") ==')
e3, t3, dt3 = call("browser_execute_js", {"code": "1+1"})
rec("隐藏时 execute_js 仍 <0.5s", (not e3) and dt3 < 0.5 and "2" in t3, "%.2fs" % dt3)
e3b, _t3b, dt3b = call("browser_cdp_call",
                       {"method": "Runtime.evaluate",
                        "params": "{\"expression\":\"1+1\",\"returnByValue\":true}"})
rec("隐藏时 cdp_call Runtime 仍 <0.5s", (not e3b) and dt3b < 0.5, "%.2fs" % dt3b)

print('\n== ④ 隐藏时点击**仍应即时可用**(页面预言机验证) ==')
c_b2 = counters()
e4, t4, dt4 = call("browser_mouse_click", {"x": 100, "y": 140})
c_a2 = counters()
rec("隐藏时 mouse_click <1s 且成功", (not e4) and dt4 < 1.0, "%.2fs err=%s" % (dt4, e4))
rec("隐藏时点击**真实生效**(预言机 click 计数+1)",
    c_a2.get("click", 0) == c_b2.get("click", 0) + 1,
    "click %s -> %s" % (c_b2.get("click"), c_a2.get("click")))
rec("点击不该误报慢因(它本来就不慢)", note(t4) == "", "note=%r" % note(t4)[:40])

print('\n== ⑤ 隐藏时触摸三件套应**立即失败**并说出真实成因 ==')
e5, t5, dt5 = call("browser_touch_press", {"x": 270, "y": 190})
rec("touch_press 快速失败(<1.5s, 原来白等 8.2s)", e5 and dt5 < 1.5, "%.2fs" % dt5)
rec("报错点明不可见 + 通道健康 + 恢复手段",
    ("不可见" in t5) and ("通道本身是健康的" in t5) and ("browser_show_window" in t5), t5[:70])
e5b, t5b, dt5b = call("browser_touch_move", {"x": 272, "y": 192})
e5c, t5c, dt5c = call("browser_touch_release", {"x": 272, "y": 192})
rec("touch_move/release 同样快速失败且成因明确",
    e5b and e5c and dt5b < 1.5 and dt5c < 1.5 and "不可见" in t5b and "不可见" in t5c,
    "%.2fs / %.2fs" % (dt5b, dt5c))

print('\n== ⑥ 隐藏时滚轮应**立即失败**并说出真实成因(本轮新增守卫) ==')
e6, t6, dt6 = call("browser_mouse_wheel", {"x": 100, "y": 140, "delta_y": 120})
rec("mouse_wheel 快速失败(<1.5s, 原来白等 8.2s)", e6 and dt6 < 1.5, "%.2fs err=%s" % (dt6, e6))
rec("滚轮报错同样给出真实成因", ("不可见" in t6) and ("browser_show_window" in t6), t6[:70])

print('\n== ⑦ 恢复可见后应立即复原, 且慢因上报消失 ==')
set_visible(True)
time.sleep(0.8)
e7, t7, dt7 = call("browser_mouse_move", {"x": 280, "y": 200})
rec("恢复后 mouse_move <0.5s 且无慢因", (not e7) and dt7 < 0.5 and note(t7) == "",
    "%.2fs note=%r" % (dt7, note(t7)[:30]))
e7b, _t7b, dt7b = call("browser_touch_press", {"x": 282, "y": 202})
e7c, _t7c, dt7c = call("browser_touch_release", {"x": 282, "y": 202})
rec("恢复后触摸族立即成功(<1s)", (not e7b) and (not e7c) and dt7b < 1.0 and dt7c < 1.0,
    "%.2fs / %.2fs" % (dt7b, dt7c))
y7b = js("String(Math.round(window.pageYOffset||0))")   # 必须在滚轮**之前**读, 否则前后读到同一个已滚过的值
e7d, t7d, dt7d = call("browser_mouse_wheel", {"x": 280, "y": 200, "delta_y": 60})
time.sleep(0.6)
y7a = js("String(Math.round(window.pageYOffset||0))")
# 阈值给到 3 秒: 实测"恢复可见后**首次**滚轮"要 0.06~2.14 秒才解掉节流(第二次起 0.03 秒),
# 而 1 秒阈值会偶发假红。故这里既断言"有界恢复", 又用**页面侧 scrollY 真的变了**证明滚轮真的生效。
rec("恢复后滚轮生效(≤3s 且页面真的滚动)", (not e7d) and dt7d < 3.0 and y7a != y7b,
    "%.2fs scrollY %s -> %s" % (dt7d, y7b, y7a))

print('\n== 收尾: 清理预言机 + 会话健康 + 窗口可见 ==')
js("(function(){var o=document.getElementById('%s');if(o)o.remove();"
   "var t=document.getElementById('occv_tall');if(t)t.remove();window.scrollTo(0,0);return 'cleanup'})()" % BTN)
e8, t8, dt8 = call("browser_execute_js", {"code": "location.href"})
s2 = style()
rec("收尾: 会话健康", (not e8) and "http" in t8, t8[:50])
rec("收尾: 窗口可见(GWL_STYLE 回读)", bool(s2 & WS_VISIBLE), "style=%s" % s2)

bad = [t for t, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for t in bad:
    print('   未通过: %s' % t)
sys.exit(1 if bad else 0)
