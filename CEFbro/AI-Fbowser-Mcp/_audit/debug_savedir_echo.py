# -*- coding: utf-8 -*-
r"""诊断: start_download 回执里 save_dir 的精确形态 vs 传入值。
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
DL = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp_dl_dbg"))


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


print('DL_DIR = %r' % DL)
e, t, d = call("browser_start_download", {"url": "https://example.com/", "save_dir": DL}, to=60)
print('resp t = %r' % t)
print('DL in t ?', DL in t)
