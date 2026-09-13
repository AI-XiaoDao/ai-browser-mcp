# -*- coding: utf-8 -*-
"""验证"字符串型参数被静默吞掉"这一系统性缺陷是否已修(真/假 A/B 对照)。

审计结论: yyjson取逻辑 对字符串 "true" 返回假; yyjson取整数 对字符串 "100" 返回 0;
本项目自己的注释也承认过同类事故(MCP_Server_Core.wsv:602
  "字符串"right"/"middle"取整数恒为0会误按左键")。

修复方式: 在 4 个共享读取器(MCP_Server.wsv 的 yyjson取整数/取小数/取长整数/取逻辑)
上按节点实际类型归一化, 一次性覆盖全部 280 个工具。

本文件已修掉三类**自身测试缺陷**(每一类都曾造成误判):
  1) 同一页面做 A/B 两臂 -> 第二臂被第一臂累积量污染(滚动位置累加)。现每臂独立新页面。
  2) 用例内部再次换页 -> 刚注入的元素被冲掉, 预言机读到 null。现"注入-操作-读回"
     在同一次导航内完成。
  3) 预言机自身超时被当作工具失败。现在只在重试耗尽后才判失败。
"""
import importlib.util
import sys
import time
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
sys.path.insert(0, '.')
spec = importlib.util.spec_from_file_location("v4", "verify_round4.py")
v4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)

N = [0]
results = []


def call(name, args, timeout=45):
    return v4.call(name, args, timeout)


def oracle(expr, tries=2, allow_empty=False):
    import json as _json
    def _unwrap(s):
        s = (s or "").strip()
        try:
            j = _json.loads(s)
            if isinstance(j, dict) and "message" in j:
                return str(j["message"])
        except Exception:
            pass
        return s.strip('"')
    """读页面真值(CDP)。只在重试耗尽后才返回失败标记。

    allow_empty=True 用于"期望值本身就是空串"的用例(如清空输入框):
    CDP 对空字符串返回 "", 若不放开会被误判为读取失败。
    """
    last = ""
    for _ in range(tries):
        e, t, _ = call("browser_execute_js", {"code": expr}, 30)
        if not e:
            # 必须解包 message 信封(browser_execute_js 已改为 CDP 优先, 返回同步信封)
            v = _unwrap(t)
            ok = (not v.startswith("{")) and v not in ("null", "undefined") and "操作超时" not in v
            if ok and (allow_empty or v != ""):
                return v
            last = v
        else:
            last = t[:60]
        time.sleep(0.6)
    return "<ORACLE-FAIL:%s>" % last


def fresh():
    """唯一 URL 强制真实导航 + 唯一 ID。"""
    N[0] += 1
    run = "c%d%s" % (N[0], str(int(time.time()))[-4:])
    call("browser_navigate",
         {"url": "https://example.com/?ab=%s" % run, "wait_for_load": True}, 60)
    time.sleep(0.7)
    ids = {"in": "in" + run}
    call("browser_execute_js", {"code": (
        "window.__mx=-1;"
        "document.addEventListener('mousemove',function(e){window.__mx=e.clientX;});"
        "document.body.style.height='5000px';"
        "document.body.insertAdjacentHTML('beforeend',"
        "'<input id=\"%s\" value=\"OLD\">');'ok'" % ids["in"])}, 30)
    time.sleep(0.3)
    return ids


def rec(tag, ok, detail):
    results.append((tag, ok, detail))
    print("  [%s] %-44s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:150]))


print("== 用例1: 鼠标坐标 —— 每臂独立新页面 ==")
# 判定依据改为**工具自报的坐标**: 这是"字符串是否被正确解析"的直接证据。
# 不再依赖页面是否收到 DOM mousemove —— 实测 VIP 鼠标移动是否派发 DOM 事件**不稳定**
# (int 型有时也收不到, 与参数解析无关), 用它当判据会把不稳定当成缺陷/把缺陷当通过。
for label, args, want in (("int {x:400,y:300}", {"x": 400, "y": 300}, "(400,300)"),
                          ("str {x:'400',y:'300'}", {"x": "400", "y": "300"}, "(400,300)")):
    fresh()
    time.sleep(0.8)
    e, t, _ = call("browser_mouse_move", args, 30)
    ok = (not e) and (want in t)
    dom = oracle("String(window.__mx)")
    rec("mouse_move %s" % label, ok,
        "工具回复=%r 期望含 %s | (参考)页面mousemove.clientX=%s" % (t[:62], want, dom))

print("\n== 用例2: 滚动坐标 —— 每臂独立新页面(避免滚动位置累加) ==")
for label, args in (("int {y:100}", {"x": 0, "y": 100}),
                    ("str {y:'100'}", {"x": "0", "y": "100"})):
    fresh()
    e, t, _ = call("browser_scroll_by", args, 40)
    got = oracle("String(Math.round(window.scrollY))")
    rec("scroll_by %s" % label, got == "100",
        "页面 scrollY=%r 期望'100' | resp=%s" % (got, t[:90]))

print("\n== 用例3: allow_empty:true 清空字段(取整数 读布尔节点) ==")
ids = fresh()
call("browser_dom_set_value", {"selector": "#" + ids["in"], "value": "OLD"}, 40)
before = oracle("document.getElementById('%s').value" % ids["in"])
e, t, _ = call("browser_dom_set_value",
               {"selector": "#" + ids["in"], "value": "", "allow_empty": True}, 40)
after = oracle("document.getElementById('%s').value" % ids["in"], allow_empty=True)
rec("dom_set_value allow_empty:true 清空", (not e) and after == "",
    "清空前=%r 清空后=%r 期望'' | resp=%s" % (before, after, t[:90]))

print("\n== 用例4: 布尔参数的字符串形式 ==")
call("browser_fingerprint_online", {"value": False}, 30)
time.sleep(0.4)
call("browser_reload", {"wait_for_load": True}, 60)
time.sleep(1.2)
v_false = oracle("String(navigator.onLine)")
call("browser_fingerprint_online", {"value": "true"}, 30)
time.sleep(0.4)
call("browser_reload", {"wait_for_load": True}, 60)
time.sleep(1.2)
v_str = oracle("String(navigator.onLine)")
rec("fingerprint_online 真false->false, 字符串'true'->true",
    v_false == "false" and v_str == "true",
    "真布尔false->%r 字符串'true'->%r" % (v_false, v_str))

print("\n== 汇总 ==")
bad = [x for x in results if not x[1]]
print("  通过 %d / %d" % (len(results) - len(bad), len(results)))
for tag, _, d in bad:
    print("  未通过: %s -> %s" % (tag, str(d)[:140]))
sys.exit(1 if bad else 0)
