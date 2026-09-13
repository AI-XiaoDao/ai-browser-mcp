# -*- coding: utf-8 -*-
"""定向验收(目标 ≤10 秒): VIP 鼠标族缺参守卫 + browser_intercept 报错指错键。

本轮修的 4 处:
  1) browser_vip_mouse_click {}  -> 原先边界检查接受 0, 会真的在 (0,0) 单击
  2) browser_vip_mouse_move {}   -> 原先零校验, 会把鼠标移到 (0,0)
  3) browser_vip_mouse_wheel {}  -> 原先零校验: 缺坐标滚到 (0,0); 缺 delta 则滚 0 像素却报成功
  4) browser_intercept {}        -> 原先落到规则分支, 报"参数 url 不能为空"(指错键)
"""
import json
import sys
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


def rec(tag, ok, detail=""):
    res.append((tag, ok))
    print("  [%s] %-48s %s" % ("PASS" if ok else "FAIL", tag, str(detail)[:96]))


def must_err(tag, tool, args, needle=None):
    e, t = call(tool, args)
    if t.startswith("EXC:"):
        rec(tag, False, "服务不可用: " + t[:60])
        return
    ok = e and (needle is None or needle in t)
    rec(tag, ok, ("报错 " if e else "!! 未报错 ") + t.replace("\n", " ")[:80])


def must_ok(tag, tool, args, needle=None):
    e, t = call(tool, args)
    if t.startswith("EXC:"):
        rec(tag, False, "服务不可用: " + t[:60])
        return
    rec(tag, (not e) and (needle is None or needle in t),
        ("成功 " if not e else "!! 报错 ") + t.replace("\n", " ")[:80])


print("== 预检 ==")
try:
    h = json.loads(urllib.request.urlopen(BASE + "/health", timeout=5).read())
    print("  tools=%s cdp=%s" % (h.get("tool_count"), h.get("cdp_ready")))
except Exception as ex:
    print("  !! 服务未就绪(%s) -> 作废" % ex)
    sys.exit(2)

call("browser_navigate", {"url": "https://example.com/?r17=%d" % __import__("time").time(),
                          "wait_for_load": True}, 45)

print("\n== 1) VIP 鼠标族: 缺参必须拒绝 ==")
must_err("vip_mouse_click {} 应拒绝", "browser_vip_mouse_click", {}, "必须同时提供")
must_err("vip_mouse_move {} 应拒绝", "browser_vip_mouse_move", {}, "必须同时提供")
must_err("vip_mouse_wheel {} 应拒绝", "browser_vip_mouse_wheel", {}, "必须同时提供")
must_err("vip_mouse_wheel {x,y} 无 delta 应拒绝", "browser_vip_mouse_wheel",
         {"x": 100, "y": 100}, "delta")

print("\n== 2) 正对照: 显式传值必须成功(防'一律报错'的假修复) ==")
must_ok("vip_mouse_move {x,y} 正对照", "browser_vip_mouse_move", {"x": 100, "y": 100})
must_ok("vip_mouse_wheel {x,y,delta_y} 正对照", "browser_vip_mouse_wheel",
        {"x": 100, "y": 100, "delta_y": 120})
must_ok("vip_mouse_click {x,y} 正对照", "browser_vip_mouse_click", {"x": 100, "y": 100})

print("\n== 3) browser_intercept: 报错必须指出正确的键 ==")
must_err("intercept {} 应报 action 缺失", "browser_intercept", {}, "action 不能省略")
e, t = call("browser_intercept", {})
# 判据要看清"报错指向哪个键": 断言消息**以 action 开头**, 而不是断言全文不含 url ——
# 新文案里为了说明历史问题特意引用了『参数 url 不能为空』, 用"全文不含 url"当判据会被自己的文案绊倒。
rec("intercept {} 报错指向 action(而非 url)", t.strip().startswith("action 不能省略"),
    t.replace("\n", " ")[:80])

bad = [x for x in res if not x[1]]
print("\n== 结果: %d/%d ==" % (len(res) - len(bad), len(res)))
for x in bad:
    print("   未通过: %s" % x[0])
sys.exit(1 if bad else 0)
