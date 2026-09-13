# -*- coding: utf-8 -*-
"""验证 v2.8.2: (A) Hook日志缺陷修复  (B) V8级Hook与插装新能力 (10个工具)

纪律: 每步独立命名, 不用会破坏闭包引用的方式改全局(本轮教训);
      先判定响应成功/失败再做内容断言; 期望值取自页面真值。
"""
import json
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
RUN = str(int(time.time()))[-6:]
res = []
ENV_ONLY = {"id", "jsonrpc", "success", "data", "message", "result", "error",
            "result_json", "poll_hint", "_hint", "needs_reload", "ok", "_async"}


def call(name, args, timeout=40):
    try:
        r = urllib.request.Request(
            BASE + "/mcp",
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                             "params": {"name": name, "arguments": args}},
                            ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(r, timeout=timeout).read().decode())
    except Exception as ex:
        return True, "EXC:%s" % ex
    if "result" not in d:
        return True, "RPCERR:%s" % json.dumps(d.get("error"), ensure_ascii=False)
    rr = d["result"]
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt


def payload(t):
    def collect(n, out, d=0):
        if d > 6:
            return
        if isinstance(n, dict):
            out.append(n)
            for v in n.values():
                collect(v, out, d + 1)
        elif isinstance(n, str) and n.strip().startswith(("{", "[")):
            try:
                collect(json.loads(n), out, d + 1)
            except Exception:
                pass
    s = (t or "").strip()
    try:
        root = json.loads(s)
    except Exception:
        return {}
    cands = []
    collect(root, cands)
    best, bs = (root if isinstance(root, dict) else {}), -1
    for d in cands:
        sc = len([k for k in d if k not in ENV_ONLY])
        sc += sum(1 for k, v in d.items()
                  if isinstance(v, list) and v and k not in ENV_ONLY)
        if sc > bs:
            best, bs = d, sc
    return best


def js(code, maxms=None):
    a = {"code": code}
    if maxms:
        a["max_ms"] = maxms
    e, t = call("browser_execute_js", a, timeout=(maxms / 1000 + 8) if maxms else 30)
    if e:
        return None
    try:
        j = json.loads(t)
        if isinstance(j, dict):
            return str(j.get("message"))
    except Exception:
        pass
    return t.strip().strip('"')


def rec(tag, ok, d=""):
    res.append((tag, ok))
    print("  [%s] %-52s %s" % ("PASS" if ok else "FAIL", tag, str(d)[:110]))


print("== 预检 ==")
h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
print("  tools=%s cdp=%s latency_max=%s" % (h.get("tool_count"), h.get("cdp_ready"),
                                            h.get("latency_max_ms")))
rec("工具总数 291(新增11个V8/插装/异常工具)", h.get("tool_count") == 291, h.get("tool_count"))

call("browser_navigate", {"url": "https://example.com/?v8=%s" % RUN, "wait_for_load": True}, 45)
time.sleep(0.4)

# ══════════ A. Hook 日志缺陷修复 ══════════
print("\n== A. Hook日志: 缺省log_key应能自动找到函数Hook日志 ==")
FN = "mcpV8Fn" + RUN
js("window.%s=function(a,b){return a+b};'ok'" % FN)
time.sleep(0.2)
e, t = call("browser_reverse_hook", {"type": "function_call", "target": "window." + FN})
rec("browser_reverse_hook 提交成功", not e, "hook")
time.sleep(0.8)
v = js("String(window.%s(7,8))" % FN)
rec("被Hook函数语义不变(返回15)", v == "15", v)
time.sleep(0.4)

