# -*- coding: utf-8 -*-
"""正向验证: 在**脚本 URL 非空**的页面上, 按 URL 正则下断能否真的命中?

为什么必须做这一步: 上一轮"断点不命中"的结论来自 about:blank + document.write 的页面,
而那种页面的内联脚本 URL 是**空串**(实测 scriptId=5, url=""), URL 正则匹配不到它 ——
属**测试场景特殊**, 不能据此判产品有缺陷。必须在真实(URL 非空)页面上验证一次,
否则等于用错误场景给产品定罪(本项目已因此误判过)。

做法: 用应用自带的欢迎页(本地 http 地址, 有真实 URL 与脚本) —— 先读脚本 URL, 再按该 URL 下断,
然后**重新导航**触发脚本重新解析(挂起的断点此时才会绑定并命中)。
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


def call(name, args, timeout=35):
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

print("== 1) 当前页地址与脚本 URL ==")
e, t, _ = call("browser_execute_js", {"code": "location.href"})
print("  location.href: %s" % t.replace("\n", " ")[:110])
cur = ""
m = re.search(r'"message":"([^"]+)"', t)
if m:
    cur = m.group(1)
call("browser_debugger_enable", {})

e, t, _ = call("browser_reverse_search_script", {"action": "list"}, 30)
print("  scripts: %s" % t.replace("\n", " ")[:300])

# 找一个"非空 URL"的脚本作为断点目标
targets = re.findall(r'\\"url\\":\\"([^"\\]*)\\"', t) or re.findall(r'"url":"([^"]*)"', t)
targets = [x for x in targets if x]
print("  非空脚本 URL 候选: %s" % targets[:4])
if not targets:
    print("  !! 没找到非空 URL 的脚本, 本页不适合做该验证(如实记录, 不硬下结论)")
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.exit(0)

uri = targets[0]
# 用该 URL 的主机片段做正则(避免正则里出现 . 与 / 的转义问题)
frag = re.escape(uri.split("?")[0])[:60]
print("\n== 2) 按 URL 正则下断(目标: %s) ==" % frag[:70])
e, t, _ = call("browser_debugger_set_breakpoint", {"url": frag, "line": 0}, 30)
print("  set_breakpoint: %s %s" % ("ERR" if e else "OK", t.replace("\n", " ")[:200]))
bound = '"locations":[]' not in t.replace(" ", "")
print("  是否立即绑定到已加载脚本(locations 非空)? %s" % ("是" if bound else "否(挂起)"))

print("\n== 3) 重新导航以触发脚本重新解析(挂起断点应在此绑定并命中) ==")
e, t, dt = call("browser_navigate", {"url": cur, "wait_for_load": True}, 40)
print("  navigate: %s %.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:90]))
e, t, dt = call("browser_debugger_wait_paused", {"max_ms": 6000}, 30)
print("  wait_paused: %s %.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:150]))

e, t, dt = call("browser_debugger_last_paused", {}, 30)
print("  last_paused: %s %s" % ("ERR" if e else "OK", t.replace("\n", " ")[:150]))

print("\n== 4) resume + 健康检查 ==")
e, t, dt = call("browser_debugger_resume", {}, 30)
print("  resume: %s %s" % ("ERR" if e else "OK", t.replace("\n", " ")[:70]))
e, t, dt = call("browser_execute_js", {"code": "1+1"}, 30)
print("  execute_js: %s %.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:60]))

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("\n  已关闭")
