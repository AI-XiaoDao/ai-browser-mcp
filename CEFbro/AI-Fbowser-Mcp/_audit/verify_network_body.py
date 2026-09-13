# -*- coding: utf-8 -*-
r"""验证第125轮: browser_network_body 的"零前置一次成功"(台账里它一直是 TARGET 失败)。

验收标准(可区分观测值, 全部用**本机自建 HTTP 服务**当预言机, 不依赖外网):
  ① 请求尚未被捕获时, 不传 request_id 的调用应当:
     自动开启 Network 域 + Network.* 捕获(经 auto_prepared 如实上报), 并给出**可行动**的失败
     (点明"只能是捕获开启之后发生的请求" + 已捕获条数), 而不是原来那句"request_id 缺少参数";
  ② 捕获开启后重新发起请求(url 带时间戳避免缓存命中) → `browser_network_body {url}` 应当**成功**
     且 body 与本地服务发出的已知载荷逐字一致(强预言机);
  ③ 不传任何参数(bare)应当自动取**最新一条**请求并成功, 且回复里 resolve_note 说明解析来源;
  ④ `browser_network {action:"body", url}` 入口别名等价可用;
  ⑤ 不存在的 url → 可行动失败(含"未命中"与条数);
  ⑥ 显式传一个合法格式但不存在的 request_id → 仍应给出可行动错误(保留原有守卫语义)。

用法: py -3 _audit\verify_network_body.py
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
PAYLOAD = '{"hello":"world","n":42,"who":"network_body_verify"}'
PAGE = "<!DOCTYPE html><html><head><title>nb-verify</title></head><body><h1>nb</h1></body></html>"


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/data.json':
            body = PAYLOAD.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
        elif path == '/text':
            body = b'nb-plain-text-body'
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
        else:
            body = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def call(n, a=None, to=90):
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
    print('  [%s] %-46s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:120]))


def payload(txt):
    """把工具回复解成可判定的 dict(优先取 data, 否则取整个对象)。"""
    try:
        o = json.loads(txt)
    except Exception:
        return None
    d = o.get("data")
    if isinstance(d, dict):
        d.setdefault("auto_prepared", o.get("auto_prepared"))
        d.setdefault("message", o.get("message"))
        return d
    return o


def main():
    port = free_port()
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print('== 本机预言机 HTTP 服务: http://127.0.0.1:%d/ ==' % port)
    base = 'http://127.0.0.1:%d' % port

    e, t, dt = call("browser_status", {})
    rec("前置: 实例健康", not e, "%s %.2fs" % (t[:40], dt))

    print('\n== ① 未捕获时(不传 request_id): 应自动开启捕获 + 可行动失败 ==')
    miss = "%s/nope-%d.json" % (base, int(time.time()))
    e1, t1, dt1 = call("browser_network_body", {"url": miss, "wait_ms": 400})
    print('     %s' % t1.replace('\n', ' ')[:220])
    rec("未命中时返回失败(不谎报成功)", e1, "%.2fs" % dt1)
    rec("失败文案点明'捕获开启之后'这一真实限制", "捕获开启之后" in t1, t1[:70])
    rec("失败文案给出已捕获条数(可诊断)", "捕获到的请求条数" in t1, t1[:80])
    rec("失败文案给出可行动替代(重发请求/显式 request_id)",
        "重新加载页面" in t1 and "request_id" in t1, t1[-90:])
    rec("已自动补齐捕获(经 auto_prepared 上报 Network.enable)",
        ("Network" in t1) and ("auto_prepared" in t1 or "已自动补齐" in t1), t1[:100])

    print('\n== ② 捕获开启后重新发起请求 → 按 url 取响应体应与本地载荷逐字一致 ==')
    url2 = "%s/data.json?t=%d" % (base, int(time.time()))
    e_nav, t_nav, dt_nav = call("browser_navigate", {"url": url2, "wait_for_load": True}, 45)
    print('     navigate: err=%s %.2fs %s' % (e_nav, dt_nav, t_nav[:70].replace('\n', ' ')))
    rec("导航到自建 JSON 文档成功", not e_nav, t_nav[:60])
    time.sleep(0.6)
    e2, t2, dt2 = call("browser_network_body", {"url": url2})
    p2 = payload(t2) or {}
    body2 = str(p2.get("body") or "")
    print('     %s' % t2.replace('\n', ' ')[:240])
    rec("按 url 自动解析并成功取回响应体", (not e2) and bool(body2), "%.2fs" % dt2)
    rec("响应体与本地服务载荷逐字一致(强预言机)", body2 == PAYLOAD,
        "len=%d 期望=%d | %r" % (len(body2), len(PAYLOAD), body2[:60]))
    rec("回复给出解析来源 resolve_note", bool(str(p2.get("resolve_note") or "")),
        str(p2.get("resolve_note") or "")[:80])

    print('\n== ③ bare 调用: 自动取最新一条请求(并跳过 favicon 这类自动请求) ==')
    url3 = "%s/text?t=%d" % (base, int(time.time()))
    call("browser_navigate", {"url": url3, "wait_for_load": True}, 45)
    time.sleep(0.8)
    e3, t3, dt3 = call("browser_network_body", {})
    p3 = payload(t3) or {}
    body3 = str(p3.get("body") or "")
    note3 = str(p3.get("resolve_note") or "")
    print('     %s' % t3.replace('\n', ' ')[:200])
    # 预言机: 期望的载荷由**解析到的 URL** 决定 —— 不假设哪一条最新(页面上还有 favicon 等自动请求)
    want = None
    if "/data.json" in note3:
        want = PAYLOAD
    elif "/text" in note3:
        want = 'nb-plain-text-body'
    rec("bare 成功且没有把 favicon 当默认", (not e3) and bool(body3) and ("favicon" not in note3),
        "%.2fs note=%s" % (dt3, note3[:80]))
    rec("bare 取到的响应体与解析出的 URL 载荷一致", want is not None and body3 == want,
        "want=%s body=%r" % (str(want)[:24], body3[:40]))

    print('\n== ④ 入口别名 browser_network {action:body} 等价可用 ==')
    url4 = "%s/data.json?t=%d" % (base, int(time.time()))
    call("browser_navigate", {"url": url4, "wait_for_load": True}, 45)
    time.sleep(0.6)
    e4, t4, dt4 = call("browser_network", {"action": "body", "url": url4})
    p4 = payload(t4) or {}
    rec("action=body 转交成功且内容一致", (not e4) and str(p4.get("body") or "") == PAYLOAD,
        "%.2fs %r" % (dt4, str(p4.get("body") or "")[:40]))

    print('\n== ⑤ 显式非法 request_id: 保留原有守卫语义 ==')
    e5, t5, dt5 = call("browser_network_body", {"request_id": "ZZZZ-not-a-real-request-id"})
    rec("不存在的 request_id 给出可行动错误",
        e5 and ("getResponseBody" in t5) and ("已不在缓存" in t5 or "尽快取" in t5),
        t5[:100])
    e5b, t5b, dt5b = call("browser_network_body", {"request_id": "bad id with spaces"})
    rec("格式非法仍被快速拒绝", e5b and "非法 CDP request_id" in t5b, t5b[:70])

    print('\n== ⑥ 既有 browser_network list 未被破坏 ==')
    e6, t6, dt6 = call("browser_network", {"action": "list", "limit": 20})
    rec("list 仍正常(含 network_logs)", (not e6) and ("network_logs" in t6), t6[:70])

    srv.shutdown()
    bad = [x for x, o in RES if not o]
    print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
    for x in bad:
        print('   未通过: %s' % x)
    sys.exit(1 if bad else 0)


main()
