# -*- coding: utf-8 -*-
r"""验证第130轮: ①`browser_get_text.max_chars` 真的生效(此前声明了却从不读);
             ②`browser_debugger_set_breakpoint` 的 CDP 别名可传;
             ③`workflow_run` 的 `file` 别名与 steps 字段表按文档可用(用内联 steps 真跑一遍)。

用法: py -3 _audit\verify_round130.py
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _console  # noqa: F401

BASE = "http://127.0.0.1:9222"
RES = []


def call(n, a=None, to=90):
    b = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": n, "arguments": a or {}}}
    r = urllib.request.Request(BASE + "/mcp",
                               data=json.dumps(b, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
    o = json.loads(urllib.request.urlopen(r, timeout=to).read().decode("utf-8"))
    rr = o.get("result") or {}
    return bool(rr.get("isError")), "".join(i.get("text") or ""
                                            for i in (rr.get("content") or [])
                                            if i.get("type") == "text")


def rec(tag, ok, detail=""):
    RES.append((tag, ok))
    print('  [%s] %-52s %s' % ('PASS' if ok else 'FAIL', tag, str(detail)[:104]))


def obj(t):
    try:
        return json.loads(t)
    except Exception:
        return None


T = {t["name"]: t for t in json.loads(urllib.request.urlopen(BASE + "/tools/list", timeout=20).read().decode())["tools"]}


def props(n):
    return set(((T.get(n, {}).get("inputSchema") or {}).get("properties") or {}).keys())


def req(n):
    return ((T.get(n, {}).get("inputSchema") or {}).get("required") or [])


print('== ① browser_get_text 的 max_chars 必须真的生效 ==')
call("browser_navigate", {"url": "https://example.com/?gt=%d" % int(time.time())})
call("browser_execute_js", {"code": "document.body.insertAdjacentHTML('beforeend','<div id=gtpad>'+'Z'.repeat(5000)+'</div>'); 'ok'"})
time.sleep(0.5)
e1, t1 = call("browser_get_text", {})
o1 = obj(t1) or {}
rec("不带 max_chars: 取全文(回归)", (not e1), "len=%d" % len(str(o1.get("message") or t1)))
e2, t2 = call("browser_get_text", {"max_chars": 50})
o2 = obj(t2) or {}
rec("带 max_chars=50 时按 50 截断(修复点)",
    (o2.get("truncated_to") == 50) and len(str(o2.get("message") or "")) == 50,
    "truncated_to=%s len=%s" % (o2.get("truncated_to"), len(str(o2.get("message") or ""))))
e3, t3 = call("browser_get_text", {"max_chars": 999999999})
o3 = obj(t3) or {}
rec("max_chars 超上限时回退默认(不报错, 不当成 0)", not e3,
    "truncated_to=%s" % o3.get("truncated_to"))
call("browser_execute_js", {"code": "(function(){var o=document.getElementById('gtpad');if(o)o.remove();return 'ok'})()"})

print('\n== ② set_breakpoint 的 CDP 原生别名 ==')
bp = props("browser_debugger_set_breakpoint")
rec("声明了 line_number/column_number(实现真读)", {"line_number", "column_number"} <= bp, sorted(bp))

print('\n== ③ workflow_run: file 别名 + steps 字段表(真跑一遍内联步骤) ==')
wf = props("workflow_run")
rec("声明了 file(与 name 等价)", "file" in wf, sorted(wf))
rec("required 不再硬要 name(入口四选一)", "name" not in req("workflow_run"), "required=%s" % req("workflow_run"))
d = T.get("workflow_run", {}).get("description", "")
rec("描述含步骤字段表(源码核实的字段名)",
    all(k in d for k in ("args|arguments", "wait_async", "delay_ms", "on_error")), d[:100])
e4, t4 = call("workflow_run", {"steps": [
    {"tool": "browser_execute_js", "args": {"code": "1+1"}},
    {"tool": "browser_get_url"},
    {"tool": "browser_execute_js", "args": {"code": "document.title"}},
]})
o4 = obj(t4) or {}
d4 = o4.get("data") if isinstance(o4.get("data"), dict) else o4   # 回包把载荷包在 data 里(探针第一版漏解包)
print('     %s' % t4.replace('\n', ' ')[:200])
rec("内联 steps + args 真能跑通(文档与实现一致)", not e4, t4[:90])
rec("执行了 3 步且全部成功(total_steps/success_count)",
    (d4.get("total_steps") == 3) and (d4.get("success_count") == 3),
    "total_steps=%s success_count=%s" % (d4.get("total_steps"), d4.get("success_count")))

print('\n== ④ browser_reverse_websocket: request_id 已声明 + query 语义如实 ==')
ws = props("browser_reverse_websocket")
rec("声明了 request_id(实现真读的必填项)", "request_id" in ws, sorted(ws))
dws = T.get("browser_reverse_websocket", {}).get("description", "")
rec("描述写清 query 走 Network.getResponseBody(不是解码后的 WS 帧)",
    "Network.getResponseBody" in dws and "不是" in dws, dws[:110])
e5, t5 = call("browser_reverse_websocket", {"action": "query"})
rec("query 缺 request_id 给可行动错误", e5 and ("request_id" in t5), t5[:100])

bad = [x for x, o in RES if not o]
print('\n结果: %d/%d 通过' % (len(RES) - len(bad), len(RES)))
for x in bad:
    print('   未通过: %s' % x)
sys.exit(1 if bad else 0)
