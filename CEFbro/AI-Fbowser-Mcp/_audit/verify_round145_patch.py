# -*- coding: utf-8 -*-
r"""第145轮 每轮一测: browser_reverse_patch(受控: 注入自有探针脚本, 绝不改页面真实业务脚本)。

判据:
  ① 基线: execute_js 快 + status 可用
  ② 先启用 Debugger 再注入带 sourceURL 的探针脚本(注册表才能收到 scriptParsed)
  ③ search_script list 能按 URL 定位到 scriptId
  ④ 页面侧调用 __mcpPatchFn() == V1
  ⑤ dry_run:true → 成功(dryRun 通过) 且页面仍 V1(未替换)
  ⑥ 实改 → 成功(热替换) 且页面侧回读 == V2(真生效)
  ⑦ 守卫: source 为空 → 拒绝
  ⑧ 全程健康; 收尾 status
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
    print('  [%s] %-56s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def health(tag, limit=1.5):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


def js(code, to=60):
    return call("browser_execute_js", {"code": code}, to=to)


def payload(t):
    try:
        o = json.loads(t)
    except Exception:
        return None
    for _ in range(5):
        if isinstance(o, dict):
            if "scripts_json" in o or "success" in o:
                return o
            nxt = o.get("data") or o.get("result") or o.get("message")
            if isinstance(nxt, str):
                try:
                    nxt = json.loads(nxt)
                except Exception:
                    return None
            o = nxt
        else:
            return None
    return o if isinstance(o, dict) else None


SRC_V1 = "window.__mcpPatchFn=function(){return 'V1'};//# sourceURL=https://example.com/mcp-patch-probe.js"
SRC_V2 = "window.__mcpPatchFn=function(){return 'V2'};//# sourceURL=https://example.com/mcp-patch-probe.js"
INJECT = ("(function(){var s=document.createElement('script');s.textContent=%s;"
          "document.body.appendChild(s);return 'injected'})()" % json.dumps(SRC_V1))

loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r145patch=%d" % int(time.time())})
health('①基线 execute_js 快')
e, t, d = call("browser_status", {})
rec('①browser_status 可用', not e, "%.2fs" % d)

print('\n== ② 启用 Debugger + 注入探针脚本 ==')
e, t, d = call("browser_debugger_enable", {}, to=90)
rec('②browser_debugger_enable 成功', not e, "%.2fs %s" % (d, t[:50]))
e, t, d = js(INJECT)
rec('②注入 sourceURL 探针脚本', (not e) and ("injected" in t), "%.2fs" % d)

print('\n== ③ search_script list 定位 scriptId ==')
e, t, d = call("browser_reverse_search_script", {"action": "list"}, to=90)
sid = ""


def find_sid_by_url(txt):
    try:
        o = json.loads(txt)
    except Exception:
        return ""
    for _ in range(5):
        if isinstance(o, dict):
            sj = o.get("scripts_json")
            if sj:
                try:
                    arr = json.loads(sj)
                except Exception:
                    return ""
                for ent in arr:
                    if "mcp-patch-probe" in (ent.get("url") or ""):
                        return ent.get("scriptId") or ""
                return ""
            nxt = o.get("data") or o.get("result")
            if isinstance(nxt, str):
                try:
                    nxt = json.loads(nxt)
                except Exception:
                    return ""
            o = nxt
        else:
            return ""
    return ""


sid = find_sid_by_url(t) if not e else ""
rec('③list 成功且按 URL 找到 scriptId', bool(sid), "scriptId=%s" % sid)

print('\n== ④ 页面侧 V1 ==')
e, t, d = js("String(window.__mcpPatchFn())")
rec('④页面侧回读 == V1', "V1" in t, t[:50])

print('\n== ⑤ dry_run:true ==')
if sid:
    e, t, d = call("browser_reverse_patch", {"script_id": sid, "source": SRC_V2, "dry_run": True}, to=90)
    rec('⑤dry_run 成功(可编译)', not e, "%.2fs %s" % (d, t[:80]))
    e2, t2, _ = js("String(window.__mcpPatchFn())")
    rec('⑤dry_run 未替换(仍 V1)', "V1" in t2, t2[:50])
    health('⑤之后 execute_js 仍快')

print('\n== ⑥ 实改 + 页面侧回读 V2 ==')
if sid:
    e, t, d = call("browser_reverse_patch", {"script_id": sid, "source": SRC_V2}, to=90)
    rec('⑥实改成功(热替换)', not e, "%.2fs %s" % (d, t[:80]))
    e2, t2, _ = js("String(window.__mcpPatchFn())")
    rec('⑥页面侧回读 == V2(真生效)', "V2" in t2, t2[:60])
    health('⑥之后 execute_js 仍快')

print('\n== ⑦ 守卫 ==')
e, t, d = call("browser_reverse_patch", {"script_id": sid}, to=60)
rec('⑦source 为空被拒', e and ("source" in t), t[:80])
health('⑦之后 execute_js 仍快')

print('\n== ⑧ 收尾 ==')
health('⑧收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑧browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
