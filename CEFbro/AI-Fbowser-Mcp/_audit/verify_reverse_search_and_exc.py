# -*- coding: utf-8 -*-
"""验收本轮两处修复。

修复1: browser_reverse_search 的注入 JS `t.split('\\r\n')` -> `t.split('\\n')`
   (现状生成给 JS 的是"单引号串里含裸换行"= 未终止字符串 = 解析期 SyntaxError)
修复2: 共享 JS 异常格式化器 优先读 exceptionDetails.exception.description(真原因)
       而不是 exceptionDetails.text(CDP 固定给 "Uncaught"), 并附 line/col

判据(每条都可证伪):
 ① 格式化器: 让浏览器抛一个**我们知道原因**的错误, 报错必须含该原因。
    仅报 "Uncaught" = 未修好。  (这是个判别性观测: 修复前后文本不同, 无其它解释)
 ② browser_reverse_search 不再报 JS 异常(修复前必报 SyntaxError)
 ③ 功能性: 注入一段**已知内容**的内联脚本, 搜其中的独特 token, 必须命中且 snippet 含该 token。
    只证明"不报错"不够 —— 必须证明它真能找到东西。
 ④ 对照(反例): 搜一个**不存在**的 token, 必须 found=0。
    若无 ④ 则 ③ 的"命中"可能只是工具恒返回非空; 两者合起来才有判别力。
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
TOKEN = "mcpSignProbe_8f3a"
res = []


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
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:88]))


# ---- 干净实例起步 ----
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
call("browser_navigate", {"url": "https://example.com/?rsfix=1", "wait_for_load": True}, 45)
time.sleep(0.6)

print("== ① 异常格式化器: 报错必须带真原因(不再是光秃秃的 Uncaught) ==")
e, t, dt = call("browser_execute_js",
                {"code": "throw new Error('mcp-fmt-probe-7d21')"}, 30)
print("     resp: %s" % t[:260])
has_reason = "mcp-fmt-probe-7d21" in t
rec("报错含我们抛出的真原因", has_reason, t[:88])
only_uncaught = ("Uncaught" in t) and (not has_reason)
rec("不再是'只报 Uncaught'(不可行动)", not only_uncaught, t[:88])

print("\n== ①b 语法类错误也应给出真原因(SyntaxError ...) ==")
e, t, dt = call("browser_execute_js", {"code": "var x = 'unterminated"}, 30)
print("     resp: %s" % t[:260])
rec("语法错误给出 SyntaxError 类原因", ("SyntaxError" in t) or ("Invalid or unexpected" in t),
    t[:88])

print("\n== ② browser_reverse_search 不再报 JS 异常 ==")
e, t, dt = call("browser_reverse_search", {"query": "sign"}, 40)
print("     resp: %s" % t[:260])
rec("调用成功(未报 JS异常/SyntaxError)", (not e) and ("JS异常" not in t), "%.2fs | %s" % (dt, t[:70]))

print("\n== ③ 功能性: 注入已知内联脚本后必须搜得到 ==")
inj = ("(function(){var s=document.createElement('script');"
       "s.textContent='var %s = 1; function mcpSignHelper(){return 2;}';"
       "document.body.appendChild(s);return 'injected'})()" % TOKEN)
e, t, dt = call("browser_execute_js", {"code": inj}, 30)
print("     注入: isError=%s %s" % (e, t[:110]))
e, t, dt = call("browser_reverse_search", {"query": TOKEN}, 40)
print("     搜索: isError=%s %s" % (e, t[:400]))
hit = False
try:
    obj = json.loads(t)
    outer = obj.get("data") if isinstance(obj.get("data"), dict) else obj
    found = outer.get("found")
    results = outer.get("results") or []
    hit = (found or 0) >= 1 and any(TOKEN in (r.get("snippet") or "") for r in results)
    print("     found=%s results=%d" % (found, len(results)))
except Exception as ex:
    print("     (解析搜索结果失败: %s)" % ex)
rec("搜到注入的 token 且 snippet 含该 token", hit, t[:88])

print("\n== ④ 对照: 搜不存在的 token 必须 found=0 ==")
e, t, dt = call("browser_reverse_search", {"query": "mcpNoSuchToken_zzz_9911"}, 40)
print("     resp: %s" % t[:240])
zero = False
try:
    obj = json.loads(t)
    outer = obj.get("data") if isinstance(obj.get("data"), dict) else obj
    zero = (outer.get("found") == 0)
    print("     found=%s" % outer.get("found"))
except Exception as ex:
    print("     (解析失败: %s)" % ex)
rec("不存在的 token 得 found=0", zero, t[:88])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
