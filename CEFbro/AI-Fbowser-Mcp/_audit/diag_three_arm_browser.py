# -*- coding: utf-8 -*-
"""三臂对照: 到底是什么让主浏览器的同步路径退化 —— 创建第二个浏览器, 还是"使用"它?

每个臂都从**干净冷启动**开始, 用完全相同的探针序列(顺序、参数一致), 唯一差别是中间那一步:

  A 控制臂 : 只探测两次主浏览器(不创建任何东西)              -> 基线
  B 仅创建 : 创建后台浏览器, 但**从不碰它**                  -> 隔离"创建"的副作用
  C 创建+使用: 创建后台浏览器, 并在它上面执行一次 JS          -> 隔离"使用"的副作用

判据: 主浏览器 `get_text`(CDP 优先, 正常 0.0x 秒且返回文本) 与 `execute_js` 的耗时。
若 B 干净而 C 退化, 则触发点是"在第二个浏览器上执行 JS"这条路径; 若 B 也退化, 则是"创建"本身。

注意(避免污染): 每臂结束都冷重启; 不在任何臂里创建**可见**窗口(那会独立扰动实例)。
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


def call(name, args, timeout=60):
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


def restart():
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
            return True
        except Exception:
            pass
    return False


def probe(tag):
    """主浏览器探针: get_text(CDP优先) 与 execute_js 各一次, 打印耗时与内容。"""
    e, t, dt = call("browser_get_text", {"selector": "h1"}, 60)
    print("    %-26s %-4s %6.2fs  %s" % (tag + " get_text", "ERR" if e else "OK", dt,
                                        t.replace("\n", " ")[:60]))
    e2, t2, dt2 = call("browser_execute_js", {"code": "1+1"}, 60)
    print("    %-26s %-4s %6.2fs  %s" % (tag + " execute_js", "ERR" if e2 else "OK", dt2,
                                        t2.replace("\n", " ")[:60]))
    return dt, dt2


results = {}

print("===== A 控制臂: 不创建任何东西, 只探测两次 =====")
restart()
call("browser_navigate", {"url": "https://example.com/?arm=A", "wait_for_load": True}, 45)
time.sleep(0.5)
results["A_before"] = probe("A1")
time.sleep(1.0)
results["A_after"] = probe("A2")

print("\n===== B 仅创建: 创建后台浏览器但绝不使用 =====")
restart()
call("browser_navigate", {"url": "https://example.com/?arm=B", "wait_for_load": True}, 45)
time.sleep(0.5)
results["B_before"] = probe("B1")
e, t, dt = call("browser_create",
                {"url": "https://example.com/?arm=B2", "background": True}, 60)
print("    %-26s %-4s %6.2fs  %s" % ("B create background", "ERR" if e else "OK", dt,
                                    t.replace("\n", " ")[:60]))
time.sleep(1.0)
results["B_after"] = probe("B2")

print("\n===== C 创建+使用: 在后台浏览器上执行一次 JS =====")
restart()
call("browser_navigate", {"url": "https://example.com/?arm=C", "wait_for_load": True}, 45)
time.sleep(0.5)
results["C_before"] = probe("C1")
e, t, dt = call("browser_create",
                {"url": "https://example.com/?arm=C2", "background": True}, 60)
print("    %-26s %-4s %6.2fs  %s" % ("C create background", "ERR" if e else "OK", dt,
                                    t.replace("\n", " ")[:60]))
e, t, dt = call("browser_execute_js", {"code": "document.title", "browser_id": 2}, 60)
print("    %-26s %-4s %6.2fs  %s" % ("C 用 browser_id=2 执行JS", "ERR" if e else "OK", dt,
                                    t.replace("\n", " ")[:60]))
time.sleep(1.0)
results["C_after"] = probe("C2")

print("\n===== 汇总(主浏览器 get_text / execute_js 耗时, 秒) =====")
for k in ("A_before", "A_after", "B_before", "B_after", "C_before", "C_after"):
    g, x = results[k]
    flag = "  <== 退化" if (g > 3.0 or x > 5.0) else ""
    print("  %-10s get_text=%6.2f  execute_js=%6.2f%s" % (k, g, x, flag))

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("\n  已关闭")
