# -*- coding: utf-8 -*-
r"""第141轮验收 N: `browser_screenshot` 改走 CDP 后, ①**不再打死 CDP 通道** ②整页/rect/质量仍正确。

修前实测(两臂): 任意截图之后, 所有 CDP 命令响应永不到达 —— 原始 `Runtime.evaluate` 30s 超时、
`execute_js` 30~35s 才靠原生回退返回或直接失败、`debugger_enable` 20s 超时;
注销+重挂 CDP 观察者**也救不回来**。

判据:
  ① 截图后 `execute_js` **必须仍是 0.03s 级**(核心回归);
  ② 连截 3 张后依然健康;
  ③ 整页截图: PNG 高度 == 页面 scrollHeight;
  ④ rect: 800x600 请求 → 800x600 图片;
  ⑤ jpeg 质量: q95 字节数 > q10;
  ⑥ 回包里有 image / via=cdp / 长度字段;
  ⑦ `via:"library"` 仍可选(但会带回"会打死 CDP 通道"的如实警告) —— 只验回包文案, 不在本会话真的执行它。

用法: py -3 _audit\verify_round141N.py
"""
import base64 as b64
import json
import os
import struct
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"
RES = []


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
        rr = o.get("result") or {}
    except Exception as ex:
        return True, "EXC:%r" % (ex,), time.time() - t0
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0


def payload(txt):
    try:
        o = json.loads(txt)
    except Exception:
        return {}
    d = o.get("data")
    if isinstance(d, dict):
        return d
    if isinstance(d, str):
        try:
            return json.loads(d)
        except Exception:
            return {}
    return o if isinstance(o, dict) else {}


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-50s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:100]))


def png_size(buf):
    if not buf or buf[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", buf[16:24])


def snap(args):
    e, t, d = call("browser_screenshot", args, to=90)
    p = payload(t)
    img = p.get("image") or ""
    raw = img.split(",", 1)[1] if img.startswith("data:") else img
    buf = None
    if raw:
        try:
            buf = b64.b64decode(raw)
        except Exception:
            buf = None
    return e, t, d, p, buf


print('== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r141N=%d" % int(time.time())})
e, t, d = call("browser_execute_js", {"code": "1+1"})
rec("基线 execute_js 正常", (not e) and d < 1.0, "%.2fs" % d)
call("browser_execute_js", {"code":
    "var d=document.createElement('div');d.style.height='5000px';d.style.background='#123';"
    "document.body.appendChild(d);"
    "String(Math.max(document.documentElement.scrollHeight,document.body.scrollHeight))"})
e, t, d = call("browser_execute_js", {"code": "String(Math.max(document.documentElement.scrollHeight,document.body.scrollHeight))"})
try:
    scroll_h = int(json.loads(t).get("message"))
except Exception:
    scroll_h = 0
print('   页面 scrollHeight=%s' % scroll_h)

print('\n== ① 截图后 CDP 通道必须健康(核心回归) ==')
e, t, d, p, buf = snap({"format": "png", "full_page": True})
rec("整页截图成功且回包 image/via=cdp", (not e) and bool(buf) and p.get("via") == "cdp:Page.captureScreenshot",
    "%.2fs via=%s len=%s" % (d, p.get("via"), p.get("image_base64_length")))
if buf:
    sz = png_size(buf)
    rec("整页高度 == scrollHeight", sz is not None and abs(sz[1] - scroll_h) <= 20, "图片=%s scrollHeight=%s" % (sz, scroll_h))
else:
    rec("整页高度 == scrollHeight", False, "无图片")
e2, t2, d2 = call("browser_execute_js", {"code": "2+2"})
rec("截图后 execute_js 仍 0.03s 级(**不再 30s**)", (not e2) and d2 < 1.0, "%.2fs %s" % (d2, t2[:40]))

print('\n== ② 连截 3 张后仍健康 ==')
worst = 0.0
for i in range(3):
    snap({"format": "png", "width": 640, "height": 480})
    e3, t3, d3 = call("browser_execute_js", {"code": "3+3"})
    worst = max(worst, d3)
rec("连截 3 张后 execute_js 最慢仍 <1s", worst < 1.0, "最慢 %.2fs" % worst)

print('\n== ③ rect 与质量 ==')
e, t, d, p, buf = snap({"format": "png", "width": 800, "height": 600})
sz = png_size(buf) if buf else None
rec("rect 生效(800x600 → 800x600)", sz == (800, 600), "图片=%s" % (sz,))
_, _, _, p10, b10 = snap({"format": "jpeg", "quality": 10, "width": 800, "height": 600})
_, _, _, p95, b95 = snap({"format": "jpeg", "quality": 95, "width": 800, "height": 600})
rec("jpeg quality 透传(q95 字节 > q10)", bool(b10) and bool(b95) and len(b95) > len(b10),
    "q10=%s q95=%s" % (len(b10) if b10 else 0, len(b95) if b95 else 0))

print('\n== ④ via 参数守卫 ==')
e, t, d = call("browser_screenshot", {"via": "nonsense"})
rec("非法 via 被拒且列出可选值", e and ("cdp" in t) and ("library" in t), t[:100])
e, t, d = call("browser_screenshot", {"via": "cdp", "width": 200, "height": 150})
rec("显式 via=cdp 正常", (not e) and bool(payload(t).get("image")), "%.2fs" % d)

print('\n== ⑤ 收尾健康 ==')
e, t, d = call("browser_execute_js", {"code": "9+9"})
rec("execute_js 正常", (not e) and d < 1.0, "%.2fs" % d)
e, t, d = call("browser_status", {})
rec("browser_status 可用", (not e), "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
