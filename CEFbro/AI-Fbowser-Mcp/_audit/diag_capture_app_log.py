# -*- coding: utf-8 -*-
"""抓应用自身的控制台输出, 看清 CDP 观察者在两个浏览器之间**到底怎么切换/是否切换成功**。

## 为什么用日志而不是继续推理
源码显示 `执行CDP命令_带参数` 在"观察者未注册或附着于其它浏览器"时会自动重注册,
并在成功时打印 `[MCP] CDP观察者已自动注册到浏览器 ID:<n>`。也就是说**程序会自己把这次切换说清楚**——
只要能看到它的控制台输出, 就不必再猜"为什么没自愈"。
故本脚本把 exe 的 stdout/stderr **重定向到文件**, 跑一遍"创建后台浏览器 → 在它上面执行JS → 再用主浏览器",
然后把日志里与观察者/注册/错误相关的行**按时间顺序**打出来。
"""
import json
import os
import shutil
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
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_app_console.log")


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


subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)

# 关键: 把 exe 的输出接到文件(而不是丢弃), 才能看到它自己说的观察者切换过程
logf = io = __import__("io").open(LOG, "w", encoding="utf-8", errors="replace")
proc = subprocess.Popen([EXE], cwd=os.path.dirname(EXE), stdout=logf, stderr=subprocess.STDOUT)
for _ in range(60):
    time.sleep(1)
    try:
        urllib.request.urlopen(BASE + '/health', timeout=3).read()
        time.sleep(4.5)
        break
    except Exception:
        pass

print("== 基线: 主浏览器 ==")
e, t, dt = call("browser_get_text", {"selector": "h1"}, 60)
print("  get_text %-4s %6.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:50]))

print("\n== 创建后台浏览器(不使用) ==")
e, t, dt = call("browser_create", {"url": "https://example.com/?log=1", "background": True}, 60)
print("  create   %-4s %6.2fs" % ("ERR" if e else "OK", dt))

print("\n== 在后台浏览器上执行 JS(browser_id=2) ==")
e, t, dt = call("browser_execute_js", {"code": "document.title", "browser_id": 2}, 60)
print("  exec#2   %-4s %6.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:50]))

print("\n== 再用主浏览器 ==")
e, t, dt = call("browser_get_text", {"selector": "h1"}, 60)
print("  get_text %-4s %6.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:50]))
e, t, dt = call("browser_execute_js", {"code": "1+1"}, 60)
print("  exec#1   %-4s %6.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:50]))

time.sleep(1.0)
logf.flush()
subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.0)
try:
    logf.close()
except Exception:
    pass

print("\n== 应用控制台输出中与观察者/注册/失败相关的行(按顺序) ==")
try:
    txt = open(LOG, encoding="utf-8", errors="replace").read()
except Exception as ex:
    print("  读取日志失败: %s" % ex); sys.exit(0)
keys = ("观察者", "注册", "CDP", "浏览器", "错误", "失败", "超时", "异常")
n = 0
for line in txt.split("\n"):
    if line.strip() and any(k in line for k in keys):
        n += 1
        print("  %s" % line.strip()[:200])
print("  (共 %d 行; 完整日志: %s)" % (n, os.path.basename(LOG)))
