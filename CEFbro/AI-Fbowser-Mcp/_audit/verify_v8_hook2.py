# -*- coding: utf-8 -*-
"""v2.8.2 续: 验证新增 10 个工具 (含goal明确要求的 getPossibleBreakpoints / addBinding)
   以及脚本注册表"导航后清表"修复。"""
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


def js(code):
    e, t = call("browser_execute_js", {"code": code})
    if e:
        return None
    try:
        j = json.loads(t)
        if isinstance(j, dict):
            return str(j.get("message"))
    except Exception:
        pass
    return t.strip().strip('"')


def cdpres(t):
    """取工具回复里的 cdp_result 文本(字符串)"""
    return str(payload(t).get("cdp_result") or "")


def rec(tag, ok, d=""):
    res.append((tag, ok))
    print("  [%s] %-50s %s" % ("PASS" if ok else "FAIL", tag, str(d)[:105]))


print("== 预检 ==")
h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
print("  tools=%s cdp=%s latency_max=%s" % (h.get("tool_count"), h.get("cdp_ready"),
                                            h.get("latency_max_ms")))
rec("工具总数 301(本轮再+10)", h.get("tool_count") == 301, h.get("tool_count"))

call("browser_navigate", {"url": "https://example.com/?v82=%s" % RUN, "wait_for_load": True}, 45)
time.sleep(0.4)
call("browser_debugger_enable", {}, 30)
# 造一个带事件监听器的对象 + 一个原型实例 + 一个函数, 供后续用例使用
js("window.__t%s={n:1};window.__t%s.addEventListener('click',function __mcpHandler(){return 1});"
   "window.__C%s=function(){};window.__C%s.prototype.k=1;window.__inst%s=new window.__C%s();'ok'"
   % (RUN, RUN, RUN, RUN, RUN, RUN))
time.sleep(0.4)

print("\n== 1. dom_resolve 取 objectId(公共入口) ==")
e, t = call("browser_reverse_dom_resolve", {"expression": "window.__t" + RUN}, 30)
pr = payload(t)
oid = str(pr.get("object_id") or "")
print("     object_id=%s  properties_json长度=%d" % (oid[:26], len(str(pr.get("properties_json") or ""))))
rec("【新】expression 解析出 objectId", not e and len(oid) > 3, oid[:40])
rec("  顺带返回自有属性", len(str(pr.get("properties_json") or "")) > 10, "")
e, t = call("browser_reverse_dom_resolve", {"expression": "1+1"}, 20)
rec("表达式返回基本类型时明确报错(非空objectId)", e or "objectId" in t, t.replace("\n", " ")[:80])

print("\n== 2. listeners 事件监听器取证 ==")
e, t = call("browser_reverse_listeners", {"selector": "window.__t" + RUN}, 30)
body = cdpres(t)
print("     cdp_result: %s" % body[:150])
rec("【新】selector 路径取到监听器(含 click)", ("click" in body) and ("handler" in body or "scriptId" in body), body[:80])
e, t = call("browser_reverse_listeners", {"selector": "#definitely-not-exist-xyz"}, 20)
rec("元素不存在时明确报错(不假成功)", e or "objectId" in t, t.replace("\n", " ")[:80])

print("\n== 3. get_possible_breakpoints 混淆定点下断(goal明确要求) ==")
e, t = call("browser_reverse_search_script", {"action": "list"}, 30)
sids = []
try:
    sids = json.loads(payload(t).get("scripts_json") or "[]")
except Exception:
    pass
print("     注册脚本数=%d" % len(sids))
rec("  注册表非空可取到 scriptId", len(sids) > 0, len(sids))
if sids:
    sid = sids[0].get("scriptId")
    e, t = call("browser_reverse_get_possible_breakpoints",
                {"script_id": sid, "line": 0, "end_line": 50}, 30)
    body = cdpres(t)
    print("     scriptId=%s cdp_result=%s" % (sid, body[:150]))
    rec("【新】返回可下断的精确位置(locations)", ("location" in body or "lineNumber" in body), body[:80])
