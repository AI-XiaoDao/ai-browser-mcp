# -*- coding: utf-8 -*-
r"""验证第125轮新增能力: browser_navigate 的**提交式跳转**(补类库 载入请求 缺口)。

预言机 = **本机自建 HTTP 服务收到的东西**(方法/请求头/请求体), 完全独立于被测工具的自述;
再加一条页面侧证据(服务端把收到的内容回显进 HTML, 用 browser_get_text 读)。

用例:
  ① GET 回归: 既有路径照旧(不能因为新增能力把老路径弄坏);
  ② POST + 自定义头 + 请求体 → 服务端确实收到 POST/头/体, 页面确实渲染出回显;
  ③ 只给 body → 自动按 POST(零前置);
  ④ **同址连续两次 POST** → 服务端必须收到**两次**(证明自定义请求路径不做"已在目标页面"快速返回);
  ⑤ 页面侧回显与请求体逐字一致(内容断言, 不只判成败)。

用法: py -3 _audit\verify_navigate_request.py
"""
import http.server
import json
import os
import socket
import sys
import threading
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
RES = []
SEEN = []          # 服务端记录: {"method","path","headers","body"}


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _record(self, body):
        SEEN.append({"method": self.command, "path": self.path,
                     "headers": {k.lower(): v for k, v in self.headers.items()},
                     "body": body})

    def _respond(self, html):
        b = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._record("")
        self._respond("<html><head><title>nav-req</title></head><body><h1>NAVPROBE</h1>"
                      "<div id='echo'>GET %s</div></body></html>" % self.path)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode("utf-8", "replace") if n else ""
        self._record(body)
        self._respond("<html><head><title>nav-req-post</title></head><body><h1>NAVPROBE</h1>"
                      "<div id='echo'>POST %s BODY=%s SIGN=%s</div></body></html>"
                      % (self.path, body, self.headers.get("X-Sign", "")))


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    dt = time.time() - t0
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text"), dt


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-46s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:112]))


def msg(txt):
    try:
        o = json.loads(txt)
        d = o.get("data")
        if isinstance(d, dict) and isinstance(d.get("message"), str):
            return d["message"]
        return str(o.get("message") or "")
    except Exception:
        return txt


def main():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d' % port
    print('== 预言机 HTTP 服务: %s ==' % base)

    print('\n== ① GET 回归(既有路径不受影响) ==')
    e1, t1, dt1 = call("browser_navigate", {"url": base + "/g1"})
    seen_get = [x for x in SEEN if x["path"] == "/g1"]
    rec("GET 导航成功", (not e1) and bool(seen_get), "%.2fs %s" % (dt1, msg(t1)[:50]))
    rec("服务端确实收到 GET /g1", bool(seen_get) and seen_get[0]["method"] == "GET",
        str([x["method"] + " " + x["path"] for x in seen_get]))

    print('\n== ② POST + 自定义头 + 请求体 ==')
    body2 = "hello=world&x=1"
    e2, t2, dt2 = call("browser_navigate",
                       {"url": base + "/p2", "method": "POST", "body": body2,
                        "headers": "X-Sign: abc123\nContent-Type: application/x-www-form-urlencoded"})
    seen2 = [x for x in SEEN if x["path"] == "/p2"]
    rec("提交式跳转成功", (not e2) and bool(seen2), "%.2fs %s" % (dt2, msg(t2)[:60]))
    rec("服务端收到的是 POST", bool(seen2) and seen2[0]["method"] == "POST",
        seen2[0]["method"] if seen2 else "未收到")
    rec("请求体逐字一致", bool(seen2) and seen2[0]["body"] == body2,
        "got=%r want=%r" % (seen2[0]["body"] if seen2 else None, body2))
    rec("自定义头 X-Sign 已送达", bool(seen2) and seen2[0]["headers"].get("x-sign") == "abc123",
        "x-sign=%r" % (seen2[0]["headers"].get("x-sign") if seen2 else None))
    rec("Content-Type 已送达", bool(seen2) and "form-urlencoded" in (seen2[0]["headers"].get("content-type") or ""),
        "content-type=%r" % (seen2[0]["headers"].get("content-type") if seen2 else None))
    _e, tt, _d = call("browser_get_text", {"selector": "#echo"})
    rec("页面侧回显与请求体一致(第二个预言机)", body2 in tt and "POST" in tt, tt[:90])

    print('\n== ③ 只给 body → 自动 POST(零前置) ==')
    e3, t3, dt3 = call("browser_navigate", {"url": base + "/p3", "body": "auto=1"})
    seen3 = [x for x in SEEN if x["path"] == "/p3"]
    rec("只给 body 时按 POST 发出", (not e3) and bool(seen3) and seen3[0]["method"] == "POST"
        and seen3[0]["body"] == "auto=1",
        "%s body=%r" % (seen3[0]["method"] if seen3 else "-", seen3[0]["body"] if seen3 else None))

    print('\n== ④ 同址连续两次 POST: 必须真的发两次(不吞掉第二次) ==')
    before = len([x for x in SEEN if x["path"] == "/p4"])
    e4a, t4a, _ = call("browser_navigate", {"url": base + "/p4", "method": "POST", "body": "n=1"})
    e4b, t4b, _ = call("browser_navigate", {"url": base + "/p4", "method": "POST", "body": "n=2"})
    got4 = [x for x in SEEN if x["path"] == "/p4"]
    rec("两次调用都成功", (not e4a) and (not e4b), "%s | %s" % (msg(t4a)[:34], msg(t4b)[:34]))
    rec("服务端收到两次(第二次未被同址快速路径吞掉)",
        len(got4) - before == 2 and [x["body"] for x in got4[-2:]] == ["n=1", "n=2"],
        "次数=%d bodies=%s" % (len(got4) - before, [x["body"] for x in got4[-2:]]))

    print('\n== ⑤ 收尾: 再回 GET 路径确认无回归 ==')
    e5, t5, _ = call("browser_navigate", {"url": base + "/g5"})
    rec("GET 仍可用", (not e5) and any(x["path"] == "/g5" for x in SEEN), msg(t5)[:50])

    srv.shutdown()
    bad = [x for x, o in RES if not o]
    print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
    for x in bad:
        print('   未通过: %s' % x)
    sys.exit(1 if bad else 0)


main()
