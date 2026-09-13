# -*- coding: utf-8 -*-
"""复现 fastcheck 里 `highlight clear 还原` 的**间歇性失败**(约 1/3, 失败那次整轮从 5s 变 10s)。

要点: 不止看"过/不过", 而是把每次都打出来 ——
  · show 之后读到的 outline(应含 dashed)
  · clear 之后读到的 outline(应为空串)
  · 两次读各自的**耗时**(失败那次整轮变慢, 说明某一步在等超时)
  · 顺手看 clear 的返回原文(它自己会报 cleared/count, 能区分"没清"与"没东西可清")
重复多轮, 用频率与耗时定位是"写没生效"、"读超时返回旧值", 还是"清的目标列表为空"。
"""
import json
import os
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


def call(name, args, timeout=40):
    t0 = time.time()
    try:
        req = urllib.request.Request(BASE + "/mcp",
                                     data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                                      "method": "tools/call",
                                                      "params": {"name": name,
                                                                 "arguments": args}},
                                                     ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except Exception as ex:
        return True, "EXC:%s" % ex, time.time() - t0
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt, time.time() - t0


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

# 造一个和 fastcheck 同形的页面元素
call("browser_navigate", {"url": "https://example.com/?hl=1", "wait_for_load": True}, 45)
time.sleep(0.5)
e, t, _ = call("browser_execute_js", {
    "code": "var d=document.createElement('input');d.id='hlProbe';document.body.appendChild(d);'ok'"})
print("造探针元素: %s %s" % ("ERR" if e else "OK", t.replace("\n", " ")[:50]))

READ = "document.getElementById('hlProbe').style.outline"
fails = 0
N = 8
for i in range(1, N + 1):
    e1, t1, d1 = call("browser_highlight", {"selector": "#hlProbe", "duration_ms": 0})
    e2, mid, d2 = call("browser_execute_js", {"code": READ})
    e3, t3, d3 = call("browser_highlight", {"action": "clear"})
    e4, aft, d4 = call("browser_execute_js", {"code": READ})
    mid = (mid or "").strip('"')
    aft = (aft or "").strip('"')
    ok = (aft == "")
    if not ok:
        fails += 1
    print("  第%d轮 show=%.2fs 读1=%.2fs clear=%.2fs 读2=%.2fs | mid=%r aft=%r %s"
          % (i, d1, d2, d3, d4, mid[:28], aft[:28], "" if ok else "  <== 失败"))
    print("        clear 原文: %s" % t3.replace("\n", " ")[:110])
    if not ok:
        # 失败时多问一句: 清完之后元素上到底还有什么
        e5, extra, _ = call("browser_execute_js", {
            "code": "(function(){var e=document.getElementById('hlProbe');"
                    "return JSON.stringify({outline:e.style.outline,offset:e.style.outlineOffset,"
                    "hasAttr:('__mcpOrigOutline' in e),listLen:(window.__MCP_HL__||[]).length})})()"})
        print("        失败现场: %s" % (extra or "").replace("\n", " ")[:150])
    time.sleep(0.3)

print("\n== 结果: %d/%d 轮失败 ==" % (fails, N))
subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("  已关闭")
