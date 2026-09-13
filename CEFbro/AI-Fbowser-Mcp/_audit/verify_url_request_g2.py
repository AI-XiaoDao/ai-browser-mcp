# -*- coding: utf-8 -*-
r"""G2 验收: 用**本机回显服务器**证明 POST 体/自定义请求头真的发出去了, 且状态码真的回读了。

为什么用本机回显而不是外网: 判据要**确定**(方法/头/体/状态码都由我控制), 且不依赖外网可达性。
回显服务器记录最后一次请求的 method/path/headers/body, 并按路径返回不同状态码。

判据:
  ① POST: 服务器看到 method=POST、body 逐字一致、自定义头一致; 工具回包 status_code=200 且 http_ok=true
  ② GET /notfound: 工具回包 status_code=404 且 http_ok=false (修前两者毫无区别)
  ③ 仅带头不带体的 GET: 头同样生效
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
PORT = 18099
SEEN = {}
R = []


class Echo(BaseHTTPRequestHandler):
    def _handle(self, method):
        n = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(n).decode('utf-8', 'replace') if n else ''
        SEEN.clear()
        SEEN.update({"method": method, "path": self.path,
                     "headers": {k: v for k, v in self.headers.items()},
                     "body": body})
        if self.path.startswith('/notfound'):
            self.send_response(404)
            payload = b'{"error":"not here"}'
        else:
            self.send_response(200)
            payload = ('{"echo_marker":"MCP_ECHO_OK","path":"%s"}' % self.path).encode('utf-8')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self._handle('GET')

    def do_POST(self):
        self._handle('POST')

    def log_message(self, *a):
        pass


srv = HTTPServer(('127.0.0.1', PORT), Echo)
threading.Thread(target=srv.serve_forever, daemon=True).start()
print('回显服务器已启动: http://127.0.0.1:%d/' % PORT)


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    if o.get("error"):
        return True, "JSONRPC_ERROR: " + json.dumps(o["error"], ensure_ascii=False)
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def rec(label, ok, detail=''):
    R.append((label, ok))
    print('   [%s] %s%s' % ('PASS' if ok else 'FAIL', label,
                            ('\n        ' + str(detail)[:300]) if detail else ''))


def run_request(args, wait=8.0):
    """发起 URL 请求并轮询 mcp_result 取最终结果。"""
    e, t = call("browser_create_url_request", args, 30)
    tid = None
    import re
    m = re.search(r'task_\d+_\d+_\d+', t)
    if m:
        tid = m.group(0)
    final = t
    deadline = time.time() + wait
    while tid and time.time() < deadline:
        time.sleep(0.6)
        _, final = call("mcp_result", {"request_id": tid}, 30)
        if '"data_size"' in final or 'status_code' in final or 'http_ok' in final or '失败' in final:
            break
    return t, final, tid


print('\n== ① POST + 自定义头 ==')
body = 'a=1&b=中文'
t0, final, tid = run_request({"url": "http://127.0.0.1:%d/post" % PORT, "method": "POST",
                              "headers": "X-MCP-Probe: hello-117\nX-Second: two",
                              "body": body}, 10)
print('   提交回包: %s' % t0[:160])
print('   最终结果: %s' % final[:320])
print('   服务器看到: method=%s path=%s' % (SEEN.get('method'), SEEN.get('path')))
print('   服务器收到 body=%r' % SEEN.get('body'))
print('   服务器收到头: X-MCP-Probe=%r X-Second=%r'
      % (SEEN.get('headers', {}).get('X-MCP-Probe'), SEEN.get('headers', {}).get('X-Second')))
rec('POST 方法真的发出去了', SEEN.get('method') == 'POST', 'method=%s' % SEEN.get('method'))
rec('请求体逐字一致(含中文)', SEEN.get('body') == body, 'body=%r 期望 %r' % (SEEN.get('body'), body))
rec('自定义请求头两条都到达', SEEN.get('headers', {}).get('X-MCP-Probe') == 'hello-117'
    and SEEN.get('headers', {}).get('X-Second') == 'two', json.dumps(SEEN.get('headers', {}), ensure_ascii=False)[:200])
rec('★回包给出 status_code=200 且 http_ok=true',
    '"status_code":200' in final and '"http_ok":true' in final, final[:260])
rec('响应体标记可读', 'MCP_ECHO_OK' in final, final[:220])

print('\n== ② 404 必须与 200 区分 ==')
t1, final1, _ = run_request({"url": "http://127.0.0.1:%d/notfound" % PORT, "method": "GET"}, 10)
print('   最终结果: %s' % final1[:300])
rec('★404 回包 status_code=404 且 http_ok=false',
    '"status_code":404' in final1 and '"http_ok":false' in final1, final1[:260])

print('\n== ③ 仅带头、不带体的 GET ==')
t2, final2, _ = run_request({"url": "http://127.0.0.1:%d/getonly" % PORT,
                             "headers": "X-Only-Header: yes"}, 10)
print('   服务器看到: method=%s X-Only-Header=%r' % (SEEN.get('method'), SEEN.get('headers', {}).get('X-Only-Header')))
rec('未给 method 时仍是 GET(不被 body 规则误改)', SEEN.get('method') == 'GET', 'method=%s' % SEEN.get('method'))
rec('只带头也生效', SEEN.get('headers', {}).get('X-Only-Header') == 'yes',
    json.dumps(SEEN.get('headers', {}), ensure_ascii=False)[:160])

print('\n== ④ 有 body 但未给 method -> 应自动 POST ==')
t3, final3, _ = run_request({"url": "http://127.0.0.1:%d/autopost" % PORT, "body": "x=1"}, 10)
print('   服务器看到: method=%s' % SEEN.get('method'))
rec('有 body 时自动用 POST', SEEN.get('method') == 'POST', 'method=%s' % SEEN.get('method'))

srv.shutdown()
ok = sum(1 for _, v in R if v)
print('\n==== 结果: %d/%d 通过 ====' % (ok, len(R)))
for label, v in R:
    print('   [%s] %s' % ('PASS' if v else 'FAIL', label))
