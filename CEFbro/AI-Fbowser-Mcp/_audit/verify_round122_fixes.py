# -*- coding: utf-8 -*-
r"""本轮三项改动的验收: ①get_run_style 补真 runtime_style ②app_* 无记录的错误文案如实
③browser_vip_touch_emulation mode=mouse 走 CDP 鼠标转触摸(并给出页面侧证据)。"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
R = []


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:300]) if detail else ''))


def j(t):
    """回包外层是 {"id":..,"success":..,"data":{...}} —— 内容在 data 里(探针第一版漏了这层, 误报 4 条 FAIL)。"""
    o = {}
    try:
        o = json.loads(t)
    except Exception:
        return {}
    if isinstance(o, dict) and isinstance(o.get('data'), dict):
        return o['data']
    return o


print('== A. browser_get_run_style 口径订正 ==')
e, t = call("browser_get_run_style", {})
d = j(t)
print('   %s' % t[:300])
rec('A1 保留原 window_style 字段(向后兼容)', 'window_style' in d, sorted(d.keys()))
rec('A2 新增 runtime_style(真值)', 'runtime_style' in d, d.get('runtime_style'))
rec('A3 新增 runtime_style_name', 'runtime_style_name' in d, d.get('runtime_style_name'))
rec('A4 新增 runtime_style_note(说明与 GWL_STYLE 的区别)', 'runtime_style_note' in d, str(d.get('runtime_style_note'))[:80])

print('\n== B. app_* 族查不到时的错误文案必须区分两种成因 ==')
call("browser_collect", {"action": "event_app_enable"})
e, t = call("browser_event", {"event_type": "app_render_load_end", "limit": 5})
print('   isError=%s %s' % (e, t[:260]))
rec('B1 开关已开时报"已开启但本机该族无记录"(不再只说"请先开开关")',
    e and ('已开启' in t) and ('无记录' in t), t[:260])
rec('B2 文案给出可用替代(浏览器事件族/CDP)', ('可用替代' in t) and ('browser_event' in t), t[:260])

print('\n== C. 鼠标转触摸(CDP 路线) ==')
call("browser_navigate", {"url": "https://example.com/?emittouch=%d" % int(time.time()),
                          "wait_for_load": True})
before = call("browser_execute_js", {"code":
              "JSON.stringify({ontouch:'ontouchstart' in window,"
              "maxTouchPoints:navigator.maxTouchPoints,"
              "touchEvent:typeof TouchEvent!=='undefined'})"})[1]
print('   开启前页面侧: %s' % before[:160])
e, t = call("browser_vip_touch_emulation", {"mode": "mouse", "enable": True, "configuration": "mobile"})
print('   开启回包: isError=%s %s' % (e, t[:200]))
rec('C1 CDP 调用成功(未走内核级注入)', (not e) and ('setEmitTouchEventsForMouse' in t), t[:200])
after = call("browser_execute_js", {"code":
             "JSON.stringify({ontouch:'ontouchstart' in window,"
             "maxTouchPoints:navigator.maxTouchPoints,"
             "touchEvent:typeof TouchEvent!=='undefined'})"})[1]
print('   开启后页面侧: %s' % after[:160])
e2, t2 = call("browser_vip_touch_emulation", {"mode": "mouse", "enable": False})
print('   撤销回包: isError=%s %s' % (e2, t2[:160]))
rec('C2 可撤销(enable=false 走同一 CDP 命令)', (not e2) and ('已关闭' in t2), t2[:160])
e3, t3 = call("browser_vip_touch_emulation", {"mode": "mouse", "enable": True, "configuration": "bogus"})
rec('C3 非法 configuration 明确报错', e3 and ('mobile' in t3), t3[:160])

print('\n== C4. ★页面侧真证据: 开启后用**鼠标点击**应让页面收到 touchstart(对照: 关闭后不应收到) ==')
LISTEN = ("(function(){window.__mcpT=[];window.__mcpM=[];"
          "document.addEventListener('touchstart',function(){window.__mcpT.push('touchstart')},true);"
          "document.addEventListener('mousedown',function(){window.__mcpM.push('mousedown')},true);"
          "return 'armed'})()")
READ = "JSON.stringify({touch:window.__mcpT, mouse:window.__mcpM})"
call("browser_vip_touch_emulation", {"mode": "mouse", "enable": True, "configuration": "mobile"})
call("browser_execute_js", {"code": LISTEN})
e, t = call("browser_mouse_click", {"x": 120, "y": 120})
print('   鼠标点击回包: isError=%s %s' % (e, t[:110]))
time.sleep(0.6)
on = call("browser_execute_js", {"code": READ})[1]
print('   开启鼠标转触摸后: %s' % on[-140:])
call("browser_vip_touch_emulation", {"mode": "mouse", "enable": False})
call("browser_execute_js", {"code": LISTEN})
e, t = call("browser_mouse_click", {"x": 140, "y": 140})
time.sleep(0.6)
off = call("browser_execute_js", {"code": READ})[1]
print('   关闭之后: %s' % off[-140:])
rec('C4 ★开启时页面收到 touchstart(鼠标事件确实被转成触摸)',
    'touchstart' in on, on[-160:])
rec('C5 对照: 关闭后页面不再收到 touchstart', 'touchstart' not in off, off[-160:])
rec('C6 对照臂: 关闭时页面收到的是 mousedown(鼠标事件本身正常到达)',
    'mousedown' in off and 'touchstart' not in off, off[-160:])
rec('C7 开启时不再发 mousedown(鼠标事件被转成触摸, 属预期语义)',
    'mousedown' not in on, on[-160:])
print('   [信息] 页面侧可见变化: before=%s after=%s' % (before.strip()[:80], after.strip()[:80]))

print('\n== D. 回执里能自查 DPI/V8 两个启动键 ==')
e, t = call("browser_startup_args", {})
d2 = j(t)
rec('D1 回执含 dpi_aware', 'dpi_aware' in d2, d2.get('dpi_aware'))
rec('D2 回执含 v8_max_stack_mb', 'v8_max_stack_mb' in d2, d2.get('v8_max_stack_mb'))

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
