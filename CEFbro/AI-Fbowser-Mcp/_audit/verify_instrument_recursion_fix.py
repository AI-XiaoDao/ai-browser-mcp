# -*- coding: utf-8 -*-
"""验收 browser_reverse_instrument 的自递归修复(实测崩栈根因)。

判别性 A/B(不需要旧二进制: 臂A 直接把**旧的注入脚本原文**在当前页面求值复现缺陷):
  臂A(旧模板, 内联复现): 用默认目标表装上透明插装 -> 再跑一段"正常"JS(用 push/call/apply)
                          -> 期望**崩栈**(RangeError: Maximum call stack size exceeded)
  臂B(新版工具):         调用真实工具 browser_reverse_instrument(默认目标)
                          -> 同一段 JS 必须**正常返回正确结果**, 且插装仍在记录(instrumented=6, calls>0)
                          -> 并检查 __mcp_orig 已挂在包装器上(后续"卸载"入口的前提)
  两臂之间必须重载页面清场 —— 臂A 会把页面搞坏, 否则会污染臂B(这正是本缺陷的危害)。

臂B 里"必须仍然记录到调用"这一条是**防"修成啥也不干"**的对照: 只证明"不崩"是不够的,
插装必须还能工作。
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
res = []

# 旧模板(逐字来自修复前的 MCP_Server_Core.wsv, 仅把 hint 缩短)
OLD_JS = """(function(){var __targets=['Function.prototype.apply','Function.prototype.call','Array.prototype.push','Array.prototype.pop','String.prototype.indexOf','String.prototype.charAt'];var __count=0;var __max=500;var __results=[];__targets.forEach(function(__t){var __parts=__t.split('.');var __obj=window;for(var __i=0;__i<__parts.length-1;__i++){__obj=__obj[__parts[__i]];if(!__obj)return}var __method=__parts[__parts.length-1];var __orig=__obj[__method];if(typeof __orig!=='function')return;__obj[__method]=function(){if(__count<__max){__results.push({target:__t,args:Array.prototype.slice.call(arguments).map(function(a){return typeof a==='string'?a.substring(0,200):typeof a}).join(','),ts:Date.now()});__count++}return __orig.apply(this,arguments)};__obj[__method].toString=function(){return __orig.toString()}});window.__mcp_instrument_results={instrumented:__targets.length,calls:__count,results:__results};return JSON.stringify({installed:true,targets:__targets.length})})()"""

# "正常业务 JS": 同时用到 push / call / apply(正是默认目标表包装的那几个)
PROBE = ("(function(){var a=[];a.push(1,2,3);var r=Array.prototype.slice.call(a,1);"
         "var f=function(x){return x+1};var y=f.apply(null,[41]);"
         "return JSON.stringify({len:a.length,r:r,y:y})})()")


def call(name, args, timeout=45):
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


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-48s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:88]))


def unesc(t):
    """响应里的内层 JSON 是被转义过的(形如 \\"len\\":3), 断言前先还原。
    (第一版没做这一步, 于是"基线正常"也被判 FAIL —— 又是转义坑。)
    """
    return t.replace('\\"', '"').replace(" ", "")


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
call("browser_navigate", {"url": "https://example.com/?recfix=1", "wait_for_load": True}, 45)
time.sleep(0.6)

e, t, dt = call("browser_execute_js", {"code": PROBE}, 30)
print("== 基线: 未插装时该 JS 应正常 ==")
print("   %s" % t[:220])
rec("基线正常运行(拿到 len=3,r=[2,3],y=42)", (not e) and ('"len":3' in unesc(t)), t[:88])
base_ok = (not e) and ('"len":3' in unesc(t))

print("\n== 臂A: 用**旧模板**内联复现缺陷(应崩栈) ==")
e, t, dt = call("browser_execute_js", {"code": OLD_JS}, 30)
print("   安装: isError=%s %s" % (e, t[:150]))
e2, t2, dt2 = call("browser_execute_js", {"code": PROBE}, 30)
print("   插装后跑同一段 JS: isError=%s" % e2)
print("   %s" % t2[:300])
crashed = e2 or ("call stack" in t2.lower()) or ("RangeError" in t2) or ("递归" in t2) \
    or ('"len":3' not in unesc(t2))
rec("旧模板确实把页面搞坏(复现缺陷)", crashed, t2[:88])

print("\n== 重载清场(臂A 已把页面搞坏, 必须清掉) ==")
call("browser_navigate", {"url": "https://example.com/?recfix=2", "wait_for_load": True}, 45)
time.sleep(0.6)
e, t, dt = call("browser_execute_js", {"code": PROBE}, 30)
rec("清场后基线恢复正常", (not e) and ('"len":3' in unesc(t)), t[:88])

print("\n== 臂B: 用**新版工具**装同一套默认目标 -> 同一段 JS 必须正常 ==")
e, t, dt = call("browser_reverse_instrument", {}, 45)
print("   安装: isError=%s %s" % (e, t[:200]))
probe_ok = False
if e:
    print("   !! 安装本身失败, 臂B 无法继续")
else:
    # 工具是异步的: 等它提交完成
    time.sleep(1.2)
    e2, t2, dt2 = call("browser_execute_js", {"code": PROBE}, 30)
    print("   插装后跑同一段 JS: isError=%s" % e2)
    print("   %s" % t2[:300])
    probe_ok = (not e2) and ('"len":3' in unesc(t2)) and ('"y":42' in unesc(t2))
    rec("新版插装后该 JS 正常返回正确结果(不再崩栈)", probe_ok, t2[:88])

if probe_ok:
    e3, t3, _ = call("browser_execute_js",
                     {"code": "JSON.stringify({i:window.__mcp_instrument_results?"
                              "window.__mcp_instrument_results.instrumented:-1,"
                              "c:window.__mcp_instrument_results?"
                              "window.__mcp_instrument_results.calls:-1,"
                              "orig:typeof Array.prototype.push.__mcp_orig})"}, 30)
    print("   插装状态: %s" % t3[:260])
    rec("插装仍在工作(instrumented=6 且 calls>0)",
        ('"i":6' in unesc(t3)) and ('"c":0' not in unesc(t3)), t3[:88])
    rec("已挂 __mcp_orig(后续卸载入口的前提)",
        '"orig":"function"' in unesc(t3), t3[:88])

# 收尾: 重载页面, 不留插装在现场
call("browser_navigate", {"url": "https://example.com/?cleaned=1", "wait_for_load": True}, 45)
time.sleep(0.5)
e, t, _ = call("browser_execute_js",
               {"code": "typeof window.__mcp_instrument_results"}, 30)
rec("收尾: 重载后插装已清除", "undefined" in t, t[:88])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
