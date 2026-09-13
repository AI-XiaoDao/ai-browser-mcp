# -*- coding: utf-8 -*-
r"""G5 定位: 本地 attachment 下载是否真的发生、download_* 事件是否落库。"""
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
PAYLOAD = b"MCP-DL-" + b"y" * 8192


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
                                            if i.get("type") == "text")


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", "attachment; filename=mcpdl2.bin")
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 0), H)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = "http://127.0.0.1:%d/f.bin" % port
print('下载源: %s' % url)

call("browser_navigate", {"url": "https://example.com/?g5b=%d" % int(time.time()),
                          "wait_for_load": True})
print('下载事件开关: %s' % call("browser_collect", {"action": "event_download_enable", "enable": True})[1][:160])
print('自动保存开关: %s' % call("browser_status", {})[1][:200])

print('\n-- 方式1: browser_start_download --')
print('   回包: %s' % call("browser_start_download", {"url": url})[1][:200])
time.sleep(5.0)

print('\n-- 方式2: 直接导航到该 URL(CEF 会按 Content-Disposition 触发下载) --')
print('   回包: %s' % call("browser_navigate", {"url": url, "wait_for_load": True})[1][:200])
time.sleep(5.0)

for label, args in (('时间线(不限类型)', {"limit": 60}),
                    ('download_*', {"event_type": "download_*", "limit": 40}),
                    ('download_start', {"event_type": "download_start", "limit": 10}),
                    ('download_progress', {"event_type": "download_progress", "limit": 10}),
                    ('download_complete', {"event_type": "download_complete", "limit": 10})):
    e, t = call("browser_event", args)
    print('\n-- browser_event %s --' % label)
    print('   isError=%s len=%d' % (e, len(t)))
    print('   %s' % t[:600].replace('\n', ' '))

# 下载目录里有没有新文件
cand = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker')
for root in (os.path.join(os.environ.get('USERPROFILE', ''), 'Downloads'), cand):
    try:
        fs = [f for f in os.listdir(root) if 'mcpdl' in f.lower()]
        if fs:
            print('\n落盘文件(%s): %s' % (root, fs))
    except Exception:
        pass
srv.shutdown()
