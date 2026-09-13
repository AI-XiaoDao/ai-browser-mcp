# -*- coding: utf-8 -*-
"""本轮待验证修复的定向验收(目标 < 15 秒)。

覆盖 6 项本轮改动:
  1) browser_kernel_events_all / reverse_probe / reverse_trace / reverse_algo /
     reverse_watch_global 缺 action -> 必须报错(原先会**直接执行** enable/start)
  2) browser_element_action 缺 index -> 必须报错(原省会点快照第 0 个元素)
  3) browser_highlight duration_ms:0 -> 必须"不自动清除"(原先被改成 3000ms)
  4) browser_fill_form 全字段失败 -> 必须 isError(原先硬编码 success:true)
"""
import json
import re
import sys
import time
import urllib.request
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _console  # noqa: F401  控制台 UTF-8 兜底(见 _console.py)

BASE = "http://127.0.0.1:9222"
res = []


def call(name, args, timeout=30):
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
        return True, "EXC:%s" % ex
    rr = resp.get("result") or {}
    txt = "".join(i.get("text") or "" for i in (rr.get("content") or [])
                  if i.get("type") == "text") or json.dumps(rr, ensure_ascii=False)
    return bool(rr.get("isError")), txt


def val(t):
    s = (t or "").strip()
    try:
        j = json.loads(s)
        if isinstance(j, dict) and "message" in j:
            return str(j["message"])
    except Exception:
        pass
    return s.strip('"')


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-46s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:100]))


def must_err(tag, tool, args, needle=None):
    e, t = call(tool, args)
    # 必须区分"工具如实报错"与"服务连不上":
    # 上一版把连接异常也算成"报错" -> 服务没启动时整片假 PASS(fill_form 那条就是这样混过去的)。
    if t.startswith("EXC:"):
        rec(tag, False, "服务不可用: " + t[:70])
        return
    rec(tag, bool(e) and (needle is None or needle in t),
        ("报错 " if e else "!! 未报错 ") + t.replace("\n", " ")[:80])


def preflight():
    """服务未就绪就直接退出, 避免把'连不上'当成通过。"""
    try:
        h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
        print("  health: tools=%s cdp=%s" % (h.get("tool_count"), h.get("cdp_ready")))
        return True
    except Exception as ex:
        print("  !! 服务未就绪(%s) -> 本次验收作废, 不算通过也不算失败" % ex)
        return False


print("== 预检 ==")
if not preflight():
    sys.exit(2)


print("== 准备 ==")
call("browser_navigate", {"url": "https://example.com/?v=%d" % int(time.time()),
                          "wait_for_load": True}, 45)
time.sleep(0.6)

print("\n== 1) 5 处'省略 action 即执行动作' 必须报错 ==")
for tool in ("browser_kernel_events_all", "browser_kernel_reverse_probe",
             "browser_kernel_reverse_trace", "browser_kernel_reverse_algo",
             "browser_kernel_reverse_watch_global"):
    must_err("%s {} 应拒绝" % tool.replace("browser_", ""), tool, {}, "不能省略")

print("\n== 2) element_action 缺 index 必须报错(否则会点第0个元素) ==")
must_err("element_action {} 应拒绝", "browser_element_action", {}, "不能省略")

print("\n== 3) highlight duration_ms:0 == 不自动清除 ==")
e, t = call("browser_highlight", {"selector": "h1", "duration_ms": 0})
r = val(t)
rec("highlight 0 -> no_auto_clear", ("no_auto_clear" in r.replace(" ", "")) or ("auto_clear_ms:0" in r.replace(" ", "")),
    r.replace("\n", " ")[:90])
time.sleep(3.5)
still = val(call("browser_execute_js",
                 {"code": "(window.__MCP_HL__||[]).length"} )[1])
rec("3.5 秒后高亮仍在(未被自动清除)", still.strip() == "1",
    "window.__MCP_HL__.length = %s (期望 1)" % still.strip())

print("\n== 4) fill_form 全字段失败必须 isError ==")
e, t = call("browser_fill_form",
            {"fields": '[{"selector":"#nope-xyz","value":"1"}]'}, 40)
rec("fill_form 全败 -> isError", bool(e), ("报错 " if e else "!! 成功 ") + t.replace("\n", " ")[:90])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d 通过 ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
