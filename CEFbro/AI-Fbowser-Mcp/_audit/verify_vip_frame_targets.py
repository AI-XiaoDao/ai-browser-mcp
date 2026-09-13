# -*- coding: utf-8 -*-
"""验收 browser_vip_execute_js_context 的三档 target（main/all_frames/frame_index）。

分两段:
  【安全段】前置守卫与回归: 未启用执行环境时三档 target 必须**明确失败并给指引**,
            而不是发一个永远不完成的异步任务让调用方白等; 未知/缺省 target 仍走原路径。
  【破坏段】启用执行环境后真机跑一次 main 与 all_frames(页面内注入 iframe, 期望 frame_count>=2)。
            注意: 启用会破坏本会话 CDP 通道(项目已实测), 故放在最后, 结束时重启进程恢复。
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
R = []


def call(n, a, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def arm(label, ok, detail):
    R.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:280])


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).raise_for_status()
        time.sleep(4.5)
        break
    except Exception:
        pass
call("browser_navigate", {"url": "https://example.com/?vipframe=1", "wait_for_load": True}, 90)

print("== 【安全段】未启用执行环境时的前置守卫 ==")
for tgt in ("main", "all_frames"):
    e, t = call("browser_vip_execute_js_context", {"code": "1+1", "target": tgt})
    print("   target=%-11s -> isError=%s %s" % (tgt, e, t[:220]))
    arm("target=%s 未启用环境时明确失败并给指引" % tgt,
        e and ('browser_vip_enable_js_env' in t), t[:220])

e, t = call("browser_vip_execute_js_context", {"code": "1+1", "target": "frame_index"})
print("   target=frame_index(未给序号) -> isError=%s %s" % (e, t[:220]))
arm("target=frame_index 未启用环境时也明确失败", e and ('browser_vip_enable_js_env' in t), t[:200])

print("\n== 回归: 缺省 target(原行为)仍可提交 ==")
e, t = call("browser_vip_execute_js_context", {"code": "1+1"})
print("   -> isError=%s %s" % (e, t[:240]))
arm("缺省 target 仍走原路径(提交成功或明确失败, 不因新参数报错)",
    (not e) or ('target' not in t), t[:220])

print("\n== 【破坏段】启用执行环境后真机验证 ==")
e, t = call("browser_vip_enable_js_env", {"enable": True, "confirm": True})
print("   enable_js_env -> isError=%s %s" % (e, t[:260]))
arm("启用执行环境成功(带破坏性告警)", (not e) and ('已启用' in t), t[:240])

print("\n-- main --")
e, t = call("browser_vip_execute_js_context", {"code": "document.title", "target": "main"})
print("   提交: isError=%s %s" % (e, t[:240]))
m = re.search(r'"task_id"\s*:\s*"([^"]+)"', t)
if m:
    tid = m.group(1)
    got = None
    for _ in range(8):
        time.sleep(1.0)
        e2, t2 = call("mcp_result", {"request_id": tid}, 40)
        if '_waiting' not in t2:
            got = t2
            break
    print("   结果: %s" % (got or '(仍未完成)')[:300])
    arm("target=main 拿到回调结果", bool(got) and ('Example Domain' in got), (got or '')[:240])
else:
    arm("target=main 拿到回调结果", False, "没拿到 task_id: %s" % t[:200])

print("\n-- all_frames(页面内先注入 iframe) --")
call("browser_execute_js", {"code":
    "(function(){var f=document.createElement('iframe');f.id='mcpFrame';"
    "f.srcdoc='<html><body>inner-frame</body></html>';document.body.appendChild(f);return 'ok'})()"}, 40)
time.sleep(1.2)
e, t = call("browser_get_frames", {})
print("   当前帧数参考: %s" % t[:160])
e, t = call("browser_vip_execute_js_context", {"code": "location.href", "target": "all_frames"})
print("   提交: isError=%s %s" % (e, t[:240]))
m = re.search(r'"task_id"\s*:\s*"([^"]+)"', t)
if m:
    tid = m.group(1)
    got = None
    for _ in range(10):
        time.sleep(1.0)
        e2, t2 = call("mcp_result", {"request_id": tid}, 40)
        if '_waiting' not in t2:
            got = t2
    print("   结果: %s" % (got or '(未完成)')[:400])
    # 注意: 回包内层 JSON 是**转义过的**(形如 \"frame_count\":4), 必须先反转义再匹配
    # (第一版就是漏了这步, 把"明明成功"的 4 帧结果判成 FAIL)
    flat = (got or '').replace('\\"', '"')
    cnt = re.search(r'"frame_count":(\d+)', flat)
    arm("★all_frames 累计了**多帧**结果(frame_count>=2)",
        bool(cnt) and int(cnt.group(1)) >= 2,
        "frame_count=%s | %s" % (cnt.group(1) if cnt else '?', (got or '')[:240]))
else:
    arm("★all_frames 累计了多帧结果", False, "没拿到 task_id: %s" % t[:200])

ok = sum(1 for _, v in R if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(R)))
for label, v in R:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))

print("\n== 收尾: 重启进程恢复 CDP 通道 ==")
subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).raise_for_status()
        time.sleep(4.0)
        break
    except Exception:
        pass
print("   CDP 恢复检查: %s" % call("browser_evaluate", {"code": "'alive:'+document.title"}, 30)[1][:120])
