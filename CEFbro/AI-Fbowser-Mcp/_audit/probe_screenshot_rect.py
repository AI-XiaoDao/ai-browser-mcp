# -*- coding: utf-8 -*-
r"""实测: `browser_screenshot` 的 rect(width/height/x/y/scale) 到底有没有生效? `from_surface` 是不是关键?

现象(上一轮): 传 width=1920 height=1080(默认) + full_page, 拿到的 PNG 却是 **984x705**(≈窗口客户区),
即疑似"截的是 view(窗口) 而不是 surface(rect 区域)", 而类库第 4 参 `是否表面` 正是 `fromSurface`。

三臂(每臂都用全新实例, 避免上一臂的副作用污染):
  A 默认(from_surface=false) + width/height=800x600
  B from_surface=true  + width/height=800x600
  C from_surface=true  + full_page=true(页面先塞 5000px 高元素)
判据: **PNG 头里的 IHDR 宽高**(图片自身的事实, 不看回包文案)。

用法: py -3 _audit\probe_screenshot_rect.py
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
_rid = [4200]


def call(n, a=None, to=90, rid=None):
    if rid is None:
        _rid[0] += 1
        rid = _rid[0]
    b = {"jsonrpc": "2.0", "id": rid, "method": "tools/call",
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


def png_size(buf):
    if not buf or buf[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", buf[16:24])


def shot(args):
    e, t, d = call("browser_screenshot", args, to=90)
    if e:
        return None, t
    raw = None
    if "base64," in t:
        raw = t.split("base64,", 1)[1]
        for stop in ('"', "\\", "}"):
            i = raw.find(stop)
            if i > 100:
                raw = raw[:i]
    if not raw:
        return None, t[:120]
    try:
        return b64.b64decode(raw), t[:160]
    except Exception as ex:
        return None, "解码失败 %r" % (ex,)


def arm(name, args, inject_tall=False, need_scroll=False):
    print('\n===== %s =====' % name)
    loop.kill_app()
    if not loop.start_app():
        print('  !! 启动失败'); return
    call("browser_navigate", {"url": "https://example.com/?shot=%d" % int(time.time())})
    scroll = 0
    if inject_tall:
        e, t, d = call("browser_execute_js", {"code":
            "var d=document.createElement('div');d.style.height='5000px';d.style.background='#123';"
            "d.id='tall';document.body.appendChild(d);"
            "String(Math.max(document.documentElement.scrollHeight, document.body.scrollHeight))"})
        try:
            scroll = int(json.loads(t).get("message"))
        except Exception:
            scroll = 0
        print('  注入后 scrollHeight=%s' % scroll)
    e, t, d = call("browser_execute_js", {"code": "String(window.innerWidth)+'x'+String(window.innerHeight)"})
    try:
        view = json.loads(t).get("message")
    except Exception:
        view = t[:30]
    print('  视口=%s' % view)
    buf, note = shot(args)
    print('  截图: %s | 回执/说明=%s' % (png_size(buf) if buf else "未取到", note[:110]))
    if buf and need_scroll:
        sz = png_size(buf)
        print('  与 scrollHeight 对比: 图高=%s, scrollHeight=%s' % (sz[1] if sz else "?", scroll))
    return png_size(buf)


arm('A 默认(from_surface 缺省=假) + 800x600', {"width": 800, "height": 600, "format": "png"})
arm('B from_surface=true + 800x600', {"width": 800, "height": 600, "format": "png", "from_surface": True})
arm('C from_surface=true + full_page(5000px 页)', {"format": "png", "from_surface": True, "full_page": True},
    inject_tall=True, need_scroll=True)
