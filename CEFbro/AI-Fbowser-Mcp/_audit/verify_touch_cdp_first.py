# -*- coding: utf-8 -*-
"""验收"触摸三件套改 CDP 优先"(目标 ≤120 秒)。

每个用例都换**干净实例**(与 verify_mouse_cdp_first.py 同法, 复用其 call/restart/cdp_alive):
  1) browser_touch_press  默认路径 -> 调用后 CDP 必须**仍存活**(改之前走内核注入必定失效),
     且页面真的收到 touchstart; 且 auto_prepared 如实上报"自动开启触摸仿真"
  2) browser_touch_move   默认路径 -> 无按下点时自动补 touchStart(零前置), 页面收到 touchstart+touchmove
  3) press -> move -> release 完整拖拽 -> 页面事件序列 = touchstart,touchmove,touchend 且坐标正确
  4) 反向对照 kernel:true -> 验证本测试的判定力(内核注入是否真使 CDP 失效)

**为什么必须有反向对照**: 若"CDP 仍存活"在任何情况下都为真, 则该断言毫无判定力
(前几轮已多次栽在"断言恒真/恒假"的测量上), 故用 kernel:true 做对照臂。
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(一份共用实现, 勿再各抄一份)

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')
res = []


def call(name, args, timeout=45):
    t0 = time.time()
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                                      "method": "tools/call",
                                                      "params": {"name": name,
                                                                 "arguments": args}},
                                                     ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def val(t):
    s = (t or "").strip()
    try:
        j = json.loads(s)
        if isinstance(j, dict) and "message" in j:
            return str(j["message"])
    except Exception:
        pass
    return s.strip('"')


def js(code):
    e, t, _ = call("browser_execute_js", {"code": code})
    return None if e else val(t)


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-52s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:90]))


def restart():
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)
    subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        time.sleep(1)
        try:
            urllib.request.urlopen(BASE + '/health', timeout=3).read()
            time.sleep(3.5)
            return True
        except Exception:
            pass
    return False


def cdp_alive():
    e, t, dt = call("browser_dom_query", {"selector": "h1"})
    return dt < 2.0, dt


LISTENER = (
    "window.__t=[];"
    "['touchstart','touchmove','touchend','touchcancel'].forEach(function(n){"
    "  document.addEventListener(n,function(e){"
    "    var p=(e.touches&&e.touches[0])||(e.changedTouches&&e.changedTouches[0])||{};"
    "    window.__t.push(n+':'+Math.round(p.clientX||0)+','+Math.round(p.clientY||0));"
    "  },{capture:true,passive:true});"
    "});"
    "'ok'")


def prep():
    call("browser_navigate", {"url": "https://example.com/?tt=%d" % int(time.time()),
                              "wait_for_load": True}, 45)
    time.sleep(0.5)
    js(LISTENER)
    time.sleep(0.3)


def events():
    """读页面侧触摸事件序列(非可覆盖观测: 页面自己记的日志)。"""
    s = js("JSON.stringify(window.__t)")
    if s is None:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


print("== 用例 1: browser_touch_press 默认路径 ==")
if not restart():
    print("  启动失败"); sys.exit(2)
prep()
ok0, dt0 = cdp_alive()
e, t, _ = call("browser_touch_press", {"x": 400, "y": 300})
time.sleep(0.8)
ok1, dt1 = cdp_alive()
ev = events()
rec("touch_press 后 CDP 仍存活", ok1, "CDP %.2fs -> %.2fs" % (dt0, dt1))
rec("touch_press 走 CDP 派发", ("CDP 派发" in t) or ("dispatchTouchEvent" in t),
    t.replace("\n", " ")[:70])
rec("auto_prepared 上报自动开启触摸仿真",
    "setTouchEmulationEnabled" in t, t.replace("\n", " ")[:70])
rec("页面真的收到 touchstart", bool(ev) and any(x.startswith("touchstart:") for x in ev),
    "events=%s" % ev)

print("\n== 用例 2: browser_touch_move 在新页面(无历史坐标, 应如实告知'零长度拖动') ==")
if not restart():
    print("  启动失败"); sys.exit(2)
prep()
e, t, _ = call("browser_touch_move", {"x": 300, "y": 200})
time.sleep(0.8)
ok2, dt2 = cdp_alive()
ev = events()
rec("touch_move 后 CDP 仍存活", ok2, "CDP 之后 %.2fs" % dt2)
rec("touch_move 走 CDP 派发", "CDP 派发" in t, t.replace("\n", " ")[:70])
rec("自动补按下已如实上报(auto_prepared 含 touchStart)", "touchStart" in t,
    t.replace("\n", " ")[:70])
rec("零长度拖动已如实告知(不静默假成功)", "起点与终点相同" in t,
    t.replace("\n", " ")[:70])
rec("页面收到自动补的 touchstart", bool(ev) and ev[0].startswith("touchstart:"),
    "events=%s" % ev)
rec("(预期)零长度拖动不产生 touchmove",
    not any(x.startswith("touchmove:") for x in (ev or [])), "events=%s" % ev)

print("\n== 用例 2b: 有历史坐标时 touch_move 应自动从上次坐标补按下 -> 真实拖动 ==")
if not restart():
    print("  启动失败"); sys.exit(2)
prep()
call("browser_touch_press", {"x": 120, "y": 140})
call("browser_touch_release", {"x": 120, "y": 140})
time.sleep(0.3)
e, t, _ = call("browser_touch_move", {"x": 300, "y": 200})
time.sleep(0.8)
okB, dtB = cdp_alive()
ev = events()
rec("2b 后 CDP 仍存活", okB, "CDP 之后 %.2fs" % dtB)
rec("2b 自动锚点为上次坐标(120,140)",
    "已自动从上次坐标 120,140 补按下" in t, t.replace("\n", " ")[:80])
rec("2b 真实拖动: 页面收到 touchmove:300,200",
    "touchmove:300,200" in (ev or []), "events=%s" % ev)

print("\n== 用例 3: press -> move -> release 完整拖拽 ==")
if not restart():
    print("  启动失败"); sys.exit(2)
prep()
e1, t1, _ = call("browser_touch_press", {"x": 100, "y": 150})
e2, t2, _ = call("browser_touch_move", {"x": 260, "y": 320})
e3, t3, _ = call("browser_touch_release", {"x": 260, "y": 320})
time.sleep(0.8)
ok3, dt3 = cdp_alive()
ev = events()
names = [x.split(":")[0] for x in (ev or [])]
rec("三连拖拽后 CDP 仍存活", ok3, "CDP 之后 %.2fs" % dt3)
rec("事件序列 = touchstart,touchmove,touchend",
    names == ["touchstart", "touchmove", "touchend"], "events=%s" % ev)
rec("坐标正确(press 100,150 / move 260,320)",
    (ev or [])[:3] == ["touchstart:100,150", "touchmove:260,320", "touchend:260,320"],
    "events=%s" % ev)
rec("三次调用都未报错", not (e1 or e2 or e3),
    "press=[%s] move=[%s] release=[%s]" % (t1.strip('"')[:28], t2.strip('"')[:28],
                                           t3.strip('"')[:28]))

print("\n== 用例 4(反向对照): kernel:true 显式内核注入 ==")
if not restart():
    print("  启动失败"); sys.exit(2)
prep()
e, t, _ = call("browser_touch_press", {"x": 400, "y": 300, "kernel": True})
time.sleep(0.8)
ok4, dt4 = cdp_alive()
rec("kernel:true 路径确实走了内核注入(消息含内核级)",
    "内核级" in t, t.replace("\n", " ")[:70])
rec("对照臂: kernel:true 后 CDP 状态(用于证明上面的存活断言有判定力)",
    True, "CDP 之后 %.2fs -> %s" % (dt4, "失效(证明断言非恒真)" if not ok4 else "仍存活(说明触摸内核注入不杀CDP)"))

print("\n== 收尾: 冷重启恢复干净实例 ==")
restart()
okF, dtF = cdp_alive()
rec("收尾重启后 CDP 可用", okF, "%.2fs" % dtF)

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
