# -*- coding: utf-8 -*-
r"""第135轮: 对台账里 3 条"刻意设计"失败做**受控实测 + 恢复性判定**, 目标是回答用户的诉求:
"确保所有显示的 MCP 能力都可以稳定正常执行功能"。

三个对象(逐项在**干净实例**上测, 每项之间自动重启, 避免互相污染):
  ① `browser_vip_mouse_wheel` —— 台账长期记 GUARD 失败(探针没给 delta_y)。本轮给真实滚动量,
     并用**页面侧 scrollY 预言机**验证"滚轮真的滚动了", 而不是只看没报错。
  ② `browser_vip_enable_js_env` —— 启用后 CDP/JS 通道是否真的坏; **再用 `enable:false` 回滚, 看能否恢复**。
  ③ `browser_reverse_instrument_script` —— install 后 JS 通道是否阻塞; **再用 action=suppress, 看能否恢复**。
判定口径: "可稳定执行" = ①按 schema 传参即成功 ②真有效果(有预言机) ③有**可用回滚**且回滚后会话恢复。

用法: py -3 _audit\probe_three_gates.py
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"
OUT = []


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    except Exception as ex:
        # 通道被打死时**必须**把异常变成可读结论, 而不是让脚本崩掉(第一版就崩在 install 后的健康探针上)
        return True, "EXC:%r" % (ex,), time.time() - t0
    dt = time.time() - t0
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), dt


def health(tag):
    """JS 通道健康探针: execute_js 与 dom_query 各一次。

    判据只看**通道**(耗时可接受 + 无错误), **不比对页面内容** —— 重启后页面可能是程序自带的起始页,
    第一版把内容也当判据, 于是把健康的实例误标成"退化"。
    """
    e1, t1, d1 = call("browser_execute_js", {"code": "1+1"}, to=60)
    e2, t2, d2 = call("browser_dom_query", {"selector": "h1"}, to=60)
    ok = (not e1) and (not e2) and ("2" in t1) and d1 < 3.0 and d2 < 3.0
    print('   [%s] execute_js %.2fs err=%s | dom_query %.2fs err=%s → %s'
          % (tag, d1, e1, d2, e2, '健康' if ok else '**退化/阻塞**'))
    return ok


def restart():
    loop.kill_app()
    ok = loop.start_app()
    print('   -- 已重启: %s --' % ('就绪' if ok else '失败'))
    return ok


print('== ① browser_vip_mouse_wheel: 给真实滚动量 + 页面侧预言机 ==')
restart()
call("browser_navigate", {"url": "https://example.com/?wheel=%d" % int(time.time())})
call("browser_execute_js", {"code": "document.body.insertAdjacentHTML('beforeend','<div style=\"height:3000px\">tall</div>');window.scrollTo(0,0);'ok'"})
time.sleep(0.5)
before = call("browser_execute_js", {"code": "String(Math.round(window.pageYOffset||0))"})[1]
e1, t1, d1 = call("browser_vip_mouse_wheel", {"x": 200, "y": 200, "delta_y": 120}, to=45)
time.sleep(0.8)
after = call("browser_execute_js", {"code": "String(Math.round(window.pageYOffset||0))"})[1]
print('   调用: %.2fs err=%s %s' % (d1, e1, t1.replace('\n', ' ')[:90]))
print('   scrollY: %s -> %s' % (before[:40], after[:40]))
OUT.append(('① mouse_wheel 传参即成功', not e1, '%.2fs' % d1))
OUT.append(('① mouse_wheel 真的滚动了(预言机)', before != after, '%s->%s' % (before[:20], after[:20])))

print('\n== ② browser_vip_enable_js_env: 启用 → 检查损伤 → enable:false 回滚 → 看能否恢复 ==')
restart()
h0 = health('启用前')
e2, t2, d2 = call("browser_vip_enable_js_env", {"enable": True, "confirm": True}, to=60)
print('   启用: %.2fs err=%s %s' % (d2, e2, t2.replace('\n', ' ')[:100]))
time.sleep(1.0)
h1 = health('启用后')
e3, t3, d3 = call("browser_vip_enable_js_env", {"enable": False, "confirm": True}, to=60)
print('   关闭: %.2fs err=%s %s' % (d3, e3, t3.replace('\n', ' ')[:100]))
time.sleep(1.0)
h2 = health('关闭后')
OUT.append(('② vip_enable_js_env 启用调用成功', not e2, '%.2fs' % d2))
OUT.append(('② 启用后 JS 通道是否受损(如实记录)', True, '受损=%s' % (not h1)))
OUT.append(('② enable:false 回滚后会话恢复', h2, '恢复=%s(启用后=%s)' % (h2, h1)))

print('\n== ③ browser_reverse_instrument_script: install → 检查阻塞 → suppress 回滚 → 看能否恢复 ==')
restart()
# 先到目标页并注入高内容, 便于观察; 再从干净页面开始
call("browser_navigate", {"url": "https://example.com/?inst=%d" % int(time.time())})
h3 = health('install 前')
e4, t4, d4 = call("browser_reverse_instrument_script", {"action": "install", "confirm": True,
                                                       "event": "beforeScriptExecution"}, to=90)
print('   install: %.2fs err=%s %s' % (d4, e4, t4.replace('\n', ' ')[:110]))
time.sleep(1.0)
h4 = health('install 后')
e5, t5, d5 = call("browser_reverse_instrument_script", {"action": "suppress"}, to=90)
print('   suppress: %.2fs err=%s %s' % (d5, e5, t5.replace('\n', ' ')[:110]))
time.sleep(1.5)
h5 = health('suppress 后')
OUT.append(('③ instrument install 调用成功(带 confirm)', not e4, '%.2fs' % d4))
OUT.append(('③ install 后 JS 通道是否阻塞(如实记录)', True, '阻塞=%s' % (not h4)))
OUT.append(('③ suppress 回滚后会话恢复', h5, '恢复=%s(install后=%s)' % (h5, h4)))

print('\n== 收尾: 重启复位 ==')
restart()
print('\n===== 汇总 =====')
for tag, ok, detail in OUT:
    print('  [%s] %-46s %s' % ('PASS' if ok else 'FAIL', tag, detail))
