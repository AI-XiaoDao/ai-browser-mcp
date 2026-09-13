# -*- coding: utf-8 -*-
r"""验证: ①`browser_create_url_request {body_file}` 能用**文件**上传大请求体(绕开 MCP HTTP 通道 ~1MB 的 arguments 上限);
     ②类库缺口 `类_FBrowser_URL请求事件.上传进度` → 事件 `urlreq_upload` 真的入库(上一轮只做到"实现+编译通过")。

为什么这样测才对:
  · 3MB body 若走 arguments, 会在到达服务端之前被内核断连(实测 1024KB 即失败, 客户端只见 RemoteDisconnected),
    所以"能不能传大 body"**只能**用 body_file 验证 —— 这同时证明新能力与上传进度事件;
  · 两个独立预言机: 本机 HTTP 服务**实际收到的字节数** + 事件里的 total/current;
  · 零前置: 不手工开任何监控开关(实现应自动置 UR_FLAG_REPORT_UPLOAD_PROGRESS 并自动打开 urlreq 监控)。

用法: py -3 _audit\verify_urlreq_upload.py
"""
import http.server
import json
import os
import socket
import sys
import tempfile
import threading
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
RES = []
BODY_BYTES = 3 * 1024 * 1024
SEEN = {}


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _reply(self, txt):
        b = txt.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        SEEN["get"] = SEEN.get("get", 0) + 1
        self._reply("GET-OK")

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        got = 0
        while got < n:
            chunk = self.rfile.read(min(65536, n - got))
            if not chunk:
                break
            got += len(chunk)
        SEEN["post_bytes"] = got
        SEEN["post_path"] = self.path
        self._reply("POST-OK:%d" % got)


def call(n, a=None, to=120):
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


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:112]))


def obj(t):
    """解析回包 JSON。**必须容错**: 异步工具的回包在 JSON 之后还跟了一段人类可读提示
    (形如 `  [task_id: task_66378859_14363_16]`), 直接 json.loads 会失败 —— 第一版探针因此
    把 task_id 解析成 None(3 条假失败)。这里按"取第一个完整 JSON 对象"的方式解析。"""
    try:
        return json.loads(t)
    except Exception:
        pass
    i = t.find("{")
    if i < 0:
        return None
    depth, instr, esc = 0, False, False
    for j in range(i, len(t)):
        c = t[j]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
            continue
        if c == '"':
            instr = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(t[i:j + 1])
                except Exception:
                    return None
    return None


def field(t, key):
    """从原始回包文本里取字段(不依赖整体 JSON 可解析)。"""
    import re
    m = re.search(r'"%s"\s*:\s*"([^"]*)"' % key, t)
    return m.group(1) if m else ""


def upload_records():
    _e, t = call("browser_event", {"event_type": "urlreq_upload", "limit": 80})
    o = obj(t)
    arr = None
    if isinstance(o, list):
        arr = o
    elif isinstance(o, dict):
        for k in ("events", "events_json", "data", "timeline_json", "items"):
            v = o.get(k)
            if isinstance(v, list):
                arr = v
                break
            if isinstance(v, str) and v.strip().startswith("["):
                arr = obj(v)
                break
    if arr is None:
        print('     !! urlreq_upload 回包无事件数组: %s' % t[:200])
        return [], None
    out = []
    for it in arr:
        d = it.get("data") if isinstance(it, dict) else None
        if isinstance(d, str):
            d = obj(d)
        if isinstance(d, dict):
            try:
                out.append((int(d.get("current")), int(d.get("total"))))
            except Exception:
                pass
    return out, arr


