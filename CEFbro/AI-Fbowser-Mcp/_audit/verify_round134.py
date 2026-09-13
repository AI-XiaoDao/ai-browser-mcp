# -*- coding: utf-8 -*-
r"""验证第134轮: ①运行目录**外**的 file 现在给出**可行动**错误(不再假装"没传参数");
             ②`code_base64` 已在 schema 里可见且可用; ③运行目录内的 file 仍正常(回归)。

用法: py -3 _audit\verify_round134.py
"""
import base64
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


T = {t["name"]: t for t in json.loads(urllib.request.urlopen(BASE + "/tools/list", timeout=20).read().decode())["tools"]}


def props(n):
    return set(((T.get(n, {}).get("inputSchema") or {}).get("properties") or {}).keys())


print('== ① 运行目录外的 file: 错误必须可行动 ==')
e1, t1 = call("browser_execute_js", {"file": "C:\\Windows\\notepad.exe"})
rec("目录外 file 仍被拒绝(安全守卫保留)", e1, t1[:80])
rec("报错点明'仅允许进程运行目录内的文件'", "进程运行目录内" in t1, t1[:110])
rec("报错列出三种传法(code/code_base64/file)", ("code_base64" in t1) and ("file" in t1), t1[:110])
rec("报错给出改法(放运行目录或改用 code/code_base64)", "运行目录下" in t1, t1[-90:])

print('\n== ② code_base64 已声明且可用 ==')
rec("execute_js 声明了 code_base64", "code_base64" in props("browser_execute_js"), sorted(props("browser_execute_js")))
rec("evaluate 声明了 code_base64", "code_base64" in props("browser_evaluate"), sorted(props("browser_evaluate")))
b64 = base64.b64encode("'B64_VERIFY:'+(4*4)".encode()).decode()
e2, t2 = call("browser_execute_js", {"code_base64": b64})
rec("code_base64 真能执行", (not e2) and ("B64_VERIFY:16" in t2), t2[:90])

print('\n== ③ 运行目录内的 file 仍正常(回归) ==')
probe = os.path.join(RUNDIR, "mcp_r134_probe.js")
with io.open(probe, "w", encoding="utf-8") as f:
    f.write("'RUNDIR_OK:'+(5+5)")
e3, t3 = call("browser_execute_js", {"file": probe})
rec("运行目录内 file 正常执行", (not e3) and ("RUNDIR_OK:10" in t3), t3[:90])
try:
    os.remove(probe)
except OSError:
    pass

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
