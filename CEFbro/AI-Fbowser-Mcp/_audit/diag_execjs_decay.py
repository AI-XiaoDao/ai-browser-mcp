# -*- coding: utf-8 -*-
"""定位 browser_execute_js(原生 CEF JS 回调通道)为何在会话中途永久失效。

上一轮实测(同一实例同一时刻):
    browser_execute_js {code:"1+1"}      -> 5.1s 超时  ❌
    browser_dom_query {selector:"h1"}    -> 0.0s 正常  ✅  (CDP 通道健康)
即两条 JS 通道会各自独立失效, 且原生通道一死就是"连 1+1 都超时"。

本脚本做受控实验, 区分几个互斥假设:
  H1 累计调用次数阈值(回调表/智能指针泄漏)
  H2 导航使回调绑定失效(旧框架回调残留)
  H3 与 CDP 通道相互独立(对照 CDP 是否一直健康)
  H4 重新导航能否恢复

输出逐次结果 + 失败点 + 恢复尝试, 便于定位。
"""
import importlib.util
import sys
import time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

sys.path.insert(0, '.')
spec = importlib.util.spec_from_file_location("v4", "verify_round4.py")
v4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)

URL = "https://example.com/"
MAXCALL = int(sys.argv[1]) if len(sys.argv) > 1 else 30


def js_ok(tag, code="1+1", timeout=25):
    """成功判据: 响应成功 且 值 == 2。

    注意 browser_execute_js 改为 CDP 优先后会返回**同步信封**
    `{"id":..,"success":true,"message":"2"}`, 而原生回退链路返回的是异步提交信封。
    故这里必须解包 message 再比较 —— 上一版直接比较原始文本, 把"已修好的成功"误判成失败。
    """
    import json as _json
    t0 = time.time()
    e, t, _ = v4.call("browser_execute_js", {"code": code}, timeout)
    dt = time.time() - t0
    val = t.strip()
    try:
        j = _json.loads(val)
        if isinstance(j, dict) and "message" in j:
            val = str(j["message"])
    except Exception:
        val = val.strip('"')
    ok = (not e) and (val == "2")
    print("  %-30s %5.1fs err=%-5s val=%-4s %s" % (tag, dt, e, val[:4], t.replace("\n", " ")[:60]))
    return ok


def cdp_ok(tag):
    t0 = time.time()
    e, t, _ = v4.call("browser_dom_query", {"selector": "h1"}, 30)
    dt = time.time() - t0
    ok = (not e) and ("Example Domain" in t)
    print("  %-30s %5.1fs err=%-5s %s" % (tag, dt, e, t.replace("\n", " ")[:70]))
    return ok


print("== 准备 ==")
v4.call("browser_navigate", {"url": URL, "wait_for_load": True}, 60)
time.sleep(1.5)
js_ok("预热 execute_js")

print("\n== 连续调用 execute_js, 找失效点 ==")
first_fail = None
for i in range(1, MAXCALL + 1):
    ok = js_ok("第%02d次" % i)
    if not ok and first_fail is None:
        first_fail = i
        print("      ^^^ 首次失败于第 %d 次" % i)
        break
    if i % 10 == 0:
        cdp_ok("  (对照)CDP dom_query @%d" % i)

print("\n== 失效后: CDP 是否仍健康 ==")
cdp_ok("失效后 CDP dom_query")

if first_fail is not None:
    print("\n== H4: 重新导航能否恢复 ==")
    v4.call("browser_navigate", {"url": URL + "?r=%d" % int(time.time()), "wait_for_load": True}, 60)
    time.sleep(2)
    js_ok("导航后 execute_js")
    print("\n== H4b: 重新载入能否恢复 ==")
    v4.call("browser_reload", {"wait_for_load": True}, 60)
    time.sleep(2)
    js_ok("reload 后 execute_js")
    print("\n== H4c: 等 10s 后再试(是否自愈) ==")
    time.sleep(10)
    js_ok("等待 10s 后 execute_js")
else:
    print("\n== %d 次连续调用全部成功, 未复现失效 ==" % MAXCALL)
    cdp_ok("收尾 CDP dom_query")