e, t = call("browser_reverse_hook_logs", {"action": "query"})
p = payload(t)
byk = p.get("by_key") or {}
print("     count=%s by_key=%s keys=%s" % (p.get("count"), byk, p.get("keys")))
rec("【缺陷1修复】缺省log_key即查到Hook日志(count>0)", (p.get("count") or 0) > 0, p.get("count"))
rec("  by_key 报出 __MCP_HOOK_LOG__ 条数", (byk.get("__MCP_HOOK_LOG__") or 0) > 0, byk)
rec("  日志内含被测函数名", FN in json.dumps(p, ensure_ascii=False), "")
rec("  日志内含本次参数/返回值", ('"args"' in json.dumps(p) or "args" in json.dumps(p)), "")

print("\n== A2. clear 后已安装的 Hook 必须继续记录(原地截断) ==")
e, t = call("browser_reverse_hook_logs", {"action": "clear"})
pclr = payload(t)
print("     cleared=%s by_key=%s" % (pclr.get("cleared"), pclr.get("by_key")))
js("String(window.%s(1,1))" % FN)
time.sleep(0.4)
e, t = call("browser_reverse_hook_logs", {"action": "query"})
p2 = payload(t)
rec("【缺陷2修复】clear后Hook仍在记录(count==1)", (p2.get("count") or 0) == 1, p2.get("count"))

print("\n== A3. hook_multi 与 fetch 原生函数(标称可用) ==")
e, t = call("browser_reverse_hook_multi", {"functions": json.dumps(["window.%s" % FN])}, 30)
rec("hook_multi 返回明确结果", not e and "Hook错误" not in t, t.replace("\n", " ")[:70])

# ══════════ B. V8 插装 ══════════
print("\n== B0. 启用调试器 + 注入标记脚本 ==")
e, t = call("browser_debugger_enable", {}, 30)
rec("browser_debugger_enable 成功", not e, t.replace("\n", " ")[:70])
MARK = "MCPV8MARK" + RUN
js("var s=document.createElement('script');s.textContent='window.__%s=1';"
   "document.head.appendChild(s);'inj'" % MARK)
time.sleep(0.5)

e, t = call("browser_reverse_search_script", {"action": "list"}, 30)
pl = payload(t)
print("     count=%s" % pl.get("count"))
rec("【新】脚本注册表已累积(scriptParsed>0)", (pl.get("count") or 0) > 0, pl.get("count"))
if pl.get("count"):
    print("     前2条: %s" % (pl.get("scripts_json") or "")[:220])

print("\n== B1. V8全脚本检索(含动态注入脚本) ==")
e, t = call("browser_reverse_search_script", {"query": MARK}, 60)
ps = payload(t)
print("     scanned=%s matched=%s hits=%s stale=%s" %
      (ps.get("scanned_scripts"), ps.get("matched_scripts"), ps.get("total_hits"),
       ps.get("stale_scripts")))
rec("【新】searchInContent 命中动态注入脚本的标记串", (ps.get("total_hits") or 0) > 0,
    ps.get("results_json", "")[:110])

print("\n== B2. 精确覆盖率(混淆定位) ==")
e, t = call("browser_reverse_precise_coverage", {"action": "start"}, 40)
rec("precise_coverage start 成功", not e, t.replace("\n", " ")[:70])
js("String(window.%s(2,3))" % FN)
time.sleep(0.3)
e, t = call("browser_reverse_precise_coverage", {"action": "take"}, 60)
pt = payload(t)
body = str(pt.get("cdp_result") or "")
print("     cdp_result 长度=%d 片段=%s" % (len(body), body[:160]))
rec("【新】take 返回非空覆盖率数据", len(body) > 20, body[:80])
e, t = call("browser_reverse_precise_coverage", {"action": "stop"}, 40)
rec("precise_coverage stop 成功", not e, "")

print("\n== B3. 黑盒/异步栈/断点开关/跳过暂停 ==")
for tool, args in [
        ("browser_reverse_blackbox", {"patterns": json.dumps([".*jquery.*"])}),
        ("browser_reverse_async_stack", {"depth": 16}),
        ("browser_reverse_breakpoints_active", {"active": False}),
        ("browser_reverse_skip_pauses", {"skip": True})]:
    e, t = call(tool, args, 30)
    rec("【新】%s" % tool.replace("browser_reverse_", ""), not e, t.replace("\n", " ")[:60])

