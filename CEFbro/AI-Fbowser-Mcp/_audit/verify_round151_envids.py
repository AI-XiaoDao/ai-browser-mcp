# -*- coding: utf-8 -*-
r"""第151轮: browser_vip_get_js_env_ids 文本化修复验收(需先启用执行环境, 启用毒化 CDP, 结尾重启)。

判据:
  ① 基线健康
  ② 启用执行环境(confirm) → 成功(已知毒化, 警告如实)
  ③ get_js_env_ids → success, 含 ids_text 与 ids_int 两数组 + note
  ④ ids_text 非空 且 不是全 "0"(修复前取整数值全 0)
  ⑤ ids_int 与 ids_text 等长(尽力转换)
  ⑥ 重启后恢复健康
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


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r151ids=%d" % int(time.time())})
e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
rec('①execute_js 快', (not e) and d < 1.5, "%.2fs" % d)

print('\n== ② 启用执行环境(已知毒化, 只是取清单的前置) ==')
e, t, d = call("browser_vip_enable_js_env", {"enable": True, "confirm": True}, to=60)
rec('②enable 成功(含毒化警告)', (not e) and ("破坏" in t), "%.2fs %s" % (d, t[:70]))

print('\n== ③ 取环境 ID 清单(修复后) ==')
e, t, d = call("browser_vip_get_js_env_ids", {}, to=60)
p = {}
try:
    p = json.loads(t)
    if isinstance(p, dict) and "data" in p:
        p = p["data"]
except Exception:
    p = {}
txt_ids = p.get("ids_text") or []
int_ids = p.get("ids_int") or []
rec('③success 且含 ids_text/ids_int/note', (not e) and p.get("success") and isinstance(txt_ids, list) and isinstance(int_ids, list) and p.get("note"),
    "count=%s" % p.get("count"))
print('  [INFO] ids_text=%s ids_int=%s' % (txt_ids, int_ids))
rec('④ids_text 非空且不是全 0(修复前全 0)', len(txt_ids) > 0 and any(str(x) != "0" for x in txt_ids),
    txt_ids)
rec('⑤ids_int 与 ids_text 等长(尽力转换)', len(txt_ids) == len(int_ids), "%d vs %d" % (len(txt_ids), len(int_ids)))
rec('⑤ids_int 从对象JSON提取出真实 id(>0)', len(int_ids) > 0 and any(x > 0 for x in int_ids), int_ids)

print('\n== ⑥ 重启恢复 ==')
loop.kill_app()
if not loop.start_app():
    print('!! 重启失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r151ids2=%d" % int(time.time())})
e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
rec('⑥重启后 execute_js 快(恢复)', (not e) and d < 1.5, "%.2fs" % d)
e, t, d = call("browser_status", {})
rec('⑥browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
