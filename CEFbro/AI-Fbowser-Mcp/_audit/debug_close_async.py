# -*- coding: utf-8 -*-
r"""诊断: browser_close 后 browser_list 仍含该 id —— 是异步生效还是假成功?
实例当前仍在运行(verify 未杀)。步骤: 读当前列表 → 再关一次 → 立即/1s/2s/3s 轮询列表。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"


def call(n, a=None, to=60):
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


def show(tag):
    e, t, d = call("browser_list", {})
    print('  %s %.2fs err=%s' % (tag, d, e))
    print('    %s' % t[:600])


show('当前列表')
e, t, d = call("browser_close", {"browser_id": 2})
print('close id=2: err=%s %.2fs %s' % (e, d, t[:80]))
for delay in (0.0, 1.0, 2.0, 3.0):
    if delay:
        time.sleep(delay)
    show('close 后 +%.1fs' % delay)
