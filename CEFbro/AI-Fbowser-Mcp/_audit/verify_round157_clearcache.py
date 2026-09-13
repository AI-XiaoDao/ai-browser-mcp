# -*- coding: utf-8 -*-
r"""第157轮: browser_clear_cache 参数粒度增强验收(行为对照 + 守卫)。

判据:
  ① 基线: 页面侧写 localStorage 标记, 读回存在
  ② set 局部标记(不同键) → 全局清理 {targets:localstorage, origin:https://example.com} → 轮询 mcp_result 成功
  ③ 页面侧回读: 标记已清除(行为级生效证明)
  ④ 守卫: targets 坏名字 → 整体报错且指名; storage_types 坏名字 → 同
  ⑤ 缺省(无参)路径仍可用(异步提交成功)
  ⑥ 全程 CDP 健康(清理不毒化)
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401
import loop

BASE = "http://127.0.0.1:9222"
RES = []
TS = int(time.time())


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


def wait_result(tid, want, timeout=30):
    for _ in range(int(timeout / 1.0)):
        e, t, _ = call("mcp_result", {"request_id": tid}, to=30)
        if not e and want in t:
            return True, t
        if e and ("VIP操作失败" in t):
            return False, t
        time.sleep(1.0)
    return False, ""


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r157cache=%d" % TS})
health('①execute_js 快')
e, t, d = js("try{localStorage.setItem('mcp_cache_probe_%d','1');'set'}catch(e){'ERR:'+e.message}" % TS)
rec('①写 localStorage 标记', "set" in t, t[:60])
e, t, d = js("String(localStorage.getItem('mcp_cache_probe_%d'))" % TS)
rec('①读回 == 1', "1" in t, t[:50])

print('\n== ②③ 带粒度全局清理 → 行为级生效 ==')
e, t, d = call("browser_clear_cache",
               {"targets": "localstorage", "origin": "https://example.com"}, to=60)
rec('②提交成功且回执含掩码说明', (not e) and ("清理对象掩码" in t), "%.2fs %s" % (d, t[:90]))
tid = ""
m = re.search(r"task_[0-9_]+", t)
if m:
    tid = m.group(0)
ok, rt = wait_result(tid, "缓存清理完成", 30) if tid else (False, "")
rec('②轮询 mcp_result 清理成功', ok, rt[:80])
e, t, d = js("String(localStorage.getItem('mcp_cache_probe_%d'))" % TS)
rec('③页面侧回读: 标记已清除(null)', "null" in t, t[:60])
health('③之后 execute_js 仍快(清理不毒化)')

print('\n== ④ 守卫 ==')
e, t, d = call("browser_clear_cache", {"targets": "localstorage,badname"}, to=60)
rec('④targets 坏名字 → 整体报错并指名', e and ("badname" in t), t[:90])
e, t, d = call("browser_clear_cache", {"storage_types": "badtype"}, to=60)
rec('④storage_types 坏名字 → 整体报错并指名', e and ("badtype" in t), t[:90])
health('④之后 execute_js 仍快')

print('\n== ⑤ 缺省路径仍可用 ==')
e, t, d = call("browser_clear_cache", {}, to=60)
rec('⑤无参提交成功(与旧行为一致)', not e, "%.2fs %s" % (d, t[:80]))

print('\n== ⑥ 收尾 ==')
health('⑥收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑥browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