e, t = call("browser_reverse_blackbox", {"patterns": "[]"}, 30)
rec("blackbox 空数组=清除", not e, "")

print("\n== B4. V8脚本级插装 beforeScriptExecution(拆打包器核心) ==")
# 上一节把 skip_pauses 设为真(全局跳过暂停), 必须先关掉, 否则插装命中了也不会真的暂停
call("browser_reverse_skip_pauses", {"skip": False}, 30)
time.sleep(0.2)
e, t = call("browser_reverse_instrument_script", {"action": "install"}, 30)
pi = payload(t)
raw = json.dumps(pi, ensure_ascii=False)
print("     verified=%s enforced警告=%s" % (pi.get("verified"), "有" if pi.get("warning") else "无"))
rec("【新】install 被CDP接受(breakpointId)", not e and "breakpointId" in raw, (str(pi.get("cdp_result")) or t)[:70])
# 关键: 本机实测该插装"接受但不生效", 工具必须如实报告, 绝不能假成功
if pi.get("verified") == "false":
    rec("【诚实性】未生效时如实报告 warning+替代路径(非假成功)",
        bool(pi.get("warning")) and bool(pi.get("alternative")), str(pi.get("warning"))[:90])
else:
    # 若换到真的支持该插装的Chromium, 则应自检通过并确实暂停
    js("var s=document.createElement('script');s.textContent='window.__IV%s=1';"
       "document.head.appendChild(s);'x'" % RUN, maxms=3000)
    e, t = call("browser_debugger_wait_paused", {"max_ms": 5000}, 20)
    rec("插装确实命中暂停(beforeScriptExecution)", not e, t.replace("\n", " ")[:70])
    call("browser_debugger_resume", {}, 20)
e, t = call("browser_reverse_instrument_script", {"action": "suppress"}, 30)
rec("suppress 止血成功(插装保留但不再拦截)", not e, t.replace("\n", " ")[:60])
e, t = call("browser_reverse_instrument_script", {"action": "remove"}, 30)
rec("remove 本机不支持时给出可行动指引", ("suppress" in t or "debugger_disable" in t), t.replace("\n", " ")[:100])

print("\n== B4b. 异常暂停 setPauseOnExceptions(调试器仍启用) ==")
e, t = call("browser_reverse_pause_on_exceptions", {"state": "caught"}, 30)
rec("【新】pause_on_exceptions 开启", not e, t.replace("\n", " ")[:80])
e, t = call("browser_reverse_pause_on_exceptions", {"state": "none"}, 30)
rec("pause_on_exceptions 关闭", not e, t.replace("\n", " ")[:80])
e, t = call("browser_reverse_pause_on_exceptions", {"state": "bogus"}, 20)
rec("非法state被拒", ("只支持" in t) or e, t.replace("\n", " ")[:80])
call("browser_cdp_call", {"method": "Debugger.disable", "params": "{}"}, 20)  # 清场(实测可清掉插装)

print("\n== B5. 诚实性: 未暂停时的篡改工具必须明确报错 ==")
e, t = call("browser_reverse_return_value", {"value": "true"}, 20)
rec("return_value 未暂停时拒绝并给指引", ("暂停" in t) or e, t.replace("\n", " ")[:80])
e, t = call("browser_reverse_set_variable", {"variable_name": "x", "value": "1"}, 20)
rec("set_variable 未暂停时拒绝并给指引", ("暂停" in t) or e, t.replace("\n", " ")[:80])
e, t = call("browser_reverse_patch", {"script_id": "1"}, 20)
rec("patch 缺source时拒绝", ("source" in t) or e, t.replace("\n", " ")[:80])
e, t = call("browser_reverse_instrument_script", {"event": "bogus"}, 20)
rec("instrument_script 非法event被拒", ("只支持" in t) or e, t.replace("\n", " ")[:80])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
