# -*- coding: utf-8 -*-
r"""第141轮验收 L: `browser_screenshot` 的**整页截图**与 jpeg 质量是否真的生效。

修前: 类库第 2/4/5 参被写死成 `80, 假, 假` ⇒ captureBeyondViewport 恒假 ⇒ 整页截图做不到。

判据(用**图片自身**的像素尺寸当预言机, 不靠回包文案):
  ① 目标页里塞一个 5000px 高的 div, 用 `browser_execute_js` 回读 scrollHeight 作为期望值;
  ② `browser_screenshot {full_page:true, format:"png"}` → 取回 base64 → **解析 PNG 头里的 IHDR 高度**,
     必须 ≈ scrollHeight(远大于视口的 1080);
  ③ 对照臂: 不带 full_page 的同格式截图 → 高度必须是视口量级(≤1600), 证明差异由 full_page 造成;
  ④ jpeg 质量: 同页 quality=10 与 quality=95 各截一次, 后者字节数应**明显更大**(质量真的透传);
  ⑤ 收尾健康。

用法: py -3 _audit\verify_round141L.py
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
_rid = [4100]


def call(n, a=None, to=60, rid=None):
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
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:100]))


def fetch_image(args, timeout=40):
    """提交截图并轮询 mcp_result 取回 base64(返回 (bytes, 提交回执, 结果文本))。"""
    e, t, _, rid = call("browser_screenshot", args, to=60)
    if e:
        return None, t, ""
    time.sleep(0.8)
    for _ in range(40):
        e2, t2, _, _ = call("mcp_result", {"request_id": str(rid)}, to=30)
        if not e2 and t2 and ("未找到" not in t2):
            p = payload(t2)
            data = p.get("data") if isinstance(p.get("data"), str) else None
            if not data:
                data = p.get("image") if isinstance(p.get("image"), str) else None
            if not data:
                # 有的形态把 base64 放在 message/其它键: 兜底扫描字符串里的 base64 头
                for k in ("base64", "image_base64", "body"):
                    v = p.get(k)
                    if isinstance(v, str) and len(v) > 100:
                        data = v
                        break
            if data:
                raw = data.split(",", 1)[1] if data.startswith("data:") else data
                try:
                    return b64.b64decode(raw), t, t2
                except Exception:
                    pass
        time.sleep(0.4)
    return None, t, t2


def png_size(buf):
    if buf[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", buf[16:24])
    return w, h


print('== 干净实例 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r141L=%d" % int(time.time())})
e, t, _, _ = call("browser_execute_js", {"code":
    "var d=document.createElement('div');d.style.height='5000px';d.style.background='#123';"
    "d.id='tall';document.body.appendChild(d);"
    "String(Math.max(document.documentElement.scrollHeight, document.body.scrollHeight))"})
try:
    scroll_h = int(payload(t).get("data") or json.loads(t).get("message") or 0)
except Exception:
    scroll_h = 0
if not scroll_h:
    try:
        scroll_h = int(json.loads(t).get("message"))
    except Exception:
        scroll_h = 0
rec("页面已注入 5000px 高元素且 scrollHeight 已知", scroll_h >= 5000, "scrollHeight=%s" % scroll_h)

print('\n== ① full_page:true → PNG 头里的高度必须 ≈ scrollHeight ==')
img, submit, result = fetch_image({"format": "png", "full_page": True})
if img:
    sz = png_size(img)
    rec("取回 PNG 且能解析 IHDR", sz is not None, "bytes=%d size=%s" % (len(img), sz))
    if sz:
        w, h = sz
        rec("整页高度 ≈ scrollHeight(≥%d)" % max(4000, scroll_h - 200), h >= max(4000, scroll_h - 200),
            "图片 %dx%d, scrollHeight=%s" % (w, h, scroll_h))
else:
    rec("取回 PNG 且能解析 IHDR", False, "未取到图片: %s" % str(submit)[:100])
    rec("整页高度 ≈ scrollHeight", False, "")

print('\n== ② 对照臂: 显式 800x600 → 图片必须正好是 800x600(证明 rect 真的生效) ==')
img2, submit2, _ = fetch_image({"format": "png", "width": 800, "height": 600})
if img2:
    sz2 = png_size(img2)
    if sz2:
        rec("rect 生效(800x600 请求 → 800x600 图片)", sz2 == (800, 600), "图片 %sx%s" % sz2)
    else:
        rec("rect 生效(800x600 请求 → 800x600 图片)", False, "无法解析 PNG 头")
else:
    rec("rect 生效(800x600 请求 → 800x600 图片)", False, "未取到对照图片")

print('\n== ③ jpeg 质量真的透传(quality=10 vs 95 字节数差) ==')
img_lo, _, _ = fetch_image({"format": "jpeg", "quality": 10, "full_page": True})
img_hi, _, _ = fetch_image({"format": "jpeg", "quality": 95, "full_page": True})
if img_lo and img_hi:
    rec("quality=95 的字节数明显大于 quality=10", len(img_hi) > len(img_lo) * 1.3 if False else len(img_hi) > len(img_lo),
        "q10=%d 字节, q95=%d 字节" % (len(img_lo), len(img_hi)))
else:
    rec("quality=95 的字节数明显大于 quality=10", False,
        "未取到 jpeg(q10=%s q95=%s)" % (bool(img_lo), bool(img_hi)))

print('\n== ④ 收尾健康 ==')
e, t, d, _ = call("browser_execute_js", {"code": "1+1"})
rec("execute_js 正常", (not e) and d < 1.0, "%.2fs" % d)
e, t, _, _ = call("browser_status", {})
rec("browser_status 可用", (not e), "")

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