def main():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d' % port
    print('== 预言机 HTTP 服务: %s ==' % base)

    fp = os.path.join(tempfile.gettempdir(), "mcp_upload_probe.bin")
    with open(fp, "wb") as f:
        f.write(b"U" * BODY_BYTES)
    print('   测试文件: %s (%d 字节)' % (fp, os.path.getsize(fp)))

    e0, t0 = call("browser_status", {})
    rec("前置: 实例健康", not e0, t0[:50])

    print('\n== ① 用 body_file 上传 3MB(不手工开任何监控开关 = 验证零前置) ==')
    e1, t1 = call("browser_create_url_request",
                  {"url": base + "/sink", "method": "POST", "body_file": fp,
                   "headers": "Content-Type: application/octet-stream"})
    print('     %s' % t1.replace('\n', ' ')[:230])
    o1 = obj(t1) or {}
    d1 = o1.get("data") if isinstance(o1.get("data"), dict) else {}
    tid = (d1 or {}).get("task_id") or o1.get("task_id") or field(t1, "task_id")
    ap = str((d1 or {}).get("auto_prepared") or o1.get("auto_prepared") or field(t1, "auto_prepared"))
    rec("body_file 形式的 URL 请求已提交", (not e1) and bool(tid), "task_id=%s" % tid)
    rec("零前置: 自动置上传进度标志 + 自动开 urlreq 监控",
        ("UPLOAD_PROGRESS" in ap) and ("监控" in ap), ap[:100] or "(未上报)")

    print('\n== ② 服务端收到的字节数(预言机一) ==')
    dl = time.time() + 40
    done = False
    last = ""
    while time.time() < dl:
        e2, t2 = call("mcp_result", {"request_id": tid, "consume": False})
        last = t2
        if (not e2) and ('"success":true' in t2 or "POST-OK" in t2):
            done = True
            break
        time.sleep(1.0)
    rec("请求在 40 秒内落定", done, last.replace('\n', ' ')[:100])
    rec("服务端**确实收到完整 %d 字节**(文件直传生效)" % BODY_BYTES,
        SEEN.get("post_bytes") == BODY_BYTES, "收到=%s" % SEEN.get("post_bytes"))

    print('\n== ③ 上传进度事件(预言机二) ==')
    recs, raw = upload_records()
    print('     urlreq_upload 事件数=%d 样例=%s' % (len(recs), recs[:4]))
    rec("收到 ≥1 条 urlreq_upload 事件(类库缺口已补)", len(recs) >= 1, "count=%d" % len(recs))
    rec("事件 total 与文件字节数一致", bool(recs) and max(x[1] for x in recs) == BODY_BYTES,
        "totals=%s 期望=%d" % ([x[1] for x in recs][:3], BODY_BYTES))
    rec("进度单调不减且不越界",
        bool(recs) and all(recs[i][0] <= recs[i + 1][0] for i in range(len(recs) - 1))
        and all(0 <= x[0] <= x[1] for x in recs), "currents=%s" % [x[0] for x in recs][:6])

    print('\n== ④ 负对照: GET(无请求体)不应产生上传进度事件 ==')
    before = len(recs)
    e4, t4 = call("browser_create_url_request", {"url": base + "/plain"}, to=60)
    time.sleep(3.0)
    recs2, _ = upload_records()
    rec("GET 请求成功提交", not e4, t4.replace('\n', ' ')[:60])
    rec("未新增上传进度事件(标志只对有体的请求置位)", len(recs2) == before,
        "before=%d after=%d" % (before, len(recs2)))

    print('\n== ⑤ body_file 不存在时给可行动错误(不静默当空体) ==')
    e5, t5 = call("browser_create_url_request",
                  {"url": base + "/x", "method": "POST",
                   "body_file": "C:\\no-such-file-mcp-probe.bin"})
    rec("不存在的 body_file 被明确拒绝", e5 and ("body_file 不存在" in t5), t5[:90])
    rec("错误文案指出 1MB 传输限制并建议绝对路径",
        ("绝对路径" in t5) and ("1MB" in t5 or "无响应" in t5), t5[-90:])

    srv.shutdown()
    try:
        os.remove(fp)
    except OSError:
        pass
    bad = [x for x, o in RES if not o]
    print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
    for x in bad:
        print('   未通过: %s' % x)
    sys.exit(1 if bad else 0)


main()
