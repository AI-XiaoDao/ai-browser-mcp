# -*- coding: utf-8 -*-
r"""第165轮: browser_vip_new_tab 验收(按本机运行模式分两支)。

判据:
  ① 基线健康; browser_get_run_style 取 runtime_style
  ② 若 runtime_style != 1(非谷歌): new_tab → **可行动失败**(类库前置, 本机不支持类) 且文案含替代
  ③ 若 runtime_style == 1: new_tab → 成功; 轮询 browser_list 出现新 id; 关闭新标签
  ④ 守卫: 非法协议 url → 拒绝
  ⑤ 收尾健康
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
    print('  [%s] %-58s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:110]))


def payload(t):
    try:
        o = json.loads(t)
    except Exception:
        return {}
    for _ in range(5):
        if isinstance(o, dict):
            if "runtime_style" in o or "browsers" in o:
                return o
            nxt = o.get("data") or o.get("result")
            if isinstance(nxt, str):
                try:
                    nxt = json.loads(nxt)
                except Exception:
                    return {}
            o = nxt
        else:
            return {}
    return o if isinstance(o, dict) else {}


def health(tag, limit=1.5):
    e, t, d = call("browser_execute_js", {"code": "1+1"}, to=60)
    rec(tag, (not e) and d < limit, "%.2fs" % d)


def list_ids():
    e, t, d = call("browser_list", {})
    p = payload(t)
    return [b.get("id") for b in (p.get("browsers") or [])]


loop.kill_app()
if not loop.start_app():
    print('!! 启动失败'); sys.exit(1)
call("browser_navigate", {"url": "https://example.com/?r165tab=%d" % int(time.time())})
health('①execute_js 快')

e, t, d = call("browser_get_run_style", {}, to=60)
p = payload(t)
style = p.get("runtime_style")
rec('①拿到 runtime_style', isinstance(style, int), "style=%s" % style)

print('\n== ②/③ 按模式分两支 ==')
e, t, d = call("browser_vip_new_tab", {"url": "https://example.com/?newtab=%d" % int(time.time()),
                                        "activate": False, "tag": "nt_probe_165"}, to=60)
if style != 1:
    rec('②非谷歌模式 → 可行动失败且含替代(本机不支持类, 允许)', e and ("谷歌" in t) and ("browser_create" in t),
        "%.2fs %s" % (d, t[:100]))
    health('②之后 execute_js 仍快')
else:
    rec('③谷歌模式 → 提交成功', not e, "%.2fs %s" % (d, t[:80]))
    before = list_ids()
    new_id = None
    for _ in range(20):
        now = list_ids()
        diffs = [i for i in now if i not in before]
        if diffs:
            new_id = diffs[0]
            break
        time.sleep(0.5)
    rec('③browser_list 出现新标签 id(异步, 轮询)', new_id is not None, "new_id=%s" % new_id)
    if new_id:
        e, t, d = call("browser_close", {"browser_id": new_id}, to=60)
        rec('③关闭新标签(回读确认)', (not e) and ("回读确认" in t), "%.2fs" % d)
    health('③之后 execute_js 仍快')

print('\n== ④ 守卫 ==')
e, t, d = call("browser_vip_new_tab", {"url": "ftp://example.com/x"}, to=60)
rec('④ftp 协议 → 拒绝(谷歌模式下)', e and ("协议" in t or "谷歌" in t), t[:90])

print('\n== ⑤ 收尾 ==')
health('⑤收尾 execute_js 快')
e, t, d = call("browser_status", {})
rec('⑤browser_status 可用', not e, "%.2fs" % d)

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
