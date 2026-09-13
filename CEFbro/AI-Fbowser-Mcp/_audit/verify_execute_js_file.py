# -*- coding: utf-8 -*-
r"""验证 `browser_execute_js` 的 `file` 参数（schema 声明"与 code 二选一"）是否**真的实现**。

为什么值得单独验: 这正是本项目最容易出的那一类缺陷 —— **声明了却没用**（此前已抓到多例）。
做法: 写一个临时 .js 文件, 用 file 参数执行, 期望拿到该文件的执行结果; 再用 code 参数跑一次做对照。

用法: py -3 _audit\verify_execute_js_file.py
"""
import json
import os
import sys
import tempfile
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
RES = []


def call(n, a=None, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp", data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-50s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:104]))


fp = os.path.join(tempfile.gettempdir(), "mcp_exec_file_probe.js")
with open(fp, "w", encoding="utf-8") as f:
    f.write("'EXEC_FILE_OK:' + (6 * 7)")

print('== browser_execute_js 的 file 参数 ==')
e1, t1 = call("browser_execute_js", {"file": fp})
rec("file= 从文件读取并执行(声明与实现一致)", (not e1) and ("EXEC_FILE_OK:42" in t1), t1[:110])

e2, t2 = call("browser_execute_js", {"code": "'CODE_OK' + (1+1)"})
rec("code= 直接执行(对照, 回归)", (not e2) and ("CODE_OK2" in t2), t2[:90])

e3, t3 = call("browser_execute_js", {"file": "C:\\no-such-js-file-probe.js"})
rec("file 不存在时给出明确结果(不静默当空代码)", e3, t3[:110])

try:
    os.remove(fp)
except OSError:
    pass
bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
