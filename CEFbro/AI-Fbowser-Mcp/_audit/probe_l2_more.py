# -*- coding: utf-8 -*-
"""L2 覆盖(目标 ≤20 秒): get_scroll / element_action 其余 action / retry。

之前只覆盖了 element_action 的 get_value 与 set_value; 本脚本补 click / focus / scroll,
以及 browser_get_scroll 与预言机是否一致(判断"是否到底"靠它), 还有 browser_retry。
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
BTN, INP, FAR = "eb" + RUN, "ei" + RUN, "ef" + RUN
res = []


def call(name, args, timeout=40):
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


ENVELOPE_ONLY = {"id", "jsonrpc", "success", "data", "message", "result", "error",
                 "result_json", "poll_hint", "_hint", "needs_reload", "ok"}


def payload(t):
    """(同 fastcheck)取最有信息量的 JSON 对象, 递归打分, 不硬编码键名。"""
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
        return s
    cands = []
    collect(root, cands)
    best, bs = (root if isinstance(root, dict) else s), -1
    for d in cands:
        sc = len([k for k in d if k not in ENVELOPE_ONLY])
        sc += sum(1 for k, v in d.items() if isinstance(v, list) and v and k not in ENVELOPE_ONLY)
        if sc > bs:
            best, bs = d, sc
    return best


def js(code):
    e, t = call("browser_execute_js", {"code": code})
    if e:
        return None
    s = t.strip()
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


print("== 预检 ==")
try:
    h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
    print("  tools=%s cdp=%s" % (h.get("tool_count"), h.get("cdp_ready")))
except Exception as ex:
    print("  !! 服务未就绪(%s) -> 作废" % ex)
    sys.exit(2)

call("browser_navigate", {"url": "https://example.com/?l2=%s" % RUN, "wait_for_load": True}, 45)
time.sleep(0.4)
# 造一个可滚动页面 + 三个可控元素(按钮/输入框/远端元素)
js("document.body.style.height='4000px';"
   "document.body.insertAdjacentHTML('beforeend',"
   "'<button id=\"%s\">go</button><input id=\"%s\">"
   "<button id=\"%s\" style=\"margin-top:3000px\">far</button>');"
   "window.__c=0;document.getElementById('%s').addEventListener('click',"
   "function(){window.__c++;});'ok'" % (BTN, INP, FAR, BTN))
time.sleep(0.3)
# 注: browser_snapshot 只收录**可交互**元素(button/input/link…), 普通 div 不会进快照 ——
# 所以"远端元素"要用 button, 而不是 div(上一版用 div 导致该用例无从验证)。

print("\n== 1) browser_get_scroll 与预言机是否一致 ==")
sc = payload(call("browser_get_scroll", {})[1])
want_y = js("String(Math.round(window.pageYOffset||0))")
want_max = js("String(Math.round((document.documentElement.scrollHeight||0)"
              "-(window.innerHeight||0)))")
print("     工具: %s" % json.dumps(sc, ensure_ascii=False)[:170] if isinstance(sc, dict) else sc[:170])
print("     预言机: y=%s max_y=%s" % (want_y, want_max))
if isinstance(sc, dict):
    gy = str(sc.get("y", sc.get("scroll_y", sc.get("scrollY"))))
    gmax = str(sc.get("max_y", sc.get("maxY", sc.get("max_scroll_y"))))
    rec("get_scroll y 与预言机一致", gy == want_y, "工具=%s 预言机=%s" % (gy, want_y))
    rec("get_scroll max_y 与预言机一致", gmax == want_max,
        "工具=%s 预言机=%s" % (gmax, want_max))
else:
    rec("get_scroll 返回可解析", False, str(sc)[:90])

print("\n== 2) element_action 的 click / focus / scroll ==")
sp = payload(call("browser_snapshot", {})[1])
elems = sp.get("elements") if isinstance(sp, dict) else None
byid = {}
for el in (elems or []):
    if el.get("id"):
        byid[el["id"]] = el.get("i")
print("     snapshot count=%s, 命中: btn=%s inp=%s far=%s"
      % (len(elems or []), byid.get(BTN), byid.get(INP), byid.get(FAR)))

if byid.get(BTN) is not None:
    call("browser_element_action", {"index": byid[BTN], "action": "click"})
    rec("element_action click 真的触发点击", js("String(window.__c)") == "1",
        "window.__c=%s" % js("String(window.__c)"))
else:
    rec("element_action click", False, "快照里没有该按钮, 无法测")
if byid.get(INP) is not None:
    call("browser_element_action", {"index": byid[INP], "action": "focus"})
    rec("element_action focus 真的获得焦点", js("document.activeElement.id") == INP,
        "activeElement=%r" % js("document.activeElement.id"))
else:
    rec("element_action focus", False, "快照里没有该输入框")
if byid.get(FAR) is not None:
    js("window.scrollTo(0,0)")
    time.sleep(0.2)
    call("browser_element_action", {"index": byid[FAR], "action": "scroll"})
    # 注意: 该 action 用的是 scrollIntoView({behavior:'smooth'}) —— **平滑滚动是异步动画**,
    # 立刻读 pageYOffset 只会拿到动画刚开始的值(实测 2)。必须等动画结束再断言,
    # 否则会把"正常工作"误判成"没滚动"(上一版就是这样误报的)。
    y2 = 0
    for _ in range(8):
        time.sleep(0.25)
        y2 = int(js("String(Math.round(window.pageYOffset||0))") or 0)
        if y2 > 100:
            break
    rec("element_action scroll 真的滚动了(平滑滚动需等待)", y2 > 100, "scrollY=%d" % y2)
else:
    rec("element_action scroll", False, "快照里没有远端元素(可能超出快照上限)")

print("\n== 3) browser_retry ==")
e, t = call("browser_retry", {"tool": "browser_get_url", "max_retries": 2,
                              "max_total_ms": 5000}, 40)
rec("retry 包裹正常工具 -> 成功", not e, t.replace("\n", " ")[:80])
e2, t2 = call("browser_retry", {"tool": "browser_dom_query",
                                "args": "{\"selector\":\"#nope-xyz\"}",
                                "max_retries": 2, "backoff_ms": 100,
                                "max_total_ms": 5000}, 40)
rec("retry 包裹失败工具 -> 应报错(不谎报成功)", bool(e2),
    ("报错 " if e2 else "!! 成功 ") + t2.replace("\n", " ")[:80])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
