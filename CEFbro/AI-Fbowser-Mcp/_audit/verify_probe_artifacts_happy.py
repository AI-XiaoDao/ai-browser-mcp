# -*- coding: utf-8 -*-
"""证明 4 个"探针填充值不合法"工具的**正常路径确实可用**。

台账里这 4 个记的是 fail, 但那是探针只会填 generic 值造成的伪失败:
  browser_set_window_style  {type: 1}          -> 合法值是 -16/-20/-12
  browser_find_by_hwnd      {hwnd: 1}          -> 需要**真实**窗口句柄(动态取得)
  browser_network_body      {request_id:...}   -> 需要**真实** CDP requestId(动态取得)
  mcp_result                {request_id:...}   -> 需要**真实**异步任务号(动态取得)

本脚本按"先取真值再调用"的顺序证明它们能成功 —— 这才是"一次调用就成功"的真实形态。
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

RESULTS = []


def c(n, a, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text").replace('\\"', '"')


def arm(label, ok, detail):
    RESULTS.append((label, ok))
    print("   [%s] %s" % ("PASS" if ok else "FAIL", label))
    print("         %s" % detail[:300])


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
c("browser_navigate", {"url": "https://example.com/?happy=1", "wait_for_load": True})

# ---------------------------------------------------------------- 1) 窗口样式
print("== 1) browser_set_window_style: 先读当前样式, 再**原值写回**(安全空操作) ==")
e0, t0 = c("browser_get_window_style", {"type": -16})
print("   取当前样式: isError=%s | %s" % (e0, t0[:200]))
mst = re.search(r'"style"\s*:\s*"(\d+)"', t0)
cur_style = mst.group(1) if mst else ""
print("   当前 style = %r" % cur_style)
if cur_style:
    # 参数名是 style(不是 value) —— 第一版探针传 value 导致被"style 不能省略"守卫拦下,
    # 那次 PASS 是假通过(只因报错文案里没有'非法窗口属性类型'字样)。
    e, t = c("browser_set_window_style", {"type": -16, "style": int(cur_style)})
    print("   原值写回: isError=%s | %s" % (e, t[:240]))
    arm("set_window_style 用合法 type+style 成功(原值写回)",
        (not e) and ("非法窗口属性类型" not in t) and ("不能省略" not in t),
        "type=-16 style=%s | isError=%s | %s" % (cur_style, e, t))
else:
    arm("set_window_style 用合法 type+style 成功(原值写回)", False,
        "没读到当前 style, 原文: %s" % t0[:200])

# ---------------------------------------------------------------- 2) 按句柄查找
print("\n== 2) browser_find_by_hwnd 先取真实窗口句柄 ==")
e, t = c("browser_get_window_handle", {})
print("   get_window_handle: isError=%s | %s" % (e, t[:200]))
m = re.search(r'(?:句柄|handle)\D{0,12}(\d{3,})', t)
hwnd = m.group(1) if m else ""
if not hwnd:
    nums = re.findall(r'\d{4,}', t)
    hwnd = nums[0] if nums else ""
print("   解析到 hwnd = %r" % hwnd)
if hwnd:
    e2, t2 = c("browser_find_by_hwnd", {"hwnd": int(hwnd)})
    print("   find_by_hwnd: isError=%s | %s" % (e2, t2[:240]))
    arm("find_by_hwnd 用真实句柄能找到浏览器",
        (not e2) and ("未找到" not in t2), "hwnd=%s | isError=%s | %s" % (hwnd, e2, t2))
else:
    arm("find_by_hwnd 用真实句柄能找到浏览器", False,
        "没能从 get_window_handle 回包里解析出句柄, 原文: %s" % t[:200])

# ---------------------------------------------------------------- 3) 响应体
print("\n== 3) browser_network_body 先取真实 CDP requestId ==")
e, t = c("browser_kernel_cdp_monitor", {"action": "add", "methods": "Network.*"})
print("   cdp_monitor add: isError=%s | %s" % (e, t[:180]))
c("browser_navigate", {"url": "https://example.com/?reqid=%d" % int(time.time()),
                       "wait_for_load": True})
time.sleep(0.6)
e, t = c("browser_cdp_event", {"event_name": "Network.requestWillBeSent"})
print("   cdp_event: isError=%s | %s" % (e, t[:300]))
ids = re.findall(r'"requestId"\s*:\s*"([^"]+)"', t)
print("   解析到 requestId 候选: %s" % ids[:4])
req_id = ids[0] if ids else ""
if req_id:
    e3, t3 = c("browser_network_body", {"request_id": req_id})
    print("   network_body: isError=%s | %s" % (e3, t3[:300]))
    arm("network_body 用真实 request_id 能取到响应体",
        (not e3) and ("非法" not in t3), "id=%s | isError=%s | %s" % (req_id, e3, t3))
else:
    # 退回: 直接从 CDP 事件缓存或 Network 域订阅里再试一次
    e, t = c("browser_cdp_event", {"event_name": "Network.responseReceived"})
    ids = re.findall(r'"requestId"\s*:\s*"([^"]+)"', t)
    req_id = ids[0] if ids else ""
    if req_id:
        e3, t3 = c("browser_network_body", {"request_id": req_id})
        arm("network_body 用真实 request_id 能取到响应体",
            (not e3) and ("非法" not in t3), "id=%s | isError=%s | %s" % (req_id, e3, t3))
    else:
        arm("network_body 用真实 request_id 能取到响应体", False,
            "没能从 CDP 事件里解析出 requestId, 原文: %s" % t[:300])

# ---------------------------------------------------------------- 4) 异步结果
print("\n== 4) mcp_result 先制造一个真实异步任务 ==")
e, t = c("browser_reverse_preload", {"code": "void 0"})
print("   制造异步任务: isError=%s | %s" % (e, t[:240]))
m = re.search(r'"task_id"\s*:\s*"([^"]+)"', t)
task = m.group(1) if m else ""
print("   解析到 task_id = %r" % task)
if task:
    e4, t4 = c("mcp_result", {"request_id": task})
    print("   mcp_result: isError=%s | %s" % (e4, t4[:300]))
    arm("mcp_result 用真实任务号能取到结果",
        (not e4) and ("未找到任务结果" not in t4), "task=%s | isError=%s | %s" % (task, e4, t4))
else:
    arm("mcp_result 用真实任务号能取到结果", False,
        "没拿到 task_id, 原文: %s" % t[:240])

ok = sum(1 for _, v in RESULTS if v)
print("\n==== 结果: %d/%d 通过 ====" % (ok, len(RESULTS)))
for label, v in RESULTS:
    print("   [%s] %s" % ("PASS" if v else "FAIL", label))
