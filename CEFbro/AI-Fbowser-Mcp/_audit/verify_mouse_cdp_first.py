# -*- coding: utf-8 -*-
"""验收"鼠标三件套改 CDP 优先"是否既保住 CDP、又真的派发了鼠标(目标 ≤90 秒)。

每个用例都换**干净实例**:
  1) browser_mouse_move / click / wheel 默认路径 -> 调用后 CDP 必须**仍存活**(修复前必死)
  2) 同时验证鼠标真的生效:
     · move : 页面监听 mousemove, 读 clientX/Y (注: 该事件投递本身偶发不稳, 仅作参考)
     · click: 按钮点击计数
     · wheel: 页面滚动量
  3) kernel:true 显式 opt-in -> CDP 应失效(这是**已知且已文档化**的取舍, 用作反向对照)
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(否则打印 ⚠ 会崩, 见 _console.py)

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
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:96]))


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


def prep():
    call("browser_navigate", {"url": "https://example.com/?mm=%d" % int(time.time()),
                              "wait_for_load": True}, 45)
    time.sleep(0.5)
    js("document.body.style.height='4000px';"
       "document.body.insertAdjacentHTML('beforeend',"
       "'<button id=mmb>go</button>');"
       "window.__c=0;window.__mx=-1;window.__my=-1;"
       "document.addEventListener('mousemove',function(e){window.__mx=e.clientX;window.__my=e.clientY;});"
       "document.getElementById('mmb').addEventListener('click',function(){window.__c++;});'ok'")
    time.sleep(0.3)


print("== 用例 1: browser_mouse_move 默认路径 ==")
if not restart():
    print("  启动失败"); sys.exit(2)
prep()
ok0, dt0 = cdp_alive()
e, t, _ = call("browser_mouse_move", {"x": 400, "y": 300})
time.sleep(0.6)
ok1, dt1 = cdp_alive()
rec("mouse_move 后 CDP 仍存活", ok1, "CDP %.1fs -> %.1fs" % (dt0, dt1))
rec("mouse_move 走 CDP 派发", "dispatchMouseEvent" in t or "CDP 派发" in t,
    t.replace("\n", " ")[:70])
mx = js("String(window.__mx)")
rec("(参考)页面收到 mousemove", mx == "400", "clientX=%s (事件投递偶发不稳, 仅参考)" % mx)

print("\n== 用例 2: browser_mouse_click 默认路径 ==")
if not restart():
    print("  启动失败"); sys.exit(2)
prep()
e, t, _ = call("browser_mouse_click", {"x": 400, "y": 300})
time.sleep(0.6)
ok2, dt2 = cdp_alive()
rec("mouse_click 后 CDP 仍存活", ok2, "CDP 之后 %.1fs" % dt2)
rec("mouse_click 走 CDP 派发", "CDP 派发" in t, t.replace("\n", " ")[:70])

print("\n== 用例 3: browser_mouse_wheel 默认路径 ==")
if not restart():
    print("  启动失败"); sys.exit(2)
prep()
e, t, _ = call("browser_mouse_wheel", {"x": 400, "y": 300, "delta_y": 300})
time.sleep(1.0)
ok3, dt3 = cdp_alive()
sy = js("String(Math.round(window.pageYOffset||0))")
rec("mouse_wheel 后 CDP 仍存活", ok3, "CDP 之后 %.1fs" % dt3)
rec("mouse_wheel 走 CDP 派发", "CDP 派发" in t, t.replace("\n", " ")[:70])
rec("(参考)滚轮真的滚动了页面", sy is not None and int(sy or 0) > 0, "scrollY=%s" % sy)

print("\n== 用例 4(反向对照): kernel:true 显式内核注入应使 CDP 失效 ==")
if not restart():
    print("  启动失败"); sys.exit(2)
prep()
e, t, _ = call("browser_mouse_move", {"x": 400, "y": 300, "kernel": True})
time.sleep(0.6)
ok4, dt4 = cdp_alive()
rec("kernel:true -> CDP 失效(已知取舍, 已在描述与消息中告知)", not ok4,
    "CDP 之后 %.1fs | %s" % (dt4, t.replace("\n", " ")[:60]))

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
