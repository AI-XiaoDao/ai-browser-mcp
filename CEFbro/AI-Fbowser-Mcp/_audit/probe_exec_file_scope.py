# -*- coding: utf-8 -*-
r"""判定 `browser_execute_js {file:…}` 的真实约束: 是"没实现"还是"被安全路径守卫拒绝"。

上一测用 %TEMP% 下的文件 → 报"缺少参数: 请提供 code 或 file"(误导)。源码看: `解码JS代码` 里
file 分支带 `验证安全路径 (code, 真)` 守卫(仅允许**进程运行目录内**的 JS)。故这里把同一份 JS 写到
**运行目录**(即 exe 所在目录)再试一次, 两者对照即可定性。

用法: py -3 _audit\probe_exec_file_scope.py
"""
import io
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNDIR = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker')
BASE = "http://127.0.0.1:9222"


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


probe = os.path.join(RUNDIR, "mcp_exec_probe.js")
with io.open(probe, "w", encoding="utf-8") as f:
    f.write("'RUN_DIR_FILE_OK:' + (2+3)")
print('探针文件(运行目录内): %s' % probe)

e1, t1 = call("browser_execute_js", {"file": probe})
print('  运行目录内的 file -> err=%s %s' % (e1, t1[:110]))

e2, t2 = call("browser_evaluate", {"file": probe})
print('  browser_evaluate 同文件 -> err=%s %s' % (e2, t2[:110]))

e3, t3 = call("browser_execute_js", {"file": "C:\\Windows\\notepad.exe"})
print('  运行目录外的 file -> err=%s %s' % (e3, t3[:110]))

# Base64 直通(源码里 code_base64 是另一条免转义通道)
import base64
b64 = base64.b64encode("'B64_OK:'+(3*3)".encode()).decode()
e4, t4 = call("browser_execute_js", {"code_base64": b64})
print('  code_base64 -> err=%s %s' % (e4, t4[:110]))

try:
    os.remove(probe)
except OSError:
    pass
