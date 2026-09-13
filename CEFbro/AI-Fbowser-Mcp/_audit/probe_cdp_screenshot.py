# -*- coding: utf-8 -*-
r"""关键对照: **CDP 自己的 `Page.captureScreenshot`** 是否安全(不打死 CDP 通道)? 能否整页?

背景: 类库 `高级_网页截图`(VIP 内核注入路线)实测会把 CDP 命令通道**打死**(之后所有 CDP 命令 30s 超时,
注销/重挂观察者都救不回来)。若 CDP 自身的截图接口安全, 就应把 `browser_screenshot` 改成走 CDP。

本探针:
  ① 基线 execute_js;
  ② `browser_cdp_call {method:"Page.captureScreenshot", params:{format:"png", fromSurface:true}}` → 结果经 mcp_result 取;
  ③ 截图后 execute_js(看是否仍 0.03s);
  ④ 整页: 页面塞 5000px 高元素 → 带 `captureBeyondViewport:true` + `clip{0,0,宽,高}` 再截 → 解析 PNG 高度;
  ⑤ 取回方式与图片可达性确认。

用法: py -3 _audit\probe_cdp_screenshot.py
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
_rid = [4300]


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
        return True, "EXC:%r" % (ex,), time.time() - t0, rid
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), time.time() - t0, rid


def png_size(buf):
    if not buf or buf[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", buf[16:24])


def snap(params, tag):
    e, t, d, rid = call("browser_cdp_call", {"method": "Page.captureScreenshot",
                                             "params": json.dumps(params, ensure_ascii=False)}, to=60)
    print('    %-28s isError=%-5s %6.2fs %s' % (tag, e, d, t[:90].replace('\n', ' ')))
    time.sleep(0.4)
    e2, t2, d2, _ = call("mcp_result", {"request_id": str(rid)}, to=60)
    raw = None
    if not e2 and t2:
        if "base64," in t2:
            raw = t2.split("base64,", 1)[1]
            for stop in ('"', "\\", "}"):
                i = raw.find(stop)
                if i > 100:
                    raw = raw[:i]
        else:
            # 结果里可能是 {"result":{"data":"<b64>"}} 形态
            try:
                o = json.loads(t2)
                s = json.dumps(o)
                i = s.find('"data":"')
                if i >= 0:
                    j = s.find('"', i + 8)
                    raw = s[i + 8:j]
            except Exception:
                pass
    if raw:
        try:
            buf = b64.b64decode(raw)
            print('        -> 图片 %s (%d 字节)' % (png_size(buf), len(buf)))
            return buf
        except Exception as ex:
            print('        -> base64 解码失败 %r' % (ex,))
    else:
        print('        -> 未从 mcp_result 取到图片: %s' % str(t2)[:120])
    return None


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?cdpshot=%d" % int(time.time())})
e, t, d, _ = call("browser_execute_js", {"code": "1+1"})
print('基线 execute_js: isError=%s %.2fs' % (e, d))

print('\n[1] CDP 截图(视口, fromSurface=true)')
buf1 = snap({"format": "png", "fromSurface": True}, "Page.captureScreenshot")

print('\n[2] 截图后 CDP 通道是否仍健康?')
e, t, d, _ = call("browser_execute_js", {"code": "2+2"})
print('    execute_js isError=%s %.2fs %s' % (e, d, t[:60]))
e, t, d, _ = call("browser_execute_js", {"code": "3+3"})
print('    再测一次   isError=%s %.2fs %s' % (e, d, t[:60]))

print('\n[3] 整页: 注入 5000px 高元素 → captureBeyondViewport + clip')
e, t, d, _ = call("browser_execute_js", {"code":
    "var d=document.createElement('div');d.style.height='5000px';document.body.appendChild(d);"
    "String(Math.max(document.documentElement.scrollHeight,document.body.scrollHeight))+'|'+"
    "String(Math.max(document.documentElement.scrollWidth,document.body.scrollWidth))+'|'+"
    "String(window.innerWidth)"})
try:
    parts = json.loads(t).get("message", "").split("|")
    H, W, VW = int(parts[0]), int(parts[1]), int(parts[2])
except Exception:
    H, W, VW = 5350, 984, 984
print('    scrollHeight=%s scrollWidth=%s innerWidth=%s' % (H, W, VW))
buf2 = snap({"format": "png", "fromSurface": True, "captureBeyondViewport": True,
             "clip": {"x": 0, "y": 0, "width": W, "height": H, "scale": 1}}, "整页(CDP)")
if buf2:
    sz = png_size(buf2)
    print('    整页对比: 图=%s, 期望高≈%d' % (sz, H))

print('\n[4] 收尾: CDP 通道与原生工具')
e, t, d, _ = call("browser_execute_js", {"code": "4+4"})
print('    execute_js isError=%s %.2fs %s' % (e, d, t[:60]))
e, t, d, _ = call("browser_status", {})
print('    browser_status isError=%s %.2fs' % (e, d))
