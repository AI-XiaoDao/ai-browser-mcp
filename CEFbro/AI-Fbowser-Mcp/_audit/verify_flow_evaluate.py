# -*- coding: utf-8 -*-
"""验收 flow/evaluate 的 F2/F3/E1/E2/E3a 五项改动。

判据:
 ① **E1+E2 核心**: browser_debugger_evaluate 只给 expression(不给 call_frame_id) -> 必须**成功**
    (修复前必然失败: "call_frame_id和expression 参数不能为空")。这条直接对应"零前置/一次成功"。
 ② **E3a**: 传一个**非法 call_frame_id** 走 parse:true -> 失败原因必须**非空**且指出帧的问题
    (修复前: 解析器读的键根本不存在 -> 一律 {"ok":false,"error":""}，调用方看不到任何原因)
 ③ **F2**: browser_debugger_flow 的默认等待必须**有界**(远小于原来的 45000ms, 用统一预算 12000 判定)
 ④ **F3**: flow 的超时失败体必须**保留** step/error, 并**追加** waited_ms/reason/hint
 ⑤ 收尾: 必须把调试器恢复(①会真的制造暂停点; 不恢复会冻结渲染器, 污染后续一切测量)
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, '_int', 'AI-Fbowser-Mcp', 'debug', 'x64', 'linker',
                   'AI-Fbowser-Mcp.exe')
res = []


def call(name, args, timeout=90):
    t0 = time.time()
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": args}}
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


def unesc(t):
    return t.replace('\\"', '"')


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-50s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:84]))


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).read()
        time.sleep(4.5)
        break
    except Exception:
        pass
call("browser_navigate", {"url": "https://example.com/?dbgfix=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== ① E1+E2: 只给 expression, 不给 call_frame_id ==")
e, t, dt = call("browser_debugger_evaluate", {"expression": "document.title"}, 90)
print("   isError=%s 用时=%.2fs" % (e, dt))
print("   %s" % t[:400])
u = unesc(t)
rec("不给帧 ID 也能成功(修复前必失败)", not e, t[:84])
rec("拿到真实值(Example Domain)", "Example" in u, t[:84])
rec("如实上报自动动作(auto_prepared)", "auto_prepared" in u, t[:84])

print("\n== ② E3a: 非法 call_frame_id 走 parse:true -> 原因必须非空 ==")
e, t, dt = call("browser_debugger_evaluate",
                {"call_frame_id": "mcp-bogus-frame-xyz", "expression": "1", "parse": True}, 60)
print("   isError=%s" % e)
print("   %s" % t[:500])
u = unesc(t)
empty_err = '"error":""' in u.replace(" ", "")
rec("失败原因不再被吞成空串", not empty_err, t[:84])
rec("原因里点明帧的问题", ("call_frame" in u) or ("frame" in u.lower()), t[:84])

print("\n== ③④ F2+F3: flow 用不存在的断点, 默认等待必须**有界**且失败体带原因 ==")
t0 = time.time()
e, t, dt = call("browser_debugger_flow", {"breakpoint": "mcp_no_such_script_zzz"}, 90)
el = time.time() - t0
print("   isError=%s 用时=%.2fs" % (e, el))
print("   %s" % t[:600])
u = unesc(t)
rec("有界: 用时显著小于旧默认 45s", el < 30.0, "%.2fs" % el)
rec("保留 step=wait_paused", '"step":"wait_paused"' in u.replace(" ", ""), t[:84])
rec("追加 waited_ms 且约等于 12000", '"waited_ms":12000' in u.replace(" ", "")
    or ('"waited_ms":' in u.replace(" ", "") and "12000" in u), t[:84])
rec("追加 reason(说明为何没等到)", '"reason":' in u.replace(" ", ""), t[:84])
rec("追加 hint(可行动指引)", '"hint":' in u.replace(" ", ""), t[:84])

print("\n== ⑤ 收尾: 恢复调试器(①真的制造过暂停点) ==")
e, t, dt = call("browser_debugger_resume", {}, 45)
print("   resume: isError=%s %s" % (e, t[:200]))
e2, t2, _ = call("browser_execute_js", {"code": "1+1"}, 30)
rec("页面可继续执行 JS(未冻结)", not e2, t2[:84])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
