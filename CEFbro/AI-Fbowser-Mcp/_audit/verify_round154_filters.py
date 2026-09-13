# -*- coding: utf-8 -*-
r"""第154轮: VIP 响应过滤器两工具受控验收(页面侧回读 oracle)。

判据:
  ⓪ 基线健康
  A. replace_data: set(替换 HTML)→ 导航到目标 → 页面侧见 PATCHED; clear → 再导航 → 恢复原内容
  B. patch_text: set(改写文本)→ 导航 → 页面侧文本被改写; clear → 再导航 → 恢复
  C. 守卫: 缺 url/body/find、非法 mode/match → 拒绝
  D. 全程 CDP 通道健康(过滤器不毒化)
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
URL_R = "https://example.com/?filtdata=%d" % TS
URL_P = "https://example.com/?filtpatch=%d" % TS
PATCHED_HTML = ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
                "</head><body><h1 id='fpatched'>PATCHED_HTML_%d</h1></body></html>" % TS)


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
call("browser_navigate", {"url": "https://example.com/?r154base=%d" % TS})
health('⓪execute_js 快')

print('\n== A. replace_data 整体替换 ==')
e, t, d = call("browser_vip_filter_replace_data",
               {"url": URL_R, "body": PATCHED_HTML, "mime_type": "text/html", "match": 0}, to=60)
rec('A①set 成功(诚实边界声明)', (not e) and ("诚实边界" in t), "%.2fs %s" % (d, t[:70]))
e, t, d = call("browser_navigate", {"url": URL_R, "wait_for_load": True}, to=90)
rec('A②导航到目标成功', not e, "%.2fs" % d)
e, t, d = js("String(!!document.getElementById('fpatched'))")
rec('A②页面侧回读: 被替换的 HTML 生效', "true" in t, t[:60])
health('A②之后 execute_js 仍快(过滤器不毒化 CDP)')
e, t, d = call("browser_vip_filter_replace_data", {"action": "clear", "url": URL_R}, to=60)
rec('A③clear 成功', not e, "%.2fs %s" % (d, t[:60]))
e, t, d = call("browser_navigate", {"url": "https://example.com/?filtdata2=%d" % TS}, to=90)
e, t, d = js("String(document.getElementById('fpatched')===null)")
rec('A③清除后同域导航: 恢复原内容(无 fpatched)', "true" in t, t[:60])

print('\n== B. patch_text 文本改写 ==')
e, t, d = call("browser_vip_filter_patch_text",
               {"url": URL_P, "find": "Example Domain", "replace": "PATCHED_DOMAIN_%d" % TS, "mode": 1, "match": 0}, to=60)
rec('B①set 成功(诚实边界声明)', (not e) and ("诚实边界" in t), "%.2fs %s" % (d, t[:70]))
e, t, d = call("browser_navigate", {"url": URL_P, "wait_for_load": True}, to=90)
rec('B②导航到目标成功', not e, "%.2fs" % d)
e, t, d = js("String(document.body.textContent.indexOf('PATCHED_DOMAIN_%d')>=0)" % TS)
rec('B②页面侧回读: 文本已改写', "true" in t, t[:60])
health('B②之后 execute_js 仍快')
e, t, d = call("browser_vip_filter_patch_text", {"action": "clear", "url": URL_P}, to=60)
rec('B③clear 成功', not e, "%.2fs %s" % (d, t[:60]))
e, t, d = call("browser_navigate", {"url": "https://example.com/?filtpatch2=%d" % TS}, to=90)
e, t, d = js("String(document.body.textContent.indexOf('PATCHED_DOMAIN_%d')===-1)" % TS)
rec('B③清除后同域导航: 原文恢复(无改写文本)', "true" in t, t[:60])

print('\n== C. 守卫 ==')
e, t, d = call("browser_vip_filter_replace_data", {"body": "x"}, to=60)
rec('C①replace_data 缺 url → 拒绝', e and ("url" in t), t[:70])
e, t, d = call("browser_vip_filter_replace_data", {"url": "https://x.com/"}, to=60)
rec('C②replace_data 缺 body → 拒绝', e and ("body" in t), t[:70])
e, t, d = call("browser_vip_filter_patch_text", {"url": "https://x.com/", "find": "a", "match": 9}, to=60)
rec('C③patch_text 非法 match=9 → 拒绝', e and ("match" in t), t[:70])
e, t, d = call("browser_vip_filter_patch_text", {"url": "https://x.com/", "find": "a", "mode": 9}, to=60)
rec('C④patch_text 非法 mode=9 → 拒绝', e and ("mode" in t), t[:70])

print('\n== D. 收尾 ==')
health('D收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('Dbrowser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
