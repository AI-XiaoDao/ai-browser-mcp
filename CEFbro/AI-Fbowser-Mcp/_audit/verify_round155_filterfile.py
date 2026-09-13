# -*- coding: utf-8 -*-
r"""第155轮: browser_vip_filter_replace_file 受控验收(页面侧回读 oracle)。

判据:
  ⓪ 基线健康; 写本地替换文件(项目目录内)
  A. set(文件替换)→ 导航到目标 → 页面侧见文件内容标记; clear → 再导航 → 恢复
  B. 守卫: 缺 url/file、路径遍历(../)、非法 match → 拒绝
  C. 全程 CDP 通道健康
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"
RES = []
TS = int(time.time())
URL_F = "https://example.com/?filtfile=%d" % TS
TMP_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "_tmp_filtfile_%d.html" % TS))
MARK = "FILEPATCHED_%d" % TS
with open(TMP_FILE, "w", encoding="utf-8") as f:
    f.write("<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
            "<body><h1 id='ffpatched'>%s</h1></body></html>" % MARK)


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


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-58s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def health(tag, limit=1.5):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


def js(code, to=60):
    return call("browser_execute_js", {"code": code}, to=to)


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r155base=%d" % TS})
health('⓪execute_js 快')

print('\n== A. 文件替换 set→导航→clear→恢复 ==')
e, t, d = call("browser_vip_filter_replace_file",
               {"url": URL_F, "file": TMP_FILE, "mime_type": "text/html", "match": 0}, to=60)
rec('A①set 成功(诚实边界声明)', (not e) and ("诚实边界" in t), "%.2fs %s" % (d, t[:70]))
e, t, d = call("browser_navigate", {"url": URL_F, "wait_for_load": True}, to=90)
rec('A②导航到目标成功', not e, "%.2fs" % d)
e, t, d = js("String(!!document.getElementById('ffpatched'))")
rec('A②页面侧回读: 文件内容已替换生效', "true" in t, t[:60])
health('A②之后 execute_js 仍快(不毒化 CDP)')
e, t, d = call("browser_vip_filter_replace_file", {"action": "clear", "url": URL_F}, to=60)
rec('A③clear 成功', not e, "%.2fs %s" % (d, t[:60]))
e, t, d = call("browser_navigate", {"url": "https://example.com/?filtfile2=%d" % TS}, to=90)
e, t, d = js("String(document.getElementById('ffpatched')===null)")
rec('A③清除后同域导航: 恢复原内容', "true" in t, t[:60])

print('\n== B. 守卫 ==')
e, t, d = call("browser_vip_filter_replace_file", {"file": TMP_FILE}, to=60)
rec('B①缺 url → 拒绝', e and ("url" in t), t[:70])
e, t, d = call("browser_vip_filter_replace_file", {"url": "https://x.com/"}, to=60)
rec('B②缺 file → 拒绝', e and ("file" in t), t[:70])
e, t, d = call("browser_vip_filter_replace_file",
               {"url": "https://x.com/", "file": "..\\..\\Windows\\win.ini"}, to=60)
rec('B③路径遍历(../) → 拒绝', e and ("路径" in t), t[:70])
e, t, d = call("browser_vip_filter_replace_file",
               {"url": "https://x.com/", "file": TMP_FILE, "match": 9}, to=60)
rec('B④非法 match=9 → 拒绝', e and ("match" in t), t[:70])

print('\n== C. 收尾 ==')
health('C收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('Cbrowser_status 可用', not e, "%.2fs" % d)
try:
    os.remove(TMP_FILE)
except Exception:
    pass

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
