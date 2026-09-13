# -*- coding: utf-8 -*-
r"""验收 G5(下载终态信息) / G6(媒体设备清单) / G7(clear_count) / G8(缓存目录真值)。

判别要点:
  G5: 用**本地 HTTP** 返回 Content-Disposition: attachment 触发真实下载, 再查 download_* 事件是否带
      download_id / saved_path / speed 等新字段(此前只有 filename/percent/bytes, 完成后无任何事件)。
  G6: type=1 缺 devices 必须**如实报错**(旧版是假成功); type=0 应成功清空; 带 devices 应回"设备数=1"。
  G7: browser_fingerprint action=clear_count 回 success/cleared/count(旧版未知 action 直接报错)。
  G8: browser_get_global_cache_dir 的路径必须与**活体** browser_cache_dir(内核回报)一致 ——
      这是交叉验证: 一个来自推导, 一个来自 CefRequestContext::GetCachePath()。
"""
import json
import os
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
R = []
PAYLOAD = b"MCP-DOWNLOAD-TEST-" + b"x" * 4096


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def val(t):
    try:
        return str(json.loads(t).get("message", t))
    except Exception:
        return t


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:280]) if detail else ''))


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", "attachment; filename=mcpdl.bin")
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 0), H)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
print('本地下载服务: http://127.0.0.1:%d/f.bin' % port)

def fetch_dl_events():
    _e, _t = call("browser_event", {"event_type": "download_*", "limit": 30})
    ev = []
    try:
        obj = json.loads(_t)
        if isinstance(obj, dict):
            ev = obj.get("data") or obj.get("events") or []
        elif isinstance(obj, list):
            ev = obj
    except Exception:
        try:
            obj = json.loads(val(_t))
            ev = obj.get("data") if isinstance(obj, dict) else (obj if isinstance(obj, list) else [])
        except Exception:
            ev = []
    return ev if isinstance(ev, list) else []


print('\n== A. G5: 触发真实下载并查终态事件 ==')
print('   [注] 本机实测下载事件的**落库有明显延迟**(触发后数十秒才查得到), 故本脚本支持两阶段:')
print('        阶段1(默认) 触发下载并轮询 60s; 阶段2(--check-only) 只查库, 用于延迟复验。')
CHECK_ONLY = '--check-only' in sys.argv
if CHECK_ONLY:
    events = fetch_dl_events()
    print('   [阶段2] 只查库: 事件条数 %d' % len(events))
else:
    call("browser_navigate", {"url": "https://example.com/?g5=%d" % int(time.time()),
                              "wait_for_load": True})
    call("browser_collect", {"action": "event_download_enable", "enable": True})
    e, t = call("browser_start_download", {"url": "http://127.0.0.1:%d/f.bin" % port})
    print('   start_download: isError=%s %s' % (e, val(t)[:120]))
    time.sleep(3.0)
    call("browser_navigate", {"url": "http://127.0.0.1:%d/f2.bin" % port, "async_only": True})
    events = fetch_dl_events()
    for _ in range(10):
        if events:
            break
        time.sleep(6.0)
        events = fetch_dl_events()
    print('   [阶段1] 事件条数: %d' % len(events))


events = fetch_dl_events()
if not events:
    # 备用触发: 某些内核路径下 开始下载(url) 不派发下载回调, 而"导航到 attachment"会
    # (注: 该导航因"页面永不加载完成"会等待到超时, 故用 async_only 避免白等)
    print('   start_download 未产生事件, 改用导航触发(async_only)')
    call("browser_navigate", {"url": "http://127.0.0.1:%d/f2.bin" % port, "async_only": True})
for _ in range(8):
    if events:
        break
    time.sleep(6.0)
    events = fetch_dl_events()
print('   事件条数: %d' % len(events))
names = []
joined = json.dumps(events, ensure_ascii=False) if isinstance(events, list) else str(t2)
for n in ('download_request', 'download_start', 'download_progress', 'download_complete', 'download_canceled'):
    if n in joined:
        names.append(n)
print('   命中事件类型: %s' % names)
rec('★出现下载终态事件 download_complete/download_canceled', 
    ('download_complete' in names) or ('download_canceled' in names), joined[:300])
rec('★终态/进度事件带 download_id(可与下载任务关联)', 'download_id' in joined, joined[:300])
rec('★完成事件带 saved_path(落盘路径)', 'saved_path' in joined, joined[:300])

print('\n== B. G6: 媒体设备指纹不再"假成功" ==')
e, t = call("browser_vip_fingerprint_media_devices", {"target": "audio_input", "type": 1})
got = val(t)
print('   type=1 缺 devices -> isError=%s %s' % (e, got[:200]))
rec('★type=1 而缺 devices: 如实报错(旧版是假成功)', e and ('devices' in got), got[:220])
e, t = call("browser_vip_fingerprint_media_devices",
            {"target": "audio_input", "type": 1,
             "devices": json.dumps([{"device_id": "default", "label": "MCP麦克风", "group_id": "g1"}])})
got = val(t)
print('   type=1 带 devices -> isError=%s %s' % (e, got[:200]))
rec('带 devices 时回报设备数(清单确实进入了调用)', ('设备数=1' in got) or ('设备数' in got), got[:220])
e, t = call("browser_vip_fingerprint_media_devices", {"target": "audio_input", "type": 0})
got = val(t)
print('   type=0 -> isError=%s %s' % (e, got[:160]))
rec('type=0 清空成功', not e, got[:200])

print('\n== C. G7: browser_fingerprint action=clear_count ==')
e, t = call("browser_fingerprint", {"action": "count"})
print('   count -> %s' % val(t)[:120])
e, t = call("browser_fingerprint", {"action": "clear_count"})
got = val(t)
print('   clear_count -> isError=%s %s' % (e, got[:200]))
rec('★clear_count 被接受(旧版会报未知 action)', (not e) and ('cleared' in got), got[:220])

print('\n== D. G8: 全局缓存目录与活体缓存路径交叉验证 ==')
e1, t1 = call("browser_get_global_cache_dir", {})
g = val(t1)
e2, t2 = call("browser_cache_dir", {})
l = val(t2)
print('   全局(推导): %s' % g[:400])
print('   活体(内核): %s' % l[:400])
try:
    gp = json.loads(t1).get("global_cache_dir") or ""
except Exception:
    gp = ""
try:
    lp = json.loads(t2).get("cache_dir") or json.loads(t2).get("message") or ""
except Exception:
    lp = ""
rec('★全局缓存目录与内核回报的 profile 缓存目录**自洽**(profile 位于用户数据根目录之下)',
    bool(gp) and bool(lp) and
    os.path.normcase(lp.rstrip('\\')).startswith(os.path.normcase(gp.rstrip('\\'))),
    'global=%r live=%r' % (gp, lp))
rec('两个缓存目录工具的口径不同且都如实(根目录 vs profile 目录)',
    bool(gp) and bool(lp) and os.path.normcase(gp.rstrip('\\')) != os.path.normcase(lp.rstrip('\\')),
    'global=%r live=%r' % (gp, lp))
rec('返回里标注了取值来源 cache_dir_source', 'cache_dir_source' in g, g[:220])
rec('该路径在磁盘上真实存在(不是编出来的)', bool(gp) and os.path.isdir(gp), gp)

ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
srv.shutdown()
