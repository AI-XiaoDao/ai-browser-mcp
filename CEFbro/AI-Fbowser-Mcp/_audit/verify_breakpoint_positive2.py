# -*- coding: utf-8 -*-
"""正向验证(修正版): 在脚本真实行范围内下断, 并用**真正的刷新**触发重新解析。

上一版两处测试缺陷(都已定位, 与产品无关):
 ① `line: 0` 落在脚本范围之外 —— 欢迎页的内联脚本 startLine=437 / endLine=887,
    第 0 行自然没有有效断点位置, 所以 CDP 回 `locations: []`(工具行为正确);
 ② 用 `browser_navigate` 到"同一个 URL"触发重载 —— 工具做了同址快速路径("已在目标页面, 未重复导航"),
    脚本根本没重新解析。正确做法是 `browser_reload`。
另: 上一版判断"locations 是否为空"时忘了 JSON 里是转义引号(`\\"locations\\":[]`),
导致判定写反 —— 这次直接解析 JSON, 不再用字符串包含判断。
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


def inner(payload_text):
    """把工具返回的文本解析成内层 dict(穿过 data/result 包装), 失败返回 {}。"""
    try:
        o = json.loads(payload_text)
    except Exception:
        return {}
    if isinstance(o, dict) and isinstance(o.get("data"), dict):
        o = o["data"]
    return o if isinstance(o, dict) else {}


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

print("== 1) 读脚本范围(决定 line 该填多少) ==")
# 先显式启用调试器: 上一次跑本脚本时**先 list 后 enable**, 注册表还是空的 ——
# 虽然 search_script 号称"零前置自动启用并等待", 但实测那次没拿到脚本(如实记录该现象),
# 故这里显式 enable 后再列, 让本验证专注于"断点能否命中"这个待答问题。
e, t, _ = call("browser_debugger_enable", {}, 30)
print("  debugger_enable: %s %s" % ("ERR" if e else "OK", t.replace("\n", " ")[:70]))
time.sleep(1.0)
e, t, _ = call("browser_reverse_search_script", {"action": "list"}, 30)
o = inner(t)
scripts = []
try:
    scripts = json.loads(o.get("scripts_json") or "[]")
except Exception as ex:
    print("  解析 scripts_json 失败: %s" % ex)
for s in scripts:
    print("   scriptId=%s url=%r 行范围=%s~%s 长度=%s"
          % (s.get("scriptId"), s.get("url"), s.get("startLine"), s.get("endLine"),
             s.get("length")))
real = [s for s in scripts if (s.get("url") or "") and isinstance(s.get("startLine"), int)]
if not real:
    print("  !! 没有带 URL 与行范围的脚本, 无法做本验证(如实记录)")
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.exit(0)
tgt = real[0]
line = int(tgt.get("startLine") or 0) + 2
uri = tgt["url"]
frag = re.escape(uri.split("?")[0])[:80]
print("\n== 2) 用脚本真实行范围下断: url正则=%r line=%d ==" % (frag[:50], line))
e, t, _ = call("browser_debugger_set_breakpoint", {"url": frag, "line": line}, 30)
o = inner(t)
raw = o.get("cdp_result") or t
locs = None
try:
    locs = json.loads(raw).get("locations")
except Exception:
    pass
print("  cdp_result: %s" % str(raw).replace("\n", " ")[:190])
print("  locations 是否非空(即已绑定到已加载脚本): %s"
      % ("是" if locs else "否(挂起, 需脚本重新解析)"))
call("browser_debugger_enable", {})

print("\n== 3) 真正刷新以触发脚本重新解析(挂起断点此时应绑定并命中) ==")
e, t, dt = call("browser_reload", {"wait_for_load": False}, 30)
print("  reload: %s %.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:80]))
e, t, dt = call("browser_debugger_wait_paused", {"max_ms": 10000}, 30)
print("  wait_paused: %s %.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:190]))
e, t, dt = call("browser_debugger_last_paused", {}, 30)
print("  last_paused: %s %s" % ("ERR" if e else "OK", t.replace("\n", " ")[:150]))

print("\n== 4) resume + 健康检查 ==")
e, t, dt = call("browser_debugger_resume", {}, 30)
print("  resume: %s %s" % ("ERR" if e else "OK", t.replace("\n", " ")[:60]))
e, t, dt = call("browser_execute_js", {"code": "1+1"}, 30)
print("  execute_js: %s %.2fs %s" % ("ERR" if e else "OK", dt, t.replace("\n", " ")[:60]))

subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("\n  已关闭")