e, t = call("browser_reverse_get_possible_breakpoints", {}, 20)
rec("缺 script_id 时明确报错并指路", ("script_id" in t) and e, t.replace("\n", " ")[:90])

print("\n== 4. add_binding 原生桥接(goal明确要求) ==")
BN = "__mcp_bind_" + RUN
e, t = call("browser_reverse_add_binding", {"name": BN}, 30)
rec("【新】Runtime.addBinding 成功", not e, cdpres(t)[:60])
e, t = call("browser_reverse_add_binding", {}, 20)
rec("缺 name 时明确报错", ("name" in t) and e, t.replace("\n", " ")[:80])

print("\n== 5. compile_script 编译不执行 ==")
e, t = call("browser_reverse_compile_script", {"source": "var __ok%s=1;" % RUN}, 30)
b1 = cdpres(t)
rec("【新】合法源码编译成功(返回scriptId)", ("scriptId" in b1), b1[:80])
e, t = call("browser_reverse_compile_script", {"source": "var a=(;"}, 30)
b2 = cdpres(t)
rec("  语法错误在 cdp_result 里暴露(exceptionDetails)", "exceptionDetails" in b2, b2[:80])
e, t = call("browser_reverse_compile_script", {}, 20)
rec("缺 source 时明确报错", ("source" in t) and e, t.replace("\n", " ")[:80])

print("\n== 6. bypass_csp / cache_disable ==")
e, t = call("browser_reverse_bypass_csp", {"enable": True}, 30)
rec("【新】Page.setBypassCSP 成功", not e, cdpres(t)[:50])
e, t = call("browser_reverse_cache_disable", {"disable": True}, 30)
rec("【新】Network.setCacheDisabled 成功", not e, cdpres(t)[:50])
e, t = call("browser_reverse_cache_disable", {"disable": False}, 30)
rec("  恢复缓存成功", not e, "")

print("\n== 7. evaluate_silent 静默求值 ==")
e, t = call("browser_reverse_evaluate_silent", {"expression": "1+41"}, 30)
b = cdpres(t)
print("     cdp_result=%s" % b[:120])
rec("【新】静默求值返回正确结果(42)", ("42" in b), b[:70])
e, t = call("browser_reverse_evaluate_silent", {}, 20)
rec("缺 expression 时明确报错", ("expression" in t) and e, t.replace("\n", " ")[:80])

print("\n== 8. await_promise 等Promise结果 ==")
e, t = call("browser_reverse_await_promise", {"expression": "Promise.resolve(7)"}, 30)
b = cdpres(t)
print("     cdp_result=%s" % b[:140])
rec("【新】Promise resolve 出结果(7)", ("7" in b), b[:70])
e, t = call("browser_reverse_await_promise", {}, 20)
rec("缺表达式时明确报错", e or "expression" in t, t.replace("\n", " ")[:80])

print("\n== 9. query_objects 找全部实例 ==")
e, t = call("browser_reverse_query_objects",
            {"prototype_expression": "window.__C%s.prototype" % RUN}, 30)
b = cdpres(t)
print("     cdp_result=%s" % b[:130])
rec("【新】按原型找到实例", ("objectId" in b or "object" in b), b[:70])
e, t = call("browser_reverse_query_objects", {}, 20)
rec("缺原型参数时明确报错", e or "prototype" in t, t.replace("\n", " ")[:80])

print("\n== 10. 脚本注册表导航清表(修复 stale) ==")
call("browser_navigate", {"url": "https://example.com/?v82b=%s" % RUN, "wait_for_load": True}, 45)
time.sleep(0.6)
e, t = call("browser_reverse_search_script", {"query": RUN}, 60)
ps = payload(t)
print("     scanned=%s stale=%s matched=%s" % (ps.get("scanned_scripts"), ps.get("stale_scripts"),
                                               ps.get("matched_scripts")))
rec("【修复】导航后无失效scriptId(stale_scripts==0)",
    (ps.get("stale_scripts") or 0) == 0, ps.get("stale_scripts"))

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
