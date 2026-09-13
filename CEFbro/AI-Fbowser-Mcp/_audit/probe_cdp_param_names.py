# -*- coding: utf-8 -*-
"""CDP 参数名风险探针 —— 核验 _audit/_cdp_param_compat.md 的 AT RISK 清单。

设计:
 * P-0 "总闸": 发一个 PDL 里肯定不存在的多余字段, 看内核是否忽略未知字段。
   - 返回 {}          -> 未知字段被忽略 -> A3/A5 等"多字段"风险整体降级
   - Invalid params   -> 多字段会被拒 -> 相关功能当前 100% 失效
 * A1/A2/A4/A5: 每种"怀疑改名的参数"发**两臂对照**(旧名 vs 新名), 让内核在
   报错里自报它真正要的字段名(与 setReturnValue 破案方式相同)。
 * 对每个方法先发一次 `{}` : 报 "wasn't found" = 方法不存在; 报
   "mandatory field missing params.X" = 方法存在且 X 才是它要的字段名。
 * 低风险优先, 拦截类探针放最后并立即复位; 结束时重启进程保证状态干净。
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


def c(n, a, to=45):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    t = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                if i.get("type") == "text")
    return bool(rr.get("isError")), t.replace('\\"', '"')


def cdp(method, params=None):
    e, t = c("browser_cdp_call", {"method": method, "params": params or {}})
    return t[:300].replace("\n", " ")


def cls(t):
    """把回包归类成可判定的短标签(不猜, 只按内核原话)。"""
    low = t.lower()
    if "wasn't found" in low or "was not found" in low or "not found" in low:
        return "方法不存在"
    if "failed to deserialize params" in low:
        return "参数名/字段错(内核自报)"
    if "invalid parameters" in low or "invalid params" in low:
        return "参数被拒"
    if '"error"' in low and "success" not in low:
        return "其它错误"
    return "接受"


def main():
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
    c("browser_navigate", {"url": "https://example.com/?cdpprobe=1", "wait_for_load": True})
    c("browser_debugger_enable", {"action": "enable"})
    c("browser_cdp_call", {"method": "Network.enable", "params": {}})

    print("== P-0 总闸: 未知字段容忍性 ==")
    r = cdp("Debugger.setSkipAllPauses",
            {"skip": True, "__mcp_probe_unknown_field": 1})
    print("   setSkipAllPauses{skip,__mcp_probe_unknown_field} -> [%s] %s" % (cls(r), r))
    gate = cls(r) == "接受"
    print("   => 未知字段%s被忽略; A3/A5 类'多字段'风险%s"
          % ("" if gate else "**不**", "整体降级为安全" if gate else "升级为'当前 100% 失效'"))

    print("\n== A5 Profiler.setSamplingInterval (怀疑 maxDepth 不属于该方法) ==")
    print("   内核只认哪些字段:")
    print("     {}                 -> [%s] %s" % (cls(cdp("Profiler.setSamplingInterval", {})),
                                                cdp("Profiler.setSamplingInterval", {})[:200]))
    r = cdp("Profiler.setSamplingInterval", {"interval": 100})
    print("     {interval:100}     -> [%s] %s" % (cls(r), r))
    r = cdp("Profiler.setSamplingInterval", {"interval": 100, "maxDepth": 32})
    print("     {interval,maxDepth}-> [%s] %s" % (cls(r), r))

    print("\n== A3 Page.addScriptToEvaluateOnNewDocument (怀疑 runImmediately) ==")
    r = cdp("Page.addScriptToEvaluateOnNewDocument", {"source": "void 0"})
    print("     {source}                    -> [%s] %s" % (cls(r), r))
    r = cdp("Page.addScriptToEvaluateOnNewDocument",
            {"source": "void 0", "runImmediately": True})
    print("     {source,runImmediately}     -> [%s] %s" % (cls(r), r))

    print("\n== A4 DOMDebugger.setInstrumentationBreakpoint (eventName 新旧名对照) ==")
    r = cdp("DOMDebugger.setInstrumentationBreakpoint", {"eventName": "setTimeout"})
    print("     {eventName}       -> [%s] %s" % (cls(r), r))
    r = cdp("DOMDebugger.setInstrumentationBreakpoint", {"instrumentation": "setTimeout"})
    print("     {instrumentation} -> [%s] %s" % (cls(r), r))
    for p in ({"eventName": "setTimeout"}, {"instrumentation": "setTimeout"}):
        cdp("DOMDebugger.removeInstrumentationBreakpoint", p)

    print("\n== A1/A2 Network.setRequestInterception (放最后, 立即复位) ==")
    r = cdp("Network.setRequestInterception", {})
    print("     {}                -> [%s] %s" % (cls(r), r))
    r = cdp("Network.setRequestInterception",
            {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]})
    print("     {patterns:[...]}  -> [%s] %s" % (cls(r), r))
    r = cdp("Network.setRequestInterception", {"patterns": []})
    print("     复位 {patterns:[]}-> [%s] %s" % (cls(r), r))
    r = cdp("Fetch.enable", {"patterns": []})
    print("     Fetch.enable      -> [%s] %s" % (cls(r), r))
    r = cdp("Fetch.disable", {})
    print("     Fetch.disable     -> [%s] %s" % (cls(r), r))

    print("\n== 对照: 已知改名成功的两条(应报'接受') ==")
    print("     Debugger.setSkipAllPauses{skip} -> [%s]"
          % cls(cdp("Debugger.setSkipAllPauses", {"skip": True})))

    print("\n== 复位并重启 (保证状态干净) ==")
    c("browser_debugger_enable", {"action": "disable"})
    subprocess.run(['taskkill', '/F', '/IM', 'AI-Fbowser-Mcp.exe'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    subprocess.Popen([EXE], cwd=os.path.dirname(EXE),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        time.sleep(1)
        try:
            urllib.request.urlopen(BASE + '/health', timeout=3).read()
            print("   已重启并就绪")
            break
        except Exception:
            pass


main()
