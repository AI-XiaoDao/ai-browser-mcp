# -*- coding: utf-8 -*-
"""对照测量: browser_reverse_return_value 报 `setReturnValue 失败: Invalid parameters`, 到底是谁的问题?

§111.4 记录: 前置三步全 OK(页面确实停在断点上), 工具构造的参数是 `{"result":{"value":<v>}}`,
与 CDP 的 CallArgument 形状一致, 却仍报 Invalid parameters。本轮做**原始 CDP 对照**:
  臂 A: 直接用 browser_cdp_call 发同样的 Debugger.setReturnValue(绕过工具自己的封装)
  臂 B: 用工具 browser_reverse_return_value
两臂在**同一个暂停帧**上依次做, 谁失败、内核原文是什么, 一目了然。
顺带在同一帧上测 browser_reverse_set_variable(它需要 variable_name+value, 我的探针脚本第 2 行有 var v)。

判据: 若臂 A 成功而臂 B 失败 -> 问题在工具的调用路径(封装/帧选择);
      若两臂都失败 -> 问题在"帧不在返回位置"或本机不支持; 两者的修法完全不同。
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

LINES = [
    "window.mcpBpTick=0;",
    "window.mcpBpFn=function mcpBpFn(){",
    "  var v=1;",
    "  return v;",
    "};",
    "window.mcpBpTimer=setInterval(window.mcpBpFn,300);",
    "//# sourceURL=https://example.com/mcp-breakpoint-probe.js",
]
SRC = "\n".join(LINES)
INJ = ("(function(){if(window.mcpBpTimer){try{clearInterval(window.mcpBpTimer)}catch(e){}}"
       "var s=document.createElement('script');s.textContent=%s;"
       "document.body.appendChild(s);return 'installed'})()" % json.dumps(SRC))


def c(n, a, to=60):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or "" for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def unesc(t):
    return t.replace('\\"', '"')


def pause_at_return():
    """启用调试器 + 注入探针 + 停在 return 行上(不 resume)。"""
    c("browser_debugger_enable", {})
    c("browser_execute_js", {"code": INJ})
    time.sleep(0.8)
    e, t = c("browser_debugger_flow",
             {"breakpoint": "mcp-breakpoint-probe", "line": 3,
              "resume": False, "max_ms": 8000})
    print("   停在断点: isError=%s -> %s" % (e, unesc(t)[:150].replace("\n", " ")))
    return not e


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

print("== 准备: 导航 + 停到 return 行 ==")
c("browser_navigate", {"url": "https://example.com/?rv=1", "wait_for_load": True})
time.sleep(0.6)
ok = pause_at_return()
if not ok:
    print("!! 前置没停住, 结论无效")
    sys.exit(2)

print("\n== 臂 A: 原始 CDP(绕过工具封装), 同样的 params ==")
e, t = c("browser_cdp_call", {"method": "Debugger.setReturnValue",
                              "params": json.dumps({"result": {"value": True}})})
print("   isError=%s -> %s" % (e, unesc(t)[:300]))

print("\n== 臂 B: 用工具 browser_reverse_return_value ==")
e, t = c("browser_reverse_return_value", {"value": "true"})
print("   isError=%s -> %s" % (e, unesc(t)[:300]))

print("\n== 顺带: 在同一帧上测 set_variable(变量名 v) ==")
e, t = c("browser_reverse_set_variable", {"variable_name": "v", "value": "42"})
print("   isError=%s -> %s" % (e, unesc(t)[:300]))

print("\n== 收尾: resume ==")
print("   ", c("browser_debugger_resume", {})[1][:100])
